"""Freeze and prepare the separate, expert-guided TypeScript v2 condition.

Usage: python3 tools/typescript_expert.py verify-inputs|freeze|verify-source|prepare|verify WORKDIR
"""
import hashlib
import json
import secrets
import shutil
import subprocess
import sys
from pathlib import Path

import one_shot

ROOT = one_shot.ROOT
SOURCE = ROOT / "one-shot-v2-typescript-expert"
SHARED = ROOT / "one-shot-v2-expert"
SCAFFOLD = ROOT / "stacks/typescript/scaffold"
MANIFEST = SOURCE / "fixture-manifest.json"
WORK = ROOT / ".work/one-shot-v2-typescript-expert/typescript"
HOME = ROOT / ".work/one-shot-v2-typescript-expert-home/typescript"
CONTROL = ROOT / ".work/one-shot-v2-typescript-expert-control"
LOG = ROOT / ".work/one-shot-v2-typescript-expert-agent-log"
IMAGE = "agentmvc-typescript-v2-toolchain:preflight"
VOLUME = "agentmvc-typescript-v2-npm-cache"
GENERATED = {"node_modules", "build", ".adonisjs", "tmp", "coverage", "__pycache__"}
TOOLS = ("typescript_expert.py", "typescript_expert_broker.py",
         "typescript_expert_agent.py", "typescript_expert_isolation.py",
         "typescript_expert_preflight.py", "typescript_expert_independent.py",
         "typescript_expert_publish.py", "typescript_expert_runtime.py")


def source_files():
    files = [one_shot.MANIFEST, SHARED / "PROMPT.md", SHARED / "MEASUREMENT.md",
             SOURCE / "README.md", SOURCE / "ENVIRONMENT.md", SOURCE / "ts.sh",
             SOURCE / "agent.json", ROOT / "tools/quick-smoke.sh",
             ROOT / "stacks/typescript/PROVENANCE.md",
             ROOT / "stacks/typescript/Dockerfile.toolchain",
             ROOT / "stacks/typescript-expert/stack.json", ROOT / "tools/measure.py",
             ROOT / "tools/scrub.py", ROOT / "tools/one_shot_publish.py",
             ROOT / "tools/one_shot_live_bench.py", ROOT / "tools/live-load.mjs",
             *(ROOT / "tools/bench" / name for name in
               ("seed.py", "load.js", "bench.py", "run.sh", "bench.sh")),
             *(ROOT / "tools" / name for name in TOOLS)]
    files.extend(path for path in SCAFFOLD.rglob("*") if path.is_file()
                 and not GENERATED.intersection(path.relative_to(SCAFFOLD).parts))
    return sorted(files)


def snapshot():
    base = json.loads(one_shot.MANIFEST.read_text())
    if one_shot.snapshot() != base:
        raise SystemExit("Original one-shot fixture changed")
    if (SHARED / "PROMPT.md").read_bytes() != (ROOT / "one-shot-v2/PROMPT.md").read_bytes():
        raise SystemExit("Expert shared prompt differs from original v2 prompt")
    files = {str(path.relative_to(ROOT)): one_shot.digest(path) for path in source_files()}
    executable = {str(path.relative_to(ROOT)): bool(path.stat().st_mode & 0o111)
                  for path in source_files()}
    raw = json.dumps({"files": files, "executable": executable},
                     sort_keys=True, separators=(",", ":")).encode()
    return {"base_fixture_sha256": base["sha256"],
            "sha256": hashlib.sha256(raw).hexdigest(), "files": files,
            "executable": executable}


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


def verify_work(work):
    one_shot.verify(work)
    record = json.loads((Path(work) / "FIXTURE.json").read_text())
    if not (Path(work) / "harness/ts.sh").stat().st_mode & 0o111:
        raise ValueError("Frozen TypeScript wrapper lost its executable bit")
    if record["fixture_sha256"] != snapshot()["sha256"]:
        raise ValueError("Expert fixture source changed")


def prepare():
    source = snapshot()
    if not MANIFEST.is_file() or json.loads(MANIFEST.read_text()) != source:
        raise SystemExit("Expert fixture differs from frozen manifest")
    if WORK.exists() or HOME.exists() or CONTROL.exists():
        raise SystemExit("Expert workdir, home, or control already exists")
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
    record = {"stack": "typescript", "condition": "v2-expert-guided",
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
    verify_work(WORK)
    print(f"ready: {WORK} (fixture {source['sha256']})")


def main():
    command = sys.argv[1] if len(sys.argv) > 1 else ""
    if command == "verify-inputs" and len(sys.argv) == 2:
        source = snapshot()
        print(json.dumps({"candidate_sha256": source["sha256"],
                          "prompt_sha256": source["files"]["one-shot-v2-expert/PROMPT.md"],
                          "files": len(source["files"])}, indent=2))
    elif command == "freeze" and len(sys.argv) == 2:
        MANIFEST.write_text(json.dumps(snapshot(), indent=2) + "\n")
        print(json.loads(MANIFEST.read_text())["sha256"])
    elif command == "verify-source" and len(sys.argv) == 2:
        source = snapshot()
        if not MANIFEST.is_file() or json.loads(MANIFEST.read_text()) != source:
            raise SystemExit("Expert fixture differs from frozen manifest")
        print(source["sha256"])
    elif command == "prepare" and len(sys.argv) == 2:
        prepare()
    elif command == "verify" and len(sys.argv) == 3:
        verify_work(sys.argv[2])
    else:
        raise SystemExit(__doc__)


if __name__ == "__main__":
    main()
