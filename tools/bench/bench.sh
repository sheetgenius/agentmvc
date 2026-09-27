#!/bin/sh
# Build this directory's production image and run the fixed benchmark against it.
#   perf/bench.sh [out-dir]      results: <out-dir>/results.json (default perf/latest)
set -eu
cd "$(dirname "$0")/.."
NAME="$(basename "$PWD")"
PORT="$(grep -o 'Port:\*\* [0-9]*' ENVIRONMENT.md | grep -o '[0-9]*')"
docker build -q -t "agentmvc-$NAME:latest" . >/dev/null
BENCH_HOST_PORT="$((PORT + 14000))" python3 perf/bench.py "agentmvc-$NAME:latest" "$NAME" "${1:-perf/latest}"
