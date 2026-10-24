#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.."
while IFS= read -r -d '' script; do bash -n "$script"; done < <(find . -path './Projects/PX4-Autopilot' -prune -o -path './Projects/ros2_workspace/src/px4_msgs' -prune -o -path './.git' -prune -o -type f -name '*.sh' -print0)
for script in Commands/bin/*; do bash -n "$script"; done
python3 - <<'PY'
import ast
from pathlib import Path
for path in list(Path('Projects/ros2_workspace/src/px4_dev_examples').rglob('*.py')) + list(Path('docker').glob('*.py')) + list(Path('tests').glob('*.py')) + list(Path('tools').rglob('*.py')):
    ast.parse(path.read_text(), filename=str(path))
import xml.etree.ElementTree as ET
for path in Path('Projects/ros2_workspace/src/px4_dev_examples/simulation').rglob('*.sdf'):
    ET.parse(path)
print('Shell syntax, Python parsing and simulation SDF XML passed.')
PY
if command -v shellcheck >/dev/null 2>&1; then
    shellcheck --severity=warning -e SC1091 docker/*.sh Commands/bin/* ./*.sh px4_ros2_vnc_image/*.sh px4_ros2_novnc_image/*.sh tests/*.sh
fi
