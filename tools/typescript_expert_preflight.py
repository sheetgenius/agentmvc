"""Product-free preflight for the versioned TypeScript expert condition.

Usage: python3 tools/typescript_expert_preflight.py broker|full
`broker` is a seconds-long isolation/timeout probe. `full` adds a watched
server, actual queue worker, static checks, and a fresh compiled image.
"""
import json
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import urllib.error
import urllib.request
from pathlib import Path

import one_shot
import typescript_expert
import typescript_expert_broker as bridge

ROOT = one_shot.ROOT
RESULTS = ROOT / "results/one-shot-v2-typescript-expert"
IMAGE = "agentmvc-typescript-v2-expert-scaffold-preflight"
APP = "agentmvc-typescript-v2-expert-preflight-app"


def call(args, timeout=120):
    proc = subprocess.run(args, cwd=ROOT, capture_output=True, text=True, timeout=timeout)
    if proc.returncode:
        raise RuntimeError(f"{args[0]} failed ({proc.returncode}): {(proc.stdout + proc.stderr)[-3000:]}")
    return proc.stdout + proc.stderr


def absent(name):
    return subprocess.run(["docker", "container", "inspect", name],
                          capture_output=True, timeout=20).returncode != 0


def url(path, timeout=1):
    with urllib.request.urlopen(f"http://127.0.0.1:{bridge.PORT}{path}", timeout=timeout) as response:
        return response.status, response.read()


def eventually(predicate, seconds=30):
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        try:
            if predicate():
                return
        except Exception:
            pass
        time.sleep(.2)
    raise RuntimeError("Preflight condition did not become ready")


def prepare_work(work):
    shutil.copytree(typescript_expert.SCAFFOLD, work, dirs_exist_ok=True,
                    ignore=shutil.ignore_patterns(*typescript_expert.GENERATED))
    for part in ("realworld_spec", "security", "harness", ".scaffold"):
        (work / part).mkdir(exist_ok=True)
    for part in ("PROMPT.md", "ENVIRONMENT.md", "MEASUREMENT.md", "EXPERIMENT.md", "FIXTURE.json"):
        (work / part).write_text("preflight-frozen-marker\n")


def broker_http_auth(work):
    original = typescript_expert.WORK
    typescript_expert.WORK = work
    with tempfile.TemporaryDirectory(prefix="typescript-expert-broker-log-") as temp:
        server = bridge.Server(("127.0.0.1", 0), "preflight-token", Path(temp))
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            endpoint = f"http://127.0.0.1:{server.server_port}/run"
            data = json.dumps({"action": "not-an-action", "port": bridge.PORT, "argv": []}).encode()
            for authorization, expected in ((None, 403), ("Bearer preflight-token", 409)):
                headers = {"Content-Type": "application/json"}
                if authorization:
                    headers["Authorization"] = authorization
                request = urllib.request.Request(endpoint, data, headers)
                try:
                    urllib.request.urlopen(request, timeout=3)
                    raise RuntimeError("Broker accepted an invalid request")
                except urllib.error.HTTPError as error:
                    if error.code != expected:
                        raise RuntimeError(f"Broker returned {error.code}, expected {expected}")
            return True
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=3)
            typescript_expert.WORK = original


def broker_checks(work, checks):
    checks["broker_auth_and_rejection"] = broker_http_auth(work)
    if any(not absent(name) for name in (bridge.DEV_NAME, bridge.WORKER_NAME)):
        raise RuntimeError("An expert development or worker container is already active")
    code, output = bridge.command_container(work, ["sleep", "30"], timeout=2)
    if code != 124 or "removed" not in output:
        raise RuntimeError(f"Injected command timeout failed: {code} {output}")
    cmd_name = output.split("removed ", 1)[1].split(".", 1)[0]
    if not absent(cmd_name):
        raise RuntimeError(f"Timed-out container remains: {cmd_name}")
    checks["timed_command_removed"] = True
    orphan = "agentmvc-typescript-v2-expert-preflight-check-orphan"
    if not absent(orphan):
        raise RuntimeError(f"Preflight orphan name is already in use: {orphan}")
    program = ('import subprocess,time,sys; '
               'subprocess.run(["docker","run","-d","--name",sys.argv[1],'
               '"--mount",f"type=bind,source={sys.argv[2]},target=/probe,readonly",'
               'sys.argv[3],"sleep","30"],check=True); time.sleep(30)')
    code, output = bridge.run_check(
        ["python3", "-c", program, orphan, str(work), typescript_expert.IMAGE],
        env=None, timeout=2, work=work)
    if code != 124 or "cleanup failures []" not in output or not absent(orphan):
        raise RuntimeError(f"Timed check cleanup failed: {code} {output}")
    checks["timed_check_descendants_removed"] = True
    original = (work / "ENVIRONMENT.md").read_bytes()
    code, output = bridge.command_container(
        work, ["sh", "-c", "printf changed >> /work/app/ENVIRONMENT.md"], timeout=10)
    if code == 0 or (work / "ENVIRONMENT.md").read_bytes() != original:
        raise RuntimeError(f"Frozen input was writable inside tool container: {output}")
    code, output = bridge.command_container(
        work, ["sh", "-c", "printf changed > /work/app/harness/frozen-probe"], timeout=10)
    if code == 0 or (work / "harness/frozen-probe").exists():
        raise RuntimeError(f"Harness mount was writable inside tool container: {output}")
    checks["readonly_container_mounts"] = True
    for label, name in (("development", bridge.DEV_NAME), ("worker", bridge.WORKER_NAME)):
        try:
            code, output = bridge.start_container(work, name, ["sleep", "30"])
            if code:
                raise RuntimeError(f"Detached {label} start failed: {output}")
            if call(["docker", "inspect", name, "--format", "{{.State.Running}}"], timeout=20).strip() != "true":
                raise RuntimeError(f"Detached {label} is not running")
            call(["docker", "logs", name], timeout=20)
            checks[f"{label}_lifecycle"] = True
        finally:
            call(["docker", "rm", "-f", name], timeout=20) if not absent(name) else None
            if not absent(name):
                raise RuntimeError(f"Detached {label} container remains")


