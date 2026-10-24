#!/usr/bin/env bash
set -euo pipefail
source /etc/px4-versions.env
export DEBIAN_FRONTEND=noninteractive
apt-get update
apt-get install -y --no-install-recommends ca-certificates curl gnupg locales software-properties-common
add-apt-repository -y universe
curl -fL --retry 3 "https://github.com/ros-infrastructure/ros-apt-source/releases/download/${ROS_APT_SOURCE_VERSION}/ros2-apt-source_${ROS_APT_SOURCE_VERSION}.noble_all.deb" -o /tmp/ros-source.deb
dpkg -i /tmp/ros-source.deb
rm /tmp/ros-source.deb
curl -fsSL --retry 3 https://packages.osrfoundation.org/gazebo.gpg -o /usr/share/keyrings/gazebo.gpg
printf 'deb [arch=%s signed-by=/usr/share/keyrings/gazebo.gpg] https://packages.osrfoundation.org/gazebo/ubuntu-stable noble main\n' "$(dpkg --print-architecture)" > /etc/apt/sources.list.d/gazebo.list
apt-get update
apt-get install -y --no-install-recommends \
    ros-dev-tools ros-jazzy-desktop ros-jazzy-ros-gz ros-jazzy-rmw-fastrtps-cpp \
    gz-harmonic libunwind-dev cppzmq-dev libeigen3-dev protobuf-compiler libprotobuf-dev \
    astyle build-essential ccache cmake cppcheck file gdb git git-lfs lcov libssl-dev libxml2-dev \
    libxml2-utils ninja-build pkg-config rsync shellcheck unzip zip bc \
    python3-dev python3-pip python3-venv python3-setuptools python3-wheel python-is-python3 \
    vim nano tmux htop sudo wget bash-completion universal-ctags ruby-dev \
    mesa-utils libgl1-mesa-dri libegl1 libopengl0 libxkbcommon-x11-0 libxcb-xinerama0 \
    libxcb-cursor0 libxcb-icccm4 libxcb-image0 libxcb-keysyms1 libxcb-render-util0 \
    libx11-xcb1 libnss3 libasound2t64 libpulse0 libfuse2t64 libvulkan1 \
    gstreamer1.0-plugins-base gstreamer1.0-plugins-good gstreamer1.0-plugins-bad \
    gstreamer1.0-plugins-ugly gstreamer1.0-libav libgstreamer-plugins-base1.0-dev \
    iputils-ping iproute2 netcat-openbsd xauth tini fontconfig x11-utils dbus-x11
python3 -m venv --system-site-packages /opt/px4-venv
/opt/px4-venv/bin/pip install --no-cache-dir -r /tmp/px4-requirements.txt
/opt/px4-venv/bin/pip freeze > /etc/px4-python-resolved.txt
dpkg-query -W > /etc/px4-packages.txt
rm -rf /var/lib/apt/lists/*
