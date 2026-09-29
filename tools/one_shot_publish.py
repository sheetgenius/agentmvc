"""Publish one measured agent's scrubbed transcript, report, effort and code size."""
import json
import os
import re
import sys
from pathlib import Path

import measure
import one_shot
import scrub

ROOT = one_shot.ROOT


def measure_docs(work):
    fixture = set(json.loads((work / "FIXTURE.json").read_text())["files"])
    excluded = measure.SKIP_DIRS | {"security", "harness", ".cargo", ".npm-cache", ".cache", ".tmp"}
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
            current_lines = measure.read_lines(path.read_text(errors="ignore"))
            previous_lines = measure.read_lines(previous.read_text(errors="ignore")) if previous.exists() else []
            owned_lines = measure.added(previous_lines, current_lines)
            if not owned_lines:
                continue
            totals["whole_tokens"] += measure.tokens(current_lines)
            totals["whole_lines"] += len(current_lines)
            totals["owned_tokens"] += measure.tokens(owned_lines)
            totals["owned_lines"] += len(owned_lines)
            totals["files"].append(rel)
    totals["files"].sort()
    return totals


def source_inventory(rules, work):
    """File-level audit of the paths behind the aggregate source measurement."""
    rows = []
    baseline = work / ".scaffold"
    for rel, (prefix, is_code) in measure.source_files(rules, work):
        path = work / rel
        old_path = baseline / rel
        current = path.read_text(errors="ignore")
        old = old_path.read_text(errors="ignore") if old_path.exists() else ""
        doc_attributes = rules["code"].get("doc_attributes", []) if is_code else ()
        owned = measure.added(measure.code_lines(old, prefix, doc_attributes),
                              measure.code_lines(current, prefix, doc_attributes))
        whole = measure.read_lines(current)
        rows.append({"path": rel, "kind": "code" if is_code else "config",
                     "baseline": "changed" if old_path.exists() else "created",
                     "whole_tokens": measure.tokens(whole), "whole_lines": len(whole),
                     "owned_tokens": measure.tokens(owned), "owned_lines": len(owned)})
    return sorted(rows, key=lambda row: row["path"])


def main():
    if len(sys.argv) != 2 or sys.argv[1] not in one_shot.STACKS:
        raise SystemExit("usage: .venv/bin/python tools/one_shot_publish.py rails|phoenix|loco")
    stack = sys.argv[1]
    work = one_shot.WORK / stack
    logs = one_shot.LOGS / stack
    dest = one_shot.RESULTS / stack
    one_shot.verify(work)
    if not (logs / "run.json").exists():
        raise SystemExit("Measured agent has not finished")
    dest.mkdir(parents=True, exist_ok=True)
    token = json.loads((one_shot.CONTROL / "tokens.json").read_text())[stack]
    deny = [re.escape(token)]
    scrub.scrub_file(logs / "events.jsonl", work, dest / "transcript", deny=deny,
                     header={"title": f"{stack.title()} one-shot agent",
                             "Prompt": "[frozen prompt](../frozen-prompt.md)"})
    cleaner = scrub.Scrubber(work, deny)
    if (logs / "last.md").exists():
        report = cleaner.text((logs / "last.md").read_text())
        if cleaner.leaks(report):
            raise SystemExit("Agent report still contains private paths or strings")
        (dest / "agent-report.md").write_text(report)
    record = json.loads((logs / "run.json").read_text())
    (dest / "run.json").write_text(json.dumps(record, indent=2) + "\n")
    rules = measure.load_stack(stack)
    # Dependency caches are workdir-local for isolation, never application source.
    rules["code"].setdefault("skip_dirs", []).extend((".cargo", ".tmp", ".npm-cache", ".cache"))
    generated = []
    if stack == "rails":
        # Exclude the installer schema only when its body matches the installed gem template.
        templates = list(work.glob("vendor/bundle/gems/solid_queue-*/lib/generators/solid_queue/install/templates/db/queue_schema.rb"))
        for migration in (work / "db/migrate").glob("*create_solid_queue.rb"):
            lines = migration.read_text().splitlines()
            body = ["".join(line.split()) for line in lines[2:-2] if line.strip()]
            if any(body == ["".join(line.split()) for line in template.read_text().splitlines()[1:-1] if line.strip()]
                   for template in templates):
                generated.append(str(migration.relative_to(work)))
        rules["code"].setdefault("generated", []).extend(generated)
    if stack == "phoenix":
        # This directory is a toolchain alias for the root scaffold, not backend source.
        rules["code"].setdefault("skip_paths", []).append("conduit")
    size = measure.measure(rules, work, work / ".scaffold")
    inventory = source_inventory(rules, work)
    for total, item in (("tokens", "whole_tokens"), ("lines", "whole_lines"),
                        ("owned_tokens", "owned_tokens"), ("owned_lines", "owned_lines")):
        if sum(row[item] for row in inventory) != size[total]:
            raise SystemExit(f"Source inventory mismatch for {total}")
    size["encoding"] = "o200k_base"
    size["baseline"] = "untouched scaffold copied to .scaffold/"
    size["rule"] = "tools/measure.py per-stack rules; generated schema and lockfiles excluded"
    size["cache_dirs_excluded"] = [".cargo", ".tmp", ".npm-cache", ".cache"]
    size["generated_excluded"] = generated
    if generated:
        size["generated_note"] = "The Solid Queue migration body matches the installed gem's queue_schema.rb template after whitespace normalization; only the wrapper differs."
    if stack == "phoenix":
        size["toolchain_alias_excluded"] = "conduit/ contains symlinks to the root Phoenix source plus Mix caches; the broker's working directory required this alias."
    (dest / "size.json").write_text(json.dumps(size, indent=2) + "\n")
    (dest / "source-files.json").write_text(json.dumps(inventory, indent=2) + "\n")
    (dest / "docs.json").write_text(json.dumps(measure_docs(work), indent=2) + "\n")
    print(stack, size, flush=True)


if __name__ == "__main__":
    main()
