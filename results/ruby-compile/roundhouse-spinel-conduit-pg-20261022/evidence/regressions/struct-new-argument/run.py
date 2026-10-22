"""Observe Ruby conformance on the actual production toolchain image."""
import json
from pathlib import Path
import subprocess
import sys

rows = []
for source in sorted(Path('.').glob('*.rb')):
    row = {'source': str(source)}
    extra = ['--rbs', str(Path('seeds') / source.stem)] if (Path('seeds') / source.stem).is_dir() else []
    for label, args in [('cruby', ['ruby', str(source)]),
                        ('types', ['spinel', '--emit-rbs', str(source), '-o', '/tmp/types.rbs', *extra]),
                        ('compile', ['spinel', '--cc=clang', str(source), '-o', '/tmp/probe', *extra])]:
        result = subprocess.run(args, capture_output=True, text=True, timeout=90)
        row[label] = dict(exit=result.returncode, stdout=result.stdout, stderr=result.stderr)
        if label == 'types' and result.returncode == 0:
            row['inferred'] = Path('/tmp/types.rbs').read_text()
    if row['compile']['exit'] == 0:
        result = subprocess.run(['/tmp/probe'], capture_output=True, text=True, timeout=10)
        row['compiled'] = dict(exit=result.returncode, stdout=result.stdout, stderr=result.stderr)
        row['matches_cruby'] = row['compiled'] == row['cruby']
    rows.append(row)
    print(json.dumps(row), flush=True)
Path(sys.argv[1] if len(sys.argv) > 1 else 'results.json').write_text(json.dumps(rows, indent=2) + '\n')
