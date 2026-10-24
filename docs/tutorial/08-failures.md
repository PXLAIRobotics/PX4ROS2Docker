# 8 Diagnose failures and recover

Your goal is to distinguish a communication problem, an estimator problem, a rejected command and an unfinished manoeuvre. Keep QGC available throughout simulated flights.

## Start with read only diagnostics

**Container**:

```bash
px4_doctor
ros2 run px4_dev_examples telemetry --once --timeout 10
px4_command commander status
px4_command param show COM_OF_LOSS_T
px4_command param show COM_OBL_RC_ACT
```

Record the current offboard-loss settings rather than assuming their values. A loss of the heartbeat causes PX4 to leave Offboard after its configured timeout and apply its configured fallback. Do not change these parameters for the beginner exercises.

| Symptom | First check |
| --- | --- |
| QGC connected, no ROS telemetry | Agent window, ROS domain, message schemas and QoS |
| Telemetry arrives but position invalid | PX4 estimator/preflight status; wait for validity |
| Offboard request refused | Established heartbeat, estimator health, command acknowledgement |
| Arm refused | QGC connected, readiness and PX4 status explanation |
| Battery unhealthy with a full indicator | Fresh PX4 battery status, not just the displayed percentage; restart SITL while disarmed if the simulated source is stale |
| Waypoint times out | Actual distance, mode, telemetry freshness and simulation speed |
| Images absent but flight works | Sensor bridge, selected world and sensor QoS |

## Controlled interruption exercise

1. Start the normal demo with `--hold 30` in the simple world.
2. Wait for the observed takeoff message.
3. Press Ctrl+C once in that demo's terminal.
4. Observe the node requesting Land and waiting for disarm. Keep QGC open until landing is confirmed.
5. Read the terminal result. An interrupted command can exit nonzero even when its recovery landing succeeds.

Ctrl+C uses the program's recovery path. It does **not** demonstrate a silent heartbeat loss. A force-killed process cannot execute cleanup. The latter is an instructor-led advanced exercise only after inspecting fallback settings; do not equate a killed Python process with a successfully completed landing.

If the program reports “Landing not confirmed”, use QGC's Land action and observe the vehicle. Do not send an in-air disarm command. Stop services only after the simulated vehicle is landed and disarmed.

## Exercise and checkpoint

Add a stale-data warning to your read-only subscriber from lesson 4. With the vehicle disarmed, stop services and observe that the warning appears instead of repeatedly printing an old position as fresh. Restart the session afterward.

**Checkpoint:** explain why node exit, a command acknowledgement and observed disarm are three different events. Submit the interruption log with the final QGC state.

[Next: perception →](09-perception.md)
