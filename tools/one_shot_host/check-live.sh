#!/usr/bin/env bash
# Run the same protocol and browser gate for every backend. The backend must already be listening.
set -euo pipefail
root="${ONE_SHOT_WORKDIR:?}"
port="${1:?usage: harness/check-live.sh PORT}"
image="agentmvc-one-shot-browser:1.63.0"
expected="$(cat "$root/harness/browser-image-id")"
actual="$(docker image inspect "$image" --format '{{.Id}}')"
if [[ "$actual" != "$expected" ]]; then
  echo "browser image differs from prepared fixture; rerun one-shot setup" >&2
  exit 1
fi
docker run --rm --init --network host --ipc host \
  -e BACKEND_URL="http://127.0.0.1:$port" -e FRONTEND_PORT="$((port + 1072))" \
  -v "$root/realworld_spec/frontend:/fixture/frontend:ro" \
  -v "$root/harness/run-live-container.sh:/harness/run-live-container.sh:ro" \
  "$image" /harness/run-live-container.sh "$port"
