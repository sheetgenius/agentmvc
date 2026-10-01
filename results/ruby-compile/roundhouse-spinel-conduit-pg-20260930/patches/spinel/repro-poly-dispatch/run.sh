#!/bin/sh
# Run inside the toolchain container, cwd = this directory:
#   docker run --rm --name spinel-spike-c01-x --cpus 8 \
#     -v <c01 dir>:/w -w /w/repro/final spinel-spike-w01-toolchain:latest sh run.sh
# STOCK   = the image's spinel (813def1fb)
# PATCHED = /w/spinel/spinel (813def1fb + patch/spinel-poly-dispatch-arg-roots.patch, built in /w/spinel)
STOCK=${STOCK:-spinel}
PATCHED=${PATCHED:-/w/spinel/spinel}
set -x
$STOCK   tag_time_merge.rb --rbs . -o /tmp/stock   >/dev/null
$PATCHED tag_time_merge.rb --rbs . -o /tmp/patched >/dev/null
/tmp/stock 300;                     echo "stock rc=$?"
SPINEL_GC_STRESS=1 /tmp/stock 300 | tail -4
/tmp/patched 300;                   echo "patched rc=$?"
SPINEL_GC_STRESS=1 /tmp/patched 300; echo "patched stress rc=$?"
