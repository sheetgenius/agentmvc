#!/usr/bin/env bash
# Serve the frozen Lit editor against a one-shot production backend.
set -euo pipefail
root="$(cd "$(dirname "$0")/.." && pwd)"
stack="${1:?usage: tools/one_shot_demo.sh rails|phoenix|loco}"
case "$stack" in rails|phoenix|loco);; *) exit 2;; esac
work="$root/.work/one-shot/$stack"
python3 "$root/tools/one_shot.py" verify "$work" >/dev/null
port="${DEMO_BACKEND_PORT:-4401}"
frontend_port="${DEMO_FRONTEND_PORT:-5174}"
name="agentmvc-one-shot-demo-$stack"
image="$name:local"
db="$name-db"
app="$name-app"
network="$name-net"
scratch="$root/.work/one-shot-demo/$stack"
postgres='postgres:17-alpine@sha256:742f40ea20b9ff2ff31db5458d127452988a2164df9e17441e191f3b72252193'
frontend_pid=""
cleanup() {
  [[ -z "$frontend_pid" ]] || { kill "$frontend_pid" 2>/dev/null || true; wait "$frontend_pid" 2>/dev/null || true; }
  docker rm -f "$app" "$db" >/dev/null 2>&1 || true
  docker network rm "$network" >/dev/null 2>&1 || true
}
trap cleanup EXIT

docker build -q -t "$image" "$work" >/dev/null
docker network create "$network" >/dev/null
docker run -d --name "$db" --network "$network" --network-alias db \
  -e POSTGRES_USER=agentmvc -e POSTGRES_PASSWORD=agentmvc -e POSTGRES_DB=agentmvc "$postgres" >/dev/null
for attempt in {1..120}; do
  if docker exec "$db" pg_isready -U agentmvc -d agentmvc >/dev/null 2>&1; then break; fi
  sleep 1
done
docker exec "$db" pg_isready -U agentmvc -d agentmvc >/dev/null
docker run -d --name "$app" --network "$network" -p "127.0.0.1:$port:$port" \
  -e DATABASE_URL=postgres://agentmvc:agentmvc@db:5432/agentmvc \
  -e SECRET_KEY_BASE="$(openssl rand -hex 64)" -e PORT="$port" "$image" >/dev/null
for attempt in {1..120}; do
  if curl -fsS -H 'Accept: application/json' "http://127.0.0.1:$port/api/tags" >/dev/null 2>&1; then break; fi
  if [[ "$(docker inspect -f '{{.State.Running}}' "$app")" != true ]]; then docker logs "$app"; exit 1; fi
  sleep 1
done
curl -fsS -H 'Accept: application/json' "http://127.0.0.1:$port/api/tags" >/dev/null

mkdir -p "$scratch"
cp -R "$root/one-shot/frontend/." "$scratch/"
ln -sfn "$root/frontend/node_modules" "$scratch/node_modules"
(cd "$scratch" && BACKEND_URL="http://127.0.0.1:$port" FRONTEND_PORT="$frontend_port" \
  exec node node_modules/vite/bin/vite.js --host 127.0.0.1) > "$scratch/vite.log" 2>&1 &
frontend_pid=$!
for attempt in {1..60}; do
  if curl -fsS "http://127.0.0.1:$frontend_port/" >/dev/null 2>&1; then break; fi
  if ! kill -0 "$frontend_pid" 2>/dev/null; then cat "$scratch/vite.log"; exit 1; fi
  sleep 1
done
curl -fsS "http://127.0.0.1:$frontend_port/" >/dev/null
DEMO_ORIGIN="${DEMO_ORIGIN:-http://127.0.0.1:$frontend_port}" \
  node "$root/tools/live-demo-seed.mjs" "http://127.0.0.1:$port"
echo "One-shot $stack demo is running. Stop this process to remove its containers."
wait "$frontend_pid"
