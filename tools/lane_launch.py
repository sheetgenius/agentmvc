"""Wait for shared Docker work before launching an unused measured session.

The frozen broker verifies its image under the shared resource lock before
binding HTTP. A different lane's benchmark can outlast the launcher's ten
second startup deadline. Queue before starting the measured clock, and retry
only that exact failure when no coding process has ever started.
"""
import shutil
import time
from unittest.mock import patch
from pathlib import Path

import lane_broker
import lane_run

ORIGINAL_LAUNCH = lane_run.launch


def launch(path):
    session = lane_run.load(path)
    logs, home = Path(session["logs"]), Path(session["home"])
    record = {"adapter": "tools/lane_launch.py", "sha256": lane_run.digest(Path(__file__)),
              "coding_inputs_changed": False, "queue_seconds": 0, "pre_coding_retries": []}
    logs.mkdir(exist_ok=True)
    original_popen = lane_run.subprocess.Popen

    def popen(argv, *args, **kwargs):
        if session["phase"] == "one-shot" and len(argv) > 1 and argv[1] == str(lane_run.ROOT / "tools/lane_broker.py"):
            import lane_oneshot
            effective = lane_oneshot.verify(session)
            proof = lane_run.load(Path(session["control"]) / "readiness-preflight.json")
            if not proof.get("passed") or proof["effective_fixture_sha256"] != effective["sha256"]:
                raise RuntimeError("One-shot TCP-readiness preflight required")
            argv = [argv[0], str(lane_run.ROOT / "tools/lane_oneshot.py"), "broker", *argv[2:]]
            record.update(coding_inputs_changed=True, effective_fixture_sha256=effective["sha256"])
        return original_popen(argv, *args, **kwargs)
    try:
        for attempt in range(1, 4):
            before = time.monotonic()
            with lane_broker.resources():
                pass
            record["queue_seconds"] += round(time.monotonic() - before, 2)
            try:
                with patch.object(lane_run.subprocess, "Popen", popen):
                    return ORIGINAL_LAUNCH(path)
            except RuntimeError as error:
                unused = not (logs / "events.jsonl").exists() and not (home / "sessions").exists()
                if str(error) != "Broker did not listen" or not unused:
                    raise
                record["pre_coding_retries"].append({"attempt": attempt, "reason": str(error),
                                                    "coding_started": False, "time": lane_run.stamp()})
                if (logs / "broker.log").exists():
                    shutil.copy2(logs / "broker.log", logs / f"broker-start-attempt-{attempt}.log")
                if attempt == 3:
                    raise
    finally:
        lane_run.save(logs / "launch-adapter.json", record)
