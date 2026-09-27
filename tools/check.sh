#!/bin/sh
# Check one step of one stack the way the reviewer did:  tools/check.sh STACK STEP
# Materializes the step's directory in .work/, runs the stack's setup, then bin/check and, if the step has one,
# bin/check-production. Needs Docker and the stack's toolchain (see stacks/STACK/ENVIRONMENT.md).
set -eu
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
STACK="$1"; STEP="$2"
case "$STACK" in ''|*[!a-z0-9_-]*) echo 'invalid stack name' >&2; exit 2;; esac
case "$STEP" in ''|*[!a-z0-9_-]*) echo 'invalid step name' >&2; exit 2;; esac
DEST="$ROOT/.work/$STACK-$STEP"
python3 "$ROOT/tools/workdir.py" "$STACK" "$STEP" "$DEST" >/dev/null
SETUP="$(python3 -c 'import json, sys; print(json.load(open(sys.argv[1])).get("setup") or "")' "$ROOT/stacks/$STACK/stack.json")"
cd "$DEST"
if [ -n "$SETUP" ]; then sh -c "$SETUP"; fi
bin/check
if [ -x bin/check-production ]; then bin/check-production; fi
if [ "$STEP" = 8-live-editing ]; then
  python3 "$ROOT/tools/live_fixture.py" verify-workdir "$DEST" >/dev/null
fi
cd "$ROOT"
rm -rf "$DEST" "$ROOT/.work/$STACK-$STEP.logs"
echo "PASS $STACK $STEP"
