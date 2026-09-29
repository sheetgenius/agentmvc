"""Independently rerun one-shot development or production acceptance gates."""
import contextlib
import json
import os
import socket
import subprocess
import sys
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

import one_shot
import scrub

ROOT = one_shot.ROOT
HOST = ROOT / "tools/one_shot_host"


def command(args, *, cwd=ROOT, env=None, timeout=3600):
    proc = subprocess.run(args, cwd=cwd, env=env, capture_output=True, text=True, timeout=timeout)
    return proc.returncode, proc.stdout + proc.stderr


def ready(port, proc, seconds=180):
    stop = time.monotonic() + seconds
    while time.monotonic() < stop:
        if proc is not None and proc.poll() is not None:
            return False
        try:
            with urllib.request.urlopen(f"http://127.0.0.1:{port}/api/tags", timeout=2) as response:
                if response.status == 200:
                    return True
        except Exception:
            time.sleep(.2)
    return False


def tool_env(work, stack, port, database):
    env = {**os.environ, "DATABASE_URL": database, "PORT": str(port),
           "SECRET_KEY_BASE": "0123456789abcdef" * 8, "TMPDIR": str(work / "tmp"),
           "CARGO_HOME": str(work / ".cargo"), "RUSTUP_HOME": str(Path.home() / ".rustup"),
           "CARGO_TARGET_DIR": str(work / "conduit/target")}
    if stack == "rails":
        gem_home = work / ("vendor/bundle" if (work / "vendor/bundle/gems").is_dir() else "vendor/gems")
        env.update(BUNDLE_USER_HOME=str(work / ".bundle"), GEM_HOME=str(gem_home),
                   GEM_PATH=f"{gem_home}:{Path.home() / '.rbenv/versions/3.3.2/lib/ruby/gems/3.3.0'}",
                   XDG_CACHE_HOME=str(work / "tmp/cache"), RUBOCOP_CACHE_ROOT=str(work / "tmp/rubocop-cache"),
                   RUBOCOP_TARGET_RUBY_VERSION="3.3", RAILS_ENV="development", RAILS_LOG_LEVEL="warn")
    return env


def phoenix_args(work, port, database):
    return ["docker", "run", "--rm", "--network", "host", "--user", f"{os.getuid()}:{os.getgid()}",
            "--mount", f"type=bind,source={work},target=/work/app", "-w", "/work/app/conduit",
            "-e", "HOME=/work/app", "-e", "MIX_HOME=/work/app/.mix", "-e", "HEX_HOME=/work/app/.hex",
            "-e", f"DATABASE_URL={database}", "-e", f"PORT={port}",
            "-e", "SECRET_KEY_BASE=" + "0123456789abcdef" * 8,
            "-e", "PGHOST=host.docker.internal", "-e", f"PGPORT={port + 50000}",
            "elixir:1.18.4-otp-27"]


