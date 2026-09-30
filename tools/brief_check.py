"""Check a practitioner brief against the protocol in briefs/README.md.

Usage: python3 tools/brief_check.py BRIEF.md [BRIEF.md ...]

A brief has a `# ` title, then six `## ` sections in a fixed order, then optional metadata sections.
The six guidance sections may hold at most 500 words in total, and no file may contain a fenced
code block. Exit status is 1 if any brief fails.
"""
import re
import sys
from pathlib import Path

SECTIONS = ["Rule ownership", "Use what the framework provides", "Bounded queries", "Boundaries",
            "Production", "Known traps"]
METADATA = {"About this brief", "Source"}
LIMIT = 500


def check(path):
    text = Path(path).read_text()
    problems = []
    lines = [line for line in text.splitlines() if line.strip()]
    if not lines or not lines[0].startswith("# "):
        problems.append("the first line must be a `# ` title")
    if re.search(r"^\s*(```|~~~)", text, re.M):
        problems.append("fenced code blocks are not allowed")
    sections = re.split(r"^## +(.+?)\s*$", text, flags=re.M)
    names, bodies = sections[1::2], sections[2::2]
    guidance = [(n, b) for n, b in zip(names, bodies) if n not in METADATA]
    if [n for n, _ in guidance] != SECTIONS:
        problems.append("sections must be, in order: " + "; ".join(SECTIONS)
                        + f" (found: {'; '.join(n for n, _ in guidance) or 'none'})")
    seen_metadata = False
    for name in names:
        if name in METADATA:
            seen_metadata = True
        elif seen_metadata:
            problems.append(f"guidance section '{name}' comes after a metadata section")
    for name, body in guidance:
        if not body.strip():
            problems.append(f"section '{name}' is empty")
    words = sum(len(re.findall(r"\S+", body)) for _, body in guidance)
    if words > LIMIT:
        problems.append(f"{words} words of guidance; the limit is {LIMIT}")
    return words, problems


def main():
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    failed = False
    for path in sys.argv[1:]:
        words, problems = check(path)
        status = "ok" if not problems else "FAIL"
        print(f"{status}  {path}: {words} words of guidance")
        for problem in problems:
            print(f"      {problem}")
        failed = failed or bool(problems)
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
