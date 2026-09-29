#!/usr/bin/env bash
# All acceptance files present in this step's frozen specification.
set -euo pipefail
shopt -s nullglob
root="${ONE_SHOT_WORKDIR:?}"
port="${1:?usage: check-api.sh PORT}"
name="agentmvc-lane-hurl-${LANE_ID:?}-$$"
trap 'docker rm -f "$name" >/dev/null 2>&1 || true' EXIT
image='ghcr.io/orange-opensource/hurl@sha256:d7727dcc0166de8aea88916e73ea435ee09bfecb8ba0c281200206b6cf37cf64'
cd "$root/realworld_spec"
files=(api/hurl/*.hurl features/*/hurl/*.hurl)
[[ ${#files[@]} -ge 13 ]] || { echo 'Incomplete acceptance fixture' >&2; exit 2; }
docker run --rm --name "$name" --label "agentmvc.lane.check=$LANE_ID" --network host \
  --mount "type=bind,source=$PWD,target=/spec,readonly" \
  -w /spec "$image" --test --jobs 1 --variable "host=http://127.0.0.1:$port" \
  --variable "uid=$(date +%s)$$" "${files[@]}"
