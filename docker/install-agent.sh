#!/usr/bin/env bash
set -eo pipefail
source /etc/px4-versions.env
git clone --branch "$XRCE_AGENT_VERSION" --depth 1 https://github.com/eProsima/Micro-XRCE-DDS-Agent.git /tmp/xrce-agent
test "$(git -C /tmp/xrce-agent rev-parse HEAD)" = "$XRCE_AGENT_COMMIT"
# Reuse Jazzy's Fast DDS/CDR, avoiding duplicate libraries with the same SONAME.
source /opt/ros/jazzy/setup.bash
cmake -S /tmp/xrce-agent -B /tmp/xrce-agent/build -DCMAKE_BUILD_TYPE=Release \
    -DUAGENT_BUILD_TESTS=OFF -DUAGENT_P2P_PROFILE=OFF \
    -DUAGENT_USE_SYSTEM_FASTDDS=ON -DUAGENT_USE_SYSTEM_FASTCDR=ON
cmake --build /tmp/xrce-agent/build -j 4
cmake --install /tmp/xrce-agent/build
ldconfig
rm -rf /tmp/xrce-agent
