"""Package published lane evidence for external release; never uploads anything.

  .venv/bin/python tools/lane_artifacts.py inspect
  .venv/bin/python tools/lane_artifacts.py export-feedback
  .venv/bin/python tools/lane_artifacts.py export-checks
  .venv/bin/python tools/lane_artifacts.py package VERSION
  .venv/bin/python tools/lane_artifacts.py verify VERSION

Like archive_raw.py, keep assets in .work and only checksums/provenance in Git.
Archives restore repository-relative paths. Packaging requires the 18 original
coding transcripts, four readers, and finished measured/reference runtimes
with 144 raw streams each. Existing versions survive; reference diagnostics
and all short feedback streams are retained separately from original counts.
"""
import argparse
import hashlib
import json
import re
import subprocess
import tarfile
import tempfile
from functools import lru_cache
from pathlib import Path, PurePosixPath

import lane_broker
import lane_check
import lane_continue
import scrub
import v2_expert_symmetry_validate as raw_validation

ROOT = lane_broker.ROOT
OUT = ROOT / "results/lanes"
WORK = ROOT / ".work/lane-artifacts"
SOURCES = (OUT, ROOT / "results/one-shot-v2-go-expert", ROOT / "results/one-shot-v2-python-expert")
PROVENANCE_KEYS = ("session", "id", "stack", "phase", "condition", "round", "source_sha256", "image_sha256",
                   "fixture_sha256", "prompt_sha256", "readable_source_sha256", "exit", "passed", "started", "finished")


def relative(path):
    path = Path(path).absolute()
    if path.resolve() != path or not path.is_relative_to(ROOT):
        raise RuntimeError("Artifact sources must be non-symlink files inside the repository")
    return str(path.relative_to(ROOT))


def checker():
    # Use the unchanged scrub patterns and any locally available exact broker
    # tokens; never copy coordinator descriptors or credentials into a bundle.
    tokens = [re.escape(path.read_text().strip()) for path in
              (ROOT / ".work/lanes").glob("*/control/token") if path.read_text().strip()]
    cleaner = scrub.Scrubber(ROOT, tokens)
    # Metric keys, route labels and units repeat millions of times. Cache only
    # this immutable cleaner's exact string results; no rule or check is skipped.
    cleaner.text = lru_cache(maxsize=16384)(cleaner.text)
    cleaner.leaks = lru_cache(maxsize=16384)(cleaner.leaks)
    return cleaner


def validate_value(value, cleaner):
    hits = {hit for text in lane_continue.strings(value) for hit in cleaner.leaks(text)}
    if hits:
        raise RuntimeError(f"Sensitive decoded JSON string/key: {sorted(hits)}")


def validate_lines(stream, cleaner, allow_empty=False):
    count = 0
    for line in stream:
        if line.strip():
            value = json.loads(line)
            validate_value(value, cleaner)
            count += 1
    if not count and not allow_empty:
        raise RuntimeError("Empty JSONL evidence")
    return count


