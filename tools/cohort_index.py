#!/usr/bin/env python3
"""Index recorded experiment identities; never launch work or alter old evidence."""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]


def read(path: Path) -> dict:
    return json.loads(path.read_text()) if path.is_file() else {}


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def existing(path: Path) -> str | None:
    return rel(path) if path.exists() else None


def first(*values):
    return next((value for value in values if value is not None), None)


def identity_links() -> tuple[dict, dict]:
    """Match prompts by bytes and fixtures by their recorded manifest identity."""
    prompts, fixtures = {}, {}
    candidates = set(ROOT.glob("steps/*.md")) | set(ROOT.glob("one-shot*/PROMPT.md"))
    candidates |= set((ROOT / "results").rglob("frozen-prompt.md"))
    for path in sorted(candidates):
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        prompts.setdefault(digest, rel(path))
    candidates = set(ROOT.glob("one-shot*/fixture-manifest.json"))
    candidates |= set(ROOT.glob("stacks/*/lane-fixture.json"))
    candidates |= set(ROOT.glob("spec/**/fixture-manifest.json"))
    candidates |= set((ROOT / "results").rglob("*fixture-manifest.json"))
    candidates.add(ROOT / "ihp-candidate/fixture-manifest.json")
    for path in sorted(candidates):
        digest = read(path).get("sha256")
        if digest:
            fixtures.setdefault(digest, rel(path))
    return prompts, fixtures


def classify(path: Path, data: dict, role: str) -> tuple[str | None, str, str]:
    parts = path.relative_to(ROOT).parts
    if parts[0] == "stacks":
        stack, series, protocol = parts[1], "original-eight-step", "eight-step"
    elif parts[1] == "lanes":
        stack = None if parts[2] == "comprehension" else parts[2]
        series, protocol = "prepared-lanes", "eight-step"
    else:
        series = parts[1]
        match = re.fullmatch(r"one-shot-(?:v2-)?(ihp|servant|typescript|rails|phoenix|go|python|clojure)(?:-expert)?", series)
        stack = match[1] if match else None
        protocol = "one-shot" if series.startswith("one-shot") else "diagnostic"
    if role in {"reader", "preflight"}:
        protocol = "comprehension" if role == "reader" else "preflight"
    return first(data.get("stack"), stack), series, protocol


def verdict(data: dict) -> str:
    if isinstance(data.get("passed"), bool):
        return "pass" if data["passed"] else "fail"
    if isinstance(data.get("exit"), int):
        return "pass" if data["exit"] == 0 else "fail"
    return "unknown"


def gates(base: Path, record: str, data: dict, role: str, legacy: bool) -> list:
    found = []
    if legacy:
        for key, value in (data.get("verified") or {}).items():
            if key in {"check", "check_production"}:
                found.append({"scope": key, "status": value,
                              "record": f"{record}/verified/{key}"})
        if role == "reader":
            stack = base.name
            grades = read(ROOT / "comprehension/grades.json")
            grade = grades.get(data["step"], {}).get(stack)
            if grade:
                found.append({"scope": "reader-grade", "status": "graded",
                              "score": grade.get("score"),
                              "record": f"comprehension/grades.json#/{data['step']}/{stack}"})
        return found
    if role == "preflight":
        # A preflight agent exiting cleanly is not an infrastructure gate verdict.
        return ([{"scope": "preflight", "status": verdict(data), "record": record}]
                if record.endswith("preflight.json") else [])
    for name in ("verification.json", "validation.json", "development.json",
                 "production.json", "grades.json"):
        path = base / name
        if not path.is_file():
            continue
        value = read(path)
        gate = {"scope": name.removesuffix(".json"), "status": verdict(value),
                "record": rel(path)}
        if name == "grades.json":
            gate.update(status="graded", score=value.get("score"), maximum=value.get("maximum"))
        found.append(gate)
        for key in ("independent_development", "independent_production"):
            if key in value:
                found.append({"scope": key, "status": verdict(value[key]),
                              "record": f"{rel(path)}#/{key}"})
    return found


