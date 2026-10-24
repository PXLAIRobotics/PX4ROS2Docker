#!/usr/bin/env python3
"""Compare the actual ROS message schemas used by our examples with PX4 sources."""
import argparse
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument('--projects', type=Path, default=Path.home() / 'Projects')
projects = parser.parse_args().projects
px4 = projects / 'PX4-Autopilot/msg'
ros = projects / 'ros2_workspace/src/px4_msgs/msg'
names = ['VehicleStatus', 'VehicleLocalPosition', 'VehicleCommand', 'VehicleCommandAck',
         'OffboardControlMode', 'TrajectorySetpoint', 'VehicleLandDetected']


def schema(path):
    return [' '.join(line.split('#')[0].split()) for line in path.read_text().splitlines()
            if line.split('#')[0].strip()]


for name in names:
    candidates = [px4 / 'versioned' / f'{name}.msg', px4 / f'{name}.msg']
    firmware = next((path for path in candidates if path.is_file()), None)
    if firmware is None or schema(firmware) != schema(ros / f'{name}.msg'):
        raise SystemExit(f'Message mismatch: {name}')
print(f'All {len(names)} control/telemetry message schemas match the pinned firmware.')
