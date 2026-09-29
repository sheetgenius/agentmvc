"""Separate reviewer probe for concurrent login-limit accounting on expert-1."""
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json
import threading
import time

import typescript_expert_heldout as heldout


heldout.NETWORK = "agentmvc-ts-expert-login-net"
heldout.DB = "agentmvc-ts-expert-login-db"
heldout.APP = "agentmvc-ts-expert-login-app"
heldout.PORT = 4119
heldout.BASE = f"http://127.0.0.1:{heldout.PORT}"
OUTPUT = heldout.RESULT / "held-out-login.json"
BURST = 25


def main():
    source_hash = heldout.source_digest()
    record = {
        "condition": "post-run-held-out-login-diagnostic",
        "source_tree_sha256": source_hash,
        "image_sha256": heldout.IMAGE,
        "reviewer_script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "started": datetime.now(timezone.utc).isoformat(),
        "burst": BURST,
        "expected": "the first 20 failed attempts are counted; later attempts in the window receive 429",
    }
    try:
        heldout.startup()
        registered = heldout.response("POST", "/api/users", {"user": {
            "username": "limiter_burst", "email": "limiter_burst@example.test",
            "password": "correct-password-123",
        }})
        assert registered["status"] == 201, heldout.public(registered)
        barrier = threading.Barrier(BURST)

        def fail(_number):
            barrier.wait(timeout=10)
            return heldout.response("POST", "/api/users/login", {"user": {
                "email": "limiter_burst@example.test", "password": "wrong-password-123",
            }}, timeout=30)["status"]

        with ThreadPoolExecutor(max_workers=BURST) as pool:
            # Hold SELECTs after each handler has read the old failure count.
            # The handler reads its Map before the first await, so this makes
            # overlap observable without modifying measured application code.
            with heldout.lock_row("lock table users in access exclusive mode"):
                futures = [pool.submit(fail, number) for number in range(BURST)]
                deadline = time.monotonic() + 10
                blocked = 0
                while time.monotonic() < deadline:
                    blocked = max(blocked, int(heldout.sql(
                        "select count(*) from pg_stat_activity where pid <> pg_backend_pid() "
                        "and wait_event_type = 'Lock' and query ilike 'select * from users where email%'"
                    )))
                    if blocked >= 2 and all(not future.done() for future in futures):
                        break
                    time.sleep(.05)
                record["blocked_login_selects_before_release"] = blocked
                record["all_requests_pending_before_release"] = all(
                    not future.done() for future in futures)
            statuses = [future.result(timeout=40) for future in futures]
        next_failure = heldout.response("POST", "/api/users/login", {"user": {
            "email": "limiter_burst@example.test", "password": "wrong-password-123",
        }})
        record["burst_statuses"] = dict(sorted(Counter(statuses).items()))
        record["next_status"] = next_failure["status"]
        record["next_body"] = heldout.public(next_failure["body"])
        record["source_tree_unchanged"] = heldout.source_digest() == source_hash
        record["finished"] = datetime.now(timezone.utc).isoformat()
        OUTPUT.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
        print(json.dumps(record, indent=2))
    except Exception as error:
        record["error"] = f"{type(error).__name__}: {error}"
        record["finished"] = datetime.now(timezone.utc).isoformat()
        OUTPUT.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
        raise
    finally:
        heldout.cleanup()


if __name__ == "__main__":
    main()
