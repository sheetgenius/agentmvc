"""Narrow localhost bridge for fixed one-shot checks and the Phoenix toolchain.

The agent receives a stack token, never a Docker socket or a host shell. Every
Docker bind mount is the agent's own workdir or a frozen acceptance fixture.
"""
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

ROOT = one_shot.ROOT
HOST = ROOT / "tools/one_shot_host"
PORTS = {"rails": 4101, "phoenix": 4102, "loco": 4103}
CHECKS = {"all", "api", "live", "security", "production", "db-start", "db-stop"}
PHOENIX_IMAGE = "elixir:1.18.4-otp-27"
LOCKS = {stack: threading.Lock() for stack in PORTS}


def run(args, *, env=None, timeout=3600):
    result = subprocess.run(args, cwd=ROOT, env=env, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, text=True, timeout=timeout)
    return result.returncode, result.stdout


def container_args(work, port):
    return ["docker", "run", "--network", "host", "--user", f"{os.getuid()}:{os.getgid()}",
            "--mount", f"type=bind,source={work},target=/work/app", "-w", "/work/app/conduit",
            "-e", "HOME=/work/app", "-e", "MIX_HOME=/work/app/.mix",
            "-e", "HEX_HOME=/work/app/.hex", "-e", "MIX_ARCHIVES=/work/app/.mix/archives",
            "-e", f"PORT={port}",
            "-e", f"DATABASE_URL=postgres://agentmvc:agentmvc@host.docker.internal:{port + 50000}/agentmvc",
            "-e", "PGHOST=host.docker.internal", "-e", f"PGPORT={port + 50000}",
            PHOENIX_IMAGE]


def verify(work):
    with contextlib.redirect_stdout(io.StringIO()):
        one_shot.verify(work)


def dispatch(stack, action, port, argv):
    work = one_shot.WORK / stack
    if port != PORTS[stack] or not work.is_dir():
        return 2, "Wrong workspace or port.\n"
    if action not in CHECKS and not (stack == "phoenix" and action.startswith("phoenix-")):
        return 2, "Unsupported action.\n"
    if action != "db-stop" and action != "phoenix-stop":
        verify(work)
    if action in CHECKS:
        if argv:
            return 2, "Check actions take no extra arguments.\n"
        script, args = ("db.sh", [action.removeprefix("db-"), str(port)]) if action.startswith("db-") else \
                       (f"check-{action}.sh", [str(port)])
        code, output = run([str(HOST / script), *args], env={**os.environ, "ONE_SHOT_WORKDIR": str(work)})
    elif action == "phoenix-run":
        if not argv or len(argv) > 100 or any(not isinstance(arg, str) or len(arg) > 10000 for arg in argv):
            return 2, "A container command is required.\n"
        code, output = run([*container_args(work, port)[:2], "--rm", *container_args(work, port)[2:-1],
                            PHOENIX_IMAGE, *argv])
    elif action == "phoenix-start":
        command = argv or ["mix", "phx.server"]
        if len(command) > 100 or any(not isinstance(arg, str) or len(arg) > 10000 for arg in command):
            return 2, "Invalid container command.\n"
        name = "agentmvc-one-shot-phoenix-dev"
        run(["docker", "rm", "-f", name], timeout=30)
        code, output = run([*container_args(work, port)[:2], "-d", "--name", name,
                            *container_args(work, port)[2:-1], PHOENIX_IMAGE, *command], timeout=120)
    elif action == "phoenix-logs":
        if argv:
            return 2, "No arguments expected.\n"
        code, output = run(["docker", "logs", "--tail", "200", "agentmvc-one-shot-phoenix-dev"], timeout=30)
    elif action == "phoenix-stop":
        if argv:
            return 2, "No arguments expected.\n"
        code, output = run(["docker", "rm", "-f", "agentmvc-one-shot-phoenix-dev"], timeout=30)
    else:
        return 2, "Unsupported action.\n"
    if action != "db-stop" and action != "phoenix-stop":
        verify(work)
    return code, output


class Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path != "/run":
            self.send_error(404)
            return
        token = self.headers.get("Authorization", "").removeprefix("Bearer ")
        stack = self.server.tokens.get(token)
        if not stack:
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
            with LOCKS[stack]:
                try:
                    code, output = dispatch(stack, action, port, argv)
                except Exception as error:
                    code, output = 1, f"Coordinator check failed: {error}\n"
            self.server.record(stack, action, code, output)
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
    def __init__(self, address, tokens, logdir):
        super().__init__(address, Handler)
        self.tokens = {token: stack for stack, token in tokens.items()}
        self.logdir = logdir
        self.logdir.mkdir(parents=True, exist_ok=True)
        self.sequence = 0
        self.guard = threading.Lock()

    def record(self, stack, action, code, output):
        with self.guard:
            self.sequence += 1
            number = self.sequence
        path = self.logdir / f"{number:04d}-{stack}-{action}.log"
        path.write_text(output)
        with (self.logdir / "requests.jsonl").open("a") as file:
            file.write(json.dumps({"time": datetime.now(timezone.utc).isoformat(),
                                   "stack": stack, "action": action, "exit": code,
                                   "log": path.name}) + "\n")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("tokens", type=Path, help="private JSON map of stack to bearer token")
    parser.add_argument("--logdir", type=Path, default=one_shot.BROKER_LOG)
    parser.add_argument("--port", type=int, default=int(os.environ.get("ONE_SHOT_BROKER_PORT", "49671")))
    args = parser.parse_args()
    tokens = json.loads(args.tokens.read_text())
    if set(tokens) != set(PORTS) or len(set(tokens.values())) != len(PORTS):
        raise SystemExit("Expected one distinct token per stack")
    server = Server(("127.0.0.1", args.port), tokens, args.logdir)
    print(f"one-shot check broker listening on 127.0.0.1:{args.port}", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
