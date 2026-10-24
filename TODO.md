# PX4 + ROS 2 Docker development environment — implementation TODO

Planning date: 2026-10-23. The Linux amd64 baseline has been implemented and exercised. Checked items have implementation or test evidence in `docs/implementation-status.md`; unchecked items retain specific follow-up scope. Optional platforms and expanded validation are not implied by a baseline pass.

## Objective and boundaries

Build a complete, reproducible single-vehicle PX4 SITL development environment containing modern Gazebo, QGroundControl (QGC), ROS 2, and a source workspace. Support both a browser/native-VNC desktop and native Linux X11/Xwayland graphics, plus headless simulation for tests. Preserve the reference repository's terminal experience, persistent folders, and numbered Bash build/run/attach/stop/remove workflow.

`../ROSLyricalDocker` is a **read-only reference**. Do all work in `PX4ROS2Docker`. Reference inspected at commit `da098840bada205c0a6187e857d2760dec9c7a16`; recheck its contents before copying selected files. Do not copy its Git history, generic ROS/OpenCV lessons, videos, tugbot worlds, or standalone drone model as a substitute for PX4 SITL. Do not change host drivers or services automatically.

The requested similarity is the development workflow and configuration. ROS 2 Lyrical is not a hard requirement. Proposed baseline: **Ubuntu 24.04 + ROS 2 Jazzy + Gazebo Harmonic**, subject to the compatibility gate below. Linux amd64 is the first fully supported target. ARM64 and Docker Desktop support require their own validation; never imply that a successful cross-build proves GUI or SITL support.

## Evidence and version decision

Official references checked during planning:

