# MQTT Connection Operator
## Installation
This custom operator operates the *MQTT connection* involving the services for the source and the target communication client. Find the corresponding *Custom Resource Definition (CRD)* [here](./custom-resource-definition/mqtt_connection_crd.yml).

## Installation
Run the following command to build a Docker image based on the provided Dockerfile:
```bash
# application_manager/custom-operators/mqtt-connection$
docker build -t mqtt-connection-operator .
```

## Usage
The operator is implemented to be run in a Pod in a Kubernetes cluster. See how it is done in our [example](./../../example/). There, an [exemplary deployment file](./../../example/kubernetes/operators/kopf_operator_mqtt.yml) is provided. In the [example](./../../example/), the CRD is created via the script [setupCluster.sh](./../../example/kubernetes/setupCluster.sh#L46).

## Parameters
The following parameters are provided via the [params file](./operator/config.yml):
- `url_application_registry`: URL to the registry where the packaged Helm Charts are stored
- `configmap_application_registry_interface` [optional]: Name of the ConfigMap that contains the information about the Helm Charts in the registry (chart name and version per application type)
- `configmap_namespace` [optional]: Kubernetes namespace where the above mentioned ConfigMap is stored

Inside the container, the params file is expected at `/config/config.yml`. Consider this when applying your own parameters.