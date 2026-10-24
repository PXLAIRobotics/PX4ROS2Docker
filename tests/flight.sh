#!/usr/bin/env bash
# Run INSIDE the development container after both workspace builds.
set -euo pipefail
cleanup() {
    [[ -z ${heartbeat_pid:-} ]] || kill "$heartbeat_pid" 2>/dev/null || true
    stop_px4_dev || true
}
trap cleanup EXIT
python3 /opt/px4-tests/check-messages.py
start_px4_dev --headless --no-attach
# A local test-only GCS heartbeat satisfies the normal PX4 GCS connection requirement.
# QGC rendering/vehicle discovery is verified separately in the desktop test.
python3 -u - <<'PY' &
import time
from pymavlink import mavutil
connection = mavutil.mavlink_connection('udpin:127.0.0.1:14550', source_system=255, source_component=190)
while True:
    connection.recv_match(blocking=True, timeout=1)
    connection.mav.heartbeat_send(mavutil.mavlink.MAV_TYPE_GCS, mavutil.mavlink.MAV_AUTOPILOT_INVALID, 0, 0, 0)
    time.sleep(0.25)
PY
heartbeat_pid=$!
timeout --signal=INT --kill-after=65 150 ros2 run px4_dev_examples offboard_demo --sitl
