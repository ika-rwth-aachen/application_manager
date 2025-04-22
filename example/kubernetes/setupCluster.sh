#!/bin/bash

REGISTRY_PORT=41671

# Delete previous application-manager cluster if it exists
if k3d cluster list | grep -q "application-manager"; then k3d cluster delete application-manager; fi

SCRIPT_PATH=$(readlink -f "$0")
SCRIPT_DIR=$(dirname "$SCRIPT_PATH")

# Create application-manager cluster using config file
cat <<EOL > $SCRIPT_DIR/application-manager-k3d-cluster.yml
kind: Simple
apiVersion: k3d.io/v1alpha5
servers: 1
agents: 4
options:
  k3s:
    nodeLabels:
      - label: node_id=cloud
        nodeFilters:
          - server:0
      - label: node_id=edge
        nodeFilters:
          - agent:0
      - label: node_id=station00
        nodeFilters:
          - agent:1
      - label: node_id=vehicle00
        nodeFilters:
          - agent:2
      - label: node_id=vehicle01
        nodeFilters:
          - agent:3
EOL
# Create k3d cluster and allow more memory usage per node than default
k3d cluster create application-manager --config=$SCRIPT_DIR/application-manager-k3d-cluster.yml --registry-use k3d-application-manager-registry.localhost:$REGISTRY_PORT \
  --k3s-arg "--kubelet-arg=eviction-hard=memory.available<200Mi,nodefs.available<5%,imagefs.available<5%@all" \
  --k3s-arg "--kubelet-arg=eviction-soft=memory.available<500Mi,nodefs.available<10%,imagefs.available<10%@all" \
  --k3s-arg "--kubelet-arg=eviction-soft-grace-period=memory.available=1m,nodefs.available=1m,imagefs.available=1m@all"
k3d kubeconfig get application-manager > "$SCRIPT_DIR/cluster_config.yml"
echo "The cluster config has been written to '$SCRIPT_DIR/cluster_config.yml'"

# Create Custom Resource Definitions
echo "Creating Custom Resource Definitions ..."
kubectl create -f $SCRIPT_DIR/../../custom-operators/mqtt-connection/custom-resource-definition/
kubectl create -f $SCRIPT_DIR/../../custom-operators/object-detection/custom-resource-definition/
kubectl create -f $SCRIPT_DIR/../../custom-operators/object-fusion/custom-resource-definition/
echo "CRDs have been created."

# Pull images from k3d image registry to all nodes
python3 $SCRIPT_DIR/utils/prepullImages.py --registry_name k3d-application-manager-registry.localhost --port $REGISTRY_PORT --yaml_file_path $SCRIPT_DIR/imagesPerNode.yml
kubectl get pods --all-namespaces | grep "node-debugger-k3d-application-manager" | awk '{print $2 " -n " $1}' | xargs -L1 kubectl delete pod 1>/dev/null
python3 $SCRIPT_DIR/utils/prepullImagesCheck.py --registry_name k3d-application-manager-registry.localhost --port $REGISTRY_PORT --yaml_file_path $SCRIPT_DIR/imagesPerNode.yml

# Print message when all processes have finished
echo "All processes have finished. The Kubernetes cluster has successfully been prepared."

echo "Checking if CRDs exist ..."
# Check if CRDs exist
if ! kubectl get crd mqttconnections.ika.rwth-aachen.de > /dev/null 2>&1; then
    echo "CRD mqttconnections.ika.rwth-aachen.de does not exist."
    exit 1
fi
if ! kubectl get crd objectdetections.ika.rwth-aachen.de > /dev/null 2>&1; then
    echo "CRD objectdetections.ika.rwth-aachen.de does not exist."
    exit 1
fi
if ! kubectl get crd objectfusions.ika.rwth-aachen.de > /dev/null 2>&1; then
    echo "CRD objectfusions.ika.rwth-aachen.de does not exist."
    exit 1
fi
echo "CRDs exist."

# Create K8s Roles
echo "Creating cluster roles ..."
kubectl create -f $SCRIPT_DIR/roles 1>/dev/null
echo "Cluster Roles have been created."

# Create K8S Persistent Volumes
echo "Creating persistent volumes ..."
kubectl create -f $SCRIPT_DIR/volumes/ 1>/dev/null
echo "Persistent volumes have been created."

# Deploy the operators
echo "Deploying the custom operators ..."
kubectl create configmap application-registry-interface --from-file=$SCRIPT_DIR/application-registry-interface/application_registry_interface.yml -o yaml --dry-run=client | sed 's/^metadata:/metadata:\n  labels:\n    tag: am/' | kubectl apply -f - 1>/dev/null
kubectl create configmap kubernetes-operator-configuration --from-file=$SCRIPT_DIR/operator-config/config.yml -o yaml --dry-run=client | sed 's/^metadata:/metadata:\n  labels:\n    tag: am/' | kubectl apply -f - 1>/dev/null
kubectl apply -f $SCRIPT_DIR/operators/kopf_operator_mqtt.yml 1>/dev/null
kubectl apply -f $SCRIPT_DIR/operators/kopf_operator_object_detection.yml 1>/dev/null
kubectl apply -f $SCRIPT_DIR/operators/kopf_operator_object_fusion.yml 1>/dev/null
echo "Custom operators have been deployed."