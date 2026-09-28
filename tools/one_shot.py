"""Prepare self-contained, isolated one-shot backend workspaces.

Usage:
  python3 tools/one_shot.py preflight
  python3 tools/one_shot.py freeze
  python3 tools/one_shot.py prepare [rails|phoenix|loco ...]
  python3 tools/one_shot.py verify WORKDIR
"""

import hashlib
import json
import os
import re
import shutil
import socket
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "one-shot"
MANIFEST = SOURCE / "fixture-manifest.json"
IMAGE = "agentmvc-one-shot-browser:1.63.0"
STACKS = ("rails", "phoenix", "loco")
RUN_NAME = os.environ.get("ONE_SHOT_RUN", "one-shot")
if not re.fullmatch(r"[a-z][a-z0-9-]*", RUN_NAME):
    raise SystemExit("ONE_SHOT_RUN must be a simple lowercase name")
WORK = ROOT / ".work" / RUN_NAME
HOMES = ROOT / ".work" / f"{RUN_NAME}-homes"
LOGS = ROOT / ".work" / f"{RUN_NAME}-agent-logs"
CONTROL = ROOT / ".work" / f"{RUN_NAME}-control"
BROKER_LOG = ROOT / ".work" / f"{RUN_NAME}-broker"
INDEPENDENT = ROOT / ".work" / f"{RUN_NAME}-independent"
RUNTIME = ROOT / ".work" / f"{RUN_NAME}-runtime"
RESULTS = ROOT / "results" / RUN_NAME
OMIT = {
    "spec/bin/run-hurl",
    "spec/features/live-editing/bin/check",
    "spec/features/live-editing/fixture-manifest.json",
}
GENERATED = {"node_modules", "dist", "test-results", "playwright-report", "__pycache__", ".DS_Store"}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fixture_sources():
    paths = [SOURCE / "PROMPT.md", SOURCE / "README.md", SOURCE / "MEASUREMENT.md",
             ROOT / "tools/one_shot.py", ROOT / "tools/one_shot_broker.py",
             ROOT / "tools/reference-live/server.mjs"]
    for folder in (SOURCE / "frontend", SOURCE / "harness", SOURCE / "environment",
                   ROOT / "spec", ROOT / "tools/security/hurl", ROOT / "tools/one_shot_host",
                   *(ROOT / "stacks" / stack / "scaffold" for stack in STACKS)):
        paths.extend(path for path in folder.rglob("*") if path.is_file()
                     and not GENERATED.intersection(path.relative_to(folder).parts)
                     and str(path.relative_to(ROOT)) not in OMIT)
    return sorted(paths)


def snapshot():
    files = {str(path.relative_to(ROOT)): digest(path) for path in fixture_sources()}
    data = json.dumps(files, sort_keys=True, separators=(",", ":")).encode()
    return {"sha256": hashlib.sha256(data).hexdigest(), "files": files}


def image_id():
    return subprocess.check_output(["docker", "image", "inspect", IMAGE, "--format", "{{.Id}}"], text=True).strip()


def build_browser():
    subprocess.run(["docker", "build", "--progress=plain", "-f", str(SOURCE / "harness/Dockerfile.browser"),
                    "-t", IMAGE, str(SOURCE)], check=True)
    return image_id()


def preflight_port():
    for port in range(4300, 4400):
        try:
            with socket.socket() as backend, socket.socket() as frontend:
                backend.bind(("127.0.0.1", port))
                frontend.bind(("127.0.0.1", port + 1072))
            return port
        except OSError:
            continue
    raise RuntimeError("no free ports for the reference backend and browser frontend")


def preflight():
    browser = build_browser()
    port = preflight_port()
    if not (ROOT / "frontend/node_modules/ws").is_dir():
        subprocess.run(["npm", "ci", "--silent"], cwd=ROOT / "frontend", check=True)
    (ROOT / ".work").mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="one-shot-preflight-", dir=ROOT / ".work") as temp:
        work = Path(temp)
        shutil.copytree(SOURCE / "frontend", work / "realworld_spec/frontend",
                        ignore=shutil.ignore_patterns(*GENERATED))
        shutil.copytree(SOURCE / "harness", work / "harness")
        (work / "harness/browser-image-id").write_text(browser + "\n")
        with (work / "reference.log").open("w") as log:
            server = subprocess.Popen(["node", str(ROOT / "tools/reference-live/server.mjs")],
                                      cwd=ROOT, env={**os.environ, "PORT": str(port)},
                                      stdout=log, stderr=subprocess.STDOUT)
            try:
                for _ in range(100):
                    if server.poll() is not None:
                        raise RuntimeError("reference server exited during browser preflight")
                    try:
                        with socket.create_connection(("127.0.0.1", port), timeout=0.2):
                            break
                    except OSError:
                        time.sleep(0.1)
                else:
                    raise RuntimeError(f"reference server did not listen on port {port}")
                subprocess.run([str(ROOT / "tools/one_shot_host/check-live.sh"), str(port)],
                               env={**os.environ, "ONE_SHOT_WORKDIR": str(work)}, check=True)
            finally:
                server.terminate()
                server.wait(timeout=10)
    print(f"browser preflight passed: {browser}")
    return browser


