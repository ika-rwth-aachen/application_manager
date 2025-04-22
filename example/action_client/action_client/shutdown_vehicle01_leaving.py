#!/usr/bin/env python3

from action_msgs.msg import GoalStatus
import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient

from application_manager_interfaces.action import DeploymentRequest
from application_manager_interfaces.msg import Application, ApplicationHeader, Connection, ObjectDetectionFusionApp, Topic


class TestActionClient(Node):

    def __init__(self):
        super().__init__('deployment_action_client')
        self.action_client_ = ActionClient(self, DeploymentRequest, '/event_detector_operator_plugin/operator_plugin/deployment_request')

    def goal_response_callback(self, future):
        # Triggered when the action server is accepting or rejecting the goal
        goal_handle = future.result()
        if not goal_handle.accepted:
            self.get_logger().info('Goal rejected. Shutting down.')
            rclpy.shutdown()

        self.get_logger().info('Goal accepted!')

        self._get_result_future = goal_handle.get_result_async()
        self._get_result_future.add_done_callback(self.get_result_callback)

    def feedback_callback(self, feedback_msg):
        # Triggered when the action server sends feedback
        self.get_logger().info('Received feedback: {0}'.format(feedback_msg.feedback.message))

    def get_result_callback(self, future):
        # Triggered when the action server sends a result
        result = future.result().result
        # This does not need to be set manually, but rather gets set by goal_handle.succeed() in the action server
        status = future.result().status 
        print()
        if status == GoalStatus.STATUS_SUCCEEDED:
            self.get_logger().info(f'Goal succeeded! {result.message}')
        else:
            self.get_logger().info('Goal failed with status: {0}'.format(status)) # if it fails, alway fails with status 6

        # Shutdown after receiving a result
        rclpy.shutdown()

    def send_goal(self):
        # Sends the goal to the action server
        self.get_logger().info('Waiting for action server...')
        self.action_client_.wait_for_server()

        # create message according to application manager interfaces
        deployment_request = DeploymentRequest.Goal()
        deployment_request.id = "station00/collective-perception-intersection"
        deployment_request.shutdown = True
        deployment_request.apps = []
        deployment_request.connections = []

        app1 = Application()
        app1.header = ApplicationHeader()
        app1.header.id = "edge/object_detection_fusion"
        app1.header.node_id = "edge"
        app1.type = app1.TYPE_OBJECT_DETECTION_FUSION
        app1.object_detection_fusion_app = ObjectDetectionFusionApp()
        app1.object_detection_fusion_app.requester_ids = ["vehicle01", "station00"]
        ego_data_vehicle01_topic = Topic()
        ego_data_vehicle01_topic.topic_name = "/vehicles/vehicle01/ego_data"
        ego_data_vehicle01_topic.source_node_id = "vehicle01"
        pointcloud_station00_topic = Topic()
        pointcloud_station00_topic.topic_name = "/stations/station00/pointcloud"
        pointcloud_station00_topic.source_node_id = "station00"
        app1.object_detection_fusion_app.ego_data_topics = [ego_data_vehicle01_topic]
        app1.object_detection_fusion_app.pointcloud_topics = [pointcloud_station00_topic]        
        deployment_request.apps.append(app1)

        connection1 = Connection()
        connection1.id = "vehicle01/edge"
        connection1.requester_ids = ["vehicle01", "station00"]
        connection1.broker_node_id = "edge"
        connection1.source_node_id = "vehicle01"
        connection1.source_topics = ["/vehicles/vehicle01/ego_data"]
        connection1.target_node_id = "edge"
        connection1.target_topics = ["/vehicles/vehicle01/ego_data"]
        connection1.type = connection1.TYPE_MQTT
        deployment_request.connections.append(connection1)

        connection2 = Connection()
        connection2.id = "station00/edge"
        connection2.requester_ids = ["vehicle01", "station00"]
        connection2.broker_node_id = "edge"
        connection2.source_node_id = "station00"
        connection2.source_topics = ["/stations/station00/drivers/lidar/pointcloud"]
        connection2.target_node_id = "edge"
        connection2.target_topics = ["/stations/station00/drivers/lidar/pointcloud"]
        connection2.type = connection2.TYPE_MQTT
        deployment_request.connections.append(connection2)

        self.send_goal_future = self.action_client_.send_goal_async(deployment_request, feedback_callback=self.feedback_callback)
        self.send_goal_future.add_done_callback(self.goal_response_callback)

def main(args=None):
    rclpy.init(args=args)
    action_client = TestActionClient()
    action_client.send_goal()
    rclpy.spin(action_client)

if __name__ == '__main__':
    main()