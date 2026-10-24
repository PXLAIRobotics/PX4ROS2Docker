# Instructor preparation and answer guide

## Prepare the class

Build the VNC image and both source workspaces before teaching. Test the actual student host configuration; software rendering is supported but may run below real time. Prepopulate sources, models and images when class network bandwidth is limited. QGC map tiles are optional network content; local Gazebo assets are bundled. Use the pinned versions rather than mixing upstream main with the release messages.

Run local checks from the host with `./tests/static.sh` and `python3 tests/tutorial.py`. Inside the container, verify the startup, telemetry and sensor checks. Run a complete hover and square in the empty world. Do not run the self-starting integration scripts while a student development session is active. GitHub Actions is not used.

The tutorial scripts are under `ExampleCode`, which is mounted to `~/ExampleCode` and included in new images. Python edits there need no colcon build; edits to `px4_dev_examples` do. Keep one controller active per vehicle and give students a second terminal for observation. Do not attach physical vehicles to this course setup.

## Suggested teaching pattern

Ask students to predict the result, execute the command, compare observation and explain the difference. Have pairs alternate controller and observer roles. Reveal `fly_square.py` after students have designed offset conversion and arrival logic. Its inheritance is deliberate: students can focus on the route while reading the shared lifecycle rather than duplicating command handling.

The read-only telemetry and lidar examples are complete scripts. The flight solution is complete but depends on the installed `px4_dev_examples` package. Fragments inside lessons are labelled or introduced as excerpts; students should not run a fragment as a standalone flight node.

## Answer guide

- Lesson 1: local state flows PX4 → agent → DDS → subscriber; a target takes the reverse route. Images use Gazebo → bridge → ROS. QGC commands use MAVLink. PX4's controllers and Gazebo's physics produce movement. A cloud alone supplies no planner or avoidance logic.
- Lesson 2: the bind mount preserves `Data`; stopping/removing the container does not remove those host files. Detach does not stop services.
- Lesson 3: requested mode and actual state may differ during transitions. Landed detection can precede automatic disarm. Different altitude references need not share values.
- Lesson 4: store receipt time with `time.monotonic()`, check age in the timer, and inspect `v_xy_valid`/`v_z_valid` before displaying velocity as valid. QoS and schema-derived topic names must match the publisher.
- Lesson 5: from `(12,-4,-20)`, three metres up gives `(12,-4,-23)`; then two metres east gives `(12,-2,-23)`. Climb gives negative `vz` in NED. Absolute `z=-3` ignores the start reference.
- Lesson 6: sleeping without spinning/streaming starves heartbeat and callbacks. An accepted arm command is not observed armed state. The code waits for mode and arm separately.
- Lesson 7: add offsets to origin, not to the latest position. Reset dwell time every time error leaves tolerance. The fourth waypoint must return above origin. A step change starts with a large legitimate tracking error.
- Lesson 8: Ctrl+C allows recovery code; a hard kill cannot run it. An old last message is not evidence of fresh telemetry. Missing telemetry can also prevent confirmation of landing.
- Lesson 9: lidar X positive is forward in its linked frame; a cone additionally bounds lateral/vertical angle. A roof return is real geometry, but not necessarily an obstacle in the planned direction. Filter NaN and infinity. Read-only perception must remain separate from control until its behaviour is specified.
- Lesson 10: CSV includes transient tracking error and uses wall time. Recording is not flight-success evidence without mode/landing observations. Default bags omit flight command inputs; custom bags need topic review before replay.
- Lesson 11: readiness, a relative takeoff, observed arrival, return, landing/disarm and evidence are required. Do not score an uncontrolled campus tour more highly than a bounded reproducible flight.

## Assessment rubric

| Area | Weight | Evidence |
| --- | --- | --- |
| Architecture, frames and time | 20% | Correct data-path and target explanations |
| Telemetry and validity | 15% | Working subscriber and stale-state handling |
| Flight lifecycle | 25% | Observed mode, arm, arrival, land and disarm |
| Waypoint logic | 15% | Relative coordinates, tolerance, dwell and deadline |
| Sensors and evaluation | 15% | Finite data, correct frames, reproducible CSV analysis |
| Reproducibility | 10% | Commands, code, logs and explained limitations |

Evaluate explanation as well as successful execution. A tutorial flight does not establish real-aircraft readiness or obstacle-avoidance capability.

## Further reading

Use versioned upstream documentation alongside the repository code:

- [PX4 v1.17 ROS 2 offboard example](https://docs.px4.io/v1.17/en/ros2/offboard_control)
- [PX4 v1.17 Offboard mode](https://docs.px4.io/v1.17/en/flight_modes/offboard)
- [ROS 2 Jazzy tutorials](https://docs.ros.org/en/jazzy/Tutorials.html)

The upstream offboard example is C++; this course supplies Python implementations for the pinned environment. Do not replace the local pinned setup with the clone/build commands from a different ROS distribution.
