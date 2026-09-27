"""Measure an implementation's code in LLM tokens (o200k) and lines.

Usage:
  python3 tools/measure.py STACK                 every step of stacks/STACK
  python3 tools/measure.py STACK STEP            one step, e.g. rails 2-add-drafts

Two views of the same code:
- whole app: every non-blank line (comments included) of the application source, which is what an agent reads;
- owned code: non-blank, non-comment lines added or changed relative to a baseline, the untouched generator
  output in stacks/STACK/scaffold/ by default, or the previous step to measure what one step cost.

Excluded everywhere: tests, lockfiles, dependencies and build output, generated schema, Markdown, the check
harness (bin/check, compose files, Dockerfiles), and tool dotfiles. The per-stack rules live in stack.json.
"""
import difflib, json, os, re, sys
from pathlib import Path

import tiktoken

ROOT = Path(__file__).resolve().parent.parent
ENCODING = tiktoken.get_encoding("o200k_base")

SKIP_DIRS = {"vendor", "deps", "_build", "target", "node_modules", "tmp", "log", ".git", ".claude", ".elixir_ls",
             ".hex", ".mix", "test", "tests", "spec", "_entities", ".scaffold", "realworld_spec"}
SKIP_FILES = {".gitignore", ".dockerignore", ".gitattributes", ".tool-versions"}
HARNESS = re.compile(r"(^|/)(bin/check|compose[^/]*\.ya?ml|docker-compose[^/]*\.ya?ml|Dockerfile[^/]*)$")
CONFIG = {".yml": "#", ".yaml": "#", ".toml": "#", ".sql": "--"}  # configuration counts, in every stack


def tokens(lines):
    return len(ENCODING.encode("\n".join(lines))) if lines else 0


def load_stack(name):
    stack = json.loads((ROOT / "stacks" / name / "stack.json").read_text())
    stack["dir"] = ROOT / "stacks" / name
    return stack


def steps(stack):
    return sorted((p.name for p in stack["dir"].iterdir() if p.is_dir() and re.match(r"\d+-", p.name)),
                  key=lambda name: int(name.split("-")[0]))


def comment_prefix(stack, rel):
    """(comment prefix, is source code) for a file this stack counts, or None."""
    code = stack["code"]
    name = os.path.basename(rel)
    if name in code.get("files", {}):
        return code["files"][name], True
    ext = os.path.splitext(name)[1]
    if ext in code["extensions"]:
        return code["extensions"][ext], True
    return (CONFIG[ext], False) if ext in CONFIG else None


def read_lines(text):
    """Every non-blank line, comments and docs included: what a scanning reader takes in."""
    return [line.strip() for line in text.split("\n") if line.strip()]


def code_lines(text, prefix, doc_attributes=()):
    """Non-blank lines that aren't comments (or, in Elixir, documentation attributes)."""
    out, in_doc = [], False
    docs = "|".join(doc_attributes)
    for raw in text.split("\n"):
        s = raw.strip()
        if docs:
            if in_doc:
                in_doc = not s.endswith('"""')
                continue
            if re.match(rf'@({docs})\s+"""', s):
                in_doc = s.count('"""') == 1
                continue
            if re.match(rf'@({docs})\s+(".*"|false)$', s):
                continue
        if s and not s.startswith(prefix):
            out.append(s)
    return out


def source_files(stack, base):
    code = stack["code"]
    skip_dirs = SKIP_DIRS | set(code.get("skip_dirs", []))
    skip_files = SKIP_FILES | set(code.get("skip_files", []))
    generated = set(code.get("generated", []))
    for dirpath, dirnames, filenames in os.walk(base):
        dirnames[:] = [d for d in dirnames if d not in skip_dirs]
        for name in filenames:
            rel = os.path.relpath(os.path.join(dirpath, name), base)
            if name in skip_files or name.endswith(".md") or rel in generated or HARNESS.search(rel):
                continue
            rule = comment_prefix(stack, rel)
            if rule:
                yield rel, rule


def added(old, new):
    out = []
    for tag, _i1, _i2, j1, j2 in difflib.SequenceMatcher(a=old, b=new, autojunk=False).get_opcodes():
        if tag in ("insert", "replace"):
            out.extend(new[j1:j2])
    return out


def measure(stack, code_dir, baseline_dir=None):
    """Sizes of code_dir, plus the owned code it adds or changes relative to baseline_dir (default: the scaffold)."""
    baseline_dir = Path(baseline_dir or stack["dir"] / "scaffold")
    docs = stack["code"].get("doc_attributes", [])
    totals = dict.fromkeys(("tokens", "lines", "code_lines", "owned_tokens", "owned_lines",
                            "files_created", "files_changed"), 0)
    for rel, (prefix, is_code) in source_files(stack, code_dir):
        docs_here = docs if is_code else ()
        text = (Path(code_dir) / rel).read_text(errors="ignore")
        old_path = baseline_dir / rel
        old = old_path.read_text(errors="ignore") if old_path.exists() else ""
        mine = added(code_lines(old, prefix, docs_here), code_lines(text, prefix, docs_here))
        totals["tokens"] += tokens(read_lines(text))
        totals["lines"] += len(read_lines(text))
        totals["code_lines"] += len(code_lines(text, prefix, docs_here))
        totals["owned_tokens"] += tokens(mine)
        totals["owned_lines"] += len(mine)
        if mine:
            totals["files_created" if not old_path.exists() else "files_changed"] += 1
    return totals


def measure_stack(name):
    """Every step of one stack: its size, and what it added or changed relative to the step before."""
    stack = load_stack(name)
    results, previous = {}, None
    for step in steps(stack):
        size = measure(stack, stack["dir"] / step)
        change = measure(stack, stack["dir"] / step, previous) if previous else None
        results[step] = {"tokens": size["tokens"], "lines": size["lines"], "code_lines": size["code_lines"],
                         "owned_tokens": size["owned_tokens"],
                         "step_tokens": change["owned_tokens"] if change else size["owned_tokens"],
                         "step_files": (f"{change['files_created']} created, {change['files_changed']} changed" if change
                                        else f"{size['files_created']} created, {size['files_changed']} changed")}
        previous = stack["dir"] / step
    return results


if __name__ == "__main__":
    name, only = sys.argv[1], (sys.argv[2] if len(sys.argv) > 2 else None)
    for step, r in measure_stack(name).items():
        if only in (None, step):
            print(f"{name} {step}: whole app {r['tokens']:,} tokens, {r['code_lines']:,} lines of code; "
                  f"owned {r['owned_tokens']:,} tokens; this step added or changed {r['step_tokens']:,} tokens ({r['step_files']})")
