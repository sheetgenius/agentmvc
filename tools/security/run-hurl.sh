#!/bin/sh
# Run the black-box security checks against a server root:  security/run-hurl.sh BASE_URL [file ...]
# BASE_URL as seen from a container, e.g. http://host.docker.internal:4101 or http://<container>:8080 with NETWORK set.
set -eu
DIR="$(cd "$(dirname "$0")/hurl" && pwd)"
BASE_URL="$1"; shift
cd "$DIR"
[ $# -eq 0 ] && set -- s*.hurl
exec docker run --rm ${NETWORK:+--network "$NETWORK"} -v "$DIR:/security:ro" -w /security ghcr.io/orange-opensource/hurl:latest \
  --test --jobs 1 --variable "host=$BASE_URL" --variable "uid=$(date +%s)$$" "$@"
