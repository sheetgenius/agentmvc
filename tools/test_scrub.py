"""Focused checks for public transcript redaction."""

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tools import scrub


class ScrubTest(unittest.TestCase):
    def test_codex_jsonl_and_markdown_hide_account_details(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            events = root / "events.jsonl"
            private = (
                f"work={Path.home()}/co/private\n"
                "contact=alice@example.test\n"
                "OPENAI_API_KEY=unmistakable-secret-value\n"
                "DATABASE_URL=postgres://alice:password@internal.example/db\n"
                "Authorization: Bearer eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxIn0.signature\n"
            )
            event = {"type": "item.completed", "item": {"type": "command_execution",
                     "command": "cat .env", "aggregated_output": private, "exit_code": 0}}
            events.write_text(json.dumps(event) + "\n")
            stem = root / "published"
            scrub.scrub_file(events, root / "work", stem, header={"title": "alice@example.test"})
            published = stem.with_suffix(".jsonl").read_text() + stem.with_suffix(".md").read_text()
            for secret in (str(Path.home()), "alice@example.test", "unmistakable-secret-value",
                           "postgres://alice:password@", "eyJhbGciOiJIUzI1NiJ9"):
                self.assertNotIn(secret, published)
            self.assertIn("[redacted]", published)
            self.assertFalse(scrub.Scrubber(root / "work").leaks(published))

    def test_plain_text_mode_and_custom_deny(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "session.txt"
            source.write_text(
                "github_pat_" + "A" * 24 + "\n"
                "my-private-host\n"
                '"password": "hunter2"\n'
                "/Users/alice/another-repo\n"
            )
            output = scrub.scrub_plain_file(source, root / "work", root / "safe", ["my-private-host"])
            published = output.read_text()
            for secret in ("github_pat_", "my-private-host", "hunter2", "/Users/alice/"):
                self.assertNotIn(secret, published)
            self.assertFalse(scrub.Scrubber(root / "work", ["my-private-host"]).leaks(published))

    def test_leak_check_refuses_output_without_echoing_secret(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "session.txt"
            source.write_text("SECRET_KEY_BASE=private-value\n")
            with patch.object(scrub.Scrubber, "text", lambda self, value: value):
                with self.assertRaises(SystemExit) as raised:
                    scrub.scrub_plain_file(source, root / "work", root / "safe")
            self.assertIn("sensitive assignment", str(raised.exception))
            self.assertNotIn("private-value", str(raised.exception))
            self.assertFalse((root / "safe.txt").exists())


if __name__ == "__main__":
    unittest.main()
