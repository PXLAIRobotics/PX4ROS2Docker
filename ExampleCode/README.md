# PX4 development walkthroughs

Use the root README to build/run the container and populate/compile Projects first.

1. **Inspect telemetry:** start the session with `start_px4_dev`, then run `ros2 run px4_dev_examples telemetry` in another shell. Check NED position and state while moving the simulated vehicle in QGC.
2. **Fly through QGC:** wait for the x500 to connect and pass preflight checks. Use Takeoff, observe Gazebo movement, then Land. Inspect the new ULog under `~/Data/px4/logs`.
3. **Fly through ROS:** with QGC connected and the simulated vehicle disarmed, run `ros2 run px4_dev_examples offboard_demo --sitl --altitude 3 --hold 5`. Confirm the printed completion report and landed/disarmed vehicle.
4. **Modify PX4:** `stop_px4_dev`, edit a PX4 source file in `~/Projects/PX4-Autopilot`, run `build_px4_sitl`, and restart. Use its own Git checkout to save firmware changes.
5. **Modify ROS:** edit `~/Projects/ros2_workspace/src/px4_dev_examples`, run `build_ros2_workspace`, source `install/setup.bash`, and rerun the node. Add dependencies to package.xml when extending it.
6. **Record:** run `record_px4_rosbag` before a simulated flight and stop it afterward. Use `ros2 bag info` on the resulting folder; keep replay nodes separate from live control nodes.

7. **Inspect perception:** the default x500 now carries an RGB-D camera and 16-channel 3D lidar. Run `view_px4_sensors` for the prepared RViz displays, or `ros2 run px4_dev_examples sensor_check --save ~/Data/evidence/sensors` to verify all streams and save RGB/depth previews. See the root README for topic names, frames and the sensor-free option.

8. **Fly from the campus roof:** the default world reconstructs Corda Campus from GRB footprints. Run `ros2 run px4_dev_examples campus_check` while disarmed to verify that the vehicle rests on the synthetic level platform on Corda 1. The normal offboard demo takes off relative to that roof and lands back on it. Switch to `PX4_GZ_WORLD=default start_px4_dev` for the earlier empty world.
