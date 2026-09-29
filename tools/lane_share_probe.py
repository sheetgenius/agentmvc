#!/usr/bin/env python3
"""Supplemental shared-edit diagnostic for any disposable final application.

Uses an already running app; never starts services. Each case gets a fresh
article and share. Reports contain only statuses, types, counts and booleans.
This is not a frozen acceptance gate. Extra envelope keys are quality-only.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from uuid import uuid4

from reviewer_common_http_probe import Client, article_path, field, share_path


CONDITION = "supplemental shared-edit diagnostic; not a frozen gate"
REVISION_SOURCE = "spec/features/live-editing/live-editing.md:21-23; spec/features/drafts/drafts.md:65-74"
ENVELOPE_SOURCE = "spec/features/live-editing/live-editing.md:21 (exact envelope interpretation; quality only)"


def metadata(response):
    return {"status": response["status"], "body_kind": type(response.get("body")).__name__}


def record(results, name, kind, source, expected, observed):
    results.append({"name": name, "kind": kind, "source": source,
                    "expected": expected, "observed": observed,
                    "passed": all(type(observed.get(k)) is type(v) and observed[k] == v
                                  for k, v in expected.items())})


def setup(results, name, response, status, usable):
    observed = metadata(response) | {"usable_response": bool(usable)}
    record(results, name, "setup", "spec/features/live-editing/live-editing.md:7-19",
           {"status": status, "usable_response": True}, observed)
    if not results[-1]["passed"]:
        raise RuntimeError("setup failed")


def shared_shape(article):
    return (isinstance(article, dict)
            and set(article) == {"slug", "title", "body", "revision"}
            and all(isinstance(article[k], str) for k in ("slug", "title", "body"))
            and type(article["revision"]) is int and article["revision"] >= 1)


def run(client, results):
    suffix = uuid4().hex[:16]
    username = "shareprobe_" + suffix
    response = client.call("POST", "/api/users", {"user": {
        "username": username, "email": username + "@example.com",
        "password": "Share-probe-" + uuid4().hex,
    }})
    token = field(response, "user", "token")
    setup(results, "setup/register", response, 201, isinstance(token, str) and bool(token))

    for name, supplied, kind in (("valid_revision", None, "contract"),
                                 ("revision_zero", 0, "contract"),
                                 ("revision_negative", -1, "contract"),
                                 ("extra_envelope_key", None, "quality_diagnostic")):
        response = client.call("POST", "/api/articles", {"article": {
            "title": f"Share probe {name} {suffix}", "description": "Diagnostic",
            "body": "Initial body",
        }}, token=token)
        slug = field(response, "article", "slug")
        setup(results, name + "/create", response, 201, isinstance(slug, str) and bool(slug))
        owner_path = article_path(slug)
        before_owner = client.call("GET", owner_path, token=token)
        setup(results, name + "/owner_read", before_owner, 200,
              isinstance(field(before_owner, "article"), dict))
        response = client.call("POST", owner_path + "/share", token=token)
        identifier, key = field(response, "share", "id"), field(response, "share", "key")
        setup(results, name + "/share", response, 201,
              isinstance(identifier, str) and bool(identifier) and isinstance(key, str) and bool(key))
        path = share_path(identifier)
        before = client.call("GET", path, key=key)
        snapshot = field(before, "article")
        setup(results, name + "/shared_read", before, 200, shared_shape(snapshot))
        revision = snapshot["revision"] if supplied is None else supplied
        title, body = "Edited " + snapshot["title"], "Edited body"
        payload = {"article": {"title": title, "body": body, "revision": revision}}
        if kind == "quality_diagnostic":
            payload["extra"] = True
        response = client.call("PUT", path, payload, key=key)
        after = client.call("GET", path, key=key)
        observed = metadata(response) | {"read_status": after["status"]}
        if name == "valid_revision":
            updated = field(response, "article")
            valid = shared_shape(updated)
            observed.update(
                exact_shared_shape=valid,
                revision_incremented_once=valid and updated["revision"] == snapshot["revision"] + 1,
                submitted_fields_saved=valid and updated["title"] == title and updated["body"] == body,
                persisted_response=valid and field(after, "article") == updated,
            )
            expected = {"status": 200, "read_status": 200, "exact_shared_shape": True,
                        "revision_incremented_once": True, "submitted_fields_saved": True,
                        "persisted_response": True}
        else:
            after_owner = client.call("GET", owner_path, token=token)
            observed.update(
                article_unchanged=field(after, "article") == snapshot,
                owner_read_status=after_owner["status"],
                full_article_unchanged=field(after_owner, "article") == field(before_owner, "article"),
            )
            expected = {"status": 422 if kind == "quality_diagnostic" else 409,
                        "read_status": 200, "article_unchanged": True,
                        "owner_read_status": 200, "full_article_unchanged": True}
            if kind == "contract":
                observed.update(stale_error=field(response, "errors", "revision") == ["is stale"],
                                current_article_returned=field(response, "article") == snapshot)
                expected.update(stale_error=True, current_article_returned=True)
            else:
                observed["structured_errors"] = isinstance(field(response, "errors"), dict)
                expected["structured_errors"] = True
        record(results, name, kind, ENVELOPE_SOURCE if kind == "quality_diagnostic" else REVISION_SOURCE,
               expected, observed)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--timeout", type=float, default=10.0)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--strict-diagnostics", action="store_true")
    args = parser.parse_args()
    results = []
    payload = {"condition": CONDITION, "results": results}
    try:
        if not math.isfinite(args.timeout) or not 0 < args.timeout <= 60:
            raise ValueError("invalid timeout")
        run(Client(args.base_url, args.timeout), results)
    except Exception as error:
        # Exception messages and response values can contain secrets or URLs.
        payload["fatal_error_type"] = type(error).__name__
    summary = {}
    for kind in ("setup", "contract", "quality_diagnostic"):
        cases = [case for case in results if case["kind"] == kind]
        summary[kind + "_passed"] = sum(case["passed"] for case in cases)
        summary[kind + "_total"] = len(cases)
    payload["summary"] = summary
    rendered = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.write_text(rendered)
    else:
        print(rendered, end="")
    if "fatal_error_type" in payload:
        return 2
    return int(any(not case["passed"] for case in results
                   if case["kind"] != "quality_diagnostic" or args.strict_diagnostics))


if __name__ == "__main__":
    raise SystemExit(main())
