"""Lesson 9: nearest finite lidar return; this node never commands flight."""
import math
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import PointCloud2
from sensor_msgs_py import point_cloud2
from px4_dev_examples.common import QOS


class LidarReader(Node):
    def __init__(self):
        super().__init__('student_lidar_reader')
        self.latest = None
        self.create_subscription(PointCloud2, '/drone/lidar/points', self.receive, QOS)
        self.create_timer(1.0, self.report)

    def receive(self, msg):
        self.latest = msg

    def report(self):
        if self.latest is None:
            return
        nearest = math.inf
        for point in point_cloud2.read_points(self.latest, field_names=('x', 'y', 'z'), skip_nans=True):
            xyz = tuple(float(point[name]) for name in ('x', 'y', 'z'))
            if all(math.isfinite(value) for value in xyz):
                nearest = min(nearest, math.sqrt(sum(value*value for value in xyz)))
        self.get_logger().info(f'Nearest finite return: {nearest:.2f} m; frame={self.latest.header.frame_id}')


def main():
    rclpy.init()
    node = LidarReader()
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
