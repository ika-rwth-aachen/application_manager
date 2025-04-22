######################################################
# Object Detection Fusion Application
#
# Performs object detection on incoming pointclouds and fuses object lists with EgoData
######################################################

# IDs of entities which request the application
string[] requester_ids

# Names of incoming topics with EgoData
Topic[] ego_data_topics

# Names of incoming topics with pointclouds
Topic[] pointcloud_topics
