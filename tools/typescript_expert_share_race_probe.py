"""Reviewer probe: a keyed write waiting behind a committed share revocation."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
import argparse
import hashlib
import json
import time

import typescript_expert_heldout as heldout


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--image", default=heldout.IMAGE)
    parser.add_argument("--source", type=Path, default=heldout.SOURCE)
    parser.add_argument("--output", type=Path,
                        default=heldout.RESULT / "held-out-share-revocation.json")
    args = parser.parse_args()
    heldout.IMAGE = args.image
    heldout.SOURCE = args.source
    heldout.NETWORK = "agentmvc-ts-expert-share-race-net"
    heldout.DB = "agentmvc-ts-expert-share-race-db"
    heldout.APP = "agentmvc-ts-expert-share-race-app"
    heldout.PORT = 4121
    heldout.BASE = f"http://127.0.0.1:{heldout.PORT}"
    before = heldout.source_digest()
    record = {
        "condition": "post-run-held-out-share-revocation-diagnostic",
        "source_tree_sha256": before,
        "image_sha256": heldout.IMAGE,
        "reviewer_script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "started": datetime.now(timezone.utc).isoformat(),
        "expected": "a keyed edit whose article write waits behind a committed revocation returns 404 and does not change the article",
    }
    try:
        heldout.startup()
        registered = heldout.response("POST", "/api/users", {"user": {
            "username": "share_race", "email": "share_race@example.test",
            "password": "password123",
        }})
        assert registered["status"] == 201, heldout.public(registered)
        token = registered["body"]["user"]["token"]
        created = heldout.article("Revocation race", token)
        slug = created["slug"]
        article_id = int(heldout.sql(f"select id from articles where slug = '{slug}'"))
        issued = heldout.response("POST", f"/api/articles/{slug}/share", token=token)
        assert issued["status"] == 201, heldout.public(issued)
        share = issued["body"]["share"]

        # A database transaction holds the article lock and changes the share,
        # without committing yet. The first activeShare SELECT sees the old
        # committed row, but the content UPDATE must wait for this transaction.
        work = (f"select id from articles where slug = '{slug}' for update; "
                f"update shares set revoked_at = now() where id = '{share['id']}'")
        with ThreadPoolExecutor(max_workers=1) as pool:
            with heldout.lock_row(work):
                future = pool.submit(
                    heldout.response, "PUT", f"/api/shares/{share['id']}/article",
                    {"article": {"title": "After revocation", "body": "Must not commit",
                                 "revision": 1}}, key=share["key"], timeout=30,
                )
                deadline = time.monotonic() + 10
                blocked = 0
                while time.monotonic() < deadline:
                    blocked = max(blocked, int(heldout.sql(
                        "select count(*) from pg_stat_activity where pid <> pg_backend_pid() "
                        "and wait_event_type = 'Lock' and "
                        "(query ilike 'update articles set%' or "
                        "query ilike 'select id from articles where id =%for update%')"
                    )))
                    if blocked:
                        break
                    if future.done():
                        break
                    time.sleep(.05)
                record["blocked_content_writes_before_commit"] = blocked
                record["request_pending_before_commit"] = not future.done()
            edit = future.result(timeout=35)
        current = json.loads(heldout.sql(
            "select json_build_object('revision', revision, 'body', body)::text "
            f"from articles where id = {article_id}"
        ))
        record["edit_status"] = edit["status"]
        record["edit_body"] = heldout.public(edit["body"])
        record["revision_after"] = current["revision"]
        record["body_after"] = current["body"]
        record["source_tree_unchanged"] = heldout.source_digest() == before
        record["finished"] = datetime.now(timezone.utc).isoformat()
        args.output.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
        print(json.dumps(record, indent=2))
    except Exception as error:
        record["error"] = f"{type(error).__name__}: {error}"
        record["finished"] = datetime.now(timezone.utc).isoformat()
        args.output.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
        raise
    finally:
        heldout.cleanup()


if __name__ == "__main__":
    main()
