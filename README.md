# PX4 + ROS 2 Docker development environment

PX4 SITL, Gazebo Harmonic, ROS 2 Jazzy and QGroundControl in a shared development image, with either an Xfce browser/VNC desktop or native Linux graphics. Source and builds stay in this repository's `Projects` folder; compilation and simulation run inside Docker.

The Bash, tmux, Vim, Nerd Font and numbered-script workflow comes from `ROSLyricalDocker`. This repository has its own images, containers and PX4 examples. See [TODO.md](TODO.md) for implementation tasks and [implementation status](docs/implementation-status.md) for verified capabilities and remaining checks.

## Versions and host requirements

- Ubuntu 24.04, ROS 2 Jazzy, Gazebo Harmonic.
- PX4 v1.17.0 and matching `px4_msgs` release/1.17 commit.
- Micro XRCE-DDS Agent v2.4.3; QGroundControl v5.1.5.
- Exact source revisions, binary checksums and ROS repository installer version: [versions.env](versions.env).
- Docker Engine on Linux amd64 is the primary target. A graphical Linux desktop is needed only for native graphics; the VNC variant provides its own desktop.
- Budget at least 40 GB of disk for images, recursive sources and builds, and 8 GB RAM; 16 GB or more is preferable. Initial builds/downloads take time. These are planning allowances, not measured minimums.
- Install Docker and grant your ordinary user daemon access before running scripts. Build without sudo so build-time UID/GID match your user.
- NVIDIA Container Toolkit is optional and must be configured on the host separately. Intel/AMD `/dev/dri` access is detected. Software rendering is available.

ARM64 has a QGC asset selection path but is not considered supported until tested. Docker Desktop and cross-architecture emulation also require separate validation. The image contains a SITL toolchain; firmware flashing, USB devices and full embedded board toolchains are future work.

## Browser/VNC workflow

On the host, from this directory:

```bash
./001_build_px4_ros2_image.sh
./002_run_px4_ros2_container.sh
```

