"""Fourth, guided IHP build without changing the three-run frozen fixture.

Commands: freeze, prepare, broker, agent, publish, development, production, runtime.
The scored fourth run is `.work/one-shot-ihp-4/ihp`; published evidence is
`results/one-shot-ihp/guided/`.
"""
import hashlib
import json
import os
import re
import secrets
import shutil
import socket
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import ihp_candidate as candidate
import ihp_candidate_agent as agent_tools
import ihp_candidate_broker as bridge
import ihp_candidate_independent as independent
import ihp_candidate_publish as publish_tools
import ihp_candidate_runtime as runtime_tools
import measure
import one_shot
import one_shot_live_bench as live
import one_shot_publish
import scrub

ROOT = one_shot.ROOT
RUN = "4"
WORK = ROOT / ".work/one-shot-ihp-4/ihp"
HOME = ROOT / ".work/one-shot-ihp-4-homes/ihp"
LOG = ROOT / ".work/one-shot-ihp-4-agent-logs/ihp"
CONTROL = ROOT / ".work/one-shot-ihp-4-control/token"
RESULT = ROOT / "results/one-shot-ihp/guided"
BRIEF = ROOT / "stacks/ihp/briefs/expert.md"
MANIFEST = RESULT / "fixture-manifest.json"
ADAPTER = ROOT / "tools/ihp_guided_host/check-production.sh"
VOLUME = "agentmvc-ihp-nix-run4"
PORT = 49674


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def prompt_bytes():
    return (ROOT / "one-shot/PROMPT.md").read_bytes() + b"\n\n---\n\n" + BRIEF.read_bytes()


def snapshot():
    base = json.loads(candidate.MANIFEST.read_text())
    if candidate.snapshot() != base:
        raise SystemExit("Original three-run IHP fixture changed")
    record = {
        "track": "guided fourth IHP build",
        "base_fixture_sha256": base["sha256"],
        "shared_prompt_sha256": digest(ROOT / "one-shot/PROMPT.md"),
        "expert_brief_sha256": digest(BRIEF),
        "prompt_sha256": hashlib.sha256(prompt_bytes()).hexdigest(),
        "guided_launcher_sha256": digest(__file__),
        "guided_production_adapter_sha256": digest(ADAPTER),
        "browser_image_id": one_shot.image_id(),
        "nix_volume": VOLUME,
    }
    record["sha256"] = hashlib.sha256(json.dumps(record, sort_keys=True,
                                  separators=(",", ":")).encode()).hexdigest()
    return record


def verify_source():
    current = snapshot()
    if not MANIFEST.exists() or json.loads(MANIFEST.read_text()) != current:
        raise SystemExit("Guided fixture differs from frozen manifest")
    return current


def verify_work():
    fixture = verify_source()
    one_shot.verify(WORK)
    record = json.loads((WORK / "FIXTURE.json").read_text())
    if record["fixture_sha256"] != fixture["sha256"] or \
            record["prompt_sha256"] != fixture["prompt_sha256"]:
        raise SystemExit("Guided workdir has the wrong fixture or prompt")
    return fixture


def prepare():
    frozen = verify_source()
    if WORK.exists() or HOME.exists() or LOG.exists():
        raise SystemExit("Guided workspace, home, or log already exists")
    base = json.loads(one_shot.MANIFEST.read_text())
    shutil.copytree(candidate.SCAFFOLD, WORK)
    shutil.copytree(candidate.SCAFFOLD, WORK / ".scaffold")
    files = {}
    candidate.copy_shared(WORK, base, files)
    (WORK / "PROMPT.md").write_bytes(prompt_bytes())
    files["PROMPT.md"] = digest(WORK / "PROMPT.md")
    for source, dest in ((candidate.SOURCE / "ENVIRONMENT.md", WORK / "ENVIRONMENT.md"),
                         (candidate.SOURCE / "ihp.sh", WORK / "harness/ihp.sh")):
        shutil.copy2(source, dest)
        files[str(dest.relative_to(WORK))] = digest(dest)
    (WORK / "harness/browser-image-id").write_text(frozen["browser_image_id"] + "\n")
    files["harness/browser-image-id"] = digest(WORK / "harness/browser-image-id")
    for path in (WORK / ".scaffold").rglob("*"):
        if path.is_file():
            files[str(path.relative_to(WORK))] = digest(path)
    record = {"stack": "ihp", "run": 4, "track": "guided",
              "fixture_sha256": frozen["sha256"],
              "base_fixture_sha256": frozen["base_fixture_sha256"],
              "prompt_sha256": frozen["prompt_sha256"],
              "browser_image_id": frozen["browser_image_id"],
              "files": dict(sorted(files.items()))}
    (WORK / "FIXTURE.json").write_text(json.dumps(record, indent=2) + "\n")
    for name in ("realworld_spec", "security", "harness", ".scaffold"):
        one_shot.readonly(WORK / name)
    for name in ("PROMPT.md", "MEASUREMENT.md", "ENVIRONMENT.md", "EXPERIMENT.md", "FIXTURE.json"):
        path = WORK / name
        path.chmod(path.stat().st_mode & ~0o222)
    previous = candidate.home
    try:
        candidate.home = lambda run: HOME if run == RUN else previous(run)
        candidate.make_home(RUN)
    finally:
        candidate.home = previous
    CONTROL.parent.mkdir(parents=True, exist_ok=True)
    CONTROL.write_text(secrets.token_hex(32))
    CONTROL.chmod(0o600)
    verify_work()
    print(f"ready: {WORK} ({frozen['sha256']})")


