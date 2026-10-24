# Tested platform matrix

Tested 2026-10-23 on Linux amd64 with Docker Engine 29.9.2. Host RAM: 30 GiB reported by `free`; builds used UID/GID 1000. Peak build memory was not measured.

| Mode / capability | Evidence | Status |
| --- | --- | --- |
| Headless SITL + ROS 2 | Full x500 takeoff/hold/land/disarm with network disabled | Verified |
| Browser/VNC desktop | Xfce, TigerVNC RFB, noVNC HTTP/WebSocket, QGC + Gazebo rendering | Verified |
| Native X11/Xwayland | Local `DISPLAY=:0`, scoped Xauthority, RViz, Mesa OpenGL 4.5 | Verified |
| Software rendering | Mesa llvmpipe; graphical vehicle/flight state inspected | Verified |
| RGB-D + 3D lidar, 2026-10-24 | EGL/software, no DISPLAY/network; payload dimensions, finite returns, TF, and complete flight with RViz subscribers | Verified |
| Host UID/GID source writes | PX4/ROS build output and persistent Data owned by host user | Verified at 1000:1000 |
| NVIDIA hardware rendering | Launcher implemented; actual renderer/performance not tested | Unverified |
| Intel/AMD DRI hardware rendering | Device/GID forwarding implemented | Unverified |
| ARM64 | QGC asset/checksum selection implemented | Unverified |
| Docker Desktop / WSLg | Browser workflow intended; no platform-specific evidence | Unverified |
| Remote SSH/TCP DISPLAY | Native launcher explicitly rejects it; use tunneled VNC instead | Unsupported |
| Host-side QGC/ROS routing, multi-vehicle, hardware flashing | Outside baseline | Future work |

Measured build evidence: first px4_msgs colcon build took 7 min 17 s, followed by 2.37 s for the authored example package. The initial apt/Python installation layer took roughly 625 s and the first large image export roughly 250 s; these are component timings, not a controlled end-to-end benchmark. Cached rebuilds reuse the toolchain. The images are about 8.6 GB (native) and 8.8 GB (VNC), with shared layers. The PX4 checkout/build uses about 2.6 GiB and the ROS workspace about 193 MiB on this host. Exact image identities and byte counts are recorded in Data/evidence/image-inventory.txt.

The README's 40 GB disk and 8–16 GB RAM guidance is a planning allowance. It is not a measured minimum or a claim that all hardware configurations meet real-time simulation performance.