def validate_file(path, cleaner, allow_empty=False):
    relative(path)
    if path.name.endswith(".json.zst"):
        size, hits = raw_validation.inspect(path)
        if hits:
            raise RuntimeError(f"Sensitive raw-stream markers: {hits}")
        proc = subprocess.Popen(["zstd", "-dc", str(path)], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        try:
            count = validate_lines(proc.stdout, cleaner, allow_empty)
        except BaseException:
            proc.kill()
            proc.wait()
            raise
        finally:
            proc.stdout.close()
        error = proc.stderr.read()
        if proc.wait():
            raise RuntimeError(f"Invalid zstd stream: {error[-200:]!r}")
        return {"decompressed_bytes": size, "jsonl_records": count}
    if path.name.endswith(".log.zst"):
        text = subprocess.check_output(["zstd", "-dc", str(path)]).decode()
        if cleaner.leaks(text):
            raise RuntimeError(f"Sensitive compressed log: {relative(path)}")
        return {"decompressed_bytes": len(text.encode())}
    if path.suffix == ".jsonl":
        with path.open() as stream:
            return {"jsonl_records": validate_lines(stream, cleaner)}
    text = path.read_text()
    if path.suffix == ".json":
        validate_value(json.loads(text), cleaner)
    elif cleaner.leaks(text):
        raise RuntimeError(f"Sensitive Markdown/plaintext: {relative(path)}")
    return {}


def provenance(path, records, cleaner):
    candidates = ([path] if path.suffix == ".json" else [])
    candidates += [path.with_suffix(".json")]
    candidates += [path.parent / name for name in ("run.json", "results.json", "prepared.json", "reference.json", "verification.json")]
    record = next((item for item in candidates if item.is_file()), None)
    if record is None:
        if path.suffix in (".md", ".log"):
            return None  # General documentation has a content hash, not a run identity.
        raise RuntimeError(f"No published provenance for {relative(path)}")
    name = relative(record)
    if name not in records:
        data = json.loads(record.read_text())
        validate_value(data, cleaner)
        records[name] = {"sha256": raw_validation.digest(record),
                         **{key: data[key] for key in PROVENANCE_KEYS if key in data}}
        companions = {}
        for filename in ("verification.json", "isolation.json", "grades.json", "source-snapshot.json",
                         "publication-adapter.json", "reference.json", "share-boundary.json"):
            item = record.parent / filename
            if item.is_file():
                validate_file(item, cleaner)
                companions[relative(item)] = raw_validation.digest(item)
        records[name]["related_record_sha256"] = companions
    return name


def require_coding_stopped():
    if any((ROOT / ".work/lanes").glob("*/logs/active.json")):
        raise RuntimeError("Feedback export requires all measured coding sessions to stop (active.json exists)")


def save_scrubbed_json(path, value, cleaner):
    value = cleaner.value(value)
    validate_value(value, cleaner)
    text = json.dumps(value, indent=2) + "\n"
    if json.loads(text) != value:
        raise RuntimeError("JSON round-trip changed feedback evidence")
    path.write_text(text)
    validate_file(path, cleaner)


def export_feedback_attempt(attempt, cleaner):
    require_coding_stopped()
    relative(attempt)
    lane = attempt.parents[2]
    descriptor = lane / "control/session.json"
    relative(descriptor)
    session = json.loads(descriptor.read_text())
    if session["id"] != lane.name:
        raise RuntimeError("Feedback directory and source session disagree")
    selected = sorted({path for pattern in ("results.json", "runner.log", "k6-*.json", "raw-*.json")
                       for path in attempt.glob(pattern) if path.is_file()})
    originals = {relative(path): raw_validation.digest(path) for path in [descriptor, *selected]}
    dest = OUT / "runtime/feedback" / lane.name / attempt.name
    if dest.exists():
        record = json.loads((dest / "results.json").read_text())
        validate_value(record, cleaner)
        if record.get("original_file_sha256") != originals:
            raise RuntimeError(f"Preserving prior feedback export; originals differ: {relative(dest)}")
        for name, sha in record["export_file_sha256"].items():
            path = dest / name
            if raw_validation.digest(path) != sha:
                raise RuntimeError(f"Feedback export checksum changed: {relative(path)}")
            validate_file(path, cleaner, allow_empty=True)
        return {"path": relative(dest), "status": "existing export verified"}
    WORK.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="feedback-", dir=WORK) as temporary:
        staging = Path(temporary) / "published"
        staging.mkdir()
        raw_hashes, raw_validation_records = {}, {}
        for path in selected:
            if path.name == "results.json":
                continue
            if path.name.startswith("raw-"):
                plain = Path(temporary) / path.name
                with path.open() as source, plain.open("w") as target:
                    for line in source:
                        if line.strip():
                            value = cleaner.value(json.loads(line))
                            validate_value(value, cleaner)
                            target.write(json.dumps(value, ensure_ascii=False) + "\n")
                compressed = staging / (path.name + ".zst")
                subprocess.run(["zstd", "-q", "-T2", "-o", str(compressed), str(plain)], check=True)
                raw_validation_records[compressed.name] = validate_file(compressed, cleaner, allow_empty=True)
                raw_hashes[compressed.name] = raw_validation.digest(compressed)
            elif path.suffix == ".json":
                save_scrubbed_json(staging / path.name, json.loads(path.read_text()), cleaner)
            else:
                (staging / path.name).write_text(cleaner.text(path.read_text()))
                validate_file(staging / path.name, cleaner)
        summary = attempt / "results.json"
        record = json.loads(summary.read_text()) if summary.is_file() else {}
        record.pop("app_log_tail", None)
        record.update(schema_version=1, session=session["id"], stack=session["stack"], phase=session["phase"],
                      label=attempt.name, condition="short feedback benchmark", warmup="1s", duration="3s",
                      timing_basis="tools/lane_check.py benchmark configuration; an interrupted attempt may not finish",
                      source_identity="Intermediate candidate; no claim that the published checkpoint matches this measurement",
                      image_identity="recorded image SHA" if record.get("image_sha256") else "image SHA not recorded",
                      summary_present=summary.is_file(), runner_log_present=(attempt / "runner.log").is_file(),
                      source_session=relative(descriptor),
                      session_result=relative(Path(session["result"])),
                      fixture_sha256=session.get("fixture_sha256"),
                      original_file_sha256=originals, raw_stream_sha256=raw_hashes,
                      raw_validation=raw_validation_records,
                      export_file_sha256={path.name: raw_validation.digest(path) for path in sorted(staging.iterdir())},
                      exported_at=lane_broker.stamp(),
                      export_tools_sha256={f"tools/{name}": raw_validation.digest(ROOT / "tools" / name)
                                           for name in ("lane_artifacts.py", "lane_continue.py", "scrub.py",
                                                        "v2_expert_symmetry_validate.py")})
        save_scrubbed_json(staging / "results.json", record, cleaner)
        # Only validated exports become public. Originals, including seed.json,
        # stay in place; only the explicit evidence allowlist is copied.
        require_coding_stopped()
        if any(raw_validation.digest(ROOT / name) != sha for name, sha in originals.items()):
            raise RuntimeError("Feedback originals changed during export")
        dest.parent.mkdir(parents=True, exist_ok=True)
        staging.rename(dest)
    return {"path": relative(dest), "status": "exported", "raw_streams": len(raw_hashes)}


