"""Fresh isolated sessions for sequential and one-shot language lanes.

Commands: freeze STACK; prepare STACK PHASE; isolation SESSION; run SESSION;
          publish SESSION; pipeline STACK [--through 8]; one-shot STACK
PHASE is 1..8 or one-shot. Sessions and published sources are immutable.
"""
import argparse
import hashlib
import json
import os
import re
import secrets
import shutil
import socket
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import one_shot
import workdir

ROOT = Path(__file__).resolve().parent.parent
LANES = ROOT / '.work/lanes'
SKIP = {'.git', '.venv', '__pycache__', '.pytest_cache', '.ruff_cache', 'node_modules',
        'dist', 'tmp', 'log', 'coverage', '.checks', '.scaffold', 'realworld_spec',
        'security', 'harness', 'perf', '.air', 'vendor', '.cache'}
INPUT_NAMES = {'PROMPT.md', 'ENVIRONMENT.md', 'MEASUREMENT.md', 'EXPERIMENT.md', 'FIXTURE.json'}
SOURCE_SUFFIXES = {'.py', '.go', '.sql', '.toml', '.sh', '.json', '.yaml', '.yml',
                   '.md', '.mod', '.sum', '.lock', '.txt', '.html', '.ini', '.cfg'}
SOURCE_NAMES = {'Dockerfile', '.dockerignore', '.gitignore', 'Makefile', 'Procfile',
                'go.mod', 'go.sum', 'uv.lock', '.air.toml', '.python-version'}


