"""Validate/export/package only the new Clojure lane's published evidence.

Commands match lane_artifacts.py: inspect, export-feedback, export-checks,
package VERSION, verify VERSION. Packaging reuses its decoded scrub checks,
raw-stream validators, deterministic tar writer and archive member hashes.
No workload is run and nothing is uploaded. Original evidence requires nine
coding transcripts, two graded readers and 72 repeated-runtime raw streams.
References are optional; the reference runtime names any promoted repairs.
"""
import argparse
import json
import re
import subprocess
import tempfile
from datetime import datetime
from pathlib import Path

import lane_artifacts as artifacts
import lane_check
import lane_run

ROOT = artifacts.ROOT
OUT = ROOT / "results/lanes/clojure"
ONESHOT = ROOT / "results/one-shot-v2-clojure-expert"
WORK = ROOT / ".work/clojure-artifacts"
PHASES = tuple(lane_run.workdir.step_name(n) for n in range(1, 9))
FINALS = {"clojure-8-live-editing-1": OUT / PHASES[-1],
          "clojure-one-shot-1": ONESHOT / "pilot-1"}
_collect = artifacts.collect


def install():
    artifacts.OUT, artifacts.WORK = OUT, WORK
    artifacts.SOURCES = (OUT, ONESHOT)
    artifacts.runtime_finished = runtime_finished


def read(path):
    return json.loads(path.read_text()) if path.is_file() else {}


def scoped_session(descriptor):
    """Refuse cross-cohort output paths even in a Clojure-named descriptor."""
    artifacts.relative(descriptor)
    session = read(descriptor)
    label = "|".join(re.escape(phase) for phase in (*PHASES, "one-shot"))
    match = re.fullmatch(rf"clojure-({label})-(1|reference-[1-9][0-9]*)", session.get("id", ""))
    if session.get("stack") != "clojure" or not match:
        raise RuntimeError("Artifact export requires a Clojure session identity")
    base = ROOT / ".work/lanes" / session["id"]
    if descriptor != base / "control/session.json":
        raise RuntimeError("Session descriptor path disagrees with its identity")
    for key, name in (("work", "app"), ("home", "home"), ("logs", "logs"), ("control", "control")):
        if Path(session[key]) != base / name:
            raise RuntimeError(f"Clojure {key} is outside its session directory")
    phase, revision = match.groups()
    result = ONESHOT / "pilot-1" if phase == "one-shot" else OUT / phase
    if revision != "1":
        result /= revision
    if (Path(session["result"]) != result
            or session["phase"] != (phase if revision == "1" else "reference")):
        raise RuntimeError("Clojure result path or phase is outside its allowed cohort")
    artifacts.relative(result)
    return session


def sessions():
    return [(path, scoped_session(path)) for path in
            sorted((ROOT / ".work/lanes").glob("clojure-*/control/session.json"))]


def export_feedback():
    install()
    artifacts.require_coding_stopped()
    cleaner, exported = artifacts.checker(), []
    for descriptor, session in sessions():
        for attempt in sorted((Path(session["logs"]) / "measurements").glob("*")):
            if attempt.is_dir():
                exported.append(artifacts.export_feedback_attempt(attempt, cleaner))
    return {"feedback_attempts": exported,
            "publication_status": "Clojure feedback exported locally; no uploads or workload runs"}


def check_sources(session):
    control, logs = Path(session["control"]), Path(session["logs"])
    selections = ((control, ("*.log", "*focused*.json", "requests.jsonl")),
                  (control / "independent-attempts", ("**/*.log",)),
                  (logs, ("*.log",)),
                  (logs / "independent", ("*.log", "*.json")),
                  (logs / "broker", ("*.log", "requests.jsonl")),
                  (logs / "security-scans", ("*.json",)))
    return sorted({path for folder, patterns in selections for pattern in patterns
                   for path in folder.glob(pattern) if path.is_file()})


