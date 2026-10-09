"""Supplemental boot-recovery condition; run under the shared Docker lock."""
import json, os, shutil, subprocess, sys, time, urllib.request
from pathlib import Path

here = Path(__file__).resolve()
if here.parent.name == 'recovery':
    pkg = here.parents[2]
    root = Path(os.environ.get('RECOVERY_BUILD_DIR', str(pkg / 'reproduce/build'))).resolve()
else:
    root = here.parents[1]
    pkg = root / 'package/results/ruby-compile/roundhouse-spinel-conduit-pg-20261009'
(root / 'logs').mkdir(parents=True, exist_ok=True)
os.environ.setdefault('CONDUIT_V8B_DOCKER_REAL', shutil.which('docker'))
os.environ.setdefault('CONDUIT_V8B_HANG_FILE', str(root / 'logs/docker-start-hang.json'))
os.environ['PATH'] = str(pkg / 'reproduce/bin') + os.pathsep + os.environ['PATH']
label, image, expected = sys.argv[1:4]
net, db, app = ['conduit-v8b-recovery-' + label + suffix for suffix in ('-net', '-db', '-app')]
record = {'condition': 'supplemental-pending-export-boot-20261009', 'label': label,
          'image': image, 'expected': expected,
          'procedure': 'Seed a durable pending export before starting the compiled server; send no enqueue request.'}

def run(args, check=True, **kwargs):
    p = subprocess.run(['docker', *args], capture_output=True, text=True, timeout=130, **kwargs)
    if check and p.returncode:
        raise RuntimeError(str(args[:3]) + ': ' + p.stderr[-3000:])
    return p

def sql(text):
    return run(['exec', '-i', db, 'psql', '-v', 'ON_ERROR_STOP=1', '-U', 'postgres', '-d', 'conduit', '-At'], input=text).stdout.strip()

try:
    record['image_id'] = run(['image', 'inspect', '--format', '{{.Id}}', image]).stdout.strip()
    run(['network', 'create', net])
    run(['run', '-d', '--name', db, '--network', net, '--network-alias', 'db',
         '--mount', 'type=volume,source=' + db + '-data,target=/var/lib/postgresql/data',
         '-e', 'POSTGRES_PASSWORD=postgres', '-e', 'POSTGRES_DB=conduit', 'conduit-v8b-postgres:17'])
    deadline = time.monotonic() + 120
    while run(['exec', db, 'pg_isready', '-h', '127.0.0.1', '-U', 'postgres', '-d', 'conduit'], False).returncode:
        if time.monotonic() >= deadline:
            raise RuntimeError('Database readiness exceeded startup limit')
        time.sleep(.2)
    sql((pkg / 'variant/source/db/structure.sql').read_text())
    sql("INSERT INTO users(username,email,password_digest,created_at,updated_at) VALUES ('recovery','recovery@example.invalid','unused',now(),now());\n"
        "INSERT INTO article_exports(user_id,status,created_at,updated_at) VALUES (1,'pending',now(),now());")
    record['before'] = sql('SELECT status FROM article_exports WHERE id=1;')
    run(['run', '-d', '--name', app, '--network', net, '-p', '127.0.0.1:4451:8080',
         '-e', 'DATABASE_URL=postgres://postgres:postgres@db:5432/conduit',
         '-e', 'SECRET_KEY_BASE=' + '0123456789abcdef' * 8, '-e', 'PORT=8080', image])
    deadline = time.monotonic() + 120
    while True:
        if run(['inspect', '--format', '{{.State.Running}}', app]).stdout.strip() != 'true':
            raise RuntimeError('Compiled server exited')
        try:
            with urllib.request.urlopen('http://127.0.0.1:4451/api/tags', timeout=2) as response:
                if response.status == 200:
                    break
        except Exception:
            pass
        if time.monotonic() >= deadline:
            marker = root / 'logs/docker-start-hang.json'
            marker.write_text(json.dumps({'container': app, 'operation': 'HTTP readiness', 'startup_limit_seconds': 120}) + '\n')
            raise RuntimeError('Container startup exceeded 120 seconds; stop Docker work')
        time.sleep(.2)
    deadline = time.monotonic() + 10
    while True:
        record['after'] = sql('SELECT status FROM article_exports WHERE id=1;')
        if record['after'] == 'done' or time.monotonic() >= deadline:
            break
        time.sleep(.2)
    record['articles'] = sql('SELECT articles::text FROM article_exports WHERE id=1;')
    record['completed'] = sql('SELECT completed_at IS NOT NULL FROM article_exports WHERE id=1;')
    record['server_sha256'] = run(['exec', app, 'sha256sum', '/app/server']).stdout.split()[0]
    record['pass'] = record['after'] == expected
except Exception as error:
    record.update({'pass': False, 'error': str(error)})
finally:
    log = run(['logs', app], False)
    (root / 'logs' / ('recovery-' + label + '-app.log')).write_text(log.stdout + log.stderr)
    run(['stop', '--time', '5', app, db], False)
    run(['rm', app, db], False)
    run(['volume', 'rm', db + '-data'], False)
    run(['network', 'rm', net], False)
    (root / 'logs' / ('recovery-' + label + '.json')).write_text(json.dumps(record, indent=2) + '\n')
print(json.dumps(record, indent=2), flush=True)
raise SystemExit(0 if record['pass'] else 1)
