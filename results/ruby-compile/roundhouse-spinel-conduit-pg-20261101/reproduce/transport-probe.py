"""Check old patch-10 transport behavior through real HTTP and two independent socket peers.

Run under the shared Docker lock. The frozen gate is unchanged; this is a supplemental correctness probe.
"""
import collections
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import urllib.error
import urllib.request

W = Path(__file__).resolve().parent.parent
OUT = Path(os.environ["PROBE_BUILD_DIR"]).resolve()
OUT.mkdir(parents=True, exist_ok=True)
case = sys.argv[1]
pins = json.loads((W / f'evidence/{case}-pins.json').read_text())
prefix = f'conduit-v14-transport-{case}'
net, db, app, client_a, client_b = [prefix + suffix for suffix in ['-net', '-db', '-app', '-client-a', '-client-b']]
record = dict(case=case, condition='supplemental-old-patch-10-transport', image=pins['compiled_tag'],
              procedure='Two clients remain alive on one Docker network so their socket peer addresses stay distinct.')
output = OUT / f'{case}-transport.json'
if output.exists():
    raise SystemExit('Preserving existing transport probe')

def docker(*args, check=True):
    p = subprocess.run(['docker', *args], capture_output=True, text=True, timeout=130)
    if check and p.returncode:
        raise RuntimeError('Docker operation failed: ' + ' '.join(args[:2]))
    return p

def request(path, body=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request('http://127.0.0.1:4501' + path, data=data,
                                 headers={'Accept': 'application/json', 'Content-Type': 'application/json'})
    try:
        response = urllib.request.urlopen(req, timeout=3)
    except urllib.error.HTTPError as error:
        response = error
    with response:
        payload = response.read().decode()
        return dict(status=response.status, content_type=response.headers.get('Content-Type'),
                    body=json.loads(payload))

def client_request(client):
    body = json.dumps({'user': {'email': 'transport@example.invalid', 'password': 'wrongpassword'}})
    result = docker('exec', client, 'curl', '-sS', '--max-time', '10', '-o', '/tmp/transport-response.json',
                    '-w', '%{http_code}', '-H', 'Content-Type: application/json', '--data', body,
                    'http://app:8080/api/users/login')
    return int(result.stdout.strip())

try:
    record['image_id'] = docker('image', 'inspect', '--format', '{{.Id}}', pins['compiled_tag']).stdout.strip()
    docker('network', 'create', net)
    docker('run', '-d', '--name', db, '--network', net, '--network-alias', 'db',
           '--tmpfs', '/var/lib/postgresql/data:rw,size=256m',
           '-e', 'POSTGRES_PASSWORD=postgres', '-e', 'POSTGRES_DB=conduit', 'conduit-v14-postgres:17')
    deadline = time.monotonic() + 120
    while docker('exec', db, 'pg_isready', '-h', '127.0.0.1', '-U', 'postgres', '-d', 'conduit', check=False).returncode:
        if time.monotonic() >= deadline:
            raise RuntimeError('Database readiness failed')
        time.sleep(.2)
    docker('run', '-d', '--name', app, '--network', net, '--network-alias', 'app',
           '-p', '127.0.0.1:4501:8080', '-e', 'DATABASE_URL=postgres://postgres:postgres@db:5432/conduit',
           '-e', 'SECRET_KEY_BASE=' + '0123456789abcdef' * 8, '-e', 'PORT=8080', pins['compiled_tag'])
    deadline = time.monotonic() + 120
    while True:
        try:
            tags = request('/api/tags')
            if tags['status'] == 200:
                break
        except Exception:
            pass
        if time.monotonic() >= deadline:
            raise RuntimeError('HTTP readiness failed')
        time.sleep(.2)
    record['json_response'] = tags
    registered = request('/api/users', {'user': {'username': 'transport', 'email': 'transport@example.invalid',
                                                'password': 'password123'}})
    record['registration_status'] = registered['status']
    if registered['status'] != 201:
        raise RuntimeError('Synthetic registration failed')
    for client in [client_a, client_b]:
        docker('run', '-d', '--name', client, '--network', net, pins['toolchain_tag'], 'sleep', '300')
    record['peer_addresses'] = {name: docker('inspect', '--format',
        '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}', client).stdout.strip()
        for name, client in [('a', client_a), ('b', client_b)]}
    assert record['peer_addresses']['a'] != record['peer_addresses']['b']
    first = [client_request(client_a) for _ in range(20)]
    record['client_a_first_twenty_status_counts'] = dict(collections.Counter(first))
    record['client_b_first_status'] = client_request(client_b)
    record['client_b_first_body'] = json.loads(docker('exec', client_b, 'cat', '/tmp/transport-response.json').stdout)
    record['client_a_twenty_first_status'] = client_request(client_a)
    record['checks'] = {
        'json_utf8_content_type': tags['content_type'] == 'application/json; charset=utf-8',
        'first_twenty_not_limited': all(status == 401 for status in first),
        'new_socket_peer_has_own_budget': record['client_b_first_status'] == 401,
        'original_socket_peer_is_limited': record['client_a_twenty_first_status'] == 429,
    }
    record['server_sha256'] = docker('exec', app, 'sha256sum', '/app/server').stdout.split()[0]
    record['pass'] = all(record['checks'].values())
except Exception as error:
    record.update({'pass': False, 'error': type(error).__name__ + ': ' + str(error)})
finally:
    logs = docker('logs', app, check=False)
    (OUT / f'{case}-transport-app.log').write_text(logs.stdout + logs.stderr)
    docker('rm', '-f', client_a, client_b, app, db, check=False)
    docker('network', 'rm', net, check=False)
    output.write_text(json.dumps(record, indent=2) + '\n')
checks = record.get('checks', {})
print(json.dumps(dict(case=case, passed=sum(checks.values()), total=len(checks),
                     failing_names=[name for name, value in checks.items() if not value],
                     pass_=record.get('pass', False))))
raise SystemExit(0 if record.get('pass') else 1)
