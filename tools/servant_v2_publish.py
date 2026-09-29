"""Publish scrubbed Servant pilot transcript, measurements, and source snapshot."""
import json
import os
import re
import shutil
from pathlib import Path

import measure
import one_shot
import one_shot_publish
import scrub
import servant_v2

ROOT = one_shot.ROOT
DEST = ROOT / "results/one-shot-v2-servant/pilot-1"
SOURCE_SKIP = {".scaffold", "realworld_spec", "security", "harness", "dist-newstyle",
               ".cabal", ".cache", ".tmp", ".git", "node_modules", "target"}
SOURCE_SUFFIXES = {".hs", ".sql", ".cabal", ".project", ".md", ".yaml", ".yml", ".toml", ".sh", ".json", ".py"}
SOURCE_NAMES = {"Dockerfile", "cabal.project", "cabal.project.freeze", "Makefile", ".dockerignore", ".gitignore"}


def measure_docs(work):
    fixture = set(json.loads((work / "FIXTURE.json").read_text())["files"])
    totals = {"whole_tokens": 0, "whole_lines": 0, "owned_tokens": 0, "owned_lines": 0, "files": []}
    for directory, subdirs, filenames in os.walk(work):
        subdirs[:] = [name for name in subdirs if name not in SOURCE_SKIP]
        for name in filenames:
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


def source_snapshot(work):
    dest = DEST / "source"
    fixture = set(json.loads((work / "FIXTURE.json").read_text())["files"])
    copied = []
    for directory, subdirs, filenames in os.walk(work):
        subdirs[:] = [name for name in subdirs if name not in SOURCE_SKIP]
        for name in filenames:
            path = Path(directory) / name
            rel = path.relative_to(work)
            if str(rel) in fixture or name == "FIXTURE.json" or (name.startswith(".") and name not in SOURCE_NAMES):
                continue
            if name not in SOURCE_NAMES and path.suffix not in SOURCE_SUFFIXES:
                continue
            if path.stat().st_size > 2_000_000:
                raise SystemExit(f"Unexpected large source file: {rel}")
            target = dest / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            if target.exists():
                if target.read_bytes() != path.read_bytes():
                    raise SystemExit(f"Source snapshot differs from finished workdir: {target}")
            else:
                shutil.copy2(path, target)
            copied.append(str(rel))
    (DEST / "source-snapshot.json").write_text(json.dumps({"files": sorted(copied)}, indent=2) + "\n")


def check_attempts():
    path = ROOT / ".work/one-shot-v2-servant-broker/requests.jsonl"
    actions = {}
    run = json.loads((servant_v2.LOG / "run.json").read_text())
    if path.exists():
        for line in path.read_text().splitlines():
            row = json.loads(line)
            if not run["started"] <= row["time"] <= run["finished"]:
                continue
            bucket = actions.setdefault(row["action"], {"attempts": 0, "failures": 0})
            bucket["attempts"] += 1
            bucket["failures"] += int(row["exit"] != 0)
    (DEST / "check-attempts.json").write_text(json.dumps(actions, indent=2) + "\n")
    return actions


def main():
    work, logs = servant_v2.WORK, servant_v2.LOG
    one_shot.verify(work)
    if not (logs / "run.json").exists():
        raise SystemExit("Measured agent has not finished")
    DEST.mkdir(parents=True, exist_ok=True)
    prompt = DEST.parent / "frozen-prompt.md"
    if prompt.exists() and prompt.read_bytes() != (work / "PROMPT.md").read_bytes():
        raise SystemExit("Published prompt differs from frozen workspace")
    prompt.write_bytes((work / "PROMPT.md").read_bytes())
    token = (servant_v2.CONTROL / "token").read_text().strip()
    deny = [re.escape(token)]
    scrub.scrub_file(logs / "events.jsonl", work, DEST / "transcript", deny=deny,
                     header={"title": "Servant v2 pilot agent",
                             "Prompt": "[frozen prompt](../frozen-prompt.md)"})
    cleaner = scrub.Scrubber(work, deny)
    if (logs / "last.md").exists():
        report = cleaner.text((logs / "last.md").read_text())
        if cleaner.leaks(report):
            raise SystemExit("Agent report contains private paths")
        (DEST / "agent-report.md").write_text(report)
    shutil.copy2(logs / "run.json", DEST / "run.json")
    rules = measure.load_stack("servant")
    size = measure.measure(rules, work, work / ".scaffold")
    inventory = one_shot_publish.source_inventory(rules, work)
    for total, item in (("tokens", "whole_tokens"), ("lines", "whole_lines"),
                        ("owned_tokens", "owned_tokens"), ("owned_lines", "owned_lines")):
        if sum(row[item] for row in inventory) != size[total]:
            raise SystemExit(f"Source inventory mismatch: {total}")
    size.update(encoding="o200k_base", baseline="untouched Servant scaffold in .scaffold/",
                rule="tools/measure.py; fixtures, tests, generated output, Dockerfile, and lockfile excluded")
    (DEST / "size.json").write_text(json.dumps(size, indent=2) + "\n")
    (DEST / "source-files.json").write_text(json.dumps(inventory, indent=2) + "\n")
    (DEST / "docs.json").write_text(json.dumps(measure_docs(work), indent=2) + "\n")
    check_attempts()
    source_snapshot(work)
    print(json.dumps({"size": size, "source_files": len(inventory)}, indent=2), flush=True)


if __name__ == "__main__":
    main()
