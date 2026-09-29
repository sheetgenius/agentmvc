"""Scrub an agent transcript (Codex `--json` events) for publishing, and render a readable Markdown copy.

Usage: python3 tools/scrub.py EVENTS.jsonl WORKDIR OUT_STEM [--deny REGEX ...] [--keep REGEX ...]
                              [--map FROM=TO ...] [--header JSON]
       python3 tools/scrub.py TRANSCRIPT.txt WORKDIR OUT_STEM --plain [--deny REGEX ...]

- WORKDIR (the agent's directory) becomes /work/app; your home directory becomes ~; your username becomes
  "user"; your hostname becomes "host"; other macOS home paths become /Users/user/;
  macOS temp paths become $TMPDIR.
- Common secret shapes (API keys, access tokens, private keys) become [redacted].
- Docker host listings (images, containers, contexts, builders, networks, volumes) keep only lines about this
  project (--keep adds patterns); everything else is replaced by a note with the number of lines removed.
- Every --deny pattern is replaced by [redacted] wherever it appears, and removes Docker listing lines.
- Every --map FROM=TO replaces a literal path or string before the rules above (for example a parent directory).
Writes OUT_STEM.jsonl and OUT_STEM.md, or OUT_STEM.txt with --plain. Exits non-zero if a
recognized secret, email, home path, username, hostname or --deny pattern survives.
Read the output before you publish it: scrubbing is a safety net, not a guarantee.
"""
import argparse, getpass, json, os, re, socket
from pathlib import Path

LISTING = re.compile(r"docker\s+(?:image\s+ls|images|ps|container\s+ls|context\s+(?:ls|inspect|show)|buildx\s+ls|"
                     r"network\s+ls|volume\s+ls|compose\s+ls|system\s+df)")
KEEP = (r"^\s*$|^\s*(?:REPOSITORY|NAME|CONTAINER|IMAGE|NETWORK|DRIVER|VOLUME|TYPE)\b|conduit|realworld|agentmvc|"
        r"postgres|hurl|grafana/k6|osv-scanner|brakeman|sobelow|\bdefault\b|orbstack|desktop-linux")
SECRETS = [r"sk-(?:proj-)?[A-Za-z0-9_-]{20,}", r"gh[pousr]_[A-Za-z0-9]{20,}", r"github_pat_[A-Za-z0-9_]{20,}",
           r"AKIA[0-9A-Z]{16}", r"xox[abprs]-[A-Za-z0-9-]{10,}", r"(?i)bearer\s+[A-Za-z0-9._-]{20,}",
           r"-----BEGIN [A-Z ]*PRIVATE KEY-----[\s\S]*?-----END [A-Z ]*PRIVATE KEY-----",
           r"(?i)(?:postgres(?:ql)?|redis)://[^\s@]+:[^\s@]+@"]
EMAIL = re.compile(r"(?<![\w.+-])[\w.%+-]+@[\w.-]+\.[A-Za-z]{2,}(?![\w.-])")
SENSITIVE_ASSIGNMENT = re.compile(
    r"(?P<prefix>\b(?:[A-Z0-9_]*(?:SECRET|PASSWORD|API_KEY|PRIVATE_KEY)[A-Z0-9_]*|"
    r"[A-Z0-9_]*TOKEN|"
    r"DATABASE_URL|REDIS_URL)\b[\"']?\s*(?:=|:)\s*)"
    r"(?P<value>\"(?:[^\"\\]|\\.)*\"|'(?:[^'\\]|\\.)*'|[^\s,;}\\\"]+)", re.I)
UNRELATED_WORKTREE = re.compile(r'~/co/(?!agentmvc(?:/|~|$))[^~\s"\\]+', re.I)
OTHER_MAC_HOME = re.compile(r'/Users/(?!user/)[^/\s"\\]+/')
OTHER_UNIX_HOME = re.compile(r'/home/(?!user/)[^/\s"\\]+/')


def redact_assignment(match):
    value = match.group("value")
    quote = value[0] if value[0] in "\"'" else ""
    return match.group("prefix") + (quote + "[redacted]" + quote if quote else "[redacted]")


