"""Checks for tools/brief_check.py."""
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import brief_check  # noqa: E402

SECTIONS = brief_check.SECTIONS


def brief(sections=SECTIONS, words=5, extra="", title="# Test brief"):
    body = "".join(f"## {name}\n\n" + " ".join(["word"] * words) + "\n\n" for name in sections)
    return f"{title}\n\n{body}{extra}"


class BriefCheckTest(unittest.TestCase):
    def run_check(self, text):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "brief.md"
            path.write_text(text)
            return brief_check.check(path)

    def test_valid_brief_with_metadata(self):
        words, problems = self.run_check(brief(extra="## About this brief\n\n- Authors: someone\n"))
        self.assertEqual(problems, [])
        self.assertEqual(words, 5 * len(SECTIONS))

    def test_template_passes(self):
        template = Path(__file__).resolve().parent.parent / "briefs" / "TEMPLATE.md"
        self.assertEqual(brief_check.check(template)[1], [])

    def test_missing_section(self):
        _, problems = self.run_check(brief(sections=SECTIONS[:-1]))
        self.assertTrue(any("sections must be" in p for p in problems))

    def test_word_limit(self):
        words, problems = self.run_check(brief(words=90))
        self.assertGreater(words, brief_check.LIMIT)
        self.assertTrue(any("limit" in p for p in problems))

    def test_metadata_does_not_count(self):
        words, problems = self.run_check(brief(extra="## About this brief\n\n" + "word " * 600 + "\n"))
        self.assertEqual(problems, [])
        self.assertEqual(words, 5 * len(SECTIONS))

    def test_code_fence(self):
        _, problems = self.run_check(brief(extra="```\ncode\n```\n"))
        self.assertIn("fenced code blocks are not allowed", problems)

    def test_guidance_after_metadata(self):
        text = brief(sections=SECTIONS[:-1], extra="## About this brief\n\nx\n\n## Known traps\n\nword\n")
        _, problems = self.run_check(text)
        self.assertTrue(any("after a metadata section" in p for p in problems))

    def test_title_required(self):
        _, problems = self.run_check(brief(title="Test brief"))
        self.assertIn("the first line must be a `# ` title", problems)


if __name__ == "__main__":
    unittest.main()
