#!/bin/sh
# Scan one step of one stack:  tools/security/scan.sh STACK STEP
# Builds the step's production image, runs the 13 black-box checks, OSV-Scanner and the stack's analyzer, and writes
# results/security/STEP-STACK.json. Needs Docker.
set -eu
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
STACK="$1"; STEP="$2"; N="${STEP%%-*}"
DEST="$ROOT/.work/$STACK-$STEP"
python3 "$ROOT/tools/workdir.py" "$STACK" "$STEP" "$DEST" >/dev/null
docker build -q -t "agentmvc-$STACK-$N" "$DEST" >/dev/null
OUT="$ROOT/.work/scan-$STACK-$STEP"
python3 "$ROOT/tools/security/scan.py" "agentmvc-$STACK-$N" "$STACK" "$DEST" "$OUT"
mkdir -p "$ROOT/results/security"
cp "$OUT/results.json" "$ROOT/results/security/$STEP-$STACK.json"
echo "wrote results/security/$STEP-$STACK.json"
