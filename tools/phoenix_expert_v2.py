"""Freeze, preflight and prepare the isolated Phoenix expert v2 diagnostic.

Usage: python3 tools/phoenix_expert_v2.py preflight|freeze|verify-source|prepare|verify WORKDIR
"""
import hashlib
import json
import os
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
SOURCE = ROOT / "one-shot-v2-phoenix-expert"
SHARED = ROOT / "one-shot-v2-expert"
SCAFFOLD = ROOT / "stacks/phoenix-expert/scaffold"
MANIFEST = SOURCE / "fixture-manifest.json"
WORK = ROOT / ".work/one-shot-v2-phoenix-expert/phoenix"
HOME = ROOT / ".work/one-shot-v2-phoenix-expert-home/phoenix"
CONTROL = ROOT / ".work/one-shot-v2-phoenix-expert-control"
LOG = ROOT / ".work/one-shot-v2-phoenix-expert-agent-log"
RESULTS = ROOT / "results/one-shot-v2-phoenix-expert"
IMAGE = "agentmvc-phoenix-expert-v2-toolchain:preflight"
PORT = 4108
GENERATED = {"deps", "_build", ".mix", ".hex", "tmp", "coverage", "__pycache__"}
TOOL_SOURCES = ("phoenix_expert_v2.py", "phoenix_expert_v2_broker.py",
                "phoenix_expert_v2_agent.py", "phoenix_expert_v2_isolation.py",
                "phoenix_expert_v2_independent.py", "phoenix_expert_v2_publish.py",
                "phoenix_expert_v2_runtime.py")


def source_files():
    paths = [one_shot.MANIFEST, SHARED / "PROMPT.md", SHARED / "MEASUREMENT.md",
             SOURCE / "README.md", SOURCE / "ENVIRONMENT.md", SOURCE / "phoenix.sh",
             ROOT / "tools/quick-smoke.sh", ROOT / "tools/measure.py",
             ROOT / "tools/scrub.py", ROOT / "tools/one_shot_publish.py",
             ROOT / "tools/one_shot_live_bench.py",
             ROOT / "stacks/phoenix-expert/stack.json",
             ROOT / "stacks/phoenix-expert/PROVENANCE.md",
             ROOT / "stacks/phoenix-expert/Dockerfile.toolchain",
             *(ROOT / "tools" / name for name in TOOL_SOURCES)]
    paths.extend(path for path in (ROOT / "tools/bench").rglob("*") if path.is_file()
                 and "__pycache__" not in path.parts and path.suffix != ".pyc")
    paths.extend(path for path in SCAFFOLD.rglob("*") if path.is_file()
                 and not GENERATED.intersection(path.relative_to(SCAFFOLD).parts))
    return sorted(paths)


def snapshot():
    base = json.loads(one_shot.MANIFEST.read_text())
    if one_shot.snapshot() != base:
        raise SystemExit("Original one-shot fixture changed")
    if (SHARED / "PROMPT.md").read_bytes() != (ROOT / "one-shot-v2/PROMPT.md").read_bytes():
        raise SystemExit("Expert shared prompt differs from original v2 prompt")
    paths = source_files()
    files = {str(path.relative_to(ROOT)): one_shot.digest(path) for path in paths}
    modes = {str(path.relative_to(ROOT)): path.stat().st_mode & 0o111 for path in paths}
    raw = json.dumps({"files": files, "executable_modes": modes},
                     sort_keys=True, separators=(",", ":")).encode()
    return {"base_fixture_sha256": base["sha256"],
            "sha256": hashlib.sha256(raw).hexdigest(), "files": files,
            "executable_modes": modes}


def image_id():
    return subprocess.check_output(["docker", "image", "inspect", IMAGE,
                                    "--format", "{{.Id}}"], text=True).strip()


def copy(source, dest, files):
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, dest)
    files[str(dest.relative_to(WORK))] = one_shot.digest(dest)


