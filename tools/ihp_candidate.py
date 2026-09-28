"""Freeze and prepare the isolated IHP candidate without altering the three-stack fixture.

Usage: python3 tools/ihp_candidate.py freeze|verify-source|preflight|prepare RUN|verify WORKDIR
RUN is a positive run number. Each run needs its own Nix store volume; see docs/running.md.
Preparing never launches a measured agent.
"""
import json
import os
import shutil
import sys
from pathlib import Path

import codex_home
import one_shot

ROOT = one_shot.ROOT
SOURCE = ROOT / "ihp-candidate"
MANIFEST = SOURCE / "fixture-manifest.json"
BASE = one_shot.MANIFEST
EXTRAS = [SOURCE / "README.md", SOURCE / "ENVIRONMENT.md", SOURCE / "ihp.sh",
          ROOT / "tools/ihp_candidate.py", ROOT / "tools/ihp_candidate_broker.py",
          ROOT / "tools/ihp_candidate_agent.py",
          ROOT / "tools/codex_home.py",
          ROOT / "stacks/ihp/stack.json",
          ROOT / "tools/ihp_candidate_host/check-production.sh"]
SCAFFOLD = ROOT / "stacks/ihp/scaffold"


def is_run(value):
    """A measured run number: a positive integer without leading zeros."""
    return value.isdigit() and not value.startswith("0")


def workspace(run):
    if not is_run(run):
        raise SystemExit("RUN must be a positive integer, such as 1 or 5")
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
    codex_home.write_home(home(run))

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
    codex_home.write_token(ROOT / ".work" / f"one-shot-ihp-{run}-control" / "token")
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
