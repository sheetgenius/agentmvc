"""Run the prepared Clojure lane using the unchanged lane runner and prompts.

The prepared-clojure condition includes Clojure source accounting, an isolated
broker port, and PostgreSQL TCP readiness from the first operation. It applies
to all eight steps and the expert v2 one-shot. Existing Go/Python fixtures and
their coordinators are never edited. Call install() before reusing the helpers
from a Clojure reviewer adapter.
"""
import argparse
import ast
import contextlib
import runpy
import shutil
import subprocess
import sys
import time
from pathlib import Path
from unittest.mock import patch

import lane_broker
import lane_check
import lane_run
import measure
import scrub
from lane_continue import scrub_events

STACK = "clojure"
CONDITION = "prepared-clojure"
BROKER_PORT = 49682
SOURCE_SUFFIXES = {".clj", ".cljc", ".cljs", ".edn"}
CACHE_DIRS = {"target", ".cpcache", ".lsp", ".gitlibs", ".m2"}
ADAPTER = Path(__file__).resolve()

# Capture the frozen implementation before installing any adapter hooks.
_source_snapshot = lane_run.source_snapshot
_prepare = lane_run.prepare
_prewarm = lane_run.prewarm
_launch = lane_run.launch
_publish = lane_run.publish
_independently_check = lane_run.independently_check
_execute = lane_run.execute
_session_verify = lane_broker.Session.verify
_command = lane_broker.command
_source_files = measure.source_files
_installed = False


def require_stack(stack):
    if stack != STACK:
        raise ValueError("This adapter is only for the new Clojure lane")


def helper_paths(paths):
    """Include local Python imports, including imports inside helper functions."""
    pending, found = list(paths), set()
    while pending:
        path = pending.pop()
        if path in found:
            continue
        found.add(path)
        tree = ast.parse(path.read_text(), filename=str(path))
        for node in ast.walk(tree):
            modules = ([item.name for item in node.names] if isinstance(node, ast.Import)
                       else [node.module] if isinstance(node, ast.ImportFrom) and node.module else [])
            for module in modules:
                local = lane_run.ROOT / "tools" / (module.split(".")[0] + ".py")
                if local.is_file() and local not in found:
                    pending.append(local)
    return found


def source_snapshot(stack):
    require_stack(stack)
    record = _source_snapshot(stack)
    entries = [lane_run.ROOT / name for name in record["files"] if name.endswith(".py")]
    entries.extend(lane_run.ROOT / "tools" / name for name in
                   ("clojure_lane.py", "one_shot_publish.py"))
    for path in sorted(helper_paths(entries)):
        relative = str(path.relative_to(lane_run.ROOT))
        record["files"][relative] = lane_run.digest(path)
        record["modes"][relative] = path.stat().st_mode & 0o111
    # lane-fixture.json is an output, never an input to its own hash.
    record["sha256"] = lane_run.fingerprint({key: record[key] for key in ("files", "modes")})
    return record


def identity():
    fixture = lane_run.verify_source(STACK)
    record = {"condition": CONDITION, "fixture_sha256": fixture["sha256"],
              "adapter": "tools/clojure_lane.py", "broker_port": BROKER_PORT,
              "postgres_readiness": "TCP on 127.0.0.1",
              "prompt_and_product_contract_changed": False}
    return dict(record, sha256=lane_run.fingerprint(record))


def verify(session):
    require_stack(session["stack"])
    fixture = lane_run.load(Path(session["work"]) / "FIXTURE.json")
    expected = "unscored-reference-repair" if session["phase"] == "reference" else CONDITION
    if fixture.get("condition") != expected or fixture.get("runtime_adapter") != identity():
        raise RuntimeError("Clojure condition was not frozen or its runtime adapter changed")
    if session.get("broker_port") != BROKER_PORT:
        raise RuntimeError("Clojure session has the wrong broker port")
    if session.get("effective_fixture_sha256") != fixture["runtime_adapter"]["sha256"]:
        raise RuntimeError("Clojure effective fixture differs from its session descriptor")
    return fixture["runtime_adapter"]


def used(session):
    return ((Path(session["logs"]) / "events.jsonl").exists()
            or (Path(session["home"]) / "sessions").exists())


