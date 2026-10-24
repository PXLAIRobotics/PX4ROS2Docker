"""Show fresh, valid local position; --once provides a bounded readiness check."""
import argparse
import time
import rclpy
from rclpy.node import Node
from rclpy.signals import SignalHandlerOptions
from px4_msgs.msg import VehicleLocalPosition, VehicleStatus
from .common import QOS, topic


class Telemetry(Node):
    def __init__(self):
        super().__init__('px4_telemetry')
        self.position = None
        self.status = None
        self.received = self.status_received = 0.0
        self.create_subscription(VehicleLocalPosition, topic('out', 'vehicle_local_position', VehicleLocalPosition), self.on_position, QOS)
        self.create_subscription(VehicleStatus, topic('out', 'vehicle_status', VehicleStatus), self.on_status, QOS)

    def on_position(self, msg):
        self.position = msg
        self.received = time.monotonic()

    def on_status(self, msg):
        self.status = msg
        self.status_received = time.monotonic()

    def ready(self):
        return (self.position is not None and self.status is not None
                and self.position.xy_valid and self.position.z_valid
                and time.monotonic() - self.received < 2
                and time.monotonic() - self.status_received < 3)

    def report(self):
        p = self.position
        print(f'NED position [m]: N={p.x:.2f} E={p.y:.2f} D={p.z:.2f}; '
              f'armed={self.status.arming_state == VehicleStatus.ARMING_STATE_ARMED}; '
              f'nav_state={self.status.nav_state}; timestamp_us={p.timestamp}', flush=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--once', action='store_true')
    parser.add_argument('--timeout', type=float, default=60)
    args, ros_args = parser.parse_known_args()
    rclpy.init(args=ros_args, signal_handler_options=SignalHandlerOptions.NO)
    node = Telemetry()
    start = last_report = time.monotonic()
    try:
        while rclpy.ok():
            rclpy.spin_once(node, timeout_sec=0.2)
            now = time.monotonic()
            if node.ready() and now - last_report > 1:
                node.report()
                last_report = now
                if args.once:
                    return
            if args.once and now - start > args.timeout:
                raise RuntimeError('Timed out waiting for fresh valid PX4 position and status')
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()