def export_feedback():
    require_coding_stopped()
    cleaner = checker()
    attempts = sorted(path for path in (ROOT / ".work/lanes").glob("*/logs/measurements/*") if path.is_dir())
    return {"feedback_attempts": [export_feedback_attempt(path, cleaner) for path in attempts],
            "publication_status": "scrubbed feedback exported locally; no uploads or workload runs"}


def export_checks():
    """Preserve completed reference check attempts, including failed gates."""
    require_coding_stopped()
    cleaner, exported, pending = checker(), [], []
    for descriptor in sorted((ROOT / ".work/lanes").glob("*/control/session.json")):
        session = json.loads(descriptor.read_text())
        if session["phase"] != "reference":
            continue
        result = Path(session["result"])
        verification, snapshot = result / "verification.json", result / "source-snapshot.json"
        if not verification.is_file() or not snapshot.is_file():
            pending.append(session["id"])
            continue
        proof, snapshot_record = json.loads(verification.read_text()), json.loads(snapshot.read_text())
        if proof.get("source_sha256") != snapshot_record["sha256"]:
            raise RuntimeError("Reference verification does not identify its published source")
        sources = sorted({path for directory, patterns in (
            (Path(session["control"]), ("*.log", "*focused*.json")),
            (Path(session["logs"]) / "independent", ("*.log", "*.json")))
            for pattern in patterns for path in directory.glob(pattern) if path.is_file()})
        originals = {relative(path): raw_validation.digest(path) for path in [verification, snapshot, *sources]}
        dest = result / "check-logs" / lane_continue.lane_run.fingerprint(originals)[:16]
        if dest.exists():
            record = json.loads((dest / "results.json").read_text())
            if record.get("original_file_sha256") != originals:
                raise RuntimeError("Preserving prior check-log export with a different inventory")
            for name, sha in record["export_file_sha256"].items():
                if raw_validation.digest(dest / name) != sha:
                    raise RuntimeError("Check-log export checksum changed")
                validate_file(dest / name, cleaner)
            exported.append(relative(dest))
            continue
        WORK.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix="checks-", dir=WORK) as temporary:
            staging = Path(temporary) / "published"
            staging.mkdir()
            for source_path in sources:
                name = ("control-" if source_path.parent == Path(session["control"]) else "independent-") + source_path.name
                if source_path.suffix == ".json":
                    save_scrubbed_json(staging / name, json.loads(source_path.read_text()), cleaner)
                else:
                    plain = Path(temporary) / name
                    plain.write_text(cleaner.text(source_path.read_text()))
                    validate_file(plain, cleaner)
                    compressed = staging / (name + ".zst")
                    subprocess.run(["zstd", "-q", "-T2", "-o", str(compressed), str(plain)], check=True)
                    validate_file(compressed, cleaner)
            record = {"session": session["id"], "condition": "reference check-log publication",
                      "source_sha256": snapshot_record["sha256"],
                      "verification": {"path": relative(verification), "record": proof},
                      "original_file_sha256": originals,
                      "export_file_sha256": {path.name: raw_validation.digest(path) for path in staging.iterdir()},
                      "exported_at": lane_broker.stamp(),
                      "scope": "Reference control and independent check evidence present after verification; originals preserved",
                      "export_tools_sha256": {Path(module.__file__).name: raw_validation.digest(Path(module.__file__))
                                              for module in (lane_continue, scrub, raw_validation)},
                      "exporter_sha256": raw_validation.digest(Path(__file__))}
            save_scrubbed_json(staging / "results.json", record, cleaner)
            if any(raw_validation.digest(ROOT / name) != sha for name, sha in originals.items()):
                raise RuntimeError("Reference check evidence changed during export")
            dest.parent.mkdir(parents=True, exist_ok=True)
            staging.rename(dest)
        exported.append(relative(dest))
    return {"exported": exported, "pending_verification": pending,
            "publication_status": "scrubbed reference check logs exported locally; not uploaded"}


