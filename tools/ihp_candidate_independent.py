"""Host-owned development and production gates for a completed IHP run.

Usage: python3 tools/ihp_candidate_independent.py 1|2|3 development|production
"""
import json
import os
import subprocess
import sys
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

import ihp_candidate
import ihp_candidate_broker as bridge
import one_shot
import scrub

ROOT = one_shot.ROOT
HOST = ROOT / "tools/one_shot_host"


def command(args, *, env=None, timeout=3600):
    proc = subprocess.run(args, cwd=ROOT, env=env, capture_output=True, text=True, timeout=timeout)
    return proc.returncode, proc.stdout + proc.stderr


def ready(port, name, output):
    deadline = time.monotonic() + 600
    while time.monotonic() < deadline:
        if command(["docker", "inspect", name, "--format", "{{.State.Running}}"], timeout=30)[1].strip() != "true":
            output.append(command(["docker", "logs", name], timeout=30)[1])
            return False
        try:
            request = urllib.request.Request(f"http://127.0.0.1:{port}/api/tags",
                                             headers={"Accept": "application/json"})
            if urllib.request.urlopen(request, timeout=2).status == 200:
                return True
        except Exception:
            time.sleep(.2)
    output.append(command(["docker", "logs", name], timeout=30)[1])
    return False


def development(run_number, work, output):
    port = 4204
    name = f"agentmvc-one-shot-ihp-{run_number}-independent-dev"
    host_env = {**os.environ, "ONE_SHOT_WORKDIR": str(work)}
    code, text = command([str(HOST / "db.sh"), "start", str(port)], env=host_env, timeout=120)
    output.append(text)
    if code:
        return code
    args = ["docker", "run", "-d", "--name", name, "--network", "host", *bridge.workspace_mounts(work),
            "-w", "/work/app", "-e", "HOME=/tmp", "-e", f"PORT={port}",
            "-e", f"DATABASE_URL=postgres://agentmvc:agentmvc@host.docker.internal:{port + 50000}/agentmvc",
            "-e", "SECRET_KEY_BASE=" + "0123456789abcdef" * 8,
            bridge.IMAGE, "sh", "-ec", bridge.DEV_SCRIPT]
    try:
        code, text = command(args, timeout=120)
        output.append(text)
        if code:
            return code
        if not ready(port, name, output):
            return 1
        code, text = command([str(HOST / "check-all.sh"), str(port)], env=host_env, timeout=1200)
        output.append(text)
        return code
    finally:
        command(["docker", "container", "rm", "-f", name], timeout=30)
        output.append(command([str(HOST / "db.sh"), "stop", str(port)], env=host_env, timeout=60)[1])


def production(run_number, work, output):
    command(["docker", "container", "rm", "-f", f"agentmvc-one-shot-ihp-{run_number}-dev"], timeout=30)
    code, text = command([str(ROOT / "tools/ihp_candidate_host/check-production.sh"), "4104"],
                         env={**os.environ, "ONE_SHOT_WORKDIR": str(work)}, timeout=3600)
    output.append(text)
    return code


def main():
    if len(sys.argv) != 3 or sys.argv[1] not in ("1", "2", "3") or sys.argv[2] not in ("development", "production"):
        raise SystemExit(__doc__)
    run_number, gate = sys.argv[1:]
    manifest = json.loads(ihp_candidate.MANIFEST.read_text())
    if ihp_candidate.snapshot() != manifest:
        raise SystemExit("Frozen candidate source changed")
    work = ihp_candidate.workspace(run_number)
    one_shot.verify(work)
    started, tick = datetime.now(timezone.utc).isoformat(), time.monotonic()
    output = []
    try:
        code = development(run_number, work, output) if gate == "development" else \
               production(run_number, work, output)
        one_shot.verify(work)
    except Exception as error:
        code = 1
        output.append(f"Independent gate error: {error}\n")
    dest = ROOT / "results" / "one-shot-ihp" / f"run-{run_number}"
    raw = ROOT / ".work" / f"one-shot-ihp-{run_number}-independent"
    dest.mkdir(parents=True, exist_ok=True)
    raw.mkdir(parents=True, exist_ok=True)
    if (dest / f"{gate}.json").exists():
        attempt = 1
        while (dest / f"{gate}-attempt{attempt}.json").exists():
            attempt += 1
        for folder in (dest, raw):
            for suffix in ("json", "log") if folder == dest else ("log",):
                old = folder / f"{gate}.{suffix}"
                if old.exists():
                    old.rename(folder / f"{gate}-attempt{attempt}.{suffix}")
    full = "\n".join(output)
    (raw / f"{gate}.log").write_text(full)
    token_file = ROOT / ".work" / f"one-shot-ihp-{run_number}-control" / "token"
    cleaner = scrub.Scrubber(work, [token_file.read_text().strip()] if token_file.exists() else [])
    cleaned = cleaner.text(full)
    if cleaner.leaks(cleaned):
        raise SystemExit("Independent log contains private paths")
    (dest / f"{gate}.log").write_text(cleaned)
    record = {"stack": "ihp", "run": int(run_number), "gate": gate,
              "port": 4204 if gate == "development" else 4104,
              "started": started, "finished": datetime.now(timezone.utc).isoformat(),
              "seconds": round(time.monotonic() - tick, 1), "exit": code,
              "fixture_sha256": json.loads((work / "FIXTURE.json").read_text())["fixture_sha256"]}
    (dest / f"{gate}.json").write_text(json.dumps(record, indent=2) + "\n")
    print(json.dumps(record, indent=2), flush=True)
    raise SystemExit(code)


if __name__ == "__main__":
    main()
