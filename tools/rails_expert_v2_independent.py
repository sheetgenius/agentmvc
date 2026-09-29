"""Independently repeat Rails expert development or fresh-production gates."""

import json
import os
import subprocess
import sys
import time
import urllib.request
from datetime import datetime, timezone

import one_shot
import rails_expert_v2 as setup
import rails_expert_v2_broker as bridge
import scrub

ROOT = one_shot.ROOT
HOST = ROOT / "tools/one_shot_host"
PORT = setup.PORT


def command(args, *, env=None, timeout=3600):
    proc = subprocess.run(args, cwd=ROOT, env=env, capture_output=True,
                          text=True, timeout=timeout)
    return proc.returncode, proc.stdout + proc.stderr


def ready(name, output):
    deadline = time.monotonic() + 600
    while time.monotonic() < deadline:
        if command(["docker", "inspect", name, "--format", "{{.State.Running}}"],
                   timeout=30)[1].strip() != "true":
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
    name = bridge.DEV
    command(["docker", "rm", "-f", name], timeout=30)
    # A stopped Puma container can leave its generated PID file on the bind mount.
    (work / "tmp/pids/server.pid").unlink(missing_ok=True)
    host_env = {**os.environ, "ONE_SHOT_WORKDIR": str(work)}
    output.append(command([str(HOST / "db.sh"), "stop", str(PORT)], env=host_env,
                          timeout=60)[1])
    code, result = command([str(HOST / "db.sh"), "start", str(PORT)],
                           env=host_env, timeout=120)
    output.append(result)
    if code:
        return code
    try:
        code, result = command([*bridge.container(work), "bundle", "exec", "rails",
                                "db:prepare"], timeout=600)
        output.append(result)
        if code:
            return code
        code, result = command([*bridge.container(work, detached=True, name=name),
                                "bundle", "exec", "rails", "server", "-b", "0.0.0.0"],
                               timeout=120)
        output.append(result)
        if code or not ready(name, output):
            return 1
        code, result = command([str(HOST / "check-all.sh"), str(PORT)],
                               env=host_env, timeout=1200)
        output.append(result)
        if code:
            return code
        for check in (("bundle", "exec", "rails", "zeitwerk:check"),
                      ("bundle", "exec", "rubocop")):
            code, result = command([*bridge.container(work), *check], timeout=600)
            output.append(result)
            if code:
                return code
        test_container = bridge.container(work, test=True)
        for check in (("bundle", "exec", "rails", "db:prepare"),
                      ("bundle", "exec", "rails", "test")):
            code, result = command([*test_container, *check], timeout=900)
            output.append(result)
            if code:
                return code
        return 0
    finally:
        command(["docker", "rm", "-f", name], timeout=30)
        output.append(command([str(HOST / "db.sh"), "stop", str(PORT)],
                              env=host_env, timeout=60)[1])


def production(work, output):
    command(["docker", "rm", "-f", bridge.DEV], timeout=30)
    code, result = command([str(HOST / "check-production.sh"), str(PORT)],
                           env={**os.environ, "ONE_SHOT_WORKDIR": str(work)},
                           timeout=3600)
    output.append(result)
    return code


def main():
    if len(sys.argv) != 2 or sys.argv[1] not in ("development", "production"):
        raise SystemExit(__doc__)
    gate, work = sys.argv[1], setup.WORK
    if setup.snapshot() != json.loads(setup.MANIFEST.read_text()):
        raise SystemExit("Frozen Rails fixture source changed")
    setup.verify_workspace(work)
    started, tick, output = datetime.now(timezone.utc).isoformat(), time.monotonic(), []
    try:
        code = development(work, output) if gate == "development" else production(work, output)
        setup.verify_workspace(work)
    except Exception as error:
        code = 1
        output.append(f"Independent gate error: {error}\n")
    dest = ROOT / "results/one-shot-v2-rails-expert/pilot-1"
    raw = ROOT / ".work/one-shot-v2-rails-expert-independent"
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
    token_file = setup.CONTROL / "token"
    cleaner = scrub.Scrubber(work, [token_file.read_text().strip()] if token_file.exists() else [])
    cleaned = cleaner.text(full)
    if cleaner.leaks(cleaned):
        raise SystemExit("Independent log contains private paths")
    (dest / f"{gate}.log").write_text(cleaned)
    record = {"stack": "rails", "condition": "v2-expert-diagnostic", "gate": gate,
              "port": PORT, "started": started,
              "finished": datetime.now(timezone.utc).isoformat(),
              "seconds": round(time.monotonic() - tick, 1), "exit": code,
              "fixture_sha256": json.loads((work / "FIXTURE.json").read_text())["fixture_sha256"]}
    (dest / f"{gate}.json").write_text(json.dumps(record, indent=2) + "\n")
    print(json.dumps(record, indent=2), flush=True)
    return code


if __name__ == "__main__":
    raise SystemExit(main())
