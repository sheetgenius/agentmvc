"""Reviewer-only TCP readiness correction; measured fixtures stay unchanged.

PostgreSQL's initialization server accepts Unix-socket connections before its
final TCP server starts. Require TCP for reviewer readiness checks. Preserve
each prior verification and identify this adapter on the new attempt.
Usage: lane_review.py --session PATH development|production|benchmark|security-scan
"""
import json
import shutil
import subprocess
import sys
from pathlib import Path

import lane_broker
import lane_check
import lane_run

ORIGINAL_COMMAND = lane_broker.command


def tcp_command(args, **kwargs):
    if "pg_isready" in args and "-h" not in args and "--host" not in args:
        args = [*args, "-h", "127.0.0.1"]
    return ORIGINAL_COMMAND(args, **kwargs)


def install():
    lane_broker.command = tcp_command


def identity():
    return {
        "path": "tools/lane_review.py",
        "sha256": lane_run.digest(Path(__file__)),
        "reason": "Wait for PostgreSQL TCP server, not its temporary Unix-socket initialization server",
        "coding_inputs_changed": False,
        "source_changed": False,
    }


def independently_check(path):
    session = lane_run.load(path)
    dest = Path(session["result"])
    dest.mkdir(parents=True, exist_ok=True)
    previous = dest / "verification.json"
    history = dest / "verification-attempts"
    if previous.exists():
        history.mkdir(exist_ok=True)
        name = f"{len(list(history.glob('*.json'))) + 1:02d}.json"
        shutil.copy2(previous, history / name)
    checks = {}
    attempt = lane_run.stamp().replace(":", "-")
    for action in ["development"] + (["production"] if session["number"] >= 3 else []):
        log = Path(session["control"]) / f"independent-{action}-{attempt}.log"
        with log.open("w") as output:
            checks[action] = subprocess.run(
                [sys.executable, str(Path(__file__).resolve()), "--session", str(path), action],
                stdout=output, stderr=subprocess.STDOUT,
            ).returncode
        print(f'{session["id"]}: independent {action} exit {checks[action]}', flush=True)
    record = {
        "passed": all(code == 0 for code in checks.values()),
        "checks": checks,
        "checked_at": lane_run.stamp(),
        "source_sha256": lane_run.load(dest / "source-snapshot.json")["sha256"],
        "reviewer_adapter": identity(),
    }
    if history.exists():
        record["previous_attempts"] = sorted(str(p.relative_to(dest)) for p in history.glob("*.json"))
    lane_run.save(previous, record)
    return record["passed"]


if __name__ == "__main__":
    install()
    print(json.dumps({"reviewer_adapter": identity()}), flush=True)
    raise SystemExit(lane_check.main())
