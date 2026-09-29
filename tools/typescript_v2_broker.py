"""Token-scoped TypeScript toolchain and acceptance bridge; no Docker socket in agents."""
import argparse
import contextlib
import io
import json
import os
import subprocess
import threading
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import one_shot
import typescript_v2

ROOT = one_shot.ROOT
HOST = ROOT / "tools/one_shot_host"
PORT = 4106
NAME = "agentmvc-typescript-v2-pilot-dev"
CHECKS = {"all", "api", "live", "security", "production", "db-start", "db-stop"}
ACTIONS = CHECKS | {"ts-run", "ts-build", "ts-test", "ts-start", "ts-logs", "ts-stop"}
GUARD = threading.Lock()


def run(args, *, env=None, timeout=7200):
    result = subprocess.run(args, cwd=ROOT, env=env, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, text=True, timeout=timeout)
    return result.returncode, result.stdout


def verify(work):
    with contextlib.redirect_stdout(io.StringIO()):
        one_shot.verify(work)
    expected = json.loads((work / "FIXTURE.json").read_text())["toolchain_image_id"]
    if typescript_v2.image_id() != expected:
        raise ValueError("Toolchain image differs from frozen workspace")


def container(work, *, detached=False):
    args = ["docker", "run", "-d" if detached else "--rm"]
    if detached:
        args += ["--name", NAME]
    args += ["--network", "host",
             "--mount", f"type=volume,source={typescript_v2.VOLUME},target=/root/.npm",
             "--mount", f"type=bind,source={work},target=/work/app"]
    for name in ("realworld_spec", "security", "harness", ".scaffold", "PROMPT.md",
                 "ENVIRONMENT.md", "MEASUREMENT.md", "EXPERIMENT.md", "FIXTURE.json"):
        args += ["--mount", f"type=bind,source={work / name},target=/work/app/{name},readonly"]
    args += ["-w", "/work/app", "-e", "NODE_ENV=development", "-e", f"PORT={PORT}",
             "-e", f"DATABASE_URL=postgres://agentmvc:agentmvc@127.0.0.1:{PORT + 50000}/agentmvc",
             "-e", "SECRET_KEY_BASE=typescript-development-secret-0123456789abcdef",
             typescript_v2.IMAGE]
    return args


def dispatch(action, port, argv):
    work = typescript_v2.WORK
    if port != PORT or not work.is_dir():
        return 2, "Wrong workspace or port.\n"
    if action not in ACTIONS or len(argv) > 100 or any(
            not isinstance(arg, str) or len(arg) > 10000 for arg in argv):
        return 2, "Unsupported action or invalid arguments.\n"
    if action not in {"db-stop", "ts-stop", "ts-logs"}:
        verify(work)
    if action in CHECKS:
        if argv:
            return 2, "Check actions take no arguments.\n"
        script, args = ("db.sh", [action.removeprefix("db-"), str(port)]) if action.startswith("db-") else \
                       (f"check-{action}.sh", [str(port)])
        code, output = run([str(HOST / script), *args],
                           env={**os.environ, "ONE_SHOT_WORKDIR": str(work)})
    elif action in {"ts-run", "ts-build", "ts-test"}:
        if action == "ts-run" and not argv:
            return 2, "Container command required.\n"
        if action != "ts-run" and argv:
            return 2, "No extra arguments expected.\n"
        command = argv if action == "ts-run" else \
                  ["npm", "run", "build"] if action == "ts-build" else ["npm", "test"]
        code, output = run([*container(work), *command])
    elif action == "ts-start":
        if argv:
            return 2, "Start takes no arguments.\n"
        run(["docker", "rm", "-f", NAME], timeout=30)
        code, output = run([*container(work, detached=True), "npm", "run", "dev", "--", "--poll"],
                           timeout=120)
    elif action == "ts-logs":
        if argv:
            return 2, "Logs takes no arguments.\n"
        code, output = run(["docker", "logs", "--tail", "200", NAME], timeout=30)
    elif action == "ts-stop":
        if argv:
            return 2, "Stop takes no arguments.\n"
        code, output = run(["docker", "rm", "-f", NAME], timeout=30)
    else:
        return 2, "Unsupported action.\n"
    if action not in {"db-stop", "ts-stop", "ts-logs"}:
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
        self.sequence += 1
        path = self.logdir / f"{self.sequence:04d}-typescript-{action}.log"
        path.write_text(output)
        with (self.logdir / "requests.jsonl").open("a") as file:
            file.write(json.dumps({"time": datetime.now(timezone.utc).isoformat(),
                                   "action": action, "exit": code, "log": path.name}) + "\n")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("token_file", type=Path)
    parser.add_argument("--port", type=int, default=49676)
    args = parser.parse_args()
    token = args.token_file.read_text().strip()
    server = Server(("127.0.0.1", args.port), token,
                    ROOT / ".work/one-shot-v2-typescript-broker")
    print(f"TypeScript broker listening on 127.0.0.1:{args.port}", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
