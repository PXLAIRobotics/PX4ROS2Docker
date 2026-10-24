"""Bridge the single-drone sensor suite; timestamps stay on Gazebo time."""
from pathlib import Path
import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    share = Path(get_package_share_directory('px4_dev_examples'))
    world_clock = '/world/' + os.environ.get('PX4_GZ_WORLD', 'corda_campus') + '/clock'
    def fixed(parent, child, xyz, rpy):
        return Node(package='tf2_ros', executable='static_transform_publisher',
                    name=child + '_tf', arguments=[
                        '--x', str(xyz[0]), '--y', str(xyz[1]), '--z', str(xyz[2]),
                        '--roll', str(rpy[0]), '--pitch', str(rpy[1]), '--yaw', str(rpy[2]),
                        '--frame-id', parent, '--child-frame-id', child], output='screen')
    return LaunchDescription([
        Node(package='ros_gz_bridge', executable='parameter_bridge', name='drone_sensor_bridge',
             parameters=[{'config_file': str(share / 'config/sensors.yaml')}], output='screen'),
        Node(package='ros_gz_bridge', executable='parameter_bridge', name='sensor_clock_bridge',
             arguments=[world_clock + '@rosgraph_msgs/msg/Clock[gz.msgs.Clock'],
             remappings=[(world_clock, '/clock')], output='screen'),
        fixed('base_link', 'rgbd_link', (0.20, 0, 0.08), (0, 0.1745329252, 0)),
        fixed('rgbd_link', 'rgbd_sensor', (0.02, 0, 0), (0, 0, 0)),
        fixed('rgbd_sensor', 'rgbd_optical_frame', (0, 0, 0), (-1.5707963268, 0, -1.5707963268)),
        fixed('base_link', 'lidar_link', (0, 0, 0.20), (0, 0, 0)),
    ])