def export_checks():
    """Retain original and reference check failures, including broker feedback."""
    install()
    artifacts.require_coding_stopped()
    cleaner, exported = artifacts.checker(), []
    for descriptor, session in sessions():
        sources = check_sources(session)
        result = Path(session["result"])
        metadata = [path for path in (result / "verification.json", result / "source-snapshot.json")
                    if path.is_file()]
        originals = {artifacts.relative(path): artifacts.raw_validation.digest(path)
                     for path in [descriptor, *metadata, *sources]}
        dest = result / "check-logs" / lane_run.fingerprint(originals)[:16]
        if dest.exists():
            record = read(dest / "results.json")
            if record.get("original_file_sha256") != originals:
                raise RuntimeError("Preserving check export with a different original inventory")
            for name, sha in record["export_file_sha256"].items():
                if Path(name).name != name or artifacts.raw_validation.digest(dest / name) != sha:
                    raise RuntimeError("Check export path or checksum changed")
                artifacts.validate_file(dest / name, cleaner)
            exported.append(artifacts.relative(dest))
            continue
        WORK.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix="checks-", dir=WORK) as temporary:
            staging = Path(temporary) / "published"
            staging.mkdir()
            for source in sources:
                name = str(source.relative_to(descriptor.parents[1])).replace("/", "--")
                if source.suffix == ".jsonl":
                    value = [json.loads(line) for line in source.read_text().splitlines() if line.strip()]
                    artifacts.save_scrubbed_json(staging / (name.removesuffix(".jsonl") + ".json"), value, cleaner)
                elif source.suffix == ".json":
                    artifacts.save_scrubbed_json(staging / name, read(source), cleaner)
                else:
                    plain = Path(temporary) / name
                    plain.write_text(cleaner.text(source.read_text()))
                    artifacts.validate_file(plain, cleaner)
                    compressed = staging / (name + ".zst")
                    subprocess.run(["zstd", "-q", "-T2", "-o", str(compressed), str(plain)], check=True)
                    artifacts.validate_file(compressed, cleaner)
            record = {"session": session["id"], "stack": "clojure", "phase": session["phase"],
                      "condition": "Clojure check-log publication; failures retained",
                      "source_sha256": read(result / "source-snapshot.json").get("sha256"),
                      "original_file_sha256": originals,
                      "export_file_sha256": {path.name: artifacts.raw_validation.digest(path)
                                             for path in staging.iterdir()},
                      "exported_at": lane_run.stamp(),
                      "scope": "Control, independent, broker and security check evidence; JSONL decoded to arrays",
                      "export_tools_sha256": tool_hashes()}
            artifacts.save_scrubbed_json(staging / "results.json", record, cleaner)
            artifacts.require_coding_stopped()
            if any(artifacts.raw_validation.digest(ROOT / name) != sha for name, sha in originals.items()):
                raise RuntimeError("Clojure check evidence changed during export")
            dest.parent.mkdir(parents=True, exist_ok=True)
            staging.rename(dest)
        exported.append(artifacts.relative(dest))
    return {"exported": exported, "publication_status": "Clojure check logs exported locally; no uploads"}


def original_results():
    return {**{f"clojure-{phase}-1": OUT / phase for phase in PHASES},
            "clojure-one-shot-1": ONESHOT / "pilot-1"}


def references():
    found = {}
    for base in FINALS.values():
        for folder in sorted(base.glob("reference-*")):
            record = read(folder / "reference.json")
            if record:
                sid = record.get("session", "")
                suffix = folder.name.removeprefix("reference-")
                original = next(sid for sid, path in FINALS.items() if path == base)
                if not suffix.isdigit() or sid != original.removesuffix("-1") + "-reference-" + suffix:
                    raise RuntimeError("Reference identity differs from its Clojure result path")
                found[sid] = folder
    return found


