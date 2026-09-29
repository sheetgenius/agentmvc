#!/usr/bin/env bash
set -euo pipefail
root="$(cd "$(dirname "$0")/.." && pwd)"
action="${1:?usage: harness/phoenix.sh run COMMAND...|build|test|start|logs|stop}"
shift
case "$action" in
  run) exec python3 "$root/harness/check-client.py" phx-run 4108 "$@";;
  build|test|start|logs|stop) exec python3 "$root/harness/check-client.py" "phx-$action" 4108 "$@";;
  *) exit 2;;
esac
