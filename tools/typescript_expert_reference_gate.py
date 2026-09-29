"""Rerun the final TypeScript reference development gate with stable DB readiness.

The frozen host db.sh can observe PostgreSQL's temporary init server as ready,
then fail its immediate second pg_isready during the server restart. Recover
only that setup failure after the labelled fresh DB accepts TCP connections;
the migration, server, worker, and acceptance checks remain unchanged.
"""

from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json
import time

import scrub
import typescript_expert_broker as broker
import typescript_expert_independent as gate

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / ".work/one-shot-v2-typescript-expert-reference-1"
WORK = ROOT / ".work/one-shot-v2-typescript-expert-reference-1-run"
RESULT = ROOT / "results/one-shot-v2-typescript-expert/expert-1/reference-1"
EXPECTED = "71904d3a33f9e8dec09a3924ee0f29659b2bf05fa45a066190833eb7239a9c1e"
DB = "agentmvc-one-shot-db-4123"


def source_hash(root):
    digest = hashlib.sha256()
    for path in sorted(p for p in root.rglob("*") if p.is_file()):
        digest.update(path.relative_to(root).as_posix().encode())
        digest.update(b"\0")
        digest.update(hashlib.sha256(path.read_bytes()).digest())
    return digest.hexdigest()


def verify_source():
    assert source_hash(SOURCE) == EXPECTED
    assert all(path.read_bytes() == (WORK / path.relative_to(SOURCE)).read_bytes()
               for path in SOURCE.rglob("*") if path.is_file())


def main():
    verify_source()
    gate.PORT = broker.PORT = 4123
    broker.DEV_NAME = "agentmvc-ts-reference-1-dev"
    broker.WORKER_NAME = "agentmvc-ts-reference-1-worker"
    original = gate.command
    recovered = False

    def stable_db_command(args, **kwargs):
        nonlocal recovered
        code, output = original(args, **kwargs)
        if args[:2] != [str(gate.HOST / "db.sh"), "start"]:
            return code, output
        label_code, label = original(
            ["docker", "inspect", DB, "--format", '{{index .Config.Labels "agentmvc.one-shot"}}'],
            timeout=10,
        )
        if label_code or label.strip() != "true":
            return code, output
        deadline = time.monotonic() + 60
        while time.monotonic() < deadline:
            ready_code, _ = original(
                ["docker", "exec", DB, "pg_isready", "-h", "127.0.0.1", "-U", "agentmvc", "-d", "agentmvc"],
                timeout=10,
            )
            if ready_code == 0:
                recovered = code != 0
                return 0, output + "DB setup confirmed final TCP server ready.\n"
            time.sleep(.2)
        return code, output + "DB did not become TCP-ready after setup failure.\n"

    gate.command = stable_db_command
    original(["docker", "rm", "-f", DB], timeout=10)
    output = []
    started = datetime.now(timezone.utc).isoformat()
    tick = time.monotonic()
    code = gate.development(WORK, output)
    verify_source()
    cleaner = scrub.Scrubber(WORK)
    clean = cleaner.text("\n".join(output))
    assert not cleaner.leaks(clean)
    RESULT.mkdir(parents=True, exist_ok=True)
    (RESULT / "development.log").write_text(clean)
    record = {
        "gate": "development", "exit": code, "seconds": round(time.monotonic() - tick, 1),
        "port": 4123, "started": started, "finished": datetime.now(timezone.utc).isoformat(),
        "reference_source_tree_sha256": EXPECTED, "source_matches_gate_workdir_before_and_after": True,
        "db_setup_recovered_from_temporary_server_race": recovered,
        "reviewer_script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "acceptance_script": "tools/one_shot_host/check-all.sh (unchanged)",
    }
    (RESULT / "development.json").write_text(json.dumps(record, indent=2) + "\n")
    print(json.dumps(record, indent=2), flush=True)
    print("\n".join(clean.splitlines()[-12:]), flush=True)
    raise SystemExit(code)


if __name__ == "__main__":
    main()