def establish_condition(path):
    """Run at the base prepare/prewarm boundary, before any toolchain work."""
    session = lane_run.load(path)
    require_stack(session["stack"])
    work = Path(session["work"])
    fixture_path = work / "FIXTURE.json"
    fixture = lane_run.load(fixture_path)
    if "runtime_adapter" in fixture:
        verify(session)
        return
    if used(session):
        raise RuntimeError("Cannot change the condition of a used coding session")
    record = identity()
    note = work / "EXPERIMENT.md"
    note.chmod(0o644)
    note.write_text(note.read_text() + "\n## Prepared Clojure condition\n\n"
                    "This session uses prepared-clojure for all eight steps and the expert v2 "
                    "one-shot. PostgreSQL checks require TCP readiness from the first operation. "
                    "The broker uses its own port; Clojure source and tests are included in "
                    "publication and measured with the stack rules. Shared prompt bytes, "
                    "specifications, acceptance checks and the product-free scaffold are unchanged. "
                    "FIXTURE.json identifies the frozen coordinator and its helper sources.\n")
    note.chmod(0o444)
    fixture.update(condition=CONDITION, runtime_adapter=record)
    fixture["files"]["EXPERIMENT.md"] = lane_run.digest(note)
    fixture_path.chmod(0o644)
    lane_run.save(fixture_path, fixture)
    fixture_path.chmod(0o444)
    session.update(broker_port=BROKER_PORT,
                   fixture_file_sha256=lane_run.digest(fixture_path),
                   effective_fixture_sha256=record["sha256"])
    lane_run.save(path, session)
    lane_run.save(Path(session["control"]) / "effective-fixture.json", record)
    lane_run.verify_workspace(session)
    verify(session)


def prewarm(path):
    establish_condition(path)
    return _prewarm(path)


def prepare(stack, phase):
    require_stack(stack)
    if phase != "one-shot" and phase not in {str(n) for n in range(1, 9)}:
        raise ValueError("Phase must be 1..8 or one-shot")
    path = _prepare(stack, phase)
    verify(lane_run.load(path))
    return path


def tcp_argv(argv):
    if (isinstance(argv, (list, tuple)) and "pg_isready" in argv
            and not any(str(arg) in {"-h", "--host"} or str(arg).startswith("--host=")
                        for arg in argv)):
        return [*argv, "-h", "127.0.0.1"]
    return argv


def route_command(argv):
    """Change only the coordinator entrypoint; preserve every worker argument."""
    if not isinstance(argv, (list, tuple)) or len(argv) < 2:
        return argv
    routes = {str(lane_run.ROOT / "tools/lane_broker.py"): "broker",
              str(lane_run.ROOT / "tools/lane_check.py"): "check-worker",
              str(lane_run.ROOT / "tools/bench/bench.py"): "benchmark"}
    action = routes.get(str(argv[1]))
    return [argv[0], str(ADAPTER), action, *argv[2:]] if action else argv


@contextlib.contextmanager
def routed_processes():
    original = subprocess.Popen

    def popen(argv, *args, **kwargs):
        return original(route_command(argv), *args, **kwargs)

    with patch.object(subprocess, "Popen", popen):
        yield


def command(argv, **kwargs):
    return _command(route_command(tcp_argv(argv)), **kwargs)


def session_verify(self, **kwargs):
    verify(self.data)
    return _session_verify(self, **kwargs)


def launch(path):
    session = lane_run.load(path)
    record = verify(session)
    if used(session):
        raise RuntimeError("Measured session already used")
    # Shared resource waiting precedes the original measured clock.
    before = time.monotonic()
    with lane_broker.resources():
        pass
    queue_seconds = round(time.monotonic() - before, 2)
    logs = Path(session["logs"])
    logs.mkdir(exist_ok=True)
    lane_run.save(logs / "launch-adapter.json", {
        "adapter": "tools/clojure_lane.py", "sha256": lane_run.digest(ADAPTER),
        "condition": CONDITION, "effective_fixture_sha256": record["sha256"],
        "queue_seconds": queue_seconds, "prompt_and_product_contract_changed": False,
        "agent_command_and_effort_counters_changed": False})
    with routed_processes():
        return _launch(path)


def is_test(path):
    return ("test" in path.parts or "tests" in path.parts
            or path.name.endswith(("_test.clj", "_test.cljc", "_test.cljs")))


def source_files(rules, base):
    for relative, rule in _source_files(rules, base):
        if rules.get("stack") == STACK and is_test(Path(relative)):
            continue
        yield relative, rule


