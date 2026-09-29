"""Token-scoped IHP check and Nix bridge. No agent receives the host Docker socket."""
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

import ihp_candidate
import one_shot

ROOT = one_shot.ROOT
HOST = ROOT / "tools/one_shot_host"
IMAGE = "nixos/nix:2.31.2@sha256:29fc5fe207f159ceb0143c25c19c774062fee02ce5eda118f3067547b3054894"
PORT = 4104
VOLUME = "agentmvc-ihp-nix-store"
CHECKS = {"all", "api", "live", "security", "production", "db-start", "db-stop"}
ACTIONS = CHECKS | {"ihp-run", "ihp-build", "ihp-start", "ihp-logs", "ihp-stop"}
GUARD = threading.Lock()
DEV_SCRIPT = '''
    set -eu
    server=$(nix --extra-experimental-features 'nix-command flakes' --accept-flake-config build --no-link --print-out-paths .#unoptimized-prod-server)
    migrate=$(nix --extra-experimental-features 'nix-command flakes' --accept-flake-config build --no-link --print-out-paths .#migrate)
    export IHP_ENV=Production IHP_MIGRATION_DIR=/work/app/Application/Migration/ IHP_SESSION_SECRET="$SECRET_KEY_BASE"
    "$migrate/bin/migrate"
    if [ -x "$server/bin/RunJobs" ]; then "$server/bin/RunJobs" & fi
    exec "$server/bin/RunProdServer"
'''


def run(args, *, env=None, timeout=7200):
    result = subprocess.run(args, cwd=ROOT, env=env, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, text=True, timeout=timeout)
    return result.returncode, result.stdout


def volume_for(work):
    run_number = work.parent.name.removeprefix("one-shot-ihp-")
    if run_number not in ("1", "2", "3") or work.name != "ihp":
        raise ValueError("Expected a numbered IHP workdir")
    return f"agentmvc-ihp-nix-run{run_number}"


def workspace_mounts(work):
    args = ["--mount", f"type=volume,source={volume_for(work)},target=/nix",
            "--mount", f"type=bind,source={work},target=/work/app"]
    for name in ("realworld_spec", "security", "harness", ".scaffold",
                 "PROMPT.md", "ENVIRONMENT.md", "MEASUREMENT.md", "EXPERIMENT.md", "FIXTURE.json"):
        args += ["--mount", f"type=bind,source={work / name},target=/work/app/{name},readonly"]
    return args


def container_args(work):
    return ["docker", "run", "--network", "host", *workspace_mounts(work),
            "-w", "/work/app", "-e", "HOME=/tmp", "-e", f"PORT={PORT}",
            "-e", f"DATABASE_URL=postgres://agentmvc:agentmvc@host.docker.internal:{PORT + 50000}/agentmvc",
            "-e", "SECRET_KEY_BASE=agentmvc-ihp-development-secret-0123456789abcdef",
            IMAGE]


def nix(*args):
    return ["nix", "--extra-experimental-features", "nix-command flakes",
            "--accept-flake-config", *args]


def verify(work):
    with contextlib.redirect_stdout(io.StringIO()):
        one_shot.verify(work)


def dispatch(run_number, action, port, argv):
    work = ihp_candidate.workspace(run_number)
    if port != PORT or not work.is_dir():
        return 2, "Wrong workspace or port.\n"
    if action not in ACTIONS:
        return 2, "Unsupported action.\n"
    if len(argv) > 100 or any(not isinstance(a, str) or len(a) > 10000 for a in argv):
        return 2, "Invalid arguments.\n"
    if action not in {"db-stop", "ihp-stop", "ihp-logs"}:
        verify(work)
    if action in CHECKS:
        if argv:
            return 2, "Check actions take no arguments.\n"
        if action.startswith("db-"):
            command = [str(HOST / "db.sh"), action.removeprefix("db-"), str(port)]
        elif action == "production":
            command = [str(ROOT / "tools/ihp_candidate_host/check-production.sh"), str(port)]
        else:
            command = [str(HOST / f"check-{action}.sh"), str(port)]
        code, output = run(command, env={**os.environ, "ONE_SHOT_WORKDIR": str(work)})
    elif action in {"ihp-run", "ihp-build"}:
        if action == "ihp-build" and argv:
            return 2, "Build takes no arguments.\n"
        if action == "ihp-run" and not argv:
            return 2, "Command required.\n"
        command = nix("build", "--no-link", ".#unoptimized-prod-server") if action == "ihp-build" else \
                  nix(*argv[1:]) if argv[0] == "nix" else \
                  nix("develop", "--override-input", "devenv-root",
                      "file+file:///work/app/.devenv/root", "--command", *argv)
        (work / ".devenv").mkdir(exist_ok=True)
        (work / ".devenv/root").write_text("/work/app")
        code, output = run([*container_args(work)[:2], "--rm", *container_args(work)[2:-1],
                            IMAGE, *command])
    elif action == "ihp-start":
        if argv:
            return 2, "Start takes no arguments.\n"
        name = f"agentmvc-one-shot-ihp-{run_number}-dev"
        run(["docker", "rm", "-f", name], timeout=30)
        args = container_args(work)
        code, output = run([*args[:2], "-d", "--name", name, *args[2:-1], IMAGE,
                            "sh", "-ec", DEV_SCRIPT], timeout=120)
    elif action in {"ihp-logs", "ihp-stop"}:
        if argv:
            return 2, "No arguments expected.\n"
        name = f"agentmvc-one-shot-ihp-{run_number}-dev"
        command = ["docker", "logs", "--tail", "200", name] if action == "ihp-logs" else \
                  ["docker", "rm", "-f", name]
        code, output = run(command, timeout=30)
    else:
        return 2, "Unsupported action.\n"
    if action not in {"db-stop", "ihp-stop", "ihp-logs"}:
        verify(work)
    return code, output


class Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path != "/run":
            self.send_error(404)
            return
        token = self.headers.get("Authorization", "").removeprefix("Bearer ")
        if token != self.server.token:
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
                    code, output = dispatch(self.server.run_number, action, port, argv)
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
    def __init__(self, address, token, run_number, logdir):
        super().__init__(address, Handler)
        self.token, self.run_number, self.logdir = token, run_number, logdir
        self.logdir.mkdir(parents=True, exist_ok=True)
        self.sequence = 0

    def record(self, action, code, output):
        self.sequence += 1
        path = self.logdir / f"{self.sequence:04d}-ihp-{action}.log"
        path.write_text(output)
        with (self.logdir / "requests.jsonl").open("a") as file:
            file.write(json.dumps({"time": datetime.now(timezone.utc).isoformat(),
                                   "action": action, "exit": code, "log": path.name}) + "\n")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("run", choices=("1", "2", "3"))
    parser.add_argument("token_file", type=Path)
    parser.add_argument("--port", type=int, default=49674)
    args = parser.parse_args()
    ihp_candidate.snapshot()
    token = args.token_file.read_text().strip()
    server = Server(("127.0.0.1", args.port), token, args.run,
                    ROOT / ".work" / f"one-shot-ihp-{args.run}-broker")
    print(f"IHP broker listening on 127.0.0.1:{args.port}", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
