#!/usr/bin/env bash
set -euo pipefail
node ace migration:run --force
node ace queue:work &
worker=$!
trap 'kill "$worker" 2>/dev/null || true' EXIT TERM INT
node ace serve --watch --no-clear "$@"
