#!/usr/bin/env bash
set -euo pipefail
root="$(cd "$(dirname "$0")/.." && pwd)"
action="${1:?usage: harness/phoenix.sh run COMMAND...|start|stop|logs}"
shift
case "$action" in
  run) exec python3 "$root/harness/check-client.py" phoenix-run 4102 "$@";;
  start) exec python3 "$root/harness/check-client.py" phoenix-start 4102 "$@";;
  stop|logs) exec python3 "$root/harness/check-client.py" "phoenix-$action" 4102;;
  *) exit 2;;
esac
