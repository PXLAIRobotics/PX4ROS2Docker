"""Check live rendered sensor data and its TF chain without commanding flight."""
import argparse
import json
import time
from pathlib import Path

import numpy as np
import rclpy
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from rclpy.time import Time
from sensor_msgs.msg import CameraInfo, Image, PointCloud2
from sensor_msgs_py import point_cloud2
from tf2_ros import Buffer, TransformListener


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--timeout', type=float, default=45)
    parser.add_argument('--save', type=Path, help='Save RGB/depth preview and JSON report here')
    args = parser.parse_args()
    rclpy.init()
    node = Node('drone_sensor_check')
    messages, stamps, counts = {}, {}, {}
    subscriptions = []
    specs = {
        '/drone/rgbd/image': Image,
        '/drone/rgbd/depth_image': Image,
        '/drone/rgbd/camera_info': CameraInfo,
        '/drone/rgbd/points': PointCloud2,
        '/drone/lidar/points': PointCloud2,
    }
    def received(topic, message):
        stamp = message.header.stamp.sec * 10**9 + message.header.stamp.nanosec
        if stamp > stamps.get(topic, -1):
            counts[topic] = counts.get(topic, 0) + 1
        stamps[topic] = stamp
        messages[topic] = message
    for topic, cls in specs.items():
        subscriptions.append(node.create_subscription(
            cls, topic, lambda msg, topic=topic: received(topic, msg), qos_profile_sensor_data))
    buffer = Buffer()
    listener = TransformListener(buffer, node)
    try:
        deadline = time.monotonic() + args.timeout
        while time.monotonic() < deadline:
            rclpy.spin_once(node, timeout_sec=0.1)
            if all(counts.get(topic, 0) >= 3 for topic in specs) and all(
                buffer.can_transform('base_link', msg.header.frame_id, Time())
                for msg in messages.values()
            ):
                break
        else:
            raise RuntimeError(f'Missing advancing sensor data or TF: {counts}')
        rgb = messages['/drone/rgbd/image']
        depth = messages['/drone/rgbd/depth_image']
        info = messages['/drone/rgbd/camera_info']
        assert rgb.encoding == 'rgb8' and (rgb.width, rgb.height) == (320, 240)
        assert depth.encoding == '32FC1' and (depth.width, depth.height) == (320, 240)
        assert info.width == rgb.width and info.height == rgb.height and info.k[0] > 0
        assert rgb.header.frame_id == depth.header.frame_id == info.header.frame_id == 'rgbd_optical_frame'
        endian = '>' if depth.is_bigendian else '<'
        depths = np.ndarray((depth.height, depth.width), dtype=endian + 'f4',
                            buffer=depth.data, strides=(depth.step, 4)).copy()
        valid = depths[np.isfinite(depths) & (depths > 0)]
        assert valid.size > 100 and valid.min() >= 0.14 and valid.max() <= 20.1
        report = {'depth_finite_pixels': int(valid.size),
                  'depth_range_m': [float(valid.min()), float(valid.max())], 'topics': {}}
        for topic, msg in messages.items():
            row = {'frame': msg.header.frame_id, 'advancing_samples': counts[topic]}
            if isinstance(msg, PointCloud2):
                xyz = point_cloud2.read_points_numpy(msg, field_names=('x', 'y', 'z'), skip_nans=True)
                xyz = xyz.reshape(-1, 3)
                xyz = xyz[np.isfinite(xyz).all(axis=1)]
                assert len(xyz) > 100, f'{topic}: no useful point returns'
                row.update(width=msg.width, height=msg.height, finite_points=len(xyz))
                if topic == '/drone/lidar/points':
                    assert msg.height == 16 and msg.width == 720
                    assert np.ptp(xyz[:, 2]) > 0.01, 'Lidar returns are flat, not 3D'
                else:
                    assert msg.height == 240 and msg.width == 320
                    assert msg.header.frame_id == 'rgbd_sensor', 'RGB-D cloud must use its FLU frame'
                    # Harmonic's cloud contains +X forward, +Y left, +Z up.
                    # Check the pixel rays against calibration: merely finding
                    # a TF chain would miss a cloud labelled as an optical frame.
                    organized = point_cloud2.read_points_numpy(
                        msg, field_names=('x', 'y', 'z'), skip_nans=False).reshape(240, 320, 3)
                    finite = np.isfinite(organized).all(axis=2)
                    rays = organized[finite]
                    assert np.all(rays[:, 0] > 0), 'RGB-D returns must be ahead of the camera'
                    rows, cols = np.indices((240, 320))
                    np.testing.assert_allclose(rays[:, 1] / rays[:, 0],
                                               -(cols[finite] + 0.5 - info.k[2]) / info.k[0], atol=0.02)
                    np.testing.assert_allclose(rays[:, 2] / rays[:, 0],
                                               -(rows[finite] + 0.5 - info.k[5]) / info.k[4], atol=0.02)
            report['topics'][topic] = row
        print(json.dumps(report, indent=2))
        if args.save:
            import cv2
            args.save.mkdir(parents=True, exist_ok=True)
            pixels = np.ndarray((rgb.height, rgb.width, 3), dtype=np.uint8,
                                buffer=rgb.data, strides=(rgb.step, 3, 1))
            cv2.imwrite(str(args.save / 'rgb.png'), cv2.cvtColor(pixels, cv2.COLOR_RGB2BGR))
            preview = np.nan_to_num(depths, nan=20, posinf=20, neginf=0)
            cv2.imwrite(str(args.save / 'depth.png'), cv2.applyColorMap(
                (np.clip(preview, 0, 20) / 20 * 255).astype(np.uint8), cv2.COLORMAP_TURBO))
            (args.save / 'sensors.json').write_text(json.dumps(report, indent=2) + '\n')
    finally:
        node.destroy_node()
        rclpy.shutdown()
