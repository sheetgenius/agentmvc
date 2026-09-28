"""Exercise the frozen IHP development launcher with a real, product-free migration."""
import json
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

import ihp_candidate
import ihp_candidate_broker as bridge

ROOT = ihp_candidate.ROOT
WORK = ROOT / ".work/ihp-migration-preflight"
NAME = "agentmvc-ihp-migration-preflight"
PORT = 4114


def command(*args, timeout=600, check=True):
    result = subprocess.run(args, cwd=ROOT, capture_output=True, text=True, timeout=timeout)
    if check and result.returncode:
        raise RuntimeError(f"{args}: {result.returncode}\n{result.stdout[-2000:]}\n{result.stderr[-2000:]}")
    return result.stdout.strip()


def main():
    if WORK.exists():
        raise SystemExit(f"Existing preflight workspace: {WORK}")
    shutil.copytree(ihp_candidate.SCAFFOLD, WORK)
    sql = "CREATE TABLE migration_probe (id UUID PRIMARY KEY NOT NULL);\n"
    (WORK / "Application/Schema.sql").write_text(sql)
    (WORK / "Application/Migration/1790000000-probe.sql").write_text(sql)
    started = time.monotonic()
    outcome = {"probe": "product-free IHP migration and development server",
               "launcher": "tools/ihp_candidate_broker.py:DEV_SCRIPT",
               "schema": sql.strip(), "port": PORT}
    try:
        command(str(ROOT / "tools/one_shot_host/db.sh"), "start", str(PORT), timeout=120)
        command("docker", "run", "-d", "--name", NAME, "--network", "host",
                "--mount", f"type=volume,source={bridge.VOLUME},target=/nix",
                "--mount", f"type=bind,source={WORK},target=/work/app",
                "-w", "/work/app", "-e", "HOME=/tmp", "-e", f"PORT={PORT}",
                "-e", f"DATABASE_URL=postgres://agentmvc:agentmvc@host.docker.internal:{PORT+50000}/agentmvc",
                "-e", "SECRET_KEY_BASE=" + "0123456789abcdef" * 8,
                bridge.IMAGE, "sh", "-ec", bridge.DEV_SCRIPT, timeout=120)
        deadline = time.monotonic() + 600
        while time.monotonic() < deadline:
            if command("docker", "inspect", NAME, "--format", "{{.State.Running}}", check=False) != "true":
                raise RuntimeError(command("docker", "logs", NAME, check=False)[-4000:])
            try:
                urllib.request.urlopen(f"http://127.0.0.1:{PORT}/", timeout=2)
                break
            except urllib.error.HTTPError as error:
                if error.code == 404:
                    break
                raise
            except (urllib.error.URLError, TimeoutError):
                time.sleep(.5)
        else:
            raise RuntimeError("Product-free IHP server did not respond")
        relation = command("docker", "exec", f"agentmvc-one-shot-db-{PORT}", "psql", "-U", "agentmvc",
                           "-d", "agentmvc", "-tAc", "select to_regclass('public.migration_probe')")
        if relation != "migration_probe":
            raise RuntimeError(f"Migration not applied: {relation!r}")
        outcome.update(migration_applied=True, server_responded=True,
                       seconds=round(time.monotonic() - started, 1))
    finally:
        command("docker", "rm", "-f", NAME, check=False)
        command(str(ROOT / "tools/one_shot_host/db.sh"), "stop", str(PORT), timeout=60, check=False)
    dest = ROOT / "results/one-shot-ihp/migration-preflight.json"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(outcome, indent=2) + "\n")
    print(json.dumps(outcome, indent=2), flush=True)


if __name__ == "__main__":
    main()
