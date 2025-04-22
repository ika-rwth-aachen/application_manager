cmake_minimum_required(VERSION 3.12.0 FATAL_ERROR)
project(application_manager_interfaces)

find_package(ros_environment REQUIRED QUIET)

find_package(action_msgs REQUIRED)
find_package(ament_cmake REQUIRED)
find_package(rosidl_default_generators REQUIRED)
find_package(std_msgs REQUIRED)

ament_export_dependencies(
      action_msgs
      std_msgs
)

set(msg_files
      "msg/Application.msg"
      "msg/ApplicationHeader.msg"
      "msg/Connection.msg"
      "msg/Topic.msg"
      "msg/Applications/ObjectDetectionFusionApp.msg"
)

set(action_files
      "action/DeploymentRequest.action"
)

rosidl_generate_interfaces(${PROJECT_NAME}
      ${msg_files}
      ${action_files}
      DEPENDENCIES action_msgs std_msgs
)

ament_package()