def development(stack, work, port, output):
    work.joinpath("tmp").mkdir(exist_ok=True)
    env_host = {**os.environ, "ONE_SHOT_WORKDIR": str(work)}
    code, db_output = command([str(HOST / "db.sh"), "start", str(port)], env=env_host, timeout=120)
    output.append(db_output)
    if code:
        return code
    database = db_output.strip().split("DATABASE_URL=", 1)[-1]
    if stack == "phoenix":
        database = database.replace("127.0.0.1", "host.docker.internal")
    env = tool_env(work, stack, port, database)
    server = None
    server_log = (work / "tmp" / f"independent-server-{port}.log").open("w")
    name = f"agentmvc-one-shot-independent-{stack}-dev"
    try:
        if stack == "rails":
            code, result = command(["bundle", "exec", "rails", "db:prepare"], cwd=work, env=env, timeout=180)
            output.append(result)
            if code:
                return code
            server = subprocess.Popen(["bundle", "exec", "rails", "server", "-b", "127.0.0.1", "-p", str(port)],
                                      cwd=work, env=env, stdout=server_log, stderr=subprocess.STDOUT,
                                      text=True)
        elif stack == "phoenix":
            args = phoenix_args(work, port, database)
            code, result = command([*args, "mix", "ecto.migrate"], timeout=300)
            output.append(result)
            if code:
                return code
            code, result = command(["docker", "run", "-d", "--name", name, *args[2:-1], args[-1],
                                    "mix", "phx.server"], timeout=120)
            output.append(result)
            if code:
                return code
        else:
            server = subprocess.Popen(["cargo", "loco", "start", "--server-and-worker"], cwd=work / "conduit", env=env,
                                      stdout=server_log, stderr=subprocess.STDOUT, text=True)
        if not ready(port, server):
            if stack == "phoenix":
                output.append(command(["docker", "logs", name], timeout=30)[1])
            elif server and server.poll() is not None:
                server_log.flush()
                output.append((work / "tmp" / f"independent-server-{port}.log").read_text())
            return 1
        code, result = command([str(HOST / "check-all.sh"), str(port)], env=env_host, timeout=900)
        output.append(result)
        if code:
            return code
        if stack == "rails":
            checks = [["bin/rubocop"]]
            directory = work
        elif stack == "phoenix":
            checks = [[*phoenix_args(work, port, database), "mix", "format", "--check-formatted"],
                      [*phoenix_args(work, port, database), "mix", "compile", "--warnings-as-errors"]]
            directory = ROOT
        else:
            checks = [["cargo", "fmt", "--all", "--", "--check"],
                      ["cargo", "clippy", "--all-targets", "--", "-D", "warnings"]]
            directory = work / "conduit"
        for check in checks:
            code, result = command(check, cwd=directory, env=env, timeout=600)
            output.append(result)
            if code:
                return code
        return 0
    finally:
        if server is not None:
            server.terminate()
            try:
                server.wait(timeout=10)
            except subprocess.TimeoutExpired:
                server.kill()
                server.wait()
        server_log.close()
        if stack == "phoenix":
            command(["docker", "rm", "-f", name], timeout=30)
        output.append(command([str(HOST / "db.sh"), "stop", str(port)], env=env_host, timeout=60)[1])


def main():
    if len(sys.argv) != 3 or sys.argv[1] not in one_shot.STACKS or sys.argv[2] not in ("development", "production"):
        raise SystemExit("usage: python3 tools/one_shot_independent.py STACK development|production")
    stack, gate = sys.argv[1:]
    work = one_shot.WORK / stack
    one_shot.verify(work)
    port = (4200 if gate == "development" else 4300) + one_shot.STACKS.index(stack) + 1
    output = []
    started = datetime.now(timezone.utc).isoformat()
    tick = time.monotonic()
    try:
        if gate == "development":
            code = development(stack, work, port, output)
        else:
            code, result = command([str(HOST / "check-production.sh"), str(port)],
                                   env={**os.environ, "ONE_SHOT_WORKDIR": str(work)}, timeout=3600)
            output.append(result)
        one_shot.verify(work)
    except Exception as error:
        code = 1
        output.append(f"Independent gate error: {error}\n")
    dest = one_shot.RESULTS / stack
    dest.mkdir(parents=True, exist_ok=True)
    raw = one_shot.INDEPENDENT / stack
    raw.mkdir(parents=True, exist_ok=True)
    if (dest / f"{gate}.json").exists():
        attempt = 1
        while (dest / f"{gate}-attempt{attempt}.json").exists():
            attempt += 1
        for suffix in ("json", "log"):
            previous = dest / f"{gate}.{suffix}"
            if previous.exists():
                previous.rename(dest / f"{gate}-attempt{attempt}.{suffix}")
        previous_raw = raw / f"{gate}.log"
        if previous_raw.exists():
            previous_raw.rename(raw / f"{gate}-attempt{attempt}.log")
    (raw / f"{gate}.log").write_text("\n".join(output))
    cleaner = scrub.Scrubber(work)
    cleaned = cleaner.text("\n".join(output))
    if cleaner.leaks(cleaned):
        raise SystemExit("Independent gate log still contains private paths")
    (dest / f"{gate}.log").write_text(cleaned)
    record = {"stack": stack, "gate": gate, "port": port, "started": started,
              "finished": datetime.now(timezone.utc).isoformat(), "seconds": round(time.monotonic() - tick, 1),
              "exit": code, "fixture_sha256": json.loads((work / "FIXTURE.json").read_text())["fixture_sha256"]}
    (dest / f"{gate}.json").write_text(json.dumps(record, indent=2) + "\n")
    print(json.dumps(record, indent=2))
    raise SystemExit(code)


if __name__ == "__main__":
    main()
