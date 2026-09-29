"""Freeze and prepare the isolated Servant v2 pilot.

Usage: python3 tools/servant_v2.py freeze|verify-source|preflight|prepare|verify WORKDIR
"""
import hashlib
import json
import secrets
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path

import one_shot

ROOT = one_shot.ROOT
SOURCE = ROOT / "one-shot-v2"
MANIFEST = SOURCE / "fixture-manifest.json"
BASE = one_shot.MANIFEST
SCAFFOLD = ROOT / "stacks/servant/scaffold"
WORK = ROOT / ".work/one-shot-v2-servant/servant"
HOME = ROOT / ".work/one-shot-v2-servant-home/servant"
CONTROL = ROOT / ".work/one-shot-v2-servant-control"
LOG = ROOT / ".work/one-shot-v2-servant-agent-log"
SCRIPTS = ("servant_v2.py", "servant_v2_broker.py", "servant_v2_agent.py")


def snapshot():
    base = json.loads(BASE.read_text())
    if one_shot.snapshot() != base:
        raise SystemExit("Original one-shot fixture changed")
    paths = [BASE, SOURCE / "PROMPT.md", SOURCE / "README.md",
             SOURCE / "MEASUREMENT.md", SOURCE / "environment/servant.md",
             SOURCE / "hs.sh", SOURCE / "hs-watch.sh", ROOT / "tools/quick-smoke.sh",
             ROOT / "stacks/servant/stack.json",
             ROOT / "stacks/servant/Dockerfile.toolchain",
             *(ROOT / "tools" / script for script in SCRIPTS),
             *(p for p in SCAFFOLD.rglob("*") if p.is_file())]
    files = {str(p.relative_to(ROOT)): one_shot.digest(p) for p in sorted(paths)}
    raw = json.dumps(files, sort_keys=True, separators=(",", ":")).encode()
    return {"base_fixture_sha256": base["sha256"],
            "sha256": hashlib.sha256(raw).hexdigest(), "files": files}


def copy(source, dest, files):
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, dest)
    files[str(dest.relative_to(WORK))] = one_shot.digest(dest)


def make_home():
    if HOME.exists():
        raise SystemExit(f"Codex home exists: {HOME}")
    HOME.mkdir(parents=True, mode=0o700)
    auth = Path.home() / ".codex/auth.json"
    if not auth.is_file():
        raise SystemExit("Missing Codex authentication")
    shutil.copy2(auth, HOME / "auth.json")
    (HOME / "auth.json").chmod(0o600)
    (HOME / "config.toml").write_text(f'''approval_policy = "never"
default_permissions = "workspace-only"
allow_login_shell = false
[features]
memories = false
multi_agent = false
apps = false
hooks = false
plugins = false
network_proxy = true
browser_use = false
computer_use = false
[permissions.workspace-only]
extends = ":workspace"
[permissions.workspace-only.filesystem]
":root" = "deny"
":minimal" = "read"
"/opt/homebrew" = "read"
"/etc/resolv.conf" = "read"
"/var/run/docker.sock" = "deny"
"/Users/honey/.orbstack/run/docker.sock" = "deny"
"{WORK / 'realworld_spec'}" = "read"
"{WORK / 'security'}" = "read"
"{WORK / 'harness'}" = "read"
"{WORK / '.scaffold'}" = "read"
"{WORK / 'PROMPT.md'}" = "read"
"{WORK / 'ENVIRONMENT.md'}" = "read"
"{WORK / 'MEASUREMENT.md'}" = "read"
"{WORK / 'EXPERIMENT.md'}" = "read"
"{WORK / 'FIXTURE.json'}" = "read"
[permissions.workspace-only.network]
enabled = true
[permissions.workspace-only.network.unix_sockets]
"/var/run/docker.sock" = "deny"
"/Users/honey/.orbstack/run/docker.sock" = "deny"
[permissions.workspace-only.network.domains]
"*" = "allow"
"127.0.0.1" = "allow"
[projects."{ROOT}"]
trust_level = "trusted"
''')
    (HOME / "config.toml").chmod(0o600)