def stamp():
    return datetime.now(timezone.utc).isoformat()


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def fingerprint(files):
    return hashlib.sha256(json.dumps(files, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def save(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + '\n')


def load(path):
    return json.loads(Path(path).read_text())


def checked_files(base, excludes=()):
    base = Path(base)
    for directory, dirs, files in os.walk(base):
        dirs[:] = sorted(d for d in dirs if d not in excludes)
        for name in dirs:
            if (Path(directory)/name).is_symlink():
                raise RuntimeError(f'Symlink directory not permitted: {Path(directory)/name}')
        for name in sorted(files):
            path = Path(directory) / name
            if path.is_symlink():
                raise RuntimeError(f'Symlink not permitted in fixture/source: {path.relative_to(base)}')
            if path.suffix != '.pyc' and name != '.DS_Store':
                yield path


def source_snapshot(stack):
    paths = set()
    folders = [ROOT/'steps', ROOT/'spec', ROOT/'one-shot/frontend', ROOT/'one-shot/harness',
               ROOT/'tools/one_shot_host', ROOT/'tools/lane_host', ROOT/'tools/security/hurl',
               ROOT/'tools/bench', ROOT/'stacks'/stack/'scaffold']
    for folder in folders:
        paths.update(checked_files(folder, SKIP - {'.scaffold', 'realworld_spec', 'security', 'harness', 'perf'}))
    for name in ['lane_run.py', 'lane_broker.py', 'lane_check.py', 'measure.py', 'scrub.py',
                 'one_shot.py', 'workdir.py', f'{stack}_track_preflight.py']:
        paths.add(ROOT/'tools'/name)
    for name in ['stack.json', 'runtime.json', 'ENVIRONMENT.md', 'PROVENANCE.md', 'STACK.md', 'SELECTION.md', 'Dockerfile.toolchain', '.dockerignore']:
        path = ROOT/'stacks'/stack/name
        if path.exists(): paths.add(path)
    for name in ['PROMPT.md', 'MEASUREMENT.md']:
        paths.add(ROOT/'one-shot-v2-expert'/name)
    paths.add(ROOT/f'one-shot-v2-{stack}-expert/ENVIRONMENT.md')
    files = {str(p.relative_to(ROOT)): digest(p) for p in sorted(paths)}
    modes = {str(p.relative_to(ROOT)): p.stat().st_mode & 0o111 for p in sorted(paths)}
    return {'sha256': fingerprint({'files': files, 'modes': modes}), 'files': files, 'modes': modes}


def freeze(stack):
    runtime = load(ROOT/'stacks'/stack/'runtime.json')
    preflight_path = ROOT/'results/lanes'/stack/'preflight.json'
    proof = load(preflight_path)
    image = subprocess.check_output(['docker', 'image', 'inspect', runtime['image'], '--format', '{{.Id}}'], text=True).strip()
    if not proof.get('passed') or proof.get('toolchain_image_id') != image:
        raise RuntimeError('Preflight must pass for the exact toolchain image')
    scaffold = ROOT/'stacks'/stack/'scaffold'
    actual = {str(p.relative_to(scaffold)):digest(p) for p in checked_files(scaffold, SKIP)}
    if proof.get('scaffold_files') and proof['scaffold_files'] != actual:
        raise RuntimeError('Scaffold differs from preflight evidence')
    record = source_snapshot(stack)
    record.update(toolchain_image_id=image, browser_image_id=one_shot.image_id(),
                  preflight_sha256=digest(preflight_path), frozen_at=stamp())
    path = ROOT/'stacks'/stack/'lane-fixture.json'
    if path.exists():
        old = load(path)
        for key in ('sha256', 'toolchain_image_id', 'browser_image_id', 'preflight_sha256'):
            if old[key] != record[key]:
                raise RuntimeError('Fixture changed; preserve the existing run and use a new condition')
        return old
    save(path, record)
    print(f'{stack}: frozen {record["sha256"]}', flush=True)
    return record


def verify_source(stack):
    frozen = load(ROOT/'stacks'/stack/'lane-fixture.json')
    now = source_snapshot(stack)
    if now['sha256'] != frozen['sha256']:
        changed = [p for p in set(now['files']) | set(frozen['files']) if now['files'].get(p) != frozen['files'].get(p)]
        raise RuntimeError(f'Frozen lane sources changed: {changed}')
    return frozen


def copy_tree(src, dst):
    shutil.copytree(src, dst, ignore=shutil.ignore_patterns(*SKIP, '*.pyc', '.DS_Store'))
    for p in dst.rglob('*'):
        if p.is_file(): p.chmod(p.stat().st_mode | 0o200)


def home_config(work, frozen):
    sock = Path.home()/'.orbstack/run/docker.sock'
    rules = '\n'.join(f'{json.dumps(str(work/part))} = "read"' for part in frozen)
    return f'''approval_policy = "never"
default_permissions = "workspace-only"
allow_login_shell = false
[features]
memories = false
multi_agent = false
apps = false
hooks = false
plugins = false
network_proxy = true
browser_use = false
computer_use = false
[permissions.workspace-only]
extends = ":workspace"
[permissions.workspace-only.filesystem]
":root" = "deny"
":minimal" = "read"
"/opt/homebrew" = "read"
"/etc/resolv.conf" = "read"
"/var/run/docker.sock" = "deny"
"{sock}" = "deny"
{rules}
[permissions.workspace-only.network]
enabled = true
[permissions.workspace-only.network.unix_sockets]
"/var/run/docker.sock" = "deny"
"{sock}" = "deny"
[permissions.workspace-only.network.domains]
"*" = "allow"
"127.0.0.1" = "allow"
[projects."{ROOT}"]
trust_level = "trusted"
'''


def make_home(home, config):
    home.mkdir(mode=0o700)
    shutil.copy2(Path.home()/'.codex/auth.json', home/'auth.json')
    (home/'auth.json').chmod(0o600)
    (home/'config.toml').write_text(config)
    (home/'config.toml').chmod(0o600)


def wrapper(path, action, port, *, dynamic=False):
    path.parent.mkdir(parents=True, exist_ok=True)
    # Resolve work root without trusting callers' current directory.
    if dynamic:
        body = f'''#!/usr/bin/env bash
set -euo pipefail
root="$(cd "$(dirname "$0")/.." && pwd)"
action="${{1:?usage: run COMMAND...|start|stop|logs|test|lint|build}}"
shift
exec python3 "$root/harness/check-client.py" "$action" {port} "$@"
'''
    else:
        # Absolute fixture path is intentional and disclosed: wrappers run on host in one fixed workspace.
        root = next(p for p in path.parents if p.name == 'app')
        body = f'#!/usr/bin/env bash\nset -euo pipefail\nexec python3 "{root}/harness/check-client.py" {action} {port}\n'
    path.write_text(body)
    path.chmod(0o755)


def session_path(stack, phase):
    label = 'one-shot' if phase == 'one-shot' else workdir.step_name(int(phase))
    return LANES/f'{stack}-{label}-1/control/session.json'


def prepare(stack, phase):
    fixture = verify_source(stack)
    runtime = load(ROOT/'stacks'/stack/'runtime.json')
    oneshot = phase == 'one-shot'
    n = 8 if oneshot else int(phase)
    label = 'one-shot' if oneshot else workdir.step_name(n)
    sid = f'{stack}-{label}-1'
    base = LANES/sid
    path = base/'control/session.json'
    if base.exists():
        if path.exists():
            verify_workspace(load(path))
            prewarm(path)
            return path
        raise RuntimeError(f'Incomplete existing session: {base}')
    previous = None
    if not oneshot and n > 1:
        prev = load(session_path(stack, str(n-1)))
        verification = load(Path(prev['result'])/'verification.json')
        if not verification.get('passed'):
            raise RuntimeError('Previous step must independently pass before continuing')
        previous = Path(prev['publish_source'])
    work, home, control, logs = (base/p for p in ('app','home','control','logs'))
    base.mkdir(parents=True)
    scaffold = ROOT/'stacks'/stack/'scaffold'
    copy_tree(previous or scaffold, work)
    copy_tree(scaffold, work/'.scaffold')
    spec = work/'realworld_spec'
    for part in ('api','docs','bin'):
        shutil.copytree(ROOT/'spec'/part, spec/part)
    for feature, available in workdir.FEATURES.items():
        if n >= available:
            shutil.copytree(ROOT/'spec/features'/feature, spec/'features'/feature,
                            ignore=shutil.ignore_patterns('validation'))
    if n == 8:
        shutil.copytree(ROOT/'one-shot/frontend', spec/'frontend',
                        ignore=shutil.ignore_patterns('node_modules','dist','test-results','playwright-report'))
    harness = work/'harness'
    harness.mkdir()
    shutil.copy2(ROOT/'one-shot/harness/check-client.py', harness/'check-client.py')
    shutil.copy2(ROOT/'one-shot/harness/run-live-container.sh', harness/'run-live-container.sh')
    (harness/'browser-image-id').write_text(fixture['browser_image_id']+'\n')
    (harness/'README.md').write_text(f'''# Fixed checks and toolchain\n\nThis session exposes only phase {label} inputs.\n`harness/{stack}.sh run COMMAND...` executes in the warmed Linux toolchain at /work/app.\n`harness/{stack}.sh start|logs|stop|test|lint|build` manage this workspace only.\n`harness/check-development.sh` owns a fresh PostgreSQL database, starts the app, runs all applicable frozen gates, lint and tests, then cleans up.\n`harness/check-all.sh {runtime['port']}` checks a running server.\n`harness/check-production.sh {runtime['port']}` builds and checks a fresh production image.\n`harness/db.sh start|stop {runtime['port']}` manages the development database.\nNo Docker socket is exposed. Dependencies may be installed inside the toolchain.\n''')
    wrapper(harness/f'{stack}.sh', '', runtime['port'], dynamic=True)
    for name, action in [('check-development.sh','development'),('check-all.sh','all'),
                         ('check-api.sh','api'),('check-production.sh','production'),
                         ('check-security.sh','security'),('check-live.sh','live')]:
        wrapper(harness/name, action, runtime['port'])
    (harness/'db.sh').write_text(f'''#!/usr/bin/env bash
set -euo pipefail
root="$(cd "$(dirname "$0")/.." && pwd)"
exec python3 "$root/harness/check-client.py" "db-${{1:?start or stop}}" {runtime['port']}
''')
    (harness/'db.sh').chmod(0o755)
    wrapper(spec/'bin/run-hurl', 'api', runtime['port'])
    if n==8: wrapper(spec/'features/live-editing/bin/check','live',runtime['port'])
    env_source = ROOT/(f'one-shot-v2-{stack}-expert' if oneshot else f'stacks/{stack}')/'ENVIRONMENT.md'
    shutil.copy2(env_source, work/'ENVIRONMENT.md')
    prompt = ROOT/('one-shot-v2-expert/PROMPT.md' if oneshot else f'steps/{label}.md')
    shutil.copy2(prompt, work/'PROMPT.md')
    shutil.copy2(ROOT/'one-shot-v2-expert/MEASUREMENT.md', work/'MEASUREMENT.md')
    (work/'EXPERIMENT.md').write_text(f'''# {stack}: {label}\n\nCondition: prepared scaffold, isolated fresh session, {'expert v2 one-shot' if oneshot else 'original eight-step prompt'}.\nThe maintainer supplies a product-free scaffold and frozen `.scaffold` snapshot after environment preflight. This is not a claim that the product already passes. Implement the current prompt.\nThe shared prompt bytes are unchanged. Runtime instructions in ENVIRONMENT adapt historical Docker commands to the fixed broker.\nPort {runtime['port']}; dependencies may be installed inside the toolchain. The client, specification, harness and inputs are read-only. No access to parent or sibling workspaces.\nOne-shot sessions start from the scaffold, never a sequential implementation. Each sequential session starts from the independently checked previous snapshot.\n''')
    frozen = ['realworld_spec','harness','.scaffold',*sorted(INPUT_NAMES)]
    if n >= 4:
        perf = work/'perf'; perf.mkdir()
        for name in ('bench.py','load.js','seed.py'):
            shutil.copy2(ROOT/'tools/bench'/name, perf/name)
        wrapper(perf/'bench.sh','benchmark',runtime['port'])
        frozen.extend('perf/'+name for name in ('bench.py','load.js','seed.py','bench.sh'))
        if not oneshot and n == 4:
            prior = load(session_path(stack,'3'))
            src = Path(prior['work'])/'perf/latest/results.json'
            if not src.exists(): src = Path(prior['work'])/'.checks/perf/latest/results.json'
            if not src.exists(): raise RuntimeError('Step 3 benchmark required before step 4')
            (perf/'baseline').mkdir(); shutil.copy2(src,perf/'baseline/results.json')
            frozen.append('perf/baseline')
    if n >= 5:
        shutil.copytree(ROOT/'tools/security/hurl',work/'security/hurl')
        wrapper(work/'security/run-hurl.sh','security',runtime['port'])
        frozen.extend(['security/hurl','security/run-hurl.sh'])
        if not oneshot and n == 5:
            prior = load(session_path(stack,'4'))
            src = Path(prior['work'])/'.checks/security/latest/results.json'
            if not src.exists(): raise RuntimeError('Step 4 security baseline required before step 5')
            (work/'security/baseline').mkdir(); shutil.copy2(src,work/'security/baseline/results.json')
            frozen.append('security/baseline')
    files = {}
    for part in frozen:
        p = work/part
        if part == 'FIXTURE.json': continue
        for f in checked_files(p) if p.is_dir() else [p]:
            files[str(f.relative_to(work))] = digest(f)
    previous_hash = fingerprint({str(p.relative_to(previous)):digest(p) for p in checked_files(previous)}) if previous else None
    record = dict(stack=stack,condition='expert-v2' if oneshot else 'eight-step-prepared-scaffold',
                  phase=label,fixture_sha256=fixture['sha256'],prompt_sha256=digest(work/'PROMPT.md'),
                  previous_source_sha256=previous_hash,toolchain_image_id=fixture['toolchain_image_id'],
                  browser_image_id=fixture['browser_image_id'],files=files)
    save(work/'FIXTURE.json',record)
    for part in frozen:
        one_shot.readonly(work/part) if (work/part).is_dir() else (work/part).chmod((work/part).stat().st_mode & ~0o222)
    make_home(home,home_config(work,frozen))
    control.mkdir(mode=0o700)
    (control/'token').write_text(secrets.token_hex(32)+'\n'); (control/'token').chmod(0o600)
    result = ROOT/f'results/one-shot-v2-{stack}-expert/pilot-1' if oneshot else ROOT/'results/lanes'/stack/label
    source = result/'source' if oneshot else ROOT/'stacks'/stack/label
    runtime['volumes'] = [dict(v, name=f'{sid}-{v["name"]}') for v in runtime.get('volumes', [])]
    session = dict(runtime,id=sid,stack=stack,phase=label,number=n,work=str(work),home=str(home),
                   control=str(control),logs=str(logs),frozen=frozen,result=str(result),
                   publish_source=str(source),broker_port=49680+(stack=='python'),
                   fixture_sha256=fixture['sha256'],fixture_file_sha256=digest(work/'FIXTURE.json'))
    save(path,session)
    verify_workspace(session)
    prewarm(path)
    print(f'prepared {sid}',flush=True)
    return path


def prewarm(path):
    session=load(path)
    marker=Path(session['control'])/'dependency-prewarm.json'
    if marker.exists():
        if not load(marker).get('passed'): raise RuntimeError('Dependency preparation failed previously')
        return
    import lane_broker
    scoped=lane_broker.Session(path)
    with lane_broker.resources():
        scoped.verify()
        rc,text=scoped.tool('prepare')
        scoped.verify()
    (Path(session['control'])/'dependency-prewarm.log').write_text(text)
    save(marker,{'passed':rc==0,'exit':rc,'prepared_at':stamp()})
    if rc: raise RuntimeError('Dependency preparation failed before measured launch')


def verify_workspace(session):
    work = Path(session['work'])
    if digest(work/'FIXTURE.json') != session['fixture_file_sha256']:
        raise RuntimeError('Fixture record changed')
    for rel, sha in load(work/'FIXTURE.json')['files'].items():
        path = work/rel
        if path.is_symlink() or not path.is_file() or digest(path) != sha:
            raise RuntimeError(f'Frozen input changed: {rel}')


def environment(home):
    env = {k:os.environ[k] for k in ('PATH','HOME','USER','LOGNAME','SHELL','TMPDIR','LANG') if k in os.environ}
    env['CODEX_HOME'] = str(home)
    return env


def isolation(path):
    session = load(path); base=Path(session['control']).parent/'isolation'
    output = Path(session['control'])/'isolation.json'
    if output.exists():
        proof=load(output)
        if proof.get('passed') and proof['home_config_sha256']==digest(Path(session['home'])/'config.toml'): return proof
        raise RuntimeError('Prior isolation probe failed')
    own,sibling,home=(base/p for p in ('own','sibling','home'))
    own.mkdir(parents=True); sibling.mkdir()
    (own/'own.txt').write_text('lane-own-marker')
    (own/'ENVIRONMENT.md').write_text('lane-frozen-marker')
    (own/'harness').mkdir(); (own/'harness/frozen.txt').write_text('lane-harness-marker')
    (sibling/'secret.txt').write_text('lane-sibling-secret')
    (base/'parent.txt').write_text('lane-parent-secret')
    config=(Path(session['home'])/'config.toml').read_text().replace(session['work'],str(own))
    make_home(home,config)
    code=f'''from pathlib import Path
import socket
for label,path in [('own','own.txt'),('sibling',{str(sibling/'secret.txt')!r}),('parent',{str(base/'parent.txt')!r})]:
    try:
        value=Path(path).read_text(); print(label+'='+value)
        if label=='own': Path('own-write.txt').write_text(value)
    except Exception as e: print(label+'='+type(e).__name__)
for label,action in [
    ('environment_write',lambda:Path('ENVIRONMENT.md').write_text('changed')),
    ('environment_chmod',lambda:Path('ENVIRONMENT.md').chmod(0o644)),
    ('environment_unlink',lambda:Path('ENVIRONMENT.md').unlink()),
    ('harness_write',lambda:Path('harness/frozen.txt').write_text('changed')),
    ('harness_unlink',lambda:Path('harness/frozen.txt').unlink()),
    ('harness_create',lambda:Path('harness/new.txt').write_text('new'))]:
    try: action(); print(label+'=succeeded')
    except Exception as e: print(label+'='+type(e).__name__)
for label,path in [('docker','/var/run/docker.sock'),('docker_resolved',{str(Path.home()/'.orbstack/run/docker.sock')!r})]:
    try:
        s=socket.socket(socket.AF_UNIX); s.settimeout(1); s.connect(path); print(label+'=connected')
    except Exception as e: print(label+'='+type(e).__name__)
'''
    prompt="Artificial isolation test: execute this command exactly once with the command tool. Do not use other tools. Report its output.\npython3 - <<'PY'\n"+code+"PY\n"
    command=['codex','exec','-C',str(own),'-m','gpt-6-sol','-c','model_reasoning_effort="low"',
             '--skip-git-repo-check','--json','-']
    result=subprocess.run(command,input=prompt,text=True,capture_output=True,env=environment(home),timeout=180)
    (base/'events.jsonl').write_text(result.stdout); (base/'stderr.log').write_text(result.stderr)
    outputs=[]
    for line in result.stdout.splitlines():
        try: row=json.loads(line)
        except json.JSONDecodeError: continue
        item=row.get('item',{})
        if row.get('type')=='item.completed' and item.get('type')=='command_execution': outputs.append(item.get('aggregated_output',''))
    text='\n'.join(outputs)
    labels=['sibling','parent','environment_write','environment_chmod','environment_unlink',
            'harness_write','harness_unlink','harness_create','docker','docker_resolved']
    checks={label:label+'=PermissionError' in text for label in labels}
    checks['own']= (own/'own-write.txt').exists() and (own/'own-write.txt').read_text()=='lane-own-marker'
    proof={'passed':all(checks.values()),'checks':checks,'exit':result.returncode,
           'home_config_sha256':digest(Path(session['home'])/'config.toml'),
           'fixture_sha256':session['fixture_sha256'],'tested_at':stamp()}
    save(output,proof)
    print(json.dumps(proof),flush=True)
    if not proof['passed']: raise RuntimeError(f'Isolation failed; inspect {base}')
    return proof


def usage(path):
    out={'input':0,'cached_input':0,'output':0,'reasoning_output':0,'commands':0,'failed_commands':0}
    for line in path.read_text().splitlines():
        try: row=json.loads(line)
        except json.JSONDecodeError: continue
        if row.get('type')=='turn.completed':
            for key,field in [('input','input_tokens'),('cached_input','cached_input_tokens'),('output','output_tokens'),('reasoning_output','reasoning_output_tokens')]:
                out[key]+=row.get('usage',{}).get(field,0)
        item=row.get('item') or {}
        if row.get('type')=='item.completed' and item.get('type')=='command_execution':
            out['commands']+=1; out['failed_commands']+=item.get('exit_code') not in (0,None)
    out['uncached_plus_output']=out['input']-out['cached_input']+out['output']
    return out


def launch(path):
    session=load(path); verify_source(session['stack']); verify_workspace(session)
    work,home,logs=(Path(session[k]) for k in ('work','home','logs'))
    if (logs/'events.jsonl').exists() or (home/'sessions').exists(): raise RuntimeError('Measured session already used')
    proof=isolation(path)
    if not proof['passed']: raise RuntimeError('Isolation required')
    token=(Path(session['control'])/'token').read_text().strip()
    env=environment(home)
    env.update(ONE_SHOT_BROKER_TOKEN=token,ONE_SHOT_BROKER_PORT=str(session['broker_port']))
    logs.mkdir(exist_ok=True)
    agent=load(ROOT/'stacks'/session['stack']/'stack.json').get('agent',{'model':'gpt-6-sol','reasoning':'xhigh'})
    command=['codex','exec','-C',str(work),'-m',agent['model'],'-c',f'model_reasoning_effort="{agent["reasoning"]}"',
             '--skip-git-repo-check','--json','-o',str(logs/'last.md'),'-']
    began,start=stamp(),time.monotonic()
    with (logs/'broker.log').open('w') as broker_log:
        broker=subprocess.Popen([sys.executable,str(ROOT/'tools/lane_broker.py'),'--session',str(path),'--port',str(session['broker_port'])],stdout=broker_log,stderr=subprocess.STDOUT)
        try:
            for _ in range(100):
                if broker.poll() is not None: raise RuntimeError('Broker exited; inspect broker.log')
                try:
                    with socket.create_connection(('127.0.0.1',session['broker_port']),timeout=.2): break
                except OSError: time.sleep(.1)
            else: raise RuntimeError('Broker did not listen')
            with (work/'PROMPT.md').open() as prompt,(logs/'events.jsonl').open('w') as events,(logs/'stderr.log').open('w') as stderr:
                process=subprocess.Popen(command,cwd=work,env=env,stdin=prompt,stdout=events,stderr=stderr,start_new_session=True)
                save(logs/'active.json',{'pid':process.pid,'started':began,'id':session['id']})
                try: rc=process.wait(timeout=7200)
                except subprocess.TimeoutExpired:
                    import signal
                    os.killpg(process.pid,signal.SIGTERM)
                    try: process.wait(timeout=10)
                    except subprocess.TimeoutExpired: os.killpg(process.pid,signal.SIGKILL)
                    rc=124
        finally:
            broker.terminate()
            try: broker.wait(timeout=15)
            except subprocess.TimeoutExpired: broker.kill(); broker.wait()
            for label in ('agentmvc.lane','agentmvc.lane.check'):
                ids=subprocess.check_output(['docker','container','ls','--all','--quiet','--filter',f'label={label}={session["id"]}'],text=True).split()
                if ids: subprocess.run(['docker','rm','-f',*ids],capture_output=True,timeout=30)
    fixture=load(work/'FIXTURE.json')
    run=dict(id=session['id'],stack=session['stack'],phase=session['phase'],condition=fixture['condition'],
             started=began,finished=stamp(),seconds=round(time.monotonic()-start,1),exit=rc,
             model=agent['model'],reasoning=agent['reasoning'],tool=subprocess.check_output(['codex','--version'],text=True).strip(),
             prompt_sha256=fixture['prompt_sha256'],fixture_sha256=fixture['fixture_sha256'],
             toolchain_image_id=fixture['toolchain_image_id'],browser_image_id=fixture['browser_image_id'],
             tokens=usage(logs/'events.jsonl'))
    save(logs/'run.json',run); (logs/'active.json').unlink(missing_ok=True)
    verify_workspace(session)
    print(json.dumps(run),flush=True)
    return rc


def product_files(work):
    for p in checked_files(work,SKIP):
        rel=p.relative_to(work)
        if str(rel) in INPUT_NAMES or p.name.startswith('.env'): continue
        if p.suffix in SOURCE_SUFFIXES or p.name in SOURCE_NAMES or rel.parts[0]=='bin':
            if p.stat().st_size>2_000_000: raise RuntimeError(f'Large source file: {rel}')
            yield p


def publish(path):
    import measure
    import one_shot_publish
    import scrub
    session=load(path); verify_workspace(session)
    work,logs,dest,source=(Path(session[k]) for k in ('work','logs','result','publish_source'))
    dest.mkdir(parents=True,exist_ok=True)
    token=(Path(session['control'])/'token').read_text().strip()
    cleaner=scrub.Scrubber(work,[re.escape(token)])
    files={}
    for p in product_files(work):
        rel=p.relative_to(work); data=p.read_bytes()
        if token.encode() in data or str(Path.home()).encode() in data or b'-----BEGIN PRIVATE KEY-----' in data:
            raise RuntimeError(f'Source requires scrub before publication: {rel}')
        target=source/rel; target.parent.mkdir(parents=True,exist_ok=True)
        if target.exists() and target.read_bytes()!=data: raise RuntimeError(f'Immutable source changed: {target}')
        if not target.exists(): shutil.copy2(p,target)
        files[str(rel)]=digest(p)
    save(dest/'source-snapshot.json',{'sha256':fingerprint(files),'path':str(source.relative_to(ROOT)),'files':files})
    for name in ('run.json','last.md'):
        if (logs/name).exists():
            text=cleaner.text((logs/name).read_text())
            if cleaner.leaks(text): raise RuntimeError('Publication contains private markers')
            (dest/('agent-report.md' if name=='last.md' else name)).write_text(text)
    scrub.scrub_file(logs/'events.jsonl',work,dest/'transcript',deny=[re.escape(token)],header={'title':session['id']})
    rules=measure.load_stack(session['stack'])
    rules['code']['skip_files'] = list(set(rules['code'].get('skip_files', [])) | {p.name for p in product_files(work) if p.name.endswith('_test.go') or (p.name.startswith('test_') or p.name=='tests.py') and p.suffix=='.py'})
    size=measure.measure(rules,work,work/'.scaffold')
    size.update(encoding='o200k_base',baseline='frozen product-free scaffold',
                limitations='Historical measurer: Go block comments and Python docstrings may count as owned code; tests/docs measured separately.')
    save(dest/'size.json',size)
    save(dest/'source-files.json',one_shot_publish.source_inventory(rules,work))
    extras={kind:{'tokens':0,'lines':0,'files':[]} for kind in ('tests','docs')}
    for p in product_files(work):
        rel=p.relative_to(work)
        kind='docs' if p.suffix=='.md' else 'tests' if ('test' in rel.parts or 'tests' in rel.parts or p.name.startswith('test_') or p.name=='tests.py' or p.name.endswith('_test.go')) else None
        if kind:
            lines=measure.read_lines(p.read_text()); extras[kind]['tokens']+=measure.tokens(lines); extras[kind]['lines']+=len(lines); extras[kind]['files'].append(str(rel))
    save(dest/'supplementary-size.json',extras)
    attempts={}
    for log in (Path(session['control'])/'requests.jsonl',logs/'broker/requests.jsonl'):
        if not log.exists(): continue
        for line in log.read_text().splitlines():
            row=json.loads(line); bucket=attempts.setdefault(row['action'],{'attempts':0,'failures':0})
            bucket['attempts']+=1; bucket['failures']+=int(row.get('exit',0)!=0)
    save(dest/'check-attempts.json',attempts)
    shutil.copy2(Path(session['control'])/'isolation.json',dest/'isolation.json')
    (dest/'frozen-prompt.md').write_bytes((work/'PROMPT.md').read_bytes())
    print(f'published {session["id"]}: {size["owned_tokens"]} owned tokens',flush=True)


def independently_check(path):
    session=load(path); dest=Path(session['result']); dest.mkdir(parents=True,exist_ok=True)
    checks={}
    for action in ['development']+(['production'] if session['number']>=3 else []):
        log=Path(session['control'])/f'independent-{action}.log'
        with log.open('w') as output:
            checks[action]=subprocess.run([sys.executable,str(ROOT/'tools/lane_check.py'),'--session',str(path),action],stdout=output,stderr=subprocess.STDOUT).returncode
        print(f'{session["id"]}: independent {action} exit {checks[action]}',flush=True)
    record={'passed':all(v==0 for v in checks.values()),'checks':checks,'checked_at':stamp(),
            'source_sha256':load(dest/'source-snapshot.json')['sha256']}
    save(dest/'verification.json',record)
    return record['passed']


def execute(path):
    session=load(path)
    done=Path(session['result'])/'verification.json'
    if done.exists():
        if not load(done)['passed']: raise RuntimeError('Previous measured attempt failed; preserve and diagnose before a repair session')
    else:
        if not (Path(session['logs'])/'run.json').exists(): launch(path)
        publish(path)
        if not independently_check(path): raise RuntimeError(f'{session["id"]}: independent gate failed')
    if session['phase'].startswith('3-') or session['phase'].startswith('4-'):
        action='benchmark' if session['phase'].startswith('3-') else 'security-scan'
        kind='perf' if action=='benchmark' else 'security'
        if (Path(session['work'])/'.checks'/kind/'latest/results.json').exists(): return
        log=Path(session['control'])/f'baseline-{action}.log'
        with log.open('w') as output:
            rc=subprocess.run([sys.executable,str(ROOT/'tools/lane_check.py'),'--session',str(path),action],stdout=output,stderr=subprocess.STDOUT).returncode
        if rc: raise RuntimeError(f'{action} baseline failed: {log}')


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('action',choices=['freeze','prepare','isolation','run','publish','check','pipeline','one-shot'])
    p.add_argument('target'); p.add_argument('phase',nargs='?'); p.add_argument('--through',type=int,default=8)
    a=p.parse_args()
    if a.action=='freeze': freeze(a.target)
    elif a.action=='prepare': print(prepare(a.target,a.phase))
    elif a.action=='isolation': isolation(Path(a.target).resolve())
    elif a.action=='run': return launch(Path(a.target).resolve())
    elif a.action=='publish': publish(Path(a.target).resolve())
    elif a.action=='check': return 0 if independently_check(Path(a.target).resolve()) else 1
    elif a.action=='one-shot': execute(prepare(a.target,'one-shot'))
    elif a.action=='pipeline':
        for n in range(1,a.through+1): execute(prepare(a.target,str(n)))
    return 0


if __name__=='__main__':
    raise SystemExit(main())
