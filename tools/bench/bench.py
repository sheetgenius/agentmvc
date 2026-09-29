"""Benchmark one production image under identical conditions.

Usage: python3 bench.py IMAGE LABEL OUT_DIR
The app and its PostgreSQL each run in a container limited to 2 CPUs and 1 GB. The app receives only
DATABASE_URL, SECRET_KEY_BASE and PORT=8080. k6 runs in its own container on the same Docker network.
Writes OUT_DIR/results.json.
"""
import json, os, shutil, subprocess, sys, threading, time, urllib.request

IMAGE, LABEL, OUT = sys.argv[1], sys.argv[2], os.path.abspath(sys.argv[3])
HERE = os.path.dirname(os.path.abspath(__file__))
NET, DB, APP = f"agentmvc-bench-{LABEL}", f"agentmvc-bench-db-{LABEL}", f"agentmvc-bench-app-{LABEL}"
HOST_PORT = int(os.environ.get("BENCH_HOST_PORT", "18080"))  # set per caller when benchmarks run in parallel
LIMITS = ["--cpus=2", "--memory=1g"]
SECRET = "0123456789abcdef" * 8
# Sensitivity analyses only (labeled as such in results): extra environment for the app, e.g. "WEB_CONCURRENCY=2".
EXTRA_ENV = [arg for pair in os.environ.get("BENCH_EXTRA_ENV", "").split() for arg in ("-e", pair)]
SCENARIOS = ["list_anonymous", "list_signed_in", "list_by_tag", "feed", "article", "comments", "tags",
             "favorite_toggle", "create_article"]
VUS, WARMUP, DURATION = "16", "3s", "15s"
# Smoke-test overrides only; published results use the defaults above.
WARMUP = os.environ.get("BENCH_WARMUP", WARMUP)
DURATION = os.environ.get("BENCH_DURATION", DURATION)
SCENARIOS = os.environ["BENCH_SCENARIOS"].split(",") if os.environ.get("BENCH_SCENARIOS") else SCENARIOS


def sh(*args, check=True, capture=True):
    result = subprocess.run(args, capture_output=capture, text=True)
    if check and result.returncode != 0:
        raise RuntimeError(f"{' '.join(args)}\n{result.stderr}")
    return result.stdout.strip() if capture else ""


def psql(sql):
    return sh("docker", "exec", DB, "psql", "-U", "postgres", "-d", "conduit", "-tAc", sql)


def memory_mb():
    usage = sh("docker", "stats", "--no-stream", "--format", "{{.MemUsage}}", APP).split("/")[0].strip()
    number, unit = float(usage[:-3]), usage[-3:]
    return round(number * {"KiB": 1 / 1024, "MiB": 1, "GiB": 1024}.get(unit, 1), 1)


def foreign_cpu_percent():
    """CPU used by every container this harness didn't start: the benchmark host is not otherwise isolated."""
    lines = sh("docker", "stats", "--no-stream", "--format", "{{.Name}} {{.CPUPerc}}").splitlines()
    return round(sum(float(cpu.rstrip("%")) for name, cpu in (line.rsplit(" ", 1) for line in lines)
                     if not name.startswith("agentmvc-")), 1)


def statements():
    return int(psql("select coalesce(sum(calls),0) from pg_stat_statements where dbid = "
                    "(select oid from pg_database where datname = 'conduit') and query !~* 'pg_stat_statements'"))


def k6(scenario, duration, export=None):
    args = ["docker", "run", "--rm", "--network", NET, "-v", f"{OUT}:/work", "grafana/k6:latest", "run", "--quiet",
            "-e", f"BASE_URL=http://{APP}:8080", "-e", f"SCENARIO={scenario}", "-e", f"VUS={VUS}",
            "-e", f"DURATION={duration}"]
    if export:
        args += ["--summary-export", f"/work/{export}"]
    if os.environ.get("BENCH_RAW_OUTPUT"):
        suffix = export.removeprefix("k6-").removesuffix(".json") if export else f"warmup-{scenario}"
        args += ["--out", f"json=/work/raw-{suffix}.json"]
    sh(*(args + ["/work/load.js"]), check=False)


def teardown():
    for name in (APP, DB):
        subprocess.run(["docker", "rm", "-f", name], capture_output=True)
    subprocess.run(["docker", "network", "rm", NET], capture_output=True)


