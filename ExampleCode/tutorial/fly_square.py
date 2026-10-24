"""Lesson 7 solution: a bounded local square using the tested flight lifecycle."""
import argparse
import csv
import math
from pathlib import Path
import signal
import time
import rclpy
from rclpy.signals import SignalHandlerOptions
from px4_dev_examples.offboard import Offboard


def square_offsets(side):
    """North, East offsets from launch, finishing above launch."""
    return [(side, 0), (side, side), (0, side), (0, 0)]


class Square(Offboard):
    def __init__(self, altitude, side, output):
        super().__init__(altitude, 0)
        self.side = side
        self.stage = 'takeoff'
        output.parent.mkdir(parents=True, exist_ok=True)
        self.file = output.open('w', newline='')
        self.writer = csv.writer(self.file)
        self.writer.writerow(['elapsed_s', 'stage', 'north_m', 'east_m', 'down_m',
                              'target_n_m', 'target_e_m', 'target_d_m', 'error_m'])
        self.started = time.monotonic()
        self.last_sample = 0.0

    def stream(self):
        super().stream()
        now = time.monotonic()
        if now - self.last_sample >= 0.2:
            p = self.position
            error = math.dist((p.x, p.y, p.z), self.target)
            self.writer.writerow([now-self.started, self.stage, p.x, p.y, p.z,
                                  *self.target, error])
            self.file.flush()
            self.last_sample = now

    def fly(self):
        for index, (north, east) in enumerate(square_offsets(self.side), 1):
            self.stage = f'waypoint_{index}'
            self.target = (self.origin[0]+north, self.origin[1]+east,
                           self.origin[2]-self.altitude)
            settled_since = None

            def settled():
                nonlocal settled_since
                p = self.position
                close = math.dist((p.x, p.y, p.z), self.target) < 0.35
                if not close:
                    settled_since = None
                elif settled_since is None:
                    settled_since = time.monotonic()
                return settled_since is not None and time.monotonic()-settled_since >= 2

            self.wait_for(settled, 35, stream=True)
            self.get_logger().info(f'Reached {self.stage}: N offset={north}, E offset={east}')
        self.stage = 'return_complete'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--sitl', action='store_true', required=True)
    parser.add_argument('--side', type=float, default=2.0)
    parser.add_argument('--altitude', type=float, default=3.0)
    parser.add_argument('--csv', type=Path, default=Path.home()/'Data/tutorial/square.csv')
    args = parser.parse_args()
    if not (0.5 <= args.side <= 5 and 1 <= args.altitude <= 5):
        parser.error('side must be 0.5–5 m and altitude 1–5 m')
    rclpy.init(signal_handler_options=SignalHandlerOptions.NO)

    def interrupt(_signum, _frame):
        raise KeyboardInterrupt

    signal.signal(signal.SIGTERM, interrupt)
    node = Square(args.altitude, args.side, args.csv)
    try:
        node.run()
    except (Exception, KeyboardInterrupt):
        if node.mode_requested and node.fresh():
            node.get_logger().warning('Requesting landing after interruption/failure')
            try:
                node.land_and_wait()
            except (Exception, KeyboardInterrupt) as error:
                node.get_logger().error(f'Landing not confirmed: {error}; use QGC')
        raise
    finally:
        node.file.close()
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
