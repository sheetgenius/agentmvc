"""Independently verify or measure one immutable lane session.

Usage: python3 tools/lane_check.py --session /absolute/session.json ACTION
ACTION: development | production | benchmark | security-scan
Development and production use frozen host checks, never agent-written bin/check.
"""
import argparse
import contextlib
import json
import os
import re
import sys
import time
import urllib.request
import uuid
from pathlib import Path

import lane_broker as broker

ROOT = broker.ROOT
LIMITS = ["--cpus=2", "--memory=1g"]
SCENARIOS = ["list_anonymous", "list_signed_in", "list_by_tag", "feed", "article",
             "comments", "tags", "favorite_toggle", "create_article"]


class Failure(Exception):
    def __init__(self, code):
        self.code = code


def append(result, output):
    code, text = result
    output.append(text)
    if code:
        raise Failure(code)


def ready(session, container, output):
    deadline = time.monotonic() + 180
    while time.monotonic() < deadline:
        code, state = broker.command(["docker", "inspect", "--format", "{{.State.Running}}", container], timeout=15)
        if code or state.strip() != "true":
            output.append(broker.command(["docker", "logs", "--tail", "100", container], timeout=30)[1])
            raise RuntimeError("Application exited before readiness")
        try:
            request = urllib.request.Request(f"http://127.0.0.1:{session.port}/api/tags",
                                             headers={"Accept": "application/json"})
            with urllib.request.urlopen(request, timeout=2) as response:
                if response.status == 200:
                    return
        except Exception:
            pass
        time.sleep(.25)
    output.append(broker.command(["docker", "logs", "--tail", "100", container], timeout=30)[1])
    raise RuntimeError("Application readiness exceeded 180 seconds")


def development(session, output):
    session.stop()
    session.database(False)
    try:
        append(session.database(True), output)
        append(session.start(), output)
        ready(session, session.dev, output)
        append(session.gate("all"), output)
        append(session.tool("lint"), output)
        append(session.tool("test", test=True), output)
    finally:
        output.append(broker.command(["docker", "logs", "--tail", "100", session.dev], timeout=30)[1])
        session.stop()
        session.database(False)


@contextlib.contextmanager
def production_app(session, output):
    if session.number < 3:
        raise RuntimeError("Production packaging begins at step 3")
    session.stop()
    append(session.build(), output)
    name = session.prefix + "-prod-" + uuid.uuid4().hex[:8]
    network, db, app = name + "-net", name + "-db", name + "-app"
    try:
        append(broker.command(["docker", "network", "create", network], timeout=30), output)
        append(broker.command(["docker", "run", "-d", "--name", db, "--network", network,
                               "--network-alias", "db", *LIMITS, "-e", "POSTGRES_USER=agentmvc",
                               "-e", "POSTGRES_PASSWORD=agentmvc", "-e", "POSTGRES_DB=agentmvc",
                               broker.POSTGRES], timeout=120), output)
        for _ in range(120):
            if broker.command(["docker", "exec", db, "pg_isready", "-U", "agentmvc",
                                "-d", "agentmvc"], timeout=10)[0] == 0:
                break
            time.sleep(.5)
        else:
            raise RuntimeError("Production database readiness timed out")
        append(broker.command(["docker", "run", "-d", "--name", app, "--network", network,
                               *LIMITS, "-p", f"127.0.0.1:{session.port}:{session.port}",
                               "-e", "DATABASE_URL=postgres://agentmvc:agentmvc@db:5432/agentmvc",
                               "-e", "SECRET_KEY_BASE=" + "0123456789abcdef" * 8,
                               "-e", f"PORT={session.port}", session.production_image], timeout=120), output)
        ready(session, app, output)
        yield app
    finally:
        output.append(broker.command(["docker", "logs", "--tail", "100", app], timeout=30)[1])
        broker.command(["docker", "rm", "-f", app, db], timeout=30)
        broker.command(["docker", "network", "rm", network], timeout=30)


def production(session, output):
    with production_app(session, output):
        append(session.gate("all"), output)


def write_result(session, kind, result):
    targets = [f".checks/{kind}/latest"]
    if kind == "perf":
        targets.append("perf/latest")
    for relative in targets:
        destination = session.output_dir(relative)
        path = broker.safe_path(session.work, str((destination / "results.json").relative_to(session.work)))
        path.write_text(json.dumps(result, indent=2) + "\n")


