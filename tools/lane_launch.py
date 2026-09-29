"""Wait for shared Docker work before launching an unused measured session.

The frozen broker verifies its image under the shared resource lock before
binding HTTP. A different lane's benchmark can outlast the launcher's ten
second startup deadline. Queue before starting the measured clock, and retry
only that exact failure when no coding process has ever started.
"""
import shutil
import time
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
    try:
        for attempt in range(1, 4):
            before = time.monotonic()
            with lane_broker.resources():
                pass
            record["queue_seconds"] += round(time.monotonic() - before, 2)
            try:
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
