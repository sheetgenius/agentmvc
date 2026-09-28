"""Keep the run ledger: one line of JSON per scored agent run, in results/runs.jsonl.

Run output (transcripts, agent reports, gate logs, raw benchmark streams) is not committed. Archive it
elsewhere, such as a GitHub release, and record the archive name and checksum in the run's row.

Usage:
  python3 tools/ledger.py add RESULT_DIR --id ID --stack STACK --prompt NAME --framework yes|partial|no
                              [--brief NAME] [--runtime SUMMARY_JSON] [--note TEXT]
                              [--archive NAME --archive-sha256 HASH]
  python3 tools/ledger.py best     the reference run for each stack, by the rule in results/README.md
  python3 tools/ledger.py table    a Markdown table of every run

RESULT_DIR is a published run directory holding run.json, size.json, the gate records development.json and
production.json, and optionally docs.json and development-attempt*.json or production-attempt*.json.
"""
import argparse
import hashlib
import json
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LEDGER = ROOT / "results" / "runs.jsonl"
BASELINE = ROOT / "one-shot" / "PROMPT.md"
FRAMEWORK = ("yes", "partial", "no")


def read(path):
    return json.loads(Path(path).read_text())


def rows():
    if not LEDGER.exists():
        return []
    return [json.loads(line) for line in LEDGER.read_text().splitlines() if line.strip()]


def rounded(value):
    if value is None:
        return None
    return round(value, 2) if value < 10 else round(value, 1)


def mean(values):
    values = [v for v in values if v is not None]
    return rounded(statistics.fmean(values)) if values else None


def gate(result, name):
    final = result / f"{name}.json"
    if not final.exists():
        return None
    earlier = len(list(result.glob(f"{name}-attempt*.json")))
    return {"result": "pass" if read(final).get("exit") == 0 else "fail", "attempts": earlier + 1}


def runtime(summary, stack):
    """Means over measurement rounds. Reads both summary formats the runtime tools have written."""
    data = read(summary)
    if "records" in data:
        records = [r for r in data["records"] if r.get("stack", stack) == stack]
        http = [r["http"] for r in records]
        scenarios = [h["scenarios"] for h in http]
        article = [s["article"]["rps"] for s in scenarios]
        listing = [s["list_anonymous"]["rps"] for s in scenarios]
        sql = [s["list_anonymous"]["sql_statements_per_request"] for s in scenarios]
        peak = [max(x.get("peak_memory_mb", 0) for x in s.values()) for s in scenarios]
        cold = [h.get("cold_start_seconds") for h in http]
        image = [h.get("image_mb") for h in http]
        p95 = [s["delivery_latency"]["p95_ms"] for r in records
               for s in r.get("live", {}).get("scenarios", []) if s.get("subscribers") == 500]
    else:
        http, live = data["http"][stack], data["live"][stack]
        scenarios = http["scenarios"]
        article = [s["rps"] for s in scenarios["article"]]
        listing = [s["rps"] for s in scenarios["list_anonymous"]]
        sql = [s["sql_statements_per_request"] for s in scenarios["list_anonymous"]]
        peak = [max(rounds[i].get("peak_memory_mb", 0) for rounds in scenarios.values())
                for i in range(len(article))]
        cold, image = http.get("cold_start_seconds", []), http.get("image_mb", [])
        p95 = [s["delivery_latency"]["p95_ms"] for s in live["scenarios"].get("500", [])]
    return {"rounds": len(article), "article_rps": mean(article), "list_rps": mean(listing),
            "list_sql_per_request": mean(sql), "peak_memory_mb": rounded(max(peak)) if peak else None,
            "cold_start_s": mean(cold), "image_mb": mean(image), "live_500_p95_ms": mean(p95)}


