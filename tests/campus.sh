#!/usr/bin/env bash
# Inside the built container with no other simulation running.
set -euo pipefail
export PX4_GZ_WORLD=corda_campus PX4_SENSOR_SUITE=rgbd_lidar
unset PX4_GZ_MODEL_POSE
trap 'stop_px4_dev' EXIT
start_px4_dev --headless --no-attach
ros2 run px4_dev_examples campus_check
ros2 run px4_dev_examples sensor_check --save "$HOME/Data/evidence/campus-sensors"