def make_record(path: Path, data: dict, role: str, prompts: dict, fixtures: dict,
                pointer: str = "") -> dict:
    base = path.parent
    record = rel(path) + pointer
    legacy = path.name == "runs.json"
    # Sidecars add evidence identities, never an inferred agent model or CLI.
    prepared = read(base / "prepared.json") if role == "reader" else {}
    validation = read(base / "validation.json") if role == "reference" else {}
    effective = read(base / "effective-fixture.json") if role == "measured-coding" else {}
    snapshot = read(base / "source-snapshot.json") if not legacy and role != "preflight" else {}
    facts = {**prepared, **validation, **data}
    stack, series, protocol = classify(path, facts, role)
    phase = first(data.get("phase"), data.get("step"), prepared.get("phase"))
    if phase is None and protocol == "one-shot":
        phase = "one-shot"
    agent = data.get("agent") or data
    tool = agent.get("tool")
    prompt_hash = first(facts.get("prompt_sha256"), facts.get("guided_prompt_sha256"))
    fixture_hash = first(facts.get("fixture_sha256"), facts.get("guided_fixture_sha256"),
                         facts.get("candidate_fixture_sha256"), facts.get("v2_fixture_sha256"))
    effective_hash = first(data.get("effective_fixture_sha256"), effective.get("sha256"))
    source_path = existing(base / "source")
    if snapshot.get("path"):
        source_path = existing(ROOT / snapshot["path"])
    if (legacy or role == "reader") and phase and stack:
        source_path = existing(ROOT / "stacks" / stack / phase.removeprefix("after-"))
    if role == "preflight":
        source_path = None  # A current scaffold is not proof of a past preflight's bytes.
    source_hash = first(snapshot.get("sha256"), facts.get("source_sha256"),
                        facts.get("source_tree_sha256"), facts.get("scaffold_sha256"))
    if source_hash is None and role == "reference":
        source_hash = read(base / "production.json").get("reference_source_tree_sha256")
    if role == "diagnostic" and isinstance(facts.get("source"), str):
        source_path = existing(ROOT / facts["source"])
    return {
        "record": record, "results": rel(base), "role": role, "series": series, "protocol": protocol,
        "stack": stack, "phase": phase,
        "model": agent.get("model"), "reasoning": agent.get("reasoning"),
        "cli": tool if isinstance(tool, str) and "codex" in tool.lower() else None,
        "condition": facts.get("condition"), "track": facts.get("track"),
        "started": first(data.get("started"), data.get("started_at"), data.get("created_at")),
        "coding_exit": data.get("exit") if role == "measured-coding" else None,
        "prompt": {"sha256": prompt_hash, "path": prompts.get(prompt_hash)},
        "fixture": {"sha256": fixture_hash, "path": fixtures.get(fixture_hash),
                    "base_sha256": facts.get("base_fixture_sha256"),
                    "effective_sha256": effective_hash,
                    "effective_record": (existing(base / "effective-fixture.json") if effective else
                                         record if data.get("effective_fixture_sha256") else None)},
        "source": {"sha256": source_hash, "path": source_path,
                   "manifest": existing(base / "source-snapshot.json") if snapshot else None,
                   "inventory": existing(base / "source-files.json") if role != "preflight" else None},
        "images": {"toolchain": first(facts.get("toolchain_image_id"), facts.get("toolchain_image_sha256")),
                   "browser": first(facts.get("browser_image_id"), facts.get("browser_image_sha256"))},
        "parent": {"session": data.get("parent_session"),
                   "source_sha256": data.get("parent_source_sha256")},
        "gates": gates(base, record, data, role, legacy),
        "evidence": [rel(p) for p in (base / "prepared.json", base / "reference.json",
                                     base / "change-summary.json", base / "isolation.json") if p.is_file()],
    }


def build_index() -> dict:
    prompts, fixtures = identity_links()
    entries = []
    for path in sorted(ROOT.glob("stacks/*/runs.json")):
        for i, data in enumerate(read(path)):
            role = "reader" if data.get("kind") == "comprehension" else "measured-coding"
            entries.append(make_record(path, data, role, prompts, fixtures, f"#/{i}"))
    result_root = ROOT / "results"
    for path in sorted(result_root.rglob("run.json")):
        if "source" in path.relative_to(result_root).parts:
            continue
        parts = path.relative_to(result_root).parts
        role = ("reader" if "comprehension" in parts else
                "preflight" if any(part.startswith("preflight") for part in parts) else
                "diagnostic" if parts[0] == "ruby-compile" or
                parts[:2] == ("one-shot-ihp", "guided") else "measured-coding")
        entries.append(make_record(path, read(path), role, prompts, fixtures))
    for path in sorted(result_root.rglob("preflight.json")):
        if "source" not in path.relative_to(result_root).parts:
            entries.append(make_record(path, read(path), "preflight", prompts, fixtures))
    # Older references have validation files instead of reference.json.
    for base in sorted(result_root.rglob("reference-*")):
        if not base.is_dir() or not re.fullmatch(r"reference-\d+", base.name):
            continue
        path = next((base / name for name in ("reference.json", "validation.json",
                     "source-snapshot.json", "production.json") if (base / name).is_file()), None)
        if path:
            entries.append(make_record(path, read(path), "reference", prompts, fixtures))
    entries.sort(key=lambda entry: entry["record"])
    return {
        "schema_version": 1,
        "generated_by": "tools/cohort_index.py",
        "scope": "Recorded coding sessions, readers, preflights, reference repairs and run.json diagnostics; not individual runtime trials or every check attempt.",
        "unknown": "null means not recorded or no matching published link; it never means equality with another null.",
        "classification": "Role, series, protocol and missing stack labels use repository paths; model, reasoning and CLI come only from the run record.",
        "counts_by_role": dict(sorted(Counter(entry["role"] for entry in entries).items())),
        "entries": entries,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Check the saved index without writing")
    args = parser.parse_args()
    output = ROOT / "results/cohorts.json"
    rendered = json.dumps(build_index(), indent=2) + "\n"
    if args.check:
        if not output.is_file() or output.read_text() != rendered:
            raise SystemExit("Cohort index is stale; run python3 tools/cohort_index.py")
        print("Cohort index matches recorded metadata")
    else:
        output.write_text(rendered)
        print(f"Wrote {rel(output)}")


if __name__ == "__main__":
    main()
