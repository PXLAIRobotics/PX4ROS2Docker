# 4 Read PX4 telemetry with Python

Your goal is to write a subscriber that turns PX4 messages into understandable measurements. Keep the vehicle disarmed for the first run.

## Inspect a message

**Container**:

```bash
ros2 interface show px4_msgs/msg/VehicleLocalPosition
ros2 topic list | sort
ros2 run px4_dev_examples telemetry --once
```

Find `x`, `y`, `z`, `xy_valid`, `z_valid` and `timestamp`. Reading a numerical value is useful only after checking its validity. The timestamp is in microseconds; it is not a Python float in seconds.

Output messages can carry a `_vN` topic suffix. Resolve the name from the installed schema rather than guessing:

```python
from px4_msgs.msg import VehicleLocalPosition
from px4_dev_examples.common import topic
print(topic('out', 'vehicle_local_position', VehicleLocalPosition))
```

To inspect exactly that topic from a shell:

```bash
POSITION_TOPIC=$(python3 -c "from px4_msgs.msg import VehicleLocalPosition as M; from px4_dev_examples.common import topic; print(topic('out', 'vehicle_local_position', M))")
ros2 topic echo "$POSITION_TOPIC" --once --qos-reliability best_effort
```

## Run the complete subscriber

The complete program is [read_position.py](../../ExampleCode/tutorial/read_position.py). Run it without creating another package:

```bash
python3 ~/ExampleCode/tutorial/read_position.py
```

Its essential ROS structure is:

```python
self.create_subscription(
    VehicleLocalPosition,
    topic('out', 'vehicle_local_position', VehicleLocalPosition),
    self.on_position,
    QOS,
)
self.create_timer(1.0, self.report)
```

The callback stores the newest message. The timer prints once per second; it avoids flooding the terminal at the incoming telemetry rate. `QOS` uses best-effort reliability, volatile durability and depth 1 to match this telemetry path. A reliable subscriber cannot receive from a best-effort-only publisher.

Press Ctrl+C to stop. This reader never sends flight commands. Unlike the packaged readiness check, the small teaching reader does not detect stale messages yet.

## Exercise

Copy the reader to `~/ExampleCode/tutorial/my_position.py`. Add velocity fields `vx`, `vy`, `vz` to its report after inspecting their validity flags. Then add a monotonic receipt timestamp and print “stale telemetry” if the newest message is older than two seconds. Keep those checks in the timer, not inside the callback.

For a package exercise, use `ros2 pkg create --build-type ament_python student_drone --dependencies rclpy px4_msgs px4_dev_examples` under `~/Projects/ros2_workspace/src`. Put your reader in `student_drone/reader.py`, add `'reader = student_drone.reader:main'` to the `console_scripts` list in `setup.py`, build and source the workspace, then run `ros2 run student_drone reader`.

**Checkpoint:** explain subscription type, resolved topic, callback, timer and QoS. Demonstrate changing output without changing PX4 source.

[Next: coordinates and time →](05-coordinates.md)
