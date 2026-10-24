"""Explicit opt-in single-vehicle SITL takeoff, hold, land and disarm example."""
import argparse
import math
import signal
import time
import rclpy
from rclpy.node import Node
from rclpy.signals import SignalHandlerOptions
from px4_msgs.msg import (VehicleLocalPosition, VehicleStatus, VehicleCommand,
                         VehicleCommandAck, OffboardControlMode, TrajectorySetpoint,
                         VehicleLandDetected)
from .common import QOS, topic, timestamp


class Offboard(Node):
    def __init__(self, altitude, hold):
        super().__init__('px4_sitl_offboard_demo')
        self.altitude, self.hold = altitude, hold
        self.position = self.status = self.land = None
        self.last_position = self.last_status = 0.0
        self.acks = []
        self.origin = None
        self.target = None
        self.mode_requested = self.offboard_observed = self.arm_observed = self.altitude_observed = False
        for cls, name, callback in [
            (VehicleLocalPosition, 'vehicle_local_position', self.on_position),
            (VehicleStatus, 'vehicle_status', self.on_status),
            (VehicleLandDetected, 'vehicle_land_detected', self.on_land),
            (VehicleCommandAck, 'vehicle_command_ack', self.on_ack),
        ]:
            self.create_subscription(cls, topic('out', name, cls), callback, QOS)
        self.control = self.create_publisher(OffboardControlMode, '/fmu/in/offboard_control_mode', QOS)
        self.trajectory = self.create_publisher(TrajectorySetpoint, '/fmu/in/trajectory_setpoint', QOS)
        self.commands = self.create_publisher(VehicleCommand, '/fmu/in/vehicle_command', QOS)

    def on_position(self, msg):
        self.position, self.last_position = msg, time.monotonic()

    def on_status(self, msg):
        self.status, self.last_status = msg, time.monotonic()

    def on_land(self, msg):
        self.land = msg

    def on_ack(self, msg):
        if msg.command not in (VehicleCommand.VEHICLE_CMD_DO_SET_MODE,
                               VehicleCommand.VEHICLE_CMD_COMPONENT_ARM_DISARM,
                               VehicleCommand.VEHICLE_CMD_NAV_LAND):
            return
        self.acks.append((time.monotonic(), msg.command, msg.result))
        self.get_logger().info(f'Command {msg.command} acknowledgement result={msg.result}')

    def command(self, command, p1=0.0, p2=0.0, p3=0.0):
        msg = VehicleCommand()
        msg.timestamp = timestamp()
        msg.command, msg.param1, msg.param2, msg.param3 = command, float(p1), float(p2), float(p3)
        msg.target_system, msg.target_component = 1, 1
        msg.source_system, msg.source_component = 1, 1
        msg.from_external = True
        self.commands.publish(msg)

    def spin(self):
        rclpy.spin_once(self, timeout_sec=0.05)

    def fresh(self):
        now = time.monotonic()
        return self.position is not None and self.status is not None and now - self.last_position < 2 and now - self.last_status < 3

    def stream(self):
        mode = OffboardControlMode()
        mode.timestamp, mode.position = timestamp(), True
        self.control.publish(mode)
        setpoint = TrajectorySetpoint()
        setpoint.timestamp = timestamp()
        setpoint.position = list(self.target)
        setpoint.velocity = [math.nan] * 3
        setpoint.acceleration = [math.nan] * 3
        setpoint.yaw = 0.0
        self.trajectory.publish(setpoint)

    def wait_for(self, predicate, seconds, stream=False):
        deadline = time.monotonic() + seconds
        while time.monotonic() < deadline:
            self.spin()
            if stream:
                if not self.fresh():
                    raise RuntimeError('PX4 telemetry became stale')
                if self.offboard_observed and self.status.nav_state != VehicleStatus.NAVIGATION_STATE_OFFBOARD:
                    raise RuntimeError('Vehicle left offboard mode unexpectedly')
                if self.arm_observed and self.status.arming_state != VehicleStatus.ARMING_STATE_ARMED:
                    raise RuntimeError('Vehicle disarmed unexpectedly during flight')
                self.stream()
            if predicate():
                return
        raise RuntimeError(f'Flight stage timed out after {seconds}s')

    def run(self):
        self.wait_for(lambda: self.fresh() and self.position.xy_valid and self.position.z_valid, 60)
        if self.status.arming_state == VehicleStatus.ARMING_STATE_ARMED:
            raise RuntimeError('Expected a disarmed simulated vehicle before starting')
        self.origin = (self.position.x, self.position.y, self.position.z)
        self.target = (self.origin[0], self.origin[1], self.origin[2] - self.altitude)
        # Establish the >2 Hz offboard stream before requesting the mode.
        deadline = time.monotonic() + 3
        self.wait_for(lambda: time.monotonic() >= deadline, 5, stream=True)
        self.mode_requested = True
        self.command(VehicleCommand.VEHICLE_CMD_DO_SET_MODE, 1, 6)
        self.wait_for(lambda: self.status.nav_state == VehicleStatus.NAVIGATION_STATE_OFFBOARD, 10, stream=True)
        self.offboard_observed = True
        self.command(VehicleCommand.VEHICLE_CMD_COMPONENT_ARM_DISARM, 1)
        self.wait_for(lambda: self.status.arming_state == VehicleStatus.ARMING_STATE_ARMED, 10, stream=True)
        self.arm_observed = True
        self.get_logger().info('Observed ARMED in OFFBOARD')
        target_z = self.origin[2] - self.altitude
        self.wait_for(lambda: abs(self.position.z - target_z) < 0.35, 35, stream=True)
        self.altitude_observed = True
        self.get_logger().info(f'Observed takeoff to {self.altitude}m above initial local position')
        self.fly()
        self.land_and_wait()
        if not self.arm_observed or not self.altitude_observed:
            raise RuntimeError('Missing flight evidence')
        print('PASS: observed arm, takeoff, hold, landing and disarm', flush=True)

    def fly(self):
        """Flight exercise hook; the default demonstration holds its target."""
        deadline = time.monotonic() + self.hold
        self.wait_for(lambda: time.monotonic() >= deadline, self.hold + 2, stream=True)

    def land_and_wait(self):
        self.command(VehicleCommand.VEHICLE_CMD_NAV_LAND)
        # Once land is requested, stop offboard streaming and observe land/disarm.
        self.wait_for(lambda: self.fresh() and self.land is not None and self.land.landed
                      and self.status.arming_state != VehicleStatus.ARMING_STATE_ARMED, 60)
        self.get_logger().info('Observed landed and disarmed')
        # PX4 can return to its previous offboard intention after disarm. Select
        # Hold explicitly so a stopped control stream does not leave QGC Not Ready.
        self.command(VehicleCommand.VEHICLE_CMD_DO_SET_MODE, 1, 4, 3)
        self.wait_for(lambda: self.status.nav_state == VehicleStatus.NAVIGATION_STATE_AUTO_LOITER, 5)
        self.get_logger().info('Restored Hold mode')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--sitl', action='store_true', required=True, help='Explicitly acknowledge this is the local simulator')
    parser.add_argument('--altitude', type=float, default=3.0)
    parser.add_argument('--hold', type=float, default=5.0)
    args, ros_args = parser.parse_known_args()
    if not (0.5 <= args.altitude <= 10 and 0 <= args.hold <= 60):
        parser.error('altitude must be 0.5–10 m and hold 0–60 seconds')
    rclpy.init(args=ros_args, signal_handler_options=SignalHandlerOptions.NO)
    # Keep the ROS context alive during interruption so the landing request can be sent.
    def request_stop(_signum, _frame):
        raise KeyboardInterrupt
    signal.signal(signal.SIGTERM, request_stop)
    node = Offboard(args.altitude, args.hold)
    try:
        node.run()
    except (Exception, KeyboardInterrupt) as error:
        if node.mode_requested and node.fresh():
            node.get_logger().warning('Interrupted or failed; requesting landing and waiting for disarm')
            try:
                node.land_and_wait()
            except (Exception, KeyboardInterrupt) as landing_error:
                node.get_logger().error(f'Landing not confirmed: {landing_error}; use QGC/PX4 console')
        if isinstance(error, KeyboardInterrupt):
            raise SystemExit(130)
        raise
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()
