#!/usr/bin/env bash
# Fast feedback for an already-running candidate. Full acceptance is separate.
set -euo pipefail
python3 - "${1:?usage: tools/quick-smoke.sh PORT}" <<'PY'
import json
import sys
from urllib.request import urlopen

base = f"http://127.0.0.1:{int(sys.argv[1])}"
try:
    with urlopen(f"{base}/api/tags", timeout=3) as response:
        tags = json.load(response)
    assert isinstance(tags.get("tags"), list)
    with urlopen(f"{base}/api/articles?limit=1", timeout=3) as response:
        page = json.load(response)
    assert isinstance(page.get("articles"), list)
    assert isinstance(page.get("articlesCount"), int)
except Exception as error:
    raise SystemExit(f"FAIL quick smoke on port {sys.argv[1]}: {error}") from None
print("PASS quick smoke: tags and article list")
PY
