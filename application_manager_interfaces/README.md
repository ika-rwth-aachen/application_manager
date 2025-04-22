# Application Manager Interfaces

This ROS 2 package provides the ROS message type definition for the *deployment request* interpreted by the application manager. The implementation is based on the [ROS 2 Action](https://docs.ros.org/en/humble/Tutorials/Beginner-CLI-Tools/Understanding-ROS2-Actions/Understanding-ROS2-Actions.html) interface. 

### Action 'DeploymentRequest'

#### Request/Goal
| Name | Type | Description |
| --- | --- | --- |
| `apps` | `Application[]` | Array of applications which are part of the requested workload |
| `connections` | `Connection[]` | Array of connections (communication channels) which are part of the requested workload |
| `id` | `string` | ID of DeploymentRequest |
| `shutdown` | `bool` | Whether a shutdown is requested (if true, shutdown is requested; if false, deployment is requested) |

#### Result
| Name | Type | Description |
| --- | --- | --- |
| `message` | `string` | Result message informing whether the goal was successfully reached |

#### Feedback
| Name | Type | Description |
| --- | --- | --- |
| `feedback` | `string` | Feedback message with updates regarding the goal |
