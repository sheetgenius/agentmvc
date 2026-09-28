"""Run one measured IHP Conduit build in a fresh, frozen workspace.

Usage: python3 tools/ihp_candidate_agent.py RUN

RUN is a positive run number, and .work/one-shot-ihp-RUN-control/token must hold the broker token.
"""
import hashlib
import json
import os
import socket
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import ihp_candidate
import one_shot

ROOT = one_shot.ROOT
BROKER_PORT = 49674


def stamp():
    return datetime.now(timezone.utc).isoformat()


def usage(path):
    out = {"input": 0, "cached_input": 0, "output": 0, "reasoning_output": 0, "commands": 0}
    for line in path.read_text().splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if event.get("type") == "turn.completed":
            data = event.get("usage", {})
            for key, source in (("input", "input_tokens"), ("cached_input", "cached_input_tokens"),
                                ("output", "output_tokens"), ("reasoning_output", "reasoning_output_tokens")):
                out[key] += data.get(source, 0)
        if event.get("type") == "item.completed" and (event.get("item") or {}).get("type") == "command_execution":
            out["commands"] += 1
    out["uncached_plus_output"] = out["input"] - out["cached_input"] + out["output"]
    return out


def main():
    if len(sys.argv) != 2 or not ihp_candidate.is_run(sys.argv[1]):
        raise SystemExit(__doc__)
    run = sys.argv[1]
    work = ihp_candidate.workspace(run)
    home = ihp_candidate.home(run)
    log = ROOT / ".work" / f"one-shot-ihp-{run}-agent-logs" / "ihp"
    if log.exists():
        raise SystemExit(f"Measured log already exists: {log}")
    manifest = json.loads(ihp_candidate.MANIFEST.read_text())
    if ihp_candidate.snapshot() != manifest:
        raise SystemExit("IHP source differs from frozen manifest")
    one_shot.verify(work)
    record = json.loads((work / "FIXTURE.json").read_text())
    if record["fixture_sha256"] != manifest["sha256"]:
        raise SystemExit("Workspace differs from frozen source")
    if not (home / "auth.json").is_file() or not (home / "config.toml").is_file():
        raise SystemExit("Missing fresh Codex home")
    if (home / "sessions").exists():
        raise SystemExit("Codex home already has sessions")
    config = (home / "config.toml").read_text()
    if 'approval_policy = "never"' not in config or 'memories = false' not in config or \
            'default_permissions = "workspace-only"' not in config:
        raise SystemExit("Codex home lacks required isolation settings")
    token = (ROOT / ".work" / f"one-shot-ihp-{run}-control" / "token").read_text().strip()
    with socket.create_connection(("127.0.0.1", BROKER_PORT), timeout=3):
        pass
    agent = json.loads((ROOT / "stacks/ihp/stack.json").read_text())["agent"]
    env = {key: os.environ[key] for key in ("PATH", "HOME", "USER", "LOGNAME", "SHELL", "TMPDIR", "LANG")
           if key in os.environ}
    env.update(CODEX_HOME=str(home), ONE_SHOT_BROKER_TOKEN=token,
               ONE_SHOT_BROKER_PORT=str(BROKER_PORT))
    command = ["codex", "exec", "-C", str(work), "-m", agent["model"],
               "-c", f'model_reasoning_effort="{agent["reasoning"]}"',
               "--skip-git-repo-check", "--json", "-o", str(log / "last.md"), "-"]
    log.mkdir(parents=True)
    began, start = stamp(), time.monotonic()
    try:
        with (work / "PROMPT.md").open() as prompt, (log / "events.jsonl").open("w") as events, \
                (log / "stderr.log").open("w") as stderr:
            rc = subprocess.run(command, cwd=work, env=env, stdin=prompt, stdout=events,
                                stderr=stderr, timeout=7200).returncode
    except subprocess.TimeoutExpired:
        rc = 124
    data = {"stack": "ihp", "run": int(run), "started": began, "finished": stamp(),
            "seconds": round(time.monotonic() - start, 1), "exit": rc,
            "model": agent["model"], "reasoning": agent["reasoning"],
            "tool": subprocess.check_output(["codex", "--version"], text=True).strip(),
            "prompt_sha256": record["prompt_sha256"], "fixture_sha256": record["fixture_sha256"],
            "browser_image_id": record["browser_image_id"],
            "launcher_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            "tokens": usage(log / "events.jsonl")}
    (log / "run.json").write_text(json.dumps(data, indent=2) + "\n")
    print(json.dumps(data, indent=2), flush=True)


if __name__ == "__main__":
    main()
