"""Token-scoped, bounded Docker bridge for the TypeScript expert condition.

The agent gets no Docker socket. Persistent server and worker commands have
separate detached lifecycles; arbitrary `ts-run` containers have a hard limit.
"""
import argparse
import contextlib
import io
import json
import os
import secrets
import signal
import subprocess
import threading
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import one_shot
import typescript_expert

ROOT = one_shot.ROOT
HOST = ROOT / "tools/one_shot_host"
PORT = 4107
DEV_NAME = "agentmvc-typescript-v2-expert-dev"
WORKER_NAME = "agentmvc-typescript-v2-expert-worker"
CHECKS = {"all", "api", "live", "security", "production", "db-start", "db-stop"}
LIFECYCLE = {"ts-start", "ts-logs", "ts-stop", "ts-worker-start", "ts-worker-logs",
             "ts-worker-stop"}
ACTIONS = CHECKS | LIFECYCLE | {"ts-run", "ts-build", "ts-test"}
GUARD = threading.Lock()
RECORD_GUARD = threading.Lock()


def run(args, *, env=None, timeout=180):
    result = subprocess.run(args, cwd=ROOT, env=env, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, text=True, timeout=timeout)
    return result.returncode, result.stdout


def cleanup_production_check(pid, work):
    name = f"agentmvc-one-shot-{work.name}-{pid}"
    actions = (["docker", "rm", "-f", f"{name}-app", f"{name}-db"],
               ["docker", "network", "rm", f"{name}-net"],
               ["docker", "image", "rm", f"{name}:latest"])
    results = [run(action, timeout=30) for action in actions]
    # Missing resources are expected if the shell's EXIT trap already cleaned.
    return "; ".join(f"{action[1]} exit {code}" for action, (code, _) in zip(actions, results))


def container_ids():
    code, output = run(["docker", "container", "ls", "-aq", "--no-trunc"], timeout=30)
    if code:
        raise RuntimeError(f"Could not inventory Docker containers: {output}")
    return set(output.split())


def cleanup_new_mounts(work, before):
    removed, failed = [], []
    for identity in container_ids() - before:
        code, output = run(["docker", "inspect", identity, "--format", "{{json .Mounts}}"], timeout=20)
        if code:
            failed.append(f"inspect {identity[:12]}: {output.strip()}")
            continue
        mounts = json.loads(output) or []
        if any(mount.get("Source") == str(work) or
               mount.get("Source", "").startswith(str(work) + os.sep) for mount in mounts):
            code, output = run(["docker", "rm", "-f", identity], timeout=30)
            (removed if code == 0 else failed).append(identity[:12] if code == 0 else f"remove {identity[:12]}: {output.strip()}")
    return f"removed gate containers {removed}; cleanup failures {failed}"


def run_check(args, *, env, timeout, work, production=False):
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
        if production:
            report += "; " + cleanup_production_check(proc.pid, work)
        return 124, output + f"\nCheck exceeded {timeout}s; process group stopped; {report}.\n"


def verify(work):
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            typescript_expert.verify_work(work)
    except SystemExit as error:
        raise ValueError(f"Frozen input verification failed: {error}") from error
    frozen = json.loads((work / "FIXTURE.json").read_text())
    if typescript_expert.image_id() != frozen["toolchain_image_id"]:
        raise ValueError("Toolchain image differs from frozen workspace")


def container(work, *, name=None, detached=False):
    args = ["docker", "run", "--init", "-d" if detached else "--rm"]
    if name:
        args += ["--name", name]
    args += ["--network", "host",
             "--mount", f"type=volume,source={typescript_expert.VOLUME},target=/root/.npm",
             "--mount", f"type=bind,source={work},target=/work/app"]
    for part in ("realworld_spec", "security", "harness", ".scaffold", "PROMPT.md",
                 "ENVIRONMENT.md", "MEASUREMENT.md", "EXPERIMENT.md", "FIXTURE.json"):
        args += ["--mount", f"type=bind,source={work / part},target=/work/app/{part},readonly"]
    args += ["-w", "/work/app", "-e", "NODE_ENV=development", "-e", f"PORT={PORT}",
             "-e", f"DATABASE_URL=postgres://agentmvc:agentmvc@127.0.0.1:{PORT + 50000}/agentmvc",
             "-e", "SECRET_KEY_BASE=typescript-expert-development-secret-0123456789abcdef",
             typescript_expert.IMAGE]
    return args


