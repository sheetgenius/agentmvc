#!/usr/bin/env bash
# Try a published Go/Python application with the fixed Lit client.
set -euo pipefail
root="$(cd "$(dirname "$0")/.." && pwd)"
stack="${1:?usage: tools/lane_demo.sh go|python [eight|one-shot]}"
condition="${2:-eight}"
case "$stack" in go) default_port=4410;; python) default_port=4411;; *) exit 2;; esac
case "$condition" in
  eight) source_dir="$root/stacks/$stack/8-live-editing";;
  one-shot) source_dir="$root/results/one-shot-v2-$stack-expert/pilot-1/source";;
  *) echo 'condition must be eight or one-shot' >&2; exit 2;;
esac
[[ -f "$source_dir/Dockerfile" ]] || { echo "Published application is not available: $source_dir" >&2; exit 1; }
port="${DEMO_BACKEND_PORT:-$default_port}"
frontend_port="${DEMO_FRONTEND_PORT:-5178}"
name="agentmvc-lane-demo-$stack-$$"
image="$name:local"
db="$name-db"
app="$name-app"
network="$name-net"
postgres='postgres:17-alpine@sha256:742f40ea20b9ff2ff31db5458d127452988a2164df9e17441e191f3b72252193'
frontend_pid=""
mkdir -p "$root/.work"
client="$(mktemp -d "$root/.work/lane-demo-client.XXXXXX")"
cleanup() {
  [[ -z "$frontend_pid" ]] || { kill "$frontend_pid" 2>/dev/null || true; wait "$frontend_pid" 2>/dev/null || true; }
  docker rm -f "$app" "$db" >/dev/null 2>&1 || true
  docker network rm "$network" >/dev/null 2>&1 || true
  docker image rm "$image" >/dev/null 2>&1 || true
  rm -rf "$client"
}
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM

docker build -t "$image" "$source_dir"
docker network create "$network" >/dev/null
docker run -d --name "$db" --network "$network" --network-alias db \
  -e POSTGRES_USER=agentmvc -e POSTGRES_PASSWORD=agentmvc -e POSTGRES_DB=agentmvc "$postgres" >/dev/null
for attempt in {1..60}; do
  if docker exec "$db" pg_isready -h 127.0.0.1 -U agentmvc -d agentmvc >/dev/null 2>&1; then break; fi
  sleep 1
done
docker exec "$db" pg_isready -h 127.0.0.1 -U agentmvc -d agentmvc >/dev/null
docker run -d --name "$app" --network "$network" -p "127.0.0.1:$port:$port" \
  -e DATABASE_URL=postgres://agentmvc:agentmvc@db:5432/agentmvc \
  -e SECRET_KEY_BASE="$(openssl rand -hex 64)" -e PORT="$port" "$image" >/dev/null
for attempt in {1..120}; do
  if curl -fsS -H 'Accept: application/json' "http://127.0.0.1:$port/api/tags" >/dev/null 2>&1; then break; fi
  if [[ "$(docker inspect -f '{{.State.Running}}' "$app")" != true ]]; then docker logs "$app"; exit 1; fi
  sleep 1
done
curl -fsS -H 'Accept: application/json' "http://127.0.0.1:$port/api/tags" >/dev/null
cp -R "$root/one-shot/frontend/." "$client/"
(cd "$client" && npm ci --silent)
(cd "$client" && BACKEND_URL="http://127.0.0.1:$port" FRONTEND_PORT="$frontend_port" \
  exec node node_modules/vite/bin/vite.js --host 127.0.0.1) > "$client/vite.log" 2>&1 &
frontend_pid=$!
for attempt in {1..60}; do
  if curl -fsS "http://127.0.0.1:$frontend_port/" >/dev/null 2>&1; then break; fi
  if ! kill -0 "$frontend_pid" 2>/dev/null; then cat "$client/vite.log"; exit 1; fi
  sleep 1
done
curl -fsS "http://127.0.0.1:$frontend_port/" >/dev/null
DEMO_ORIGIN="http://127.0.0.1:$frontend_port" \
  node "$root/tools/live-demo-seed.mjs" "http://127.0.0.1:$port"
echo "$stack $condition demo is running. Open the link in several tabs. Ctrl-C cleans up."
wait "$frontend_pid"
