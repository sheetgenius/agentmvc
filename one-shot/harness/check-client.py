#!/usr/bin/env python3
"""Call the coordinator's fixed Docker-backed checks without a Docker socket."""
import json
import os
import sys
import urllib.error
import urllib.request

if len(sys.argv) < 3:
    raise SystemExit("usage: check-client.py ACTION PORT [container command ...]")
token = os.environ.get("ONE_SHOT_BROKER_TOKEN")
if not token:
    raise SystemExit("ONE_SHOT_BROKER_TOKEN is missing; ask the orchestrator to start the check service")
payload = json.dumps({"action": sys.argv[1], "port": int(sys.argv[2]), "argv": sys.argv[3:]}).encode()
request = urllib.request.Request(
    f"http://127.0.0.1:{int(os.environ.get('ONE_SHOT_BROKER_PORT', '49671'))}/run", payload,
    {"Content-Type": "application/json", "Authorization": f"Bearer {token}"},
)
try:
    with urllib.request.urlopen(request, timeout=3600) as response:
        while chunk := response.read(65536):
            sys.stdout.buffer.write(chunk)
            sys.stdout.buffer.flush()
except urllib.error.HTTPError as error:
    sys.stderr.write(error.read().decode(errors="replace"))
    raise SystemExit(1)
