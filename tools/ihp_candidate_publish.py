"""Publish a measured IHP build's scrubbed transcript and code inventory."""
import json
import os
import re
import sys
from pathlib import Path

import ihp_candidate
import measure
import one_shot
import one_shot_publish
import scrub

ROOT = one_shot.ROOT


def docs(work):
    fixture = set(json.loads((work / "FIXTURE.json").read_text())["files"])
    excluded = measure.SKIP_DIRS | {"security", "harness", ".devenv", ".cache", ".tmp", "build", "Test", ".github"}
    totals = {"whole_tokens": 0, "whole_lines": 0, "owned_tokens": 0, "owned_lines": 0, "files": []}
    for directory, subdirs, files in os.walk(work):
        subdirs[:] = [name for name in subdirs if name not in excluded]
        for name in files:
            if not name.endswith(".md"):
                continue
            path = Path(directory) / name
            rel = str(path.relative_to(work))
            if rel in fixture:
                continue
            previous = work / ".scaffold" / rel
            lines = measure.read_lines(path.read_text(errors="ignore"))
            old = measure.read_lines(previous.read_text(errors="ignore")) if previous.exists() else []
            owned = measure.added(old, lines)
            if owned:
                totals["whole_tokens"] += measure.tokens(lines)
                totals["whole_lines"] += len(lines)
                totals["owned_tokens"] += measure.tokens(owned)
                totals["owned_lines"] += len(owned)
                totals["files"].append(rel)
    totals["files"].sort()
    return totals


def main():
    if len(sys.argv) != 2 or sys.argv[1] not in ("1", "2", "3"):
        raise SystemExit(__doc__)
    run_number = sys.argv[1]
    work = ihp_candidate.workspace(run_number)
    logs = ROOT / ".work" / f"one-shot-ihp-{run_number}-agent-logs" / "ihp"
    dest = ROOT / "results" / "one-shot-ihp" / f"run-{run_number}"
    one_shot.verify(work)
    if not (logs / "run.json").exists():
        raise SystemExit("Measured agent has not finished")
    dest.mkdir(parents=True, exist_ok=True)
    prompt = dest.parent / "frozen-prompt.md"
    source_prompt = ROOT / "one-shot/PROMPT.md"
    if prompt.exists() and prompt.read_bytes() != source_prompt.read_bytes():
        raise SystemExit("Published prompt differs from frozen source")
    prompt.write_bytes(source_prompt.read_bytes())
    token = (ROOT / ".work" / f"one-shot-ihp-{run_number}-control" / "token").read_text().strip()
    deny = [re.escape(token)]
    scrub.scrub_file(logs / "events.jsonl", work, dest / "transcript", deny=deny,
                     header={"title": f"IHP one-shot agent, run {run_number}",
                             "Prompt": "[frozen prompt](../frozen-prompt.md)"})
    cleaner = scrub.Scrubber(work, deny)
    if (logs / "last.md").exists():
        report = cleaner.text((logs / "last.md").read_text())
        if cleaner.leaks(report):
            raise SystemExit("Agent report contains private paths")
        (dest / "agent-report.md").write_text(report)
    (dest / "run.json").write_bytes((logs / "run.json").read_bytes())
    rules = measure.load_stack("ihp")
    rules["code"].setdefault("skip_dirs", []).extend(("build", "security", "harness", ".devenv", ".cache", ".tmp", "Test", ".github"))
    rules["code"].setdefault("skip_paths", []).append("Config/nix")
    rules["code"].setdefault("skip_files", []).extend((".stylish-haskell.yaml", "Setup.hs", "Makefile"))
    size = measure.measure(rules, work, work / ".scaffold")
    inventory = one_shot_publish.source_inventory(rules, work)
    for total, item in (("tokens", "whole_tokens"), ("lines", "whole_lines"),
                        ("owned_tokens", "owned_tokens"), ("owned_lines", "owned_lines")):
        if sum(row[item] for row in inventory) != size[total]:
            raise SystemExit(f"Source inventory mismatch: {total}")
    size.update(encoding="o200k_base", baseline="untouched IHP scaffold in .scaffold/",
                rule="tools/measure.py with fixed IHP review exclusions; generated output, fixtures, tests, deployment scaffolding, formatter config and lockfiles excluded",
                review_exclusions={"skip_dirs": rules["code"]["skip_dirs"],
                                   "skip_paths": rules["code"]["skip_paths"],
                                   "skip_files": rules["code"]["skip_files"]})
    (dest / "size.json").write_text(json.dumps(size, indent=2) + "\n")
    (dest / "source-files.json").write_text(json.dumps(inventory, indent=2) + "\n")
    (dest / "docs.json").write_text(json.dumps(docs(work), indent=2) + "\n")
    requests = ROOT / ".work" / f"one-shot-ihp-{run_number}-broker" / "requests.jsonl"
    actions = {}
    if requests.exists():
        for line in requests.read_text().splitlines():
            row = json.loads(line)
            bucket = actions.setdefault(row["action"], {"attempts": 0, "failures": 0})
            bucket["attempts"] += 1
            bucket["failures"] += int(row["exit"] != 0)
    (dest / "check-attempts.json").write_text(json.dumps(actions, indent=2) + "\n")
    print(json.dumps({"run": int(run_number), "size": size, "checks": actions}, indent=2), flush=True)


if __name__ == "__main__":
    main()
