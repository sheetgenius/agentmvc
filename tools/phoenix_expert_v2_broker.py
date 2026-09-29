"""Token-scoped Phoenix toolchain and fixed-check bridge; no agent Docker socket."""
import argparse
import contextlib
import io
import json
import os
import signal
import subprocess
import threading
import uuid
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import one_shot
import phoenix_expert_v2 as setup

ROOT = one_shot.ROOT
HOST = ROOT / "tools/one_shot_host"
PORT = setup.PORT
DEV = "agentmvc-phoenix-expert-v2-dev"
CHECKS = {"all", "api", "live", "security", "production", "db-start", "db-stop"}
ACTIONS = CHECKS | {"phx-run", "phx-build", "phx-test", "phx-start", "phx-logs", "phx-stop"}
GUARD = threading.Lock()


def run(args, *, env=None, timeout=600, cleanup=None):
    try:
        result = subprocess.run(args, cwd=ROOT, env=env, stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT, text=True, timeout=timeout)
        return result.returncode, result.stdout
    except subprocess.TimeoutExpired as error:
        if cleanup:
            subprocess.run(["docker", "rm", "-f", cleanup], capture_output=True, timeout=30)
        output = "".join(item.decode(errors="replace") if isinstance(item, bytes) else item
                         for item in (error.stdout, error.stderr) if item)
        return 124, output + f"\nCoordinator command timed out after {timeout}s.\n"


def verify(work):
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            setup.verify_workspace(work)
        source = setup.snapshot()
    except SystemExit as error:
        raise ValueError(f"Frozen input verification failed: {error}") from error
    record = json.loads((work / "FIXTURE.json").read_text())
    if source["sha256"] != record["fixture_sha256"]:
        raise ValueError("Host fixture source differs from prepared workspace")
    if setup.image_id() != record["toolchain_image_id"]:
        raise ValueError("Toolchain image differs from frozen workspace")


def container_ids():
    code, output = run(["docker", "container", "ls", "-aq", "--no-trunc"], timeout=30)
    if code:
        raise RuntimeError(f"Cannot inventory Docker containers: {output}")
    return set(output.split())


def cleanup_new_mounts(work, before):
    removed, failures = [], []
    for identity in container_ids() - before:
        code, output = run(["docker", "inspect", identity, "--format", "{{json .Mounts}}"], timeout=20)
        if code:
            failures.append(f"inspect {identity[:12]}: {output.strip()}")
            continue
        mounts = json.loads(output) or []
        if any(mount.get("Source") == str(work) or
               mount.get("Source", "").startswith(str(work) + os.sep) for mount in mounts):
            code, output = run(["docker", "rm", "-f", identity], timeout=30)
            (removed if code == 0 else failures).append(identity[:12] if code == 0 else output.strip())
    return f"removed {removed}; cleanup failures {failures}"


def cleanup_production(pid, work):
    name = f"agentmvc-one-shot-{work.name}-{pid}"
    for command in (["docker", "rm", "-f", f"{name}-app", f"{name}-db"],
                    ["docker", "network", "rm", f"{name}-net"],
                    ["docker", "image", "rm", f"{name}:latest"]):
        run(command, timeout=30)


