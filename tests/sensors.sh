#!/usr/bin/env bash
# Inside a built development container, with no existing simulation running.
set -euo pipefail
trap 'stop_px4_dev' EXIT
export PX4_SENSOR_SUITE=rgbd_lidar
start_px4_dev --headless --no-attach
ros2 run px4_dev_examples sensor_check --save "$HOME/Data/evidence/sensors"
