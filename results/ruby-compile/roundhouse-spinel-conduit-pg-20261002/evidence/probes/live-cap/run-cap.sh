#!/usr/bin/env bash
# usage: run-cap.sh IMAGE LABEL
set -euo pipefail
here=$(cd "$(dirname "$0")" && pwd); image=$1; label=v5-cap-$2
net=$label-net; db=$label-db; app=$label-app
cleanup() { docker rm -f -v "$app" "$db" >/dev/null 2>&1 || true; docker network rm "$net" >/dev/null 2>&1 || true; }
trap cleanup EXIT
docker network create "$net" >/dev/null
docker run -d --name "$db" --network "$net" --network-alias db -e POSTGRES_PASSWORD=postgres -e POSTGRES_DB=conduit postgres:17-alpine >/dev/null
until docker exec "$db" pg_isready -h 127.0.0.1 -U postgres -d conduit >/dev/null 2>&1; do sleep .5; done
docker run -d --name "$app" --network "$net" --network-alias app --cpus=2 --memory=1g \
  -e DATABASE_URL=postgres://postgres:postgres@db:5432/conduit -e SECRET_KEY_BASE=$(openssl rand -hex 64) -e PORT=8080 "$image" >/dev/null
docker run --rm --name "$label-node" --network "$net" -v "$here:/cap:ro" -e BACKEND_URL=http://app:8080 \
  --entrypoint sh agentmvc-one-shot-browser:1.63.0 -c 'until curl -fsS http://app:8080/api/tags >/dev/null 2>&1; do sleep .5; done; mkdir /tmp/c && cp /cap/*.js /cap/*.mjs /tmp/c/ && ln -s /opt/agentmvc/node_modules /tmp/c/node_modules && cd /tmp/c && node cap.mjs'
