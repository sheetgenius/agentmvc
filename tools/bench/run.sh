#!/bin/sh
# Benchmark one step of one stack:  tools/bench/run.sh STACK STEP
# Builds the step's production image and writes results/speed/STEP-STACK.json. Needs Docker; run one at a time on a
# quiet machine, and compare stacks only with runs from the same session.
set -eu
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
STACK="$1"; STEP="$2"; N="${STEP%%-*}"
DEST="$ROOT/.work/$STACK-$STEP"
python3 "$ROOT/tools/workdir.py" "$STACK" "$STEP" "$DEST" >/dev/null
docker build -q -t "agentmvc-$STACK-$N" "$DEST" >/dev/null
OUT="$ROOT/.work/bench-$STACK-$STEP"
python3 "$ROOT/tools/bench/bench.py" "agentmvc-$STACK-$N" "$STACK-$N" "$OUT"
mkdir -p "$ROOT/results/speed"
cp "$OUT/results.json" "$ROOT/results/speed/$STEP-$STACK.json"
echo "wrote results/speed/$STEP-$STACK.json"
