#!/usr/bin/env bash
# Replay frozen v11 heads and verify every patch and exported source hash.
set -euo pipefail
here=$(cd "$(dirname "$0")" && pwd)
exec python3 "$here/prepare-toolchain.py" "${1:-$here/build}"
