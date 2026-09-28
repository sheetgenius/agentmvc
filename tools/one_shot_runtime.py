"""Two nearby, reversed-order HTTP and direct WebSocket rounds for one-shot images."""
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import one_shot
import one_shot_live_bench as live

ROOT = one_shot.ROOT
OUT = one_shot.RESULTS / "runtime"
SCRATCH = one_shot.RUNTIME


def command(*args, **kwargs):
    result = subprocess.run(args, capture_output=True, text=True, **kwargs)
    if result.returncode:
        raise RuntimeError(f"{' '.join(map(str, args))}: {result.returncode}\n{result.stdout[-4000:]}\n{result.stderr[-4000:]}")
    return result.stdout


def http_round(stack, round_number):
    label = f"{one_shot.RUN_NAME}-{stack}-round{round_number}"
    scratch = SCRATCH / label
    output = OUT / "http" / f"{stack}-round{round_number}"
    completed = output / "results.json"
    if completed.exists():
        prior = json.loads(completed.read_text())
        if prior.get("exit") == 0 and len(prior.get("scenarios", {})) == 9 and \
                all(row.get("failed_checks") == 0 for row in prior["scenarios"].values()):
            print(f"HTTP {label} already complete; reusing its raw round", flush=True)
            return
        raise RuntimeError(f"Incomplete prior HTTP round: {output}")
    scratch.mkdir(parents=True, exist_ok=False)
    env = {**os.environ, "BENCH_RAW_OUTPUT": "1"}
    output.mkdir(parents=True, exist_ok=False)
    result = subprocess.run([sys.executable, str(ROOT / "tools/bench/bench.py"),
                             f"agentmvc-{one_shot.RUN_NAME}-{stack}:final", label, str(scratch)],
                            env=env, capture_output=True, text=True)
    (output / "runner.log").write_text(result.stdout + result.stderr)
    for path in scratch.iterdir():
        if path.name.startswith(("k6-", "raw-")) and path.suffix == ".json":
            shutil.copy2(path, output / path.name)
    if (scratch / "results.json").exists():
        data = json.loads((scratch / "results.json").read_text())
        data.pop("app_log_tail", None)
        data["exit"] = result.returncode
        (output / "results.json").write_text(json.dumps(data, indent=2) + "\n")
        failures = {scenario: row["failed_checks"] for scenario, row in data.get("scenarios", {}).items()
                    if row.get("failed_checks", 0)}
        if failures:
            raise RuntimeError(f"{label}: k6 checks failed: {failures}")
    if result.returncode:
        raise RuntimeError(f"{label}: HTTP runner exited {result.returncode}; see {output / 'runner.log'}")
    print(f"HTTP {label} complete", flush=True)


def main():
    if len(sys.argv) != 1:
        raise SystemExit("usage: python3 tools/one_shot_runtime.py")
    command(sys.executable, str(ROOT / "tools/one_shot.py"), "verify-source")
    for stack in one_shot.STACKS:
        work = one_shot.WORK / stack
        command(sys.executable, str(ROOT / "tools/one_shot.py"), "verify", str(work))
        command("docker", "build", "-q", "-t", f"agentmvc-{one_shot.RUN_NAME}-{stack}:final", str(work))
    for round_number in (1, 2):
        order = one_shot.STACKS if round_number == 1 else tuple(reversed(one_shot.STACKS))
        for stack in order:
            http_round(stack, round_number)
            live.one(stack, round_number, (10, 100, 500), 20)


if __name__ == "__main__":
    main()
