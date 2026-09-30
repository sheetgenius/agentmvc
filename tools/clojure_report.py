"""Render the Clojure overview from published records, without running workloads."""
import re
from pathlib import Path

import lane_report as report

ROOT = report.ROOT
OUT = ROOT / "results/lanes/clojure"


def result(folder):
    size, proof, snapshot = (report.read(folder / name) for name in
                             ("size.json", "verification.json", "source-snapshot.json"))
    if not all((size, proof, snapshot)):
        return None
    if proof.get("source_sha256") != snapshot["sha256"]:
        raise RuntimeError(f"Verification/source identity mismatch: {folder}")
    return {"folder": folder, "size": size, "verification": proof, "snapshot": snapshot,
            "run": report.read(folder / "run.json")}


def review_cell(row):
    for name in ("results.json", "share-boundary.json"):
        path = row["folder"] / "reviewer-parity" / name
        proof = report.read(path)
        if proof and proof.get("source_sha256") != row["snapshot"]["sha256"]:
            raise RuntimeError(f"Reviewer/source identity mismatch: {path}")
    return report.review_cell(row["folder"])


def runtime_table(condition, sources, heading):
    summary = report.read(OUT / "runtime" / condition / "summary.json")
    if summary:
        known = {row["session"]: row for row in sources}
        for session, identity in summary.get("applications", {}).items():
            row = known.get(session)
            if row is None:
                continue  # The shared renderer labels unknown sources as identity mismatches.
            parity = report.read(row["folder"] / "reviewer-parity/results.json")
            if (identity.get("source_sha256") != row["snapshot"]["sha256"] or not parity
                    or parity.get("source_sha256") != identity.get("source_sha256")
                    or not parity.get("image_sha256")
                    or parity["image_sha256"] != identity.get("image_sha256")):
                raise RuntimeError(f"Runtime/reviewer identity mismatch: {session}")
    return report.runtime_table(condition, sources, heading)


