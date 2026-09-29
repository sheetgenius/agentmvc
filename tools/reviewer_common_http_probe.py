#!/usr/bin/env python3
"""Reviewer-only Conduit HTTP probes against an already-running disposable app.

This script is outside every frozen fixture and never starts Docker. It creates
users and articles, so point it at a disposable database. The JSON output keeps
contract assertions separate from extra quality diagnostics. The same request
sequence can be used for Rails, TypeScript, and Phoenix.

Examples:
  python3 tools/reviewer_common_http_probe.py --base-url http://127.0.0.1:4101
  python3 tools/reviewer_common_http_probe.py --base-url http://127.0.0.1:4101 \
    --output /tmp/rails-parity.json

Contract sources are paths relative to the repository root. The frozen Hurl
suite wins where its assertions and prose differ. This script supplements that
suite; its quality diagnostics are not scored acceptance requirements.
"""

from __future__ import annotations

import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import threading
import urllib.error
import urllib.parse
import urllib.request
from uuid import uuid4


class Client:
    def __init__(self, base_url: str, timeout: float):
        base = base_url.rstrip("/")
        if base.endswith("/api"):
            base = base[:-4]
        parsed = urllib.parse.urlsplit(base)
        if parsed.scheme not in ("http", "https") or not parsed.netloc:
            raise ValueError("--base-url must be an http(s) origin, optionally ending in /api")
        if parsed.username is not None or parsed.password is not None:
            raise ValueError("--base-url must not contain credentials")
        if parsed.query or parsed.fragment or parsed.path not in ("", "/"):
            raise ValueError("--base-url must be an origin, optionally ending in /api")
        self.base = base
        self.timeout = timeout

    def call(self, method: str, path: str, body=None, *, token=None, key=None):
        headers = {"Accept": "application/json"}
        if token is not None:
            headers["Authorization"] = f"Token {token}"
        if key is not None:
            headers["X-Share-Key"] = key
        data = None
        if body is not None:
            data = json.dumps(body).encode("utf-8")
            headers["Content-Type"] = "application/json"
        request = urllib.request.Request(
            self.base + path, data=data, headers=headers, method=method
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as opened:
                status, content = opened.status, opened.read()
        except urllib.error.HTTPError as error:
            status, content = error.code, error.read()
        try:
            value = json.loads(content) if content else None
        except (ValueError, UnicodeDecodeError):
            value = content.decode("utf-8", errors="replace")[:160]
        return {"status": status, "body": value}


def field(response, *path):
    value = response.get("body")
    for part in path:
        if not isinstance(value, dict):
            return None
        value = value.get(part)
    return value


def compact(response):
    value = response.get("body")
    if not isinstance(value, dict):
        return {"status": response["status"], "body_kind": type(value).__name__}

    def redacted(item):
        if isinstance(item, dict):
            return {
                key: "[redacted]" if key.lower() in ("key", "token", "password") else redacted(val)
                for key, val in item.items()
            }
        if isinstance(item, list):
            return [redacted(val) for val in item]
        return item

    article = value.get("article")
    summary = {"status": response["status"]}
    if "errors" in value:
        summary["errors"] = redacted(value["errors"])
    if isinstance(article, dict):
        summary["article"] = {
            key: article[key]
            for key in ("slug", "title", "description", "body", "revision")
            if key in article
        }
    if isinstance(value.get("share"), dict):
        summary["share"] = {"id": value["share"].get("id"), "key": "[redacted]"}
    return summary


def record(results, name, kind, source, expected, passed, observed):
    results.append(
        {
            "name": name,
            "kind": kind,
            "source": source,
            "expected": expected,
            "passed": bool(passed),
            "observed": observed,
        }
    )


def register(client, name, suffix):
    email = f"{name}_{suffix}@test.com"
    response = client.call(
        "POST",
        "/api/users",
        {"user": {"username": f"{name}_{suffix}", "email": email, "password": "password123"}},
    )
    token = field(response, "user", "token")
    if response["status"] != 201 or not isinstance(token, str) or not token:
        raise RuntimeError(f"registration failed: {compact(response)}")
    return email, token


def make_article(client, token, title, description="Diagnostic", body="Initial"):
    return client.call(
        "POST",
        "/api/articles",
        {"article": {"title": title, "description": description, "body": body}},
        token=token,
    )


def article_path(slug):
    return "/api/articles/" + urllib.parse.quote(slug, safe="")


def share_path(identifier):
    return "/api/shares/" + urllib.parse.quote(identifier, safe="") + "/article"


def run(client, *, include_burst=True):
    suffix = uuid4().hex[:12]
    results = []
    _, owner = register(client, "parity_owner", suffix)
    _, stranger = register(client, "parity_stranger", suffix)
    created = make_article(client, owner, f"Parity article {suffix}")
    slug = field(created, "article", "slug")
    if created["status"] != 201 or not isinstance(slug, str):
        raise RuntimeError(f"article setup failed: {compact(created)}")
    path = article_path(slug)
    initial_revision = field(created, "article", "revision")

    # drafts.md, Edit conflicts: any unequal integer is stale; only a
    # non-integer is invalid. Authentication, visibility, and ownership precede
    # revision and field validation.
    for name, supplied, status, message in (
        ("revision_zero", 0, 409, "is stale"),
        ("revision_negative", -1, 409, "is stale"),
        ("revision_noninteger", "one", 422, "is invalid"),
        ("revision_null", None, 422, "is invalid"),
    ):
        case_created = make_article(client, owner, f"{name} {suffix}")
        case_slug = field(case_created, "article", "slug")
        if case_created["status"] != 201 or not isinstance(case_slug, str):
            raise RuntimeError(f"revision case setup failed: {compact(case_created)}")
        case_path = article_path(case_slug)
        case_revision = field(case_created, "article", "revision")
        response = client.call(
            "PUT", case_path, {"article": {"body": name, "revision": supplied}}, token=owner
        )
        unchanged = client.call("GET", case_path, token=owner)
        record(
            results,
            name,
            "contract",
            "spec/features/drafts/drafts.md:65-81",
            {"status": status, "errors.revision[0]": message, "unchanged": True},
            response["status"] == status
            and field(response, "errors", "revision") == [message]
            and (status != 409 or field(response, "article", "revision") == case_revision)
            and unchanged["status"] == 200
            and field(unchanged, "article", "revision") == case_revision
            and field(unchanged, "article", "body") == "Initial",
            {"edit": compact(response), "read": compact(unchanged)},
        )

    correct = client.call(
        "PUT", path, {"article": {"body": "Explicit revision", "revision": initial_revision}}, token=owner
    )
    new_revision = field(correct, "article", "revision")
    record(
        results,
        "matching_revision",
        "contract",
        "spec/features/drafts/drafts.md:65-68",
        {"status": 200, "revision": initial_revision + 1},
        correct["status"] == 200 and new_revision == initial_revision + 1,
        compact(correct),
    )

    omitted = client.call("PUT", path, {"article": {"body": "Omitted revision"}}, token=owner)
    latest_revision = field(omitted, "article", "revision")
    record(
        results,
        "omitted_revision",
        "contract",
        "spec/features/drafts/drafts.md:65-68; spec/features/drafts/hurl/drafts.hurl:158-169",
        {"status": 200, "revision": initial_revision + 2},
        omitted["status"] == 200 and latest_revision == initial_revision + 2,
        compact(omitted),
    )

    stale = client.call(
        "PUT", path, {"article": {"body": "Stale", "revision": initial_revision}}, token=owner
    )
    record(
        results,
        "stale_revision_returns_current",
        "contract",
        "spec/features/drafts/drafts.md:69-73",
        {"status": 409, "current_revision": initial_revision + 2},
        stale["status"] == 409
        and field(stale, "errors", "revision") == ["is stale"]
        and field(stale, "article", "revision") == initial_revision + 2,
        compact(stale),
    )

    malformed = {"article": []}
    for name, probe_path, token, expected_status, error_field, error_text in (
        ("malformed_unauthenticated", path, None, 401, "token", "is missing"),
        ("malformed_stranger", path, stranger, 403, "article", "forbidden"),
        (
            "malformed_missing_article",
            article_path(f"missing-{suffix}"),
            owner,
            404,
            "article",
            "not found",
        ),
        ("malformed_owner", path, owner, 422, None, None),
    ):
        response = client.call("PUT", probe_path, malformed, token=token)
        record(
            results,
            name,
            "contract",
            "spec/features/drafts/drafts.md:77-81",
            {"status": expected_status, **({f"errors.{error_field}[0]": error_text} if error_field else {})},
            response["status"] == expected_status
            and (error_field is None or field(response, "errors", error_field) == [error_text]),
            compact(response),
        )

    # A 255-character title is a storage boundary diagnostic: the public spec
    # gives no maximum. If an implementation accepts it, the duplicate-title
    # requirement still applies and both slugs must be usable.
    long_title = "a" * (255 - len(suffix)) + suffix
    long_first = make_article(client, owner, long_title)
    first_slug = field(long_first, "article", "slug")
    first_read = (
        client.call("GET", article_path(first_slug)) if isinstance(first_slug, str) else None
    )
    record(
        results,
        "long_title_boundary",
        "quality_diagnostic",
        "spec/docs/endpoints.md:145-185",
        "clean 201 with readable slug, or clean 422; no server error",
        (long_first["status"] == 422)
        or (
            long_first["status"] == 201
            and first_read is not None
            and first_read["status"] == 200
            and field(first_read, "article", "title") == long_title
        ),
        {"create": compact(long_first), "read_status": first_read["status"] if first_read else None},
    )
    if long_first["status"] == 201:
        long_second = make_article(client, owner, long_title)
        second_slug = field(long_second, "article", "slug")
        second_read = (
            client.call("GET", article_path(second_slug)) if isinstance(second_slug, str) else None
        )
        record(
            results,
            "duplicate_long_title_slug",
            "contract",
            "spec/docs/endpoints.md:183-185",
            "second accepted title gets a distinct, readable slug",
            long_second["status"] == 201
            and isinstance(second_slug, str)
            and second_slug != first_slug
            and second_read is not None
            and second_read["status"] == 200,
            {
                "create": compact(long_second),
                "first_slug": first_slug,
                "second_read_status": second_read["status"] if second_read else None,
            },
        )

    huge = "9" * 100
    for name, method, probe_path, error_field, source in (
        (
            "huge_export_id",
            "GET",
            "/api/user/exports/" + huge,
            "export",
            "spec/features/exports/exports.md:24-44",
        ),
        (
            "huge_comment_id",
            "DELETE",
            path + "/comments/" + huge,
            "comment",
            "spec/docs/error-handling.md:25; spec/api/hurl/errors_comments.hurl:81-86",
        ),
    ):
        response = client.call(method, probe_path, token=owner)
        record(
            results,
            name,
            "contract",
            source,
            {"status": 404, f"errors.{error_field}[0]": "not found"},
            response["status"] == 404
            and field(response, "errors", error_field) == ["not found"],
            compact(response),
        )

    padded = make_article(
        client,
        owner,
        f"  Padded {suffix}  ",
        description="  Padded description  ",
        body="  Padded body  ",
    )
    padded_slug = field(padded, "article", "slug")
    padded_read = (
        client.call("GET", article_path(padded_slug), token=owner)
        if isinstance(padded_slug, str)
        else None
    )
    padded_edit = (
        client.call(
            "PUT", article_path(padded_slug), {"article": {"body": "  Edited body  "}}, token=owner
        )
        if isinstance(padded_slug, str)
        else None
    )
    record(
        results,
        "padded_text_preservation",
        "quality_diagnostic",
        "spec/docs/endpoints.md:145-185 (exact whitespace is not asserted by frozen checks)",
        "accepted nonblank text round-trips unchanged",
        padded["status"] == 201
        and padded_read is not None
        and padded_read["status"] == 200
        and field(padded_read, "article", "title") == f"  Padded {suffix}  "
        and field(padded_read, "article", "description") == "  Padded description  "
        and field(padded_read, "article", "body") == "  Padded body  "
        and padded_edit is not None
        and padded_edit["status"] == 200
        and field(padded_edit, "article", "body") == "  Edited body  ",
        {
            "create": compact(padded),
            "read": compact(padded_read) if padded_read else None,
            "edit": compact(padded_edit) if padded_edit else None,
        },
    )

    # The link ID must remain attached to the article after a title/slug edit.
    # All share keys in the report are redacted, including failures.
    link = client.call("POST", path + "/share", token=owner)
    share_id = field(link, "share", "id")
    share_key = field(link, "share", "key")
    if link["status"] != 201 or not isinstance(share_id, str) or not isinstance(share_key, str):
        record(
            results,
            "share_lifecycle_setup",
            "contract",
            "spec/features/live-editing/live-editing.md:7-9",
            "201 with opaque id and key",
            False,
            compact(link),
        )
    else:
        valid = client.call("GET", share_path(share_id), key=share_key)
        wrong = client.call("GET", share_path(share_id), key="wrong-key")
        record(
            results,
            "share_key_access",
            "contract",
            "spec/features/live-editing/live-editing.md:9-19",
            "valid 200 exact shared shape; wrong key 404",
            valid["status"] == 200
            and isinstance(field(valid, "article"), dict)
            and set(field(valid, "article")) == {"slug", "title", "body", "revision"}
            and wrong["status"] == 404,
            {"valid": compact(valid), "wrong": compact(wrong)},
        )
        shared_revision = field(valid, "article", "revision")
        if not isinstance(shared_revision, int):
            shared_revision = 0  # Keep later probes reportable when the shared read is malformed.
        edited = client.call(
            "PUT",
            share_path(share_id),
            {"article": {"title": f"Share edit {suffix}", "body": "Shared body", "revision": shared_revision}},
            key=share_key,
        )
        shared_slug = field(edited, "article", "slug")
        stable = client.call("GET", share_path(share_id), key=share_key)
        record(
            results,
            "share_edit_stable_identity",
            "contract",
            "spec/features/live-editing/live-editing.md:21-23",
            "200, revision +1, same share ID reads new slug",
            edited["status"] == 200
            and field(edited, "article", "revision") == shared_revision + 1
            and isinstance(shared_slug, str)
            and stable["status"] == 200
            and field(stable, "article", "slug") == shared_slug,
            {"edit": compact(edited), "read": compact(stable)},
        )
        if isinstance(shared_slug, str):
            path = article_path(shared_slug)
        stale_shared = client.call(
            "PUT",
            share_path(share_id),
            {"article": {"title": "Stale", "body": "Stale", "revision": shared_revision}},
            key=share_key,
        )
        record(
            results,
            "share_stale_revision",
            "contract",
            "spec/features/live-editing/live-editing.md:21-23",
            "409 with current shared article",
            stale_shared["status"] == 409
            and field(stale_shared, "errors", "revision") == ["is stale"]
            and field(stale_shared, "article", "revision") == shared_revision + 1,
            compact(stale_shared),
        )
        invalid_shape = client.call(
            "PUT",
            share_path(share_id),
            {"article": {"title": "Bad", "body": "Bad", "revision": shared_revision + 1, "status": "draft"}},
            key=share_key,
        )
        after_invalid_shape = client.call("GET", share_path(share_id), key=share_key)
        record(
            results,
            "share_exact_input_shape",
            "contract",
            "spec/features/live-editing/live-editing.md:21-23",
            "422 without mutation",
            invalid_shape["status"] == 422
            and field(invalid_shape, "errors") is not None
            and after_invalid_shape["status"] == 200
            and field(after_invalid_shape, "article") == field(stable, "article"),
            {"invalid": compact(invalid_shape), "after": compact(after_invalid_shape)},
        )
        rotated = client.call("POST", path + "/share", token=owner)
        new_id = field(rotated, "share", "id")
        new_key = field(rotated, "share", "key")
        old_after_rotation = client.call("GET", share_path(share_id), key=share_key)
        new_after_rotation = (
            client.call("GET", share_path(new_id), key=new_key)
            if isinstance(new_id, str) and isinstance(new_key, str)
            else None
        )
        record(
            results,
            "share_rotation",
            "contract",
            "spec/features/live-editing/live-editing.md:7-9",
            "201; old link 404; new link 200",
            rotated["status"] == 201
            and isinstance(new_id, str)
            and old_after_rotation["status"] == 404
            and new_after_rotation is not None
            and new_after_rotation["status"] == 200,
            {
                "rotate": compact(rotated),
                "old": compact(old_after_rotation),
                "new": compact(new_after_rotation) if new_after_rotation else None,
            },
        )
        revoked = client.call("DELETE", path + "/share", token=owner)
        after_revocation = (
            client.call("GET", share_path(new_id), key=new_key)
            if isinstance(new_id, str) and isinstance(new_key, str)
            else None
        )
        record(
            results,
            "share_revocation",
            "contract",
            "spec/features/live-editing/live-editing.md:7-11",
            "204; revoked link 404",
            revoked["status"] == 204
            and after_revocation is not None
            and after_revocation["status"] == 404,
            {
                "revoke": compact(revoked),
                "after": compact(after_revocation) if after_revocation else None,
            },
        )

    # S13 checks the 21st failed login after 20 attempts. HTTP * in its repeat
    # block does not promise particular statuses for attempts 1-20.
    sequential_email, _ = register(client, "parity_limit_seq", suffix)
    bad_login = {"user": {"email": sequential_email, "password": "wrongpassword"}}
    first_twenty = [client.call("POST", "/api/users/login", bad_login)["status"] for _ in range(20)]
    twenty_first = client.call("POST", "/api/users/login", bad_login)
    record(
        results,
        "login_rate_limit_sequential",
        "contract",
        "security/hurl/s13_login_rate_limit.hurl:15-27 (frozen fixture path in each workdir)",
        "after 20 failed logins, next attempt is 429",
        twenty_first["status"] == 429,
        {"first_twenty_status_counts": dict(Counter(first_twenty)), "next": compact(twenty_first)},
    )

    if include_burst:
        burst_email, _ = register(client, "parity_limit_burst", suffix)
        burst_body = {"user": {"email": burst_email, "password": "wrongpassword"}}
        start = threading.Event()

        def bad_attempt(_):
            start.wait()
            return client.call("POST", "/api/users/login", burst_body)["status"]

        with ThreadPoolExecutor(max_workers=25) as pool:
            futures = [pool.submit(bad_attempt, i) for i in range(25)]
            start.set()
            statuses = [future.result() for future in futures]
        next_attempt = client.call("POST", "/api/users/login", burst_body)
        counts = Counter(statuses)
        record(
            results,
            "login_rate_limit_burst",
            "quality_diagnostic",
            "security/hurl/s13_login_rate_limit.hurl:15-27 (concurrency is outside frozen S13)",
            "25 concurrent bad logins admit at most 20; later attempts are 429",
            set(counts).issubset({401, 429})
            and counts.get(401, 0) <= 20
            and counts.get(429, 0) >= 5
            and sum(counts.values()) == 25
            and next_attempt["status"] == 429,
            {"burst_status_counts": dict(counts), "next": compact(next_attempt)},
        )

    return results


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", required=True, help="running Conduit app origin, optionally ending in /api")
    parser.add_argument("--timeout", type=float, default=15.0, help="per-request timeout in seconds")
    parser.add_argument("--output", type=Path, help="write JSON here instead of stdout")
    parser.add_argument("--skip-login-burst", action="store_true", help="skip 25 simultaneous login requests")
    parser.add_argument("--strict-diagnostics", action="store_true", help="exit 1 for quality failures too")
    args = parser.parse_args()
    client = Client(args.base_url, args.timeout)
    try:
        results = run(client, include_burst=not args.skip_login_burst)
        payload = {
            "condition": "reviewer-only common HTTP diagnostic; never a frozen gate",
            "base_url": client.base,
            "results": results,
            "summary": {
                "contract_passed": sum(item["passed"] for item in results if item["kind"] == "contract"),
                "contract_total": sum(item["kind"] == "contract" for item in results),
                "quality_passed": sum(item["passed"] for item in results if item["kind"] == "quality_diagnostic"),
                "quality_total": sum(item["kind"] == "quality_diagnostic" for item in results),
            },
        }
    except Exception as error:
        payload = {
            "condition": "reviewer-only common HTTP diagnostic; never a frozen gate",
            "base_url": client.base,
            "fatal_setup_or_transport_error": f"{type(error).__name__}: {error}",
        }
    rendered = json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    if args.output:
        args.output.write_text(rendered)
    else:
        print(rendered, end="")
    if "fatal_setup_or_transport_error" in payload:
        return 2
    contract_failed = payload["summary"]["contract_passed"] != payload["summary"]["contract_total"]
    quality_failed = payload["summary"]["quality_passed"] != payload["summary"]["quality_total"]
    return 1 if contract_failed or (args.strict_diagnostics and quality_failed) else 0


if __name__ == "__main__":
    raise SystemExit(main())
