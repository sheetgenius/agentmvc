#!/usr/bin/env bash
set -euo pipefail
root="$(cd "$(dirname "$0")/.." && pwd)"
action="${1:?usage: harness/go.sh run COMMAND...|build|test|lint|start|logs|stop}"
shift
case "$action" in
  run) exec python3 "$root/harness/check-client.py" go-run 4110 "$@";;
  build|test|lint|start|logs|stop)
    exec python3 "$root/harness/check-client.py" "go-$action" 4110 "$@";;
  *) exit 2;;
esac
