#!/usr/bin/env bash
# Run build-images.sh after refreshing the Roundhouse source mtimes in its toolchain context.
# This runs inside the Docker lock, so no other build can write the shared Cargo target cache
# between the refresh and this build: Cargo must see every source as newer than its outputs.
# (Refreshing at prepare time let five candidate-01 omissions reuse without-60's binary.)
# usage: BUILD_DIR=<package>/reproduce/build fresh-build.sh <package>/reproduce/build-images.sh TARGET...
set -euo pipefail
ctx=${BUILD_DIR:?}/toolchain-context/vendor/roundhouse
[[ -f $ctx/build.rs ]] || { echo "missing $ctx" >&2; exit 2; }
find "$ctx/src" "$ctx/runtime" -type f -exec touch {} +
touch "$ctx/build.rs"
echo "refreshed mtimes under $ctx at $(date -u +%FT%TZ)"
exec "$@"
