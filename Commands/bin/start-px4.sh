#!/usr/bin/env bash
# Start PX4, Gazebo, and QGroundControl inside the development container.
set -eo pipefail
for argument in "$@"; do
    case "$argument" in
        --help|-h)
            echo 'Usage: start-px4.sh [--headless] [--no-gazebo-gui] [--no-attach]'
            echo 'Sets up sources, builds PX4 and ROS 2, then starts the simulation.'
            echo 'The first run downloads sources and can take a while. Later builds are incremental.'
            echo 'Set BUILD_JOBS to control build parallelism (default: 4).'
            exit 0 ;;
        --headless|--no-gazebo-gui|--no-attach) ;;
        *) printf 'Unknown option: %s\nUse --help for usage.\n' "$argument" >&2; exit 2 ;;
    esac
done
SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
# Reattach immediately when the simulator is already running; do not build
# binaries or update installed ROS files underneath an active session.
if ! tmux has-session -t px4-dev 2>/dev/null; then
    echo 'Preparing PX4 workspace...'
    "$SCRIPT_DIR/setup_px4_workspace"
    echo 'Building PX4 SITL...'
    "$SCRIPT_DIR/build_px4_sitl"
    echo 'Building ROS 2 workspace...'
    "$SCRIPT_DIR/build_ros2_workspace"
fi
# ROS setup files require nounset to be disabled. Load the newly built overlay
# in this process so the simulation and its tmux windows can find the packages.
source /opt/ros/jazzy/setup.bash
source "$HOME/Projects/ros2_workspace/install/setup.bash"
exec "$SCRIPT_DIR/start_px4_dev" "$@"
