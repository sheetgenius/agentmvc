#!/usr/bin/env bash
# Build IHP's Nix image without a host Docker socket in the agent workspace,
# then run the unchanged production acceptance gate through its Dockerfile.
set -euo pipefail
root="${ONE_SHOT_WORKDIR:?}"
port="${1:?usage: check-production.sh PORT}"
[[ "$port" == 4104 ]] || { echo 'Wrong IHP port' >&2; exit 2; }
run="$(basename "$(dirname "$root")")"
case "$run" in one-shot-ihp-1|one-shot-ihp-2|one-shot-ihp-3) ;; *) echo 'Wrong IHP workdir' >&2; exit 2;; esac
volume="agentmvc-ihp-nix-run${run##*-}"
docker run --rm \
  --mount "type=volume,source=$volume,target=/nix" \
  --mount "type=bind,source=$root,target=/work/app" \
  --mount "type=bind,source=$root/realworld_spec,target=/work/app/realworld_spec,readonly" \
  --mount "type=bind,source=$root/security,target=/work/app/security,readonly" \
  --mount "type=bind,source=$root/harness,target=/work/app/harness,readonly" \
  --mount "type=bind,source=$root/.scaffold,target=/work/app/.scaffold,readonly" \
  --mount "type=bind,source=$root/PROMPT.md,target=/work/app/PROMPT.md,readonly" \
  --mount "type=bind,source=$root/ENVIRONMENT.md,target=/work/app/ENVIRONMENT.md,readonly" \
  --mount "type=bind,source=$root/MEASUREMENT.md,target=/work/app/MEASUREMENT.md,readonly" \
  --mount "type=bind,source=$root/EXPERIMENT.md,target=/work/app/EXPERIMENT.md,readonly" \
  --mount "type=bind,source=$root/FIXTURE.json,target=/work/app/FIXTURE.json,readonly" \
  -w /work/app nixos/nix:2.31.2 sh -eu -c '
    image=$(nix --extra-experimental-features "nix-command flakes" --accept-flake-config build --no-link --print-out-paths .#agentmvc-image)
    cat "$image"
  ' | docker load
"$(dirname "$0")/../one_shot_host/check-production.sh" "$port"
