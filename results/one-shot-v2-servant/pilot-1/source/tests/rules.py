"""Focused HTTP transitions against the running development server."""

import json
import sys
import unittest
import urllib.error
import urllib.request
import uuid


BASE = f"http://127.0.0.1:{int(sys.argv.pop(1))}/api"


def call(method, path, body=None, token=None, key=None):
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Token {token}"
    if key:
        headers["X-Share-Key"] = key
    request = urllib.request.Request(
        BASE + path,
        data=None if body is None else json.dumps(body).encode(),
        headers=headers,
        method=method,
    )
    try:
        with urllib.request.urlopen(request, timeout=5) as response:
            content = response.read()
            return response.status, json.loads(content) if content else None
    except urllib.error.HTTPError as error:
        return error.code, json.load(error)


class Rules(unittest.TestCase):
    def setUp(self):
        unique = uuid.uuid4().hex[:12]
        status, result = call(
            "POST",
            "/users",
            {"user": {"username": unique, "email": unique + "@example.test", "password": "password123"}},
        )
        self.assertEqual(status, 201)
        self.token = result["user"]["token"]

    def test_revision_is_shared_by_author_and_capability(self):
        status, result = call(
            "POST",
            "/articles",
            {"article": {"title": "Rule", "description": "desc", "body": "first", "status": "draft"}},
            self.token,
        )
        self.assertEqual(status, 201)
        slug = result["article"]["slug"]
        _, share = call("POST", f"/articles/{slug}/share", token=self.token)
        ident, key = share["share"]["id"], share["share"]["key"]

        status, _ = call("GET", f"/articles/{slug}")
        self.assertEqual(status, 404)
        status, result = call(
            "PUT",
            f"/shares/{ident}/article",
            {"article": {"title": "Rule edited", "body": "second", "revision": 1}},
            key=key,
        )
        self.assertEqual(status, 200)
        new_slug = result["article"]["slug"]
        status, result = call(
            "PUT", f"/articles/{new_slug}", {"article": {"body": "stale", "revision": 1}}, self.token
        )
        self.assertEqual(status, 409)
        self.assertEqual(result["article"]["body"], "second")
        status, result = call(
            "PUT", f"/articles/{new_slug}", {"article": {"body": "third", "revision": 2}}, self.token
        )
        self.assertEqual(status, 200)
        self.assertEqual(result["article"]["revision"], 3)
        status, result = call("GET", f"/shares/{ident}/article", key=key)
        self.assertEqual(status, 200)
        self.assertEqual(result["article"]["body"], "third")

        status, _ = call("PUT", f"/shares/{ident}/article", {"article": {}}, key="wrong")
        self.assertEqual(status, 404)
        call("DELETE", f"/articles/{new_slug}/share", token=self.token)
        status, _ = call("GET", f"/shares/{ident}/article", key=key)
        self.assertEqual(status, 404)


if __name__ == "__main__":
    unittest.main()
