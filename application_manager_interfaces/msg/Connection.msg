# ID of the connection
string id

# In case of brokered communication: ID of the node running the broker
string broker_node_id

# IDs of entities which request the connection
string[] requester_ids

# ID of source node
string source_node_id

# N topics to be bridged from source node (to be mapped to entries of target_topics[])
string[] source_topics

# ID of target node
string target_node_id

# N topics to be bridged to target node (to be mapped to entries of source_topics[])
string[] target_topics

# Type of communication
uint8 type
uint8 TYPE_ROS = 0
uint8 TYPE_MQTT = 1
uint8 TYPE_ZENOH = 2