def runtime_finished(condition):
    base = OUT / "runtime" / condition
    path = base / "summary.json"
    if not path.is_file():
        return False
    summary = json.loads(path.read_text())
    applications, records = summary.get("applications", {}), summary.get("records", [])
    expected = {(sid, number, kind) for sid in applications for number in (1, 2) for kind in ("http", "socket")}
    actual = {(row.get("session"), row.get("round"), row.get("kind")) for row in records}
    return bool(summary.get("finished") and summary.get("condition") == condition and len(applications) == 4
                and len(records) == 16 and actual == expected
                and all((base / row["path"] / "results.json").is_file() for row in records))


def artifact_paths():
    groups = {"transcripts": [], "runtime": [], "evidence": []}
    for base in SOURCES:
        for path in sorted(base.rglob("*transcript*.jsonl")):
            if "source" in path.relative_to(base).parts:
                continue
            markdown = path.with_suffix(".md")
            if not markdown.is_file():
                raise RuntimeError(f"Missing readable transcript: {relative(path)}")
            groups["transcripts"].extend((path, markdown))
        for path in sorted(base.rglob("*")):
            parts = path.relative_to(base).parts
            if (not path.is_file() or "source" in parts or "transcript" in path.name or
                    re.fullmatch(r"artifacts-.+\.json", path.name)):
                continue
            if path.suffix in (".json", ".md", ".log") or path.name.endswith(".log.zst"):
                groups["evidence"].append(path)
    groups["runtime"] = sorted((OUT / "runtime").rglob("raw-*.json.zst"))
    return groups


