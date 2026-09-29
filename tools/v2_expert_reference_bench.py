"""Short paired HTTP diagnostic for the validated, unscored v2 references.

The scored one-shot runtime results live under runtime/. This tool uses the
same production benchmark and seed, but only two read scenarios at 10 seconds
each. It is intentionally labeled as a reference diagnostic.
"""

import hashlib
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import one_shot

ROOT = one_shot.ROOT
OUT = ROOT / "results/v2-expert-symmetry/reference-runtime"
IMAGES = {
    "rails": "agentmvc-v2-expert-rails-reference-1:review",
    "typescript": "agentmvc-v2-expert-typescript:reference-1",
    "phoenix": "agentmvc-v2-expert-phoenix-reference-2:review",
}
ORDER = ((1, ("rails", "typescript", "phoenix")),
         (2, ("phoenix", "typescript", "rails")))


def command(args, **kwargs):
    return subprocess.run(args, cwd=ROOT, check=True, capture_output=True,
                          text=True, **kwargs).stdout.strip()


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def one(stack, image, round_number):
    label = f"v2-reference-{stack}-{round_number}"
    scratch = ROOT / ".work/v2-expert-reference-runtime" / label
    dest = OUT / stack / f"round{round_number}"
    if scratch.exists() or dest.exists():
        raise RuntimeError(f"Existing measurement: {scratch} or {dest}")
    scratch.mkdir(parents=True)
    dest.mkdir(parents=True)
    env = {key: value for key, value in os.environ.items() if not key.startswith("BENCH_")}
    env.update(BENCH_SCENARIOS="list_anonymous,article", BENCH_WARMUP="2s",
               BENCH_DURATION="10s", BENCH_RAW_OUTPUT="1")
    proc = subprocess.run([sys.executable, str(ROOT / "tools/bench/bench.py"),
                           image, label, str(scratch)], cwd=ROOT, env=env,
                          text=True, capture_output=True, timeout=1800)
    (dest / "runner.log").write_text(proc.stdout + proc.stderr)
    for path in scratch.glob("k6-*.json"):
        shutil.copy2(path, dest / path.name)
    streams = {}
    for path in scratch.glob("raw-*.json"):
        packed = dest / (path.name + ".zst")
        command(["zstd", "-q", "-T2", "-o", str(packed), str(path)])
        command(["zstd", "-q", "-t", str(packed)])
        streams[packed.name] = digest(packed)
    if not (scratch / "results.json").exists():
        raise RuntimeError(f"No result; see {dest / 'runner.log'}")
    data = json.loads((scratch / "results.json").read_text())
    data.pop("app_log_tail", None)
    data.update(stack=stack, round=round_number, exit=proc.returncode,
                image_sha256=command(["docker", "image", "inspect", "--format",
                                      "{{.Id}}", image]), raw_stream_sha256=streams)
    (dest / "results.json").write_text(json.dumps(data, indent=2) + "\n")
    if proc.returncode or len(data.get("scenarios", {})) != 2 or len(streams) != 4 or any(
        row.get("failed_checks") for row in data.get("scenarios", {}).values()
    ):
        raise RuntimeError(f"Failed diagnostic: {dest / 'results.json'}")
    shutil.rmtree(scratch)
    return data


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    images = {stack: command(["docker", "image", "inspect", "--format",
                              "{{.Id}}", tag]) for stack, tag in IMAGES.items()}
    started = datetime.now(timezone.utc).isoformat()
    records = []
    for round_number, order in ORDER:
        for stack in order:
            print(f"{stack} reference round {round_number}: starting", flush=True)
            records.append(one(stack, IMAGES[stack], round_number))
    (OUT / "summary.json").write_text(json.dumps({
        "condition": "v2-expert-reference-short-paired-http-diagnostic",
        "scored": False,
        "started": started,
        "finished": datetime.now(timezone.utc).isoformat(),
        "images": IMAGES,
        "image_sha256": images,
        "benchmark_sha256": digest(ROOT / "tools/bench/bench.py"),
        "load_sha256": digest(ROOT / "tools/bench/load.js"),
        "scenarios": ["list_anonymous", "article"],
        "order": [stack for _, order in ORDER for stack in order],
        "vus": 16, "warmup": "2s", "duration": "10s", "rounds": 2,
        "limits": {"app": "2 CPU, 1 GiB", "database": "2 CPU, 1 GiB"},
        "records": [{"stack": r["stack"], "round": r["round"],
                     "image_sha256": r["image_sha256"]} for r in records],
    }, indent=2) + "\n")
    print(f"Complete: {OUT / 'summary.json'}", flush=True)


if __name__ == "__main__":
    main()
