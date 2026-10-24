# 7 Build a waypoint controller

Your goal is to command a small square and advance only after an observed arrival. Use the empty `default` world for the full square. A position-step exercise is not a trajectory planner; it does not enforce speed, acceleration or obstacle clearance.

## Plan relative waypoints

After takeoff, hold the same down coordinate and visit offsets from launch:

```python
def square_offsets(side):
    return [(side, 0), (side, side), (0, side), (0, 0)]
```

These tuples are North/East, so the first segment heads north. Returning to `(0, 0)` means above launch, not landing yet. Land only after returning.

Before opening the solution, write your own function to convert those offsets to full NED targets. Test it with a nonzero launch position. Sketch the square with north pointing up and east right.

## Use the existing lifecycle

The complete [fly_square.py](../../ExampleCode/tutorial/fly_square.py) subclasses `Offboard`. It overrides the `fly()` stage, while inheriting readiness, prestream, mode/arm observations, heartbeat, stale-state checks, landing and Hold restoration. This keeps the new lesson focused on waypoint decisions. The base `offboard_demo` still uses `fly()` simply to hold.

The key target update is:

```python
self.target = (
    self.origin[0] + north,
    self.origin[1] + east,
    self.origin[2] - self.altitude,
)
```

Arrival means a three-dimensional error below 0.35 m continuously for two wall seconds. Leaving the tolerance resets the dwell timer. Each waypoint has a 35-second deadline. This avoids advancing merely because time passed or because the vehicle briefly crossed a sphere.

**Container**, QGC connected and vehicle disarmed:

```bash
python3 ~/ExampleCode/tutorial/fly_square.py --sitl --side 2 --altitude 3
python3 ~/ExampleCode/tutorial/analyze_flight.py ~/Data/tutorial/square.csv
```

Expect four `Reached waypoint_…` messages, followed by the normal landed/disarmed PASS. A CSV is written throughout offboard streaming; it includes takeoff and waypoint tracking, not the landing phase.

## Exercise

Implement a triangle that returns above launch. Keep the same range bounds, arrival rule and interruption handling. Compare a 1 m and 2 m square: does a larger step change peak tracking error? Explain why maximum error right after a target change is not a measurement of estimator accuracy.

**Checkpoint:** all four arrivals are observed, the vehicle returns and lands, and the CSV contains finite errors for each waypoint. Never run a second controller at the same time.

[Next: failure diagnosis →](08-failures.md)
