# Implementation status

Implemented 2026-10-23 by this Codex chat. Changes are local; no commit or publication was requested. `ROSLyricalDocker` remains unchanged.

## Usable baseline

Linux amd64 with Ubuntu 24.04, ROS 2 Jazzy, Gazebo Harmonic, PX4 v1.17.0, matching px4_msgs, XRCE Agent v2.4.3 and QGC v5.1.5. Both native and VNC images build. PX4 source and compiled outputs are in host `Projects/PX4-Autopilot`; ROS source/build outputs are in `Projects/ros2_workspace`.

Implemented: numbered build/run/attach/stop/remove wrappers; persistent mounts; UID/GID mapping; scoped Xauthority forwarding; software/NVIDIA/DRI selection; pinned editor configuration; source setup that preserves edits; PX4/ROS rebuild helpers; agent, simulator, GUI and QGC orchestration in tmux; telemetry, opt-in flight, interruption recovery, bag recording and diagnostics; local static/image/desktop/flight tests.

## Verification evidence

Evidence logs/screenshots are under ignored `Data/evidence/`, with raw service output under `Data/sessions/`.

| Check | Result |
| --- | --- |
| Shell syntax and authored Python parsing | Pass |
| Dockerfile Hadolint | Pass; apt/Python version warnings reflect the documented update policy; runtime HOME expansion is documented inline |
| ShellCheck at warning/error level | Pass; SC1091 excluded for image-only/dynamic source files |
| Native + VNC image builds | Pass, including cached rebuilds and numbered wrappers invoked from `/tmp` |
| Source initialization | All recursive submodules populated at recorded commits; rerun preserved an intentional tracked PX4 edit |
| Source/schema compatibility | All seven control/telemetry message schemas match firmware exactly |
| Reference configuration | Nine copied config/font files match byte for byte; checksums in reference-checksums.sha256 |
| PX4 + Gazebo plugin build | Pass as UID/GID 1000; release metadata reports v1.17.0 |
| ROS workspace | px4_msgs and px4_dev_examples compile; first message build took 7 min 17 s on this host |
| Image smoke | Pass: user permissions, ROS/Python imports, NumPy 1.26, agent, Vim, tmux and RViz settings |
| Python compatibility | ROS cv_bridge/OpenCV load against NumPy 1.26.4; pip check reports no broken requirements |
| VNC/noVNC | RFB handshake, HTTP page, WebSocket upgrade and Xfce session pass |
| QGC desktop | Runs as ordinary user; live vehicle connection visually verified |
| Corda Campus origin | Default 50.951737 N / 5.352412 E, assumed 50 m AMSL; verified PX4 global/home position, fresh ROS telemetry and QGC Ready / Hold on the campus map. Evidence: corda-campus.log and qgroundcontrol-corda-campus.png |
| Headless flight | Pass: observed arm, takeoff to 3 m, hold, land and disarm, with session cleanup |
| Graphical flight with QGC | Pass; real QGC supplies the GCS connection; complete flight returns to Ready / Hold |
| Interrupted flight | SIGINT during airborne hold caused landing and observed disarm; expected timeout exit 124 / node interrupt exit 130 |
| Gazebo scene | x500 visible and moving; GUI attaches after vehicle readiness to avoid its initial empty snapshot |
| Native graphics | Local Xwayland cookie forwarded; Mesa llvmpipe OpenGL 4.5; RViz launched and exited cleanly |
| Bash initialization | Repeated sourcing preserves PATH and keeps the alias/rebuild function available |
| Native negative cases | Missing DISPLAY and an empty Xauthority cookie produce clear failures |
| Docker negative cases | Unavailable daemon, occupied container name and occupied desktop ports fail clearly |
| Coexistence | Reference desktop image and PX4 desktop respond on separate localhost ports; reference source is never mounted or changed |
| Pause/resume | Gazebo reports paused state and fresh ROS telemetry returns after resume |
| Stop/restart | Processes removed; immediate stop/run tested; stop wrapper waits for Docker automatic removal to release the name |
| Offline operation | Full flight passes with `--network none`; bundled x500/world need no online assets |
| ROS bag | MCAP bag contains 342 position, 16 status and 1 command acknowledgement messages on the correct versioned topics |

## Decisions and fixes