def command_container(work, command, timeout):
    name = "agentmvc-typescript-v2-expert-cmd-" + secrets.token_hex(6)
    try:
        return run([*container(work, name=name), *command], timeout=timeout)
    except subprocess.TimeoutExpired:
        code, detail = run(["docker", "rm", "-f", name], timeout=30)
        if code:
            return 124, f"Container command exceeded {timeout}s; cleanup of {name} failed: {detail}\n"
        return 124, f"Container command exceeded {timeout}s; removed {name}.\n"


def start_container(work, name, command):
    run(["docker", "rm", "-f", name], timeout=30)
    try:
        return run([*container(work, name=name, detached=True), *command], timeout=60)
    except subprocess.TimeoutExpired:
        run(["docker", "rm", "-f", name], timeout=30)
        return 124, f"Starting {name} timed out; container removed.\n"


def dispatch(action, port, argv):
    work = typescript_expert.WORK
    if port != PORT or not work.is_dir():
        return 2, "Wrong workspace or port.\n"
    if action not in ACTIONS or len(argv) > 100 or any(
            not isinstance(arg, str) or len(arg) > 10000 for arg in argv):
        return 2, "Unsupported action or invalid arguments.\n"
    if action not in {"db-stop", "ts-stop", "ts-logs", "ts-worker-stop", "ts-worker-logs"}:
        verify(work)
    if action in CHECKS:
        if argv:
            return 2, "Check actions take no arguments.\n"
        script, args = ("db.sh", [action.removeprefix("db-"), str(port)]) if action.startswith("db-") else \
                       (f"check-{action}.sh", [str(port)])
        code, output = run_check([str(HOST / script), *args],
                                 env={**os.environ, "ONE_SHOT_WORKDIR": str(work)},
                                 timeout=3600 if action == "production" else 1200,
                                 work=work,
                                 production=action == "production")
    elif action in {"ts-run", "ts-build", "ts-test"}:
        if action == "ts-run" and not argv:
            return 2, "Container command required.\n"
        if action != "ts-run" and argv:
            return 2, "No extra arguments expected.\n"
        command = argv if action == "ts-run" else \
                  ["npm", "run", "build"] if action == "ts-build" else ["npm", "test"]
        if action == "ts-run" and command[:2] == ["node", "ace"] and \
                len(command) > 2 and command[2] in {"queue:work", "serve"}:
            return 2, "Use ts.sh worker-start or start for persistent processes.\n"
        code, output = command_container(work, command, 180 if action == "ts-run" else 600)
    elif action in {"ts-start", "ts-worker-start"}:
        if argv:
            return 2, "Start takes no arguments.\n"
        name, command = ((DEV_NAME, ["npm", "run", "dev", "--", "--poll"])
                         if action == "ts-start" else (WORKER_NAME, ["node", "ace", "queue:work"]))
        code, output = start_container(work, name, command)
    elif action in {"ts-logs", "ts-worker-logs"}:
        if argv:
            return 2, "Logs takes no arguments.\n"
        name = DEV_NAME if action == "ts-logs" else WORKER_NAME
        code, output = run(["docker", "logs", "--tail", "200", name], timeout=30)
    elif action in {"ts-stop", "ts-worker-stop"}:
        if argv:
            return 2, "Stop takes no arguments.\n"
        name = DEV_NAME if action == "ts-stop" else WORKER_NAME
        code, output = run(["docker", "rm", "-f", name], timeout=30)
    else:
        return 2, "Unsupported action.\n"
    if action not in {"db-stop", "ts-stop", "ts-logs", "ts-worker-stop", "ts-worker-logs"}:
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
            if size <= 0 or size > 1048576:
                raise ValueError("Invalid request length")
            data = json.loads(self.rfile.read(size))
            action, port, argv = data["action"], data["port"], data["argv"]
            if not isinstance(action, str) or not isinstance(port, int) or not isinstance(argv, list):
                raise ValueError("Invalid request")
            with GUARD:
                try:
                    code, output = dispatch(action, port, argv)
                except Exception as error:
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
        with RECORD_GUARD:
            self.sequence += 1
            path = self.logdir / f"{self.sequence:04d}-typescript-{action}.log"
            path.write_text(output)
            with (self.logdir / "requests.jsonl").open("a") as file:
                file.write(json.dumps({"time": datetime.now(timezone.utc).isoformat(),
                                       "action": action, "exit": code, "log": path.name}) + "\n")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("token_file", type=Path)
    parser.add_argument("--port", type=int, default=49677)
    args = parser.parse_args()
    token = args.token_file.read_text().strip()
    server = Server(("127.0.0.1", args.port), token,
                    ROOT / ".work/one-shot-v2-typescript-expert-broker")
    print(f"TypeScript expert broker listening on 127.0.0.1:{args.port}", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