def raw_paths(condition, identities):
    return {artifacts.relative(OUT / "runtime" / condition / sid / f"round{number}/http" /
                               f"raw-{prefix}{scenario}.json.zst")
            for sid in identities for number in (1, 2) for prefix in ("", "warmup-")
            for scenario in lane_check.SCENARIOS}


def runtime_finished(condition):
    base = OUT / "runtime" / condition
    summary = read(base / "summary.json")
    applications, records = summary.get("applications", {}), summary.get("records", [])
    allowed = FINALS if condition == "measured" else references()
    if (not summary.get("finished") or summary.get("condition") != condition or not applications
            or not set(applications).issubset(allowed)
            or condition == "measured" and set(applications) != set(FINALS)):
        return False
    expected = {(sid, number, kind) for sid in applications for number in (1, 2) for kind in ("http", "socket")}
    if len(records) != len(expected) or {(row.get("session"), row.get("round"), row.get("kind"))
                                       for row in records} != expected:
        return False
    for row in records:
        expected_path = f"{row['session']}/round{row['round']}/{row['kind']}"
        if row.get("path") != expected_path:
            return False
        data = read(base / expected_path / "results.json")
        identity = applications[row["session"]]
        if (identity.get("source_sha256") != verified_source(allowed[row["session"]])
                or not identity.get("image_sha256") or not data.get("finished")
                or data.get("session") != row["session"] or data.get("round") != row["round"]
                or type(data.get("exit")) is not int or type(data.get("passed")) is not bool
                or any(data.get(key) != identity.get(key)
                                           for key in ("source_sha256", "image_sha256"))):
            return False
        if row["kind"] == "http":
            expected_names = {f"raw-{prefix}{name}.json.zst" for prefix in ("", "warmup-")
                              for name in lane_check.SCENARIOS}
            scenarios = data.get("scenarios", {})
            if (set(data.get("raw_stream_sha256", {})) != expected_names
                    or set(scenarios) != set(lane_check.SCENARIOS)
                    or any(item.get("requests", 0) <= 0 or "failed_checks" not in item for item in scenarios.values())
                    or (data.get("vus"), data.get("warmup"), data.get("duration")) != (16, "3s", "15s")
                    or data.get("limits") != lane_check.LIMITS):
                return False
        else:
            scenarios = data.get("scenarios", [])
            if ([item.get("subscribers") for item in scenarios] != [10, 100, 500]
                    or any(item.get("saves") != 20 or not all(key in item for key in
                           ("missing", "duplicate_revisions", "regressed_revisions")) for item in scenarios)):
                return False
        if condition == "reference" and not data["passed"]:
            return False
    return condition != "reference" or summary.get("passed") is True


def verified_source(folder):
    proof, snapshot = read(folder / "verification.json"), read(folder / "source-snapshot.json")
    if (not snapshot or lane_run.fingerprint(snapshot.get("files", {})) != snapshot.get("sha256")
            or not proof.get("passed") or proof.get("source_sha256") != snapshot["sha256"]):
        return None
    expected = ROOT / "stacks/clojure" / folder.name if folder.parent == OUT else folder / "source"
    source = ROOT / snapshot.get("path", "")
    if source != expected or not source.is_dir():
        return None
    artifacts.relative(source)
    actual = {str(path.relative_to(source)): artifacts.raw_validation.digest(path)
              for path in lane_run.checked_files(source)}
    return snapshot["sha256"] if actual == snapshot["files"] else None


def reviewed(folder):
    source = verified_source(folder)
    parity, share = (read(folder / "reviewer-parity" / name) for name in ("results.json", "share-boundary.json"))
    return bool(source and parity.get("passed") and share.get("passed")
                and parity.get("source_sha256") == share.get("source_sha256") == source)


