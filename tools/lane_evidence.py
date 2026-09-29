"""Reviewer evidence for completed Go/Python lanes; never edits measured inputs.

parity [--session PATH ...]: frozen production gates and exact common HTTP probe.
runtime: original four applications, two reversed-order HTTP/socket rounds;
         --condition reference --session PATH ... measures strict references.
validate [--condition measured|reference]: verify runtime streams without Docker.
comprehension-prepare --session PATH: source-only copy for step 1 or 6.
comprehension-run --session PATH --answer-key PATH: fresh read-only reader.

Run parity/runtime only after measured coding has stopped. Existing evidence is
preserved. Failed runs require a separately named condition, not an overwrite.
"""
import argparse
import json
import os
import re
import shutil
import signal
import subprocess
import sys
import time
from pathlib import Path

import lane_broker as broker
import lane_check
import lane_continue as publication
import lane_review as reviewer
import lane_run
import scrub
import v2_expert_symmetry_validate as raw_validation

ROOT = broker.ROOT
OUT = ROOT / "results/lanes"
ENTRIES = (("go", "8"), ("python", "8"), ("go", "one-shot"), ("python", "one-shot"))
SCENARIOS = set(lane_check.SCENARIOS)
SOCKET_COUNTS = (10, 100, 500)
TOOLS = ("lane_evidence.py", "lane_check.py", "lane_broker.py", "lane_continue.py", "lane_review.py",
         "reviewer_common_http_probe.py", "bench/bench.py", "bench/load.js", "bench/seed.py",
         "one_shot_live_bench.py", "live-load.mjs", "v2_expert_symmetry_validate.py", "scrub.py")


def load(path):
    return json.loads(Path(path).read_text())


def cleaner(session):
    token = session.control / "token"
    deny = [re.escape(token.read_text().strip())] if token.exists() else []
    return scrub.Scrubber(session.work, deny)