def patched_bridge():
    old_workspace, old_volume = candidate.workspace, bridge.volume_for
    candidate.workspace = lambda run: WORK if str(run) == RUN else old_workspace(run)
    bridge.volume_for = lambda work: VOLUME if Path(work).resolve() == WORK.resolve() else old_volume(work)
    return old_workspace, old_volume


def broker():
    verify_work()
    if not CONTROL.exists():
        raise SystemExit("Missing guided broker token")
    patched_bridge()
    original_dispatch = bridge.dispatch

    def guided_dispatch(run_number, action, port, argv):
        if action != "production":
            return original_dispatch(run_number, action, port, argv)
        if run_number != RUN or port != 4104 or argv:
            return 2, "Wrong guided production request.\n"
        bridge.verify(WORK)
        code, output = bridge.run([str(ADAPTER), str(port)],
                                  env={**os.environ, "ONE_SHOT_WORKDIR": str(WORK)})
        bridge.verify(WORK)
        return code, output

    bridge.dispatch = guided_dispatch
    server = bridge.Server(("127.0.0.1", PORT), CONTROL.read_text().strip(), RUN,
                           ROOT / ".work/one-shot-ihp-4-broker")
    print(f"Guided IHP broker listening on 127.0.0.1:{PORT}", flush=True)
    server.serve_forever()


def agent():
    frozen = verify_work()
    if LOG.exists() or (HOME / "sessions").exists():
        raise SystemExit("Measured guided log or Codex session already exists")
    config = (HOME / "config.toml").read_text()
    for required in ('approval_policy = "never"', 'memories = false',
                     'default_permissions = "workspace-only"'):
        if required not in config:
            raise SystemExit(f"Missing Codex isolation setting: {required}")
    if not (HOME / "auth.json").is_file():
        raise SystemExit("Missing fresh guided Codex auth")
    with socket.create_connection(("127.0.0.1", PORT), timeout=3):
        pass
    stack = json.loads((ROOT / "stacks/ihp/stack.json").read_text())["agent"]
    env = {key: os.environ[key] for key in ("PATH", "HOME", "USER", "LOGNAME", "SHELL", "TMPDIR", "LANG")
           if key in os.environ}
    env.update(CODEX_HOME=str(HOME), ONE_SHOT_BROKER_TOKEN=CONTROL.read_text().strip(),
               ONE_SHOT_BROKER_PORT=str(PORT))
    command = ["codex", "exec", "-C", str(WORK), "-m", stack["model"],
               "-c", f'model_reasoning_effort="{stack["reasoning"]}"',
               "--skip-git-repo-check", "--json", "-o", str(LOG / "last.md"), "-"]
    LOG.mkdir(parents=True)
    began, tick = datetime.now(timezone.utc).isoformat(), time.monotonic()
    try:
        with (WORK / "PROMPT.md").open() as prompt, (LOG / "events.jsonl").open("w") as events, \
                (LOG / "stderr.log").open("w") as stderr:
            rc = subprocess.run(command, cwd=WORK, env=env, stdin=prompt, stdout=events,
                                stderr=stderr, timeout=7200).returncode
    except subprocess.TimeoutExpired:
        rc = 124
    data = {"stack": "ihp", "run": 4, "track": "guided", "started": began,
            "finished": datetime.now(timezone.utc).isoformat(),
            "seconds": round(time.monotonic() - tick, 1), "exit": rc,
            "model": stack["model"], "reasoning": stack["reasoning"],
            "tool": subprocess.check_output(["codex", "--version"], text=True).strip(),
            "prompt_sha256": frozen["prompt_sha256"],
            "fixture_sha256": frozen["sha256"],
            "base_fixture_sha256": frozen["base_fixture_sha256"],
            "browser_image_id": frozen["browser_image_id"],
            "launcher_sha256": digest(__file__),
            "tokens": agent_tools.usage(LOG / "events.jsonl")}
    (LOG / "run.json").write_text(json.dumps(data, indent=2) + "\n")
    print(json.dumps(data, indent=2), flush=True)


