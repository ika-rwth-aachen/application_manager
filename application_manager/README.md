# Application Manager

This package contains the ROS 2 node of the application manager. It acts as a ROS 2 action server and listens for incoming requests (`DeploymentRequests`) to deploy, reconfigure, or shutdown applications.

## Usage
The application manager can either be run in a Docker container or in a pod as part of a Kubernetes cluster.

See how the application manager is started in a Docker container in our [example](./../example/). From the container, it orchestrates resources in the Kubernetes cluster.

In case of **running in a Docker container** outside the Kubernetes cluster, the application manager needs to be provided with a cluster configuration file in order to be able to interact with the Kubernetes cluster. This cluster configuration file can be mounted to the container. The path where the file can be found by the application manager is specified via the parameter `cluster_config` in [`params.yml`](./config/params.yml). In our [example](./../example/), the cluster configuration file is created by the script [setupCluster.sh](./../example/kubernetes/setupCluster.sh#L41).

If **running in a Kubernetes pod**, make sure to provide the application manager with the correct service account permissions to be able to interact with the Kubernetes cluster. See the [role-based access control in our example](./../example/kubernetes/roles/).

## Action and Parameters
### Action

| Action | Type | Description |
| --- | --- | --- |
| [name parameterized via parameter `deployment_action_name`] | [`application_manager_interfaces/action/DeploymentRequest`](./application_manager_interfaces/action/DeploymentRequest.action) | Description of workload that is to be deployed by the application manager and the custom operators |

### Parameters

| Parameter | Type | Default | Description |
| --- | --- | --- | --- |
| `cluster_config` | `string` | `config/cluster_config.yml` | File containing the cluster configuration (necessary if executed standalone and not in a Kubernetes pod) |
| `deployment_action_name` | `string` | | Name of the action containing the DeploymentRequest |
| `namespace` | `string` | `default` | Kubernetes namespace where the workload is  deployed to |
| `k3d_image_registry` | `string` | `""` | Name of local k3d image registry storing container images |
| `connections.communication_broker_nodes` | `string[]` | `[]` | Names of Kubernetes nodes where communication brokers are running |
| `connections.communication_broker_params.<BROKER_NODE_NAME>.host` | `string` | `""` | IP address or hostname of the machine/service running the communication broker on node `<BROKER_NODE_NAME>` |
| `connections.communication_broker_params.<BROKER_NODE_NAME>.port` | `int` | `None` | Port the communication broker on node `<BROKER_NODE_NAME>` is listening on |
