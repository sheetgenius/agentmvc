#!/usr/bin/env python3
"""Serialize reproduction with AgentMVC's lane Docker lock (macOS/Linux)."""
import fcntl
import os
from pathlib import Path
import subprocess
import sys

if len(sys.argv) < 2:
    raise SystemExit("usage: with-docker-lock.py COMMAND [ARG ...]")
repo = Path(__file__).resolve().parents[4]
common = Path(subprocess.check_output(
    ["git", "-C", str(repo), "rev-parse", "--path-format=absolute", "--git-common-dir"],
    text=True).strip())
lock = Path(os.environ.get("AGENTMVC_DOCKER_LOCK", str(common.parent / ".work/lane-docker.lock")))
if not lock.exists():
    lock.parent.mkdir(parents=True, exist_ok=True)
    lock.touch()
with lock.open("r") as stream:
    print("Waiting for shared Docker lock: " + str(lock), flush=True)
    fcntl.flock(stream, fcntl.LOCK_EX)
    raise SystemExit(subprocess.call(sys.argv[1:]))
