# 5 Coordinates, altitude and time

Your goal is to predict a movement before commanding it. A frame mistake can produce valid messages with the wrong motion.

## Local position is NED

PX4 local coordinates are North, East, Down, in metres. ROS often uses East, North, Up. For a vector expressed relative to the same origin:

```python
def enu_to_ned(east, north, up):
    return north, east, -up

assert enu_to_ned(2, 1, 3) == (1, 2, -3)
```

This swaps axes and changes the vertical sign. It does not transform geodetic latitude/longitude into local metres, nor does it convert a quaternion. Body frames also differ: ROS FLU is Forward/Left/Up; PX4 FRD is Forward/Right/Down. Camera optical axes are a third convention.

| Desired movement | NED target offset |
| --- | --- |
| 2 m north | `(2, 0, 0)` |
| 2 m east | `(0, 2, 0)` |
| 3 m up | `(0, 0, -3)` |

Capture the current valid position as `(n0, e0, d0)`. A takeoff three metres above it has target `(n0, e0, d0 - 3)`. Do not assume the local origin equals the spawn position or the world ground.

At Corda Campus the launch deck is already on a roof. World elevation, PX4 local down, height above the launch surface and altitude above mean sea level are separate quantities. The generated [campus manifest](../../Projects/ros2_workspace/src/px4_dev_examples/simulation/campus.json) records the world/spawn values. `campus_check` compares observed rooftop support to those values.

## Use the intended clock

The existing PX4 control examples use wall-time timestamps in microseconds and the normal XRCE synchronisation:

```python
import time
timestamp_us = time.time_ns() // 1000
start = time.monotonic()
# A duration is measured with monotonic(), not by subtracting wall dates.
```

Gazebo sensors and RViz use simulation time through `/clock`. Keep those settings as supplied. Enabling `use_sim_time` on a control node alone does not coordinate the entire PX4 time pipeline. Slower software rendering also means a wall-time timeout can expire before a simulated flight reaches its target.

## Exercise and checkpoint

Given start NED `(12, -4, -20)`, compute targets for 3 m up, then 2 m east. Predict the sign of `vz` during climb. Discuss why assigning `z=-3` is incorrect when starting on a rooftop. Answers are in the instructor guide.

**Checkpoint:** you can explain the reference for every coordinate and avoid confusing negative down with negative height.

[Next: offboard flight →](06-offboard.md)
