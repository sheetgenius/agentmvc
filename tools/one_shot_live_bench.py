"""Run repeated direct WebSocket measurements on the one-shot production images."""
import argparse
import json
import os
import statistics
import subprocess
import sys
import threading
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

import one_shot

ROOT = one_shot.ROOT
OUT = one_shot.RESULTS / "runtime/live"
STACKS = ("rails", "phoenix", "loco")
LIMITS = ("--cpus=2", "--memory=1g")
HOST_PORT = 18108


def run(*args, check=True):
    result = subprocess.run(args, capture_output=True, text=True)
    if check and result.returncode:
        raise RuntimeError(f"{' '.join(args)}\n{result.stdout}\n{result.stderr}")
    return result.stdout.strip()


def memory_mb(text):
    value, unit = text.strip().split("/")[0].strip()[:-3], text.strip().split("/")[0].strip()[-3:]
    return float(value) * {"KiB": 1 / 1024, "MiB": 1, "GiB": 1024}[unit]


def sample(app):
    lines = run("docker", "stats", "--no-stream", "--format", "{{.Name}}|{{.CPUPerc}}|{{.MemUsage}}").splitlines()
    values = [(name, float(cpu.rstrip("%")), memory_mb(mem)) for name, cpu, mem in (line.split("|") for line in lines)]
    own = next((value for value in values if value[0] == app), None)
    if own is None:
        raise RuntimeError(f"missing container stats for {app}")
    foreign = sum(cpu for name, cpu, _ in values if name not in (app,) and not name.startswith(f"agentmvc-{one_shot.RUN_NAME}-bench-"))
    return {"cpu_percent": round(own[1], 2), "memory_mb": round(own[2], 2),
            "foreign_container_cpu_percent": round(foreign, 2), "host_load_1m": round(os.getloadavg()[0], 2)}


def ready():
    deadline = time.monotonic() + 180
    while time.monotonic() < deadline:
        try:
            request = urllib.request.Request(f"http://127.0.0.1:{HOST_PORT}/api/tags",
                                             headers={"Accept": "application/json"})
            if urllib.request.urlopen(request, timeout=2).status == 200:
                return
        except Exception:
            time.sleep(.2)
    raise RuntimeError("backend did not answer /api/tags")


def workload(app, count, saves):
    command = ["node", str(ROOT / "tools/live-load.mjs"), f"http://127.0.0.1:{HOST_PORT}", str(count), str(saves)]
    proc = subprocess.Popen(command, cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, bufsize=1)
    idle, active = [], []
    sampling = threading.Event()
    thread = None
    result = None

    def sample_active():
        while sampling.is_set():
            try:
                active.append(sample(app))
            except Exception:
                pass
            time.sleep(.25)

    for line in proc.stdout:
        message = json.loads(line)
        if message["event"] == "idle_ready":
            for _ in range(2):
                idle.append(sample(app))
        elif message["event"] == "active_start":
            sampling.set()
            thread = threading.Thread(target=sample_active, daemon=True)
            thread.start()
        elif message["event"] == "result":
            result = message
            sampling.clear()
    if thread:
        thread.join()
    errors = proc.stderr.read()
    if proc.wait() or result is None:
        raise RuntimeError(f"load generator failed: {errors}")
    result["idle"] = {"cpu_percent_median": round(statistics.median(s["cpu_percent"] for s in idle), 2),
                      "memory_mb_peak": max(s["memory_mb"] for s in idle)}
    result["active"] = {"cpu_percent_peak": max((s["cpu_percent"] for s in active), default=None),
                        "memory_mb_peak": max((s["memory_mb"] for s in active), default=None)}
    result["idle_samples"] = idle
    result["active_samples"] = active
    samples = idle + active
    result["foreign_container_cpu_percent_peak"] = max(s["foreign_container_cpu_percent"] for s in samples)
    result["host_load_1m_peak"] = max(s["host_load_1m"] for s in samples)
    return result


