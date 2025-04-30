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

from application_manager.connections.connection import BaseConnection

from application_manager.utils import multiple_replace
from application_manager_interfaces.msg import Connection


class MQTTConnection(BaseConnection):

    def __init__(self, 
                 mqtt_connection: Connection, 
                 broker_node_id: str, 
                 connection_id: Optional[str] = None,
                 k3d_image_registry: Optional[str] = None
                 ) -> None:
        """Initialize the MQTTConnection object
        Args:
            mqtt_connection (Connection): Connection from application_manager_interfaces
            broker_node_id (str): Broker node ID
            connection_id (str): Connection ID
            k3d_image_registry (str, optional): Name of local k3d image registry to obtain container images from. Defaults to None.
        """
        super().__init__(mqtt_connection, broker_node_id, connection_id)

        self.connection_type = "TYPE_MQTT"
        self.default_helm_chart_name = "mqtt-connection-helm"
        if k3d_image_registry:      # Else: Use default image defined in Helm chart
            self.container_image = {"repository": k3d_image_registry + "/mqtt_client", "tag": "latest"}
        else:
            self.container_image = None

    def get_config(
            self,
            name_source_client: str,
            name_target_client: str,
            communication_broker_configs: dict,
            already_bridged_topics: Optional[list[str]] = [],
            ) -> list[dict]:
        """Generates the configuration of MQTT Connection
        Args:
            name_source_client (str): Name of the source MQTT client
            name_target_client (str): Name of the target MQTT client
            communication_broker_configs (dict): Communication broker configuration
            already_bridged_topics (list[str], optional): Topics already published/bridged via different Connection, e.g., in the scope of the initial deployment.
        Returns:
            dict: Configuration of MQTT Connection
        """
        config = {"configSource": {}, "configTarget": {}, "configCommon": {}}

        # Configuration of the source MQTT Client service
        publish_source_topics = []
        ros_node_name_source = f"mqtt_{self.connection_id}_source"
        ros_node_name_source = ros_node_name_source.replace("-","_")
        for topic in self.connection.source_topics:
            if topic not in already_bridged_topics:
                publish_source_topics.append(topic)
        bridge_config_source = {
            "ros2mqtt": {
                "ros_topics": [publish_source_topics[i] for i in range(len(publish_source_topics))]
            }
        }
        if publish_source_topics:
            for i in range(len(publish_source_topics)):
                bridge_config_source["ros2mqtt"][publish_source_topics[i]] = {"mqtt_topic": 'mqtt' + publish_source_topics[i]}
            config["configSource"] = {
                "name": name_source_client,
                "commandOverride": [
                    "/bin/bash", 
                    "-c", 
                    f"source install/setup.bash && ros2 launch mqtt_client standalone.launch.ros2.xml node_name:={ros_node_name_source}"
                ],
                "nodeSelector": {"node_id": self.connection.source_node_id},
                "configMQTT": {
                    "ros_node_name": ros_node_name_source,
                    "bridge": bridge_config_source,
                    "client": {
                        "id": f"mqtt-{self.connection_id}-source"
                    }
                }
            }

        # Configuration of the target MQTT Client service
        publish_target_topics = []
        ros_node_name_target = f"mqtt_{self.connection_id}_target"
        ros_node_name_target = ros_node_name_target.replace("-","_")
        for topic in self.connection.target_topics:
            if topic not in already_bridged_topics:
                publish_target_topics.append(topic)
        bridge_config_target = {
            "mqtt2ros": {
                "mqtt_topics": [f'mqtt{publish_target_topics[i]}' for i in range(len(publish_target_topics))]
            }
        }
        if publish_target_topics:
            for i in range(len(publish_target_topics)):
                bridge_config_target["mqtt2ros"][f'mqtt{publish_target_topics[i]}'] = {"ros_topic": publish_target_topics[i]}
            config["configTarget"] = {
                "name": name_target_client,
                "commandOverride": [
                    "/bin/bash", 
                    "-c", 
                    f"source install/setup.bash && ros2 launch mqtt_client standalone.launch.ros2.xml node_name:={ros_node_name_target}"
                ],
                "nodeSelector": {"node_id": self.connection.target_node_id},
                "configMQTT": {
                    "ros_node_name": ros_node_name_target,
                    "bridge": bridge_config_target,
                    "client": {
                        "id": f"mqtt-{self.connection_id}-target"
                    }
                }
            }

        # Common Configuration (Source and Target)
        config["configCommon"] = {
            "labelTag": "application-manager",
            "terminationGracePeriodSeconds": 1,
            "image": self.container_image if self.container_image else {},
            "broker": {
                "host": communication_broker_configs[self.broker_node_id]["host"],
                "port": communication_broker_configs[self.broker_node_id]["port"]
            }
        }

        return config

    def generate_custom_resource(
            self,
            communication_broker_configs: dict,
            shutdown: bool,
            already_bridged_topics: Optional[list[str]] = [],
            namespace: str = "default",
            ) -> list[dict]:
        """Generates the Custom Ressource for the Connection
        Args:
            communication_broker_configs (dict): Communication broker configuration
            shutdown (bool): Whether to stop or start the MQTT clients
            already_bridged_topics (list[str], optional): Topics already published/bridged via different Connection, e.g., in the scope of the initial deployment.
            namespace (str, optional): Namespace where the Connection is to be deployed to.
        Returns:
            dict: Configuration of Custom Resource for the Connection
        """

        connection_id = multiple_replace(self.connection_id, {"_": "-", "/": "-"})
        config = self.get_config(
            name_source_client = f"kopf-mqtt-{connection_id}-source",
            name_target_client = f"kopf-mqtt-{connection_id}-target",
            communication_broker_configs = communication_broker_configs,
            already_bridged_topics = already_bridged_topics
        )
        config["operator"] = {
            "namespace": namespace,
            "requester": self.connection.requester_ids,
            "shutdown": shutdown,
        }

        # Get config for Custom Ressource for the Connection
        cr_name = f"mqtt-connection-{connection_id}"
        body_custom_resource = {
            "apiVersion": "ika.rwth-aachen.de/v1",
            "kind": "MqttConnection",
            "metadata": {
                "name": cr_name,
                "labels": {
                    "name": cr_name,
                    "tag": "application-manager",
                },
            },
            "spec": config,
        }
        custom_resource = {
            "group": "ika.rwth-aachen.de",
            "version": "v1",
            "namespace": namespace,
            "plural": "mqttconnections",
            "name": body_custom_resource["metadata"]["name"],
            "body": body_custom_resource
        }

        return custom_resource
