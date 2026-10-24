#!/usr/bin/env bash
# Shared host-side implementation for the numbered lifecycle scripts.
set -euo pipefail
REPO_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
mode=${1:?mode}; action=${2:?action}; shift 2
case "$mode" in vnc|novnc|headless) ;; *) echo "Unknown mode: $mode" >&2; exit 2;; esac
image="px4_ros2_${mode}:latest"
name="px4_ros2_${mode}"
if [[ $mode == headless ]]; then image=px4_ros2_novnc:latest; fi
command -v docker >/dev/null || { echo 'Install Docker Engine first.' >&2; exit 1; }
docker info >/dev/null 2>&1 || { echo 'Cannot access Docker. Check daemon and user permissions.' >&2; exit 1; }
case "$action" in
    build)
        target=native; [[ $mode != vnc ]] || target=vnc
        exec docker build --target "$target" -t "$image" \
            --build-arg "USER_UID=$(id -u)" --build-arg "USER_GID=$(id -g)" "$@" "$REPO_DIR" ;;
    attach) exec docker exec -it "$name" bash "$@" ;;
    stop)
        auto_remove=$(docker container inspect --format '{{.HostConfig.AutoRemove}}' "$name")
        docker stop "$@" "$name"
        # Docker can return before --rm releases the name. Make stop→run reliable.
        if [[ $auto_remove == true ]]; then
            for _ in {1..100}; do
                if ! docker container inspect "$name" >/dev/null 2>&1; then exit 0; fi
                sleep 0.1
            done
            echo 'Container stopped; automatic removal is still in progress. Retry shortly.' >&2
            exit 1
        fi
        exit 0 ;;
    remove) exec docker rm "$@" "$name" ;;
    remove-image) exec docker image rm "$@" "$image" ;;
    run) ;;
    *) echo "Unknown action: $action" >&2; exit 2 ;;
esac
args=(--rm --name "$name" --hostname "$name" --shm-size=2g)
if [[ -t 0 && -t 1 ]]; then args+=(-it); else args+=(-i); fi
for directory in Commands/bin ExampleCode Projects Data; do
    mkdir -p "$REPO_DIR/$directory"
    args+=(--mount "type=bind,src=$REPO_DIR/$directory,dst=/home/user/${directory##*/}")
done
args+=(-e "ROS_DOMAIN_ID=${ROS_DOMAIN_ID:-0}" -e TERM=xterm-256color)
if [[ $mode == vnc ]]; then
    args+=(-p "127.0.0.1:${WEB_PORT:-6901}:6901" -p "127.0.0.1:${VNC_PORT:-5901}:5901")
    args+=(-e "VNC_PW=${VNC_PW:-password}" -e "VNC_RESOLUTION=${VNC_RESOLUTION:-1280x800}")
elif [[ $mode == novnc ]]; then
    [[ $(uname -s) == Linux ]] || { echo 'Native display requires Linux. Use the VNC mode.' >&2; exit 1; }
    case ${DISPLAY:-} in :*|unix:*) ;; *) echo 'Set DISPLAY to a local X11/Xwayland display, or use VNC.' >&2; exit 1;; esac
    display_number=${DISPLAY##*:}; display_number=${display_number%%.*}
    socket="/tmp/.X11-unix/X$display_number"
    [[ -S $socket ]] || { echo "Missing X11 socket: $socket" >&2; exit 1; }
    args+=(-e "DISPLAY=$DISPLAY" -e QT_X11_NO_MITSHM=1 --mount "type=bind,src=/tmp/.X11-unix,dst=/tmp/.X11-unix,readonly")
    args+=(--group-add "$(stat -c %g "$socket")")
    auth_source=${XAUTHORITY:-$HOME/.Xauthority}
    if [[ -f $auth_source ]]; then
        command -v xauth >/dev/null || { echo 'Install xauth on the host.' >&2; exit 1; }
        entries=$(xauth -f "$auth_source" nlist "$DISPLAY")
        [[ -n $entries ]] || { echo 'No matching Xauthority cookie for DISPLAY.' >&2; exit 1; }
        auth_dir=$(mktemp -d /tmp/px4-xauth.XXXXXX)
        cleanup() { rm -f -- "$auth_dir/Xauthority"; rmdir -- "$auth_dir"; }
        trap cleanup EXIT
        touch "$auth_dir/Xauthority"
        printf '%s\n' "$entries" | sed 's/^..../ffff/' | xauth -f "$auth_dir/Xauthority" nmerge -
        chmod 644 "$auth_dir/Xauthority"
        args+=(--mount "type=bind,src=$auth_dir/Xauthority,dst=/tmp/px4.Xauthority,readonly" -e XAUTHORITY=/tmp/px4.Xauthority)
    else
        echo 'No Xauthority file found; relying on the local X server access policy (e.g. WSLg).' >&2
    fi
fi
source "$REPO_DIR/docker/gpu-options.sh"
# Extra Docker options precede the image; optionally separate a command using --.
run_options=(); command_args=()
while (( $# )); do
    if [[ $1 == -- ]]; then shift; command_args=("$@"); break; fi
    run_options+=("$1"); shift
done
if [[ $mode == headless && ${#command_args[@]} == 0 ]]; then command_args=(bash); fi
# Do not exec: native Xauthority cleanup must run after the foreground container exits.
docker run "${args[@]}" "${run_options[@]}" "$image" "${command_args[@]}"
