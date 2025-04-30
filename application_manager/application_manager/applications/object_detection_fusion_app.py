# ==============================================================================
# MIT License

# Copyright (c) 2025 Institute for Automotive Engineering (ika), RWTH Aachen University

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
# ==============================================================================

from typing import Optional

from application_manager.utils import multiple_replace
from application_manager_interfaces.msg import Application


class ObjectDetectionFusionApp:

    def __init__ (self, odf_app: Application, k3d_image_registry: Optional[str] = None) -> None:
        """Initializes the Object Detection Fusion application
        Args:
            odf_app (Application): Application from application_manager_interfaces
            k3d_image_registry (str, optional): Name of local k3d image registry to obtain container images from. Defaults to None.
        """
        self.app = odf_app

        if k3d_image_registry:      # Else: Use default image defined in Helm chart
            self.container_image_object_fusion = {"repository": k3d_image_registry + "/object_fusion", "tag": "latest"}
            self.container_image_object_detection = {"repository": k3d_image_registry + "/point_cloud_object_detection", "tag": "latest"}
            self.container_image_k8s_configmap_watcher = {"repository": k3d_image_registry + "/k8s_configmap_watcher", "tag": "latest"}
        else:
            self.container_image_object_fusion = None
            self.container_image_object_detection = None
            self.container_image_k8s_configmap_watcher = None

    def get_config(self, namespace: str, shutdown: bool) -> tuple[dict, dict]:
        """Generates the configuration for the Object Detection Fusion application
        Args:
            namespace (str): Namespace where the Object Detection Fusion application is supposed to be deployed to
            shutdown (bool): Whether to stop or start the application
        Returns:
            list[dict]: Configuration of Object Detection Fusion application
        """
        config = {"objectDetection": {}, "objectFusion": {}}
        
        # Generate config for the Object Detection services (one per incoming pointcloud topic)
        topics_objectlist = []
        for pointcloud_topic in self.app.object_detection_fusion_app.pointcloud_topics:
            client_id = pointcloud_topic.source_node_id
            topic_objectlist = f'/{client_id}_local_objectlist'
            topics_objectlist.append(topic_objectlist)
            pcod_ros_node_name = f"pcod_{client_id}"
            object_detection_name = "od-" + multiple_replace(self.app.header.node_id + "_" + client_id, {"_": "-", "/": "-"})
            object_detection_instance = {
                "operator": {
                    "namespace": namespace,
                    "requester": self.app.object_detection_fusion_app.requester_ids,
                    "shutdown": shutdown,
                },
                "name": object_detection_name,
                "commandOverride": [
                    "/bin/bash",
                    "-c",
                    f"source install/setup.bash && ros2 launch point_cloud_object_detection point_cloud_object_detection.launch.py node_name:={pcod_ros_node_name} point_cloud_topic:={pointcloud_topic.topic_name} object_list_topic:={topic_objectlist}"
                ],
                "labelTag": "application-manager",
                "terminationGracePeriodSeconds": 1,
                "nodeSelector": {"node_id": self.app.header.node_id},
                "image": self.container_image_object_detection if self.container_image_object_detection else {},
                "configDetection": {
                    "ros_node_name": pcod_ros_node_name
                }
            }
            config["objectDetection"][client_id] = object_detection_instance

        # Generate config for the Object Fusion and the K8s ConfigMap Watcher services
        object_fusion_name = "of-" + multiple_replace(self.app.header.id, {"_": "-", "/": "-"})
        object_fusion_ros_node_name = "of_" + multiple_replace(self.app.header.id, {"-": "_", "/": "_"})
        watcher_ros_node_name = f"{object_fusion_ros_node_name}_watcher"
        topics_ego_data = [ego_data.topic_name for ego_data in self.app.object_detection_fusion_app.ego_data_topics]
        topic_fused_objectlist = "/" + multiple_replace(self.app.header.id, {"-": "_", "/": "_"}) + "_global_objectlist"
        topic_fused_trajectories = "/" + multiple_replace(self.app.header.id, {"-": "_", "/": "_"}) + "_global_trajectories"
        config["objectFusion"] = {
            "operator": {
                "namespace": namespace,
                "requester": self.app.object_detection_fusion_app.requester_ids,
                "shutdown": shutdown,
                "topicsEgoData": topics_ego_data,
                "topicsObjectlist": topics_objectlist,
            },
            "fusion": {
                "name": object_fusion_name,
                "commandOverride": [
                    "/bin/bash",
                    "-c",
                    f"source install/setup.bash && ros2 launch object_fusion fusion_function_launch.py node_name:={object_fusion_ros_node_name} raw_object_lists_topic:=/raw_objects_dummy_topic fused_object_lists_topic:={topic_fused_objectlist} fused_trajectories_topic:={topic_fused_trajectories}"
                ],
                "labelTag": "application-manager",
                "terminationGracePeriodSeconds": 1,
                "nodeSelector": {"node_id": self.app.header.node_id},
                "image": self.container_image_object_fusion if self.container_image_object_fusion else {},
                "configFusion": {
                    "ros_node_name": object_fusion_ros_node_name,
                    "use_sim_time": True,
                    "additional_inputs": {
                        "mode": "dynamic",
                        "topics_egodata": topics_ego_data,
                        "topics_objectlist": topics_objectlist,
                        "length": 0,
                    }
                }
            },
            "watcher": {
                "name": f"{object_fusion_name}-watcher",
                "commandOverride": [
                    "/bin/bash",
                    "-c",
                    f"source install/setup.bash && ros2 launch k8s_configmap_watcher k8s_configmap_watcher.launch.py node_name:={watcher_ros_node_name}"
                ],
                "labelTag": "application-manager",
                "terminationGracePeriodSeconds": 1,
                "nodeSelector": {"node_id": self.app.header.node_id},
                "image": self.container_image_k8s_configmap_watcher if self.container_image_k8s_configmap_watcher else {},
                "configWatcher": {
                    "ros_node_name": watcher_ros_node_name,
                    "configmap_name": f"{object_fusion_name}-configmap",
                    "namespace": namespace,
                    "period": 0.5,
                    "ros_params_file_name": "params.yml",
                    "target_ros_node": object_fusion_ros_node_name,
                }
            }
        }
        return [config["objectDetection"], config["objectFusion"]]

    def generate_custom_resources(self, shutdown: bool, namespace: str = "default") -> dict:
        """Generates the Custom Resources for the Object Detection Fusion application
        Args:
            shutdown (bool): Whether to stop or start the application
            namespace (str): Namespace where the object detection fusion is to be deployed to
        Returns:
            list[dict]: Custom Resources for the Object Detection Fusion application
        """
        custom_resources = []

        [config_detection, config_fusion] = self.get_config(namespace, shutdown)

        # Generate Custom Resources for the Object Detection services
        for client_id in config_detection:
            body_custom_resource_od = {
                "apiVersion": "ika.rwth-aachen.de/v1",
                "kind": "ObjectDetection",
                "metadata": {
                    "name": config_detection[client_id]["name"],
                    "labels": {
                        "name": config_detection[client_id]["name"],
                        "tag": "application-manager",
                    },
                },
                "spec": config_detection[client_id],
            }
            custom_resources.append({
                "group": "ika.rwth-aachen.de",
                "version": "v1",
                "namespace": namespace,
                "plural": "objectdetections",
                "name": body_custom_resource_od["metadata"]["name"],
                "body": body_custom_resource_od
            })

        # Generate Custom Resource for the Object Fusion service
        body_custom_resource_of = {
            "apiVersion": "ika.rwth-aachen.de/v1",
            "kind": "ObjectFusion",
            "metadata": {
                "name": config_fusion["fusion"]["name"],
                "labels": {
                    "name": config_fusion["fusion"]["name"],
                    "tag": "application-manager",
                },
            },
            "spec": config_fusion,
        }
        custom_resources.append({
            "group": "ika.rwth-aachen.de",
            "version": "v1",
            "namespace": namespace,
            "plural": "objectfusions",
            "name": body_custom_resource_of["metadata"]["name"],
            "body": body_custom_resource_of
        })

        return custom_resources