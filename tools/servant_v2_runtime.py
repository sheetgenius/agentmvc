"""Two repeated HTTP and WebSocket production rounds for the gated Servant pilot."""
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import one_shot
import one_shot_live_bench as live
import servant_v2

ROOT = one_shot.ROOT
DEST = ROOT / "results/one-shot-v2-servant/pilot-1/runtime"
IMAGE = "agentmvc-v2-pilot-servant:final"


def command(args, *, env=None, timeout=3600):
    proc = subprocess.run(args, cwd=ROOT, env=env, capture_output=True, text=True, timeout=timeout)
    if proc.returncode:
        raise RuntimeError(f"{args}: {proc.returncode}\n{proc.stdout[-3000:]}\n{proc.stderr[-3000:]}")
    return proc.stdout


def http_round(round_number):
    label = f"v2-pilot-servant-round{round_number}"
    scratch = ROOT / ".work/one-shot-v2-servant-runtime" / label
    output = DEST / "http" / f"round{round_number}"
    scratch.mkdir(parents=True, exist_ok=False)
    output.mkdir(parents=True, exist_ok=False)
    proc = subprocess.run([sys.executable, str(ROOT / "tools/bench/bench.py"),
                           IMAGE, label, str(scratch)], env={**os.environ, "BENCH_RAW_OUTPUT": "1"},
                          capture_output=True, text=True, timeout=3600)
    (output / "runner.log").write_text(proc.stdout + proc.stderr)
    for path in scratch.glob("k6-*.json"):
        shutil.copy2(path, output / path.name)
    for path in scratch.glob("raw-*.json"):
        compressed = output / (path.name + ".zst")
        command(["zstd", "-q", "-T2", "-o", str(compressed), str(path)])
        command(["zstd", "-q", "-t", str(compressed)])
    if not (scratch / "results.json").exists():
        raise RuntimeError(f"HTTP round {round_number} produced no results; see {output / 'runner.log'}")
    data = json.loads((scratch / "results.json").read_text())
    data.pop("app_log_tail", None)
    data["exit"] = proc.returncode
    (output / "results.json").write_text(json.dumps(data, indent=2) + "\n")
    if proc.returncode or any(row.get("failed_checks", 0) for row in data.get("scenarios", {}).values()):
        raise RuntimeError(f"HTTP round {round_number} failed; see {output / 'results.json'}")
    if len(list(output.glob("raw-*.json.zst"))) != 18:
        raise RuntimeError(f"HTTP round {round_number} lacks raw streams")
    return data


def main():
    source = json.loads(servant_v2.MANIFEST.read_text())
    if servant_v2.snapshot() != source:
        raise SystemExit("Frozen fixture source changed")
    one_shot.verify(servant_v2.WORK)
    result = DEST.parent
    for gate in ("development", "production"):
        data = json.loads((result / f"{gate}.json").read_text())
        if data["exit"]:
            raise SystemExit(f"{gate} gate failed; no comparable runtime round")
    command(["docker", "build", "-q", "-t", IMAGE, str(servant_v2.WORK)])
    image_id = command(["docker", "image", "inspect", "--format", "{{.Id}}", IMAGE]).strip()
    one_shot.RUN_NAME = "v2-pilot"
    live.OUT = DEST / "live"
    records = []
    for round_number in (1, 2):
        if round_number == 1:
            http = http_round(round_number)
            live.one("servant", round_number, (10, 100, 500), 20)
        else:
            live.one("servant", round_number, (10, 100, 500), 20)
            http = http_round(round_number)
        socket = json.loads((live.OUT / f"servant-round{round_number}.json").read_text())
        if socket["status"] != "complete" or any(
            scenario[key] for scenario in socket["scenarios"]
            for key in ("missing", "duplicate_revisions", "regressed_revisions")
        ):
            raise RuntimeError(f"WebSocket round {round_number} failed")
        if socket["image_sha256"] != image_id:
            raise RuntimeError("Runtime image changed between rounds")
        records.append({"round": round_number, "http": http, "live": socket})
    DEST.mkdir(parents=True, exist_ok=True)
    (DEST / "summary.json").write_text(json.dumps({
        "stack": "servant", "condition": "v2-pilot", "image_sha256": image_id,
        "http_vus": 16, "http_warmup": "3s", "http_duration": "15s",
        "limits": {"app": "2 CPU, 1 GiB", "database": "2 CPU, 1 GiB"},
        "raw_http_streams_verified": 36, "records": records,
    }, indent=2) + "\n")
    print("Servant v2 pilot: two HTTP and WebSocket rounds complete", flush=True)


if __name__ == "__main__":
    main()
