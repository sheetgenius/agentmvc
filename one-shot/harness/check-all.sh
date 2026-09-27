#!/usr/bin/env bash
set -euo pipefail
root="$(cd "$(dirname "$0")/.." && pwd)"
port="${1:?usage: harness/check-all.sh PORT}"
"$root/harness/check-api.sh" "$port"
"$root/harness/check-live.sh" "$port"
"$root/harness/check-security.sh" "$port"
