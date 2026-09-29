"""Two repeated production HTTP and live-socket rounds for a completed IHP run.

Usage: python3 tools/ihp_candidate_runtime.py 1|2|3
"""
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import ihp_candidate
import ihp_candidate_broker as bridge
import one_shot
import one_shot_live_bench as live

ROOT = one_shot.ROOT


def command(args, *, env=None, timeout=3600):
    proc = subprocess.run(args, env=env, capture_output=True, text=True, timeout=timeout)
    if proc.returncode:
        raise RuntimeError(f"{args}: {proc.returncode}\n{proc.stdout[-3000:]}\n{proc.stderr[-3000:]}")
    return proc.stdout


def build_image(work, image):
    script = 'image=$(nix --extra-experimental-features "nix-command flakes" --accept-flake-config build --no-link --print-out-paths .#agentmvc-image); cat "$image"'
    args = ["docker", "run", "--rm", *bridge.workspace_mounts(work), "-w", "/work/app", bridge.IMAGE,
            "sh", "-eu", "-c", script]
    with (ROOT / ".work/ihp-runtime-image-build.log").open("wb") as log:
        producer = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=log)
        consumer = subprocess.run(["docker", "load"], stdin=producer.stdout, capture_output=True, text=True)
        producer.stdout.close()
        rc = producer.wait()
    if rc or consumer.returncode:
        raise RuntimeError(f"Nix image build/load failed: {rc}, {consumer.returncode}\n"
                           + (ROOT / ".work/ihp-runtime-image-build.log").read_text()[-4000:])
    command(["docker", "build", "-q", "-t", image, str(work)])
    return command(["docker", "image", "inspect", "--format", "{{.Id}}", image]).strip()


def http_round(run_number, round_number, image, output):
    label = f"one-shot-ihp-{run_number}-round{round_number}"
    scratch = ROOT / ".work" / f"one-shot-ihp-{run_number}-runtime" / label
    dest = output / "http" / f"round{round_number}"
    scratch.mkdir(parents=True, exist_ok=False)
    dest.mkdir(parents=True, exist_ok=False)
    env = {**os.environ, "BENCH_RAW_OUTPUT": "1"}
    proc = subprocess.run([sys.executable, str(ROOT / "tools/bench/bench.py"), image, label, str(scratch)],
                          env=env, capture_output=True, text=True, timeout=3600)
    (dest / "runner.log").write_text(proc.stdout + proc.stderr)
    for path in scratch.glob("k6-*.json"):
        shutil.copy2(path, dest / path.name)
    for path in scratch.glob("raw-*.json"):
        compressed = dest / (path.name + ".zst")
        command(["zstd", "-q", "-T0", "-o", str(compressed), str(path)])
        command(["zstd", "-q", "-t", str(compressed)])
    if (scratch / "results.json").exists():
        data = json.loads((scratch / "results.json").read_text())
        data.pop("app_log_tail", None)
        data["exit"] = proc.returncode
        (dest / "results.json").write_text(json.dumps(data, indent=2) + "\n")
    if proc.returncode:
        raise RuntimeError(f"HTTP round {round_number} exited {proc.returncode}: see {dest / 'runner.log'}")
    return data


def main():
    if len(sys.argv) != 2 or sys.argv[1] not in ("1", "2", "3"):
        raise SystemExit(__doc__)
    run_number = sys.argv[1]
    manifest = json.loads(ihp_candidate.MANIFEST.read_text())
    if ihp_candidate.snapshot() != manifest:
        raise SystemExit("Frozen candidate source changed")
    work = ihp_candidate.workspace(run_number)
    one_shot.verify(work)
    result = ROOT / "results" / "one-shot-ihp" / f"run-{run_number}"
    for gate in ("development", "production"):
        data = json.loads((result / f"{gate}.json").read_text())
        if data["exit"]:
            raise SystemExit(f"{gate} gate failed; no comparable runtime round")
    image = f"agentmvc-one-shot-ihp-{run_number}-ihp:final"
    image_id = build_image(work, image)
    one_shot.RUN_NAME = f"one-shot-ihp-{run_number}"
    live.OUT = result / "runtime" / "live"
    output = result / "runtime"
    records = []
    for round_number in (1, 2):
        if round_number == 1:
            http = http_round(run_number, round_number, image, output)
            live.one("ihp", round_number, (10, 100, 500), 20)
        else:
            live.one("ihp", round_number, (10, 100, 500), 20)
            http = http_round(run_number, round_number, image, output)
        socket = json.loads((live.OUT / f"ihp-round{round_number}.json").read_text())
        if http.get("exit") != 0 or any(x.get("failed_checks", 0) for x in http.get("scenarios", {}).values()):
            raise RuntimeError(f"HTTP check failure in round {round_number}")
        if socket.get("status") != "complete" or any(s[k] for s in socket["scenarios"] for k in
                                                    ("missing", "duplicate_revisions", "regressed_revisions")):
            raise RuntimeError(f"WebSocket delivery failure in round {round_number}")
        archives = list((output / "http" / f"round{round_number}").glob("raw-*.json.zst"))
        if len(archives) != 18:
            raise RuntimeError(f"Expected 18 raw HTTP streams, found {len(archives)}")
        records.append({"round": round_number, "image_sha256": socket["image_sha256"],
                        "http": http, "live": socket, "raw_http_streams": len(archives)})
    if {r["image_sha256"] for r in records} != {image_id}:
        raise RuntimeError("Runtime image changed between rounds")
    summary = {"stack": "ihp", "run": int(run_number), "image_sha256": image_id,
               "http_vus": 16, "http_warmup": "3s", "http_duration": "15s",
               "limits": {"app": "2 CPU, 1 GiB", "database": "2 CPU, 1 GiB"},
               "raw_http_streams_verified": 36, "records": records}
    (output / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(f"IHP run {run_number}: two rounds, 36 compressed raw HTTP streams verified", flush=True)


if __name__ == "__main__":
    main()
