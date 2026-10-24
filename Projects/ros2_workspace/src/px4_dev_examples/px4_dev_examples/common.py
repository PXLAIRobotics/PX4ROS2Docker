"""PX4 topic versions, QoS and clocks shared by the examples."""
import time
from rclpy.qos import QoSProfile, ReliabilityPolicy, DurabilityPolicy

QOS = QoSProfile(depth=1, reliability=ReliabilityPolicy.BEST_EFFORT,
                 durability=DurabilityPolicy.VOLATILE)


def topic(direction, name, message_type):
    version = getattr(message_type, 'MESSAGE_VERSION', 0)
    return f'/fmu/{direction}/{name}' + (f'_v{version}' if version else '')


def timestamp():
    # Baseline uses wall clock and the PX4 XRCE time synchronizer, not /clock.
    return time.time_ns() // 1000
