"""Downward range and tilt-corrected base-link height above the beam's surface hit."""
import math
import time


def surface_height(distance, quaternion):
    """PX4 FRD-to-NED quaternion; range aperture is FLU (0.125, 0, -0.019364).

    At nonzero tilt the hit is displaced horizontally; this is not a terrain map.
    Reject tilt beyond 30 degrees rather than displaying a misleading height.
    """
    if not math.isfinite(distance) or not 0.05 <= distance <= 100:
        return math.nan
    if len(quaternion) != 4 or not all(math.isfinite(v) for v in quaternion):
        return math.nan
    norm = math.sqrt(sum(v*v for v in quaternion))
    if not 0.9 < norm < 1.1:
        return math.nan
    w, x, y, z = (v/norm for v in quaternion)
    down = 1 - 2*(x*x+y*y)
    if down < math.cos(math.radians(30)):
        return math.nan
    offset_down = .125 * 2*(x*z-w*y) + .019364*down
    return distance*down + offset_down


def main():
    import rclpy
    from rclpy.node import Node
    from sensor_msgs.msg import LaserScan, Range
    from std_msgs.msg import Float32
    from px4_msgs.msg import VehicleAttitude
    from px4_dev_examples.common import QOS, topic

    class GroundClearance(Node):
        def __init__(self):
            super().__init__('ground_clearance')
            self.attitude = None
            self.last_attitude = self.last_scan = 0.
            self.range = self.create_publisher(Range, '/drone/height/range', QOS)
            self.height = self.create_publisher(Float32, '/drone/height/above_surface', QOS)
            self.create_subscription(VehicleAttitude, topic('out', 'vehicle_attitude', VehicleAttitude), self.on_attitude, QOS)
            self.create_subscription(LaserScan, '/drone/height/scan', self.on_scan, QOS)
            self.create_timer(.2, self.expire)

        def on_attitude(self, msg):
            self.attitude = msg.q
            self.last_attitude = time.monotonic()

        def on_scan(self, msg):
            self.last_scan = time.monotonic()
            distance = float(msg.ranges[0]) if len(msg.ranges) == 1 else math.nan
            result = Range()
            result.header = msg.header
            result.radiation_type = Range.INFRARED
            # Ideal single simulated ray, not a finite-cone real sensor.
            result.field_of_view = 0.0
            result.min_range, result.max_range, result.range = msg.range_min, msg.range_max, distance
            self.range.publish(result)
            height = surface_height(distance, self.attitude) if self.attitude is not None and self.last_scan-self.last_attitude < 1 else math.nan
            self.height.publish(Float32(data=height))

        def expire(self):
            now = time.monotonic()
            if now-self.last_scan > 1 or now-self.last_attitude > 1:
                self.height.publish(Float32(data=math.nan))

    rclpy.init()
    node = GroundClearance()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()
