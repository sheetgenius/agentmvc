#!/usr/bin/env bash
# Build the toolchain image, then the compiled production image (and optionally the CRuby and Rails images).
#
# usage: [BUILD_DIR=reproduce/build] reproduce/build-images.sh [toolchain] [compiled] [cruby] [reference]
#        (no targets = toolchain compiled)
#
# Tags default to the names Dockerfile.production and the evidence use; override with TOOLCHAIN_TAG,
# COMPILED_TAG, CRUBY_TAG, REFERENCE_TAG. Extra `docker build` flags: DOCKER_BUILD_FLAGS.
# Run prepare-toolchain.sh first. Needs Docker with BuildKit (cache mounts).
set -euo pipefail

here=$(cd "$(dirname "$0")" && pwd)
pkg=$(dirname "$here")
repo=$(cd "$pkg/../../.." && pwd)
export CONDUIT_V8B_DOCKER_REAL=${CONDUIT_V8B_DOCKER_REAL:-$(command -v docker)}
export PATH="$here/bin:$PATH"
build=${BUILD_DIR:-$here/build}
export BUILDX_CONFIG=${BUILDX_CONFIG:-$build/buildx}
TOOLCHAIN_TAG=${TOOLCHAIN_TAG:-conduit-v8b-toolchain:2fce0ce9ff06}  # default of ARG TOOLCHAIN_IMAGE
COMPILED_TAG=${COMPILED_TAG:-conduit-v8b-app:compiled}
CRUBY_TAG=${CRUBY_TAG:-conduit-v8b-app:cruby}
REFERENCE_TAG=${REFERENCE_TAG:-conduit-v8b-rails:reference-1}
read -r -a flags <<< "${DOCKER_BUILD_FLAGS:-}"
targets=("$@"); [[ ${#targets[@]} -gt 0 ]] || targets=(toolchain compiled)

for target in "${targets[@]}"; do
  case "$target" in
    toolchain)
      ctx=$build/toolchain-context
      [[ -f "$ctx/Dockerfile" && -d "$ctx/vendor/spinel" ]] || { echo "run prepare-toolchain.sh first" >&2; exit 1; }
      docker build --progress=plain ${flags[@]+"${flags[@]}"} -t "$TOOLCHAIN_TAG" "$ctx"
      docker run --name conduit-v8b-toolchain-version "$TOOLCHAIN_TAG" sh -c 'ruby --version && roundhouse --version && spinel --version && spin --version'
      docker rm conduit-v8b-toolchain-version >/dev/null
      ;;
    compiled)  # same Dockerfile and source the production gate builds; .dockerignore comes from the source
      docker build --progress=plain ${flags[@]+"${flags[@]}"} --build-arg "TOOLCHAIN_IMAGE=$TOOLCHAIN_TAG" \
        -f "$pkg/toolchain/Dockerfile.production" -t "$COMPILED_TAG" "$pkg/variant/source"
      docker image inspect "$COMPILED_TAG" --format '{{.Id}} {{.Size}}'
      ;;
    cruby)     # the compile variant's own Rails Dockerfile (control for source changes)
      docker build --progress=plain ${flags[@]+"${flags[@]}"} -t "$CRUBY_TAG" "$pkg/variant/source"
      ;;
    reference) # the unmodified Rails reference-1 (baseline for evidence/edge)
      docker build --progress=plain ${flags[@]+"${flags[@]}"} -t "$REFERENCE_TAG" \
        "$repo/results/one-shot-v2-rails-expert/pilot-1/reference-1/source"
      ;;
    *) echo "unknown target: $target" >&2; exit 2 ;;
  esac
done