def run_check(args, *, env, timeout, work, action):
    before = container_ids()
    proc = subprocess.Popen(args, cwd=ROOT, env=env, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, text=True, start_new_session=True)
    try:
        output, _ = proc.communicate(timeout=timeout)
        return proc.returncode, output
    except subprocess.TimeoutExpired:
        try:
            os.killpg(proc.pid, signal.SIGTERM)
        except ProcessLookupError:
            pass
        try:
            output, _ = proc.communicate(timeout=5)
        except subprocess.TimeoutExpired:
            try:
                os.killpg(proc.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            output, _ = proc.communicate(timeout=5)
        report = cleanup_new_mounts(work, before)
        if action == "production":
            cleanup_production(proc.pid, work)
        if action == "db-start":
            run([str(HOST / "db.sh"), "stop", str(PORT)], timeout=60)
        return 124, output + f"\nCheck exceeded {timeout}s; process group stopped; {report}.\n"


def container(work, *, detached=False, name=None):
    args = setup.container(work, detached=detached, name=name)
    overlays = []
    for part in ("realworld_spec", "security", "harness", ".scaffold", "PROMPT.md",
                 "ENVIRONMENT.md", "MEASUREMENT.md", "EXPERIMENT.md", "FIXTURE.json"):
        overlays += ["--mount", f"type=bind,source={work / part},target=/work/app/{part},readonly"]
    return [*args[:-1], *overlays, args[-1]]


def dispatch(action, port, argv):
    work = setup.WORK
    if port != PORT or not work.is_dir():
        return 2, "Wrong workspace or port.\n"
    if action not in ACTIONS or len(argv) > 100 or any(
            not isinstance(arg, str) or len(arg) > 10_000 for arg in argv):
        return 2, "Unsupported action or invalid arguments.\n"
    if action not in {"db-stop", "phx-stop", "phx-logs"}:
        verify(work)
    if action in CHECKS:
        if argv:
            return 2, "Check actions take no arguments.\n"
        script, args = ("db.sh", [action.removeprefix("db-"), str(port)]) if action.startswith("db-") else \
                       (f"check-{action}.sh", [str(port)])
        code, output = run_check([str(HOST / script), *args],
                                 env={**os.environ, "ONE_SHOT_WORKDIR": str(work)},
                                 timeout=3600 if action == "production" else 1200,
                                 work=work, action=action)
    elif action in {"phx-run", "phx-build", "phx-test"}:
        if action == "phx-run" and not argv:
            return 2, "Container command required.\n"
        if action != "phx-run" and argv:
            return 2, "No extra arguments expected.\n"
        command = argv if action == "phx-run" else \
                  ["mix", "release", "--overwrite"] if action == "phx-build" else ["mix", "test"]
        if action == "phx-run" and ("phx.server" in command or "--no-halt" in command):
            return 2, "Use phoenix.sh start for a persistent server.\n"
        name = f"agentmvc-phoenix-expert-v2-cmd-{uuid.uuid4().hex[:10]}"
        args = [*container(work, name=name)]
        if action == "phx-build":
            args = [*args[:-1], "-e", "MIX_ENV=prod", args[-1]]
        code, output = run([*args, *command], timeout=1800 if action == "phx-build" else 600,
                           cleanup=name)
    elif action == "phx-start":
        if argv:
            return 2, "Start takes no arguments.\n"
        run(["docker", "rm", "-f", DEV], timeout=30)
        code, output = run([*container(work, detached=True, name=DEV), "mix", "phx.server"],
                           timeout=120, cleanup=DEV)
    elif action == "phx-logs":
        if argv:
            return 2, "Logs takes no arguments.\n"
        code, output = run(["docker", "logs", "--tail", "200", DEV], timeout=30)
    elif action == "phx-stop":
        if argv:
            return 2, "Stop takes no arguments.\n"
        code, output = run(["docker", "rm", "-f", DEV], timeout=30)
    else:
        return 2, "Unsupported action.\n"
    if action not in {"db-stop", "phx-stop", "phx-logs"}:
        verify(work)
    return code, output


class Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path != "/run":
            self.send_error(404)
            return
        if self.headers.get("Authorization", "").removeprefix("Bearer ") != self.server.token:
            self.send_error(403)
            return
        try:
            size = int(self.headers.get("Content-Length", "0"))
            if size <= 0 or size > 1_048_576:
                raise ValueError("Invalid request length")
            data = json.loads(self.rfile.read(size))
            action, port, argv = data["action"], data["port"], data["argv"]
            if not isinstance(action, str) or not isinstance(port, int) or not isinstance(argv, list):
                raise ValueError("Invalid request")
            with GUARD:
                try:
                    code, output = dispatch(action, port, argv)
                except (Exception, SystemExit) as error:
                    code, output = 1, f"Coordinator check failed: {error}\n"
            self.server.record(action, code, output)
            body = output.encode(errors="replace")
            self.send_response(200 if code == 0 else 409)
        except (KeyError, ValueError, json.JSONDecodeError) as error:
            body = f"Invalid request: {error}\n".encode()
            self.send_response(400)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        pass


class Server(ThreadingHTTPServer):
    def __init__(self, address, token, logdir):
        super().__init__(address, Handler)
        self.token, self.logdir = token, logdir
        logdir.mkdir(parents=True, exist_ok=True)
        self.sequence = 0

    def record(self, action, code, output):
        self.sequence += 1
        path = self.logdir / f"{self.sequence:04d}-phoenix-{action}.log"
        path.write_text(output)
        with (self.logdir / "requests.jsonl").open("a") as file:
            file.write(json.dumps({"time": datetime.now(timezone.utc).isoformat(),
                                   "action": action, "exit": code, "log": path.name}) + "\n")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("token_file", type=Path)
    parser.add_argument("--port", type=int, default=49678)
    args = parser.parse_args()
    server = Server(("127.0.0.1", args.port), args.token_file.read_text().strip(),
                    ROOT / ".work/one-shot-v2-phoenix-expert-broker")
    print(f"Phoenix expert broker listening on 127.0.0.1:{args.port}", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
