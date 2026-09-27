#!/usr/bin/env bash
# Build one step-8 backend, start its PostgreSQL and the shared editor, and print a fresh link.
set -euo pipefail
root="$(cd "$(dirname "$0")/.." && pwd)"
stack="${1:-}"
case "$stack" in rails) port=4101;; phoenix) port=4102;; loco) port=4103;; *) echo 'usage: tools/demo.sh rails|phoenix|loco' >&2; exit 2;; esac
source_dir="$root/stacks/$stack/8-live-editing"
[[ -d "$source_dir" ]] || { echo "step-8 snapshot missing: $source_dir" >&2; exit 1; }
name="agentmvc-demo-$stack-$$"
image="$name"
db="$name-db"
app="$name-app"
network="$name-net"
frontend_port="${FRONTEND_PORT:-5173}"
frontend_pid=""
frontend_log="$(mktemp)"

cleanup() {
  [[ -z "$frontend_pid" ]] || { kill "$frontend_pid" 2>/dev/null || true; wait "$frontend_pid" 2>/dev/null || true; }
  docker container rm -f "$app" "$db" >/dev/null 2>&1 || true
  docker network rm "$network" >/dev/null 2>&1 || true
  docker image rm "$image" >/dev/null 2>&1 || true
  rm -f "$frontend_log"
}
trap cleanup EXIT

docker build -t "$image" "$source_dir"
docker network create "$network" >/dev/null
docker run -d --name "$db" --network "$network" --network-alias db \
  -e POSTGRES_PASSWORD=conduit -e POSTGRES_DB=conduit postgres:17-alpine >/dev/null
for attempt in {1..60}; do
  if docker exec "$db" pg_isready -U postgres -d conduit >/dev/null 2>&1; then break; fi
  sleep 1
done
docker exec "$db" pg_isready -U postgres -d conduit >/dev/null
docker run -d --name "$app" --network "$network" -p "$port:$port" \
  -e DATABASE_URL=postgres://postgres:conduit@db:5432/conduit \
  -e SECRET_KEY_BASE="$(openssl rand -hex 64)" -e PORT="$port" "$image" >/dev/null
for attempt in {1..90}; do
  if curl -fsS -H 'Accept: application/json' "http://127.0.0.1:$port/api/tags" >/dev/null 2>&1; then break; fi
  if [[ "$(docker inspect -f '{{.State.Running}}' "$app")" != true ]]; then docker logs "$app"; exit 1; fi
  sleep 1
done
curl -fsS -H 'Accept: application/json' "http://127.0.0.1:$port/api/tags" >/dev/null

if [[ ! -d "$root/frontend/node_modules" ]]; then (cd "$root/frontend" && npm ci --silent); fi
(cd "$root/frontend" && BACKEND_URL="http://127.0.0.1:$port" FRONTEND_PORT="$frontend_port" \
  exec node node_modules/vite/bin/vite.js --host 0.0.0.0) > "$frontend_log" 2>&1 &
frontend_pid=$!
for attempt in {1..60}; do
  if curl -fsS "http://127.0.0.1:$frontend_port/" >/dev/null 2>&1; then break; fi
  if ! kill -0 "$frontend_pid" 2>/dev/null; then cat "$frontend_log"; exit 1; fi
  sleep 1
done
curl -fsS "http://127.0.0.1:$frontend_port/" >/dev/null
DEMO_ORIGIN="${DEMO_ORIGIN:-http://127.0.0.1:$frontend_port}" \
  node "$root/tools/live-demo-seed.mjs" "http://127.0.0.1:$port"
echo 'Paste the link into more tabs or browsers. Press Ctrl-C to stop.'
wait "$frontend_pid"