def readonly(path):
    for file in path.rglob("*"):
        if file.is_file():
            file.chmod(file.stat().st_mode & ~0o222)


def materialize(stack, fixture, browser):
    target = WORK / stack
    if target.exists():
        raise SystemExit(f"workspace already exists: {target}; move it aside before preparing again")
    scaffold = ROOT / "stacks" / stack / "scaffold"
    shutil.copytree(scaffold, target, ignore=shutil.ignore_patterns(*GENERATED))
    shutil.copytree(scaffold, target / ".scaffold", ignore=shutil.ignore_patterns(*GENERATED))

    files = {}

    def copy(source, dest):
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, dest)
        files[str(dest.relative_to(target))] = digest(dest)

    for source_name in fixture["files"]:
        source = ROOT / source_name
        if source_name.startswith("spec/"):
            dest = target / "realworld_spec" / source_name.removeprefix("spec/")
        elif source_name.startswith("one-shot/frontend/"):
            dest = target / "realworld_spec/frontend" / source_name.removeprefix("one-shot/frontend/")
        elif source_name.startswith("tools/security/hurl/"):
            dest = target / "security/hurl" / source_name.removeprefix("tools/security/hurl/")
        elif source_name.startswith("one-shot/harness/"):
            dest = target / "harness" / source_name.removeprefix("one-shot/harness/")
        elif source_name == "one-shot/PROMPT.md":
            dest = target / "PROMPT.md"
        elif source_name == "one-shot/MEASUREMENT.md":
            dest = target / "MEASUREMENT.md"
        elif source_name == "one-shot/README.md":
            dest = target / "EXPERIMENT.md"
        elif source_name == f"one-shot/environment/{stack}.md":
            dest = target / "ENVIRONMENT.md"
        else:
            continue
        copy(source, dest)

    (target / "harness/browser-image-id").write_text(browser + "\n")
    files["harness/browser-image-id"] = digest(target / "harness/browser-image-id")
    for source in (target / ".scaffold").rglob("*"):
        if source.is_file():
            files[str(source.relative_to(target))] = digest(source)
    record = {"stack": stack, "fixture_sha256": fixture["sha256"],
              "prompt_sha256": digest(target / "PROMPT.md"), "browser_image_id": browser,
              "files": dict(sorted(files.items()))}
    (target / "FIXTURE.json").write_text(json.dumps(record, indent=2) + "\n")
    for part in ("realworld_spec", "security", "harness", ".scaffold"):
        readonly(target / part)
    for name in ("PROMPT.md", "MEASUREMENT.md", "ENVIRONMENT.md", "EXPERIMENT.md", "FIXTURE.json"):
        (target / name).chmod((target / name).stat().st_mode & ~0o222)
    print(f"{stack}: {target} (fixture {fixture['sha256']})")


def verify(work):
    work = Path(work)
    record = json.loads((work / "FIXTURE.json").read_text())
    changed = [name for name, expected in record["files"].items()
               if not (work / name).is_file() or digest(work / name) != expected]
    for part in ("realworld_spec", "security", "harness", ".scaffold"):
        for path in (work / part).rglob("*"):
            if path.is_file() and not GENERATED.intersection(path.relative_to(work).parts) \
                    and str(path.relative_to(work)) not in record["files"]:
                changed.append(str(path.relative_to(work)))
    if changed:
        raise SystemExit("fixture changed: " + ", ".join(changed))
    print(record["fixture_sha256"])


def main():
    command = sys.argv[1] if len(sys.argv) > 1 else ""
    if command == "preflight" and len(sys.argv) == 2:
        preflight()
    elif command == "freeze" and len(sys.argv) == 2:
        MANIFEST.write_text(json.dumps(snapshot(), indent=2) + "\n")
        print(json.loads(MANIFEST.read_text())["sha256"])
    elif command == "verify-source" and len(sys.argv) == 2:
        current = snapshot()
        if not MANIFEST.exists() or json.loads(MANIFEST.read_text()) != current:
            raise SystemExit("one-shot fixture differs from frozen manifest")
        print(current["sha256"])
    elif command == "prepare":
        chosen = sys.argv[2:] or STACKS
        if any(stack not in STACKS for stack in chosen):
            raise SystemExit("choose rails, phoenix, or loco")
        if any((WORK / stack).exists() for stack in chosen):
            raise SystemExit("a selected workspace exists; move it aside before preparing again")
        fixture = snapshot()
        if not MANIFEST.exists() or json.loads(MANIFEST.read_text()) != fixture:
            raise SystemExit("one-shot fixture differs from frozen manifest")
        browser = preflight()
        for stack in chosen:
            materialize(stack, fixture, browser)
    elif command == "verify" and len(sys.argv) == 3:
        verify(sys.argv[2])
    else:
        raise SystemExit("usage: one_shot.py preflight|freeze|verify-source|prepare [rails|phoenix|loco ...]|verify WORKDIR")


if __name__ == "__main__":
    main()