def collect():
    groups = artifact_paths()
    tracked = set(subprocess.check_output(["git", "ls-files", "-z", "--", *[relative(p) for p in SOURCES]],
                                          cwd=ROOT).decode().split("\0"))
    if any(relative(path) in tracked for path in groups["transcripts"]+groups["runtime"]
           +[path for path in groups["evidence"] if path.name.endswith(".log.zst")]):
        raise RuntimeError("Full lane transcripts/raw streams must remain outside Git")
    cleaner, records = checker(), {}
    entries = {}
    for kind, paths in groups.items():
        entries[kind] = []
        for path in paths:
            name = relative(path)
            validation = validate_file(path, cleaner, allow_empty=path.is_relative_to(OUT / "runtime/feedback"))
            sha = raw_validation.digest(path)
            source_record = provenance(path, records, cleaner)
            if kind == "runtime":
                data = json.loads((path.parent / "results.json").read_text())
                if data.get("raw_stream_sha256", {}).get(path.name) != sha:
                    raise RuntimeError(f"Raw stream does not match its runtime record: {name}")
            elif path.name.endswith(".log.zst"):
                data = json.loads((path.parent / "results.json").read_text())
                if data.get("export_file_sha256", {}).get(path.name) != sha:
                    raise RuntimeError(f"Check log does not match its publication record: {name}")
            entries[kind].append({"path": name, "bytes": path.stat().st_size, "sha256": sha,
                                  "provenance": source_record, **validation})
    step_name = lane_continue.lane_run.workdir.step_name
    coding_paths = {relative(OUT / stack / step_name(n) / "transcript.jsonl")
                    for stack in ("go", "python") for n in range(1, 9)}
    coding_paths.update(relative(ROOT / f"results/one-shot-v2-{stack}-expert/pilot-1/transcript.jsonl")
                        for stack in ("go", "python"))
    reader_paths = {relative(OUT / "comprehension" / f"{stack}-after-{step_name(n)}" / "transcript.jsonl")
                    for stack in ("go", "python") for n in (1, 6)}
    transcripts = {row["path"] for row in entries["transcripts"] if row["path"].endswith(".jsonl")}
    coding, readers = len(transcripts & coding_paths), len(transcripts & reader_paths)
    final_ids = {f"{stack}-{phase}-1" for stack in ("go", "python") for phase in (step_name(8), "one-shot")}
    raw_paths = {row["path"] for row in entries["runtime"]}
    original_raw = {relative(OUT / "runtime/measured" / sid / f"round{number}/http" /
                            f"raw-{prefix}{scenario}.json.zst") for sid in final_ids for number in (1, 2)
                    for prefix in ("", "warmup-") for scenario in lane_check.SCENARIOS}
    original_streams = len(raw_paths & original_raw)
    reference_summary = OUT / "runtime/reference/summary.json"
    reference_ids = json.loads(reference_summary.read_text()).get("applications", {}) if reference_summary.is_file() else {}
    reference_raw = {relative(OUT / "runtime/reference" / sid / f"round{number}/http" /
                             f"raw-{prefix}{scenario}.json.zst") for sid in reference_ids for number in (1, 2)
                     for prefix in ("", "warmup-") for scenario in lane_check.SCENARIOS}
    reference_streams = len(raw_paths & reference_raw)
    return {"files": entries, "provenance": records,
            "coverage": {"coding_transcripts": coding, "reader_transcripts": readers,
                         "measured_raw_streams": original_streams,
                         "additional_transcripts": sorted(transcripts - coding_paths - reader_paths),
                         "additional_runtime_streams": len(raw_paths - original_raw),
                         "reference_raw_streams": reference_streams,
                         "reference_inventory_complete": len(reference_ids) == 4 and reference_streams == 144,
                         "runtime_finished": {condition: runtime_finished(condition) for condition in ("measured", "reference")},
                         "reference_check_logs": sum(row['path'].endswith('.log.zst') for row in entries['evidence']),
                         "expected_originals": {"coding_transcripts": 18, "reader_transcripts": 4, "measured_raw_streams": 144},
                         "original_inventory_complete": coding == 18 and readers == 4 and original_streams == 144}}


def file_digest(stream):
    digest = hashlib.sha256()
    for block in iter(lambda: stream.read(1024 * 1024), b""):
        digest.update(block)
    return digest.hexdigest()


