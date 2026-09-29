"""Freeze, preflight and prepare the isolated Rails expert v2 diagnostic.

Usage: python3 tools/rails_expert_v2.py preflight|freeze|verify-source|prepare|verify WORKDIR
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
SOURCE = ROOT / "one-shot-v2-rails-expert"
SHARED = ROOT / "one-shot-v2-expert"
SCAFFOLD = ROOT / "stacks/rails-expert/scaffold"
MANIFEST = SOURCE / "fixture-manifest.json"
WORK = ROOT / ".work/one-shot-v2-rails-expert/rails"
HOME = ROOT / ".work/one-shot-v2-rails-expert-home/rails"
CONTROL = ROOT / ".work/one-shot-v2-rails-expert-control"
LOG = ROOT / ".work/one-shot-v2-rails-expert-agent-log"
RESULTS = ROOT / "results/one-shot-v2-rails-expert"
IMAGE = "agentmvc-rails-expert-v2-toolchain:preflight"
PORT = 4109
VOLUME = "agentmvc-rails-expert-v2-bundle"
GENERATED = {"vendor", "tmp", "log", "coverage", "__pycache__", ".bundle"}
TOOL_SOURCES = ("rails_expert_v2.py", "rails_expert_v2_broker.py",
                "rails_expert_v2_isolation.py")


def source_files():
    paths = [one_shot.MANIFEST, SHARED / "PROMPT.md", SHARED / "MEASUREMENT.md",
             SOURCE / "README.md", SOURCE / "ENVIRONMENT.md", SOURCE / "rails.sh",
             ROOT / "tools/quick-smoke.sh", ROOT / "tools/measure.py",
             ROOT / "tools/scrub.py", ROOT / "tools/one_shot_publish.py",
             ROOT / "tools/one_shot_live_bench.py",
             ROOT / "stacks/rails-expert/stack.json",
             ROOT / "stacks/rails-expert/PROVENANCE.md",
             ROOT / "stacks/rails-expert/Dockerfile.toolchain",
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
    for name in ("harness/rails.sh", "harness/check-all.sh",
                 "harness/check-production.sh"):
        if not os.access(work / name, os.X_OK):
            raise SystemExit(f"Frozen check is not executable: {name}")


def db_url(port, database="agentmvc"):
    return f"postgres://agentmvc:agentmvc@host.docker.internal:{port + 50000}/{database}"


def container(work, port=PORT, *, detached=False, name=None, test=False):
    args = ["docker", "run", "-d" if detached else "--rm"]
    if name:
        args += ["--name", name]
    args += ["--network", "host", "--mount",
             f"type=volume,source={VOLUME},target=/usr/local/bundle", "--mount",
             f"type=bind,source={work},target=/work/app", "-w", "/work/app",
             "-e", f"PORT={port}",
             "-e", f"DATABASE_URL={db_url(port, 'agentmvc_test' if test else 'agentmvc')}",
             "-e", f"RAILS_ENV={'test' if test else 'development'}",
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
        raise SystemExit("Rails expert fixture differs from frozen manifest")
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
        elif name.startswith("one-shot/harness/") and name != "one-shot/harness/rails.sh":
            dest = WORK / "harness" / name.removeprefix("one-shot/harness/")
        else:
            continue
        copy(src, dest, files)
    for src, dest in ((SHARED / "PROMPT.md", WORK / "PROMPT.md"),
                      (SHARED / "MEASUREMENT.md", WORK / "MEASUREMENT.md"),
                      (SOURCE / "README.md", WORK / "EXPERIMENT.md"),
                      (SOURCE / "ENVIRONMENT.md", WORK / "ENVIRONMENT.md"),
                      (SOURCE / "rails.sh", WORK / "harness/rails.sh"),
                      (ROOT / "tools/quick-smoke.sh", WORK / "harness/quick-smoke.sh")):
        copy(src, dest, files)
    (WORK / "harness/browser-image-id").write_text(browser + "\n")
    files["harness/browser-image-id"] = one_shot.digest(WORK / "harness/browser-image-id")
    for path in (WORK / ".scaffold").rglob("*"):
        if path.is_file():
            files[str(path.relative_to(WORK))] = one_shot.digest(path)
    record = {"stack": "rails", "condition": "v2-expert-diagnostic",
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
    if not os.access(WORK / "harness/rails.sh", os.X_OK):
        raise SystemExit("Rails harness wrapper is not executable")
    before = one_shot.digest(WORK / "Gemfile.lock")
    subprocess.run([*container(WORK), "bundle", "check"], check=True, timeout=120)
    subprocess.run([*container(WORK), "bundle", "exec", "rails", "zeitwerk:check"],
                   check=True, timeout=180)
    if one_shot.digest(WORK / "Gemfile.lock") != before:
        raise SystemExit("bundle changed frozen scaffold lock; update before freeze")
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
    raise SystemExit(f"Rails scaffold did not serve {expected} on port {port}")


def install_probe(work):
    """Add generic capability probes only to the disposable preflight copy."""
    (work / "lib/socket_probe.rb").write_text('''require "faye/websocket"

class SocketProbe
  def self.call(env)
    return [400, { "content-type" => "text/plain" }, ["upgrade required"]] unless Faye::WebSocket.websocket?(env)

    socket = Faye::WebSocket.new(env)
    socket.on(:message) { |event| socket.send(event.data) }
    socket.rack_response
  end
end
''')
    (work / "app/jobs").mkdir(exist_ok=True)
    (work / "app/jobs/probe_job.rb").write_text('''require "fileutils"

class ProbeJob < ActiveJob::Base
  def perform
    FileUtils.mkdir_p(Rails.root.join("tmp"))
    File.write(Rails.root.join("tmp/job-preflight"), "done")
  end
end
''')
    route = work / "config/routes.rb"
    route.write_text('require_relative "../lib/socket_probe"\n' +
                     route.read_text().replace('Rails.application.routes.draw do',
                                               'Rails.application.routes.draw do\n  mount SocketProbe, at: "/socket-probe"'))


def websocket_probe(port):
    program = '''const WebSocket = require("ws");
const ws = new WebSocket(`ws://127.0.0.1:${process.argv[1]}/socket-probe`);
const timeout = setTimeout(() => process.exit(2), 7000);
ws.on("open", () => ws.send("socket-preflight"));
ws.on("message", data => {
  if (data.toString() !== "socket-preflight") process.exit(3);
  clearTimeout(timeout);
  ws.close();
  process.exit(0);
});
ws.on("error", error => { console.error(error.message); process.exit(4); });'''
    subprocess.run(["node", "-e", program, str(port)], cwd=ROOT / "frontend",
                   check=True, timeout=15)


def wait_file(path, seconds):
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        if path.is_file() and path.read_text() == "done":
            return
        time.sleep(.2)
    raise SystemExit(f"Background job did not create {path}")


def wait_container_file(container_name, path, seconds):
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        if subprocess.run(["docker", "exec", container_name, "test", "-f", path],
                          capture_output=True, timeout=5).returncode == 0:
            return
        time.sleep(.2)
    raise SystemExit(f"Production background job did not create {path}")


def preflight():
    subprocess.run(["docker", "build", "-q", "-f", str(ROOT / "stacks/rails-expert/Dockerfile.toolchain"),
                    "-t", IMAGE, str(ROOT / "stacks/rails-expert")], check=True, timeout=900)
    browser = one_shot.preflight()
    port = one_shot.preflight_port()
    host = ROOT / "tools/one_shot_host/db.sh"
    (ROOT / ".work").mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="rails-expert-preflight-", dir=ROOT / ".work") as folder:
        work = Path(folder)
        shutil.copytree(SCAFFOLD, work, dirs_exist_ok=True, ignore=shutil.ignore_patterns(*GENERATED))
        before = one_shot.digest(work / "Gemfile.lock")
        for command in (("bundle", "check"), ("bundle", "exec", "rails", "zeitwerk:check"),
                        ("bundle", "exec", "rubocop")):
            subprocess.run([*container(work, port), *command], check=True, timeout=600)
        if one_shot.digest(work / "Gemfile.lock") != before:
            raise SystemExit("Bundler changed frozen scaffold lock")
        image = "agentmvc-rails-expert-scaffold-smoke:preflight"
        dev = "agentmvc-rails-expert-scaffold-dev"
        app = "agentmvc-rails-expert-scaffold-prod"
        install_probe(work)
        subprocess.run([str(host), "start", str(port)], check=True, timeout=120)
        try:
            subprocess.run([*container(work, port, test=True), "bundle", "exec", "rails", "db:prepare"],
                           check=True, timeout=300)
            subprocess.run([*container(work, port, test=True), "bundle", "exec", "rails", "test"],
                           check=True, timeout=300)
            db_name = f"agentmvc-one-shot-db-{port}"
            untouched = subprocess.check_output(["docker", "exec", db_name, "psql", "-U", "agentmvc",
                                                 "-d", "agentmvc", "-tAc",
                                                 "SELECT to_regclass('public.good_jobs') IS NULL"],
                                                text=True, timeout=30).strip()
            if untouched != "t":
                raise SystemExit("Test migration touched development database")
            subprocess.run([*container(work, port), "bundle", "exec", "rails", "db:prepare"],
                           check=True, timeout=300)
            subprocess.run([*container(work, port, detached=True, name=dev),
                            "bundle", "exec", "rails", "server", "-b", "0.0.0.0"],
                           check=True, stdout=subprocess.DEVNULL, timeout=60)
            wait_health(port, {"status": "ok"})
            websocket_probe(port)
            subprocess.run([*container(work, port), "bundle", "exec", "rails", "runner",
                            "ProbeJob.perform_later"], check=True, timeout=120)
            wait_file(work / "tmp/job-preflight", seconds=30)
            source = work / "app/controllers/health_controller.rb"
            original = source.read_text()
            source.write_text(original.replace('status: "ok"', 'status: "ready"'))
            start = time.monotonic()
            wait_health(port, {"status": "ready"})
            watch_seconds = round(time.monotonic() - start, 2)
            source.write_text(original)
            wait_health(port, {"status": "ok"})
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
            websocket_probe(port)
            smoke = ('raise "bcrypt" unless BCrypt::Password.create("probe") == "probe"; '
                     't = JWT.encode({"text" => "漢字 ✅"}, "preflight-secret", "HS256"); '
                     'raise "jwt" unless JWT.decode(t, "preflight-secret", true, algorithm: "HS256").first["text"] == "漢字 ✅"; '
                     'puts "release crypto and Unicode ok"')
            checked = subprocess.run(["docker", "exec", app, "bundle", "exec", "rails", "runner", smoke],
                                     check=True, timeout=120, capture_output=True, text=True)
            if "release crypto and Unicode ok" not in checked.stdout:
                raise SystemExit(f"Release smoke output unexpected: {checked.stdout} {checked.stderr}")
            subprocess.run(["docker", "exec", app, "bundle", "exec", "rails", "runner",
                            "ProbeJob.perform_later"], check=True, timeout=120)
            wait_container_file(app, "/rails/tmp/job-preflight", seconds=30)
        finally:
            subprocess.run(["docker", "rm", "-f", app], capture_output=True, timeout=30)
            subprocess.run([str(host), "stop", str(port)], capture_output=True, timeout=60)
            subprocess.run(["docker", "image", "rm", image], capture_output=True, timeout=30)
    return {"browser_image_id": browser, "watch_seconds": watch_seconds,
            "test_database_isolated": True, "good_job_dev_and_production": True,
            "raw_websocket_dev_and_production": True, "release_crypto_unicode_verified": True}


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
            raise SystemExit("Rails expert fixture differs from frozen manifest")
        print(current["sha256"])
    elif command == "prepare" and len(sys.argv) == 2:
        prepare()
    elif command == "verify" and len(sys.argv) == 3:
        verify_workspace(Path(sys.argv[2]))
    else:
        raise SystemExit(__doc__)


if __name__ == "__main__":
    main()
