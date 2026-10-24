#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.."
image=${1:-px4_ros2_novnc:latest}
docker run --rm "$image" bash -ec '
    test "$(id -u)" -gt 0
    source /etc/os-release; test "$VERSION_ID" = 24.04
    test "$ROS_DISTRO" = jazzy
    python3 -c "import rclpy; import cv_bridge; import cv2; import numpy; import jinja2; import em; import pymavlink; assert int(numpy.__version__.split(chr(46))[0]) == 1"
    ros2 pkg prefix ros_gz_bridge
    test -x /opt/qgroundcontrol/AppRun
    MicroXRCEAgent --help >/dev/null 2>&1 || test "$?" -eq 1
    vim -Nu "$HOME/.vimrc" -n -es -c "qall!"
    tmux -L smoke new-session -d -s smoke
    test -f "$HOME/.tmux/plugins/tmux/nord.tmux"
    tmux -L smoke kill-server
    vim --version | grep -F +ruby
    test -w "$HOME/.rviz2/persistent_settings"
'
