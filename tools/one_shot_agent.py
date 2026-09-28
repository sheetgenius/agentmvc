"""Launch exactly one measured Codex coding session in a prepared one-shot workdir.

Usage: python3 tools/one_shot_agent.py rails|phoenix|loco
"""
import hashlib
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import one_shot

ROOT = one_shot.ROOT
LOGS = one_shot.LOGS


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
    if len(sys.argv) != 2 or sys.argv[1] not in one_shot.STACKS:
        raise SystemExit(__doc__)
    stack = sys.argv[1]
    work = one_shot.WORK / stack
    home = one_shot.HOMES / stack
    log = LOGS / stack
    if log.exists():
        raise SystemExit(f"Measured session already exists: {log}")
    manifest = json.loads(one_shot.MANIFEST.read_text())
    if one_shot.snapshot() != manifest:
        raise SystemExit("Source fixture differs from frozen manifest")
    one_shot.verify(work)
    record = json.loads((work / "FIXTURE.json").read_text())
    if record["fixture_sha256"] != manifest["sha256"]:
        raise SystemExit("Workdir fixture differs from source fixture")
    if not (home / "auth.json").is_file() or not (home / "config.toml").is_file():
        raise SystemExit("Missing fresh Codex home")
    if (home / "sessions").exists():
        raise SystemExit("Codex home already contains sessions")
    config = (home / "config.toml").read_text()
    if 'approval_policy = "never"' not in config or 'memories = false' not in config or \
            'default_permissions = "workspace-only"' not in config:
        raise SystemExit("Codex home lacks required isolation settings")
    token = json.loads((one_shot.CONTROL / "tokens.json").read_text())[stack]
    agent = json.loads((ROOT / "stacks" / stack / "stack.json").read_text())["agent"]
    env = {key: os.environ[key] for key in ("PATH", "HOME", "USER", "LOGNAME", "SHELL", "TMPDIR", "LANG")
           if key in os.environ}
    env.update(CODEX_HOME=str(home), ONE_SHOT_BROKER_TOKEN=token,
               ONE_SHOT_BROKER_PORT=os.environ.get("ONE_SHOT_BROKER_PORT", "49671"),
               CARGO_HOME=str(work / ".cargo"), RUSTUP_HOME=str(Path.home() / ".rustup"),
               CARGO_TARGET_DIR=str(work / "conduit/target"),
               npm_config_cache=str(work / ".npm-cache"))
    command = ["codex", "exec", "-C", str(work), "-m", agent["model"],
               "-c", f'model_reasoning_effort="{agent["reasoning"]}"',
               "--skip-git-repo-check", "--json", "-o", str(log / "last.md"), "-"]
    log.mkdir(parents=True)
    began = stamp()
    started = time.monotonic()
    exit_code = None
    try:
        with (work / "PROMPT.md").open() as prompt, (log / "events.jsonl").open("w") as events, \
                (log / "stderr.log").open("w") as stderr:
            exit_code = subprocess.run(command, cwd=work, env=env, stdin=prompt, stdout=events,
                                       stderr=stderr, timeout=7200).returncode
    except subprocess.TimeoutExpired:
        exit_code = 124
    finished = stamp()
    data = {"stack": stack, "started": began, "finished": finished,
            "seconds": round(time.monotonic() - started, 1), "exit": exit_code,
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
