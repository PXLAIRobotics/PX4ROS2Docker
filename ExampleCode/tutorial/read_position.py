"""Lesson 4: a complete read-only PX4 subscriber. Run inside Docker."""
import rclpy
from rclpy.node import Node
from px4_msgs.msg import VehicleLocalPosition
from px4_dev_examples.common import QOS, topic


class PositionReader(Node):
    def __init__(self):
        super().__init__('student_position_reader')
        self.position = None
        self.create_subscription(VehicleLocalPosition,
            topic('out', 'vehicle_local_position', VehicleLocalPosition),
            self.on_position, QOS)
        self.create_timer(1.0, self.report)

    def on_position(self, msg):
        self.position = msg

    def report(self):
        p = self.position
        if p is None:
            self.get_logger().info('Waiting for position...')
        elif not (p.xy_valid and p.z_valid):
            self.get_logger().info('Position received, estimator not ready')
        else:
            self.get_logger().info(f'N={p.x:.2f} E={p.y:.2f} D={p.z:.2f} m')


def main():
    rclpy.init()
    node = PositionReader()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
