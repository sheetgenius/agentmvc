"""Validate and index the two paired one-shot runtime rounds."""
import json
import subprocess

import one_shot


OUT = one_shot.RESULTS / "runtime"
SCENARIOS = ("list_anonymous", "list_signed_in", "list_by_tag", "feed", "article",
             "comments", "tags", "favorite_toggle", "create_article")
COUNTS = (10, 100, 500)


def read(path):
    return json.loads(path.read_text())


def main():
    records = []
    for round_number in (1, 2):
        stacks = one_shot.STACKS if round_number == 1 else tuple(reversed(one_shot.STACKS))
        for stack in stacks:
            http_dir = OUT / "http" / f"{stack}-round{round_number}"
            http = read(http_dir / "results.json")
            live = read(OUT / "live" / f"{stack}-round{round_number}.json")
            if http.get("exit") != 0 or tuple(http.get("scenarios", {})) != SCENARIOS:
                raise SystemExit(f"Incomplete HTTP round: {stack} {round_number}")
            if live.get("status") != "complete" or [s["subscribers"] for s in live["scenarios"]] != list(COUNTS):
                raise SystemExit(f"Incomplete live round: {stack} {round_number}")
            if any(s["failed_checks"] for s in http["scenarios"].values()):
                raise SystemExit(f"Failed HTTP checks: {stack} {round_number}")
            if any(s[key] for s in live["scenarios"] for key in
                   ("missing", "duplicate_revisions", "regressed_revisions")):
                raise SystemExit(f"Failed live deliveries: {stack} {round_number}")
            archives = sorted(http_dir.glob("raw-*.json.zst"))
            if len(archives) != 18:
                raise SystemExit(f"Expected 18 raw streams: {stack} {round_number}; got {len(archives)}")
            for archive in archives:
                subprocess.run(["zstd", "-t", "-q", str(archive)], check=True,
                               stdout=subprocess.DEVNULL)
            records.append({
                "stack": stack, "round": round_number,
                "http": {"image_mb": http["image_mb"],
                         "cold_start_seconds": http["cold_start_seconds"],
                         "idle_memory_mb": http["idle_memory_mb"],
                         "scenarios": http["scenarios"]},
                "live": {"image_sha256": live["image_sha256"],
                         "baseline": live["baseline"],
                         "scenarios": [{key: scenario[key] for key in
                                        ("subscribers", "articles", "saves", "actual_saves_per_second",
                                         "save_latency", "delivery_latency", "missing",
                                         "duplicate_revisions", "regressed_revisions", "idle", "active",
                                         "foreign_container_cpu_percent_peak", "host_load_1m_peak")}
                                       for scenario in live["scenarios"]]},
                "raw_http_streams": len(archives),
            })
    for stack in one_shot.STACKS:
        images = {row["live"]["image_sha256"] for row in records if row["stack"] == stack}
        if len(images) != 1:
            raise SystemExit(f"Image changed between rounds: {stack}")
    summary = {"run": one_shot.RUN_NAME,
               "order": [row["stack"] for row in records],
               "http_vus": 16, "http_warmup": "3s", "http_duration": "15s",
               "limits": {"app": "2 CPU, 1 GiB", "database": "2 CPU, 1 GiB"},
               "raw_http_streams_verified": sum(row["raw_http_streams"] for row in records),
               "records": records}
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(f"Verified {len(records)} rounds and {summary['raw_http_streams_verified']} raw streams")


if __name__ == "__main__":
    main()
