#!/usr/bin/env bash
set -euo pipefail
source /etc/px4-versions.env
case "$(dpkg --print-architecture)" in
    amd64) arch=x86_64; checksum=$QGC_AMD64_SHA256 ;;
    arm64) arch=aarch64; checksum=$QGC_ARM64_SHA256 ;;
    *) echo 'QGC supports only amd64/arm64 in this environment' >&2; exit 1 ;;
esac
curl -fL --retry 3 "https://github.com/mavlink/qgroundcontrol/releases/download/${QGC_VERSION}/QGroundControl-${arch}.AppImage" -o /tmp/qgc.AppImage
printf '%s  /tmp/qgc.AppImage\n' "$checksum" | sha256sum -c -
chmod +x /tmp/qgc.AppImage
cd /opt
/tmp/qgc.AppImage --appimage-extract >/dev/null
mv squashfs-root qgroundcontrol
rm /tmp/qgc.AppImage