def publish():
    verify_work()
    if not (LOG / "run.json").exists():
        raise SystemExit("Guided agent has not finished")
    RESULT.mkdir(parents=True, exist_ok=True)
    prompt = RESULT / "frozen-prompt.md"
    if prompt.exists() and prompt.read_bytes() != prompt_bytes():
        raise SystemExit("Published guided prompt changed")
    prompt.write_bytes(prompt_bytes())
    token = CONTROL.read_text().strip()
    scrub.scrub_file(LOG / "events.jsonl", WORK, RESULT / "transcript",
                     deny=[re.escape(token)],
                     header={"title": "IHP guided agent, fourth build",
                             "Prompt": "[guided frozen prompt](frozen-prompt.md)"})
    cleaner = scrub.Scrubber(WORK, [re.escape(token)])
    if (LOG / "last.md").exists():
        report = cleaner.text((LOG / "last.md").read_text())
        if cleaner.leaks(report):
            raise SystemExit("Guided report contains private paths")
        (RESULT / "agent-report.md").write_text(report)
    (RESULT / "run.json").write_bytes((LOG / "run.json").read_bytes())
    rules = measure.load_stack("ihp")
    rules["code"].setdefault("skip_dirs", []).extend(("build", "security", "harness", ".devenv", ".cache", ".tmp", "Test", ".github"))
    rules["code"].setdefault("skip_paths", []).append("Config/nix")
    rules["code"].setdefault("skip_files", []).extend((".stylish-haskell.yaml", "Setup.hs", "Makefile"))
    size = measure.measure(rules, WORK, WORK / ".scaffold")
    inventory = one_shot_publish.source_inventory(rules, WORK)
    for total, item in (("tokens", "whole_tokens"), ("lines", "whole_lines"),
                        ("owned_tokens", "owned_tokens"), ("owned_lines", "owned_lines")):
        if sum(row[item] for row in inventory) != size[total]:
            raise SystemExit(f"Source inventory mismatch: {total}")
    size.update(encoding="o200k_base", baseline="untouched IHP scaffold in .scaffold/",
                rule="same IHP measurement exclusions as runs 1–3",
                review_exclusions={"skip_dirs": rules["code"]["skip_dirs"],
                                   "skip_paths": rules["code"]["skip_paths"],
                                   "skip_files": rules["code"]["skip_files"]})
    for name, value in (("size.json", size), ("source-files.json", inventory),
                        ("docs.json", publish_tools.docs(WORK))):
        (RESULT / name).write_text(json.dumps(value, indent=2) + "\n")
    actions = {}
    requests = ROOT / ".work/one-shot-ihp-4-broker/requests.jsonl"
    if requests.exists():
        for line in requests.read_text().splitlines():
            row = json.loads(line)
            bucket = actions.setdefault(row["action"], {"attempts": 0, "failures": 0})
            bucket["attempts"] += 1
            bucket["failures"] += int(row["exit"] != 0)
    (RESULT / "check-attempts.json").write_text(json.dumps(actions, indent=2) + "\n")
    print(json.dumps({"run": 4, "track": "guided", "size": size, "checks": actions}, indent=2))


