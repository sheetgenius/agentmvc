"""Freeze and prepare the isolated IHP candidate without altering the three-stack fixture.

Usage: python3 tools/ihp_candidate.py freeze|verify-source|preflight|prepare RUN|verify WORKDIR
RUN is 1, 2 or 3. Preparing never launches a measured agent.
"""
import json
import os
import shutil
import sys
from pathlib import Path

import one_shot

ROOT = one_shot.ROOT
SOURCE = ROOT / "ihp-candidate"
MANIFEST = SOURCE / "fixture-manifest.json"
BASE = one_shot.MANIFEST
EXTRAS = [SOURCE / "README.md", SOURCE / "ENVIRONMENT.md", SOURCE / "ihp.sh",
          ROOT / "tools/ihp_candidate.py", ROOT / "tools/ihp_candidate_broker.py",
          ROOT / "tools/ihp_candidate_agent.py",
          ROOT / "stacks/ihp/stack.json",
          ROOT / "tools/ihp_candidate_host/check-production.sh"]
SCAFFOLD = ROOT / "stacks/ihp/scaffold"


def workspace(run):
    if run not in ("1", "2", "3"):
        raise SystemExit("RUN must be 1, 2 or 3")
    return ROOT / ".work" / f"one-shot-ihp-{run}" / "ihp"


def home(run):
    return ROOT / ".work" / f"one-shot-ihp-{run}-homes" / "ihp"


def snapshot():
    original = json.loads(BASE.read_text())
    if one_shot.snapshot() != original:
        raise SystemExit("The original one-shot fixture changed")
    paths = [BASE, *EXTRAS, *(p for p in SCAFFOLD.rglob("*") if p.is_file())]
    files = {str(p.relative_to(ROOT)): one_shot.digest(p) for p in sorted(paths)}
    return {"base_fixture_sha256": original["sha256"],
            "sha256": one_shot.hashlib.sha256(json.dumps(files, sort_keys=True,
                              separators=(",", ":")).encode()).hexdigest(),
            "files": files}


def copy_shared(target, original, files):
    for name in original["files"]:
        source = ROOT / name
        if name.startswith("spec/"):
            dest = target / "realworld_spec" / name.removeprefix("spec/")
        elif name.startswith("one-shot/frontend/"):
            dest = target / "realworld_spec/frontend" / name.removeprefix("one-shot/frontend/")
        elif name.startswith("tools/security/hurl/"):
            dest = target / "security/hurl" / name.removeprefix("tools/security/hurl/")
        elif name.startswith("one-shot/harness/"):
            dest = target / "harness" / name.removeprefix("one-shot/harness/")
        elif name == "one-shot/PROMPT.md":
            dest = target / "PROMPT.md"
        elif name == "one-shot/MEASUREMENT.md":
            dest = target / "MEASUREMENT.md"
        elif name == "one-shot/README.md":
            dest = target / "EXPERIMENT.md"
        else:
            continue
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, dest)
        files[str(dest.relative_to(target))] = one_shot.digest(dest)


def make_home(run):
    target = home(run)
    if target.exists():
        raise SystemExit(f"Codex home exists: {target}")
    target.mkdir(parents=True, mode=0o700)
    auth = Path.home() / ".codex/auth.json"
    if not auth.is_file():
        raise SystemExit("Missing local Codex authentication")
    shutil.copy2(auth, target / "auth.json")
    (target / "auth.json").chmod(0o600)
    (target / "config.toml").write_text(f'''approval_policy = "never"
default_permissions = "workspace-only"
allow_login_shell = false
[features]
memories = false
multi_agent = false
apps = false
hooks = false
plugins = false
browser_use = false
computer_use = false
[permissions.workspace-only]
extends = ":workspace"
[permissions.workspace-only.filesystem]
":root" = "deny"
":minimal" = "read"
"/opt/homebrew" = "read"
"/Users/honey/.rbenv" = "read"
"/Users/honey/.cargo/bin" = "read"
"/Users/honey/.rustup" = "read"
"/etc/resolv.conf" = "read"
"/Library/Developer" = "read"
":tmpdir" = "deny"
":slash_tmp" = "deny"
[permissions.workspace-only.network]
enabled = true
[projects."{ROOT}"]
trust_level = "trusted"
''')
    (target / "config.toml").chmod(0o600)


def prepare(run):
    source = snapshot()
    if not MANIFEST.is_file() or json.loads(MANIFEST.read_text()) != source:
        raise SystemExit("IHP candidate fixture differs from frozen manifest")
    target = workspace(run)
    if target.exists():
        raise SystemExit(f"Workspace exists: {target}")
    if home(run).exists():
        raise SystemExit(f"Codex home exists: {home(run)}")
    browser = one_shot.image_id()
    shutil.copytree(SCAFFOLD, target)
    shutil.copytree(SCAFFOLD, target / ".scaffold")
    files = {}
    copy_shared(target, json.loads(BASE.read_text()), files)
    for src, dest in ((SOURCE / "ENVIRONMENT.md", target / "ENVIRONMENT.md"),
                      (SOURCE / "ihp.sh", target / "harness/ihp.sh")):
        shutil.copy2(src, dest)
        files[str(dest.relative_to(target))] = one_shot.digest(dest)
    (target / "harness/browser-image-id").write_text(browser + "\n")
    files["harness/browser-image-id"] = one_shot.digest(target / "harness/browser-image-id")
    for path in (target / ".scaffold").rglob("*"):
        if path.is_file():
            files[str(path.relative_to(target))] = one_shot.digest(path)
    record = {"stack": "ihp", "run": int(run), "fixture_sha256": source["sha256"],
              "base_fixture_sha256": source["base_fixture_sha256"],
              "prompt_sha256": one_shot.digest(target / "PROMPT.md"),
              "browser_image_id": browser, "files": dict(sorted(files.items()))}
    (target / "FIXTURE.json").write_text(json.dumps(record, indent=2) + "\n")
    for name in ("realworld_spec", "security", "harness", ".scaffold"):
        one_shot.readonly(target / name)
    for name in ("PROMPT.md", "MEASUREMENT.md", "ENVIRONMENT.md", "EXPERIMENT.md", "FIXTURE.json"):
        path = target / name
        path.chmod(path.stat().st_mode & ~0o222)
    make_home(run)
    one_shot.verify(target)
    print(f"ready: {target} (fixture {source['sha256']})")


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "freeze" and len(sys.argv) == 2:
        MANIFEST.write_text(json.dumps(snapshot(), indent=2) + "\n")
        print(json.loads(MANIFEST.read_text())["sha256"])
    elif cmd == "verify-source" and len(sys.argv) == 2:
        current = snapshot()
        if not MANIFEST.is_file() or json.loads(MANIFEST.read_text()) != current:
            raise SystemExit("IHP candidate fixture differs from frozen manifest")
        print(current["sha256"])
    elif cmd == "preflight" and len(sys.argv) == 2:
        one_shot.preflight()
    elif cmd == "prepare" and len(sys.argv) == 3:
        prepare(sys.argv[2])
    elif cmd == "verify" and len(sys.argv) == 3:
        one_shot.verify(sys.argv[2])
    else:
        raise SystemExit(__doc__)


if __name__ == "__main__":
    main()