- Use Noble/Jazzy/Harmonic rather than inherit Lyrical/Jetty: the selected stable PX4 release explicitly supports this baseline.
- Keep source, build directories and `rootfs/parameters.bson` under Projects. ULogs, bags, QGC settings/Documents/cache, Gazebo cache, session logs and ccache persist under Data. This preserves upstream PX4's working layout.
- Reuse ROS Jazzy's Fast DDS/CDR libraries for the XRCE agent instead of installing duplicate middleware libraries.
- Extract QGC at image build time and make its root-owned extraction directory readable/executable by the non-root user. Runtime FUSE and privileged mode are unnecessary.
- Constrain NumPy/Pandas to preserve compatibility with Ubuntu's ROS/OpenCV binary extensions.
- Start Gazebo's GUI only after the x500 and ROS telemetry are ready. PX4 retains its interactive console in graphical sessions, and GUI output has a separate log.
- Keep the ROS context alive during interruption so recovery can send a land command. After disarm, explicitly select Hold so a stopped offboard stream does not leave QGC in Not Ready.
- Resolve bag topic names from the compiled message versions, including `_v1` suffixes.
- Wait for Docker automatic removal in the host stop wrapper so immediate restarts do not race container-name cleanup.
- Guard repeated Bash sourcing and avoid adding duplicate tool paths.
- Pin Command-T's Vim-compatible 7.x branch and use Ruby-enabled vim-nox. The current main branch requires Neovim. Compile and explicitly load the native matcher during the image build while preserving the original vimrc.

## Follow-up scope

Unchecked TODO entries are expanded validation or optional features; their completion is not implied by baseline checks. Hardware GPU acceleration (NVIDIA/Intel/AMD), ARM64, Docker Desktop, every destructive lifecycle alias, injected component crashes, image-only source population, an independent reviewer walkthrough and measured peak build resources remain unverified.

Full Gazebo-time flight control, external host QGC/ROS routing, multi-vehicle, firmware flashing/HITL and experimental Lyrical/Jetty remain extensions. QGC text-to-speech has no configured speech backend; its visual vehicle/flight functions are verified. Apt and some transitive dependency versions evolve; package and Python inventories are recorded inside the images rather than claiming a bit-identical snapshot.

The final VNC container was recreated from the finished image and successfully reused the compiled firmware and ROS workspace. PX4 reports Release 1.17.0, valid telemetry flows, the recorded bag remains present, QGC retains its saved preferences/window state, and its live view shows Ready / Hold. The running desktop is available on localhost:6901; the user-facing browser tab is left connected. See tested-platforms.md for the support matrix.

Final source checks, Hadolint, image smoke checks and the VNC/QGC endpoint test pass. Verification details and exact image IDs are in Data/evidence. The repository has no newly created commit; review/commit/push remain user actions.

## Runtime recovery follow-up

A running session later lost fresh ROS and QGC telemetry while its processes remained alive. Gazebo world time continued, but PX4 reported stale MAVLink counters and IMU timestamp errors. The disarmed session was restarted, restoring fresh telemetry and QGC Ready / Hold. The underlying trigger has not been established; this recovery does not establish a permanent fix for long-running stalls. If it recurs, retain `Data/sessions` logs and restart with `stop_px4_dev` followed by `start_px4_dev` once the vehicle is safely disarmed.

## RGB-D and 3D lidar addition (2026-10-24)

The default x500 now includes an authored 320×240/10 Hz RGB-D camera and a 720×16/10 Hz 3D lidar. These are generic simulated sensors, not a claim of calibration to specific hardware. Their combined 220 g mass and mounts are included in the dynamics. The inherited upstream PX4 and Gazebo checkouts remain clean.

The `sensors` tmux window bridges RGB, floating-point depth, camera info and both clouds using lazy best-effort subscriptions. Static TF covers body, camera optical and lidar frames. A world-specific clock bridge supports RViz simulation time without changing PX4 control time. Sensor-enabled startup checks advancing timestamps, dimensions, finite depth/3D returns and TF before declaring readiness. `PX4_SENSOR_SUITE=none` preserves the lighter original x500 path.

Verified locally on Linux amd64 with software rendering:

- Payload/TF check passed: RGB-D images/cloud are 320×240 in `rgbd_optical_frame`; lidar cloud is 720×16 in `lidar_link`, with finite ground returns and nonzero vertical spread. Camera info dimensions/intrinsics match the images.
- Sensor-free selection passed with fresh ROS telemetry and no sensor bridge window: `Data/evidence/sensors-free.log`.
- EGL headless rendering passed with no DISPLAY and no network in the native container: `Data/evidence/sensors-headless.log`; RGB/depth previews and JSON under `Data/evidence/sensors/`.
- With RViz subscribed to the sensor streams and real QGC connected, PX4 armed, took off 3 m, held, landed/disarmed and restored Hold: `Data/evidence/sensors-final-flight.log`.
- RViz started with Mesa OpenGL 4.5 and the prepared configuration; `/clock` publication was checked. Cloud/image subscriptions and simulation-time configuration were verified; the viewer layout was not visually inspected during this follow-up.
- Native and VNC images rebuilt with the new helpers, seed assets and tests. Headless payload validation uses the mounted workspace. Full image-only source setup remains an existing deferred check.

