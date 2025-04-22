#!/usr/bin/env python

import os

from ament_index_python import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch_ros.actions import Node
from launch.substitutions import LaunchConfiguration


def generate_launch_description():

    args = [
        DeclareLaunchArgument("name", default_value="application_manager", description="node name"),
        DeclareLaunchArgument("namespace", default_value="", description="node namespace"),
        DeclareLaunchArgument(
            "params", 
            default_value=os.path.join(get_package_share_directory("application_manager"), "config", "params.yml"), 
            description="path to parameter file"
        ),
        DeclareLaunchArgument("log_level", default_value="info", description="ROS logging level (debug, info, warn, error, fatal)"),
    ]

    return LaunchDescription([
        *args,
        Node(package="application_manager",
             executable="application_manager",
             name=LaunchConfiguration('name'),
             namespace=LaunchConfiguration('namespace'),
             parameters=[LaunchConfiguration('params')],
             arguments=["--ros-args", "--log-level", LaunchConfiguration("log_level")],
             output="screen",
             emulate_tty=True)
    ])
