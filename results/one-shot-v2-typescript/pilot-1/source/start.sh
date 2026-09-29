#!/usr/bin/env bash
set -euo pipefail

node ace migration:run --force
node ace queue:work &
worker=$!
node bin/server.js &
server=$!
trap 'kill "$worker" "$server" 2>/dev/null || true' EXIT TERM INT
wait -n "$worker" "$server"
