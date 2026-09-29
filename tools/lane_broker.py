"""Session-scoped toolchain and gate service; the agent never receives Docker access.

Usage: python3 tools/lane_broker.py --session /absolute/session.json [--port 49680]
The session descriptor is trusted coordinator input outside the agent workspace.
Only ``run`` accepts agent-supplied argv, executed after the fixed container image.
"""
import argparse
import contextlib
import fcntl
import hashlib
import json
import os
import re
import signal
import subprocess
import threading
import uuid
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HOST = ROOT / "tools/lane_host"
POSTGRES = "postgres:17-alpine@sha256:742f40ea20b9ff2ff31db5458d127452988a2164df9e17441e191f3b72252193"
ACTIONS = {"run", "start", "stop", "logs", "build", "test", "lint", "db-start", "db-stop",
           "api", "security", "live", "all", "development", "production", "benchmark", "security-scan"}


def stamp():
    return datetime.now(timezone.utc).isoformat()


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


@contextlib.contextmanager
def resources():
    """Both lane brokers and independent checks serialize Docker work."""
    lock = ROOT / ".work/lane-docker.lock"
    lock.parent.mkdir(parents=True, exist_ok=True)
    with lock.open("a") as stream:
        fcntl.flock(stream.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(stream.fileno(), fcntl.LOCK_UN)


def command(argv, *, env=None, timeout=600):
    """Terminate the whole local process group on timeout and retain its output."""
    proc = subprocess.Popen([str(arg) for arg in argv], cwd=ROOT, env=env,
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                            text=True, start_new_session=True)
    try:
        output, _ = proc.communicate(timeout=timeout)
        return proc.returncode, output
    except subprocess.TimeoutExpired:
        for sig, seconds in ((signal.SIGTERM, 5), (signal.SIGKILL, 5)):
            try:
                os.killpg(proc.pid, sig)
            except ProcessLookupError:
                pass
            try:
                output, _ = proc.communicate(timeout=seconds)
                return 124, output + f"\nCoordinator timeout after {timeout}s.\n"
            except subprocess.TimeoutExpired:
                continue
        return 124, f"Coordinator timeout after {timeout}s; process group was killed.\n"


def checked(argv, **kwargs):
    code, output = command(argv, **kwargs)
    if code:
        raise RuntimeError(f"Command failed ({code}): {output[-6000:]}")
    return output.strip()


def safe_path(base, relative):
    """Do not follow an agent-created symlink during host reads, mounts or writes."""
    relative = Path(relative)
    if relative.is_absolute() or not relative.parts or ".." in relative.parts:
        raise ValueError(f"Invalid relative path: {relative}")
    current = base
    for part in relative.parts:
        current = current / part
        if current.is_symlink():
            raise ValueError(f"Symlink is not permitted here: {relative}")
    return current


class Session:
    def __init__(self, path):
        self.path = Path(path)
        if not self.path.is_absolute():
            raise ValueError("--session must be an absolute path")
        self.data = json.loads(self.path.read_text())
        self.id = self.data["id"]
        if not re.fullmatch(r"[a-z0-9][a-z0-9-]{0,55}", self.id):
            raise ValueError("Session id must be a short lowercase Docker-safe name")
        self.work = Path(self.data["work"])
        if not self.work.is_absolute() or self.work.is_symlink() or not self.work.is_dir():
            raise ValueError("Session work must be an existing absolute non-symlink directory")
        if self.work.resolve() == ROOT or ROOT.is_relative_to(self.work.resolve()):
            raise ValueError("A session cannot mount the repository or its parent")
        self.control, self.logs = Path(self.data["control"]), Path(self.data["logs"])
        for path in (self.control, self.logs, self.path):
            if not path.is_absolute() or path.resolve().is_relative_to(self.work.resolve()):
                raise ValueError("Session control, logs and descriptor must be outside the workspace")
        self.control.mkdir(parents=True, exist_ok=True)
        self.logs.mkdir(parents=True, exist_ok=True)
        self.port, self.number = self.data["port"], self.data["number"]
        if (type(self.port) is not int or not 1024 <= self.port <= 15535 or
                type(self.number) is not int or not 1 <= self.number <= 8):
            raise ValueError("Invalid session port or step number")
        self.image = self.data["image"]
        if not isinstance(self.image, str) or not self.image or self.image.startswith("-"):
            raise ValueError("Invalid toolchain image")
        self.prefix = f"agentmvc-lane-{self.id}"
        self.dev, self.db = self.prefix + "-dev", self.prefix + "-db"
        self.production_image = self.prefix + ":current"
        self.frozen = self.data.get("frozen", [])
        if "FIXTURE.json" not in self.frozen:
            self.frozen = [*self.frozen, "FIXTURE.json"]
        self.env = {**os.environ, "ONE_SHOT_WORKDIR": str(self.work),
                    "LANE_NUMBER": str(self.number), "LANE_ID": self.id}
        self.fixture_digest = digest(safe_path(self.work, "FIXTURE.json"))
        if self.fixture_digest != self.data.get("fixture_file_sha256"):
            raise ValueError("Fixture record differs from trusted session descriptor")

    def argv(self, name):
        args = self.data.get("commands", {}).get(name, [])
        if not isinstance(args, list) or any(not isinstance(arg, str) for arg in args):
            raise ValueError(f"commands.{name} must be an argv vector")
        return args

    def verify(self, *, image=True):
        fixture_path = safe_path(self.work, "FIXTURE.json")
        if digest(fixture_path) != self.fixture_digest:
            raise ValueError("FIXTURE.json changed after the session service started")
        fixture = json.loads(fixture_path.read_text())
        files = fixture["files"]
        for name, expected in files.items():
            path = safe_path(self.work, name)
            if not path.is_file() or digest(path) != expected:
                raise ValueError(f"Frozen input changed: {name}")
        for name in self.frozen:
            path = safe_path(self.work, name)
            if not path.exists():
                raise ValueError(f"Missing frozen input: {name}")
            if path.is_dir():
                for nested in path.rglob("*"):
                    rel = str(nested.relative_to(self.work))
                    safe_path(self.work, rel)
                    if nested.is_file() and rel not in files:
                        raise ValueError(f"Added file in frozen input: {rel}")
        expected = fixture.get("toolchain_image_id") or self.data.get("image_id")
        if image and expected:
            actual = checked(["docker", "image", "inspect", "--format", "{{.Id}}", self.image], timeout=30)
            if actual != expected:
                raise ValueError("Toolchain image differs from the frozen fixture")

    def container(self, *, name=None, detached=False, test=False):
        args = ["docker", "run", "-d" if detached else "--rm", "--init"]
        if name:
            args += ["--name", name]
        args += ["--label", f"agentmvc.lane={self.id}", "--network", "host",
                 "--mount", f"type=bind,source={self.work},target=/work/app", "-w", "/work/app"]
        for volume in self.data.get("volumes", []):
            args += ["--mount", f"type=volume,source={volume['name']},target={volume['target']}"]
        for part in self.frozen:
            path = safe_path(self.work, part)
            args += ["--mount", f"type=bind,source={path},target=/work/app/{part},readonly"]
        env = dict(self.data.get("env", {}))
        database = "agentmvc_test" if test else "agentmvc"
        env.update(PORT=str(self.port),
                   DATABASE_URL=f"postgres://agentmvc:agentmvc@host.docker.internal:{self.port + 50000}/{database}",
                   SECRET_KEY_BASE="0123456789abcdef" * 8)
        for key, value in env.items():
            args += ["-e", f"{key}={value}"]
        return [*args, self.image]

    def run(self, argv, *, test=False, timeout=900):
        name = self.prefix + "-cmd-" + uuid.uuid4().hex[:8]
        try:
            return command([*self.container(name=name, test=test), *argv], timeout=timeout)
        finally:
            command(["docker", "rm", "-f", name], timeout=30)

    def tool(self, name, *, test=False):
        argv = self.argv(name)
        return self.run(argv, test=test) if argv else (0, f"No {name} command configured.\n")

    def stop(self):
        return command(["docker", "rm", "-f", self.dev], timeout=30)

    def start(self):
        self.stop()
        argv = self.argv("start")
        if not argv:
            return 2, "No start command configured.\n"
        code, prepared = self.tool("prepare")
        if code:
            return code, prepared
        code, output = command([*self.container(name=self.dev, detached=True), *argv], timeout=120)
        return code, prepared + output

    def database(self, start):
        if not start:
            return command(["docker", "rm", "-f", self.db], timeout=30)
        code, output = command(["docker", "run", "-d", "--name", self.db,
                                "--label", f"agentmvc.lane={self.id}",
                                "-p", f"127.0.0.1:{self.port + 50000}:5432",
                                "-e", "POSTGRES_USER=agentmvc", "-e", "POSTGRES_PASSWORD=agentmvc",
                                "-e", "POSTGRES_DB=agentmvc", POSTGRES], timeout=120)
        if code:
            return code, output
        import time
        for _ in range(120):
            code, _ = command(["docker", "exec", self.db, "pg_isready", "-U", "agentmvc",
                                "-d", "agentmvc"], timeout=10)
            if not code:
                code, extra = command(["docker", "exec", self.db, "createdb", "-U", "agentmvc",
                                        "agentmvc_test"], timeout=30)
                return code, output + extra + f"Development database ready on port {self.port + 50000}.\n"
            time.sleep(.5)
        self.database(False)
        return 124, output + "PostgreSQL readiness timed out.\n"

    def build(self):
        return command(["docker", "build", "-t", self.production_image, str(self.work)], timeout=1800)

    def gate(self, name):
        if name not in {"api", "all", "security", "live"}:
            raise ValueError("Invalid fixed gate")
        if name == "live" and self.number < 8:
            return 2, "Live checks begin at step 8.\n"
        try:
            return command(["bash", str(HOST / f"check-{name}.sh"), str(self.port)],
                           env=self.env, timeout=600)
        finally:
            code, identities = command(["docker", "ps", "-aq", "--filter",
                                        f"label=agentmvc.lane.check={self.id}"], timeout=30)
            if not code and identities.strip():
                command(["docker", "rm", "-f", *identities.split()], timeout=30)

    def output_dir(self, relative):
        path = safe_path(self.work, relative)
        path.mkdir(parents=True, exist_ok=True)
        return path


def dispatch(session, action, port, argv):
    if action not in ACTIONS or port != session.port:
        return 2, "Unsupported action or wrong port.\n"
    if (not isinstance(argv, list) or len(argv) > 100 or
            any(not isinstance(arg, str) or len(arg) > 10000 or "\0" in arg for arg in argv)):
        return 2, "Invalid container arguments.\n"
    if action != "run" and argv:
        return 2, "This action takes no arguments.\n"
    if action == "run" and not argv:
        return 2, "A container command is required.\n"
    if action not in {"stop", "logs", "db-stop"}:
        session.verify()
    try:
        if action == "run":
            result = session.run(argv)
        elif action == "start":
            result = session.start()
        elif action == "stop":
            result = session.stop()
        elif action == "logs":
            result = command(["docker", "logs", "--tail", "200", session.dev], timeout=30)
        elif action == "build":
            result = session.build()
        elif action in {"test", "lint"}:
            result = session.tool(action, test=action == "test")
        elif action.startswith("db-"):
            result = session.database(action == "db-start")
        elif action in {"api", "all", "security", "live"}:
            result = session.gate(action)
        else:
            import lane_check
            result = lane_check.perform(session, action)
    finally:
        if action not in {"stop", "logs", "db-stop"}:
            session.verify()
    return result


class Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path != "/run":
            self.send_error(404)
            return
        if self.headers.get("Authorization", "") != "Bearer " + self.server.token:
            self.send_error(403)
            return
        try:
            size = int(self.headers.get("Content-Length", "0"))
            if not 0 < size <= 1048576:
                raise ValueError("Invalid request size")
            data = json.loads(self.rfile.read(size))
            action, port, argv = data["action"], data["port"], data.get("argv", [])
            if not isinstance(action, str) or type(port) is not int:
                raise ValueError("Invalid action or port")
            with self.server.guard, resources():
                try:
                    code, output = dispatch(self.server.session, action, port, argv)
                except Exception as error:
                    code, output = 1, f"Coordinator action failed: {type(error).__name__}: {error}\n"
                self.server.record(action, code, output)
            status = 200 if code == 0 else 409
        except (ValueError, KeyError, TypeError) as error:
            status, output = 400, f"Invalid request: {error}\n"
        body = output.encode(errors="replace")
        self.send_response(status)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        try:
            self.wfile.write(body)
        except (BrokenPipeError, ConnectionResetError):
            pass

    def log_message(self, format, *args):
        pass


class Server(ThreadingHTTPServer):
    daemon_threads = True

    def __init__(self, session, port):
        super().__init__(("127.0.0.1", port), Handler)
        self.session, self.guard = session, threading.Lock()
        self.token = (session.control / "token").read_text().strip()
        if len(self.token) < 32:
            raise ValueError("Missing or short broker token")
        self.directory = session.logs / "broker"
        self.directory.mkdir(parents=True, exist_ok=True)

    def record(self, action, code, output):
        label = action if action in ACTIONS else "invalid-action"
        name = f"{stamp().replace(':', '-')}-{uuid.uuid4().hex[:8]}-{label}.log"
        (self.directory / name).write_text(output)
        with (self.directory / "requests.jsonl").open("a") as stream:
            stream.write(json.dumps({"time": stamp(), "action": action, "exit": code,
                                     "log": name, "session": self.session.id}) + "\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--session", required=True, type=Path)
    parser.add_argument("--port", type=int)
    args = parser.parse_args()
    session = Session(args.session)
    with resources():
        session.verify()
    port = args.port or session.data.get("broker_port", 49680)
    server = Server(session, port)
    print(f"Lane broker {session.id} listening on 127.0.0.1:{port}", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
