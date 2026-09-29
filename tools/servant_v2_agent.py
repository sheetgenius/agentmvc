"""Launch the single measured Servant v2 pilot in its frozen workdir."""
import hashlib
import json
import os
import socket
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

import one_shot
import servant_v2

ROOT = one_shot.ROOT
BROKER_PORT = 49675


def stamp():
    return datetime.now(timezone.utc).isoformat()


def usage(path):
    out = {"input": 0, "cached_input": 0, "output": 0,
           "reasoning_output": 0, "commands": 0}
    for line in path.read_text().splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if event.get("type") == "turn.completed":
            data = event.get("usage", {})
            for key, source in (("input", "input_tokens"),
                                ("cached_input", "cached_input_tokens"),
                                ("output", "output_tokens"),
                                ("reasoning_output", "reasoning_output_tokens")):
                out[key] += data.get(source, 0)
        if event.get("type") == "item.completed" and (event.get("item") or {}).get("type") == "command_execution":
            out["commands"] += 1
    out["uncached_plus_output"] = out["input"] - out["cached_input"] + out["output"]
    return out


def main():
    work, home, log = servant_v2.WORK, servant_v2.HOME, servant_v2.LOG
    if log.exists():
        raise SystemExit(f"Measured log already exists: {log}")
    source = json.loads(servant_v2.MANIFEST.read_text())
    if servant_v2.snapshot() != source:
        raise SystemExit("Source differs from frozen manifest")
    one_shot.verify(work)
    record = json.loads((work / "FIXTURE.json").read_text())
    if record["fixture_sha256"] != source["sha256"]:
        raise SystemExit("Workdir fixture differs from source")
    if record["toolchain_image_id"] != servant_v2.image_id():
        raise SystemExit("Toolchain image differs from prepared fixture")
    if not (home / "auth.json").is_file() or not (home / "config.toml").is_file():
        raise SystemExit("Missing fresh Codex home")
    if (home / "sessions").exists():
        raise SystemExit("Codex home contains sessions")
    config = (home / "config.toml").read_text()
    if 'approval_policy = "never"' not in config or 'memories = false' not in config or \
            'default_permissions = "workspace-only"' not in config:
        raise SystemExit("Codex home lacks isolation settings")
    token = (servant_v2.CONTROL / "token").read_text().strip()
    with socket.create_connection(("127.0.0.1", BROKER_PORT), timeout=3):
        pass
    agent = json.loads((ROOT / "stacks/servant/stack.json").read_text())["agent"]
    env = {key: os.environ[key] for key in
           ("PATH", "HOME", "USER", "LOGNAME", "SHELL", "TMPDIR", "LANG") if key in os.environ}
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
    data = {"stack": "servant", "condition": "v2-pilot", "started": began,
            "finished": stamp(), "seconds": round(time.monotonic() - start, 1),
            "exit": rc, "model": agent["model"], "reasoning": agent["reasoning"],
            "tool": subprocess.check_output(["codex", "--version"], text=True).strip(),
            "prompt_sha256": record["prompt_sha256"],
            "fixture_sha256": record["fixture_sha256"],
            "toolchain_image_id": record["toolchain_image_id"],
            "browser_image_id": record["browser_image_id"],
            "launcher_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            "tokens": usage(log / "events.jsonl")}
    (log / "run.json").write_text(json.dumps(data, indent=2) + "\n")
    print(json.dumps(data, indent=2), flush=True)


if __name__ == "__main__":
    main()