def verify_archive(path, expected):
    wanted = {row["path"]: row for row in expected}
    seen = set()
    process = subprocess.Popen(["zstd", "-dc", str(path)], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    try:
        with tarfile.open(fileobj=process.stdout, mode="r|") as archive:
            for member in archive:
                parts = PurePosixPath(member.name)
                if not member.isfile() or parts.is_absolute() or ".." in parts.parts or member.name not in wanted or member.name in seen:
                    raise RuntimeError("Unexpected/unsafe archive member")
                row = wanted[member.name]
                if member.size != row["bytes"] or file_digest(archive.extractfile(member)) != row["sha256"]:
                    raise RuntimeError(f"Archive content differs from manifest: {member.name}")
                if member.uid or member.gid or member.uname or member.gname:
                    raise RuntimeError("Archive contains host ownership metadata")
                seen.add(member.name)
        # Consume the compressed stream completely to check its trailer as well.
        for _ in iter(lambda: process.stdout.read(1024 * 1024), b""):
            pass
        error = process.stderr.read()
        if process.wait() or seen != set(wanted):
            raise RuntimeError(f"Incomplete/invalid archive: {error[-200:]!r}")
    except BaseException:
        process.kill()
        process.wait()
        raise
    finally:
        process.stdout.close()


def create_archive(compressed, rows):
    plain = compressed.with_suffix("")
    with tarfile.open(plain, "x", format=tarfile.PAX_FORMAT) as archive:
        for row in rows:
            path = ROOT / row["path"]
            info = tarfile.TarInfo(row["path"])
            info.size, info.mode, info.mtime = row["bytes"], 0o644, 0
            with path.open("rb") as source:
                archive.addfile(info, source)
    subprocess.run(["zstd", "-q", "-T2", "-o", str(compressed), str(plain)], check=True)
    verify_archive(compressed, rows)
    result = {"asset": compressed.name, "bytes": compressed.stat().st_size,
              "sha256": raw_validation.digest(compressed), "files": len(rows)}
    plain.unlink()
    return result


def package(version):
    manifest_path = OUT / f"artifacts-{version}.json"
    work = WORK / version
    if manifest_path.exists() or work.exists():
        raise RuntimeError("Preserving existing artifact version; select a new version")
    if not all(runtime_finished(condition) for condition in ("measured", "reference")):
        raise RuntimeError("Finish both measured and reference runtime before release packaging")
    checks = export_checks()
    if checks["pending_verification"]:
        raise RuntimeError("Reference check publication is still incomplete")
    data = collect()
    if not all(data["coverage"][name] for name in ("original_inventory_complete", "reference_inventory_complete")):
        raise RuntimeError("Final original/reference inventory is incomplete; inspect reports what is available")
    work.mkdir(parents=True)
    assets = {kind: create_archive(work / f"agentmvc-lanes-{version}-{kind}.tar.zst", rows)
              for kind, rows in data["files"].items() if rows}
    manifest = {"schema_version": 1, "artifact_version": version, "created_at": lane_broker.stamp(),
                "publication_status": "prepared locally; not uploaded", "restore_root": "repository root",
                "snapshot_status": "complete original inventory" if data["coverage"]["original_inventory_complete"] else "partial inventory",
                "validation": "Unchanged scrub patterns over decoded JSON strings/object keys and Markdown; raw zstd validation; archive contents rehashed",
                "tools_sha256": {f"tools/{name}": raw_validation.digest(ROOT / "tools" / name) for name in
                                 ("lane_artifacts.py", "lane_continue.py", "scrub.py", "v2_expert_symmetry_validate.py")},
                "assets": assets, **data}
    validate_value(manifest, checker())
    with manifest_path.open("x") as stream:
        stream.write(json.dumps(manifest, indent=2) + "\n")
    return manifest


def verify(version):
    manifest = json.loads((OUT / f"artifacts-{version}.json").read_text())
    validate_value(manifest, checker())
    for kind, asset in manifest["assets"].items():
        path = WORK / version / asset["asset"]
        if raw_validation.digest(path) != asset["sha256"] or path.stat().st_size != asset["bytes"]:
            raise RuntimeError(f"Archive checksum mismatch: {asset['asset']}")
        verify_archive(path, manifest["files"][kind])
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("inspect", "export-feedback", "export-checks", "package", "verify"))
    parser.add_argument("version", nargs="?")
    args = parser.parse_args()
    if args.action in ("package", "verify") and (not args.version or not re.fullmatch(r"[a-z0-9][a-z0-9._-]{0,55}", args.version)):
        parser.error("Provide a short lowercase artifact version, for example v1")
    if args.action == "export-feedback":
        print(json.dumps(export_feedback(), indent=2))
        return
    if args.action == "export-checks":
        print(json.dumps(export_checks(), indent=2))
        return
    result = collect() if args.action == "inspect" else package(args.version) if args.action == "package" else verify(args.version)
    print(json.dumps({"coverage": result["coverage"], "assets": result.get("assets", {}),
                      "publication_status": result.get("publication_status", "validation only; no archives written")}, indent=2))


if __name__ == "__main__":
    main()