Open [the desktop](http://localhost:6901/vnc.html?autoconnect=true&resize=remote) with password `password`. A native VNC client can use `localhost:5901`. Both ports bind only to host loopback. Open an Xfce terminal inside the desktop, or attach from another host terminal:

```bash
./003_attach_bash_to_px4_ros2_container.sh
```

Inside the container, initialize persistent source checkouts and compile:

```bash
setup_px4_workspace
build_px4_sitl
build_ros2_workspace
# Make the newly built ROS overlay available in this shell:
source ~/Projects/ros2_workspace/install/setup.bash
start_px4_dev
```

`start_px4_dev` creates a `px4-dev` tmux session: XRCE agent, PX4 console, sensor bridge, Gazebo GUI, QGroundControl and a ROS shell. It waits for valid PX4 ROS telemetry and rendered sensor data with TF before reporting readiness. In QGC, wait for vehicle connection and preflight readiness; use the normal Takeoff/Land actions for a manual simulated flight.

From the ROS tmux window (or a newly attached shell), try:

```bash
ros2 run px4_dev_examples telemetry
# Ctrl+C exits telemetry. This next command deliberately commands a simulated flight:
ros2 run px4_dev_examples offboard_demo --sitl
```

The offboard demo requests arm, takes off 3 m relative to the initial local position, holds 5 seconds, lands, waits for automatic disarm and restores Hold mode. A GCS connection (normally QGC) and healthy estimator are required. It reports observed flight states and fails on stage timeouts. Run it only with the local simulator selected. Interrupting it requests landing and waits for confirmation; QGC and the PX4 console remain available for intervention.

Detach from tmux with `Ctrl+b`, then `d`. Detaching leaves simulation running. Stop it explicitly:

```bash
stop_px4_dev
```

From the host, the lifecycle commands are:

```bash
./997_stop_px4_ros2_container.sh
./998_remove_px4_ros2_container.sh   # for a retained container created without --rm
./999_remove_px4_ros2_image.sh
```

The default run is foreground and `--rm`: stopping it removes the container, preserving bind-mounted sources/data. The `001c`, `002c`, `003c`, `997c`, `998c`, `999c` scripts explicitly select the same VNC image.

## Native Linux display (without VNC)

The inherited `novnc` suffix means **no VNC server**. The VNC browser application itself is named **noVNC**.

```bash
./001b_build_px4_ros2_novnc_image.sh
./002b_run_px4_ros2_novnc_container.sh
```

Run from a graphical Linux terminal with a local X11/Xwayland `DISPLAY`. The launcher checks the socket and forwards a temporary Xauthority cookie; install `xauth` on the host if necessary. SSH/TCP display forwarding is unsupported. On WSLg, an absent Xauthority file can be normal, but WSLg has not been validated here.

Inside the container use the same setup/build/session commands. Gazebo and QGC open on your host display. The `003b`, `997b`, `998b`, `999b` scripts attach, stop and remove this mode's resources.

## Persistent layout

| Host path | Container path | Contents |
| --- | --- | --- |
| `Commands/bin` | `~/bin` | Developer helpers on PATH |
| `ExampleCode` | `~/ExampleCode` | PX4 walkthroughs |
| `Projects/PX4-Autopilot` | `~/Projects/PX4-Autopilot` | Pinned upstream Git checkout, edits, SITL build and parameter state |
| `Projects/ros2_workspace` | `~/Projects/ros2_workspace` | Authored examples, upstream messages and colcon outputs |
| `Data` | `~/Data` | QGC settings/cache, ULogs, bags, session logs and compiler cache |

`setup_px4_workspace` recursively fetches PX4 and its submodules and checks out `px4_msgs` at the locked revision. It preserves an existing matching checkout and edits. A different revision produces an error with guidance; setup never resets your work. If an initial network failure leaves an incomplete checkout, inspect/recover it explicitly before rerunning setup.

PX4 and px4_msgs are ignored nested upstream repositories. Commit environment scripts and authored examples in this repository; manage PX4 changes in its own Git checkout/fork. Build outputs live under `Projects`, so they survive container recreation too. Avoid sharing the same build directory between incompatible images or architectures.

Images include seed helper/example files outside mount locations for use without bind mounts. A fresh image-only workspace is initialized by the same setup command. Mounting a host folder intentionally makes the host files authoritative.

## Development and configuration

Edit PX4 source on the host or in container Vim. Stop SITL, run `build_px4_sitl` and restart it. Run `build_ros2_workspace` after ROS changes and source the install setup in the current shell. New interactive shells automatically source ROS and any existing workspace overlay.

`clean_and_rebuild_ros2_workspace` removes only this ROS workspace's generated `build`, `install` and `log` folders, rebuilds and sources the result. Sources are preserved. For PX4 clean builds, use the upstream build commands deliberately; no cleanup runs automatically on startup.

The tmux and Vim configuration files are copied from the reference. All declared plugins are installed during image build at revisions in `docker/plugins.lock`. tmux uses Nord and tmux-sensible; Vim retains Gruvbox, Airline and the original mappings/settings. Command-T uses its Vim-compatible Ruby release, with a Ruby-enabled Vim build. The Xfce terminal uses the supplied Cascadia Nerd Font.

Useful commands inside the container:

```bash
px4_doctor
BUILD_JOBS=4 build_px4_sitl
start_px4_dev --no-attach
start_px4_sitl --headless       # standalone; start the XRCE agent separately
start_micro_xrce_agent
start_qgroundcontrol
px4_command commander status
record_px4_rosbag
rviz2
glxinfo -B
```

`start_px4_sitl` uses an x500 with the RGB-D/lidar suite and the bundled `corda_campus` world. `PX4_GZ_WORLD` selects another bundled world. Parameters persist under `Projects/PX4-Autopilot/build/px4_sitl_default/rootfs/parameters.bson`; stop SITL and back up that file before any deliberate reset. Flight ULogs are linked into `Data/px4/logs`; ROS recordings go into `Data/bags`; tmux service output goes into timestamped `Data/sessions` directories. Use the installed `pyulog` tools for ULog inspection and `ros2 bag info/play` for ROS bags.

The world's geographic origin remains **50.951737° N, 5.352412° E**, with assumed flat ground at **50 m AMSL**. In the campus world, the actual drone starts on the Corda 1 roof at local East/North **(-85, -38) m**, approximately **50.9513954° N, 5.3512024° E**. The platform is about **23.56 m above ground**; the vehicle rests about **73.8 m AMSL**. These are approximate simulation coordinates, not a surveyed launch position. QGC discovers this actual vehicle/home location from PX4.

To relocate the entire world geographically, stop the session and supply all three origin values inside the container (the campus geometry and rooftop spawn retain their local offsets):

```bash
stop_px4_dev
PX4_HOME_LAT=50.951737 PX4_HOME_LON=5.352412 PX4_HOME_ALT=50 start_px4_dev
```

The same overrides work with standalone `start_px4_sitl`. Location changes require restarting SITL.

QGC configuration and cache use `Data/qgc`. To reset its settings, stop QGC and move that folder aside. QGC-selected mission export locations should be placed under `~/Data` or `~/Projects` to keep them across container removal.

Host-side overrides and extra arguments:

```bash
VNC_PW=secret VNC_RESOLUTION=1920x1080 WEB_PORT=6902 VNC_PORT=5902 \
  GPU_MODE=software ./002_run_px4_ros2_container.sh
BUILD_JOBS=2 build_px4_sitl  # inside container, for constrained hosts
./001b_build_px4_ros2_novnc_image.sh --build-arg USER_UID=1001 --build-arg USER_GID=1001
./002h_run_px4_ros2_headless_container.sh -- bash -lc 'px4_doctor'
```

Build scripts forward Docker build options. Run scripts accept Docker options before an optional `--`; words after `--` replace the container command. `GPU_MODE` accepts `auto`, `nvidia`, `dri`, or `software`. VNC acceleration depends on its X server; inspect the actual renderer rather than assuming GPU passthrough accelerates Xvnc. Classic VNC password authentication uses only the first eight characters. Use SSH tunnels for remote desktop access.

## Corda Campus world

The default `corda_campus` world contains **82 actual GRB building footprints**, with angled/concave outlines, rounded facades and courtyards preserved as triangulated meshes. Visual and collision geometry match. Corda 1, its companion, Corda 2 and Corda 3 have sloping wedge roofs; Corda Arena and nearby offices retain their mapped outlines. Other roofs are mostly flat. Corda 1/2/3 have separate green roof and blue-grey/light/warm-grey facade materials. Their roof slopes are approximated from campus references; full closed collision meshes match the combined visual surfaces.

Heights use available 3D GRB values matched by stable building IDs, architectural dimensions where available and explicit estimates for missing data. Corda 1's 30 m maximum comes from the architect; the detailed roof plane remains approximate. All sources, licences, data dates and approximation rules are documented in [tools/campus/SOURCES.md](tools/campus/SOURCES.md). The Arena now has a hollow roofed hall, glazed entrance, open simulation doors, simple internal galleries and projecting cube facade detail. The 35 m Philips water tower has open lattice supports, stairs and a saucer tank. Six traced parking areas have illustrative bay markings; Corda 4 and 5 have window bands. These are untextured approximations: detailed interiors, terrain, trees, cars and surveyed rooftop structures are omitted.

A **synthetic level 4×4 m launch platform** sits above Corda 1's sloping roof so the drone can stand and land stably. It is marked with an H; it is not a real helipad. The generator verifies the platform lies inside the roof footprint. The spawn is at approximately 50.9516471 N, 5.3522555 E. Footprints and the tower use native EPSG:3812 coordinates transformed locally, correcting an offset in the WFS geographic-coordinate response.

For an existing container/workspace, install the new assets and restart:

```bash
stop_px4_dev
build_ros2_workspace --packages-select px4_dev_examples
source ~/Projects/ros2_workspace/install/setup.bash
start_px4_dev --no-attach
# Verify the disarmed vehicle stays at the rooftop elevation:
ros2 run px4_dev_examples campus_check
```

`start_gazebo_gui` opens the normal Gazebo controls with a view of the campus landmarks and parking. It supplies the installed campus resource paths for meshes. The `sensors` window bridges the selected world's clock, so the existing RViz viewer also works in the campus.

To use the original empty world, stop the session and run `PX4_GZ_WORLD=default start_px4_dev`. To use campus geometry without rendered sensors, use `PX4_SENSOR_SUITE=none start_px4_dev`. `PX4_GZ_MODEL_POSE` can explicitly override the default local spawn (`x,y,z,roll,pitch,yaw` in metres/radians); ensure any alternative starts clear of buildings. An explicit world/pose override is forwarded to tmux even if its server was already running.

All world/model/mesh assets are local, so simulation needs no map download. Editable source footprints, height attributes and overrides are under `tools/campus`; generated assets and a per-building provenance report are installed under the ROS package's `simulation` directory. Regeneration is an optional offline GIS build step described in the source notes; ordinary Docker image builds just package the checked-in meshes. Software rendering and complex collisions can reduce simulation speed.

The integration check `bash /opt/px4-tests/campus.sh` starts and stops its own headless session, verifies rooftop support for several seconds and checks sensor payloads/TF. Run it only without an active development session. The ordinary opt-in offboard demo takes off relative to the rooftop and returns to the launch platform.

## RGB-D camera and 3D lidar

The default drone includes a forward-facing RGB-D camera tilted 10° downward and a roof-mounted 3D lidar. The authored model extends the pinned upstream x500 without editing its source or Gazebo model repository. It adds 70 g camera mass and 150 g lidar mass with fixed mounts and visible sensor housings.

| Sensor | Configuration | ROS 2 topics |
| --- | --- | --- |
| RGB-D | 320 × 240, 87° horizontal FOV, 0.15–20 m, 10 Hz simulation time | `/drone/rgbd/image`, `/drone/rgbd/depth_image`, `/drone/rgbd/camera_info`, `/drone/rgbd/points` |
| 3D lidar | 720 horizontal × 16 vertical samples, 360° × 30° FOV, 0.1–50 m, 10 Hz simulation time | `/drone/lidar/points` |

RGB uses `sensor_msgs/Image` with `rgb8`; depth uses `32FC1` in metres. Both clouds use `sensor_msgs/PointCloud2`. The lidar cloud contains all 16 vertical channels; it is not a single-plane LaserScan. Update rates are configured simulation rates; actual throughput depends on rendering hardware and subscribers.

After updating an existing checkout, rebuild the ROS package inside the container and restart the session:

```bash
stop_px4_dev
build_ros2_workspace --packages-select px4_dev_examples
source ~/Projects/ros2_workspace/install/setup.bash
start_px4_dev --no-attach
view_px4_sensors
# In another shell: check payloads, advancing stamps and TF; save optional previews:
ros2 run px4_dev_examples sensor_check --save ~/Data/evidence/sensors
```

The `sensors` tmux window runs `ros2 launch px4_dev_examples sensors.launch.py`. Standalone `start_px4_sitl` starts the model/server only; launch that bridge separately for ROS sensor topics. When choosing another world, give that bridge the matching `PX4_GZ_WORLD` environment value as well. The bridge uses best-effort sensor QoS and lazy subscriptions so unused streams avoid unnecessary transfers. For direct inspection, use `--qos-reliability best_effort`. Sensors also work without a display server using Gazebo's Ogre2 EGL headless rendering; software rendering can be slower.

`view_px4_sensors` opens the included RViz configuration with RGB/depth panels and both clouds. Its fixed frame is `base_link` (ROS FLU). Static TF connects that frame to `lidar_link`, `rgbd_link`, `rgbd_sensor` and `rgbd_optical_frame`; images, camera info and the RGB-D cloud use the optical frame (+Z forward, +X right, +Y down). This is a vehicle-relative view; no map/odometry TF, SLAM or obstacle-avoidance controller is provided. These sensors feed ROS perception and do not automatically change PX4 flight behaviour or stream camera video into QGC.

Sensor timestamps and `/clock` use Gazebo simulation time. The sensor launch bridges the selected world's clock; RViz uses `use_sim_time:=true`. Keep the existing PX4 offboard control nodes on their documented wall-time setup. Do not launch a second clock bridge at the same time.

To run without the rendered sensor suite, stop the session and use `PX4_SENSOR_SUITE=none start_px4_dev` (the campus world remains selected). The same selector works with standalone SITL. Sensor-free runs do not require the rendered sensor checks or publish these sensor topics. To record sensors alongside control telemetry, pass their topics explicitly, for example:

```bash
record_px4_rosbag /drone/rgbd/image /drone/rgbd/depth_image \
  /drone/rgbd/camera_info /drone/lidar/points /tf_static /clock
```

Camera/lidar definitions, bridge YAML and RViz settings live under `Projects/ros2_workspace/src/px4_dev_examples/{simulation,config,launch}`. Rebuild that package after asset/config changes. The integration check `bash /opt/px4-tests/sensors.sh` starts and stops its own headless session; run it only when no development session is active.

## Networking, ROS topics and time

Default Docker bridge networking works because all components run inside the same container:

| Path | Transport | Default endpoint |
| --- | --- | --- |
| PX4 client → Micro XRCE-DDS Agent | UDP | Container localhost:8888 |
| PX4 → QGroundControl | MAVLink/UDP | Container localhost:14550 |
| Agent ↔ ROS nodes | DDS | Common `ROS_DOMAIN_ID`, default 0; Fast DDS RMW |
| Browser → noVNC → VNC | HTTP/WebSocket + RFB | Host loopback 6901 / 5901 |

No XRCE/MAVLink host port is published by default. Running host-side QGC or ROS nodes requires explicit PX4 destination addressing, DDS discovery and appropriate network access; publishing a UDP port alone does not route outbound PX4 telemetry to a host application. This external topology is outside the verified baseline.

Message topics with a nonzero `MESSAGE_VERSION` have a `_vN` suffix. The provided nodes and bag recorder derive names from the installed definitions; `ros2 topic list` shows the actual names. Subscriptions use compatible best-effort QoS. Direct `ros2 topic echo` may need `--qos-reliability best_effort`.

The baseline control examples use system time in microseconds and PX4's normal XRCE synchronization. They do not enable `use_sim_time`. For sensor-free sessions, an optional visualization clock bridge is available via `ros2 launch px4_dev_examples clock.launch.py`; use it only for nodes configured for that clock. A full conversion of PX4/ROS control to Gazebo time requires coordinated PX4 synchronization settings and has not been validated here.

PX4 local positions use NED: positive X north, Y east, Z down. The demo sets a negative Z change for takeoff and does not interpret ROS ENU values as PX4 coordinates. ROS ENU → NED maps `(x,y,z)` to `(y,x,-z)`; body FLU → FRD flips Y and Z. For quaternion transforms, account for both world and body frames and ordering explicitly.

## Checks and troubleshooting

```bash
./tests/static.sh
./tests/image-smoke.sh px4_ros2_novnc:latest
./tests/desktop.sh
# Inside a built development container, with no other session/QGC running:
bash /opt/px4-tests/flight.sh
bash /opt/px4-tests/sensors.sh
bash /opt/px4-tests/campus.sh
```

The flight test starts headless SITL and a local test GCS heartbeat, then asserts arm/takeoff/hold/land/disarm. It does not replace the manual QGC visual/flight test. The CI image job is opt-in through workflow dispatch because full builds are large. See `docs/implementation-status.md` for actual results.

- **No ROS telemetry:** check XRCE agent logs, PX4 client startup, matching message definitions and `ROS_DOMAIN_ID`; inspect QoS and version suffixes. Use `px4_doctor`.
- **No QGC vehicle:** confirm PX4 is running and QGC's UDP autoconnect is enabled; another listener on 14550 can interfere. Host QGC requires a different routing setup.
- **Arm/mode rejected:** read command acknowledgements and PX4 preflight/failsafe messages. Wait for estimator readiness and QGC connection; do not disable safety checks globally.
- **Black/failed GUI:** inspect Qt/XCB diagnostics and `glxinfo -B`; try `GPU_MODE=software`, check Xauthority for native mode, or use VNC.
- **Stale build/version conflicts:** stop the session; review `versions.env`, source revisions and compiled workspace. A changed PX4 message schema requires a matching px4_msgs rebuild.
- **Permission errors:** check image UID/GID against host ownership. Rebuild with the right user IDs rather than running the environment as root.
- **Memory/disk pressure:** lower `BUILD_JOBS`, inspect generated builds/caches, and remove only reviewed disposable output. Lifecycle scripts never prune all Docker resources.
- **Desktop ports occupied:** use `WEB_PORT`/`VNC_PORT` overrides. This is also needed when running the reference environment alongside this one. Give concurrent PX4 simulations distinct `ROS_DOMAIN_ID` values to avoid mixing their identically named ROS topics.

Initial image/source setup requires internet. The bundled x500/default-world assets are local after recursive source setup; QGC maps and optional remote models can still require internet. Apt and transitive dependency versions are recorded in the image but are not repository-snapshot locked. Upgrade source pins, messages, agent and QGC together, rebuild both images/workspaces, and rerun integration tests before claiming the new combination supported.

## License

Environment code uses the [MIT license](LICENSE), retaining the reference project's attribution. Fonts retain their included license. PX4, px4_msgs, eProsima dependencies, QGroundControl and editor plugins retain their upstream licenses; their downloads/checkouts are separate from this repository's authored code. See [third-party notices](docs/third-party.md).