def reader_graded(phase):
    folder = OUT / "comprehension" / f"clojure-after-{phase}"
    records = [read(folder / name) for name in
               ("run.json", "prepared.json", "started.json", "grades.json", "key-preparation.json", "isolation.json")]
    if not all(records) or not all((folder / name).is_file() for name in ("answer.md", "answer-key.md")):
        return False
    run, prepared, started, grades, key, isolation = records
    source = verified_source(OUT / phase)
    answer_sha, key_sha = (artifacts.raw_validation.digest(folder / name) for name in ("answer.md", "answer-key.md"))
    try:
        timestamps = [datetime.fromisoformat(value) for value in
                      (key["saved_at"], run["started"], run["finished"], grades["graded_at"])]
        items = grades["items"]
        return bool(source and run.get("exit") == 0 and run.get("source_unchanged") is True
                    and isolation.get("passed") is True and key.get("reader_answers_consulted") is False
                    and all(record.get("source_sha256") == source for record in (run, prepared, started, grades))
                    and key.get("source_snapshot_sha256") == source
                    and run.get("readable_source_sha256") == prepared.get("readable_source_sha256")
                    and grades.get("answer_sha256") == answer_sha
                    and grades.get("answer_key_sha256") == key.get("answer_key_sha256") == key_sha
                    and run.get("answer_key_sha256_before_reader") == started.get("answer_key_sha256_before_reader") == key_sha
                    and grades.get("answer_key_saved_at") == key["saved_at"]
                    and grades.get("reader_started_at") == started.get("started") == run["started"]
                    and timestamps == sorted(timestamps) and timestamps[0] < timestamps[1]
                    and sorted(item["question"] for item in items) == list(range(1, 13))
                    and all(item["score"] in (0, .5, 1) and item.get("source") and item.get("reason") for item in items)
                    and grades.get("maximum") == 12 and grades.get("score") == sum(item["score"] for item in items))
    except (KeyError, TypeError, ValueError):
        return False


def completion():
    originals, repairs = original_results(), references()
    verified = {}
    for sid, folder in originals.items():
        run, proof, isolation = (read(folder / name) for name in ("run.json", "verification.json", "isolation.json"))
        phase = "one-shot" if sid == "clojure-one-shot-1" else sid.removeprefix("clojure-").removesuffix("-1")
        required = {"development"} | ({"production"} if phase == "one-shot" or int(phase[0]) >= 3 else set())
        verified[sid] = bool(verified_source(folder) and run.get("id") == sid and run.get("finished")
                             and run.get("condition") == "prepared-clojure" and isolation.get("passed")
                             and all(proof.get("checks", {}).get(action) == 0 for action in required))
    readers = {phase: reader_graded(phase) for phase in (PHASES[0], PHASES[5])}
    promoted = read(OUT / "runtime/reference/summary.json").get("applications", {})
    selected = {}
    for original, folder in FINALS.items():
        candidates = [sid for sid in promoted if sid in repairs and repairs[sid].parent == folder and reviewed(repairs[sid])]
        sid = max(candidates, key=lambda name: int(name.rsplit("-", 1)[1])) if candidates else original
        selected[original] = {"session": sid, "reviewer_passed": reviewed(repairs[sid] if sid in repairs else folder)}
    promoted_ready = all(sid in repairs and reviewed(repairs[sid]) for sid in promoted)
    return {"independent_checks": verified, "graded_readers": readers, "selected_finals": selected,
            "selected_references": sorted(promoted),
            "ready": all(verified.values()) and all(readers.values()) and promoted_ready
                     and all(row["reviewer_passed"] for row in selected.values())
                     and runtime_finished("measured") and (not promoted or runtime_finished("reference"))}


