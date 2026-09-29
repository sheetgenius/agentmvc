#!/usr/bin/env python3
"""Source-driven supplemental favorite diagnostic for final Go/Python apps.

Run only against an already-running disposable application. Creates four users
and one article; leaves them for inspection. Never starts Docker or changes the
frozen/common probe. This is a reviewer diagnostic, not a frozen acceptance gate.

Example: python3 tools/lane_favorites_probe.py --base-url http://127.0.0.1:4111
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import urllib.parse
from uuid import uuid4

from reviewer_common_http_probe import Client, article_path, field


CONDITION = "source-driven supplemental favorites diagnostic; not a frozen gate"
SOURCES = ["spec/docs/endpoints.md", "spec/docs/api-response-format.md"]


def scalar(value, expected_type):
    """Only export known numeric/boolean fields; never echo unexpected text."""
    return value if type(value) is expected_type else {"invalid_type": type(value).__name__}


def metadata(response):
    body = response.get("body")
    observed = {"status": response["status"], "body_kind": type(body).__name__}
    if isinstance(body, dict) and "errors" in body:
        errors = body["errors"]
        observed["errors_kind"] = type(errors).__name__
        if isinstance(errors, dict):
            known = {"username", "email", "password", "article", "token", "tagList", "title"}
            observed["error_fields"] = sorted(key for key in errors if key in known)
            observed["other_error_fields"] = sum(key not in known for key in errors)
    return observed


def record(results, name, expected, observed, passed):
    results.append({"name": name, "expected": expected, "observed": observed, "passed": passed})


def setup(results, name, response, expected_status, usable=True):
    passed = response["status"] == expected_status and usable
    observed = metadata(response)
    observed["usable_response"] = usable
    record(results, name, {"status": expected_status, "usable_response": True}, observed, passed)
    if not passed:
        raise RuntimeError("setup failed; see structured case")


def inspect_phase(client, results, phase, users, tag, slug, favoriting):
    count = len(favoriting)
    for viewer in ("anonymous", "author", "a", "b", "reader"):
        token = users[viewer]["token"] if viewer in users else None
        expected_favorited = viewer in favoriting
        response = client.call("GET", article_path(slug), token=token)
        article = field(response, "article")
        valid_article = isinstance(article, dict)
        observed = metadata(response)
        observed.update(
            target_article=valid_article and article.get("slug") == slug,
            favorites_count=scalar(field(response, "article", "favoritesCount"), int),
            favorited=scalar(field(response, "article", "favorited"), bool),
        )
        expected = {"status": 200, "target_article": True,
                    "favorites_count": count, "favorited": expected_favorited}
        record(results, f"{phase}/{viewer}/direct", expected, observed,
               all(observed[key] == value for key, value in expected.items()))

        # Every list has the same unique tag scope, preventing unrelated rows
        # from hiding this article behind pagination. Only favorite eligibility
        # differs between the three queries.
        for favorite_filter in (None, "a", "b"):
            query = {"tag": tag, "limit": 20, "offset": 0}
            if favorite_filter is not None:
                query["favorited"] = users[favorite_filter]["username"]
            response = client.call("GET", "/api/articles?" + urllib.parse.urlencode(query), token=token)
            articles = field(response, "articles")
            valid_list = isinstance(articles, list)
            items = articles if valid_list else []
            members = [item for item in items if isinstance(item, dict) and item.get("slug") == slug]
            present = favorite_filter is None or favorite_filter in favoriting
            wanted = 1 if present else 0
            observed = metadata(response)
            observed.update(
                articles_is_list=valid_list,
                articles_count=scalar(field(response, "articlesCount"), int),
                returned_count=len(items),
                target_occurrences=len(members),
                favorites_counts=[scalar(item.get("favoritesCount"), int) for item in members],
                favorited_flags=[scalar(item.get("favorited"), bool) for item in members],
            )
            expected = {
                "status": 200, "articles_is_list": True, "articles_count": wanted,
                "returned_count": wanted, "target_occurrences": wanted,
                "favorites_counts": [count] if present else [],
                "favorited_flags": [expected_favorited] if present else [],
            }
            label = f"favorited_{favorite_filter}" if favorite_filter else "no_favorite_filter"
            record(results, f"{phase}/{viewer}/{label}", expected, observed,
                   all(observed[key] == value for key, value in expected.items()))


def run(client, results):
    suffix = uuid4().hex[:16]
    users = {}
    for role in ("author", "a", "b", "reader"):
        username = f"favorite_{role}_{suffix}"
        response = client.call("POST", "/api/users", {"user": {
            "username": username, "email": f"{username}@example.com",
            "password": f"Favorite-check-{uuid4().hex}",
        }})
        token = field(response, "user", "token")
        setup(results, f"setup/register_{role}", response, 201,
              isinstance(token, str) and bool(token) and field(response, "user", "username") == username)
        users[role] = {"username": username, "token": token}

    tag = f"favoriteprobe{suffix}"
    response = client.call("POST", "/api/articles", {"article": {
        "title": f"Favorite probe {suffix}", "description": "Reviewer supplemental check",
        "body": "Favorite membership must not narrow total favorite counts.", "tagList": [tag],
    }}, token=users["author"]["token"])
    slug = field(response, "article", "slug")
    setup(results, "setup/create_article", response, 201, isinstance(slug, str) and bool(slug))
    path = article_path(slug) + "/favorite"
    for role in ("a", "b"):
        response = client.call("POST", path, token=users[role]["token"])
        setup(results, f"setup/favorite_{role}", response, 200)

    inspect_phase(client, results, "two_favorites", users, tag, slug, {"a", "b"})
    response = client.call("DELETE", path, token=users["a"]["token"])
    setup(results, "setup/unfavorite_a", response, 200)
    inspect_phase(client, results, "one_favorite", users, tag, slug, {"b"})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", required=True, help="disposable app origin, optionally ending in /api")
    parser.add_argument("--timeout", type=float, default=10.0, help="per-request timeout, 0 < seconds <= 60")
    parser.add_argument("--output", type=Path, help="write JSON here instead of stdout")
    args = parser.parse_args()
    results = []
    payload = {"condition": CONDITION, "contract_sources": SOURCES, "results": results}
    exit_code = 0
    try:
        if not math.isfinite(args.timeout) or not 0 < args.timeout <= 60:
            raise ValueError("timeout out of range")
        client = Client(args.base_url, args.timeout)
        run(client, results)
    except Exception as error:
        # Exception messages, server bodies, URLs and headers may contain
        # credentials or personal data. Keep only type and safe case metadata.
        payload["fatal_setup_or_transport_error"] = {"type": type(error).__name__}
        exit_code = 2
    passed = sum(item["passed"] for item in results)
    payload["summary"] = {"passed": passed, "failed": len(results) - passed, "total": len(results)}
    rendered = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.write_text(rendered)
    else:
        print(rendered, end="")
    return exit_code or (1 if passed != len(results) else 0)


if __name__ == "__main__":
    raise SystemExit(main())
