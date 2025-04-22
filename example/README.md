# Example: Running the Application Manager
This example demonstrates how to run the Application Manager in a local Kubernetes cluster using k3d. The Application Manager is launched in a Docker container and, from its container, deploys and deletes Kubernetes resources on demand. In this example, deployment and shutdown requests are sent from a simple action client to the Application Manager.

The example relies on our *RobotKube* use case ["Collective Perception at Intersection"](https://github.com/ika-rwth-aachen/robotkube/tree/main/use-cases/collective-perception-intersection) in which vehicles one after another approach an intersection and leave it again. In the *RobotKube* use case, the action is sent automated as a result of the vehicles approaching a certain region of interest. Here in this example, the action is sent manually from the action client.

## Usage

### Prerequisites

If not available already, install the following:

- [Ubuntu](https://ubuntu.com/download/desktop)
- [Docker Engine](https://docs.docker.com/engine/install/ubuntu/) 
- [k3d](https://k3d.io/v5.6.0/#install-current-latest-release)
- [kubectl](https://kubernetes.io/docs/tasks/tools/#kubectl)
- [Helm](https://helm.sh/docs/intro/install/)
- Python Package [PyYAML](https://pypi.org/project/PyYAML/)

### Quick Start

1. Make sure prerequisites are installed and clone this repository:
    ```bash
    git clone https://github.com/ika-rwth-aachen/application_manager.git
    ```

1. Create a [local k3d image registry](https://k3d.io/v5.2.0/usage/registries/) using the provided bash script:
    ```bash
    # application_manager/example
    ./kubernetes/createRegistry.sh
    ```

    **Hint**: This will take approximately 5 minutes.

1. Run the provided helper script [setupCluster.sh](./kubernetes/setupCluster.sh) to create the Kubernetes Cluster:
    ```bash
    # application_manager/example
    ./kubernetes/setupCluster.sh
    ```

    **Hint**: This will take approximately 5 minutes. Previous clusters named `application-registry` will be deleted.

1. Monitor the start-up and shut down of the different Kubernetes resources and also the (un)installation of Helm releases:
    ```bash
    watch -n 0.1 kubectl get all
    ```
    ```bash
    watch -n 0.1 helm list
    ```

1. In another terminal, launch the Application Manager in a Docker container:
    ```bash
    # application_manager/example
    docker run --rm --network host --name application-manager --volume $(pwd)/kubernetes/cluster_config.yml:/docker-ros/ws/install/application_manager/share/application_manager/config/cluster_config.yml ghcr.io/ika-rwth-aachen/application_manager:latest
    ```

1. In another terminal, send the first deployment request from the action client (`vehicle00` approaching):
    ```bash
    docker exec -it application-manager bash -c "source install/setup.bash && ros2 run action_client deployment_vehicle00_approaching"
    ```

1. Send the second deployment request from the action client (`vehicle01` approaching):
    ```bash
    docker exec -it application-manager bash -c "source install/setup.bash && ros2 run action_client deployment_vehicle01_approaching"
    ```

1. Send the first shutdown request from the action client (`vehicle00` leaving):
    ```bash
    docker exec -it application-manager bash -c "source install/setup.bash && ros2 run action_client shutdown_vehicle00_leaving"
    ```

1. Send the second shutdown request from the action client (`vehicle01` leaving):
    ```bash
    docker exec -it application-manager bash -c "source install/setup.bash && ros2 run action_client shutdown_vehicle01_leaving"
    ```	