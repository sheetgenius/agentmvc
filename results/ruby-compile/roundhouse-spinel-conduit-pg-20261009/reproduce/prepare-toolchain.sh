#!/usr/bin/env bash
# Rebuild the toolchain Docker build context from the public upstreams plus this package's patches.
#
# usage: reproduce/prepare-toolchain.sh [BUILD_DIR]     (default: reproduce/build)
#
# Produces BUILD_DIR/toolchain-context/ = Dockerfile (toolchain/Dockerfile.toolchain), patches/ (the flat,
# checksummed patch set that the image carries) and vendor/{roundhouse,spinel} (patched source trees).
# Roundhouse gets the 10-patch series; Spinel is built as upstream has it (no local patches in v8).
# Needs: bash, git, python3, network access to github.com.
set -euo pipefail

ROUNDHOUSE_URL=${ROUNDHOUSE_URL:-https://github.com/rubys/roundhouse.git}
SPINEL_URL=${SPINEL_URL:-https://github.com/matz/spinel.git}
ROUNDHOUSE_SHA=ea4d3e682c86d817b2617b5862ed9a14d634f7eb
SPINEL_SHA=f85f04b3abef4b0540406948c56db7a51a420122
# SHA-256 of patches/roundhouse/SHA256SUMS; Dockerfile.production checks the same value inside the image.
MANIFEST_SHA256=2fce0ce9ff067966d7295f71206b6d7b3592da558b663352ed785fca93aa1777
# Spinel reads its version from .spinel-dist when built without .git (same content as `make dist` writes).
SPINEL_DIST=$'f85f04b3a\n2026.09.12+7503'
# Digests of the vendor trees used for the published toolchain image (see tree_digest below).
ROUNDHOUSE_TREE_SHA256=98a0841e6237677184707d459f71feba923a6be70c87b21533498d0ed31ebf5c
SPINEL_TREE_SHA256=cb4aee8b0d77b52a0cb52bff16a6202a70ea2858d94871a7d275366761f61f90

here=$(cd "$(dirname "$0")" && pwd)
pkg=$(dirname "$here")
build=${1:-$here/build}
mkdir -p "$build"
build=$(cd "$build" && pwd)
ctx=$build/toolchain-context
src=$build/src

sha256() { if command -v sha256sum >/dev/null; then sha256sum "$@"; else shasum -a 256 "$@"; fi; }
tree_digest() {  # sha256 over "<sha256>  <relative path>" of every regular file and symlink, sorted by path
  python3 - "$1" <<'PY'
import hashlib, os, sys
root = sys.argv[1]; lines = []
for d, dirs, files in os.walk(root):
    dirs[:] = [x for x in dirs if x != ".git"]
    for f in files:
        p = os.path.join(d, f); rel = os.path.relpath(p, root)
        data = os.readlink(p).encode() if os.path.islink(p) else open(p, "rb").read()
        lines.append(f"{hashlib.sha256(data).hexdigest()}  {rel}\n")
print(hashlib.sha256("".join(sorted(lines, key=lambda l: l[66:])).encode()).hexdigest())
PY
}

rm -rf "$ctx" "$src"
mkdir -p "$ctx/patches" "$ctx/vendor" "$src"

echo "== patches: assemble the flat set and verify SHA256SUMS"
cp "$pkg/patches/roundhouse/series" "$pkg/patches/roundhouse/SHA256SUMS" "$ctx/patches/"
while IFS= read -r p; do
  [[ -z "$p" || "$p" == \#* ]] && continue
  cp "$pkg/patches/roundhouse/$p" "$ctx/patches/$p"
done < "$pkg/patches/roundhouse/series"
(cd "$ctx/patches" && sha256 -c SHA256SUMS)
got=$(sha256 "$ctx/patches/SHA256SUMS" | cut -d' ' -f1)
[[ "$got" == "$MANIFEST_SHA256" ]] || { echo "SHA256SUMS digest $got != $MANIFEST_SHA256" >&2; exit 1; }
listed=$( (echo SHA256SUMS; awk '{print $2}' "$ctx/patches/SHA256SUMS") | LC_ALL=C sort)
present=$(cd "$ctx/patches" && ls | LC_ALL=C sort)
[[ "$listed" == "$present" ]] || { echo "patch set differs from SHA256SUMS" >&2; exit 1; }
echo "manifest sha256 $got OK"

clone() {  # url sha dir
  git init -q "$3"
  git -C "$3" remote add origin "$1"
  git -C "$3" fetch -q --tags origin "$2"
  git -C "$3" -c advice.detachedHead=false checkout -q "$2"
  [[ "$(git -C "$3" rev-parse HEAD)" == "$2" ]]
}

echo "== roundhouse $ROUNDHOUSE_SHA + series"
clone "$ROUNDHOUSE_URL" "$ROUNDHOUSE_SHA" "$src/roundhouse"
while IFS= read -r p; do
  [[ -z "$p" || "$p" == \#* ]] && continue
  echo "applying $p"
  git -C "$src/roundhouse" apply --index --whitespace=nowarn "$ctx/patches/$p"
done < "$ctx/patches/series"
git -C "$src/roundhouse" diff --cached --stat | tail -1

echo "== spinel $SPINEL_SHA (no local patches)"
clone "$SPINEL_URL" "$SPINEL_SHA" "$src/spinel"
described=$(git -C "$src/spinel" describe --tags --match '[0-9][0-9][0-9][0-9].[0-9][0-9].[0-9][0-9]' \
  --match '[0-9][0-9][0-9][0-9].[0-9][0-9].[0-9][0-9].[0-9]*' 2>/dev/null \
  | sed -e 's/-\([0-9][0-9]*\)-g[0-9a-f]*$/+\1/' || true)
[[ "$described" == "${SPINEL_DIST#*$'\n'}" ]] || echo "note: git describe gives '$described'; using recorded release string"

echo "== export vendor trees (without .git)"
for name in roundhouse spinel; do
  mkdir -p "$ctx/vendor/$name"
  tar -C "$src/$name" --exclude=./.git -cf - . | tar -C "$ctx/vendor/$name" -xf -
done
printf '%s\n' "$SPINEL_DIST" > "$ctx/vendor/spinel/.spinel-dist"
cp "$pkg/toolchain/Dockerfile.toolchain" "$ctx/Dockerfile"

status=0
for name in roundhouse spinel; do
  want=ROUNDHOUSE_TREE_SHA256; [[ $name == spinel ]] && want=SPINEL_TREE_SHA256
  got=$(tree_digest "$ctx/vendor/$name")
  if [[ "$got" == "${!want}" ]]; then echo "vendor/$name tree sha256 $got OK"
  else echo "vendor/$name tree sha256 $got differs from published ${!want}" >&2; status=1; fi
done
echo "context: $ctx"
exit $status
