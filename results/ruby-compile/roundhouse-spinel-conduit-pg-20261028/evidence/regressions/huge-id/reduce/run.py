"""Compile and run every probe here with spinel and CRuby; write <label>.json."""
import json
import subprocess
import sys
from pathlib import Path

rows = []
for source in sorted(Path('/probes').glob('*.rb')):
    row = {'source': source.name}
    for kind, cmd in [('ruby', ['ruby', str(source)]),
                      ('compile', ['spinel', '--cc=clang', str(source), '-o', '/tmp/repro'])]:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        row[kind] = {'exit': r.returncode, 'stdout': r.stdout, 'stderr': r.stderr[-2000:]}
    if row['compile']['exit'] == 0:
        r = subprocess.run(['/tmp/repro'], capture_output=True, text=True, timeout=20)
        row['native'] = {'exit': r.returncode, 'stdout': r.stdout, 'stderr': r.stderr[-2000:]}
    row['matches_cruby'] = (row.get('native', {}).get('stdout') == row['ruby']['stdout']
                            and row.get('native', {}).get('exit') == row['ruby']['exit'])
    rows.append(row)
    print(json.dumps({'source': source.name, 'matches_cruby': row['matches_cruby'],
                      'native': row.get('native', row['compile'])}), flush=True)
Path('/probes/' + sys.argv[1] + '.json').write_text(json.dumps(rows, indent=2) + '\n')
