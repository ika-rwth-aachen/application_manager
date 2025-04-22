#!/usr/bin/env python3

import asyncio
import os
import sys

import ament_index_python.packages
import rclpy
from kubernetes.client.exceptions import ApiException
from rcl_interfaces.msg import ParameterDescriptor
from rclpy.action import ActionServer, CancelResponse, GoalResponse
from rclpy.node import Node

from application_manager.applications.object_detection_fusion_app import ObjectDetectionFusionApp
from application_manager.connections.mqtt_connection import MQTTConnection
from application_manager.kubernetes_api import KubernetesAPI
from application_manager.utils import multiple_replace

from application_manager_interfaces.action import DeploymentRequest
from application_manager_interfaces.msg import Application, Connection


class ApplicationManagerNode(Node):

    def __init__(self):
        """Application Manager node class inheriting from the Node class
        """
        super().__init__("application_manager")

        self.load_parameters()
        self.setup()

    def load_parameters(self):
        """Declares and loads parameters used in the node.
        """
        param_desc = ParameterDescriptor()

        # common parameters
        param_desc.description = "File containing the cluster configuration."
        self.declare_parameter("cluster_config", "config/cluster_config.yml", descriptor=param_desc)
        param_desc.description = "Name of subscribed topic containing the deployment request."
        self.declare_parameter("deployment_action_name", rclpy.Parameter.Type.STRING, descriptor=param_desc)
        param_desc.description = "Name of local k3d image registry."
        self.declare_parameter("k3d_image_registry", "", descriptor=param_desc)
        param_desc.description = "Namespace in which the deployment is created."
        self.declare_parameter("namespace", "default", descriptor=param_desc)

        self.cluster_config_file = self.get_parameter("cluster_config").value
        try:
            self.deployment_action_name = self.get_parameter("deployment_action_name").value
        except rclpy.exceptions.ParameterUninitializedException:
            self.get_logger().fatal(f"Parameter 'deployment_action_name' is required")
            sys.exit(1)
        self.k3d_image_registry = self.get_parameter("k3d_image_registry").value
        self.namespace = self.get_parameter("namespace").value

        # connection-specific parameters
        param_desc.description = "Topic names: Skip publication of topics which are being already published during the intial deployment"
        self.declare_parameter("connections.init_comm_topics", rclpy.Parameter.Type.STRING_ARRAY, descriptor=param_desc)
        self.init_comm_topics = self.get_parameter_or("connections.init_comm_topics", [])
        if self.init_comm_topics:
            self.init_comm_topics = self.init_comm_topics.value
        # Communication Broker
        self.communication_broker_configs = {}
        param_desc.description = "Kubernetes nodes running the communication brokers"
        self.declare_parameter("connections.communication_broker_nodes", rclpy.Parameter.Type.STRING_ARRAY, descriptor=param_desc)
        try:
            communication_broker_nodes = self.get_parameter("connections.communication_broker_nodes").value
        except rclpy.exceptions.ParameterUninitializedException:
            self.get_logger().fatal(f"Parameter 'connections.communication_broker_nodes' is required")
            sys.exit(1)
        for node in communication_broker_nodes:
            self.communication_broker_configs[node] = {}
            param_desc.description = f"IP address or hostname of the machine/service running the communication broker on node {node}"
            self.declare_parameter(f"connections.communication_broker_params.{node}.host", rclpy.Parameter.Type.STRING, descriptor=param_desc)
            try:
                self.communication_broker_configs[node]["host"] = self.get_parameter(f"connections.communication_broker_params.{node}.host").value
            except rclpy.exceptions.ParameterUninitializedException:
                self.get_logger().fatal(f"Parameter 'connections.communication_broker_params.{node}.host' is required")
                sys.exit(1)
            param_desc.description = f"Port the communication broker on node {node} is listening on"
            self.declare_parameter(f"connections.communication_broker_params.{node}.port", rclpy.Parameter.Type.INTEGER, descriptor=param_desc)
            try:
                self.communication_broker_configs[node]["port"] = self.get_parameter(f"connections.communication_broker_params.{node}.port").value
            except rclpy.exceptions.ParameterUninitializedException:
                self.get_logger().fatal(f"Parameter 'connections.communication_broker_params.{node}.port' is required")
                sys.exit(1)

    def setup(self):
        """Sets up ROS2 action server, initializes Kubernetes API
        """
        self.action_server = ActionServer(
            self,
            DeploymentRequest,
            self.deployment_action_name,
            execute_callback=self.action_execute_callback,
            goal_callback=self.action_handle_goal,
            cancel_callback=self.action_handle_cancel,
            handle_accepted_callback=self.action_handle_accepted)

        # check if provided path for cluster config file is absolute or relative
        if not os.path.isabs(self.cluster_config_file):
            self.cluster_config_file = os.path.join(
                ament_index_python.packages.get_package_share_directory('application_manager'),
                self.cluster_config_file
            )

        # check if Application Manager is deployed in a pod in a Kubernetes cluster
        check_am_in_kubernetes_pod = 'KUBERNETES_SERVICE_HOST' in os.environ and 'KUBERNETES_SERVICE_PORT' in os.environ

        # initialize Kubernetes API
        if check_am_in_kubernetes_pod:
            self.kubernetes_api = KubernetesAPI()
        else:
            # if running outside a Kubernetes cluster, cluster config file has to be provided
            if not os.path.exists(self.cluster_config_file):
                self.get_logger().fatal("ERROR: No cluster config file found!")
                sys.exit(1)
            self.kubernetes_api = KubernetesAPI(self.cluster_config_file)

        self.get_logger().info(f"Application Manager is set up and ready to receive DeploymentRequests.")

    def action_handle_goal(self, goal_request: DeploymentRequest.Goal) -> GoalResponse:
        """This callback is invoked when an action goal is requested
        Args:
            goal_request (DeploymentRequest.Goal): Deployment request
        Returns:
            GoalResponse: Accept or reject the goal, determines if the action should be executed or not
        """
        if not goal_request.shutdown:
            self.get_logger().info(f"[Deployment] Received DeploymentRequest '{goal_request.id}'.")
        else:
            self.get_logger().info(f"[Shutdown] Received DeploymentRequest '{goal_request.id}'.")

        # Check if the goal request interface is valid
        try:
            assert isinstance(goal_request, DeploymentRequest.Goal), "Request is not an instance of DeploymentRequest.Goal"
            assert isinstance(goal_request.apps, list), "Apps is not a list"
            assert isinstance(goal_request.connections, list), "Connections is not a list"
            return GoalResponse.ACCEPT

        # If any checks fail, reject the goal
        except AssertionError as e:
            self.get_logger().error(f"DeploymentRequest '{goal_request.id}' rejected due to error: '{e}'")
            return GoalResponse.REJECT

    def action_handle_cancel(self, goal_handle: DeploymentRequest.Goal) -> CancelResponse:
        """This callback is invoked when a running action is requested to cancel by the action client
        Args:
            goal_handle (DeploymentRequest.Goal): Deployment request
        Returns:
            CancelResponse: Accept or reject the cancel request
        """
        self.get_logger().info(f"Received request to cancel deployment request '{goal_handle.request.id}'.")
        return CancelResponse.ACCEPT

    def action_handle_accepted(self, goal_handle: DeploymentRequest.Goal) -> None:
        """This callback is invoked when an action goal request is accepted
        Args:
            goal_handle (DeploymentRequest.Goal): Deployment request
        """
        self.get_logger().info(f"DeploymentRequest '{goal_handle.request.id}' accepted")
        goal_handle.execute()

    def action_execute_callback(self, goal_handle: DeploymentRequest.Goal) -> DeploymentRequest.Result:
        """Processing and execution of action goal
        Args:
            goal_handle (DeploymentRequest.Goal): Deployment request
        Returns:
            DeploymentRequest.Result: Result after goal is finished
        """
        deployment_request = goal_handle.request
        deployment_request_name = multiple_replace(deployment_request.id, {"_": "-", "/": "-"})

        cr_deployments = []
        # Configure the Custom Resources for the applications
        if deployment_request.apps:
            cr_deployments.extend(self.configure_custom_resource_deployments_applications(
                apps=deployment_request.apps, 
                namespace=self.namespace, 
                shutdown=deployment_request.shutdown
            ))

        # Configure the Custom Resources for the connections
        if deployment_request.connections:
            cr_deployments.extend(self.configure_custom_resource_deployments_connections(
                connections=deployment_request.connections,
                namespace=self.namespace,
                shutdown=deployment_request.shutdown
            ))

        feedback_list = []
        # Open temporary event loop to deploy all Custom Resources concurrently
        if cr_deployments:
            feedback_list.extend(self.temporary_event_loop(self.deploy_custom_resources_concurrently(cr_deployments)))

        # Publish feedback messages
        [goal_handle.publish_feedback(feedback) for feedback in feedback_list]

        result = DeploymentRequest.Result()
        result.message = f"DeploymentRequest '{deployment_request_name}' successfully processed!"
        self.get_logger().info(f"{result.message}\n")

        goal_handle.succeed()
        return result

    def configure_custom_resource_deployments_applications(
            self, 
            apps: list[Application], 
            namespace: str,
            shutdown: bool
        ) -> list[dict]:
        """Configures Custom Resources for applications based on application type
        Args:
            apps (list[Application]): Applications to configure
            namespace (str): Namespace to deploy the application to
            shutdown (bool): Flag indicating whether the application is to be shut down
        Returns:
            list[dict]: Custom Resource Deployments for the applications
        """
        cr_deployments = []
        for app in apps:

            # Application-specific configurations
            if app.type == app.TYPE_OBJECT_DETECTION_FUSION:
                odf_app = ObjectDetectionFusionApp(
                    odf_app=app, 
                    k3d_image_registry=self.k3d_image_registry
                )
                cr_deployments.extend(odf_app.generate_custom_resources(
                    shutdown=shutdown,
                    namespace=namespace
                ))

            else:
                # Further application types to be implemented
                pass
        
        return cr_deployments

    def select_communication_broker(self, connection: Connection) -> str:
        """Selects communication broker for the Connection
            Case 1: Only one communication broker is available
            Case 2: Communication broker is specified in the Connection
            Case 3: Communication broker is running on target node
            Case 4: Communication broker is running on source node
        Args:
            connection (Connection): Connection to be established
        Returns:
            str: Communication broker node ID
        """
        if len(self.communication_broker_configs) == 1:
            broker_node_id = list(self.communication_broker_configs.keys())[0]
        elif connection.broker_node_id in list(self.communication_broker_configs.keys()):
            broker_node_id = connection.broker_node_id
        elif connection.target_node_id in list(self.communication_broker_configs.keys()):
            broker_node_id = connection.target_node_id
        elif connection.source_node_id in list(self.communication_broker_configs.keys()):
            broker_node_id = connection.source_node_id
        return broker_node_id

    def configure_custom_resource_deployments_connections(
            self, 
            connections: list[Connection],
            namespace: str,
            shutdown: bool
        ) -> list[dict]:
        """Configures Custom Resources for Connections based on connection type
        Args:
            cons (list[Connection]): Connections to be configured
            namespace (str): Namespace to deploy the Connections to
            shutdown (bool): Flag to indicate if the Connection is to be shutdown
        Returns:
            list[dict]: Custom Resource Deployments for the Connections
        """
        cr_deployments = []
        for connection in connections:
            connection_id = multiple_replace(connection.id, {"_": "-", "/": "-"})

            # Decide which broker to use for the connection
            broker_node_id = self.select_communication_broker(connection)

            # Configure the connection based on the connection type
            if connection.type == connection.TYPE_MQTT:
                mqtt_connection = MQTTConnection(
                    mqtt_connection=connection, 
                    broker_node_id=broker_node_id,
                    connection_id=connection_id,
                    k3d_image_registry=self.k3d_image_registry
                )
                cr_deployments.append(mqtt_connection.generate_custom_resource(
                    communication_broker_configs=self.communication_broker_configs,
                    shutdown=shutdown,
                    already_bridged_topics=self.init_comm_topics,
                    namespace=namespace
                ))

            else:
                # Further connection types to be implemented
                pass

        return cr_deployments

    async def deploy_custom_resources_concurrently(self, cr_deployments: list[dict]) -> list[DeploymentRequest.Feedback]:
        """Deploys Custom Resources concurrently
        Args:
            cr_deployments (list[dict]): Custom resources to be deployed
        Returns:
            list[DeploymentRequest.Feedback]: Feedback messages if the deployment was successful or not
        """
        # Deploy all Custom Resources concurrently
        coroutines_deploy = [
            self.deploy_custom_resource_with_feedback(
                group=cr_deployment.get("group"),
                version=cr_deployment.get("version"),
                namespace=cr_deployment.get("namespace"),
                plural=cr_deployment.get("plural"),
                name=cr_deployment.get("name"),
                body=cr_deployment.get("body")
            )
            for cr_deployment in cr_deployments
        ]
        feedback_list = await asyncio.gather(*coroutines_deploy)
        return feedback_list

    async def deploy_custom_resource_with_feedback(
            self, group: str, version: str, namespace: str, plural: str, name: str, body: dict
        ) -> DeploymentRequest.Feedback:
        """Deploys a Custom Resource and returns a feedback message
        Args:
            group (str): Group of the Custom Resource
            version (str): Version of the Custom Resource
            namespace (str): Namespace where the Custom Resource is suppose to be deployed to
            plural (str): Plural of the Custom Resource
            name (str): Name of the Custom Resource
            body (dict): Body of the Custom Resource
        Returns:
            DeploymentRequest.Feedback: Feedback messages if the deployment was successful or not
        """
        feedback = DeploymentRequest.Feedback()
        deployment_update = "No update was made to the Custom Resource"
        try:
            response = self.kubernetes_api.update_custom_resource(
                group=group, version=version, namespace=namespace, plural=plural, name=name, body=body
            )
            deployment_update = f'Successfully updated "{body["metadata"]["name"]}"'
        except ApiException as api_e:
            if api_e.status == 404:
                try:  # Custom Resource does not exist yet. Create it
                    response = self.kubernetes_api.create_custom_resource(
                        group=group, version=version, namespace=namespace, plural=plural, body=body
                    )
                    deployment_update = f'Successfully created "{body["metadata"]["name"]}"'
                except Exception as e:
                    deployment_update = f'Deployment of "{body["metadata"]["name"]}" was unsuccessful: {e}'
            else:
                deployment_update = f'Failed to update "{body["metadata"]["name"]}". {api_e}'
        except Exception as e:
            deployment_update = f'Deployment of "{body["metadata"]["name"]}" was unsuccessful: {e}'
        feedback.message = deployment_update
        return feedback

    def temporary_event_loop(self, coroutine) -> any:
        """Creates temporary event loop to run a function implemented with async/await inside event loop of ROS2
        Args:
            coroutine : Async function to be executed inside this temporary event loop
        Returns:
            any: Result of the async function
        """
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(coroutine)
        finally:
            loop.close()
            asyncio.set_event_loop(None)
        return result

def main():
    rclpy.init()
    rclpy.spin(ApplicationManagerNode())
    rclpy.shutdown()

if __name__ == '__main__':
    main()