def one(stack, round_number, counts, saves):
    name = f"agentmvc-{one_shot.RUN_NAME}-bench-{stack}-{round_number}-{os.getpid()}"
    net, db, app = f"{name}-net", f"{name}-db", f"{name}-app"
    image = f"agentmvc-{one_shot.RUN_NAME}-{stack}:final"
    started = datetime.now(timezone.utc).isoformat()
    data = {"stack": stack, "round": round_number, "started": started, "image": image,
            "image_sha256": run("docker", "image", "inspect", "--format", "{{.Id}}", image),
            "image_mb": round(int(run("docker", "image", "inspect", "--format", "{{.Size}}", image)) / 1e6, 1),
            "limits": list(LIMITS), "backend_instances": 1, "database": "postgres:17-alpine",
            "scenarios": []}
    try:
        run("docker", "network", "create", net)
        run("docker", "run", "-d", "--name", db, "--network", net, "--network-alias", "db", *LIMITS,
            "-e", "POSTGRES_PASSWORD=conduit", "-e", "POSTGRES_DB=conduit", "postgres:17-alpine")
        for _ in range(240):
            if not subprocess.run(["docker", "exec", db, "pg_isready", "-h", "127.0.0.1", "-U", "postgres", "-d", "conduit"],
                                  capture_output=True).returncode:
                break
            time.sleep(.5)
        run("docker", "exec", db, "pg_isready", "-h", "127.0.0.1", "-U", "postgres", "-d", "conduit")
        run("docker", "run", "-d", "--name", app, "--network", net, *LIMITS,
            "-p", f"127.0.0.1:{HOST_PORT}:8080", "-e", "DATABASE_URL=postgres://postgres:conduit@db:5432/conduit",
            "-e", "SECRET_KEY_BASE=" + "0123456789abcdef" * 8, "-e", "PORT=8080", image)
        ready()
        time.sleep(2)
        data["baseline"] = sample(app)
        for count in counts:
            scenario = workload(app, count, saves)
            data["scenarios"].append(scenario)
            print(f"{stack} round {round_number}, {count} subscribers: {scenario['delivery_latency']}", flush=True)
        data["status"] = "complete"
    except Exception as error:
        data["status"] = "failed"
        data["error"] = str(error)
        raise
    finally:
        run("docker", "rm", "-f", app, db, check=False)
        run("docker", "network", "rm", net, check=False)
        data["finished"] = datetime.now(timezone.utc).isoformat()
        OUT.mkdir(parents=True, exist_ok=True)
        (OUT / f"{stack}-round{round_number}.json").write_text(json.dumps(data, indent=2) + "\n")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--rounds", type=int, default=2)
    parser.add_argument("--start-round", type=int, default=1)
    parser.add_argument("--stacks", default="rails,phoenix,loco")
    parser.add_argument("--counts", default="10,100,500")
    parser.add_argument("--saves", type=int, default=20)
    args = parser.parse_args()
    counts = [int(value) for value in args.counts.split(",")]
    stacks = tuple(args.stacks.split(","))
    if not stacks or any(stack not in STACKS for stack in stacks):
        raise SystemExit("--stacks must list rails, phoenix, and/or loco")
    run(sys.executable, str(ROOT / "tools/one_shot.py"), "verify-source")
    if not (ROOT / "frontend/node_modules").is_dir():
        subprocess.run(["npm", "ci", "--silent"], cwd=ROOT / "frontend", check=True)
    for stack in stacks:
        source = one_shot.WORK / stack
        if not source.is_dir():
            raise SystemExit(f"missing one-shot backend: {source}")
        run(sys.executable, str(ROOT / "tools/one_shot.py"), "verify", str(source))
        run("docker", "build", "-q", "-t", f"agentmvc-{one_shot.RUN_NAME}-{stack}:final", str(source))
    for round_number in range(args.start_round, args.start_round + args.rounds):
        order = stacks if round_number % 2 else tuple(reversed(stacks))
        for stack in order:
            one(stack, round_number, counts, args.saves)


if __name__ == "__main__":
    main()