def verify_workspace(work):
    one_shot.verify(work)
    for name in ("harness/phoenix.sh", "harness/check-all.sh",
                 "harness/check-production.sh"):
        if not os.access(work / name, os.X_OK):
            raise SystemExit(f"Frozen check is not executable: {name}")


def db_url(port, database="agentmvc"):
    return f"postgres://agentmvc:agentmvc@host.docker.internal:{port + 50000}/{database}"


def container(work, port=PORT, *, detached=False, name=None):
    args = ["docker", "run", "-d" if detached else "--rm"]
    if name:
        args += ["--name", name]
    args += ["--network", "host", "--mount",
             f"type=bind,source={work},target=/work/app", "-w", "/work/app",
             "-e", f"PORT={port}", "-e", f"DATABASE_URL={db_url(port)}",
             "-e", f"TEST_DATABASE_URL={db_url(port, 'agentmvc_test')}",
             "-e", "SECRET_KEY_BASE=" + "0123456789abcdef" * 8,
             IMAGE]
    return args


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
        raise SystemExit("Phoenix expert fixture differs from frozen manifest")
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
        elif name.startswith("one-shot/harness/") and name != "one-shot/harness/phoenix.sh":
            dest = WORK / "harness" / name.removeprefix("one-shot/harness/")
        else:
            continue
        copy(src, dest, files)
    for src, dest in ((SHARED / "PROMPT.md", WORK / "PROMPT.md"),
                      (SHARED / "MEASUREMENT.md", WORK / "MEASUREMENT.md"),
                      (SOURCE / "README.md", WORK / "EXPERIMENT.md"),
                      (SOURCE / "ENVIRONMENT.md", WORK / "ENVIRONMENT.md"),
                      (SOURCE / "phoenix.sh", WORK / "harness/phoenix.sh"),
                      (ROOT / "tools/quick-smoke.sh", WORK / "harness/quick-smoke.sh")):
        copy(src, dest, files)
    (WORK / "harness/browser-image-id").write_text(browser + "\n")
    files["harness/browser-image-id"] = one_shot.digest(WORK / "harness/browser-image-id")
    for path in (WORK / ".scaffold").rglob("*"):
        if path.is_file():
            files[str(path.relative_to(WORK))] = one_shot.digest(path)
    record = {"stack": "phoenix", "condition": "v2-expert-diagnostic",
              "fixture_sha256": source["sha256"],
              "base_fixture_sha256": source["base_fixture_sha256"],
              "prompt_sha256": one_shot.digest(WORK / "PROMPT.md"),
              "measurement_sha256": one_shot.digest(WORK / "MEASUREMENT.md"),
              "toolchain_image_id": image_id(), "browser_image_id": browser,
              "files": dict(sorted(files.items()))}
    (WORK / "FIXTURE.json").write_text(json.dumps(record, indent=2) + "\n")
    for part in ("realworld_spec", "security", "harness", ".scaffold"):
        one_shot.readonly(WORK / part)
    for name in ("PROMPT.md", "MEASUREMENT.md", "ENVIRONMENT.md", "EXPERIMENT.md", "FIXTURE.json"):
        path = WORK / name
        path.chmod(path.stat().st_mode & ~0o222)
    if not os.access(WORK / "harness/phoenix.sh", os.X_OK):
        raise SystemExit("Phoenix harness wrapper is not executable")
    before = one_shot.digest(WORK / "mix.lock")
    subprocess.run([*container(WORK), "mix", "deps.get"], check=True, timeout=900)
    if one_shot.digest(WORK / "mix.lock") != before:
        raise SystemExit("mix deps.get changed frozen scaffold lock; update before freeze")
    subprocess.run([*container(WORK), "mix", "compile", "--warnings-as-errors"], check=True,
                   timeout=900)
    make_home()
    CONTROL.mkdir(parents=True, mode=0o700)
    (CONTROL / "token").write_text(secrets.token_hex(32) + "\n")
    (CONTROL / "token").chmod(0o600)
    verify_workspace(WORK)
    print(f"ready: {WORK} (fixture {source['sha256']})")


