#!/usr/bin/env bash
set -euo pipefail
root="$(cd "$(dirname "$0")/.." && pwd)"
exec python3 "$root/harness/check-client.py" security "${1:?usage: harness/check-security.sh PORT}"