def benchmark(session, output):
    if session.number < 3:
        raise RuntimeError("Benchmark requires a production image (step 3 onward)")
    session.stop()
    append(session.build(), output)
    label = session.id + "-" + uuid.uuid4().hex[:8]
    scratch = session.logs / "measurements" / label
    scratch.mkdir(parents=True)
    env = {key: value for key, value in os.environ.items() if not key.startswith("BENCH_")}
    env.update(BENCH_WARMUP="1s", BENCH_DURATION="3s", BENCH_HOST_PORT=str(session.port + 14000),
               BENCH_RAW_OUTPUT="1")
    args = [sys.executable, str(ROOT / "tools/bench/bench.py"), session.production_image, label, str(scratch)]
    try:
        code, text = broker.command(args, env=env, timeout=600)
        output.append(text)
        (scratch / "runner.log").write_text(text)
    finally:
        for name in (f"agentmvc-bench-app-{label}", f"agentmvc-bench-db-{label}"):
            broker.command(["docker", "rm", "-f", name], timeout=30)
        broker.command(["docker", "network", "rm", f"agentmvc-bench-{label}"], timeout=30)
    path = scratch / "results.json"
    if not path.exists():
        raise RuntimeError("Benchmark did not produce results.json; raw logs retained")
    result = json.loads(path.read_text())
    result.pop("app_log_tail", None)
    result.update(session=session.id, condition="short feedback benchmark", warmup="1s", duration="3s",
                  image_sha256=broker.checked(["docker", "image", "inspect", "--format", "{{.Id}}",
                                               session.production_image], timeout=30))
    rows = result.get("scenarios", {})
    result["exit"] = code or (1 if set(rows) != set(SCENARIOS) or
                               any(row.get("failed_checks", 0) for row in rows.values()) else 0)
    (scratch / "results.json").write_text(json.dumps(result, indent=2) + "\n")
    write_result(session, "perf", result)
    output.append("Benchmark summary: .checks/perf/latest/results.json (also perf/latest/results.json).\n")
    if result["exit"]:
        raise Failure(result["exit"])


def security_scan(session, output):
    record = {"session": session.id, "stack": session.data["stack"], "started": broker.stamp()}
    with production_app(session, output):
        code, text = session.gate("security")
        output.append(text)
        cases = {name: status == "Success" for status, name in
                 re.findall(r"(Success|Failure) (s\d+_\w+)\.hurl", text)}
        record.update(black_box=cases, black_box_exit=code,
                      core_passed=sum(ok for name, ok in cases.items()
                                      if not name.startswith(("s12_", "s13_"))),
                      core_total=11,
                      defense_in_depth_passed=sum(ok for name, ok in cases.items()
                                                  if name.startswith(("s12_", "s13_"))),
                      defense_in_depth_total=2)
        if len(cases) != 13:
            raise RuntimeError("Security scan did not report all 13 cases")
    for key, command_name in (("static_analysis", "security"), ("dependencies", "dependencies")):
        if session.argv(command_name):
            code, text = session.tool(command_name)
            output.append(text)
            record[key] = {"exit": code, "output": text[-12000:]}
        else:
            record[key] = {"status": "not configured"}
    record.update(finished=broker.stamp(), image_sha256=broker.checked(
        ["docker", "image", "inspect", "--format", "{{.Id}}", session.production_image], timeout=30))
    scratch = session.logs / "security-scans"
    scratch.mkdir(parents=True, exist_ok=True)
    (scratch / f"{uuid.uuid4().hex}.json").write_text(json.dumps(record, indent=2) + "\n")
    write_result(session, "security", record)
    output.append("Security baseline: .checks/security/latest/results.json. Failing cases are recorded as findings.\n")


def perform(session, action):
    output, code = [], 0
    try:
        {"development": development, "production": production,
         "benchmark": benchmark, "security-scan": security_scan}[action](session, output)
    except Failure as failure:
        code = failure.code
    except Exception as error:
        code = 1
        output.append(f"Coordinator {action} failed: {type(error).__name__}: {error}\n")
    return code, "\n".join(output)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--session", type=Path, required=True)
    parser.add_argument("action", choices=("development", "production", "benchmark", "security-scan"))
    args = parser.parse_args()
    session = broker.Session(args.session)
    started, tick = broker.stamp(), time.monotonic()
    with broker.resources():
        session.verify()
        code, output = perform(session, args.action)
        try:
            session.verify()
        except Exception as error:
            code = 1
            output += f"\nFrozen input verification failed: {error}\n"
    dest = session.logs / "independent"
    dest.mkdir(parents=True, exist_ok=True)
    stem = f"{args.action}-{started.replace(':', '-')}-{uuid.uuid4().hex[:8]}"
    (dest / f"{stem}.log").write_text(output)
    record = {"session": session.id, "stack": session.data["stack"], "phase": session.data["phase"],
              "number": session.number, "gate": args.action, "started": started,
              "finished": broker.stamp(), "seconds": round(time.monotonic() - tick, 1), "exit": code,
              "fixture_record_sha256": session.fixture_digest, "log": f"{stem}.log"}
    (dest / f"{stem}.json").write_text(json.dumps(record, indent=2) + "\n")
    print(output, flush=True)
    print(json.dumps(record, indent=2), flush=True)
    return code


if __name__ == "__main__":
    raise SystemExit(main())
