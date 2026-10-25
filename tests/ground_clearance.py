"""Projection and invalid-reading checks; no ROS runtime required."""
import importlib.util
import math
from pathlib import Path
import unittest

path = Path(__file__).resolve().parents[1] / 'Projects/ros2_workspace/src/px4_dev_examples/px4_dev_examples/ground_clearance.py'
spec = importlib.util.spec_from_file_location('ground_clearance', path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class GroundClearanceTests(unittest.TestCase):
    def test_level_includes_aperture_offset(self):
        self.assertAlmostEqual(module.surface_height(3., [1, 0, 0, 0]), 3.019364)

    def test_pitch_projects_range_and_front_mount_offset(self):
        pitch = math.radians(20)
        q = [math.cos(pitch/2), 0, math.sin(pitch/2), 0]
        self.assertAlmostEqual(module.surface_height(4., q), (4.+.019364)*math.cos(pitch)-.125*math.sin(pitch))

    def test_yaw_does_not_change_height(self):
        self.assertAlmostEqual(module.surface_height(3., [math.sqrt(.5), 0, 0, math.sqrt(.5)]), 3.019364)

    def test_invalid_and_excessive_tilt_are_unavailable(self):
        for distance in [math.nan, math.inf, -math.inf, .049, 100.01]:
            self.assertTrue(math.isnan(module.surface_height(distance, [1, 0, 0, 0])))
        for q in [[0, 0, 0, 0], [math.nan, 0, 0, 0], [math.cos(math.pi/8), math.sin(math.pi/8), 0, 0]]:
            self.assertTrue(math.isnan(module.surface_height(3., q)))


if __name__ == '__main__':
    unittest.main()
