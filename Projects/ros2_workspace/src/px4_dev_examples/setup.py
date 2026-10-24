from glob import glob
from setuptools import setup

setup(
    name='px4_dev_examples', version='0.1.0', packages=['px4_dev_examples'],
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/px4_dev_examples']),
        ('share/px4_dev_examples', ['package.xml']),
        ('share/px4_dev_examples/launch', glob('launch/*.launch.py')),
        ('share/px4_dev_examples/config', glob('config/*')),
        ('share/px4_dev_examples/simulation', glob('simulation/*.sh')),
        ('share/px4_dev_examples/simulation/models/x500_rgbd_lidar',
         glob('simulation/models/x500_rgbd_lidar/*')),
    ],
    install_requires=['setuptools'], zip_safe=True,
    maintainer='PX4 Docker developers', maintainer_email='dev@example.com',
    description='PX4 SITL telemetry and offboard examples', license='MIT',
    entry_points={'console_scripts': [
        'telemetry = px4_dev_examples.telemetry:main',
        'sensor_check = px4_dev_examples.sensors:main',
        'offboard_demo = px4_dev_examples.offboard:main',
    ]},
)