- [PX4 ROS 2 user guide](https://docs.px4.io/main/en/ros2/user_guide): currently recommends Jazzy on Ubuntu 24.04. Use this to inform the baseline, then check the chosen PX4 release's versioned documentation.
- [PX4 Gazebo simulation](https://docs.px4.io/main/en/sim_gazebo_gz/): reference for simulator targets and launch options.
- [PX4 uXRCE-DDS](https://docs.px4.io/main/en/middleware/uxrce_dds): reference for agent/client compatibility and transport configuration.
- [PX4 ROS 2 offboard example](https://docs.px4.io/main/en/ros2/offboard_control): reference for control-message sequencing and coordinate conventions.
- [Gazebo ROS installation](https://gazebosim.org/docs/harmonic/ros_installation/): reference for supported ROS/Gazebo pairings and package sources.
- [QGC installation](https://docs.qgroundcontrol.com/en/getting_started/download_and_install.html) and [QGC releases](https://github.com/mavlink/qgroundcontrol/releases): resolve an exact stable asset, architecture, runtime requirements, and checksum. The first link describes development builds; do not silently install its daily build.

These moving pages do not constitute a tested lockfile. Exact PX4, px4_msgs, agent, QGC and dependency revisions must be selected and tested in phase A. Do not mix Lyrical/Jetty packages into the baseline. An experimental Lyrical profile is optional follow-up work after the baseline passes.

## Intended architecture and contracts

One development container contains all components. Both GUI variants derive from the same toolchain stage. PX4 and Gazebo run locally; QGC connects to PX4 over MAVLink; ROS 2 connects through the Micro XRCE-DDS Agent. `ros_gz_bridge` is for Gazebo sensors/clock, not a replacement for the PX4 ROS transport. No MAVROS dependency is needed for the baseline.

| Contract | Proposed value / behavior |
| --- | --- |
| User | Non-root `user`, `/home/user`, build-time host UID/GID |
| Image targets | `native`, `vnc`, sharing the same tools and source pins |
| Image names | `px4_ros2_novnc:latest`, `px4_ros2_vnc:latest`; also emit immutable version tags |
| Container names | `px4_ros2_novnc`, `px4_ros2_vnc` |
| Default mode | Root unlettered scripts launch VNC; `c` aliases mean VNC; `b` means no VNC |
| Browser/VNC | Host loopback ports 6901/5901, overridable with `WEB_PORT`/`VNC_PORT` |
| Graphics | Native X11 cookie forwarding; VNC Xfce + TigerVNC + noVNC; explicit software fallback |
| Default network | Docker bridge; all simulation services in the same container |
| PX4 ↔ agent | Local UDP 8888 candidate; verify against pinned client/startup scripts |
| PX4 ↔ QGC | Local MAVLink UDP 14550 candidate; verify target and listener, not just port publication |
| DDS | Explicit common ROS domain and a tested RMW implementation |
| Source | `~/Projects/PX4-Autopilot`, `~/Projects/ros2_workspace` |
| Persistence | `Commands/bin → ~/bin`, `ExampleCode → ~/ExampleCode`, `Projects → ~/Projects`, `Data → ~/Data` |
| Process startup | Container opens shell/desktop; simulation starts only through explicit helpers |

The historical `novnc` image suffix means **without VNC**, whereas the browser desktop uses the noVNC application. Explain this prominently in README.

## Work assignment and completion rules

Each checkbox is a discrete task ID. Claim an entire phase or a bounded group of IDs before implementation. Record owner, branch/commit, decisions, verification commands, and failures in `docs/implementation-status.md`. Mark a task complete only with its deliverable and evidence. Do not claim unavailable GPU/GUI hardware tests passed; list them as pending.

| Work package | Suggested owner | Depends on | Main files owned |
| --- | --- | --- | --- |
| A: compatibility and contracts | Integration agent | None | `versions.env`, `docs/compatibility.md`, architecture decisions |
| B: base image and editor setup | Image agent | A | `Dockerfile`, installers, shell/editor configuration |
| C: sources and builds | Workspace agent | A; B for runtime checks | workspace bootstrap/build scripts, manifests |
| D: QGC and desktop | Desktop agent | A, B | QGC installer/launcher, VNC startup, desktop entries |
| E: host lifecycle | Launcher agent | A; B/D for integration | numbered scripts, mode directories, GPU/X11 helper |
| F: simulation orchestration | Simulation agent | C, D, E | simulation helpers, tmux session, network documentation |
| G: ROS demonstrations | ROS agent | C, F | ROS packages, launch/config files, PX4 examples |
| H: verification | Test agent | B–G | local validation scripts |
| I: documentation and acceptance | Integration agent | H | README, final status and evidence |

After A, source preparation and host launcher work can proceed alongside image work. Avoid concurrent edits to shared Dockerfile, version manifest, README, and this checklist; nominate one integration owner. These are suggested future assignments, not agents already dispatched.

## A — Resolve and prove the compatibility baseline

Exit gate: a documented version matrix and minimal PX4/ROS/QGC feasibility evidence, before broad implementation.

- [x] A01 Inventory both repositories, read applicable `AGENTS.md`, record clean/dirty status, and preserve existing user files. Confirm all writes target PX4ROS2Docker.
- [x] A02 Record the reference commit and selected file checksums; map inherited configuration versus PX4-specific replacements in `docs/reference-map.md`.
- [x] A03 Select a stable PX4 release and immutable commit; inspect its versioned Ubuntu, Gazebo and ROS instructions and its actual setup/startup scripts.
- [x] A04 Validate Ubuntu 24.04/Jazzy/Harmonic against that release. Document any package naming/repository discrepancy between PX4 and Gazebo docs and verify the chosen apt candidate versions.
- [x] A05 Select matching `px4_msgs` and, if used, `px4_ros_com` revisions. Verify message definitions against PX4's exported DDS topics. Do not assume arbitrary latest branches match.
- [x] A06 Pin a Micro XRCE-DDS Agent release compatible with the selected PX4 client; record protocol compatibility. Do not assume a new agent major release is interchangeable.
- [x] A07 Resolve a stable QGC release asset for amd64; record URL, SHA256, license, minimum runtime and PX4 compatibility. Treat ARM64 as a separate matrix entry.
- [x] A08 Create `versions.env` plus a source manifest with base image digest, OS/ROS/Gazebo choice, source SHAs, QGC checksum, Python constraints and plugin pins. No `latest` downloads or moving branches as build inputs.
- [x] A09 Prototype a minimal build/start for PX4 x500, a ROS telemetry subscription, and QGC under a display. Record commands and failures in `docs/compatibility.md`; resolve blockers before declaring the matrix supported.
- [x] A10 Freeze the naming, mount, network and helper contracts in this plan. Record any justified deviations so independently implemented scripts agree.

## B — Shared image, Bash, tmux and Vim

Exit gate: both image targets build; shell and plugin checks pass as the configured non-root user.

- [x] B01 Create `.gitignore` and `.dockerignore` excluding generated PX4 builds, colcon outputs, downloads, logs, bags, caches and local agent/credential directories. Keep authored workspace packages and build scripts in context.
- [x] B02 Implement a shared toolchain stage with `native` and `vnc` final targets. Keep apt/tool layers reusable across both modes.
- [x] B03 Install official signed ROS/Gazebo repositories and the selected package set; verify installed Gazebo major version and bridge compatibility. Avoid competing simulator package families.
- [x] B04 Install PX4 SITL compiler/build dependencies from the pinned release requirements: C/C++ tools, CMake, Ninja, Python tooling, ccache and debugging utilities. Audit upstream setup scripts before using them in Docker.
- [x] B05 Isolate PX4 Python requirements in a pinned environment that can access required system ROS packages, or document a tested alternative. Verify ROS Python imports and PX4 generation together; do not bypass externally-managed Python restrictions blindly.
- [x] B06 Install ROS desktop/RViz, colcon/rosdep tooling and transport dependencies. Resolve rosdep for the actual workspace; omit Nav2, TurtleBot and OpenCV teaching dependencies unless a PX4 feature needs them.
- [x] B07 Retain useful reference tools: git, vim, tmux, nano, htop, sudo, wget/curl, bash-completion, universal-ctags, Mesa diagnostics, ping and xauth. Add transport diagnostics as needed.
- [x] B08 Create `/home/user` using caller UID/GID build args; handle preexisting Ubuntu user/group collisions. Reject UID/GID zero and keep build/run artifacts user-owned.
- [x] B09 Copy the reference `docker/tmux.conf`, `docker/vimrc`, Nerd Fonts/license and Xfce terminal settings without stylistic changes; record attribution and compare checksums.
- [x] B10 Adapt `install-user-config.sh` to install TPM, Nord, tmux-sensible, Vundle and every declared Vim plugin. Pin fetched revisions; check actual plugin load and any native plugin build requirements, not just clone directories.
- [x] B11 Adapt Bash setup: `~/bin`, local PATH, `ll`, colcon completion, selected ROS distro, optional workspace overlay and current-shell rebuild function. Guard missing overlays; avoid duplicate sourcing on repeated shell startup.
- [x] B12 Implement an entrypoint that sources ROS/overlay and `exec`s the requested command. Test interactive attach, noninteractive commands and desktop startup. Never auto-arm or auto-start SITL in shell initialization.
- [x] B13 Preserve writable RViz initial settings and existing user settings. Install process reaping/signal handling for both final targets.
- [x] B14 Record build metadata/package inventory inside the image. Document which apt dependencies are fixed versus updateable; do not claim bit-identical rebuilds without an apt snapshot strategy.

## C — Persistent source workspace and development builds

Exit gate: a fresh checkout can populate sources and rebuild PX4 and ROS as the ordinary user without losing edits.

- [x] C01 Create tracked `Commands/bin`, `ExampleCode`, `Projects/ros2_workspace/src`, and `Data/.gitkeep`; ensure empty host bind mounts cannot hide the only source copy.
- [x] C02 Choose a source-seeding mechanism: immutable seed outside mount paths plus explicit `setup_px4_workspace` copying/cloning into mounted Projects. Support unmounted image use as well.
- [x] C03 Implement idempotent PX4 checkout at the locked commit with recursive submodules; verify submodule completeness. Never reset, clean or overwrite a dirty existing checkout.
- [x] C04 Populate matching `px4_msgs` and optional `px4_ros_com` from the manifest; distinguish fetched upstream checkouts from authored tracked packages.
- [x] C05 Implement `build_px4_sitl` with configurable bounded parallel jobs and ccache. Document compiler/debug configuration, output binary and rebuild cycle.
- [x] C06 Implement `build_ros2_workspace` using `colcon build --symlink-install` and explicit underlay sourcing. Ensure fresh shells find the resulting overlay.
- [x] C07 Adapt the clean/rebuild helper to remove only this workspace's build/install/log directories; reject missing, root or unexpected target paths and preserve sources.
- [x] C08 Persist PX4 parameters, ULogs, QGC settings/missions, ROS bags and useful caches under documented persistent Projects/Data paths. Verify actual application paths instead of merely creating unused folders.
- [x] C09 Separate disposable build caches from user data. Document source upgrades, compatible message rebuilds and explicit parameter reset; startup must not silently upgrade dependencies.
- [x] C10 Verify host ownership after setup, compilation, recording and shutdown. Avoid recurring broad recursive chown operations.
- [x] C11 Prefetch the baseline world's required models or document an explicit preparation step. Prove a prepared baseline simulation can start without fetching remote Fuel assets.

## D — QGroundControl and remote desktop

Exit gate: QGC and Gazebo render inside VNC and native display sessions and QGC settings survive container removal.

- [x] D01 Add a checksum-verified QGC installer using the locked release. Extract AppImage during build and launch its AppRun where supported, avoiding runtime FUSE/privileged-container requirements.
- [x] D02 Install and verify QGC's actual Qt/XCB/OpenGL/multimedia dependencies; inspect unresolved shared libraries and launch diagnostics for the selected release.
- [x] D03 Add `start_qgroundcontrol`, a desktop launcher and PATH integration; run as `user` and preserve supplied arguments and meaningful exit codes.
- [x] D04 Configure persistent QGC settings, missions and logs without hiding bundled application resources. Document first-launch behavior and reset procedure.
- [x] D05 Port Xfce + TigerVNC + noVNC + websockify and the reference font/terminal configuration. Retain `VNC_PW`, `VNC_RESOLUTION`, localhost host bindings and documented password-length behavior.
- [x] D06 Port D-Bus session setup, X readiness checks, private runtime directory, signal forwarding and child cleanup. Make desktop/service startup failures observable and nonzero.
- [x] D07 Test Gazebo and QGC simultaneously in the VNC desktop, including Qt/OpenGL failure diagnostics and software rendering. Record actual renderer; GPU passthrough is not proof of accelerated Xvnc rendering.
- [x] D08 Verify local QGC receives live PX4 vehicle state and can perform the baseline simulated flight. Capture visible evidence; a running QGC PID alone is insufficient.

## E — Host Bash lifecycle and graphics

Exit gate: every numbered wrapper works from an unrelated working directory, with correct names and persistent mounts.

Create this exact root command family (unless A10 records a replacement):

| Action | Default VNC | Native/no VNC | Explicit VNC alias |
| --- | --- | --- | --- |
| Build | `001_build_px4_ros2_image.sh` | `001b_build_px4_ros2_novnc_image.sh` | `001c_build_px4_ros2_vnc_image.sh` |
| Run | `002_run_px4_ros2_container.sh` | `002b_run_px4_ros2_novnc_container.sh` | `002c_run_px4_ros2_vnc_container.sh` |
| Attach | `003_attach_bash_to_px4_ros2_container.sh` | `003b_attach_bash_to_px4_ros2_novnc_container.sh` | `003c_attach_bash_to_px4_ros2_vnc_container.sh` |
| Stop | `997_stop_px4_ros2_container.sh` | `997b_stop_px4_ros2_novnc_container.sh` | `997c_stop_px4_ros2_vnc_container.sh` |
| Remove container | `998_remove_px4_ros2_container.sh` | `998b_remove_px4_ros2_novnc_container.sh` | `998c_remove_px4_ros2_vnc_container.sh` |
| Remove image | `999_remove_px4_ros2_image.sh` | `999b_remove_px4_ros2_novnc_image.sh` | `999c_remove_px4_ros2_vnc_image.sh` |

- [x] E01 Implement underlying `px4_ros2_vnc_image/` and `px4_ros2_novnc_image/` scripts: `01_build_image.sh`, `02_run_container.sh`, `03_attach_bash.sh`, `97_stop_container.sh`, `98_remove_container.sh`, `99_remove_image.sh`. Root scripts delegate with arguments intact.
- [x] E02 Resolve paths from `BASH_SOURCE`; use quoted Bash arrays, strict error handling and executable bits. Test a checkout path containing spaces.
- [x] E03 Forward build options and host UID/GID; forward run options before the image. Document how to supply container command arguments separately if supported.
- [x] E04 Preserve foreground `--rm -it` usage and distinct mode names. Ensure stop/remove/image-remove target only this project's resources; never prune Docker globally or delete Data/Projects.
- [x] E05 Create required bind directories as the host user before Docker starts. Share the four reference mount locations and configure sufficient shared memory.
- [x] E06 Validate Docker availability, daemon access, name conflicts and host port collisions with actionable messages. Document concurrent use with ROSLyricalDocker and alternate desktop ports.
- [x] E07 Implement native Linux local X11/Xwayland socket validation, scoped temporary Xauthority forwarding and cleanup. Do not use blanket `xhost +`; reject unsupported remote DISPLAY values.
- [x] E08 Consolidate GPU selection for both modes; support explicit `auto`, NVIDIA, DRI and software choices. Preserve numeric render-device group access and useful diagnostics when the NVIDIA runtime is absent.
- [x] E09 Avoid privileged mode, host PID namespace and unnecessary devices. QGC extracted execution should not need FUSE; hardware USB/serial passthrough is outside baseline SITL.
- [x] E10 No `setup_nvidia_docker.sh` is retained. Host NVIDIA toolkit setup is a documented external prerequisite and never runs from build/run scripts.
- [x] E11 Add a headless entry point that requires neither DISPLAY nor desktop ports; make it usable without TTY for local automated tests.

## F — SITL launch, process lifecycle and communications

Exit gate: one explicit command starts a usable session; stop/restart leaves no orphan processes or stale ports.

- [x] F01 Implement `start_px4_sitl` for the pinned release's x500 target (candidate `make px4_sitl gz_x500`); validate model/world arguments and working directory.
- [x] F02 Implement a headless mode using supported pinned-release options; avoid launching a second Gazebo server accidentally. Check simulator time advances and vehicle is spawned.
- [x] F03 Build/install the locked agent and add `start_micro_xrce_agent`; candidate command `MicroXRCEAgent udp4 -p 8888`. Expose validated port configuration and preserve diagnostics.
- [x] F04 Add `start_px4_dev` using a named tmux session with agent, PX4 console/Gazebo, ROS diagnostics and QGC panes/windows. Preserve the inherited tmux theme and key behavior.
- [x] F05 Implement bounded readiness checks and startup ordering: agent available, simulator/vehicle ready, telemetry flowing. Replace fixed long sleeps with observable conditions.
- [x] F06 Track session-owned process groups or tmux panes. Implement `stop_px4_dev` without global `killall`; propagate interrupts and clean up partial startup failures.
- [x] F07 Handle an already-running session explicitly: attach or fail helpfully; do not start duplicate agents, simulators or QGC listeners.
- [x] F08 Document the port/direction/protocol table and verify the actual PX4 MAVLink destination is the QGC listener. Keep 8888 and 14550 internal for the default same-container topology.
- [x] F09 Select a tested DDS RMW/domain configuration, including the PX4 client's domain setting. Verify QoS with actual subscriptions, not only topic discovery.
- [x] F10 Document optional host-side QGC/ROS networking separately. UDP publication alone does not redirect PX4 outbound traffic; provide an explicit destination route and tests if this option is implemented.
- [x] F11 Select one coherent time policy for baseline ROS control. If using Gazebo `/clock`, bridge it, configure participating nodes and PX4 time synchronization consistently for the pinned release. Test timestamp units and pause/resume behavior.
- [x] F12 Add `px4_doctor` to report versions, source revisions, permissions, renderer, process state, ports, ROS domain/RMW, topic freshness and log locations without changing configuration.

## G — PX4-focused ROS workspace and examples

Exit gate: ROS receives telemetry and executes a complete, observable simulated offboard flight.

- [x] G01 Add an authored ROS package such as `px4_dev_examples` with package metadata, declared dependencies, launch files, README and license. Keep it distinct from fetched upstream packages.
- [x] G02 Implement a telemetry example subscribing to selected `/fmu/out` topics using compatible QoS; print timestamp, vehicle status and position with units/frame labels.
- [x] G03 Implement an explicit simulation-only offboard demo: wait for estimator readiness, stream required control messages, request mode/arm, verify acknowledgements/state, take off, hold, land and confirm disarm.
- [x] G04 Handle rejected commands, stale telemetry, startup timeouts and loss of the offboard stream. Bound the mission duration and provide a documented interruption/landing path.
- [x] G05 Document and test PX4 NED/FRD versus ROS ENU/FLU conventions, quaternion ordering and timestamp units. Do not pass ROS coordinates directly into PX4 fields without conversion.
- [x] G06 Keep flight-triggering demos opt-in. Do not weaken PX4 safety parameters globally to make an example pass; document any simulation-specific parameter changes and reset behavior.
- [x] G07 Add a launch/config example for Gazebo-to-ROS sensor bridging and RViz if the selected model provides sensors. Verify topic names/types, frame IDs and clock settings against that model. Implemented RGB-D + 16-channel 3D lidar with payload/TF checks and display-free EGL validation.
- [x] G08 Add `record_px4_rosbag` with explicit topic selection and persistent output; document PX4 ULog collection and replay/inspection basics.
- [x] G09 Replace the reference lesson content with concise PX4 walkthroughs: telemetry, QGC flight, ROS offboard flight, modifying/rebuilding PX4, and adding a ROS node. Do not import unrelated teaching assets.

## H — Local verification

Exit gate: reproducible automated evidence plus manual evidence for supported graphical modes.

- [x] H01 Add static checks for shell syntax/ShellCheck, manifest completeness and Dockerfile linting; resolve findings or record narrowly justified exceptions.
- [ ] H02 Build both targets from a fresh checkout. Record build duration, image size, peak resource needs and exact pins; repeat a cached build to confirm useful layer reuse.
- [x] H03 Add image smoke checks for versions, non-root identity, ROS imports, PX4 toolchain, Gazebo, QGC libraries, tmux plugin loading and full Vim configuration startup.
- [ ] H04 Test source initialization twice, dirty-checkout preservation, recursive submodules and a fresh PX4/colcon build with bind mounts. Also test image-only use without host mounts.
- [x] H05 Automate headless SITL with deadlines and log capture. Assert model spawn, advancing simulation, agent connection and fresh ROS telemetry, not just process existence.
- [x] H06 Automate the simulation-only offboard mission and assert observed arm, altitude/hold, landing and disarm states. On failure preserve PX4/agent/ROS logs and clean up session-owned processes.
- [x] H07 Check VNC RFB handshake, noVNC HTTP page, WebSocket upgrade and live Xfce session. Separately inspect real QGC/Gazebo windows and renderer behavior.
- [x] H08 Manually validate native X11/Xwayland with a valid cookie; exercise missing DISPLAY/cookie and software-render fallback diagnostics.
- [ ] H09 Test container stop during simulation, unexpected agent/simulator exit, restart and repeated launch. Confirm cleanup, nonzero failure reporting and no stale ports.
- [x] H10 Test persistence through container removal/recreation: edited PX4/ROS source, settings, flight logs and bags remain intact and host-owned.
- [ ] H11 Test every lifecycle alias from outside the repo and from a path with spaces; test extra Docker argument handling, conflicting names/ports and unavailable daemon.
- [x] H12 Verify coexistence with ROSLyricalDocker using alternate desktop ports and independent names; confirm reference repository status/checksums are unchanged.
- [x] H13 Provide local static/image/headless checks with bounded runtimes and failure artifacts. GitHub Actions is intentionally not used; GUI/GPU checks remain an explicit manual matrix.
- [x] H14 Test offline runtime after preparation; distinguish required online build/model setup from optional QGC map tiles. Document any remaining network dependency.
- [x] H15 Publish a tested host/architecture/rendering matrix. Validate ARM64 and Docker Desktop separately if claiming support; otherwise clearly scope baseline to Linux amd64.

## I — User documentation and final acceptance

- [x] I01 Write README with prerequisites and measured resource guidance, build/run/attach examples for both modes, desktop URL, VNC options and the historical `novnc` naming explanation.
- [x] I02 Give an exact fresh-clone walkthrough: build image → run container → initialize workspace → build PX4/ROS → start session → see vehicle in QGC → inspect ROS telemetry → execute opt-in offboard demo → stop.
- [x] I03 Document all helper commands, environment overrides, mounts, source/version upgrade procedure and which steps require internet.
- [x] I04 Document everyday development: modify PX4 C++, rebuild/restart SITL, modify a ROS package, rebuild/source overlay, use tmux/Vim, inspect ULogs/bags and reset only selected simulation state.
- [x] I05 Add troubleshooting for apt/version mismatch, stale px4_msgs, incompatible agent, DDS QoS/domain, missing QGC heartbeat, Qt/XCB failures, black Gazebo windows, Xauthority, ownership and insufficient memory/disk.
- [x] I06 Preserve third-party licenses and font/config attribution; distinguish repository-owned examples from downloaded upstream sources and binaries.
- [ ] I07 Have an agent other than the implementer follow the README from a clean checkout. Record deviations and fix the commands/documentation before completion.
- [x] I08 Attach final verification evidence and remaining platform limitations to `docs/implementation-status.md`; leave genuinely untested tasks unchecked.

## Definition of done

A user can clone PX4ROS2Docker, build and run either GUI variant through familiar numbered scripts, initialize persistent sources, edit and rebuild PX4 and ROS code, start x500 SITL, see Gazebo and QGC, receive PX4 telemetry in ROS 2, complete a takeoff/hold/land offboard demonstration, and stop/recreate the container without losing work. Bash, tmux, Vim and terminal appearance match the inspected reference configuration. Headless integration checks pass, supported graphical modes have visual evidence, exact dependency choices are recorded, and ROSLyricalDocker remains unchanged.

Optional work after baseline acceptance: experimental Lyrical/Jetty, multi-vehicle simulation, custom airframes/worlds, external ROS networking, ARM64 expansion, firmware flashing/HITL, joystick/video integration and PX4 ROS 2 control-interface-library examples. Do not let these defer the baseline acceptance gates.

## J — Corda Campus world (2026-10-24)

- [x] J01 Acquire and attribute current GRB building outlines and exact-ID 3D GRB heights; retain source snapshots and mark estimated heights.
- [x] J02 Generate watertight static collision/visual meshes preserving concave outlines, curves and courtyards; add approximated Corda 1 wedge roofs.
- [x] J03 Place a clearly synthetic level launch platform inside Corda 1's actual roof footprint and verify stable disarmed support.
- [x] J04 Integrate the default campus world, alternate empty world, pose overrides, GUI resource paths and selected-world sensor clock.
- [x] J05 Validate rendered sensor payloads and a full rooftop takeoff/hold/landing/disarm; verify offline and sensor-free compatibility.
- [x] J06 Provide reproducible source refresh/regeneration tools, data/GUI licences, documentation and a Gazebo scene screenshot.

- [x] J07 Correct WFS datum conversion using native EPSG:3812; validate against independent map imagery and move the roof spawn with its building.
- [x] J08 Replace the Arena extrusion with a roofed hollow shell, glazed facade, open simulation entrance and schematic galleries.
- [x] J09 Add the mapped Philips water tower, traced parking areas, bay markings and Corda 4/5 facade bands; verify geometry and sensor output.

- [x] J10 Omit distant small buildings, batch static visuals while retaining collisions, and add a QGC/sensors mode without the Gazebo GUI.
- [x] J11 Add the Corda 8 sawtooth roof and separate Corda 5 office wings, curved hall and entrance drum; extend geometry regression checks.

- [x] J12 Replace the simple launch slab/posts with a chamfered rooftop landing deck, continuous support plinth and flush markings; keep the flight area unobstructed.
