#!/usr/bin/env bash
# Invoked inside px4-supervise.py's owned process group.
set -eo pipefail
source "$PX4_SENSOR_GZ_ENV"
if [[ $PX4_SENSOR_SUITE == rgbd_lidar ]]; then
    export PX4_GZ_MODELS="$PX4_SENSOR_SHARE/simulation/models"
fi
if [[ -f "$PX4_SENSOR_SHARE/simulation/worlds/${PX4_GZ_WORLD}.sdf" ]]; then
    export PX4_GZ_WORLDS="$PX4_SENSOR_SHARE/simulation/worlds"
fi
export GZ_SIM_RESOURCE_PATH="$PX4_SENSOR_SHARE/simulation/models:$PX4_GZ_WORLDS:$GZ_SIM_RESOURCE_PATH"
export PX4_GZ_STANDALONE=1
# EGL keeps rendering sensors usable even with no X server / no Gazebo GUI.
# PX4's pinned launcher has no option for this flag, so start its server here.
gz sim -s -r --headless-rendering "${PX4_GZ_WORLDS}/${PX4_GZ_WORLD}.sdf" &
if [[ -z ${HEADLESS:-} ]]; then start_gazebo_gui & fi
exec "$@"