Configured sensor rates use simulation time; no hardware-performance guarantee is made. These are perception outputs, with no SLAM, autonomous avoidance or QGC video pipeline included. Long-running telemetry stalls noted above remain unresolved.

An initial 640×480/15 Hz RGB-D preset was too expensive with both point-cloud displays active on software rendering. The default was reduced to 320×240/10 Hz before final validation. Hardware rendering and sustained real-time performance remain platform-dependent.

The final VNC container was recreated from the updated image after validation, then started with the sensor suite and RViz viewer. Final startup evidence: `Data/evidence/sensors-ready.log`; runtime health: `Data/evidence/sensors-final-health.log`.

## Corda Campus world (2026-10-24)

The default world is now `corda_campus`: 29 runtime buildings from 82 mapped GRB building footprints, with actual concave/angled/rounded outlines and outdoor courtyards. Binary STL meshes have explicit normals and matching static collision/visual geometry. Each nested building is explicitly static for physics performance. Corda 1, its companion, Corda 2 and Corda 3 have approximated sloping wedge roofs; Corda 1's maximum is 30 m per its architect. Corda 1/2/3 have separate green roof and blue-grey/light/warm-grey facade materials. Their roof slopes are approximated from campus references; full closed collision meshes match the combined visual surfaces. Current GRB outlines include Corda Arena; its 24 m height follows the campus masterplan.

The full source height snapshot contains 48 positive exact-ID 3D GRB matches; architectural constraints, visual overrides and generic fallbacks for the retained runtime buildings are recorded individually in campus.json. The ID-based source refresh recovered ten usable heights outside the older geometry-based download. Every source/estimate is recorded in the generated `simulation/campus.json`. Height attributes use stable-ID joins independently of footprint geometry; the native-grid correction below resolves the earlier geographic-coordinate mismatch. No erroneous spatial height transfer is applied. `tools/campus/SOURCES.md` details data dates, attribution and accuracy limits; its attribution is also installed inside the campus model.

The original approximate GPS point was east of Corda 1. The default spawn is now on its actual footprint, at local East/North (-11,-10) m, approximately 50.9516471 N / 5.3522555 E. A synthetic 6×6 m chamfered landing deck sits above the sloping roof. Its top is 23.974 m above assumed ground; the disarmed vehicle rests around 74.214 m AMSL with the retained 50 m ground datum. Terrain and detailed roof geometry are not surveyed. The launch platform is not a real campus helipad.

Verified on Linux amd64/software rendering:

- Generator verifies watertight topology and cap area, preserving footprint holes. Regeneration into a separate folder matches the packaged assets byte for byte without network: `campus-regenerate.log`.
- Rooftop support check: eight seconds of disarmed global position at the expected elevation, roughly centimetre-scale position variation: `campus-start.log` and `campus-after-flight.log`.
- RGB-D images/depth and both point clouds return actual world surfaces with matching TF: `Data/evidence/campus-sensors/`.
- Full QGC-connected offboard takeoff 3 m above the rooftop, hold, landing/disarm and restored Hold passed: `campus-flight.log`.
- Campus GUI inspected through noVNC: curved/angled buildings, courtyards, wedge roof and launch pad visible. Screenshot: `corda-campus-world.png`.

The source fetcher downloads into a new review directory; it never silently replaces accepted inputs. GIS dependencies are isolated from ROS and needed only to regenerate assets. Runtime meshes and data attribution are bundled for offline operation. A failed startup's cleanup is now scoped to its own run marker so an old readiness waiter cannot destroy a replacement tmux session. Explicit world/pose overrides are forwarded into tmux, and absent overrides clear stale inherited values.

Additional campus checks: source refresh fetched the same 82 footprints and 50 exact-ID height records into a separate review directory (`campus-fetch.log`); ten additional positive heights were reviewed and accepted, reducing generic estimates. Final campus and sensor-free campus checks passed with network disabled, and the original empty/sensor-free world still supplies fresh ROS telemetry (`campus-offline.log`). A final sensor/roof check after the peripheral height refinements is recorded in `campus-final-offline.log`. Both native and VNC images include the local world and installed attribution. The reference repository and nested PX4/Gazebo source checkouts remain unchanged.

