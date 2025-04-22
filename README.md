# Application Management in C-ITS: Application Manager and Custom Operators

<p align="center">
  <img src="https://img.shields.io/github/v/release/ika-rwth-aachen/application_manager"/>
  <img src="https://img.shields.io/github/license/ika-rwth-aachen/application_manager"/>
  <a href="https://github.com/ika-rwth-aachen/application_manager/actions/workflows/docker-ros.yml"><img src="https://github.com/ika-rwth-aachen/application_manager/actions/workflows/docker-ros.yml/badge.svg"/></a>
  <a href="https://ika-rwth-aachen.github.io/application_manager/"><img src="https://github.com/ika-rwth-aachen/application_manager/actions/workflows/doc.yml/badge.svg"/></a>
  <img src="https://img.shields.io/badge/ROS 2-humble-293754"/>
  <a href="https://github.com/ika-rwth-aachen/application_manager"><img src="https://img.shields.io/github/stars/ika-rwth-aachen/application_manager?style=social"/></a>
</p>

With this repository, we provide a reference implementation of our application management framework which is conceptualized in the research article mentioned below. The framework consists of the components *application manager* and the *custom operators*. The framework enables the demand-driven deployment, reconfiguration, and shutdown of applications in a Kubernetes cluster.

The repository contains the following components:
- **Application Manager**: The application manager is a ROS 2 node implemented in the [*application_manager*](./application_manager/) package. It acts as a ROS 2 action server and listens for incoming requests (`DeploymentRequests`) to deploy, reconfigure, or shutdown applications.
- **Application Manager Interfaces**: The [*application_manager_interfaces*](./application_manager_interfaces/) package contains the ROS 2 action and message definitions containing the `DeploymentRequest` which is interpreted by the application manager.
- **Custom Operators**: The code for the implemented [*Kopf*](https://kopf.readthedocs.io/en/latest/) operators together with the Kubernetes custom resource definitions (CRDs) is located in the [*custom-operators*](./custom-operators/) folder.

The reference implementation contains the *Object Detection Fusion* application enabling collective environment perception. This application is applied in the experiment described in our research article mentioned below. The logic is extensible for new applications.

<p align="center">
  <img src="assets/application_management.png" alt="Image Description" width="80%">
</p>

The image above illustrates the architecture of the application management framework. The application manager and the custom operators are brought into action in the use case ["Collective Perception at Intersection"](https://github.com/ika-rwth-aachen/robotkube/tree/main/use-cases/collective-perception-intersection) in the scope of [**RobotKube**](https://github.com/ika-rwth-aachen/robotkube). We invite you to check out the code and run the use case.


> [!IMPORTANT]  
> This repository is open-sourced and maintained by the [**Institute for Automotive Engineering (ika) at RWTH Aachen University**](https://www.ika.rwth-aachen.de/).  
> **Advanced C-ITS Use Cases** are one of many research topics within our [*Vehicle Intelligence & Automated Driving*](https://www.ika.rwth-aachen.de/en/competences/fields-of-research/vehicle-intelligence-automated-driving.html) domain.  
> If you would like to learn more about how we can support your advanced driver assistance and automated driving efforts, feel free to reach out to us!  
> :email: ***opensource@ika.rwth-aachen.de***

## Quick Start

> [!NOTE]
> Check out the [repository RobotKube](https://github.com/ika-rwth-aachen/robotkube) containing executable use cases to see the application manager and the custom operators in action!  
> Especially the use case ["Collective Perception at Intersection"](https://github.com/ika-rwth-aachen/robotkube/tree/main/use-cases/collective-perception-intersection) gives a good idea of their capabilities.

Consider our [example](./example/) and see how to run the application manager in a Docker container orchestrating Kubernetes resources in a local Kubernetes cluster based on *k3d*.

## Installation

You can integrate the *application_manager* package stack into your existing ROS 2 workspace by cloning the repository, installing all dependencies using [*rosdep*](http://wiki.ros.org/rosdep), and then building it from source.

```bash
# ROS workspace$
git clone https://github.com/ika-rwth-aachen/application_manager.git src
rosdep install -r --ignore-src --from-paths src
colcon build --packages-up-to application_manager --cmake-args -DCMAKE_BUILD_TYPE=Release
pip install kubernetes
```

### docker-ros

The *application_manager* package stack is also available as a Docker image, containerized through [*docker-ros*](https://github.com/ika-rwth-aachen/docker-ros). Note that launching the container launches the `application_manager` node by default (`ros2 launch application_manager application_manager.launch.py`).

```bash
docker run --rm ghcr.io/ika-rwth-aachen/application_manager:latest
```

## Documentation

### How to add support for a new application

<details><summary><i>Click to show</i></summary>

Consider the following steps:
1. In the [*application_manager*](./application_manager/) package, create a new class in a new Python file located in the [`applications`](./application_manager/application_manager/applications/) folder. Include it in the [main file](./application_manager/application_manager/application_manager.py).
1. Call the functions implemented in the new class for your application in the [main file](./application_manager/application_manager/application_manager.py) in `configure_custom_resource_deployments_applications()`.
1. Depending on your needs, implement one or more new custom operators in the [`custom-operators`](./custom-operators/) folder.
    1. Add one new Custom Resource Definition (CRD) (see for example [here](./custom-operators/object-fusion/custom-resource-definition/object_fusion_crd.yml)) per implemented operator.
    1. Add the code of you new operator in the [`custom-operators`](./custom-operators/) folder. 
1. Extend the ROS 2 message definition in the [*application_manager_interfaces*](./application_manager_interfaces/) package with your new application, especially [here](./application_manager_interfaces/msg/Application.msg). Consider what information is needed in the scope of the interface.

</details>

## Research Article
Coming soon!

## Acknowledgements

This work is accomplished within the projects *6GEM* (FKZ 16KISK036K) and *autotech.agil* (FKZ 01IS22088A). We acknowledge the financial support for the projects by the *Federal Ministry of Education and Research of Germany (BMBF)*.