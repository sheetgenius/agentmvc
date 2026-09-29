"""Verify the 24 raw k6 streams in the unscored reference diagnostic."""

import json

from v2_expert_symmetry_validate import digest, inspect
from v2_expert_reference_bench import OUT


def main():
    records = []
    for stack in ("rails", "typescript", "phoenix"):
        for round_number in (1, 2):
            folder = OUT / stack / f"round{round_number}"
            expected = json.loads((folder / "results.json").read_text())["raw_stream_sha256"]
            if len(expected) != 4:
                raise RuntimeError(f"Missing streams: {folder}")
            for name, sha in expected.items():
                path = folder / name
                if digest(path) != sha:
                    raise RuntimeError(f"Raw checksum changed: {path}")
                size, hits = inspect(path)
                if hits:
                    raise RuntimeError(f"Sensitive marker {hits} in {path}")
                records.append({"path": str(path.relative_to(OUT)), "sha256": sha,
                                "compressed_bytes": path.stat().st_size,
                                "decompressed_bytes": size})
    output = {"status": "pass", "raw_streams": len(records),
              "compressed_bytes": sum(row["compressed_bytes"] for row in records),
              "decompressed_bytes": sum(row["decompressed_bytes"] for row in records),
              "sensitive_marker_hits": {}, "files": records}
    (OUT / "raw-validation.json").write_text(json.dumps(output, indent=2) + "\n")
    print(json.dumps({key: output[key] for key in
                      ("status", "raw_streams", "compressed_bytes", "decompressed_bytes")},
                     indent=2))


if __name__ == "__main__":
    main()
