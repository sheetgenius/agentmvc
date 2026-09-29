"""Paired HTTP and socket rounds for an independently gated shine-track image.

Usage: python3 tools/shine_runtime.py STACK VARIANT WORKDIR
The image tag is agentmvc-shine-VARIANT-STACK:final and the results live in
results/shine/STACK/VARIANT/runtime.
"""

import json
import subprocess
import sys
from pathlib import Path

import ihp_candidate_runtime as measured
import one_shot
import one_shot_live_bench as live


def main():
    if len(sys.argv) != 4 or sys.argv[1] not in ("rails", "phoenix", "loco"):
        raise SystemExit(__doc__)
    stack, variant, workdir = sys.argv[1:]
    work = Path(workdir).resolve()
    output = one_shot.ROOT / "results" / "shine" / stack / variant / "runtime"
    image = f"agentmvc-shine-{variant}-{stack}:final"
    subprocess.run(["docker", "build", "-q", "-t", image, str(work)], check=True)
    image_id = subprocess.check_output(
        ["docker", "image", "inspect", "--format", "{{.Id}}", image], text=True
    ).strip()
    one_shot.RUN_NAME = f"shine-{variant}"
    live.OUT = output / "live"
    records = []
    for round_number in (1, 2):
        if round_number == 1:
            http = measured.http_round(f"{stack}-{variant}", round_number, image, output)
            live.one(stack, round_number, (10, 100, 500), 20)
        else:
            live.one(stack, round_number, (10, 100, 500), 20)
            http = measured.http_round(f"{stack}-{variant}", round_number, image, output)
        socket = json.loads((live.OUT / f"{stack}-round{round_number}.json").read_text())
        if http["exit"] or any(row["failed_checks"] for row in http["scenarios"].values()):
            raise RuntimeError(f"HTTP round {round_number} failed")
        if socket["status"] != "complete" or any(
            scenario[key]
            for scenario in socket["scenarios"]
            for key in ("missing", "duplicate_revisions", "regressed_revisions")
        ):
            raise RuntimeError(f"Socket round {round_number} failed")
        archives = list((output / "http" / f"round{round_number}").glob("raw-*.json.zst"))
        if len(archives) != 18:
            raise RuntimeError(f"Expected 18 raw streams, found {len(archives)}")
        records.append({"round": round_number, "http": http, "live": socket})
    if {row["live"]["image_sha256"] for row in records} != {image_id}:
        raise RuntimeError("Socket image differs from HTTP image")
    output.mkdir(parents=True, exist_ok=True)
    (output / "summary.json").write_text(json.dumps({
        "stack": stack, "variant": variant, "image_sha256": image_id,
        "http_vus": 16, "http_warmup": "3s", "http_duration": "15s",
        "limits": {"app": "2 CPU, 1 GiB", "database": "2 CPU, 1 GiB"},
        "raw_http_streams_verified": 36, "records": records,
    }, indent=2) + "\n")
    print(f"{stack} {variant}: two paired rounds and 36 raw streams verified")


if __name__ == "__main__":
    main()
