#!/usr/bin/env bash
set -euo pipefail
root="$(cd "$(dirname "$0")/.." && pwd)"
action="${1:?usage: harness/ts.sh run COMMAND...|build|test|start|logs|stop}"
shift
case "$action" in
  run) exec python3 "$root/harness/check-client.py" ts-run 4106 "$@";;
  build|test|start|logs|stop) exec python3 "$root/harness/check-client.py" "ts-$action" 4106 "$@";;
  *) exit 2;;
esac
