#!/usr/bin/env bash
set -euo pipefail
root="$(cd "$(dirname "$0")/.." && pwd)"
exec python3 "$root/harness/check-client.py" live "${1:?usage: harness/check-live.sh PORT}"
