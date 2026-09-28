#!/usr/bin/env bash
set -euo pipefail
root="${ONE_SHOT_WORKDIR:?}"
port="${1:?usage: harness/check-all.sh PORT}"
"$(dirname "$0")/check-api.sh" "$port"
"$(dirname "$0")/check-live.sh" "$port"
"$(dirname "$0")/check-security.sh" "$port"