def write_text(path, value, session):
    text = cleaner(session).text(value)
    leaks = cleaner(session).leaks(text)
    if leaks:
        raise RuntimeError(f"Publication contains sensitive material: {leaks}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)


def save(path, value, session):
    # Scrub string values before serialization, so redaction never breaks JSON.
    value = cleaner(session).value(value)
    text = json.dumps(value, indent=2, ensure_ascii=False) + "\n"
    if any(cleaner(session).leaks(item) for item in publication.strings(json.loads(text))):
        raise RuntimeError(f"Publication failed scrub validation: {path.name}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)


def tool_hashes():
    return {name: broker.digest(ROOT / "tools" / name) for name in TOOLS}


def source_identity(session, *, gated=True):
    """Match the built workspace to its published, independently gated snapshot."""
    lane_run.verify_source(session.data["stack"])
    session.verify(image=False)
    result = Path(session.data["result"])
    snapshot = load(result / "source-snapshot.json")
    expected = snapshot["files"]
    if lane_run.fingerprint(expected) != snapshot["sha256"]:
        raise RuntimeError("Published source manifest hash is inconsistent")
    published = Path(session.data["publish_source"])
    actual = {str(p.relative_to(published)): broker.digest(p)
              for p in lane_run.checked_files(published)}
    working = {str(p.relative_to(session.work)): broker.digest(p)
               for p in lane_run.product_files(session.work)}
    if actual != expected or working != expected:
        raise RuntimeError("Working/published source differs from the recorded snapshot")
    if (session.logs / "active.json").exists():
        raise RuntimeError("Measured agent session is still active")
    if gated:
        verification = load(result / "verification.json")
        if not verification.get("passed") or verification.get("source_sha256") != snapshot["sha256"]:
            raise RuntimeError("Independent gates must pass on this exact snapshot first")
    return {"session": session.id, "stack": session.data["stack"], "phase": session.data["phase"],
            "condition": load(session.work / "FIXTURE.json")["condition"],
            "source_sha256": snapshot["sha256"], "fixture_sha256": session.data["fixture_sha256"],
            "fixture_record_sha256": session.fixture_digest,
            "prompt_sha256": broker.digest(session.work / "PROMPT.md")}


def image_id(session):
    return broker.checked(["docker", "image", "inspect", "--format", "{{.Id}}",
                           session.production_image], timeout=30)


def parity_path(session):
    return Path(session.data["result"]) / "reviewer-parity"


def parity(session):
    reviewer.install()
    if session.number != 8:
        raise RuntimeError("Final parity applies to step 8 and expert one-shot sessions")
    dest = parity_path(session)
    if dest.exists():
        raise RuntimeError(f"Preserving existing parity evidence: {dest}")
    dest.mkdir(parents=True)
    record = {"session": session.id, "stack": session.data["stack"], "phase": session.data["phase"],
              "started": broker.stamp(), "tools_sha256": tool_hashes(),
              "limits": lane_check.LIMITS, "database": broker.POSTGRES,
              "app_environment_keys": ["DATABASE_URL", "SECRET_KEY_BASE", "PORT"],
              "passed": False, "exit": 1}
    output = []
    try:
        identity = source_identity(session)
        record.update(identity)
        with broker.resources():
            session.verify()
            with lane_check.production_app(session, output):
                record["image_sha256"] = image_id(session)
                code, log = session.gate("all")
                output.append(log)
                record["frozen_production_gate_exit"] = code
                probe_code, text = broker.command([
                    sys.executable, str(ROOT / "tools/reviewer_common_http_probe.py"),
                    "--base-url", f"http://127.0.0.1:{session.port}", "--strict-diagnostics"], timeout=600)
                record["http_probe_exit"] = probe_code
                try:
                    record["http_probe"] = json.loads(text)
                except ValueError:
                    output.append(text)
                    raise RuntimeError("Common HTTP probe did not return JSON")
                summary = record["http_probe"].get("summary", {})
                record["http_probe_complete"] = (summary.get("contract_total") == 21 and
                                                  summary.get("quality_total") == 3)
                record["passed"] = (code == probe_code == 0 and record["http_probe_complete"])
                record["exit"] = 0 if record["passed"] else 1
            session.verify()
            if source_identity(session) != identity:
                raise RuntimeError("Source changed during parity evaluation")
    except Exception as error:
        record.update(passed=False, exit=1, error=f"{type(error).__name__}: {error}")
    finally:
        record["finished"] = broker.stamp()
        write_text(dest / "runner.log", "\n".join(output), session)
        save(dest / "results.json", record, session)
    print(f"{session.id}: parity {'passed' if record['passed'] else 'failed'}", flush=True)
    return record


def stream_names():
    return {f"raw-{prefix}{name}.json.zst" for name in SCENARIOS for prefix in ("", "warmup-")}


def inspect_streams(dest, expected):
    if set(expected) != stream_names():
        raise RuntimeError(f"Expected all 18 warmup/measurement streams: {dest}")
    rows = []
    for name, sha in sorted(expected.items()):
        path = dest / name
        if raw_validation.digest(path) != sha:
            raise RuntimeError(f"Changed raw stream: {path}")
        size, hits = raw_validation.inspect(path)
        if hits:
            raise RuntimeError(f"Sensitive raw-stream markers: {hits}")
        rows.append({"path": str(path.relative_to(OUT / "runtime")), "sha256": sha,
                     "compressed_bytes": path.stat().st_size, "decompressed_bytes": size})
    return rows


def runtime_checks(data):
    rows = data.get("scenarios", {})
    return (data.get("exit") == 0 and set(rows) == SCENARIOS and
            all(row.get("requests", 0) > 0 and row.get("failed_checks") == 0 for row in rows.values()) and
            data.get("vus") == 16 and data.get("duration") == "15s" and
            data.get("warmup") == "3s" and data.get("extra_env") == "" and
            data.get("limits") == lane_check.LIMITS)


def http_round(session, identity, round_number, dest):
    scratch = ROOT / ".work/lane-evidence" / session.id / f"http-round{round_number}"
    scratch.mkdir(parents=True, exist_ok=False)
    dest.mkdir(parents=True, exist_ok=False)
    label = f"lane-evidence-{session.id}-r{round_number}"
    env = {key: value for key, value in os.environ.items() if not key.startswith("BENCH_")}
    env.update(BENCH_WARMUP="3s", BENCH_DURATION="15s", BENCH_RAW_OUTPUT="1",
               BENCH_HOST_PORT=str(session.port + 14000))
    record = {**identity, "round": round_number, "started": broker.stamp(), "exit": 1,
              "tools_sha256": tool_hashes(), "raw_stream_sha256": {}, "warmup": "3s"}
    try:
        code, text = broker.command([sys.executable, str(Path(__file__).resolve()), "_http",
                                      "--image", session.production_image, "--label", label,
                                      "--output", str(scratch)], env=env, timeout=3600)
        (scratch / "runner.log").write_text(text)
        write_text(dest / "runner.log", text, session)
        data = load(scratch / "results.json")
        data.pop("app_log_tail", None)
        record.update(data, exit=code)
        for path in sorted(scratch.glob("k6-*.json")):
            save(dest / path.name, load(path), session)
        # Validate in private scratch before publishing any compressed bytes.
        for path in sorted(scratch.glob("raw-*.json")):
            compressed = scratch / (path.name + ".zst")
            broker.checked(["zstd", "-q", "-T2", "-o", str(compressed), str(path)])
            _, hits = raw_validation.inspect(compressed)
            if hits:
                raise RuntimeError(f"Sensitive raw-stream markers: {hits}")
            shutil.copy2(compressed, dest / compressed.name)
            record["raw_stream_sha256"][compressed.name] = raw_validation.digest(compressed)
        record["passed"] = (runtime_checks(record) and set(record["raw_stream_sha256"]) == stream_names())
        if not record["passed"]:
            record["exit"] = code or 1
    except Exception as error:
        record.update(passed=False, exit=1, error=f"{type(error).__name__}: {error}")
    finally:
        for name in (f"agentmvc-bench-app-{label}", f"agentmvc-bench-db-{label}"):
            broker.command(["docker", "rm", "-f", name], timeout=30)
        broker.command(["docker", "network", "rm", f"agentmvc-bench-{label}"], timeout=30)
        record["finished"] = broker.stamp()
        save(dest / "results.json", record, session)
    if record["passed"]:
        shutil.rmtree(scratch)  # synthetic seed credentials are never exported
    return record


def benchmark_worker(image, label, output):
    """Run the frozen benchmark, correcting only its observed PG startup race."""
    import runpy
    original = subprocess.run

    def tcp_ready(args, *positional, **kwargs):
        if isinstance(args, (list, tuple)) and "pg_isready" in args and "-h" not in args and "--host" not in args:
            args = [*args, "-h", "127.0.0.1"]
        return original(args, *positional, **kwargs)

    subprocess.run = tcp_ready
    try:
        path = ROOT / "tools/bench/bench.py"
        sys.argv = [str(path), image, label, str(output)]
        runpy.run_path(str(path), run_name="__main__")
    finally:
        subprocess.run = original


def socket_worker(port, app):
    import one_shot_live_bench as live
    live.HOST_PORT = port
    data = {"baseline": live.sample(app), "scenarios": []}
    for count in SOCKET_COUNTS:
        data["scenarios"].append(live.workload(app, count, 20))
    print(json.dumps(data), flush=True)


def socket_checks(data):
    scenarios = data.get("scenarios", [])
    return (data.get("exit") == 0 and [row.get("subscribers") for row in scenarios] == list(SOCKET_COUNTS)
            and all(row.get("saves") == 20 and all(row.get(key) == 0 for key in
                    ("missing", "duplicate_revisions", "regressed_revisions")) for row in scenarios))


def socket_round(session, identity, round_number, dest):
    dest.mkdir(parents=True, exist_ok=False)
    output = []
    record = {**identity, "round": round_number, "started": broker.stamp(), "exit": 1,
              "limits": lane_check.LIMITS, "database": broker.POSTGRES,
              "backend_instances": 1, "tools_sha256": tool_hashes()}
    try:
        with lane_check.production_app(session, output) as app:
            if image_id(session) != identity["image_sha256"]:
                raise RuntimeError("Production image changed before the socket workload")
            code, text = broker.command([sys.executable, str(Path(__file__).resolve()),
                                        "_socket", "--port", str(session.port), "--app", app], timeout=600)
            output.append(text)
            record.update(json.loads(text), exit=code)
        record["passed"] = socket_checks(record)
        if not record["passed"]:
            record["exit"] = code or 1
    except Exception as error:
        record.update(passed=False, exit=1, error=f"{type(error).__name__}: {error}")
    finally:
        record["finished"] = broker.stamp()
        write_text(dest / "runner.log", "\n".join(output), session)
        save(dest / "results.json", record, session)
    return record


def runtime(sessions, condition="measured"):
    reviewer.install()
    dest = OUT / "runtime" / condition
    if dest.exists():
        raise RuntimeError(f"Preserving existing runtime evidence: {dest}")
    identities = {}
    for session in sessions:
        identity = source_identity(session)
        proof = load(parity_path(session) / "results.json")
        if (proof.get("source_sha256") != identity["source_sha256"] or
                proof.get("frozen_production_gate_exit") != 0 or not proof.get("image_sha256")):
            raise RuntimeError(f"Frozen production gates must pass on this snapshot: {session.id}")
        if condition == "reference" and not proof.get("passed"):
            raise RuntimeError(f"Reference runtime requires full reviewer parity: {session.id}")
        identities[session.id] = {**identity, "image_sha256": proof["image_sha256"]}
    if len(identities) != len(sessions):
        raise RuntimeError("Runtime session list contains duplicates")
    record = {"condition": condition, "description": "prepared-scaffold final production runtime", "started": broker.stamp(),
              "rounds": 2, "http_vus": 16, "http_warmup": "3s", "http_duration": "15s",
              "http_scenarios": lane_check.SCENARIOS, "socket_subscribers": list(SOCKET_COUNTS), "socket_saves": 20,
              "limits": {"app": "2 CPU, 1 GiB", "database": "2 CPU, 1 GiB"},
              "tools_sha256": tool_hashes(), "applications": identities, "order": [], "records": [], "passed": False,
              "reviewer_parity": {session.id: {key: load(parity_path(session) / "results.json").get(key)
                  for key in ("passed", "http_probe_complete", "http_probe_exit", "frozen_production_gate_exit")}
                  for session in sessions},
              "interpretation": "Runtime success does not imply supplemental reviewer parity; see reviewer_parity."}
    dest.mkdir(parents=True)
    try:
        with broker.resources():
            for session in sessions:
                session.verify()
                if image_id(session) != identities[session.id]["image_sha256"]:
                    raise RuntimeError(f"Production image differs from parity: {session.id}")
            record["http_database_image_sha256"] = broker.checked(
                ["docker", "image", "inspect", "--format", "{{.Id}}", "postgres:17-alpine"])
            record["load_generator_image_sha256"] = broker.checked(
                ["docker", "image", "inspect", "--format", "{{.Id}}", "grafana/k6:latest"])
            record["socket_database_image"] = broker.POSTGRES
            for number, order in ((1, sessions), (2, list(reversed(sessions)))):
                for session in order:
                    identity = identities[session.id]
                    record["order"].append({"round": number, "session": session.id})
                    kinds = ("http", "socket") if number == 1 else ("socket", "http")
                    for kind in kinds:
                        print(f"{session.id}: round {number} {kind}", flush=True)
                        target = dest / session.id / f"round{number}" / kind
                        run = http_round if kind == "http" else socket_round
                        result = run(session, identity, number, target)
                        record["records"].append({"session": session.id, "round": number, "kind": kind,
                                                  "passed": result["passed"], "path": str(target.relative_to(dest))})
                        if source_identity(session) != {k: v for k, v in identity.items() if k != "image_sha256"}:
                            raise RuntimeError("Source changed during runtime evaluation")
                        if image_id(session) != identity["image_sha256"]:
                            raise RuntimeError("Production image changed during runtime evaluation")
            record["passed"] = all(row["passed"] for row in record["records"])
    except Exception as error:
        record["error"] = f"{type(error).__name__}: {error}"
    finally:
        record["finished"] = broker.stamp()
        save(dest / "summary.json", record, sessions[0])
    if record["passed"]:
        validate(condition)
    return record


def validate(condition="measured"):
    base = OUT / "runtime" / condition
    summary = load(base / "summary.json")
    expected_sessions = set(summary.get("applications", {}))
    if (summary.get("condition") != condition or not summary.get("passed") or
            not expected_sessions or len(summary.get("records", [])) != len(expected_sessions) * 4):
        raise RuntimeError("Runtime summary is incomplete or failed")
    originals = {f"{stack}-{'one-shot' if phase == 'one-shot' else lane_run.workdir.step_name(8)}-1"
                 for stack, phase in ENTRIES}
    if condition == "measured" and expected_sessions != originals:
        raise RuntimeError("Measured runtime must include all four original applications")
    expected_records = {(session, number, kind) for session in expected_sessions
                        for number in (1, 2) for kind in ("http", "socket")}
    actual_records = {(row["session"], row["round"], row["kind"]) for row in summary["records"]}
    if actual_records != expected_records:
        raise RuntimeError("Runtime does not contain each application in both rounds")
    rows = []
    for entry in summary["records"]:
        dest = base / entry["path"]
        data = load(dest / "results.json")
        identity = summary["applications"][entry["session"]]
        if any(data.get(key) != identity[key] for key in ("source_sha256", "image_sha256")):
            raise RuntimeError(f"Runtime identity mismatch: {dest}")
        if entry["kind"] == "http":
            if not runtime_checks(data):
                raise RuntimeError(f"Incomplete HTTP round: {dest}")
            rows.extend(inspect_streams(dest, data["raw_stream_sha256"]))
        elif not socket_checks(data):
            raise RuntimeError(f"Incomplete socket round: {dest}")
    result = {"status": "pass", "raw_streams": len(rows), "sensitive_marker_hits": {},
              "compressed_bytes": sum(row["compressed_bytes"] for row in rows),
              "decompressed_bytes": sum(row["decompressed_bytes"] for row in rows), "files": rows}
    if len(rows) != len(expected_sessions) * 36:
        raise RuntimeError("Expected 36 raw streams per application across two rounds")
    (base / "raw-validation.json").write_text(json.dumps(result, indent=2) + "\n")
    print(f"Validated {len(rows)} compressed raw streams", flush=True)
    return result


def comprehension_paths(session):
    if session.number not in (1, 6) or session.data["phase"] == "one-shot":
        raise RuntimeError("Original comprehension observations are after steps 1 and 6")
    label = f"{session.data['stack']}-after-{session.data['phase']}"
    return ROOT / ".work/lane-comprehension" / label, OUT / "comprehension" / label


def read_only_config(work):
    # Reuse the lane's tested isolation profile, with an explicit read rule for
    # the entire reader workspace and no network. No model-side instructions,
    # answers, harness, docs, or inherited memory are copied into that workspace.
    config = lane_run.home_config(work, []).replace('extends = ":workspace"', 'extends = ":read-only"')
    section = "[permissions.workspace-only.network]\nenabled = true"
    return config.replace(section, f'{json.dumps(str(work))} = "read"\n'
                          '[permissions.workspace-only.network]\nenabled = false')


def comprehension_prepare(session):
    identity = source_identity(session)
    base, dest = comprehension_paths(session)
    if base.exists() or dest.exists():
        raise RuntimeError(f"Preserving existing comprehension session: {base}")
    work = base / "app"
    work.mkdir(parents=True)
    published = Path(session.data["publish_source"])
    inventory = load(Path(session.data["result"]) / "source-files.json")
    files = {}
    for row in inventory:
        path = broker.safe_path(published, row["path"])
        target = broker.safe_path(work, row["path"])
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, target)
        files[row["path"]] = broker.digest(target)
    if not files:
        raise RuntimeError("Empty comprehension source inventory")
    lane_run.make_home(base / "home", read_only_config(work))
    prompt = ROOT / "steps/comprehension.md"
    shutil.copy2(prompt, base / "prompt.md")
    record = {**identity, "prepared_at": broker.stamp(), "prompt_sha256": broker.digest(prompt),
              "readable_source_sha256": lane_run.fingerprint(files), "files": files,
              "home_config_sha256": broker.digest(base / "home/config.toml"),
              "source_inventory_sha256": broker.digest(Path(session.data["result"]) / "source-files.json"),
              "condition": "fresh read-only reader; original comprehension prompt; whole-app source only"}
    save(dest / "prepared.json", record, session)
    print(f"Prepared {dest.relative_to(ROOT)}; save a source-derived answer key before launching the reader", flush=True)
    return record


def reader_command(work, model, reasoning, last=None):
    args = ["codex", "exec", "-C", str(work), "-m", model,
            "-c", f'model_reasoning_effort="{reasoning}"', "--skip-git-repo-check", "--json"]
    return args + (["-o", str(last)] if last else []) + ["-"]


def reader_isolation(base, session):
    probe = base / "isolation"
    own, home = probe / "own", probe / "home"
    own.mkdir(parents=True)
    (own / "source.txt").write_text("reader-source-marker")
    (probe / "secret.txt").write_text("reader-outside-marker")
    lane_run.make_home(home, read_only_config(own))
    code = f'''from pathlib import Path
for name, action in [
    ('read', lambda: Path('source.txt').read_text()),
    ('write', lambda: Path('source.txt').write_text('changed')),
    ('create', lambda: Path('new.txt').write_text('new')),
    ('chmod', lambda: Path('source.txt').chmod(0o600)),
    ('unlink', lambda: Path('source.txt').unlink()),
    ('outside', lambda: Path({str(probe / 'secret.txt')!r}).read_text())]:
    try: print(name + '=' + str(action()))
    except Exception as error: print(name + '=' + type(error).__name__)
'''
    prompt = ("Artificial isolation test: execute this command exactly once with the command tool. "
              "Do not use other tools. Report its output.\npython3 - <<'PY'\n" + code + "PY\n")
    proc = subprocess.run(reader_command(own, "gpt-6-sol", "low"), cwd=own,
                          env=lane_run.environment(home), input=prompt, text=True,
                          capture_output=True, timeout=180)
    (probe / "events.jsonl").write_text(proc.stdout)
    (probe / "stderr.log").write_text(proc.stderr)
    outputs = []
    for line in proc.stdout.splitlines():
        try:
            event = json.loads(line)
        except ValueError:
            continue
        item = event.get("item", {})
        if event.get("type") == "item.completed" and item.get("type") == "command_execution":
            outputs.append(item.get("aggregated_output", ""))
    text = "\n".join(outputs)
    checks = {name: name + "=PermissionError" in text for name in ("write", "create", "chmod", "unlink", "outside")}
    checks["read"] = "read=reader-source-marker" in text
    checks["source_unchanged"] = ((own / "source.txt").is_file() and
                                  (own / "source.txt").read_text() == "reader-source-marker")
    proof = {"passed": proc.returncode == 0 and all(checks.values()), "checks": checks,
             "home_config_sha256": broker.digest(base / "home/config.toml"), "tested_at": broker.stamp()}
    _, dest = comprehension_paths(session)
    save(dest / "isolation.json", proof, session)
    if not proof["passed"]:
        raise RuntimeError("Reader isolation failed; preserve the probe and inspect its output")
    return proof


def comprehension_run(session, answer_key):
    source_identity(session)
    base, dest = comprehension_paths(session)
    prepared = load(dest / "prepared.json")
    work, home, logs = base / "app", base / "home", base / "logs"
    if logs.exists() or (home / "sessions").exists():
        raise RuntimeError("Comprehension reader already used; preserve its evidence")
    if not answer_key.is_file() or not answer_key.read_text().strip() or answer_key.is_relative_to(work):
        raise RuntimeError("The source-derived answer key must exist outside the reader workspace")
    actual = {str(p.relative_to(work)): broker.digest(p) for p in lane_run.checked_files(work)}
    if actual != prepared["files"] or broker.digest(base / "prompt.md") != prepared["prompt_sha256"]:
        raise RuntimeError("Reader source or original prompt changed after preparation")
    if broker.digest(ROOT / "steps/comprehension.md") != prepared["prompt_sha256"]:
        raise RuntimeError("Original comprehension prompt differs from prepared copy")
    if broker.digest(home / "config.toml") != prepared["home_config_sha256"]:
        raise RuntimeError("Reader permissions changed after preparation")
    # The reviewer supplies a key derived from source before opening any reader
    # answer. It is archived and hashed before this fresh reader is launched.
    write_text(dest / "answer-key.md", answer_key.read_text(), session)
    key_sha = broker.digest(dest / "answer-key.md")
    reader_isolation(base, session)
    logs.mkdir()
    model = load(ROOT / "stacks" / session.data["stack"] / "stack.json").get(
        "agent", {"model": "gpt-6-sol", "reasoning": "xhigh"})
    start = time.monotonic()
    record = {"session": session.id, "started": broker.stamp(), "model": model["model"],
              "reasoning": model["reasoning"], "source_sha256": prepared["source_sha256"],
              "readable_source_sha256": prepared["readable_source_sha256"],
              "prompt_sha256": prepared["prompt_sha256"], "answer_key_sha256_before_reader": key_sha,
              "home_config_sha256": prepared["home_config_sha256"], "grading": "pending source-supported review"}
    save(dest / "started.json", record, session)
    with (base / "prompt.md").open() as prompt, (logs / "events.jsonl").open("w") as events, (logs / "stderr.log").open("w") as stderr:
        process = subprocess.Popen(reader_command(work, model["model"], model["reasoning"], logs / "answer.md"),
                                   cwd=work, env=lane_run.environment(home), stdin=prompt,
                                   stdout=events, stderr=stderr, start_new_session=True)
        try:
            code = process.wait(timeout=1800)
        except subprocess.TimeoutExpired:
            for sig in (signal.SIGTERM, signal.SIGKILL):
                try:
                    os.killpg(process.pid, sig)
                    process.wait(timeout=5)
                    break
                except ProcessLookupError:
                    break
                except subprocess.TimeoutExpired:
                    continue
            code = 124
    actual = {str(p.relative_to(work)): broker.digest(p) for p in lane_run.checked_files(work)}
    record.update(exit=code, finished=broker.stamp(), seconds=round(time.monotonic() - start, 1),
                  tokens=lane_run.usage(logs / "events.jsonl"), source_unchanged=actual == prepared["files"],
                  tool=broker.checked(["codex", "--version"], timeout=30))
    if not record["source_unchanged"]:
        record["exit"] = 1
    publication.scrub_events(logs / "events.jsonl", work, dest / "transcript",
                             header={"title": f"{session.id}: original comprehension questions"})
    if (logs / "answer.md").exists():
        write_text(dest / "answer.md", (logs / "answer.md").read_text(), session)
    write_text(dest / "stderr.log", (logs / "stderr.log").read_text(), session)
    save(dest / "run.json", record, session)
    print(f"{session.id}: comprehension reader exit {record['exit']}; grading remains separate", flush=True)
    return record["exit"]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("parity", "runtime", "validate", "comprehension-prepare", "comprehension-run", "_socket", "_http"))
    parser.add_argument("--session", type=Path, action="append")
    parser.add_argument("--answer-key", type=Path)
    parser.add_argument("--condition", choices=("measured", "reference"), default="measured")
    parser.add_argument("--port", type=int)
    parser.add_argument("--app")
    parser.add_argument("--image")
    parser.add_argument("--label")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.action == "_socket":
        socket_worker(args.port, args.app)
        return 0
    if args.action == "_http":
        benchmark_worker(args.image, args.label, args.output)
        return 0
    if args.action == "validate":
        validate(args.condition)
        return 0
    if args.action.startswith("comprehension-"):
        if not args.session or len(args.session) != 1:
            parser.error("Comprehension requires one --session")
        session = broker.Session(args.session[0].resolve())
        if args.action == "comprehension-prepare":
            comprehension_prepare(session)
            return 0
        if not args.answer_key:
            parser.error("Save the source-derived --answer-key before launching the reader")
        return comprehension_run(session, args.answer_key.resolve())
    if args.action == "runtime" and args.condition == "measured" and args.session:
        parser.error("Measured runtime uses the fixed four original final applications")
    if args.action == "runtime" and args.condition == "reference" and not args.session:
        parser.error("Reference runtime requires explicit --session paths")
    paths = args.session or [lane_run.session_path(*entry) for entry in ENTRIES]
    sessions = [broker.Session(path.resolve()) for path in paths]
    results = [parity(session) for session in sessions] if args.action == "parity" else [runtime(sessions, args.condition)]
    return 0 if all(result["passed"] for result in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
