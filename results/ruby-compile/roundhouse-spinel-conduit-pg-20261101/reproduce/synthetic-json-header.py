"""Compile and serve an independent two-controller JSON response repro using a recorded toolchain."""
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import urllib.request

W = Path(__file__).resolve().parent.parent
OUT = Path(os.environ["PROBE_BUILD_DIR"]).resolve()
OUT.mkdir(parents=True, exist_ok=True)
case, expected = sys.argv[1:3]
pins = json.loads((W / f'evidence/{case}-pins.json').read_text())
build = OUT / ('synthetic-' + case)
build.mkdir(parents=True, exist_ok=True)
prefix = 'conduit-v14-synthetic-' + case
record = dict(case=case, fixture='synthetic-json-header', toolchain=pins['toolchain_tag'],
              expected_content_type=expected, database='SQLite; synthetic fixture only')
output = OUT / f'{case}-synthetic-json-header.json'
if output.exists() and '--retry' not in sys.argv:
    raise SystemExit('Preserving existing synthetic record; a retry must archive it first')
if '--reuse-build' in sys.argv:
    assert (build / 'runtime/server').exists()
    record.update(compile_exit=0, reused_native_after_packaging_repair=True)
else:
    result = subprocess.run(['docker', 'run', '--rm', '--name', prefix + '-compile',
        '--mount', f'type=bind,source={W / "evidence/synthetic-json-header"},target=/source,readonly',
        '--mount', f'type=bind,source={build},target=/output',
        pins['toolchain_tag'], 'bash', '/source/build.sh'])
    record['compile_exit'] = result.returncode
    if result.returncode:
        output.write_text(json.dumps(record, indent=2) + '\n')
        raise SystemExit(result.returncode)
(build / 'runtime/storage').mkdir(parents=True, exist_ok=True)

def docker(*args, check=True):
    return subprocess.run(['docker', *args], capture_output=True, text=True, check=check, timeout=130)

try:
    docker('run', '-d', '--name', prefix + '-server', '-p', '127.0.0.1:4501:8080',
           '--mount', f'type=bind,source={build / "runtime"},target=/app', '-w', '/app',
           '-e', 'PORT=8080', '-e', 'SECRET_KEY_BASE=' + '0123456789abcdef' * 8,
           pins['toolchain_tag'], '/app/server', '--binding', '0.0.0.0')
    deadline = time.monotonic() + 120
    while True:
        try:
            request = urllib.request.Request('http://127.0.0.1:4501/probe', headers={'Accept': 'application/json'})
            with urllib.request.urlopen(request, timeout=2) as response:
                record.update(status=response.status, content_type=response.headers.get('Content-Type'),
                              body=json.loads(response.read().decode()))
                break
        except Exception:
            if docker('inspect', '--format', '{{.State.Running}}', prefix + '-server').stdout.strip() != 'true':
                raise RuntimeError('Synthetic server exited')
            if time.monotonic() >= deadline:
                raise RuntimeError('Synthetic HTTP readiness failed')
            time.sleep(.2)
    record['server_sha256'] = docker('exec', prefix + '-server', 'sha256sum', '/app/server').stdout.split()[0]
    record['pass'] = record['status'] == 200 and record['body'] == {'ok': True} and record['content_type'] == expected
except Exception as error:
    record.update({'pass': False, 'error_name': type(error).__name__})
finally:
    log = docker('logs', prefix + '-server', check=False)
    (OUT / f'{case}-synthetic-json-header-app.log').write_text(log.stdout + log.stderr)
    docker('rm', '-f', prefix + '-server', check=False)
    (OUT / f'{case}-synthetic-json-header.json').write_text(json.dumps(record, indent=2) + '\n')
print(json.dumps({k: record.get(k) for k in ['case', 'compile_exit', 'status', 'content_type', 'pass', 'error_name']}))
raise SystemExit(0 if record.get('pass') else 1)