def supplementary_size(work):
    extras = {kind: {"tokens": 0, "lines": 0, "files": []} for kind in ("tests", "docs")}
    for path in lane_run.product_files(work):
        relative = path.relative_to(work)
        kind = "docs" if path.suffix == ".md" else "tests" if is_test(relative) else None
        if kind:
            lines = measure.read_lines(path.read_text())
            extras[kind]["tokens"] += measure.tokens(lines)
            extras[kind]["lines"] += len(lines)
            extras[kind]["files"].append(str(relative))
    return extras


def publish(path):
    session = lane_run.load(path)
    record = verify(session)
    _publish(path)
    dest = Path(session["result"])
    lane_run.save(dest / "supplementary-size.json", supplementary_size(Path(session["work"])))
    lane_run.save(dest / "effective-fixture.json", record)
    lane_run.save(dest / "publication-adapter.json", {
        "adapter": "tools/clojure_lane.py", "sha256": lane_run.digest(ADAPTER),
        "condition": CONDITION, "effective_fixture_sha256": record["sha256"],
        "validation": "Decoded JSON strings and keys plus rendered Markdown",
        "source_extensions_added": sorted(SOURCE_SUFFIXES), "cache_dirs_excluded": sorted(CACHE_DIRS)})
    launch_record = Path(session["logs"]) / "launch-adapter.json"
    if launch_record.exists():
        lane_run.save(dest / launch_record.name, lane_run.load(launch_record))


def independently_check(path):
    session = lane_run.load(path)
    verify(session)
    previous = Path(session["result"]) / "verification.json"
    if previous.exists():
        history = previous.parent / "verification-attempts"
        history.mkdir(exist_ok=True)
        shutil.copy2(previous, history / f"{len(list(history.glob('*.json'))) + 1:02d}.json")
    control = Path(session["control"])
    logs = [control / f"independent-{action}.log" for action in ("development", "production")]
    if any(log.exists() for log in logs):
        history = control / "independent-attempts"
        history.mkdir(exist_ok=True)
        attempt = history / f"{len(list(history.iterdir())) + 1:02d}"
        attempt.mkdir()
        for log in logs:
            if log.exists():
                shutil.copy2(log, attempt / log.name)
    with routed_processes():
        return _independently_check(path)


def execute(path):
    verify(lane_run.load(path))
    with routed_processes():
        return _execute(path)


def benchmark(args):
    """Preserve the frozen benchmark workload and require TCP readiness."""
    original = subprocess.run

    def run(argv, *positional, **kwargs):
        return original(tcp_argv(argv), *positional, **kwargs)

    path = lane_run.ROOT / "tools/bench/bench.py"
    with patch.object(subprocess, "run", run), patch.object(sys, "argv", [str(path), *args]):
        runpy.run_path(str(path), run_name="__main__")


def install():
    global _installed
    if _installed:
        return
    lane_run.SOURCE_SUFFIXES.update(SOURCE_SUFFIXES)
    lane_run.SKIP.update(CACHE_DIRS)
    measure.SKIP_DIRS.update(CACHE_DIRS)
    measure.source_files = source_files
    scrub.scrub_file = scrub_events
    lane_run.source_snapshot = source_snapshot
    lane_run.prepare = prepare
    lane_run.prewarm = prewarm
    lane_run.launch = launch
    lane_run.publish = publish
    lane_run.independently_check = independently_check
    lane_run.execute = execute
    lane_broker.command = command
    lane_broker.Session.verify = session_verify
    _installed = True


def main(argv=None):
    install()
    args = list(sys.argv[1:] if argv is None else argv)
    if args and args[0] in {"broker", "check-worker", "benchmark"}:
        action, rest = args[0], args[1:]
        if action == "benchmark":
            benchmark(rest)
            return 0
        with patch.object(sys, "argv", [str(ADAPTER), *rest]):
            return lane_broker.main() if action == "broker" else lane_check.main()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("freeze", "prepare", "isolation", "run", "publish",
                                           "check", "pipeline", "one-shot"))
    parser.add_argument("target")
    parser.add_argument("phase", nargs="?", choices=tuple(map(str, range(1, 9))) + ("one-shot",))
    parser.add_argument("--through", type=int, choices=range(1, 9), default=8)
    parsed = parser.parse_args(args)
    if parsed.action in {"freeze", "prepare", "pipeline", "one-shot"}:
        require_stack(parsed.target)
        if parsed.action == "prepare" and parsed.phase is None:
            parser.error("prepare requires a phase (1..8 or one-shot)")
    else:
        verify(lane_run.load(Path(parsed.target).resolve()))
    with patch.object(sys, "argv", [str(ADAPTER), *args]):
        return lane_run.main()


if __name__ == "__main__":
    raise SystemExit(main())
