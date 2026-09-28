"""Copy an agent-built app into stacks/STACK/reference/ and check that it is the code the ledger measured.

Usage: python3 tools/reference.py STACK WORKDIR RUN_ID [--replace]

The copy keeps the app's own source, tests, migrations, lockfiles, Dockerfile and project docs. It leaves out
the frozen fixture copies, dependencies, build output, caches, symlinks, and anything the app's own
.gitignore ignores. It then measures the copy against stacks/STACK/scaffold/ and compares the owned token
count with the run's row in results/runs.jsonl.
"""
import argparse
import json
import shutil
import subprocess
import tempfile
from pathlib import Path

import measure

ROOT = measure.ROOT
LEDGER = ROOT / "results" / "runs.jsonl"
FIXTURE = ["/realworld_spec/", "/security/", "/harness/", "/.scaffold/", "/PROMPT.md", "/MEASUREMENT.md",
           "/ENVIRONMENT.md", "/EXPERIMENT.md", "/FIXTURE.json"]
CACHES = ["/.cargo/", ".cargo/registry/", ".cargo/git/", "vendor/bundle/", ".bundle/", "deps/", "_build/",
          "target/", "node_modules/", ".devenv/", ".direnv/", "/build/", "dist-newstyle/", "/tmp/", "/log/",
          "/storage/", ".hex/", ".mix/", ".cache/", ".tmp/", ".npm-cache/", ".elixir_ls/", "test-results/",
          "playwright-report/", ".git/", "__pycache__/", ".DS_Store", ".liquid/"]


def app_files(work):
    """Files git would add from WORKDIR, honoring the app's .gitignore but not the user's global excludes."""
    with tempfile.TemporaryDirectory() as git_dir:
        subprocess.run(["git", "init", "-q", "--bare", git_dir], check=True)
        command = ["git", "-c", "core.excludesFile=/dev/null", f"--git-dir={git_dir}", f"--work-tree={work}",
                   "ls-files", "--others", "--exclude-standard", "-z"]
        for pattern in FIXTURE + CACHES:
            command += ["-x", pattern]
        out = subprocess.run(command, cwd=work, check=True, capture_output=True).stdout
    names = [name for name in out.decode().split("\0") if name]
    return sorted(name for name in names if not (work / name).is_symlink())


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("stack")
    parser.add_argument("workdir", type=Path)
    parser.add_argument("run_id")
    parser.add_argument("--replace", action="store_true")
    args = parser.parse_args()
    rows = [json.loads(line) for line in LEDGER.read_text().splitlines() if line.strip()]
    row = next((r for r in rows if r["id"] == args.run_id), None)
    if row is None or row["stack"] != args.stack:
        raise SystemExit(f"{args.run_id} is not a {args.stack} run in the ledger")
    work = args.workdir.resolve()
    target = ROOT / "stacks" / args.stack / "reference"
    if target.exists():
        if not args.replace:
            raise SystemExit(f"{target} exists; pass --replace to swap in a new reference")
        shutil.rmtree(target)
    names = app_files(work)
    for name in names:
        (target / name).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(work / name, target / name)
        (target / name).chmod((target / name).stat().st_mode | 0o200)
    size = measure.measure(measure.load_stack(args.stack), target)
    expected = row["code"]["owned_tokens"]
    print(f"{args.stack}: copied {len(names)} files; owned {size['owned_tokens']:,} tokens "
          f"(ledger {expected:,}), whole app {size['tokens']:,} tokens")
    if size["owned_tokens"] != expected:
        raise SystemExit("owned tokens differ from the ledger; check what the copy included or left out")


if __name__ == "__main__":
    main()
