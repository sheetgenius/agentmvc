"""Materialize the directory an agent works in, for running a step or checking one.

Usage:
  python3 tools/workdir.py STACK STEP DEST            the code after STEP, ready to check (bin/check, bin/check-production)
  python3 tools/workdir.py STACK STEP DEST --before   what the agent starts STEP with: the previous step's code plus the
                                                      step's inputs

The repository stores only what agents wrote. An agent's directory also holds:
- realworld_spec/  the spec, with the features that exist at that step (drafts from step 2, exports from step 7);
- .scaffold/       the untouched generator output;
- ENVIRONMENT.md   the stack facts;
- perf/            from step 4: the benchmark, plus perf/baseline/results.json when the agent is about to tune;
- security/        from step 5: the security checks, plus security/baseline/results.json when about to harden.
"""
import shutil, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TOOLS = ROOT / "tools"
FEATURES = {"drafts": 2, "exports": 7, "live-editing": 8}  # feature -> the step that adds it


def number(step):
    return int(step.split("-")[0])


def step_dirs(stack):
    return sorted((p.name for p in (ROOT / "stacks" / stack).iterdir() if p.is_dir() and p.name[0].isdigit()), key=number)


def step_name(n):
    for path in (ROOT / "steps").glob(f"{n}-*.md"):
        return path.stem
    raise SystemExit(f"no step {n} in steps/")


def materialize(stack, step, dest, before=False):
    n = number(step)
    dest = Path(dest)
    if dest.exists():
        shutil.rmtree(dest)
    if before and n == 1:
        dest.mkdir(parents=True)
    else:
        code = ROOT / "stacks" / stack / (step_name(n - 1) if before else step)
        if not code.is_dir():
            raise SystemExit(f"{code} doesn't exist: run the earlier steps first")
        shutil.copytree(code, dest)
        shutil.copytree(ROOT / "stacks" / stack / "scaffold", dest / ".scaffold")
    shutil.copy(ROOT / "stacks" / stack / "ENVIRONMENT.md", dest / "ENVIRONMENT.md")

    spec = dest / "realworld_spec"
    for part in ("api", "docs", "bin"):
        shutil.copytree(ROOT / "spec" / part, spec / part)
    for feature, added_at in FEATURES.items():
        if n >= added_at:
            shutil.copytree(ROOT / "spec" / "features" / feature, spec / "features" / feature,
                            ignore=shutil.ignore_patterns("validation"))
    if n >= 8:
        shutil.copytree(ROOT / "frontend", spec / "frontend",
                        ignore=shutil.ignore_patterns("node_modules", "dist", "test-results", "playwright-report"))

    if n >= 4:
        (dest / "perf").mkdir()
        for name in ("bench.py", "load.js", "seed.py", "bench.sh"):
            shutil.copy(TOOLS / "bench" / name, dest / "perf" / name)
        baseline = ROOT / "results" / "speed" / f"3-package-{stack}.json"
        if before and n == 4 and baseline.exists():
            (dest / "perf" / "baseline").mkdir()
            shutil.copy(baseline, dest / "perf" / "baseline" / "results.json")
    if n >= 5:
        shutil.copytree(TOOLS / "security" / "hurl", dest / "security" / "hurl")
        shutil.copy(TOOLS / "security" / "run-hurl.sh", dest / "security" / "run-hurl.sh")
        baseline = ROOT / "results" / "security" / f"4-tune-{stack}.json"
        if before and n == 5 and baseline.exists():
            (dest / "security" / "baseline").mkdir()
            shutil.copy(baseline, dest / "security" / "baseline" / "results.json")
    return dest


if __name__ == "__main__":
    stack, step, dest = sys.argv[1:4]
    before = "--before" in sys.argv[4:]
    if not step[0].isdigit():
        raise SystemExit("STEP is a step directory name, e.g. 2-add-drafts")
    print(materialize(stack, step, dest, before))