def add(args):
    result = Path(args.result_dir)
    run, size = read(result / "run.json"), read(result / "size.json")
    docs = read(result / "docs.json") if (result / "docs.json").exists() else None
    tokens = run["tokens"]
    row = {
        "id": args.id,
        "date": run["started"][:10],
        "stack": args.stack,
        "prompt": {"name": args.prompt, "sha256": run["prompt_sha256"]},
        "brief": args.brief,
        "fixture_sha256": run["fixture_sha256"],
        "agent": {"tool": run["tool"], "model": run["model"], "reasoning": run["reasoning"]},
        "effort": {"seconds": run["seconds"], "uncached_plus_output_tokens": tokens["uncached_plus_output"],
                   "total_input_tokens": tokens["input"], "output_tokens": tokens["output"],
                   "commands": tokens["commands"]},
        "gates": {"development": gate(result, "development"), "production": gate(result, "production")},
        "code": {"owned_tokens": size["owned_tokens"], "owned_lines": size["owned_lines"],
                 "whole_tokens": size["tokens"], "docs_tokens": docs["owned_tokens"] if docs else None},
        "runtime": runtime(args.runtime, args.stack) if args.runtime else None,
        "review": {"framework": args.framework, "note": args.note},
        "archive": {"name": args.archive, "sha256": args.archive_sha256} if args.archive else None,
    }
    if any(r["id"] == row["id"] for r in rows()):
        raise SystemExit(f"{row['id']} is already in the ledger")
    LEDGER.parent.mkdir(exist_ok=True)
    with LEDGER.open("a") as out:
        out.write(json.dumps(row, separators=(",", ":")) + "\n")
    print(f"added {row['id']}")


def eligible(row, baseline):
    gates = row["gates"].values()
    return (row["prompt"]["sha256"] == baseline and not row["brief"]
            and all(g and g["result"] == "pass" for g in gates)
            and row["review"]["framework"] != "no")


def best():
    baseline = hashlib.sha256(BASELINE.read_bytes()).hexdigest()
    picks = {}
    for row in rows():
        if eligible(row, baseline):
            current = picks.get(row["stack"])
            if current is None or row["code"]["owned_tokens"] < current["code"]["owned_tokens"]:
                picks[row["stack"]] = row
    for stack, row in picks.items():
        print(f"{stack}: {row['id']} ({row['code']['owned_tokens']:,} owned tokens)")
    return picks


def table():
    print("| Run | Stack | Prompt | Gates | Owned tokens | Agent minutes | Single article req/s | "
          "Article list req/s | Framework |")
    print("| --- | --- | --- | --- | ---: | ---: | ---: | ---: | --- |")
    for row in rows():
        prompt = row["prompt"]["name"] + (f" + {row['brief']}" if row["brief"] else "")
        gates = "pass" if all(g and g["result"] == "pass" for g in row["gates"].values()) else "fail"
        rt = row["runtime"] or {}
        fmt = lambda v: "" if v is None else f"{v:,}"
        print(f"| {row['id']} | {row['stack']} | {prompt} | {gates} | {row['code']['owned_tokens']:,} | "
              f"{row['effort']['seconds'] / 60:.1f} | {fmt(rt.get('article_rps'))} | {fmt(rt.get('list_rps'))} | "
              f"{row['review']['framework']} |")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    a = sub.add_parser("add")
    a.add_argument("result_dir")
    a.add_argument("--id", required=True)
    a.add_argument("--stack", required=True)
    a.add_argument("--prompt", required=True, help="short name of the prompt, such as density")
    a.add_argument("--brief", help="short name of a stack brief appended to the prompt")
    a.add_argument("--framework", required=True, choices=FRAMEWORK,
                   help="yes: conventional framework paths; partial: framework runs the app but the agent "
                        "routed around one convention; no: the production app bypasses the framework")
    a.add_argument("--runtime", help="runtime summary.json for this run")
    a.add_argument("--note")
    a.add_argument("--archive")
    a.add_argument("--archive-sha256")
    sub.add_parser("best")
    sub.add_parser("table")
    args = parser.parse_args()
    {"add": lambda: add(args), "best": best, "table": table}[args.command]()


if __name__ == "__main__":
    main()
