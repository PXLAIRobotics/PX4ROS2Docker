"""Local tutorial checks: links/assets, Python syntax, route geometry and CSV math."""
import ast
from pathlib import Path
import re
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
for path in (ROOT/'ExampleCode/tutorial').glob('*.py'):
    ast.parse(path.read_text(), filename=str(path))
for path in [ROOT/'README.md', ROOT/'ExampleCode/README.md', *(ROOT/'docs/tutorial').rglob('*.md')]:
    for target in re.findall(r'!?\[[^\]]*\]\(([^)]+)\)', path.read_text()):
        if '://' in target or target.startswith('#'):
            continue
        destination = (path.parent/target.split('#')[0]).resolve()
        assert destination.exists(), f'{path}: missing {target}'

# Test the pure route function without importing ROS on the host.
source = ast.parse((ROOT/'ExampleCode/tutorial/fly_square.py').read_text())
function = next(node for node in source.body if isinstance(node, ast.FunctionDef) and node.name == 'square_offsets')
namespace = {}
exec(compile(ast.Module(body=[function], type_ignores=[]), '<route>', 'exec'), namespace)
route = namespace['square_offsets'](2)
assert route == [(2, 0), (2, 2), (0, 2), (0, 0)]
assert all(sum((a-b)**2 for a,b in zip(p,q)) == 4 for p,q in zip([(0,0),*route],route))
with tempfile.TemporaryDirectory() as folder:
    path = Path(folder)/'flight.csv'
    path.write_text('stage,error_m\nwaypoint_1,3\nwaypoint_1,4\n')
    result = subprocess.run([sys.executable, str(ROOT/'ExampleCode/tutorial/analyze_flight.py'),str(path)], check=True, capture_output=True, text=True)
    assert 'mean=3.500' in result.stdout and 'RMSE=3.536' in result.stdout
    path.write_text('stage,error_m\n')
    assert subprocess.run([sys.executable,str(ROOT/'ExampleCode/tutorial/analyze_flight.py'),str(path)],capture_output=True).returncode != 0
print('PASS: tutorial links, images, script syntax, square route and offline CSV analysis')