def prepare():
    source = snapshot()
    if not MANIFEST.is_file() or json.loads(MANIFEST.read_text()) != source:
        raise SystemExit("Servant v2 fixture differs from frozen manifest")
    if WORK.exists():
        raise SystemExit(f"Workspace exists: {WORK}")
    if HOME.exists() or CONTROL.exists():
        raise SystemExit("Servant pilot home or control directory already exists")
    browser = one_shot.image_id()
    shutil.copytree(SCAFFOLD, WORK)
    shutil.copytree(SCAFFOLD, WORK / ".scaffold")
    files = {}
    base = json.loads(BASE.read_text())
    for name in base["files"]:
        src = ROOT / name
        if name.startswith("spec/"):
            dest = WORK / "realworld_spec" / name.removeprefix("spec/")
        elif name.startswith("one-shot/frontend/"):
            dest = WORK / "realworld_spec/frontend" / name.removeprefix("one-shot/frontend/")
        elif name.startswith("tools/security/hurl/"):
            dest = WORK / "security/hurl" / name.removeprefix("tools/security/hurl/")
        elif name.startswith("one-shot/harness/"):
            dest = WORK / "harness" / name.removeprefix("one-shot/harness/")
        else:
            continue
        copy(src, dest, files)
    for src, dest in ((SOURCE / "PROMPT.md", WORK / "PROMPT.md"),
                      (SOURCE / "README.md", WORK / "EXPERIMENT.md"),
                      (SOURCE / "MEASUREMENT.md", WORK / "MEASUREMENT.md"),
                      (SOURCE / "environment/servant.md", WORK / "ENVIRONMENT.md"),
                      (SOURCE / "hs.sh", WORK / "harness/hs.sh"),
                      (SOURCE / "hs-watch.sh", WORK / "harness/hs-watch.sh"),
                      (ROOT / "tools/quick-smoke.sh", WORK / "harness/quick-smoke.sh")):
        copy(src, dest, files)
    (WORK / "harness/browser-image-id").write_text(browser + "\n")
    files["harness/browser-image-id"] = one_shot.digest(WORK / "harness/browser-image-id")
    for path in (WORK / ".scaffold").rglob("*"):
        if path.is_file():
            files[str(path.relative_to(WORK))] = one_shot.digest(path)
    record = {"stack": "servant", "condition": "v2-pilot",
              "fixture_sha256": source["sha256"],
              "base_fixture_sha256": source["base_fixture_sha256"],
              "prompt_sha256": one_shot.digest(WORK / "PROMPT.md"),
              "toolchain_image_id": image_id(), "browser_image_id": browser,
              "files": dict(sorted(files.items()))}
    (WORK / "FIXTURE.json").write_text(json.dumps(record, indent=2) + "\n")
    for name in ("realworld_spec", "security", "harness", ".scaffold"):
        one_shot.readonly(WORK / name)
    for name in ("PROMPT.md", "MEASUREMENT.md", "ENVIRONMENT.md", "EXPERIMENT.md", "FIXTURE.json"):
        path = WORK / name
        path.chmod(path.stat().st_mode & ~0o222)
    make_home()
    CONTROL.mkdir(parents=True, mode=0o700)
    (CONTROL / "token").write_text(secrets.token_hex(32) + "\n")
    (CONTROL / "token").chmod(0o600)
    one_shot.verify(WORK)
    print(f"ready: {WORK} (fixture {source['sha256']})")


def image_id():
    return subprocess.check_output(["docker", "image", "inspect",
                                    "agentmvc-servant-v2-toolchain:preflight",
                                    "--format", "{{.Id}}"], text=True).strip()


def preflight():
    subprocess.run(["docker", "build", "-f", str(ROOT / "stacks/servant/Dockerfile.toolchain"),
                    "-t", "agentmvc-servant-v2-toolchain:preflight", str(SCAFFOLD)], check=True)
    subprocess.run(["docker", "run", "--rm", "--mount",
                    "type=volume,source=agentmvc-servant-v2-pilot-store,target=/root/.local/state/cabal",
                    "agentmvc-servant-v2-toolchain:preflight", "sh", "-ec",
                    "test -d /root/.local/state/cabal/store"], check=True)
    browser = one_shot.preflight()
    port = one_shot.preflight_port()
    image, name = "agentmvc-servant-v2-scaffold-smoke:preflight", "agentmvc-servant-v2-scaffold-smoke"
    (ROOT / ".work").mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="servant-v2-preflight-", dir=ROOT / ".work") as temp:
        temp = Path(temp)
        shutil.copytree(SCAFFOLD, temp, dirs_exist_ok=True)
        subprocess.run(["docker", "run", "--rm", "--network", "host", "--mount",
                        f"type=bind,source={temp},target=/work/app", "-w", "/work/app",
                        "agentmvc-servant-v2-toolchain:preflight", "cabal", "build", "exe:conduit"], check=True)
        subprocess.run(["docker", "build", "-q", "-t", image, str(temp)], check=True)
        subprocess.run(["docker", "rm", "-f", name], capture_output=True)
        try:
            subprocess.run(["docker", "run", "-d", "--name", name, "-p", f"127.0.0.1:{port}:{port}",
                            "-e", f"PORT={port}", image], check=True, capture_output=True)
            for _ in range(100):
                try:
                    with urllib.request.urlopen(f"http://127.0.0.1:{port}/health", timeout=1) as response:
                        if json.load(response) == {"status": "ok"}:
                            break
                except Exception:
                    time.sleep(.1)
            else:
                raise SystemExit("Servant scaffold production image did not serve GET /health")
        finally:
            subprocess.run(["docker", "rm", "-f", name], capture_output=True)
            subprocess.run(["docker", "image", "rm", image], capture_output=True)
    print(f"Servant scaffold compile and production health passed; toolchain {image_id()}, browser {browser}")


def main():
    command = sys.argv[1] if len(sys.argv) > 1 else ""
    if command == "freeze" and len(sys.argv) == 2:
        MANIFEST.write_text(json.dumps(snapshot(), indent=2) + "\n")
        print(json.loads(MANIFEST.read_text())["sha256"])
    elif command == "verify-source" and len(sys.argv) == 2:
        current = snapshot()
        if not MANIFEST.is_file() or json.loads(MANIFEST.read_text()) != current:
            raise SystemExit("Servant v2 fixture differs from frozen manifest")
        print(current["sha256"])
    elif command == "preflight" and len(sys.argv) == 2:
        preflight()
    elif command == "prepare" and len(sys.argv) == 2:
        prepare()
    elif command == "verify" and len(sys.argv) == 3:
        one_shot.verify(sys.argv[2])
    else:
        raise SystemExit(__doc__)


if __name__ == "__main__":
    main()