class Scrubber:
    def __init__(self, workdir, deny=(), keep=(), maps=()):
        home, user = str(Path.home()), getpass.getuser()
        host = socket.gethostname().split(".")[0]
        self.deny = [re.compile(p, re.I) for p in deny]
        self.keep = re.compile("|".join([KEEP, *keep]), re.I)
        self.rules = [(re.compile(re.escape(str(Path(workdir).resolve()))), "/work/app"),
                      *[(re.compile(re.escape(src)), dst) for src, dst in maps],
                      (re.compile(re.escape(home)), "~"),
                      (OTHER_MAC_HOME, "/Users/user/"),
                      (OTHER_UNIX_HOME, "/home/user/"),
                      (UNRELATED_WORKTREE, "[redacted]"),
                      (re.compile(r"(?:/private)?/var/folders/\w+/\w+/T"), "$TMPDIR"),
                      (re.compile(rf"\b{re.escape(user)}\b"), "user"),
                      (re.compile(rf"\b{re.escape(host)}(?:\.local)?\b", re.I), "host"),
                      *[(re.compile(p), "[redacted]") for p in SECRETS],
                      (EMAIL, "[redacted-email]"),
                      (SENSITIVE_ASSIGNMENT, redact_assignment),
                      *[(p, "[redacted]") for p in self.deny]]
        self.forbidden = [("home path", re.compile(re.escape(home))),
                          ("username", re.compile(rf"\b{re.escape(user)}\b")),
                          ("hostname", re.compile(rf"\b{re.escape(host)}\b", re.I)),
                          ("other home path", OTHER_MAC_HOME), ("other home path", OTHER_UNIX_HOME),
                          ("other worktree", UNRELATED_WORKTREE), ("email", EMAIL),
                          *[("secret", re.compile(p)) for p in SECRETS],
                          *[("custom deny pattern", p) for p in self.deny]]

    def text(self, value):
        for pattern, replacement in self.rules:
            value = pattern.sub(replacement, value)
        return value

    def value(self, value):
        if isinstance(value, str):
            return self.text(value)
        if isinstance(value, list):
            return [self.value(v) for v in value]
        if isinstance(value, dict):
            return {k: self.value(v) for k, v in value.items()}
        return value

    def listing(self, item):
        if item.get("type") != "command_execution" or not LISTING.search(item.get("command", "")):
            return item
        kept, removed = [], 0
        for line in (item.get("aggregated_output") or "").splitlines():
            if self.keep.search(line) and not any(p.search(line) for p in self.deny):
                kept.append(line)
            else:
                removed += 1
        if removed:
            kept.append(f"[{removed} lines of unrelated output removed]")
        return {**item, "aggregated_output": "\n".join(kept) + ("\n" if kept else "")}

    def event(self, event):
        if isinstance(event.get("item"), dict):
            event = {**event, "item": self.listing(event["item"])}
        return self.value(event)

    def leaks(self, text):
        found = {label for label, pattern in self.forbidden if pattern.search(text)}
        if any(match.group("value").strip("\"'") != "[redacted]"
               for match in SENSITIVE_ASSIGNMENT.finditer(text)):
            found.add("sensitive assignment")
        return sorted(found)


def fence(text, lang=""):
    ticks = "```"
    while ticks in text:
        ticks += "`"
    return f"{ticks}{lang}\n{text.rstrip()}\n{ticks}"


def render(events, header, max_lines=40):
    """A readable Markdown view: messages in full, commands in full, long outputs cut."""
    lines = [f"# {header.get('title', 'Agent transcript')}", ""]
    rows = [(k, v) for k, v in header.items() if k != "title"]
    if rows:
        lines += ["| | |", "| --- | --- |", *[f"| {k} | {v} |" for k, v in rows], ""]
    lines += [f"Outputs longer than {max_lines} lines are cut here; the `.jsonl` file next to this one has them in full.", ""]
    for event in events:
        item = event.get("item")
        if event.get("type") != "item.completed" or not item:
            continue
        kind = item.get("type")
        if kind == "agent_message":
            lines += ["**Agent:**", "", item.get("text", "").strip(), ""]
        elif kind == "command_execution":
            output = (item.get("aggregated_output") or "").rstrip("\n").split("\n")
            shown = output[:max_lines] + ([f"[... {len(output) - max_lines} more lines]"] if len(output) > max_lines else [])
            lines += [fence("$ " + item.get("command", ""), "sh")]
            if any(shown):
                lines += [f"<details><summary>output (exit {item.get('exit_code')})</summary>", "", fence("\n".join(shown)),
                          "", "</details>"]
            lines += [""]
        elif kind == "file_change":
            changes = item.get("changes") or []
            lines += ["*Files changed:* " + ", ".join(f"`{c.get('path')}` ({c.get('kind')})" for c in changes), ""]
        elif kind == "web_search":
            lines += [f"*Web search:* {item.get('query') or item.get('action')}", ""]
    return "\n".join(lines) + "\n"


def scrub_file(events_path, workdir, out_stem, deny=(), keep=(), header=None, maps=()):
    scrubber = Scrubber(workdir, deny, keep, maps)
    with open(events_path) as source:
        events = [scrubber.event(json.loads(line)) for line in source if line.strip()]
    raw = "".join(json.dumps(e, ensure_ascii=False) + "\n" for e in events)
    readable = render(events, scrubber.value(header or {}))
    leaks = scrubber.leaks(raw + readable)
    if leaks:
        raise SystemExit(f"{events_path}: scrubbing left sensitive material: {', '.join(leaks)}")
    out_stem = Path(out_stem)
    out_stem.parent.mkdir(parents=True, exist_ok=True)
    out_stem.with_suffix(".jsonl").write_text(raw)
    out_stem.with_suffix(".md").write_text(readable)
    return events


def scrub_plain_file(input_path, workdir, out_stem, deny=(), maps=()):
    scrubber = Scrubber(workdir, deny, maps=maps)
    readable = scrubber.text(Path(input_path).read_text())
    leaks = scrubber.leaks(readable)
    if leaks:
        raise SystemExit(f"{input_path}: scrubbing left sensitive material: {', '.join(leaks)}")
    output = Path(out_stem).with_suffix(".txt")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(readable)
    return output


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("events"), parser.add_argument("workdir"), parser.add_argument("out_stem")
    parser.add_argument("--deny", action="append", default=[])
    parser.add_argument("--keep", action="append", default=[])
    parser.add_argument("--map", action="append", default=[])
    parser.add_argument("--header", default="{}")
    parser.add_argument("--plain", action="store_true", help="scrub a plain-text transcript to OUT_STEM.txt")
    args = parser.parse_args()
    maps = [tuple(m.split("=", 1)) for m in args.map]
    if args.plain:
        output = scrub_plain_file(args.events, args.workdir, args.out_stem, args.deny, maps)
        print(f"wrote {output}")
    else:
        scrub_file(args.events, args.workdir, args.out_stem, args.deny, args.keep, json.loads(args.header), maps)
        print(f"wrote {args.out_stem}.jsonl and {args.out_stem}.md")
