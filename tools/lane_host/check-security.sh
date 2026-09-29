#!/usr/bin/env bash
# The same thirteen security cases; the pre-hardening baseline uses the host fixture.
set -euo pipefail
shopt -s nullglob
root="${ONE_SHOT_WORKDIR:?}"
port="${1:?usage: check-security.sh PORT}"
# Always use the coordinator's fixed cases, including a pre-step-5 scan.
fixture="$(cd "$(dirname "$0")/../.." && pwd)/tools/security/hurl"
name="agentmvc-lane-security-${LANE_ID:?}-$$"
trap 'docker rm -f "$name" >/dev/null 2>&1 || true' EXIT
image='ghcr.io/orange-opensource/hurl@sha256:d7727dcc0166de8aea88916e73ea435ee09bfecb8ba0c281200206b6cf37cf64'
cd "$fixture"
files=(s*.hurl)
[[ ${#files[@]} == 13 ]] || { echo 'Incomplete security fixture' >&2; exit 2; }
docker run --rm --name "$name" --label "agentmvc.lane.check=$LANE_ID" --network host \
  --mount "type=bind,source=$PWD,target=/security,readonly" \
  -w /security "$image" --test --jobs 1 --variable "host=http://127.0.0.1:$port" \
  --variable "uid=$(date +%s)$$" "${files[@]}"
