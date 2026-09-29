"""Run the exact expert-1 HTTP/socket probes against a separate reference image."""
from pathlib import Path
import argparse
import hashlib
import json

import typescript_expert_heldout as heldout


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--image", required=True)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    heldout.IMAGE = args.image
    heldout.SOURCE = args.source
    heldout.OUTPUT = args.output
    heldout.NETWORK = "agentmvc-ts-reference-heldout-net"
    heldout.DB = "agentmvc-ts-reference-heldout-db"
    heldout.APP = "agentmvc-ts-reference-heldout-app"
    heldout.PORT = 4125
    heldout.BASE = f"http://127.0.0.1:{heldout.PORT}"
    heldout.main()
    record = json.loads(args.output.read_text())
    record["condition"] = "reference-1-held-out-diagnostic"
    record["source"] = "separate reference-1 copy; compiled diagnostic image"
    record["wrapper_sha256"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    args.output.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")


if __name__ == "__main__":
    main()
