#!/usr/bin/env bash
set -euo pipefail

port="${1:?usage: run-live-container.sh PORT}"
scratch="$(mktemp -d)"
server_pid=""
cleanup() {
  if [[ -n "$server_pid" ]]; then kill "$server_pid" 2>/dev/null || true; wait "$server_pid" 2>/dev/null || true; fi
  rm -rf "$scratch"
}
trap cleanup EXIT

cp -a /fixture/frontend/. "$scratch/"
ln -s /opt/agentmvc/node_modules "$scratch/node_modules"
cd "$scratch"
node tests/protocol.js "$port"
node node_modules/vite/bin/vite.js --host 127.0.0.1 > "$scratch/vite.log" 2>&1 &
server_pid=$!
for attempt in {1..60}; do
  if curl -fsS "http://127.0.0.1:$FRONTEND_PORT/" >/dev/null 2>&1; then break; fi
  if ! kill -0 "$server_pid" 2>/dev/null; then cat "$scratch/vite.log"; exit 1; fi
  sleep 1
done
curl -fsS "http://127.0.0.1:$FRONTEND_PORT/" >/dev/null
node node_modules/@playwright/test/cli.js test
