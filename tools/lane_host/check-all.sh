#!/usr/bin/env bash
set -euo pipefail
port="${1:?usage: check-all.sh PORT}"
number="${LANE_NUMBER:?}"
here="$(cd "$(dirname "$0")" && pwd)"
bash "$here/check-api.sh" "$port"
if (( number >= 5 )); then bash "$here/check-security.sh" "$port"; fi
if (( number >= 8 )); then bash "$here/check-live.sh" "$port"; fi
