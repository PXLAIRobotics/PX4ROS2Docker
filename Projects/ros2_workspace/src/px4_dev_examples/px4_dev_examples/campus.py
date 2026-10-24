"""Verify the disarmed vehicle stays on Corda 1's roof, not on the ground."""
import json
import math
import time
from pathlib import Path

from ament_index_python.packages import get_package_share_directory
import rclpy
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from px4_msgs.msg import VehicleGlobalPosition, VehicleStatus
from px4_dev_examples.common import topic


def main():
    manifest=json.loads((Path(get_package_share_directory('px4_dev_examples'))/'simulation/campus.json').read_text())
    launch=manifest['launch']
    rclpy.init();node=Node('campus_roof_check')
    samples=[];status=None
    def position(msg):
        if msg.lat_lon_valid and msg.alt_valid:
            samples.append((time.monotonic(),msg))
    def state(msg):
        nonlocal status
        status=msg
    subs=[node.create_subscription(VehicleGlobalPosition,
        topic('out','vehicle_global_position',VehicleGlobalPosition),position,qos_profile_sensor_data),
        node.create_subscription(VehicleStatus,topic('out','vehicle_status',VehicleStatus),state,qos_profile_sensor_data)]
    try:
        deadline=time.monotonic()+35
        while time.monotonic()<deadline:
            rclpy.spin_once(node,timeout_sec=.1)
            if len(samples)>8 and samples[-1][0]-samples[0][0]>=8 and status is not None:
                break
        else: raise RuntimeError('No sustained fresh global position/status for rooftop verification')
        expected=launch['world_ground_altitude_m']+launch['platform_top_m']+.24
        tail=[msg for stamp,msg in samples if stamp>samples[0][0]+2]
        altitudes=[msg.alt for msg in tail]
        max_error=0
        for msg in tail:
            north=math.radians(msg.lat-launch['latitude'])*6371000
            east=math.radians(msg.lon-launch['longitude'])*6371000*math.cos(math.radians(launch['latitude']))
            max_error=max(max_error,math.hypot(east,north))
        assert status.arming_state==VehicleStatus.ARMING_STATE_DISARMED, 'Check requires a disarmed vehicle'
        assert max_error<2.0, f'Vehicle moved off rooftop spawn: {max_error:.2f} m'
        assert max(abs(alt-expected) for alt in altitudes)<1.5, f'Wrong support elevation: {altitudes[-1]:.2f} vs {expected:.2f} AMSL'
        assert max(altitudes)-min(altitudes)<.8, 'Vehicle is falling or unstable on the roof'
        print(json.dumps({'result':'PASS','platform_top_above_ground_m':launch['platform_top_m'],
              'observed_altitude_m':altitudes[-1],'expected_altitude_m':expected,
              'altitude_span_m':max(altitudes)-min(altitudes),'max_horizontal_error_m':max_error,
              'samples':len(tail),'disarmed':True},indent=2))
    finally:
        node.destroy_node();rclpy.shutdown()


if __name__=='__main__':main()
