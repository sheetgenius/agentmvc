#!/usr/bin/env bash
set -euo pipefail
roundhouse --target spinel -o /work/emitted /source
cd /work/emitted
spin build -- --cc=clang --jobs=8
mkdir -p /output/runtime/storage
set -- build/bin/*
test "$#" -eq 1
test -x "$1"
cp "$1" /output/runtime/server
for directory in db config public static; do
  if [[ -d "$directory" ]]; then
    cp -a "$directory" /output/runtime/
  fi
done
