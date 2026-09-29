"""Paired runtime measurement for the optimized copy of guided IHP."""

import json
import subprocess
from pathlib import Path

import ihp_candidate_runtime as measured
import one_shot
import one_shot_live_bench as live

ROOT = one_shot.ROOT
WORK = ROOT / ".work/shine-ihp/ihp"
OUT = ROOT / "results/shine/ihp/runtime"
IMAGE = "agentmvc-shine-ihp-ihp:final"


def main():
    gate = json.loads((OUT.parent / "production.json").read_text())
    if gate["exit"]:
        raise SystemExit("Optimized production gate failed")
    subprocess.run(["docker", "build", "-q", "-t", IMAGE, str(WORK)], check=True)
    image_id = subprocess.check_output(
        ["docker", "image", "inspect", "--format", "{{.Id}}", IMAGE], text=True
    ).strip()
    one_shot.RUN_NAME = "shine-ihp"
    live.OUT = OUT / "live"
    records = []
    for round_number in (1, 2):
        if round_number == 1:
            http = measured.http_round("shine", round_number, IMAGE, OUT)
            live.one("ihp", round_number, (10, 100, 500), 20)
        else:
            live.one("ihp", round_number, (10, 100, 500), 20)
            http = measured.http_round("shine", round_number, IMAGE, OUT)
        socket = json.loads((live.OUT / f"ihp-round{round_number}.json").read_text())
        if http["exit"] or any(row["failed_checks"] for row in http["scenarios"].values()):
            raise RuntimeError(f"HTTP round {round_number} failed")
        if socket["status"] != "complete" or any(
            scenario[key]
            for scenario in socket["scenarios"]
            for key in ("missing", "duplicate_revisions", "regressed_revisions")
        ):
            raise RuntimeError(f"Socket round {round_number} failed")
        archives = list((OUT / "http" / f"round{round_number}").glob("raw-*.json.zst"))
        if len(archives) != 18:
            raise RuntimeError(f"Expected 18 raw streams, found {len(archives)}")
        records.append({"round": round_number, "image_sha256": image_id,
                        "http": http, "live": socket, "raw_http_streams": len(archives)})
    if {row["live"]["image_sha256"] for row in records} != {image_id}:
        raise RuntimeError("Socket image differs from HTTP image")
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "summary.json").write_text(json.dumps({
        "track": "IHP optimized build-only", "image_sha256": image_id,
        "http_vus": 16, "http_warmup": "3s", "http_duration": "15s",
        "limits": {"app": "2 CPU, 1 GiB", "database": "2 CPU, 1 GiB"},
        "raw_http_streams_verified": 36, "records": records,
    }, indent=2) + "\n")
    print("Optimized IHP: two paired rounds and 36 raw streams verified")


if __name__ == "__main__":
    main()
