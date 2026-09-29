#!/usr/bin/env bash
set -euo pipefail
root="$(cd "$(dirname "$0")/.." && pwd)"
action="${1:?usage: harness/ihp.sh run COMMAND...|build|start|logs|stop}"
shift
case "$action" in
  run) exec python3 "$root/harness/check-client.py" ihp-run 4104 "$@";;
  build|start|logs|stop) exec python3 "$root/harness/check-client.py" "ihp-$action" 4104 "$@";;
  *) exit 2;;
esac
