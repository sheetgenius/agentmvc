#!/usr/bin/env bash
# Build and check one backend image with fresh PostgreSQL and the three-variable runtime contract.
set -euo pipefail
root="$(cd "$(dirname "$0")/.." && pwd)"
port="${1:?usage: harness/check-production.sh PORT}"
name="agentmvc-one-shot-$(basename "$root")-$$"
network="$name-net"
db="$name-db"
app="$name-app"
image="$name:latest"
postgres='postgres:17-alpine@sha256:742f40ea20b9ff2ff31db5458d127452988a2164df9e17441e191f3b72252193'
cleanup() {
  docker rm -f "$app" "$db" >/dev/null 2>&1 || true
  docker network rm "$network" >/dev/null 2>&1 || true
  docker image rm "$image" >/dev/null 2>&1 || true
}
trap cleanup EXIT

docker build -t "$image" "$root"
docker network create "$network" >/dev/null
docker run -d --name "$db" --network "$network" --network-alias db \
  -e POSTGRES_USER=agentmvc -e POSTGRES_PASSWORD=agentmvc -e POSTGRES_DB=agentmvc \
  "$postgres" >/dev/null
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
if ! curl -fsS -H 'Accept: application/json' "http://127.0.0.1:$port/api/tags" >/dev/null; then
  docker logs "$app"
  exit 1
fi
"$root/harness/check-all.sh" "$port"
