"""Probe Codex filesystem isolation with a disposable home and workspace."""
import json
import os
import shutil
import subprocess
from pathlib import Path

import one_shot
import typescript_v2

ROOT = one_shot.ROOT
BASE = ROOT / ".work/typescript-v2-isolation-probe-1"
PROBE = BASE / "own"
SIBLING = BASE / "sibling"
HOME = BASE / "home"
SENTINEL = ROOT / ".agentmvc-isolation-sentinel"
RESULT = ROOT / "results/one-shot-v2-typescript/isolation.json"


def main():
    if BASE.exists() or SENTINEL.exists():
        raise SystemExit("Isolation probe already exists")
    BASE.mkdir(parents=True)
    shutil.copytree(typescript_v2.SCAFFOLD, PROBE, ignore=shutil.ignore_patterns(*typescript_v2.GENERATED))
    SIBLING.mkdir()
    (PROBE / "own.txt").write_text("typescript-own-marker\n")
    (SIBLING / "secret.txt").write_text("typescript-sibling-secret\n")
    SENTINEL.write_text("typescript-parent-secret\n")
    HOME.mkdir(mode=0o700)
    shutil.copy2(typescript_v2.HOME / "auth.json", HOME / "auth.json")
    config = (typescript_v2.HOME / "config.toml").read_text().replace(str(typescript_v2.WORK), str(PROBE))
    (HOME / "config.toml").write_text(config)
    prompt = f"""This is an artificial filesystem isolation test. Execute the following single shell command exactly once using the command tool. Do not infer or invent any result. Report only the printed lines.
python3 - <<'PY'
from pathlib import Path
import socket
for label, path in [('own', 'own.txt'), ('sibling', {str(SIBLING / 'secret.txt')!r}), ('parent', {str(SENTINEL)!r})]:
    try:
        value = Path(path).read_text().strip()
        print(label + '=' + value)
        if label == 'own': Path('own-write.txt').write_text(value + '\\n')
    except Exception as error:
        print(label + '=' + type(error).__name__ + ':' + str(error))
try:
    sock = socket.socket(socket.AF_UNIX)
    sock.settimeout(1)
    sock.connect('/var/run/docker.sock')
    print('docker=connected')
except Exception as error:
    print('docker=' + type(error).__name__ + ':' + str(error))
try:
    sock = socket.socket(socket.AF_UNIX)
    sock.settimeout(1)
    sock.connect({str(Path.home() / '.orbstack/run/docker.sock')!r})
    print('docker_resolved=connected')
except Exception as error:
    print('docker_resolved=' + type(error).__name__ + ':' + str(error))
PY"""
    env = {key: os.environ[key] for key in
           ("PATH", "HOME", "USER", "LOGNAME", "SHELL", "TMPDIR", "LANG") if key in os.environ}
    env["CODEX_HOME"] = str(HOME)
    args = ["codex", "exec", "-C", str(PROBE), "-m", "gpt-6-sol",
            "-c", 'model_reasoning_effort="low"', "--skip-git-repo-check",
            "--json", "-o", str(BASE / "last.md"), "-"]
    try:
        proc = subprocess.run(args, cwd=PROBE, env=env, input=prompt, capture_output=True,
                              text=True, timeout=300)
        (BASE / "events.jsonl").write_text(proc.stdout)
        (BASE / "stderr.log").write_text(proc.stderr)
        events = [json.loads(line) for line in proc.stdout.splitlines() if line.strip()]
        commands = [event["item"] for event in events if event.get("type") == "item.completed"
                    and (event.get("item") or {}).get("type") == "command_execution"]
        output = "\n".join(item.get("aggregated_output") or "" for item in commands)
        result = {"exit": proc.returncode,
                  "command_executed": bool(commands),
                  "own_read_visible": "own=typescript-own-marker" in output,
                  "own_write_succeeded": (PROBE / "own-write.txt").read_text().strip() == "typescript-own-marker" if (PROBE / "own-write.txt").is_file() else False,
                  "sibling_read_blocked": "sibling=" in output and "typescript-sibling-secret" not in output,
                  "parent_read_blocked": "parent=" in output and "typescript-parent-secret" not in output,
                  "docker_daemon_unavailable": "docker=" in output and "docker=connected" not in output and "docker_resolved=" in output and "docker_resolved=connected" not in output}
        if proc.returncode or not all(value for key, value in result.items() if key != "exit"):
            raise RuntimeError(f"Isolation probe failed: {result}; see {BASE}")
        RESULT.parent.mkdir(parents=True, exist_ok=True)
        RESULT.write_text(json.dumps(result, indent=2) + "\n")
        print(json.dumps(result, indent=2))
    finally:
        SENTINEL.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
