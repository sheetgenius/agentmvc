#!/usr/bin/env bash
set -euo pipefail
root="$(cd "$(dirname "$0")/.." && pwd)"
action="${1:?usage: harness/ts.sh run COMMAND...|build|test|start|logs|stop|worker-start|worker-logs|worker-stop}"
shift
case "$action" in
  run) exec python3 "$root/harness/check-client.py" ts-run 4107 "$@";;
  build|test|start|logs|stop|worker-start|worker-logs|worker-stop)
    exec python3 "$root/harness/check-client.py" "ts-$action" 4107 "$@";;
  *) exit 2;;
esac
