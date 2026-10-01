"""Paired benchmark: Rails baseline vs the Roundhouse->Spinel compiled Conduit, alternating order.

Usage: python3 run_paired.py OUT_DIR [--rounds 2] [--scenarios a,b] [--warmup 3s --duration 15s]

Uses the unchanged tools/bench/bench.py (same seed, limits, k6 load, 16 VUs) once per configuration per round.
Round 1 runs CONFIGS in order, round 2 in reverse. Records image IDs, extra env, the declared budget, the derived
worker count (from the app's boot log), and every bench.py results.json.
"""
import argparse, json, os, re, subprocess, sys, time
from datetime import datetime, timezone

# Publication edit: ROOT was an absolute local checkout path; it is now the repository root containing this file
# (results/ruby-compile/<package>/evidence/bench/). Nothing else changed.
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), *[".."] * 5))
BENCH = os.path.join(ROOT, "tools/bench/bench.py")
CONFIGS = [
    # label, image, BENCH_EXTRA_ENV, description
    ("rails-ref-1proc", "agentmvc-v2-expert-rails-reference-1:review", "",
     "Rails reference-1 image as recorded: one Puma process, RAILS_MAX_THREADS default 3, YJIT"),
    ("rails-ref-auto", "agentmvc-v2-expert-rails-reference-1:review", "WEB_CONCURRENCY=auto",
     "Rails reference-1 image, Puma workers derived from the cgroup quota (concurrent-ruby available_processor_count)"),
    ("cruby-v4-1proc", "spinel-spike-lead-conduit:v4-cruby", "",
     "Compile variant v4 source on CRuby/Rails (control for source changes), one Puma process"),
    ("compiled-v4", "spinel-spike-lead-conduit:v4-compiled", "",
     "Compiled v4: OS workers derived from cgroup quota x PG-lane factor 2 (documented rule)"),
    ("compiled-v4-k1", "spinel-spike-lead-conduit:v4-compiled", "SPINEL_WORKER_FACTOR=1",
     "Compiled v4: OS workers = ceil(quota) (factor 1)"),
]


def sh(*args):
    return subprocess.run(args, capture_output=True, text=True, check=True).stdout.strip()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("out")
    ap.add_argument("--rounds", type=int, default=2)
    ap.add_argument("--scenarios", default="")
    ap.add_argument("--warmup", default="")
    ap.add_argument("--duration", default="")
    ap.add_argument("--only", default="")
    a = ap.parse_args()
    out = os.path.abspath(a.out)
    os.makedirs(out, exist_ok=True)
    configs = [c for c in CONFIGS if not a.only or c[0] in a.only.split(",")]
    meta = {"started": datetime.now(timezone.utc).isoformat(),
            "budget": {"app": "--cpus=2 --memory=1g", "database": "--cpus=2 --memory=1g"},
            "bench_sha256": sh("shasum", "-a", "256", BENCH).split()[0],
            "load_sha256": sh("shasum", "-a", "256", os.path.join(ROOT, "tools/bench/load.js")).split()[0],
            "k6_image": sh("docker", "image", "inspect", "--format", "{{.Id}}", "grafana/k6:latest"),
            "postgres_image": sh("docker", "image", "inspect", "--format", "{{.Id}}", "postgres:17-alpine"),
            "configs": {c[0]: {"image": c[1], "image_id": sh("docker", "image", "inspect", "--format", "{{.Id}}", c[1]),
                                "extra_env": c[2], "description": c[3]} for c in configs},
            "overrides": {"scenarios": a.scenarios, "warmup": a.warmup, "duration": a.duration},
            "runs": []}
    for rnd in range(1, a.rounds + 1):
        order = configs if rnd % 2 == 1 else list(reversed(configs))
        for label, image, extra, _ in order:
            name = f"spinel-spike-{label}-r{rnd}"
            dest = os.path.join(out, f"{label}/round{rnd}")
            if os.path.exists(os.path.join(dest, "results.json")):
                print(f"skip existing {dest}", flush=True)
                continue
            env = {k: v for k, v in os.environ.items() if not k.startswith("BENCH_")}
            env["BENCH_HOST_PORT"] = "18090"
            if extra:
                env["BENCH_EXTRA_ENV"] = extra
            if a.scenarios:
                env["BENCH_SCENARIOS"] = a.scenarios
            if a.warmup:
                env["BENCH_WARMUP"] = a.warmup
            if a.duration:
                env["BENCH_DURATION"] = a.duration
            print(f"{datetime.now(timezone.utc).isoformat()} round {rnd}: {label}", flush=True)
            t = time.time()
            proc = subprocess.run([sys.executable, BENCH, image, name, dest], cwd=ROOT, env=env,
                                  capture_output=True, text=True, timeout=3600)
            os.makedirs(dest, exist_ok=True)
            open(os.path.join(dest, "runner.log"), "w").write(proc.stdout + proc.stderr)
            rec = {"label": label, "round": rnd, "exit": proc.returncode, "seconds": round(time.time() - t, 1)}
            rp = os.path.join(dest, "results.json")
            if os.path.exists(rp):
                d = json.load(open(rp))
                tail = d.get("app_log_tail", "")
                m = re.search(r"OS workers:[^\n]*", tail)
                rec["derived_workers"] = m.group(0) if m else None
                m = re.search(r"Workers: (\d+)", tail)
                rec["puma_workers"] = m.group(1) if m else None
                rec["failed_checks"] = sum(v.get("failed_checks", 0) for v in d.get("scenarios", {}).values())
                rec["rps"] = {k: v.get("rps") for k, v in d.get("scenarios", {}).items()}
                rec["foreign_cpu_max"] = max((v.get("foreign_container_cpu_percent_max", 0)
                                              for v in d.get("scenarios", {}).values()), default=None)
            if image.startswith("agentmvc-v2-expert-rails") or "cruby" in image:
                rec["puma_workers"] = "see boot-banners (Rails request logging hides the Puma banner in app_log_tail)"
            meta["runs"].append(rec)
            print(json.dumps(rec), flush=True)
            json.dump(meta, open(os.path.join(out, "summary.json"), "w"), indent=2)
    meta["finished"] = datetime.now(timezone.utc).isoformat()
    json.dump(meta, open(os.path.join(out, "summary.json"), "w"), indent=2)


if __name__ == "__main__":
    main()
