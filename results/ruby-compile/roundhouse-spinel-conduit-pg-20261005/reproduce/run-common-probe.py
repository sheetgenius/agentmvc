"""Run the common HTTP probe against one unchanged production image.

Usage: python3 reproduce/run-common-probe.py STACK IMAGE OUTPUT_JSON

The coordinator owns Docker. The app receives the same three environment
variables as the frozen production gate and uses a fresh disposable database.
"""

import argparse
import json
import os
import subprocess
import sys
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
PORT = int(os.environ.get("PROBE_PORT", "4440"))
LIMITS = ("--cpus=2", "--memory=1g")


def command(args, *, check=True, timeout=300):
    proc = subprocess.run(args, cwd=ROOT, capture_output=True, text=True,
                          timeout=timeout)
    if check and proc.returncode:
        raise RuntimeError(f"{args[:3]} failed ({proc.returncode}): {proc.stderr[-2000:]}")
    return proc


def ready(name):
    deadline = time.monotonic() + 180
    while time.monotonic() < deadline:
        if command(["docker", "inspect", "--format", "{{.State.Running}}", name],
                   check=False).stdout.strip() != "true":
            raise RuntimeError(f"App exited: {command(['docker', 'logs', name], check=False).stderr[-2000:]}")
        try:
            request = urllib.request.Request(f"http://127.0.0.1:{PORT}/api/tags",
                                             headers={"Accept": "application/json"})
            with urllib.request.urlopen(request, timeout=2) as response:
                if response.status == 200:
                    return
        except Exception:
            time.sleep(.2)
    raise RuntimeError("App did not answer /api/tags within 180 seconds")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stack", choices=("rails", "typescript", "phoenix"))
    parser.add_argument("image")
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    if args.output.exists():
        raise SystemExit(f"Preserving existing probe: {args.output}")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    label = "conduit-v7-common-http-" + args.stack
    net, db, app = label + "-net", label + "-db", label + "-app"
    image_id = command(["docker", "image", "inspect", "--format", "{{.Id}}",
                        args.image]).stdout.strip()
    started = datetime.now(timezone.utc).isoformat()
    record = {"stack": args.stack, "image": args.image, "image_sha256": image_id,
              "started": started, "database": "postgres:17-alpine",
              "limits": list(LIMITS), "app_environment_keys":
              ["DATABASE_URL", "SECRET_KEY_BASE", "PORT"]}
    try:
        command(["docker", "network", "create", net])
        command(["docker", "run", "-d", "--name", db, "--network", net,
                 "--network-alias", "db", *LIMITS, "-e", "POSTGRES_PASSWORD=postgres",
                 "-e", "POSTGRES_DB=conduit", "postgres:17-alpine"])
        for _ in range(120):
            if command(["docker", "exec", db, "pg_isready", "-h", "127.0.0.1",
                        "-U", "postgres", "-d", "conduit"], check=False).returncode == 0:
                break
            time.sleep(.5)
        else:
            raise RuntimeError("PostgreSQL did not become ready")
        command(["docker", "run", "-d", "--name", app, "--network", net,
                 *LIMITS, "-p", f"127.0.0.1:{PORT}:8080",
                 "-e", "DATABASE_URL=postgres://postgres:postgres@db:5432/conduit",
                 "-e", "SECRET_KEY_BASE=" + "0123456789abcdef" * 8,
                 "-e", "PORT=8080", args.image])
        ready(app)
        result = command([sys.executable, str(ROOT / "tools/reviewer_common_http_probe.py"),
                          "--base-url", f"http://127.0.0.1:{PORT}"], check=False,
                         timeout=300)
        payload = json.loads(result.stdout)
        record.update(exit=result.returncode, probe=payload)
    except Exception as error:
        record.update(exit=2, error=f"{type(error).__name__}: {error}")
    finally:
        logs = command(["docker", "logs", app], check=False)
        record["app_log_tail"] = (logs.stdout + logs.stderr)[-12000:]
        command(["docker", "rm", "-f", "-v", app, db], check=False)
        command(["docker", "network", "rm", net], check=False)
        record["finished"] = datetime.now(timezone.utc).isoformat()
        args.output.write_text(json.dumps(record, indent=2) + "\n")
    print(json.dumps({key: record.get(key) for key in ("stack", "image_sha256", "exit", "error")},
                     indent=2))
    return record["exit"]


if __name__ == "__main__":
    raise SystemExit(main())
