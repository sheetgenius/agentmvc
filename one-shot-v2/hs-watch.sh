#!/usr/bin/env bash
# Poll source files so reload also works when the host bind mount misses inotify events.
set -uo pipefail
fingerprint() {
  { find app src migrations -type f \( -name '*.hs' -o -name '*.sql' \) -print0 2>/dev/null || true
    printf '%s\0' conduit.cabal cabal.project cabal.project.freeze
  } | sort -z | xargs -0 -r sha256sum 2>/dev/null | sha256sum
}
while true; do
  previous="$(fingerprint)"
  setsid cabal run exe:conduit &
  server=$!
  while kill -0 "$server" 2>/dev/null; do
    sleep 0.5
    if [[ "$(fingerprint)" != "$previous" ]]; then
      kill -TERM -- "-$server" 2>/dev/null || true
      wait "$server" 2>/dev/null || true
      break
    fi
  done
  sleep 1
done
