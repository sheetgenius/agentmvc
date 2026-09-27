#!/usr/bin/env bash
set -euo pipefail
root="$(cd "$(dirname "$0")/.." && pwd)"
port="${1:?usage: harness/check-api.sh PORT}"
image='ghcr.io/orange-opensource/hurl@sha256:d7727dcc0166de8aea88916e73ea435ee09bfecb8ba0c281200206b6cf37cf64'
cd "$root/realworld_spec"
files=(api/hurl/*.hurl features/*/hurl/*.hurl)
docker run --rm --network host -v "$PWD:/spec:ro" -w /spec "$image" \
  --test --jobs 1 --variable "host=http://127.0.0.1:$port" \
  --variable "uid=$(date +%s)$$" "${files[@]}"