Final delivery: recreated the VNC container from the updated image and started the default campus session. `campus-ready.log` confirms stable rooftop support, with fresh ROS telemetry and QGC Ready / Hold. The noVNC view is left on Gazebo; `corda-campus-world.png` captures the final scene. `ROSLyricalDocker` and the fetched PX4/Gazebo repositories remain unchanged. No commit or push was made.

Corda 2/3 roof correction and facade colours: offline regeneration, exact visual/collision triangle comparison, stable rooftop support and live RGB-D/lidar checks passed (`campus-colours-regenerate.log`, `campus-colours-check.log`). Both images were rebuilt with the separated roof/facade meshes.

Campus landmark refinement: Corda Arena is now a hollow roofed shell with collision walls, visually transparent but colliding glazing, an 8 m open simulation entrance, three schematic gallery levels and cube facade ornament based on current official renders. The construction-stage survey hole is no longer treated as an outdoor courtyard. The Philips water tower has four lattice legs, cross-braces, spiral treads and a closed saucer tank; six orthophoto-traced parking areas use illustrative bay markings. Corda 4/5 have pale facades and horizontal window bands.

The orthophoto comparison exposed the source of the earlier geometry offset: the WFS CRS84 output disagrees with native EPSG:3812 and EPSG:3857 responses. The fetcher now requests native Belgian Lambert 2008 and projects locally, retaining the same 82 building IDs and height attributes. The tower is anchored to GRB KNW OIDN 9709, manually identified against the orthophoto (its original source label is mast). Building and launch coordinates now agree with independent map imagery. Earlier screenshot/flight evidence above predates this coordinate correction. See SOURCES.md for control points and mixed-date parking/layout limitations.

Validation: `campus-landmarks-geometry.log` checks the independent native-grid control point, open entrance ray, colliding glass and roof, tower placement, parking and mesh validity. `campus-landmarks-check.log` verifies stable support at the corrected Corda 1 position and live RGB-D/lidar payloads.

The complete rooftop arm/takeoff/hold/landing/disarm and restored Hold passed after the native-grid correction (`campus-landmarks-flight.log`), followed by stable rooftop support. Both Docker images were rebuilt with the final landmark assets; offline mesh regeneration matches a clean output directory byte for byte (`campus-landmarks-regenerate.log`). Geometry checks and regeneration run locally with isolated GIS dependencies; GitHub Actions has been removed.

Performance/building refinement: the full 82-building native snapshot remains available; 53 small peripheral buildings are excluded by the configurable 350 m² / 160 m rule. Batched static geometry reduces the campus from 686 links / 690 visuals to 37 links / 66 visuals, with all retained collision shapes and poses preserved. Corda 8 has nine physical sawtooth wedges with clerestory strips (8/10.5 m approximate valley/ridge); Corda 5 now has separate 11.5 m office wings, a 7.5 m curved hall and a 13.5 m entrance drum. Dimensions are approximate, guided by official maps/orthophotography.

Twenty-second desktop observations with software rendering and the original 10 Hz sensor settings recorded elapsed simulation/wall-time ratios of 0.645 before and 0.888 after (`campus-performance-before.jsonl`, `campus-performance-after.jsonl`). View position/desktop geometry differed, so these are indicative observations, not a controlled speedup or fixed-FPS guarantee. Scene-count reductions are deterministic. `campus-optimized-check.log` confirms stable rooftop support and unchanged RGB-D/lidar dimensions and finite returns. Geometry regression checks now cover culling, batching, the Corda 5 partition and actual sawtooth collision roofs.

The new `--no-gazebo-gui` mode passed startup, rooftop stability, unchanged sensor payloads, full takeoff/hold/land/disarm and restored Hold (`campus-optimized-no-viewer.log`); its separate 20-second sample recorded an elapsed factor of 0.943 with QGroundControl still running. These remain local observations, not a hardware-independent benchmark. Full offline regeneration and structural checks are recorded in `campus-optimized-regenerate.log`.

Landing deck refinement: replaced the slab and thin posts with a six-metre chamfered deck, roof-conforming closed plinth, edge fascia, support ribs, matte teal finish, white circle/H/boundary, amber corner brackets and flush green marker lenses. The flight surface has no raised obstacles; paint/lenses are visual-only. Platform and plinth have two closed collision meshes. Batched campus totals are now 37 links, 72 visuals and 297 collisions. The source point is unchanged; updated deck/spawn elevations are generated automatically. GitHub Actions has been removed at the user’s request; all verification remains local.
