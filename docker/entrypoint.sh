#!/usr/bin/env bash
set -eo pipefail
export ROS_DOMAIN_ID="${ROS_DOMAIN_ID:-0}"
export RMW_IMPLEMENTATION="${RMW_IMPLEMENTATION:-rmw_fastrtps_cpp}"
export GZ_DISTRO=harmonic
source /opt/ros/jazzy/setup.bash
if [[ -f "$HOME/Projects/ros2_workspace/install/setup.bash" ]]; then
    source "$HOME/Projects/ros2_workspace/install/setup.bash"
fi
mkdir -p "$HOME/Data"/{qgc/config,qgc/data,qgc/cache,qgc/Documents,bags,sessions,ccache,gazebo} "$HOME/.rviz2"
if [[ ! -e "$HOME/Documents" && ! -L "$HOME/Documents" ]]; then
    ln -s "$HOME/Data/qgc/Documents" "$HOME/Documents"
fi
if [[ ! -e "$HOME/.gz" && ! -L "$HOME/.gz" ]]; then
    ln -s "$HOME/Data/gazebo" "$HOME/.gz"
fi
export CCACHE_DIR="$HOME/Data/ccache"
if [[ ! -e "$HOME/.rviz2/persistent_settings" ]]; then
    cp /etc/px4-rviz-settings "$HOME/.rviz2/persistent_settings"
fi
exec "$@"
