#!/usr/bin/env bash
# Native ROS 2 cockpit; application source lives outside this repository.
set -eo pipefail
case "${1:-}" in
    --help|-h)
        echo 'Usage: start-px4-cockpit.sh [--check]'
        echo 'Open the local PX4 simulator cockpit. Start start-px4-corda-simulation.sh first.'
        echo 'Application: ${UAV_COCKPIT_DIR:-$HOME/.local/share/uav-cockpit}'
        echo 'If missing, install automatically from ~/Data/UAVCockpit.tar.gz.'
        exit 0 ;;
    --check|'') ;;
    *) echo 'Usage: start-px4-cockpit.sh [--check]' >&2; exit 2 ;;
esac
if (( $# > 1 )); then echo 'Usage: start-px4-cockpit.sh [--check]' >&2; exit 2; fi
app_dir=${UAV_COCKPIT_DIR:-$HOME/.local/share/uav-cockpit}
archive="$HOME/Data/UAVCockpit.tar.gz"
if [[ ! -f "$app_dir/cockpit.py" && -f "$archive" ]]; then
    # Check the extracted bundle before copying into the persistent installation.
    (
        staging_dir=$(mktemp -d)
        trap 'rm -rf "$staging_dir"' EXIT
        tar -xzf "$archive" -C "$staging_dir"
        [[ -f "$staging_dir/cockpit.py" ]] || {
            echo "Cockpit archive does not contain cockpit.py at its root: $archive" >&2
            exit 1
        }
        mkdir -p "$app_dir"
        # Docker creates an empty named volume as root on its first mount.
        # Repair only the standard volume directory, not an external install.
        if [[ ! -w "$app_dir" && "$app_dir" == "$HOME/.local/share/uav-cockpit" && $(stat -c %u "$app_dir") == 0 ]]; then
            sudo -n chown -- "$(id -u):$(id -g)" "$app_dir"
        fi
        [[ -w "$app_dir" ]] || {
            echo "Cockpit installation directory is not writable: $app_dir" >&2
            exit 1
        }
        cp -a "$staging_dir/." "$app_dir/"
    )
    echo "Installed cockpit from $archive into $app_dir"
fi
[[ -f "$app_dir/cockpit.py" ]] || {
    echo "Cockpit is not installed at $app_dir/cockpit.py" >&2
    echo 'Put UAVCockpit.tar.gz in ~/Data, attach the px4-uav-cockpit Docker volume, or set UAV_COCKPIT_DIR to your external installation.' >&2
    exit 1
}
source /opt/ros/jazzy/setup.bash
[[ -f "$HOME/Projects/ros2_workspace/install/setup.bash" ]] || {
    echo 'Build the ROS workspace first with build_ros2_workspace.' >&2; exit 1;
}
source "$HOME/Projects/ros2_workspace/install/setup.bash"
python3 -c 'import rclpy; from PyQt5 import QtWidgets; from px4_dev_examples.offboard import Offboard'
if [[ ${1:-} == --check ]]; then
    python3 -m py_compile "$app_dir/cockpit.py"
    echo "Cockpit ready: $app_dir"
    exit 0
fi
[[ -n ${DISPLAY:-} || -n ${WAYLAND_DISPLAY:-} ]] || { echo 'Open this command in the container desktop (DISPLAY is unset).' >&2; exit 1; }
# One cockpit controller per ROS domain; a second launch cannot compete in flight.
exec flock -n "/tmp/uav-cockpit-${ROS_DOMAIN_ID:-0}.lock" python3 "$app_dir/cockpit.py" --sitl
