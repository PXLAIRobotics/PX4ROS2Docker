# Student cockpit bundle

Release archives are shared separately and are not committed to Git. The instructor’s local files are `Data/releases/uav-cockpit-2026-10-26.tar.gz` and its `.sha256` checksum; `Data/releases` is ignored. Students should obtain both files from their instructor.

Source snapshot of the active application in the `px4-uav-cockpit` Docker volume, packaged on 26 October 2026. The latest `campus_map.py` includes the drag/release fix and the Corda 7 callouts: PXL Digital at the lower-left corner and PXL Smart ICT at the lower-right corner on the north-up map. The bundle includes `cockpit.py`, `campus_map.py`, the launcher, control/velocity/map checks, live diagnostic scripts, installation instructions, MIT license, map attribution and a per-file `SHA256SUMS` manifest. Historical backup scripts, bytecode and obsolete map files are excluded.

Students need this repository's Docker environment and built ROS workspace. Compatible repository revision: `915d995291ef390bcff5fa3808ecc15a52821d98` or a later compatible revision. The archive is application source, not a complete simulator image; ROS dependencies, PX4 and campus assets come from the repository. Follow the [root installation workflow](../README.md#corda-flight-cockpit), then `INSTALL.md` inside the archive.

Verify the download from the directory containing both files:

```bash
# Linux
sha256sum -c uav-cockpit-2026-10-26.tar.gz.sha256
# macOS
shasum -a 256 -c uav-cockpit-2026-10-26.tar.gz.sha256
```

Validation on the release date: control logic, velocity ramps/holds, map geometry/zoom, and 30 real Qt drag/release/reset event cycles passed. A live check received vehicle telemetry and camera frames, confirmed preflight readiness and captured the disarmed cockpit without issuing flight commands. The flight-commanding `check_velocity_live.py` was included but was not run for this packaging task.

The application uses the installed Gazebo campus map rather than a separately bundled map. Its height metrics are takeoff/control-start relative and AMSL; above-surface sensor display is not included in this saved version. Keep attribution with redistributed copies.