def health(port):
    with urllib.request.urlopen(f"http://127.0.0.1:{port}/health", timeout=2) as response:
        return json.load(response)


def wait_health(port, expected, seconds=90):
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        try:
            if health(port) == expected:
                return
        except Exception:
            pass
        time.sleep(.2)
    raise SystemExit(f"Phoenix scaffold did not serve {expected} on port {port}")


def preflight():
    subprocess.run(["docker", "build", "-q", "-f", str(ROOT / "stacks/phoenix-expert/Dockerfile.toolchain"),
                    "-t", IMAGE, str(ROOT / "stacks/phoenix-expert")], check=True, timeout=900)
    browser = one_shot.preflight()
    port = one_shot.preflight_port()
    host = ROOT / "tools/one_shot_host/db.sh"
    (ROOT / ".work").mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="phoenix-expert-preflight-", dir=ROOT / ".work") as folder:
        work = Path(folder)
        shutil.copytree(SCAFFOLD, work, dirs_exist_ok=True, ignore=shutil.ignore_patterns(*GENERATED))
        before = one_shot.digest(work / "mix.lock")
        subprocess.run([*container(work, port), "mix", "deps.get"], check=True, timeout=900)
        if one_shot.digest(work / "mix.lock") != before:
            candidate = ROOT / ".work/phoenix-expert-preflight-mix.lock"
            shutil.copy2(work / "mix.lock", candidate)
            raise SystemExit(f"Dependency lock changed during preflight; inspect {candidate}")
        for command in (("mix", "format", "--check-formatted"),
                        ("mix", "compile", "--warnings-as-errors")):
            subprocess.run([*container(work, port), *command], check=True, timeout=900)
        image = "agentmvc-phoenix-expert-scaffold-smoke:preflight"
        dev = "agentmvc-phoenix-expert-scaffold-dev"
        app = "agentmvc-phoenix-expert-scaffold-prod"
        subprocess.run([str(host), "start", str(port)], check=True, timeout=120)
        try:
            subprocess.run([*container(work, port), "mix", "test"], check=True, timeout=900)
            db_name = f"agentmvc-one-shot-db-{port}"
            probe = subprocess.check_output(["docker", "exec", db_name, "psql", "-U", "agentmvc",
                                             "-d", "agentmvc", "-tAc",
                                             "SELECT to_regclass('public.oban_jobs') IS NULL"],
                                            text=True, timeout=30).strip()
            if probe != "t":
                raise SystemExit("Test migration touched development database")
            subprocess.run([*container(work, port), "mix", "ecto.migrate"], check=True, timeout=300)
            subprocess.run([*container(work, port, detached=True, name=dev), "mix", "phx.server"], check=True,
                           stdout=subprocess.DEVNULL, timeout=60)
            wait_health(port, {"status": "ok"})
            source = work / "lib/conduit_web/controllers/health_controller.ex"
            original = source.read_text()
            source.write_text(original.replace('status: "ok"', 'status: "ready"'))
            start = time.monotonic()
            wait_health(port, {"status": "ready"})
            watch_seconds = round(time.monotonic() - start, 2)
            print(f"watched health edit visible in {watch_seconds:.2f}s")
            source.write_text(original)
        finally:
            subprocess.run(["docker", "rm", "-f", dev], capture_output=True, timeout=30)
            subprocess.run([str(host), "stop", str(port)], capture_output=True, timeout=60)
        subprocess.run(["docker", "build", "-q", "-t", image, str(work)], check=True, timeout=2400)
        subprocess.run([str(host), "start", str(port)], check=True, timeout=120)
        try:
            subprocess.run(["docker", "run", "-d", "--name", app, "--network", "host",
                            "-e", f"DATABASE_URL={db_url(port)}",
                            "-e", "SECRET_KEY_BASE=" + "0123456789abcdef" * 8,
                            "-e", f"PORT={port}", image], check=True, stdout=subprocess.DEVNULL, timeout=60)
            wait_health(port, {"status": "ok"})
            smoke = (
                'Bcrypt.verify_pass("probe", Bcrypt.hash_pwd_salt("probe")) || raise "bcrypt NIF failed"; '
                'signer = Joken.Signer.create("HS256", "preflight-secret"); '
                '{:ok, jwt, _} = Joken.encode_and_sign(%{"title" => "漢字 ✅"}, signer); '
                '{:ok, %{"title" => "漢字 ✅"}} = Joken.verify_and_validate(%{}, jwt, signer); '
                'Jason.decode!(Jason.encode!(%{"title" => "漢字 ✅"})) == %{"title" => "漢字 ✅"} '
                '|| raise "Unicode JSON failed"; '
                'System.get_env("LANG") == "C.UTF-8" || raise "runtime locale is not UTF-8"; '
                'IO.puts("release crypto and Unicode ok")'
            )
            checked = subprocess.run(["docker", "exec", app, "bin/conduit", "eval", smoke],
                                     check=True, timeout=120, capture_output=True, text=True)
            if "release crypto and Unicode ok" not in checked.stdout or "latin1" in checked.stderr.lower():
                raise SystemExit(f"Release smoke output unexpected: {checked.stdout} {checked.stderr}")
        finally:
            subprocess.run(["docker", "rm", "-f", app], capture_output=True, timeout=30)
            subprocess.run([str(host), "stop", str(port)], capture_output=True, timeout=60)
            subprocess.run(["docker", "image", "rm", image], capture_output=True, timeout=30)
    return {"browser_image_id": browser, "watch_seconds": watch_seconds,
            "test_database_isolated": True, "release_crypto_unicode_verified": True}