def main():
    report.OUT = OUT
    phases = {phase: result(OUT / phase) for phase in report.PHASES}
    one_shot = result(ROOT / "results/one-shot-v2-clojure-expert/pilot-1")
    completed = sum(bool(row and row["verification"].get("passed"))
                    for row in [*phases.values(), one_shot])
    preflight = report.read(OUT / "preflight.json")
    status = (f"**{completed}/9 coding sessions independently verified.**" if completed else
              "**Environment preflight passed; measured coding has not completed a verified session.**"
              if preflight and preflight.get("passed") else
              "**Environment preparation in progress. No measured coding result is available yet.**")
    lines = ["# Clojure", "",
             "An eight-step build and an independent expert one-shot of the same Conduit backend. "
             "The selected stack combines Ring/Jetty, Reitit/Malli, next.jdbc/HoneySQL, "
             "Integrant, Migratus, Proletarian and Buddy, packaged as a JVM AOT uberjar.", "",
             status, "",
             "[Stack choice and Clojure guidance](../../../stacks/clojure/SELECTION.md) · "
             "[Conditions and method](METHODOLOGY.md) · "
             "[Shared expert prompt](../../../one-shot-v2-expert/PROMPT.md)", "",
             "## Eight-step history", "",
             "Each checkpoint preserves its source, prompt, effort, failures and independent verdict. "
             "Production checks begin at step 3. Preparation and later reviewer work are outside coding effort.", "",
             "| Step | Owned backend and independent checks |",
             "| --- | --- |"]
    for number, (phase, label) in enumerate(zip(report.PHASES, report.NAMES), 1):
        lines.append(f"| {report.link(ROOT / 'steps' / (phase + '.md'), f'{number} · {label}')} | "
                     f"{report.cell(phases[phase])} |")
    lines += ["", "## Independent expert one-shot", "", report.cell(one_shot), ""]

    finals = [("Eight-step final", phases["8-live-editing"]), ("Expert one-shot", one_shot)]
    finals = [(label, row) for label, row in finals if row]
    originals, references = [], []
    if finals:
        lines += ["## Full-product sources", "",
                  "| Original source | Owned / whole backend tokens | Coding minutes | Uncached + output tokens | Reviewer checks |",
                  "| --- | ---: | ---: | ---: | --- |"]
        for label, row in finals:
            sessions = list(phases.values()) if label == "Eight-step final" else [row]
            runs = [item["run"] for item in sessions if item and item["run"]]
            complete = len(runs) == len(sessions)
            minutes = f'{sum(run["seconds"] for run in runs) / 60:.1f}' if complete else "Pending"
            effort = f'{sum(run["tokens"]["uncached_plus_output"] for run in runs):,}' if complete else "Pending"
            size = row["size"]
            lines.append(f'| {report.link(ROOT / row["snapshot"]["path"], label)} | '
                         f'{size["owned_tokens"]:,} / {size["tokens"]:,} | {minutes} | {effort} | '
                         f'{review_cell(row)} |')
            if row["run"]:
                originals.append({**row, "session": row["run"]["id"], "label": label})
            for folder in sorted(row["folder"].glob("reference-*")):
                match = re.fullmatch(r"reference-(\d+)", folder.name)
                candidate = result(folder) if match else None
                identity = report.read(folder / "reference.json") if candidate else None
                if candidate and candidate["verification"].get("passed") and identity:
                    references.append({**candidate, "session": identity["session"],
                                       "label": f"{label} · reference {match[1]}"})
        lines += runtime_table("measured", originals, "Repeated original runtime")
    if references:
        lines += ["", "## Reviewed references", "",
                  "These independently checked repairs preserve their measured parents and earlier attempts. "
                  "Their editing effort is unscored; supplemental review is shown separately.", "",
                  "| Source | Owned backend tokens | Reviewer checks |", "| --- | ---: | --- |"]
        for row in references:
            lines.append(f'| {report.link(ROOT / row["snapshot"]["path"], row["label"])} | '
                         f'{row["size"]["owned_tokens"]:,} | {review_cell(row)} |')
        lines += runtime_table("reference", references, "Repeated reference runtime")

    lines += ["", "## Evidence and limits", "",
              "Backend size excludes dependencies, compiled output, tests and Markdown; tests/docs are recorded "
              "separately. Owned size uses the frozen prepared scaffold as its baseline. This focused library "
              "assembly is not a Rails-style integrated model framework.", "",
              "AOT compiles application namespaces to JVM bytecode. JVM JIT warmup still matters; the common "
              "short performance windows do not establish fully warmed steady-state performance or a language ranking.", ""]
    if preflight:
        lines.append("[Environment preflight and its actual verdict](preflight.json)")
    for phase in ("1-build", "6-polish"):
        folder = OUT / "comprehension" / f"clojure-after-{phase}"
        grades = report.read(folder / "grades.json")
        if grades:
            lines += ["", report.link(folder, f'Comprehension after {phase}: '
                                       f'{grades["score"]}/{grades["maximum"]}')]
    manifests = sorted(OUT.glob("artifacts-*.json"))
    for manifest in manifests:
        data = report.read(manifest)
        publication = data.get("publication", {})
        if publication.get("release_url"):
            lines += ["", f'[Scrubbed transcripts and raw measurements]({publication["release_url"]}) · '
                      f'{report.link(manifest, "Artifact hashes and provenance")}. Full evidence stays outside Git.']
    if finals:
        lines += ["", "Try a measured final app from the repository root (Docker and Node.js required):", "",
                  "```sh", "tools/lane_demo.sh clojure eight", "tools/lane_demo.sh clojure one-shot", "```", ""]
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "README.md").write_text("\n".join(lines) + "\n")
    print(f"Clojure overview: {completed}/9 independently verified")


if __name__ == "__main__":
    main()
