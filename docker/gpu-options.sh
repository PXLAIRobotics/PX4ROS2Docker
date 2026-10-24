#!/usr/bin/env bash
# Sourced after args is created by host-common.sh.
gpu=${GPU_MODE:-auto}
case "$gpu" in auto|nvidia|dri|software) ;; *) echo 'GPU_MODE must be auto, nvidia, dri or software' >&2; exit 2;; esac
if [[ $gpu == auto ]]; then
    if command -v nvidia-smi >/dev/null 2>&1 && nvidia-smi >/dev/null 2>&1; then
        runtimes=$(docker info --format '{{json .Runtimes}}')
        if [[ $runtimes == *nvidia* ]]; then gpu=nvidia; else gpu=software; fi
    elif [[ -d /dev/dri ]]; then gpu=dri
    else gpu=software; fi
fi
case "$gpu" in
    nvidia) args+=(--gpus all -e "NVIDIA_DRIVER_CAPABILITIES=graphics,display,utility,compute" -e __GLX_VENDOR_LIBRARY_NAME=nvidia -e __NV_PRIME_RENDER_OFFLOAD=1) ;;
    dri)
        [[ -d /dev/dri ]] || { echo '/dev/dri is unavailable' >&2; exit 1; }
        args+=(--device /dev/dri)
        for device in /dev/dri/*; do
            [[ ! -c $device ]] || args+=(--group-add "$(stat -c %g "$device")")
        done ;;
    software) args+=(-e LIBGL_ALWAYS_SOFTWARE=1 -e __GLX_VENDOR_LIBRARY_NAME=mesa) ;;
esac
printf 'Graphics mode: %s\n' "$gpu"
