# Compatibility baseline

Selected 2026-10-23. Primary target: Linux amd64, Ubuntu 24.04 container.

| Component | Selected input | Reason |
| --- | --- | --- |
| Ubuntu | 24.04; digest in Dockerfile | PX4 v1.17 toolchain supports Noble |
| ROS 2 | Jazzy | PX4's recommended Noble ROS distribution |
| Gazebo | Harmonic (gz-sim8, transport13) | Explicitly handled by the selected PX4 gz_bridge build |
| PX4 | v1.17.0, d6f12ad1c4f70ad3230afd7d86e971421e02fef4 | Stable release |
| px4_msgs | release/1.17, 86d8239e962f6939e05c3737784f60c02fa884db | Release branch matching firmware schema |
| XRCE Agent | v2.4.3, 73622810d984349b80bbac0ef55fc0b694d62222 | PX4's XRCE v2 client family |
| QGC | v5.1.5, official architecture asset + SHA256 | Stable desktop release, extracted without FUSE |

Upstream evidence: [PX4 v1.17 setup script](https://github.com/PX4/PX4-Autopilot/blob/v1.17.0/Tools/setup/ubuntu.sh), [PX4 v1.17 Gazebo bridge CMake](https://github.com/PX4/PX4-Autopilot/blob/v1.17.0/src/modules/simulation/gz_bridge/CMakeLists.txt), [ROS user guide](https://docs.px4.io/main/en/ros2/user_guide), [XRCE bridge](https://docs.px4.io/v1.17/en/middleware/uxrce_dds), [QGC v5.1.5 release](https://github.com/mavlink/qgroundcontrol/releases/tag/v5.1.5).

Installation uses the signed OSRF Harmonic apt repository and the signed official ROS repository; Jazzy's standard ros-gz packages are the Harmonic pairing. Inspect the installed package inventory if changing these sources. Avoid installing Jetty or Gazebo Classic alongside this baseline.

The Ubuntu setup script was inspected rather than executed wholesale: its host service/embedded compiler actions are unnecessary for SITL, and Python goes in an isolated system-site-packages venv. The selected PX4 Python requirement file is retained for traceability.

`versions.env` locks source commits and QGC assets. Plugin commits are in `docker/plugins.lock`. Ubuntu/ROS/Gazebo apt packages and the agent's small upstream logger dependency can change within their configured release constraints. The agent reuses ROS Jazzy's Fast DDS/CDR libraries to avoid duplicate middleware libraries; `/etc/px4-packages.txt` and `/etc/px4-python-resolved.txt` record actual build versions. This is a pinned-source environment, not a bit-identical dependency snapshot.

Actual test evidence and platform limitations are recorded in implementation-status.md. A compatibility choice alone does not prove the complete combination works.
