"""Versioned TCP-readiness environment for the unstarted expert one-shots.

Inherits the original frozen lane and changes only PostgreSQL readiness in
the agent's broker. Freeze this adapter and its dependencies before coding;
the eight-step sessions continue using their original broker.
"""
import argparse
import runpy
import subprocess
import sys
from pathlib import Path

import lane_broker
import lane_review
import lane_run

ORIGINAL_PREPARE = lane_run.prepare
CONDITION = "expert-v2-tcp-readiness"
ADAPTERS = ("lane_oneshot.py", "lane_launch.py", "lane_continue.py", "lane_review.py")


def identity(stack):
    base = lane_run.verify_source(stack)
    record = {
        "condition": CONDITION,
        "base_fixture_sha256": base["sha256"],
        "files": {f"tools/{name}": lane_run.digest(lane_run.ROOT / "tools" / name)
                  for name in ADAPTERS},
        "change": "Require PostgreSQL TCP readiness in all broker checks before coding starts",
        "prompt_and_product_contract_changed": False,
    }
    return dict(record, sha256=lane_run.fingerprint(record))


def verify(session):
    if session["phase"] != "one-shot":
        raise RuntimeError("TCP agent adapter is reserved for the new one-shot condition")
    fixture = lane_run.load(Path(session["work"]) / "FIXTURE.json")
    record = fixture.get("runtime_adapter")
    if not record or fixture["condition"] != CONDITION:
        raise RuntimeError("One-shot runtime adapter was not frozen")
    if record != identity(session["stack"]):
        raise RuntimeError("One-shot runtime adapter changed after preparation")
    return record


def prepare(stack, phase):
    path = ORIGINAL_PREPARE(stack, phase)
    if phase != "one-shot":
        return path
    session = lane_run.load(path)
    work, logs, home = (Path(session[key]) for key in ("work", "logs", "home"))
    fixture = lane_run.load(work / "FIXTURE.json")
    if "runtime_adapter" in fixture:
        verify(session)
        return path
    if (logs / "events.jsonl").exists() or (home / "sessions").exists():
        raise RuntimeError("Cannot change the condition of a used coding session")
    record = identity(stack)
    note = work / "EXPERIMENT.md"
    note.chmod(0o644)
    note.write_text(note.read_text() + "\n## One-shot runtime correction\n\n"
                    "This one-shot uses the expert-v2-tcp-readiness condition. The broker "
                    "waits for PostgreSQL TCP readiness, avoiding the temporary initialization "
                    "server's Unix-socket readiness race observed during the eight-step runs. "
                    "The prompt, scaffold, specification, client and acceptance checks are unchanged. "
                    "FIXTURE.json records the effective adapter and inherited fixture hashes.\n")
    note.chmod(0o444)
    fixture.update(condition=CONDITION, runtime_adapter=record)
    fixture["files"]["EXPERIMENT.md"] = lane_run.digest(note)
    target = work / "FIXTURE.json"
    target.chmod(0o644)
    lane_run.save(target, fixture)
    target.chmod(0o444)
    session["fixture_file_sha256"] = lane_run.digest(target)
    session["effective_fixture_sha256"] = record["sha256"]
    lane_run.save(path, session)
    lane_run.save(Path(session["control"]) / "effective-fixture.json", record)
    lane_run.verify_workspace(session)
    verify(session)
    return path


def install_broker():
    original_verify = lane_broker.Session.verify

    def verified(self, **kwargs):
        verify(self.data)
        return original_verify(self, **kwargs)

    lane_review.install()
    tcp_command = lane_broker.command

    def command(argv, **kwargs):
        if len(argv) > 1 and argv[1] == str(lane_run.ROOT / "tools/bench/bench.py"):
            argv = [argv[0], str(Path(__file__).resolve()), "benchmark", *argv[2:]]
        return tcp_command(argv, **kwargs)

    lane_broker.command = command
    lane_broker.Session.verify = verified


def benchmark(args):
    """The frozen feedback workload runs in its own process; fix readiness only."""
    original = subprocess.run

    def tcp_ready(argv, *positional, **kwargs):
        if isinstance(argv, (list, tuple)) and "pg_isready" in argv and "-h" not in argv and "--host" not in argv:
            argv = [*argv, "-h", "127.0.0.1"]
        return original(argv, *positional, **kwargs)

    subprocess.run = tcp_ready
    try:
        path = lane_run.ROOT / "tools/bench/bench.py"
        sys.argv = [str(path), *args]
        runpy.run_path(str(path), run_name="__main__")
    finally:
        subprocess.run = original


def preflight(path):
    """Three fresh database initializations; no application source is changed."""
    session = lane_run.load(path)
    verify(session)
    if ((Path(session["logs"]) / "events.jsonl").exists()
            or (Path(session["home"]) / "sessions").exists()):
        raise RuntimeError("Readiness preflight must precede coding")
    lane_run.verify_workspace(session)
    proof_path = Path(session["control"]) / "readiness-preflight.json"
    if proof_path.exists():
        existing = lane_run.load(proof_path)
        if existing.get("passed") and existing["effective_fixture_sha256"] == verify(session)["sha256"]:
            print("Existing successful readiness preflight verified", flush=True)
            return 0
        raise RuntimeError("Preserving existing readiness preflight; diagnose before a new attempt")
    install_broker()
    scoped = lane_broker.Session(path)
    # Other measured lanes may still own their normal application/DB ports.
    scoped.port += 1000
    rounds = []
    with lane_broker.resources():
        scoped.verify()
        try:
            for number in range(1, 4):
                scoped.database(False)
                code, _ = scoped.database(True)
                tcp_code, _ = lane_broker.command(
                    ["docker", "exec", scoped.db, "pg_isready", "-h", "127.0.0.1",
                     "-U", "agentmvc", "-d", "agentmvc"], timeout=30)
                rounds.append({"round": number, "database_start_exit": code,
                               "explicit_tcp_probe_exit": tcp_code})
                if code or tcp_code:
                    break
        finally:
            scoped.database(False)
    record = {"passed": len(rounds) == 3 and all(
        row["database_start_exit"] == row["explicit_tcp_probe_exit"] == 0 for row in rounds),
        "checked_at": lane_run.stamp(), "effective_fixture_sha256": verify(session)["sha256"],
        "rounds": rounds, "probe_host_port": scoped.port + 50000,
        "coding_started": False, "application_source_changed": False}
    lane_run.save(proof_path, record)
    print(record, flush=True)
    return 0 if record["passed"] else 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["broker", "preflight", "benchmark"])
    args, rest = parser.parse_known_args()
    if args.action == "broker":
        sys.argv = [sys.argv[0], *rest]
        install_broker()
        lane_broker.main()
    elif args.action == "benchmark":
        benchmark(rest)
    else:
        parser = argparse.ArgumentParser()
        parser.add_argument("--session", required=True, type=Path)
        raise SystemExit(preflight(parser.parse_args(rest).session))