def main():
    command = sys.argv[1] if len(sys.argv) > 1 else ""
    if command == "preflight" and len(sys.argv) == 2:
        source, tick = snapshot(), time.monotonic()
        error = None
        checks = {}
        try:
            checks = preflight()
            if snapshot() != source:
                raise RuntimeError("Fixture source changed during preflight")
        except (Exception, SystemExit) as exc:
            error = str(exc)
        try:
            toolchain = image_id()
        except Exception:
            toolchain = None
        try:
            browser = one_shot.image_id()
        except Exception:
            browser = None
        result = {"passed": error is None, "mode": "full",
                  "fixture_sha256": source["sha256"],
                  "prompt_sha256": source["files"]["one-shot-v2-expert/PROMPT.md"],
                  "toolchain_image_id": toolchain,
                  "browser_image_id": browser,
                  "seconds": round(time.monotonic() - tick, 1), "checks": checks}
        if error:
            result["error"] = error
        RESULTS.mkdir(parents=True, exist_ok=True)
        path = RESULTS / "preflight.json"
        if path.exists():
            attempt = 1
            while path.with_name(f"preflight-attempt{attempt}.json").exists():
                attempt += 1
            path.rename(path.with_name(f"preflight-attempt{attempt}.json"))
        path.write_text(json.dumps(result, indent=2) + "\n")
        print(json.dumps(result, indent=2))
        if error:
            raise SystemExit(1)
    elif command == "freeze" and len(sys.argv) == 2:
        MANIFEST.write_text(json.dumps(snapshot(), indent=2) + "\n")
        print(json.loads(MANIFEST.read_text())["sha256"])
    elif command == "verify-source" and len(sys.argv) == 2:
        current = snapshot()
        if not MANIFEST.is_file() or json.loads(MANIFEST.read_text()) != current:
            raise SystemExit("Phoenix expert fixture differs from frozen manifest")
        print(current["sha256"])
    elif command == "prepare" and len(sys.argv) == 2:
        prepare()
    elif command == "verify" and len(sys.argv) == 3:
        verify_workspace(Path(sys.argv[2]))
    else:
        raise SystemExit(__doc__)


if __name__ == "__main__":
    main()
