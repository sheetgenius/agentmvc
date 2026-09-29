"""Verify and scrub-check compressed same-session k6 streams before release."""

import hashlib
import json
import subprocess
from pathlib import Path

import one_shot

ROOT = one_shot.ROOT
BASE = ROOT / "results/v2-expert-symmetry/runtime"
MARKERS = {
    "host_home": str(Path.home()).encode(),
    "host_repo": str(ROOT).encode(),
    "private_key": b"-----BEGIN PRIVATE KEY-----",
    "codex_auth": b"auth.json",
    "broker_token": b"ONE_SHOT_BROKER_TOKEN",
    "http_auth_header": b'"Authorization"',
    "jwt_header": b"Token eyJ",
}


def digest(path):
    sha = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            sha.update(block)
    return sha.hexdigest()


def inspect(path):
    process = subprocess.Popen(["zstd", "-dc", str(path)], stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE)
    hits, size, tail = set(), 0, b""
    width = max(map(len, MARKERS.values())) - 1
    try:
        for block in iter(lambda: process.stdout.read(1024 * 1024), b""):
            size += len(block)
            sample = tail + block
            hits.update(name for name, marker in MARKERS.items() if marker in sample)
            tail = sample[-width:]
    finally:
        process.stdout.close()
    stderr = process.stderr.read()
    if process.wait() != 0:
        raise RuntimeError(f"Invalid zstd stream {path}: {stderr[-500:]!r}")
    return size, sorted(hits)


def main():
    records = []
    for stack in ("rails", "typescript", "phoenix"):
        for round_number in (1, 2):
            folder = BASE / stack / f"round{round_number}"
            data = json.loads((folder / "results.json").read_text())
            expected = data["raw_stream_sha256"]
            if len(expected) != 18:
                raise RuntimeError(f"Missing raw streams: {folder}")
            for name, sha in expected.items():
                path = folder / name
                actual = digest(path)
                if actual != sha:
                    raise RuntimeError(f"Raw checksum changed: {path}")
                uncompressed, hits = inspect(path)
                if hits:
                    raise RuntimeError(f"Sensitive marker {hits} in {path}")
                records.append({"path": str(path.relative_to(BASE)), "sha256": sha,
                                "compressed_bytes": path.stat().st_size,
                                "decompressed_bytes": uncompressed})
    output = {"status": "pass", "raw_streams": len(records),
              "compressed_bytes": sum(row["compressed_bytes"] for row in records),
              "decompressed_bytes": sum(row["decompressed_bytes"] for row in records),
              "sensitive_marker_hits": {}, "files": records}
    (BASE / "raw-validation.json").write_text(json.dumps(output, indent=2) + "\n")
    print(json.dumps({key: output[key] for key in
                      ("status", "raw_streams", "compressed_bytes", "decompressed_bytes")},
                     indent=2))


if __name__ == "__main__":
    main()
