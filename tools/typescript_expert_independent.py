"""Repeat the guided TypeScript run's development or fresh-production gate."""
import json
import os
import subprocess
import sys
import time
import urllib.request
from datetime import datetime, timezone

import one_shot
import scrub
import typescript_expert
import typescript_expert_broker as bridge

ROOT = one_shot.ROOT
HOST = ROOT / "tools/one_shot_host"
PORT = 4107


def command(args, *, env=None, timeout=3600):
    proc = subprocess.run(args, cwd=ROOT, env=env, capture_output=True, text=True, timeout=timeout)
    return proc.returncode, proc.stdout + proc.stderr


def ready(name, output):
    deadline = time.monotonic() + 600
    while time.monotonic() < deadline:
        if command(["docker", "inspect", name, "--format", "{{.State.Running}}"], timeout=30)[1].strip() != "true":
            output.append(command(["docker", "logs", name], timeout=30)[1])
            return False
        try:
            request = urllib.request.Request(f"http://127.0.0.1:{PORT}/api/tags",
                                             headers={"Accept": "application/json"})
            if urllib.request.urlopen(request, timeout=2).status == 200:
                return True
        except Exception:
            time.sleep(.2)
    output.append(command(["docker", "logs", name], timeout=30)[1])
    return False


def development(work, output):
    name = bridge.DEV_NAME
    for candidate in (name, bridge.WORKER_NAME):
        command(["docker", "rm", "-f", candidate], timeout=30)
    host_env = {**os.environ, "ONE_SHOT_WORKDIR": str(work)}
    code, result = command([str(HOST / "db.sh"), "start", str(PORT)], env=host_env, timeout=120)
    output.append(result)
    if code:
        return code
    try:
        code, result = bridge.command_container(work, ["node", "ace", "migration:run", "--force"], 120)
        output.append(result)
        if code:
            return code
        code, result = bridge.start_container(work, bridge.WORKER_NAME,
                                              ["node", "ace", "queue:work"])
        output.append(result)
        if code:
            return code
        code, result = bridge.start_container(work, name,
                                              ["npm", "run", "dev", "--", "--poll"])
        output.append(result)
        if code or not ready(name, output):
            return 1
        if command(["docker", "inspect", bridge.WORKER_NAME,
                    "--format", "{{.State.Running}}"], timeout=30)[1].strip() != "true":
            output.append(command(["docker", "logs", bridge.WORKER_NAME], timeout=30)[1])
            return 1
        code, result = bridge.run_check([str(HOST / "check-all.sh"), str(PORT)],
                                        env=host_env, timeout=1200, work=work)
        output.append(result)
        return code
    finally:
        for candidate in (name, bridge.WORKER_NAME):
            command(["docker", "rm", "-f", candidate], timeout=30)
        output.append(command([str(HOST / "db.sh"), "stop", str(PORT)], env=host_env, timeout=60)[1])


def production(work, output):
    for candidate in (bridge.DEV_NAME, bridge.WORKER_NAME):
        command(["docker", "rm", "-f", candidate], timeout=30)
    code, result = bridge.run_check([str(HOST / "check-production.sh"), str(PORT)],
                                    env={**os.environ, "ONE_SHOT_WORKDIR": str(work)},
                                    timeout=3600, work=work, production=True)
    output.append(result)
    return code


def main():
    if len(sys.argv) != 2 or sys.argv[1] not in ("development", "production"):
        raise SystemExit(__doc__)
    gate, work = sys.argv[1], typescript_expert.WORK
    if typescript_expert.snapshot() != json.loads(typescript_expert.MANIFEST.read_text()):
        raise SystemExit("Frozen fixture source changed")
    typescript_expert.verify_work(work)
    started, tick, output = datetime.now(timezone.utc).isoformat(), time.monotonic(), []
    try:
        code = development(work, output) if gate == "development" else production(work, output)
        typescript_expert.verify_work(work)
    except Exception as error:
        code = 1
        output.append(f"Independent gate error: {error}\n")
    dest = ROOT / "results/one-shot-v2-typescript-expert/expert-1"
    raw = ROOT / ".work/one-shot-v2-typescript-expert-independent"
    dest.mkdir(parents=True, exist_ok=True)
    raw.mkdir(parents=True, exist_ok=True)
    if (dest / f"{gate}.json").exists():
        attempt = 1
        while (dest / f"{gate}-attempt{attempt}.json").exists():
            attempt += 1
        for folder in (dest, raw):
            for suffix in (("json", "log") if folder == dest else ("log",)):
                old = folder / f"{gate}.{suffix}"
                if old.exists():
                    old.rename(folder / f"{gate}-attempt{attempt}.{suffix}")
    full = "\n".join(output)
    (raw / f"{gate}.log").write_text(full)
    token_file = typescript_expert.CONTROL / "token"
    cleaner = scrub.Scrubber(work, [token_file.read_text().strip()] if token_file.exists() else [])
    cleaned = cleaner.text(full)
    if cleaner.leaks(cleaned):
        raise SystemExit("Independent log contains private paths")
    (dest / f"{gate}.log").write_text(cleaned)
    record = {"stack": "typescript", "condition": "v2-expert-guided", "gate": gate,
              "port": PORT, "started": started,
              "finished": datetime.now(timezone.utc).isoformat(),
              "seconds": round(time.monotonic() - tick, 1), "exit": code,
              "fixture_sha256": json.loads((work / "FIXTURE.json").read_text())["fixture_sha256"]}
    (dest / f"{gate}.json").write_text(json.dumps(record, indent=2) + "\n")
    print(json.dumps(record, indent=2), flush=True)
    raise SystemExit(code)


if __name__ == "__main__":
    main()
