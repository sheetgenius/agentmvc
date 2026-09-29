"""Package published lane evidence for external release; never uploads anything.

  .venv/bin/python tools/lane_artifacts.py inspect
  .venv/bin/python tools/lane_artifacts.py package VERSION
  .venv/bin/python tools/lane_artifacts.py verify VERSION

Like archive_raw.py, keep assets in .work and only checksums/provenance in Git.
Archives restore repository-relative paths. Packaging requires the 18 original
coding transcripts, four readers, and 144 final raw streams. Existing versions
survive; additional reference/diagnostic transcripts are listed separately.
"""
import argparse
import hashlib
import json
import re
import subprocess
import tarfile
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
    return scrub.Scrubber(ROOT, tokens)


def validate_value(value, cleaner):
    hits = {hit for text in lane_continue.strings(value) for hit in cleaner.leaks(text)}
    if hits:
        raise RuntimeError(f"Sensitive decoded JSON string/key: {sorted(hits)}")


def validate_lines(stream, cleaner):
    count = 0
    for line in stream:
        if line.strip():
            value = json.loads(line)
            validate_value(value, cleaner)
            count += 1
    if not count:
        raise RuntimeError("Empty JSONL evidence")
    return count


def validate_file(path, cleaner):
    relative(path)
    if path.name.endswith(".json.zst"):
        size, hits = raw_validation.inspect(path)
        if hits:
            raise RuntimeError(f"Sensitive raw-stream markers: {hits}")
        proc = subprocess.Popen(["zstd", "-dc", str(path)], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        try:
            count = validate_lines(proc.stdout, cleaner)
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
    candidates = [path.parent / name for name in ("run.json", "results.json", "prepared.json")]
    record = next((item for item in candidates if item.is_file()), None)
    if record is None:
        raise RuntimeError(f"No published provenance for {relative(path)}")
    name = relative(record)
    if name not in records:
        data = json.loads(record.read_text())
        validate_value(data, cleaner)
        records[name] = {"sha256": raw_validation.digest(record),
                         **{key: data[key] for key in PROVENANCE_KEYS if key in data}}
        companions = {}
        for filename in ("verification.json", "isolation.json", "grades.json", "source-snapshot.json",
                         "publication-adapter.json"):
            item = record.parent / filename
            if item.is_file():
                validate_file(item, cleaner)
                companions[relative(item)] = raw_validation.digest(item)
        records[name]["related_record_sha256"] = companions
    return name


def collect():
    groups = {"transcripts": [], "runtime": []}
    for base in SOURCES:
        for path in sorted(base.rglob("*transcript*.jsonl")):
            if "source" in path.relative_to(base).parts:
                continue
            markdown = path.with_suffix(".md")
            if not markdown.is_file():
                raise RuntimeError(f"Missing readable transcript: {relative(path)}")
            groups["transcripts"].extend((path, markdown))
    groups["runtime"] = sorted((OUT / "runtime").rglob("raw-*.json.zst"))
    tracked = set(subprocess.check_output(["git", "ls-files", "-z", "--", *[relative(p) for p in SOURCES]],
                                          cwd=ROOT).decode().split("\0"))
    selected = [path for paths in groups.values() for path in paths]
    if any(relative(path) in tracked for path in selected):
        raise RuntimeError("Full lane transcripts/raw streams must remain outside Git")
    cleaner, records = checker(), {}
    entries = {}
    for kind, paths in groups.items():
        entries[kind] = []
        for path in paths:
            name = relative(path)
            validation = validate_file(path, cleaner)
            sha = raw_validation.digest(path)
            source_record = provenance(path, records, cleaner)
            if kind == "runtime":
                data = json.loads((path.parent / "results.json").read_text())
                if data.get("raw_stream_sha256", {}).get(path.name) != sha:
                    raise RuntimeError(f"Raw stream does not match its runtime record: {name}")
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
    return {"files": entries, "provenance": records,
            "coverage": {"coding_transcripts": coding, "reader_transcripts": readers,
                         "measured_raw_streams": original_streams,
                         "additional_transcripts": sorted(transcripts - coding_paths - reader_paths),
                         "additional_runtime_streams": len(raw_paths - original_raw),
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
    data = collect()
    if not data["coverage"]["original_inventory_complete"]:
        raise RuntimeError("Final original inventory is incomplete; inspect reports what is available")
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
    parser.add_argument("action", choices=("inspect", "package", "verify"))
    parser.add_argument("version", nargs="?")
    args = parser.parse_args()
    if args.action != "inspect" and (not args.version or not re.fullmatch(r"[a-z0-9][a-z0-9._-]{0,55}", args.version)):
        parser.error("Provide a short lowercase artifact version, for example v1")
    result = collect() if args.action == "inspect" else package(args.version) if args.action == "package" else verify(args.version)
    print(json.dumps({"coverage": result["coverage"], "assets": result.get("assets", {}),
                      "publication_status": result.get("publication_status", "validation only; no archives written")}, indent=2))


if __name__ == "__main__":
    main()
