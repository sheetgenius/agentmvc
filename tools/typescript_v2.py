"""Freeze, preflight, and prepare the isolated TypeScript v2 pilot.

Usage: python3 tools/typescript_v2.py preflight|freeze|verify-source|prepare|verify WORKDIR
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
SOURCE = ROOT / "one-shot-v2-typescript"
SHARED = ROOT / "one-shot-v2"
SCAFFOLD = ROOT / "stacks/typescript/scaffold"
MANIFEST = SOURCE / "fixture-manifest.json"
WORK = ROOT / ".work/one-shot-v2-typescript/typescript"
HOME = ROOT / ".work/one-shot-v2-typescript-home/typescript"
CONTROL = ROOT / ".work/one-shot-v2-typescript-control"
LOG = ROOT / ".work/one-shot-v2-typescript-agent-log"
IMAGE = "agentmvc-typescript-v2-toolchain:preflight"
VOLUME = "agentmvc-typescript-v2-npm-cache"
GENERATED = {"node_modules", "build", ".adonisjs", "tmp", "coverage", "__pycache__"}


def source_files():
    paths = [one_shot.MANIFEST, SHARED / "PROMPT.md", SHARED / "MEASUREMENT.md",
             SOURCE / "README.md", SOURCE / "ENVIRONMENT.md", SOURCE / "ts.sh",
             ROOT / "tools/quick-smoke.sh", ROOT / "stacks/typescript/stack.json",
             ROOT / "stacks/typescript/PROVENANCE.md",
             ROOT / "stacks/typescript/Dockerfile.toolchain",
             *(ROOT / "tools" / name for name in
               ("typescript_v2.py", "typescript_v2_broker.py", "typescript_v2_agent.py",
                "typescript_v2_isolation.py"))]
    paths.extend(path for path in SCAFFOLD.rglob("*") if path.is_file()
                 and not GENERATED.intersection(path.relative_to(SCAFFOLD).parts))
    return sorted(paths)


def snapshot():
    base = json.loads(one_shot.MANIFEST.read_text())
    if one_shot.snapshot() != base:
        raise SystemExit("Original one-shot fixture changed")
    files = {str(path.relative_to(ROOT)): one_shot.digest(path) for path in source_files()}
    raw = json.dumps(files, sort_keys=True, separators=(",", ":")).encode()
    return {"base_fixture_sha256": base["sha256"],
            "sha256": hashlib.sha256(raw).hexdigest(), "files": files}


def image_id():
    return subprocess.check_output(["docker", "image", "inspect", IMAGE,
                                    "--format", "{{.Id}}"], text=True).strip()


def copy(source, dest, files):
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, dest)
    files[str(dest.relative_to(WORK))] = one_shot.digest(dest)


def container(work, *command):
    return ["docker", "run", "--rm", "--network", "host",
            "--mount", f"type=volume,source={VOLUME},target=/root/.npm",
            "--mount", f"type=bind,source={work},target=/work/app",
            "-w", "/work/app", IMAGE, *command]


def make_home():
    if HOME.exists():
        raise SystemExit(f"Codex home exists: {HOME}")
    HOME.mkdir(parents=True, mode=0o700)
    auth = Path.home() / ".codex/auth.json"
    if not auth.is_file():
        raise SystemExit("Missing Codex authentication")
    shutil.copy2(auth, HOME / "auth.json")
    (HOME / "auth.json").chmod(0o600)
    socket = Path.home() / ".orbstack/run/docker.sock"
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
"{socket}" = "deny"
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
"{socket}" = "deny"
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
        raise SystemExit("TypeScript v2 fixture differs from frozen manifest")
    if WORK.exists() or HOME.exists() or CONTROL.exists():
        raise SystemExit("Pilot workspace, home, or control already exists")
    browser = one_shot.image_id()
    ignore = shutil.ignore_patterns(*GENERATED)
    shutil.copytree(SCAFFOLD, WORK, ignore=ignore)
    shutil.copytree(SCAFFOLD, WORK / ".scaffold", ignore=ignore)
    files = {}
    base = json.loads(one_shot.MANIFEST.read_text())
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
    for src, dest in ((SHARED / "PROMPT.md", WORK / "PROMPT.md"),
                      (SHARED / "MEASUREMENT.md", WORK / "MEASUREMENT.md"),
                      (SOURCE / "README.md", WORK / "EXPERIMENT.md"),
                      (SOURCE / "ENVIRONMENT.md", WORK / "ENVIRONMENT.md"),
                      (SOURCE / "ts.sh", WORK / "harness/ts.sh"),
                      (ROOT / "tools/quick-smoke.sh", WORK / "harness/quick-smoke.sh")):
        copy(src, dest, files)
    (WORK / "harness/browser-image-id").write_text(browser + "\n")
    files["harness/browser-image-id"] = one_shot.digest(WORK / "harness/browser-image-id")
    for path in (WORK / ".scaffold").rglob("*"):
        if path.is_file():
            files[str(path.relative_to(WORK))] = one_shot.digest(path)
    record = {"stack": "typescript", "condition": "v2-pilot",
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
    subprocess.run(container(WORK, "npm", "ci", "--no-audit", "--no-fund"), check=True)
    make_home()
    CONTROL.mkdir(parents=True, mode=0o700)
    (CONTROL / "token").write_text(secrets.token_hex(32) + "\n")
    (CONTROL / "token").chmod(0o600)
    one_shot.verify(WORK)
    print(f"ready: {WORK} (fixture {source['sha256']})")


def preflight():
    subprocess.run(["docker", "build", "-q", "-f", str(ROOT / "stacks/typescript/Dockerfile.toolchain"),
                    "-t", IMAGE, str(ROOT / "stacks/typescript")], check=True)
    browser = one_shot.preflight()
    with tempfile.TemporaryDirectory(prefix="typescript-v2-preflight-", dir=ROOT / ".work") as temp:
        work = Path(temp)
        shutil.copytree(SCAFFOLD, work, dirs_exist_ok=True,
                        ignore=shutil.ignore_patterns(*GENERATED))
        for command in (("npm", "ci", "--no-audit", "--no-fund"),
                        ("npm", "run", "typecheck"), ("npm", "run", "lint"),
                        ("npm", "run", "build")):
            subprocess.run(container(work, *command), check=True)
        image = "agentmvc-typescript-v2-scaffold-smoke:preflight"
        name = "agentmvc-typescript-v2-scaffold-smoke"
        port = one_shot.preflight_port()
        subprocess.run(["docker", "build", "-q", "-t", image, str(work)], check=True)
        subprocess.run([str(ROOT / "tools/one_shot_host/db.sh"), "start", str(port)], check=True)
        try:
            subprocess.run(["docker", "run", "-d", "--name", name, "--network", "host",
                            "-e", f"DATABASE_URL=postgres://agentmvc:agentmvc@127.0.0.1:{port + 50000}/agentmvc",
                            "-e", "SECRET_KEY_BASE=typescript-preflight-secret-0123456789abcdef",
                            "-e", f"PORT={port}", image], check=True, capture_output=True)
            for _ in range(100):
                try:
                    with urllib.request.urlopen(f"http://127.0.0.1:{port}/health", timeout=1) as response:
                        if json.load(response) == {"status": "ok"}:
                            break
                except Exception:
                    time.sleep(.1)
            else:
                raise SystemExit("TypeScript scaffold production image did not serve GET /health")
            logs = subprocess.check_output(["docker", "logs", name], text=True, stderr=subprocess.STDOUT)
            if "Starting worker" not in logs or "migrated" not in logs:
                raise SystemExit("TypeScript scaffold did not migrate or start queue worker")
        finally:
            subprocess.run(["docker", "rm", "-f", name], capture_output=True)
            subprocess.run([str(ROOT / "tools/one_shot_host/db.sh"), "stop", str(port)], capture_output=True)
            subprocess.run(["docker", "image", "rm", image], capture_output=True)
    print(f"TypeScript scaffold and production health passed; toolchain {image_id()}, browser {browser}")


def main():
    command = sys.argv[1] if len(sys.argv) > 1 else ""
    if command == "preflight" and len(sys.argv) == 2:
        preflight()
    elif command == "freeze" and len(sys.argv) == 2:
        MANIFEST.write_text(json.dumps(snapshot(), indent=2) + "\n")
        print(json.loads(MANIFEST.read_text())["sha256"])
    elif command == "verify-source" and len(sys.argv) == 2:
        source = snapshot()
        if not MANIFEST.is_file() or json.loads(MANIFEST.read_text()) != source:
            raise SystemExit("TypeScript v2 fixture differs from frozen manifest")
        print(source["sha256"])
    elif command == "prepare" and len(sys.argv) == 2:
        prepare()
    elif command == "verify" and len(sys.argv) == 3:
        one_shot.verify(sys.argv[2])
    else:
        raise SystemExit(__doc__)


if __name__ == "__main__":
    main()
