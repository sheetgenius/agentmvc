"""Security baseline for one production image.

Usage: python3 scan.py IMAGE STACK SOURCE_DIR OUT_DIR      (STACK: a directory in stacks/; see tools/security/scan.sh)
- Runs the app like the benchmark does (2 CPUs / 1 GB, only DATABASE_URL, SECRET_KEY_BASE and PORT).
- Runs the 13 black-box checks in security/hurl over the container network.
- Scans the lockfile named in stacks/STACK/stack.json with OSV-Scanner, and runs the static analyzer named there,
  if the stack has one (brakeman and sobelow are built in; add a branch in static_analysis() for another).
Writes OUT_DIR/results.json.
"""
import json, os, re, shutil, subprocess, sys, tempfile, time, urllib.request

IMAGE, STACK, SOURCE, OUT = sys.argv[1], sys.argv[2], os.path.abspath(sys.argv[3]), os.path.abspath(sys.argv[4])
HERE = os.path.dirname(os.path.abspath(__file__))
NET, DB, APP = f"agentmvc-sec-{STACK}", f"agentmvc-sec-db-{STACK}", f"agentmvc-sec-app-{STACK}"
LIMITS = ["--cpus=2", "--memory=1g"]
CONFIG = json.load(open(os.path.join(HERE, "..", "..", "stacks", STACK, "stack.json")))["security"]
DEFENSE_IN_DEPTH = {"s12_nosniff_header", "s13_login_rate_limit"}


def run(*args, **kwargs):
    return subprocess.run(args, capture_output=True, text=True, **kwargs)


def teardown():
    for name in (APP, DB):
        run("docker", "rm", "-f", name)
    run("docker", "network", "rm", NET)


def start_app():
    run("docker", "network", "create", NET)
    run("docker", "run", "-d", "--name", DB, "--network", NET, *LIMITS, "-e", "POSTGRES_PASSWORD=postgres",
        "-e", "POSTGRES_DB=conduit", "postgres:17-alpine")
    for _ in range(60):
        if run("docker", "exec", DB, "pg_isready", "-U", "postgres", "-d", "conduit").returncode == 0:
            break
        time.sleep(0.5)
    time.sleep(1)
    run("docker", "run", "-d", "--name", APP, "--network", NET, *LIMITS, "-p", "127.0.0.1:18081:8080",
        "-e", f"DATABASE_URL=postgres://postgres:postgres@{DB}:5432/conduit",
        "-e", "SECRET_KEY_BASE=" + "0123456789abcdef" * 8, "-e", "PORT=8080", IMAGE)
    deadline = time.time() + 180
    while time.time() < deadline:
        try:
            probe = urllib.request.Request("http://127.0.0.1:18081/api/tags", headers={"Accept": "application/json"})
            if urllib.request.urlopen(probe, timeout=2).status == 200:
                return
        except Exception:
            time.sleep(0.2)
    raise RuntimeError("app never answered:\n" + run("docker", "logs", APP).stdout[-3000:])


def black_box():
    result = run(os.path.join(HERE, "run-hurl.sh"), f"http://{APP}:8080", env={**os.environ, "NETWORK": NET})
    text = result.stdout + result.stderr
    outcome = {name: status == "Success" for status, name in re.findall(r"(Success|Failure) (s\d+_\w+)\.hurl", text)}
    return outcome, text[-6000:]


def dependency_scan():
    lock = CONFIG["lockfile"]
    result = run("docker", "run", "--rm", "-v", f"{SOURCE}:/src:ro", "ghcr.io/google/osv-scanner:latest", "scan",
                 "source", "--lockfile", f"/src/{lock}", "--format", "json")
    try:
        data = json.loads(result.stdout)
    except ValueError:
        return {"error": result.stderr[-1000:]}
    found = [{"package": p["package"]["name"], "version": p["package"]["version"],
              "ids": [v["id"] for v in p["vulnerabilities"]]}
             for r in data.get("results", []) for p in r.get("packages", [])]
    return {"lockfile": lock, "vulnerable_packages": found}


def static_analysis():
    if CONFIG.get("analyzer") == "brakeman":
        result = run("docker", "run", "--rm", "-v", f"{SOURCE}:/code:ro", "presidentbeef/brakeman:latest",
                     "--format", "json", "--quiet", "--no-exit-on-warn", "--no-exit-on-error", "/code")
        try:
            warnings = json.loads(result.stdout).get("warnings", [])
            return {"tool": "brakeman", "findings": [{"type": w["warning_type"], "confidence": w["confidence"],
                                                     "file": w.get("file"), "message": w["message"]} for w in warnings]}
        except ValueError:
            return {"tool": "brakeman", "error": (result.stdout + result.stderr)[-1500:]}
    if CONFIG.get("analyzer") == "sobelow":
        script = ("mix local.hex --force >/dev/null && mix archive.install hex sobelow --force >/dev/null && "
                  "mix sobelow --root . --format json --private")
        # Mix loads the project and may write build files, so Sobelow gets a writable scratch copy. Its JSON
        # output needs Jason, which the archive doesn't bundle: ERL_LIBS lends it the project's compiled copy.
        with tempfile.TemporaryDirectory() as scratch:
            copy = os.path.join(scratch, "app")
            shutil.copytree(SOURCE, copy, symlinks=True, ignore=shutil.ignore_patterns(".git", "realworld_spec"))
            result = run("docker", "run", "--rm", "--user", f"{os.getuid()}:{os.getgid()}", "-e", "HOME=/tmp",
                         "-e", "MIX_HOME=/tmp/mix", "-e", "HEX_HOME=/tmp/hex", "-e", "ERL_LIBS=/app/_build/dev/lib",
                         "-v", f"{copy}:/app", "-w", "/app",
                         "elixir:1.18.4-otp-27", "sh", "-c", script)
        try:
            data = json.loads(result.stdout[result.stdout.index("{"):])
            findings = [dict(item, confidence=level) for level, items in data.get("findings", {}).items()
                        for item in items]
            return {"tool": "sobelow", "findings": findings}
        except ValueError:
            return {"tool": "sobelow", "error": (result.stdout + result.stderr)[-1500:]}
    return {"tool": None, "note": CONFIG.get("analyzer_note", "No static security analyzer configured for this stack.")}


def main():
    os.makedirs(OUT, exist_ok=True)
    teardown()
    results = {"image": IMAGE, "stack": STACK}
    try:
        start_app()
        outcome, log = black_box()
        results["black_box"] = outcome
        results["core_passed"] = sum(v for k, v in outcome.items() if k not in DEFENSE_IN_DEPTH)
        results["core_total"] = sum(1 for k in outcome if k not in DEFENSE_IN_DEPTH)
        results["defense_in_depth_passed"] = sum(v for k, v in outcome.items() if k in DEFENSE_IN_DEPTH)
        results["hurl_log_tail"] = log
    finally:
        teardown()
    results["dependencies"] = dependency_scan()
    results["static_analysis"] = static_analysis()
    json.dump(results, open(os.path.join(OUT, "results.json"), "w"), indent=2)
    print(json.dumps({k: results[k] for k in ("stack", "core_passed", "core_total", "defense_in_depth_passed")
                      if k in results}))


if __name__ == "__main__":
    main()
