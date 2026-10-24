#!/usr/bin/env bash
set -euo pipefail
image=${1:-px4_ros2_vnc:latest}
container=$(docker run -d --rm "$image")
cleanup() { docker stop -t 10 "$container" >/dev/null 2>&1 || true; }
trap cleanup EXIT
for attempt in {1..60}; do
    if docker exec "$container" python3 -c '
import socket, urllib.request
with socket.create_connection(("localhost",5901),timeout=2) as s:
    assert s.recv(12).startswith(b"RFB ")
assert urllib.request.urlopen("http://localhost:6901/vnc.html",timeout=2).status == 200
with socket.create_connection(("localhost",6901),timeout=2) as s:
    s.sendall(b"GET /websockify HTTP/1.1\r\nHost: localhost:6901\r\nUpgrade: websocket\r\nConnection: Upgrade\r\nSec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==\r\nSec-WebSocket-Version: 13\r\n\r\n")
    assert b"101 Switching Protocols" in s.recv(4096)
' 2>/dev/null; then break; fi
    if (( attempt == 60 )); then docker logs "$container"; exit 1; fi
    sleep 1
done
docker exec "$container" pgrep -x xfce4-session
docker exec "$container" bash -c '
    export DISPLAY=:1 XDG_RUNTIME_DIR="/tmp/runtime-$(id -u)" LIBGL_ALWAYS_SOFTWARE=1
    timeout --signal=INT --kill-after=5 15 start_qgroundcontrol > /tmp/qgc-smoke.log 2>&1
    result=$?
    cat /tmp/qgc-smoke.log
    test "$result" -eq 124 || exit 1
    ! grep -E "error while loading shared libraries|Could not load the Qt platform plugin|QQmlApplicationEngine failed" /tmp/qgc-smoke.log
'
echo 'VNC, noVNC, desktop and QGC launch checks passed. Visual flight check is separate.'
