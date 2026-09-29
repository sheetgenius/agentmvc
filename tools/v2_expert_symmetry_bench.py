"""Repeat the same production HTTP workload for the three expert candidates.

Usage: python3 tools/v2_expert_symmetry_bench.py RAILS_IMAGE

The measured sources must already pass their independent gates. This reviewer
tool does not edit a candidate or any frozen input. It alternates stack order
between rounds to reduce time-order bias and keeps each k6 stream compressed.
"""

import argparse
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
OUT = ROOT / "results/v2-expert-symmetry/runtime"
IMAGES = {
    "typescript": "agentmvc-v2-expert-typescript:final",
    "phoenix": "agentmvc-v2-expert-phoenix:final",
}


def run(args, **kwargs):
    return subprocess.run(args, cwd=ROOT, text=True, capture_output=True,
                          check=True, **kwargs).stdout.strip()


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def one(stack, image, round_number):
    label = f"v2-symmetry-{stack}-{round_number}"
    scratch = ROOT / ".work/v2-expert-symmetry-runtime" / label
    dest = OUT / stack / f"round{round_number}"
    if dest.exists() or scratch.exists():
        raise RuntimeError(f"Existing measurement: {dest} or {scratch}")
    scratch.mkdir(parents=True)
    dest.mkdir(parents=True)
    env = {key: value for key, value in os.environ.items() if key not in
           ("BENCH_DURATION", "BENCH_WARMUP", "BENCH_SCENARIOS", "BENCH_EXTRA_ENV",
            "BENCH_HOST_PORT")}
    env["BENCH_RAW_OUTPUT"] = "1"
    command = [sys.executable, str(ROOT / "tools/bench/bench.py"), image,
               label, str(scratch)]
    proc = subprocess.run(command, cwd=ROOT, env=env, text=True,
                          capture_output=True, timeout=3600)
    (dest / "runner.log").write_text(proc.stdout + proc.stderr)
    # seed.json contains synthetic JWTs; summary exports do not need it.
    for pattern in ("k6-*.json",):
        for path in scratch.glob(pattern):
            shutil.copy2(path, dest / path.name)
    streams = {}
    for path in scratch.glob("raw-*.json"):
        compressed = dest / (path.name + ".zst")
        run(["zstd", "-q", "-T2", "-o", str(compressed), str(path)])
        run(["zstd", "-q", "-t", str(compressed)])
        streams[compressed.name] = digest(compressed)
    if not (scratch / "results.json").exists():
        raise RuntimeError(f"No benchmark result: {dest / 'runner.log'}")
    data = json.loads((scratch / "results.json").read_text())
    data.pop("app_log_tail", None)
    data.update(exit=proc.returncode, stack=stack, round=round_number,
                image_sha256=run(["docker", "image", "inspect", "--format",
                                  "{{.Id}}", image]), raw_stream_sha256=streams)
    (dest / "results.json").write_text(json.dumps(data, indent=2) + "\n")
    if proc.returncode or any(row.get("failed_checks") for row in
                              data.get("scenarios", {}).values()):
        raise RuntimeError(f"Benchmark failed: {dest / 'results.json'}")
    expected = 9
    if len(streams) != expected * 2:
        raise RuntimeError(f"Expected {expected * 2} warmup/measurement streams, got {len(streams)}")
    shutil.rmtree(scratch)
    return data


def completed(stack, round_number, image_id):
    dest = OUT / stack / f"round{round_number}"
    path = dest / "results.json"
    if not path.exists():
        return None
    data = json.loads(path.read_text())
    if (data.get("image_sha256") != image_id or data.get("exit") != 0
            or len(data.get("scenarios", {})) != 9
            or len(data.get("raw_stream_sha256", {})) != 18):
        raise RuntimeError(f"Incomplete or mismatched existing round: {path}")
    for name, expected in data["raw_stream_sha256"].items():
        path = dest / name
        if not path.is_file() or digest(path) != expected:
            raise RuntimeError(f"Raw stream changed: {path}")
    return data


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("rails_image")
    args = parser.parse_args()
    images = {"rails": args.rails_image, **IMAGES}
    image_ids = {stack: run(["docker", "image", "inspect", "--format",
                            "{{.Id}}", image]) for stack, image in images.items()}
    k6_image_id = run(["docker", "image", "inspect", "--format", "{{.Id}}",
                       "grafana/k6:latest"])
    postgres_image_id = run(["docker", "image", "inspect", "--format", "{{.Id}}",
                             "postgres:17-alpine"])
    OUT.mkdir(parents=True, exist_ok=True)
    started = datetime.now(timezone.utc).isoformat()
    records = []
    for round_number, order in ((1, ("rails", "typescript", "phoenix")),
                                (2, ("phoenix", "typescript", "rails"))):
        for stack in order:
            previous = completed(stack, round_number, image_ids[stack])
            print(f"{stack} round {round_number}: " +
                  ("verified previous result" if previous else "starting"), flush=True)
            records.append(previous or one(stack, images[stack], round_number))
    (OUT / "summary.json").write_text(json.dumps({
        "condition": "v2-expert-same-session-http",
        "started": started,
        "finished": datetime.now(timezone.utc).isoformat(),
        "images": images,
        "image_sha256": image_ids,
        "load_generator_image_sha256": k6_image_id,
        "database_image_sha256": postgres_image_id,
        "limits": {"app": "2 CPU, 1 GiB", "database": "2 CPU, 1 GiB"},
        "vus": 16, "warmup": "3s", "duration": "15s", "rounds": 2,
        "order": ["rails", "typescript", "phoenix", "phoenix", "typescript", "rails"],
        "benchmark_sha256": digest(ROOT / "tools/bench/bench.py"),
        "load_sha256": digest(ROOT / "tools/bench/load.js"),
        "records": [{"stack": row["stack"], "round": row["round"],
                     "image_sha256": row["image_sha256"]} for row in records],
    }, indent=2) + "\n")
    print(f"Complete: {OUT / 'summary.json'}", flush=True)


if __name__ == "__main__":
    main()