def gate(name):
    frozen = verify_work()
    patched_bridge()
    started, tick, output = datetime.now(timezone.utc).isoformat(), time.monotonic(), []
    try:
        if name == "development":
            code = independent.development(4, WORK, output)
        else:
            independent.command(["docker", "container", "rm", "-f", "agentmvc-one-shot-ihp-4-dev"], timeout=30)
            code, log = independent.command([str(ADAPTER), "4104"],
                                             env={**os.environ, "ONE_SHOT_WORKDIR": str(WORK)},
                                             timeout=3600)
            output.append(log)
        one_shot.verify(WORK)
    except Exception as error:
        code = 1
        output.append(f"Independent gate error: {error}\n")
    raw = ROOT / ".work/one-shot-ihp-4-independent"
    raw.mkdir(parents=True, exist_ok=True)
    RESULT.mkdir(parents=True, exist_ok=True)
    if (RESULT / f"{name}.json").exists():
        attempt = 1
        while (RESULT / f"{name}-attempt{attempt}.json").exists():
            attempt += 1
        for folder, suffixes in ((RESULT, ("json", "log")), (raw, ("log",))):
            for suffix in suffixes:
                old = folder / f"{name}.{suffix}"
                if old.exists():
                    old.rename(folder / f"{name}-attempt{attempt}.{suffix}")
    full = "\n".join(output)
    (raw / f"{name}.log").write_text(full)
    cleaner = scrub.Scrubber(WORK, [CONTROL.read_text().strip()])
    cleaned = cleaner.text(full)
    if cleaner.leaks(cleaned):
        raise SystemExit("Guided independent log contains private paths")
    (RESULT / f"{name}.log").write_text(cleaned)
    record = {"stack": "ihp", "run": 4, "track": "guided", "gate": name,
              "port": 4204 if name == "development" else 4104,
              "started": started, "finished": datetime.now(timezone.utc).isoformat(),
              "seconds": round(time.monotonic() - tick, 1), "exit": code,
              "fixture_sha256": frozen["sha256"]}
    (RESULT / f"{name}.json").write_text(json.dumps(record, indent=2) + "\n")
    print(json.dumps(record, indent=2), flush=True)
    raise SystemExit(code)


def runtime():
    frozen = verify_work()
    patched_bridge()
    for gate_name in ("development", "production"):
        if json.loads((RESULT / f"{gate_name}.json").read_text())["exit"]:
            raise SystemExit(f"{gate_name} failed; no comparable runtime")
    image = "agentmvc-one-shot-ihp-4-ihp:final"
    image_id = runtime_tools.build_image(WORK, image)
    one_shot.RUN_NAME = "one-shot-ihp-4"
    live.OUT = RESULT / "runtime/live"
    output, records = RESULT / "runtime", []
    for round_number in (1, 2):
        if round_number == 1:
            http = runtime_tools.http_round(4, round_number, image, output)
            live.one("ihp", round_number, (10, 100, 500), 20)
        else:
            live.one("ihp", round_number, (10, 100, 500), 20)
            http = runtime_tools.http_round(4, round_number, image, output)
        sock = json.loads((live.OUT / f"ihp-round{round_number}.json").read_text())
        if http.get("exit") != 0 or any(s.get("failed_checks", 0) for s in http.get("scenarios", {}).values()):
            raise RuntimeError(f"HTTP check failure in round {round_number}")
        if sock.get("status") != "complete" or any(s[key] for s in sock["scenarios"] for key in
                                                    ("missing", "duplicate_revisions", "regressed_revisions")):
            raise RuntimeError(f"WebSocket delivery failure in round {round_number}")
        archives = list((output / "http" / f"round{round_number}").glob("raw-*.json.zst"))
        if len(archives) != 18:
            raise RuntimeError(f"Expected 18 raw HTTP streams, found {len(archives)}")
        records.append({"round": round_number, "image_sha256": sock["image_sha256"],
                        "http": http, "live": sock, "raw_http_streams": len(archives)})
    if {r["image_sha256"] for r in records} != {image_id}:
        raise RuntimeError("Runtime image changed between rounds")
    summary = {"stack": "ihp", "run": 4, "track": "guided", "image_sha256": image_id,
               "prompt_sha256": frozen["prompt_sha256"],
               "http_vus": 16, "http_warmup": "3s", "http_duration": "15s",
               "limits": {"app": "2 CPU, 1 GiB", "database": "2 CPU, 1 GiB"},
               "raw_http_streams_verified": 36, "records": records}
    (output / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print("Guided IHP run: two rounds, 36 compressed raw HTTP streams verified", flush=True)


def main():
    if len(sys.argv) != 2:
        raise SystemExit(__doc__)
    action = sys.argv[1]
    if action == "freeze":
        if MANIFEST.exists():
            raise SystemExit("Guided manifest already exists")
        MANIFEST.parent.mkdir(parents=True, exist_ok=True)
        MANIFEST.write_text(json.dumps(snapshot(), indent=2) + "\n")
        print(json.loads(MANIFEST.read_text())["sha256"])
    elif action == "verify-source": print(verify_source()["sha256"])
    elif action == "verify": print(verify_work()["sha256"])
    elif action == "prepare": prepare()
    elif action == "broker": broker()
    elif action == "agent": agent()
    elif action == "publish": publish()
    elif action in ("development", "production"): gate(action)
    elif action == "runtime": runtime()
    else: raise SystemExit(__doc__)


if __name__ == "__main__":
    main()
