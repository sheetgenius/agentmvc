#!/usr/bin/env bash
# Same frozen protocol/browser runner, with session-scoped timeout cleanup.
set -euo pipefail
root="${ONE_SHOT_WORKDIR:?}"
port="${1:?usage: check-live.sh PORT}"
image='agentmvc-one-shot-browser:1.63.0'
expected="$(cat "$root/harness/browser-image-id")"
actual="$(docker image inspect "$image" --format '{{.Id}}')"
[[ "$actual" == "$expected" ]] || { echo 'Browser image differs from frozen fixture' >&2; exit 1; }
name="agentmvc-lane-live-${LANE_ID:?}-$$"
trap 'docker rm -f "$name" >/dev/null 2>&1 || true' EXIT
docker run --rm --name "$name" --label "agentmvc.lane.check=$LANE_ID" --init --network host --ipc host \
  -e BACKEND_URL="http://127.0.0.1:$port" -e FRONTEND_PORT="$((port + 1072))" \
  --mount "type=bind,source=$root/realworld_spec/frontend,target=/fixture/frontend,readonly" \
  --mount "type=bind,source=$root/harness/run-live-container.sh,target=/harness/run-live-container.sh,readonly" \
  "$image" /harness/run-live-container.sh "$port"