def main():
    os.makedirs(OUT, exist_ok=True)
    shutil.copy(os.path.join(HERE, "load.js"), os.path.join(OUT, "load.js"))
    teardown()
    results = {"image": IMAGE, "label": LABEL, "limits": LIMITS, "extra_env": os.environ.get("BENCH_EXTRA_ENV", ""), "vus": int(VUS), "duration": DURATION,
               "image_mb": round(int(sh("docker", "image", "inspect", "--format", "{{.Size}}", IMAGE)) / 1e6, 1)}
    try:
        sh("docker", "network", "create", NET)
        sh("docker", "run", "-d", "--name", DB, "--network", NET, *LIMITS, "-e", "POSTGRES_PASSWORD=postgres",
           "-e", "POSTGRES_DB=conduit", "postgres:17-alpine", "-c", "shared_preload_libraries=pg_stat_statements",
           "-c", "max_connections=200")
        for _ in range(60):
            if subprocess.run(["docker", "exec", DB, "pg_isready", "-U", "postgres", "-d", "conduit"],
                              capture_output=True).returncode == 0:
                break
            time.sleep(0.5)
        time.sleep(1)
        psql("create extension if not exists pg_stat_statements")

        started = time.time()
        sh("docker", "run", "-d", "--name", APP, "--network", NET, *LIMITS, "-p", f"127.0.0.1:{HOST_PORT}:8080",
           "-e", f"DATABASE_URL=postgres://postgres:postgres@{DB}:5432/conduit", "-e", f"SECRET_KEY_BASE={SECRET}",
           "-e", "PORT=8080", *EXTRA_ENV, IMAGE)
        last = None
        while time.time() - started < 180:
            try:
                probe = urllib.request.Request(f"http://127.0.0.1:{HOST_PORT}/api/tags", headers={"Accept": "application/json"})
                if urllib.request.urlopen(probe, timeout=2).status == 200:
                    break
            except Exception as error:
                last = repr(error)
                time.sleep(0.1)
        else:
            logs = subprocess.run(["docker", "logs", APP], capture_output=True, text=True)
            raise RuntimeError(f"app did not answer /api/tags within 180s (last: {last}):\n"
                               + (logs.stdout + logs.stderr)[:4000])
        results["cold_start_seconds"] = round(time.time() - started, 2)

        sh(sys.executable, os.path.join(HERE, "seed.py"), f"http://127.0.0.1:{HOST_PORT}",
           os.path.join(OUT, "seed.json"))
        results["seed_seconds"] = json.load(open(os.path.join(OUT, "seed.json")))["seed_seconds"]
        results["idle_memory_mb"] = memory_mb()

        results["scenarios"] = {}
        for scenario in SCENARIOS:
            k6(scenario, WARMUP)
            psql("select pg_stat_statements_reset()")
            peak, foreign, sampling = [0.0], [], [True]

            def sample():
                while sampling[0]:
                    try:
                        peak[0] = max(peak[0], memory_mb())
                        foreign.append(foreign_cpu_percent())
                    except Exception:
                        pass
                    time.sleep(1)

            sampler = threading.Thread(target=sample)
            sampler.start()
            k6(scenario, DURATION, export=f"k6-{scenario}.json")
            sampling[0] = False
            sampler.join()
            metrics = json.load(open(os.path.join(OUT, f"k6-{scenario}.json")))["metrics"]
            duration = metrics["http_req_duration"]
            requests = metrics["http_reqs"]["count"]
            checks = metrics.get("checks", {})
            results["scenarios"][scenario] = {
                "requests": requests,
                "rps": round(metrics["http_reqs"]["rate"], 1),
                "p50_ms": round(duration["med"], 2),
                "p95_ms": round(duration["p(95)"], 2),
                "p99_ms": round(duration["p(99)"], 2),
                "failed_checks": checks.get("fails", 0),
                "sql_statements_per_request": round(statements() / max(requests, 1), 2),
                "peak_memory_mb": peak[0],
                "foreign_container_cpu_percent_max": max(foreign, default=None),
                "host_load_1m": round(os.getloadavg()[0], 1),
            }
            print(f"{LABEL} {scenario}: {results['scenarios'][scenario]}", flush=True)
        results["app_log_tail"] = sh("docker", "logs", "--tail", "20", APP, check=False)[-2000:]
    finally:
        json.dump(results, open(os.path.join(OUT, "results.json"), "w"), indent=2)
        teardown()


if __name__ == "__main__":
    main()
