#!/usr/bin/env bash
# Assemble a gate workspace and run the unmodified fresh-production gate (tools/one_shot_host/check-production.sh).
#
# usage: [BUILD_DIR=reproduce/build] reproduce/run-gate.sh [compiled|rails] [PORT]   (defaults: compiled 4440)
#
# Workspace = variant/source + the repo's frozen gate inputs, laid out as for the Rails expert v2 workspaces
# (tools/rails_expert_v2.py prepare):
#   realworld_spec/  <- spec/ and one-shot/frontend/   (files listed in one-shot/fixture-manifest.json)
#   security/hurl/   <- tools/security/hurl/           (same manifest)
#   harness/         <- one-shot/harness/ + one-shot-v2-rails-expert/rails.sh + tools/quick-smoke.sh
#   harness/browser-image-id <- ID of the local conduit-v7-browser:1.63.0 image (built here if missing)
# "compiled" replaces the variant's Rails Dockerfile with toolchain/Dockerfile.production, which needs the
# toolchain image from build-images.sh under its default tag. "rails" keeps the variant's own Dockerfile.
# The naming adapter maps the gate resources to conduit-v7-gate-*; the host check scripts are unchanged.
# ASSEMBLE_ONLY=1 builds the workspace and stops before the gate.
set -euo pipefail

here=$(cd "$(dirname "$0")" && pwd)
pkg=$(dirname "$here")
repo=$(cd "$pkg/../../.." && pwd)
# The frozen host scripts retain their exact bytes; the adapter names resources and saves cleanup logs.
export CONDUIT_V7_DOCKER_REAL=${CONDUIT_V7_DOCKER_REAL:-$(command -v docker)}
export PATH="$here/bin:$PATH"
kind=${1:-compiled}
port=${2:-4440}
build=${BUILD_DIR:-$here/build}
export BUILDX_CONFIG=${BUILDX_CONFIG:-$build/buildx}
browser=conduit-v7-browser:1.63.0
toolchain=conduit-v7-toolchain:241f8d692ce5
# Digest of harness/, realworld_spec/ and security/ (minus browser-image-id) in the published gate workspace.
INPUTS_SHA256=a8999f01c936cc37fe182c314c7a9a602b62611c1a15dc8338e7853d30831710

case "$kind" in compiled|rails) ;; *) echo "usage: $0 [compiled|rails] [PORT]" >&2; exit 2;; esac
mkdir -p "$build"
build=$(cd "$build" && pwd)
export CONDUIT_V7_CAPTURE_DIR="$build/container-logs"
ws=$build/conduit-v7-ws-$kind
rm -rf "$ws"
mkdir -p "$ws"
cp -a "${SOURCE_DIR:-$pkg/variant/source}/." "$ws/"
if [[ $kind == compiled ]]; then
  cp "$pkg/toolchain/Dockerfile.production" "$ws/Dockerfile"
  docker image inspect "$toolchain" >/dev/null 2>&1 || { echo "missing $toolchain; run build-images.sh" >&2; exit 1; }
fi

python3 - "$repo" "$ws" "$INPUTS_SHA256" <<'PY'
import hashlib, json, os, shutil, sys
repo, ws, expected = sys.argv[1:]
digest = lambda p: hashlib.sha256(open(p, "rb").read()).hexdigest()
manifest = json.load(open(os.path.join(repo, "one-shot/fixture-manifest.json")))["files"]
routes = [("spec/", "realworld_spec/"), ("one-shot/frontend/", "realworld_spec/frontend/"),
          ("tools/security/hurl/", "security/hurl/"), ("one-shot/harness/", "harness/")]
copies = [(name, dest + name[len(src):]) for name in manifest for src, dest in routes if name.startswith(src)]
copies += [("one-shot-v2-rails-expert/rails.sh", "harness/rails.sh"), ("tools/quick-smoke.sh", "harness/quick-smoke.sh")]
for name, dest in copies:
    source = os.path.join(repo, name)
    if name in manifest and digest(source) != manifest[name]:
        sys.exit(f"frozen input changed since the fixture manifest: {name}")
    os.makedirs(os.path.dirname(os.path.join(ws, dest)), exist_ok=True)
    shutil.copy2(source, os.path.join(ws, dest))
lines = sorted((f"{digest(os.path.join(ws, d))}  {d}\n" for _, d in copies), key=lambda l: l[66:])
got = hashlib.sha256("".join(lines).encode()).hexdigest()
if got != expected:
    sys.exit(f"assembled gate inputs {got} differ from the published workspace {expected}")
print(f"gate inputs: {len(lines)} files, sha256 {got} (matches the published workspace)")
PY

if ! docker image inspect "$browser" >/dev/null 2>&1; then
  docker build --progress=plain -f "$repo/one-shot/harness/Dockerfile.browser" -t "$browser" "$repo/one-shot"
fi
docker image inspect "$browser" --format '{{.Id}}' > "$ws/harness/browser-image-id"

log=$build/gate-$kind.log
echo "workspace: $ws"
[[ "${ASSEMBLE_ONLY:-}" == 1 ]] && exit 0
echo "log: $log"
# check-production.sh removes its containers without -v, which would leave PostgreSQL's anonymous data volume.
# Record the volumes its containers mount while it runs, and remove them afterwards.
volumes=$build/gate-$kind.volumes
: > "$volumes"
( while sleep 2; do
    for c in $(docker ps -q --filter "name=agentmvc-one-shot-$(basename "$ws")-"); do
      docker inspect -f '{{range .Mounts}}{{if eq .Type "volume"}}{{println .Name}}{{end}}{{end}}' "$c" 2>/dev/null
    done >> "$volumes"
  done ) &
watcher=$!
set +e
ONE_SHOT_WORKDIR="$ws" "$repo/tools/one_shot_host/check-production.sh" "$port" 2>&1 | tee "$log"
status=${PIPESTATUS[0]}
set -e
kill "$watcher" 2>/dev/null || true
for v in $(sort -u "$volumes"); do docker volume rm "$v" >/dev/null 2>&1 && echo "removed volume $v"; done
echo "check-production.sh exit $status"
exit "$status"
