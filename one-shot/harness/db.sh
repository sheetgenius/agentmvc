#!/usr/bin/env bash
set -euo pipefail
root="$(cd "$(dirname "$0")/.." && pwd)"
case "${1:?usage: harness/db.sh start|stop PORT}" in
  start) action=db-start;;
  stop) action=db-stop;;
  *) exit 2;;
esac
exec python3 "$root/harness/check-client.py" "$action" "${2:?usage: harness/db.sh start|stop PORT}"
