#!/usr/bin/env bash
set -euo pipefail
root="$(cd "$(dirname "$0")/.." && pwd)"
action="${1:?usage: harness/rails.sh run COMMAND...|build|test|start|logs|stop}"
shift
case "$action" in
  run) exec python3 "$root/harness/check-client.py" rails-run 4109 "$@";;
  build|test|start|logs|stop)
    exec python3 "$root/harness/check-client.py" "rails-$action" 4109 "$@";;
  *) exit 2;;
esac
