#!/usr/bin/env bash
set -euo pipefail
root="$(cd "$(dirname "$0")/.." && pwd)"
action="${1:?usage: harness/hs.sh run COMMAND...|build|test|start|logs|stop}"
shift
case "$action" in
  run) exec python3 "$root/harness/check-client.py" hs-run 4105 "$@";;
  build|test|start|logs|stop) exec python3 "$root/harness/check-client.py" "hs-$action" 4105 "$@";;
  *) exit 2;;
esac