def collect():
    install()
    data = _collect()
    transcripts = {row["path"] for row in data["files"]["transcripts"] if row["path"].endswith(".jsonl")}
    coding = {artifacts.relative(folder / "transcript.jsonl") for folder in original_results().values()}
    readers = {artifacts.relative(OUT / "comprehension" / f"clojure-after-{phase}" / "transcript.jsonl")
               for phase in (PHASES[0], PHASES[5])}
    raw = {row["path"] for row in data["files"]["runtime"]}
    measured = raw_paths("measured", FINALS)
    promoted = read(OUT / "runtime/reference/summary.json").get("applications", {})
    reference = raw_paths("reference", promoted)
    readiness = completion()
    data["coverage"] = {"coding_transcripts": len(transcripts & coding), "reader_transcripts": len(transcripts & readers),
                        "measured_raw_streams": len(raw & measured), "reference_raw_streams": len(raw & reference),
                        "additional_transcripts": sorted(transcripts - coding - readers),
                        "additional_runtime_streams": len(raw - measured - reference),
                        "expected_originals": {"coding_transcripts": 9, "reader_transcripts": 2, "measured_raw_streams": 72},
                        "original_inventory_complete": coding.issubset(transcripts) and readers.issubset(transcripts) and measured.issubset(raw),
                        "reference_inventory_complete": not promoted or reference.issubset(raw) and runtime_finished("reference"),
                        "runtime_finished": {condition: runtime_finished(condition) for condition in ("measured", "reference")},
                        "check_logs": sum(row["path"].endswith(".log.zst") for row in data["files"]["evidence"]),
                        "completion": readiness}
    return data


def tool_hashes():
    return {f"tools/{name}": artifacts.raw_validation.digest(ROOT / "tools" / name) for name in
            ("clojure_artifacts.py", "lane_artifacts.py", "lane_continue.py", "scrub.py", "v2_expert_symmetry_validate.py")}


def package(version):
    install()
    if not isinstance(version, str) or not re.fullmatch(r"[a-z0-9][a-z0-9._-]{0,55}", version):
        raise ValueError("Use a short lowercase artifact version, for example v1")
    artifacts.require_coding_stopped()
    manifest_path, work = OUT / f"artifacts-{version}.json", WORK / version
    if manifest_path.exists() or work.exists():
        raise RuntimeError("Preserving existing artifact version; select a new version")
    if not completion()["ready"]:
        raise RuntimeError("Complete nine coding gates, two graded readers and selected final reviewer/runtime evidence first")
    export_feedback()
    export_checks()
    data = collect()
    if not (data["coverage"]["original_inventory_complete"] and data["coverage"]["reference_inventory_complete"]
            and data["coverage"]["completion"]["ready"]):
        raise RuntimeError("Clojure release evidence is incomplete; inspect the inventory")
    work.mkdir(parents=True)
    assets = {kind: artifacts.create_archive(work / f"agentmvc-clojure-{version}-{kind}.tar.zst", rows)
              for kind, rows in data["files"].items() if rows}
    manifest = {"schema_version": 1, "artifact_version": version, "created_at": lane_run.stamp(),
                "publication_status": "prepared locally; not uploaded", "restore_root": "repository root",
                "snapshot_status": "complete Clojure original inventory; selected references optional",
                "validation": "Unchanged decoded scrub patterns, raw zstd validation and archive member hashes",
                "tools_sha256": tool_hashes(), "assets": assets, **data}
    artifacts.validate_value(manifest, artifacts.checker())
    with manifest_path.open("x") as stream:
        stream.write(json.dumps(manifest, indent=2) + "\n")
    return manifest


def main():
    install()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("inspect", "export-feedback", "export-checks", "package", "verify"))
    parser.add_argument("version", nargs="?")
    args = parser.parse_args()
    if args.action in ("package", "verify") and (not args.version or not re.fullmatch(r"[a-z0-9][a-z0-9._-]{0,55}", args.version)):
        parser.error("Provide a short lowercase artifact version, for example v1")
    if args.action in ("export-feedback", "export-checks"):
        print(json.dumps(export_feedback() if args.action == "export-feedback" else export_checks(), indent=2))
        return
    result = collect() if args.action == "inspect" else package(args.version) if args.action == "package" else artifacts.verify(args.version)
    print(json.dumps({"coverage": result["coverage"], "assets": result.get("assets", {}),
                      "publication_status": result.get("publication_status", "validation only; no archives written")}, indent=2))


if __name__ == "__main__":
    main()
