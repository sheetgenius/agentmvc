"""Index and package the lossless k6 point streams for a GitHub release."""

import hashlib
import json
import re
import subprocess
import tarfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results/raw-data"
WORK = ROOT / ".work/raw-data-release"
EXPECTED = {
    "one-shot": 108,
    "one-shot-semantic-density": 108,
    "one-shot-ihp": 144,
    "shine": 144,
    "one-shot-v2-servant": 36,
    "one-shot-v2-typescript": 36,
}
PRIVATE = re.compile(
    rb"/Users/|/home/[^/\s]+/|-----BEGIN [A-Z ]*PRIVATE KEY-----|"
    rb"github_pat_[A-Za-z0-9_]{20,}|gh[pousr]_[A-Za-z0-9]{20,}|"
    rb"sk-(?:proj-)?[A-Za-z0-9_-]{20,}"
)


def digest(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def scan(path):
    process = subprocess.Popen(["zstd", "-dc", str(path)], stdout=subprocess.PIPE)
    tail = b""
    while block := process.stdout.read(1024 * 1024):
        if PRIVATE.search(tail + block):
            process.kill()
            raise RuntimeError(f"private-looking text in {path}")
        tail = block[-256:]
    if process.wait():
        raise RuntimeError(f"zstd decompression failed: {path}")


def main():
    WORK.mkdir(parents=True, exist_ok=True)
    OUT.mkdir(parents=True, exist_ok=True)
    index = {}
    archives = {}
    for name, expected in EXPECTED.items():
        paths = sorted((ROOT / "results" / name).rglob("raw-*.json.zst"))
        if len(paths) != expected:
            raise RuntimeError(f"{name}: found {len(paths)} streams; expected {expected}")
        asset = f"{name}-raw.tar"
        archive = WORK / asset
        records = []
        with tarfile.open(archive, "w") as tar:
            for path in paths:
                scan(path)
                records.append({
                    "path": str(path.relative_to(ROOT)),
                    "bytes": path.stat().st_size,
                    "sha256": digest(path),
                })
                tar.add(path, arcname=str(path.relative_to(ROOT)), recursive=False)
        index[name] = records
        archives[name] = {
            "asset": asset,
            "bytes": archive.stat().st_size,
            "sha256": digest(archive),
            "streams": len(records),
        }
        print(f"{name}: {len(records)} streams, {archive.stat().st_size / 1e6:.1f} MB", flush=True)
    (OUT / "index.json").write_text(json.dumps(index, indent=2) + "\n")
    (OUT / "archives.json").write_text(json.dumps(archives, indent=2) + "\n")


if __name__ == "__main__":
    main()