def full_checks(work, checks):
    call([*typescript_expert.container(work, "npm", "ci", "--no-audit", "--no-fund")], timeout=300)
    checks["npm_ci"] = True
    for label, command in (("typecheck", ["npm", "run", "typecheck"]),
                           ("lint", ["npm", "run", "lint"]),
                           ("tests", ["npm", "test"]),
                           ("compiled_build", ["npm", "run", "build"])):
        code, output = bridge.command_container(work, command, timeout=180 if label != "compiled_build" else 600)
        if code:
            raise RuntimeError(f"{label} failed: {output[-3000:]}")
        checks[label] = True
    db_started = False
    try:
        call([str(bridge.HOST / "db.sh"), "start", str(bridge.PORT)], timeout=90)
        db_started = True
        code, output = bridge.command_container(work, ["node", "ace", "migration:run", "--force"], timeout=120)
        if code:
            raise RuntimeError(f"Migration failed: {output[-3000:]}")
        checks["fresh_development_migration"] = True
        for name, command in ((bridge.WORKER_NAME, ["node", "ace", "queue:work"]),
                              (bridge.DEV_NAME, ["npm", "run", "dev", "--", "--poll"])):
            code, output = bridge.start_container(work, name, command)
            if code:
                raise RuntimeError(f"{name} failed: {output[-3000:]}")
        eventually(lambda: url("/health")[0] == 200, seconds=40)
        if call(["docker", "inspect", bridge.WORKER_NAME, "--format", "{{.State.Running}}"], timeout=20).strip() != "true":
            raise RuntimeError("Development queue worker exited")
        checks["development_health"] = True
        checks["development_worker"] = True
        route = work / "start/routes.ts"
        original = route.read_bytes()
        try:
            route.write_bytes(original + b"\nrouter.get('/preflight-watch', () => ({ marker: 'expert-watch' }))\n")
            eventually(lambda: json.loads(url("/preflight-watch")[1]) == {"marker": "expert-watch"},
                       seconds=40)
            checks["watched_edit"] = True
        finally:
            route.write_bytes(original)
    finally:
        for name in (bridge.DEV_NAME, bridge.WORKER_NAME):
            subprocess.run(["docker", "rm", "-f", name], capture_output=True, timeout=30)
        if db_started:
            call([str(bridge.HOST / "db.sh"), "stop", str(bridge.PORT)], timeout=60)
    call(["docker", "build", "-q", "-t", IMAGE, str(work)], timeout=900)
    checks["production_image_build"] = True
    db_started = False
    try:
        call([str(bridge.HOST / "db.sh"), "start", str(bridge.PORT)], timeout=90)
        db_started = True
        call(["docker", "run", "-d", "--name", APP, "--network", "host",
              "-e", f"DATABASE_URL=postgres://agentmvc:agentmvc@127.0.0.1:{bridge.PORT + 50000}/agentmvc",
              "-e", "SECRET_KEY_BASE=typescript-expert-preflight-secret-0123456789abcdef",
              "-e", f"PORT={bridge.PORT}", IMAGE], timeout=60)
        eventually(lambda: url("/health")[0] == 200, seconds=50)
        checks["fresh_compiled_production_health"] = True
        top = call(["docker", "top", APP], timeout=20)
        if "queue:work" not in top:
            raise RuntimeError("Compiled production worker did not start")
        checks["compiled_worker"] = True
    finally:
        subprocess.run(["docker", "rm", "-f", APP], capture_output=True, timeout=30)
        if db_started:
            call([str(bridge.HOST / "db.sh"), "stop", str(bridge.PORT)], timeout=60)
        subprocess.run(["docker", "image", "rm", IMAGE], capture_output=True, timeout=30)


def main():
    if len(sys.argv) != 2 or sys.argv[1] not in ("broker", "full"):
        raise SystemExit(__doc__)
    mode = sys.argv[1]
    source = typescript_expert.snapshot()
    if typescript_expert.MANIFEST.exists() and json.loads(typescript_expert.MANIFEST.read_text()) != source:
        raise SystemExit("Frozen expert fixture differs from current source")
    started = time.monotonic()
    checks = {}
    (ROOT / ".work").mkdir(exist_ok=True)
    error = None
    try:
        with tempfile.TemporaryDirectory(prefix="typescript-expert-preflight-", dir=ROOT / ".work") as temp:
            work = Path(temp)
            prepare_work(work)
            broker_checks(work, checks)
            if mode == "full":
                full_checks(work, checks)
    except Exception as exc:
        error = str(exc)
    result = {"passed": error is None, "mode": mode,
              "fixture_sha256": source["sha256"],
              "prompt_sha256": source["files"]["one-shot-v2-expert/PROMPT.md"],
              "toolchain_image_id": typescript_expert.image_id(),
              "browser_image_id": one_shot.image_id(),
              "seconds": round(time.monotonic() - started, 1), "checks": checks}
    if error is not None:
        result["error"] = error
    RESULTS.mkdir(parents=True, exist_ok=True)
    path = RESULTS / ("preflight.json" if mode == "full" else "broker-preflight.json")
    if path.exists():
        attempt = 1
        while path.with_name(f"{path.stem}-attempt{attempt}.json").exists():
            attempt += 1
        path.rename(path.with_name(f"{path.stem}-attempt{attempt}.json"))
    path.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
    if error is not None:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
