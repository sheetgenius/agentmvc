"""Run one step for one stack with an AI agent, and record it.

Usage: python3 tools/run-step.py STACK STEP [--deny REGEX ...]

1. Materializes the agent's directory in .work/STACK-STEP (tools/workdir.py --before).
2. Runs the agent on steps/STEP.md. The default is the Codex CLI with the model and reasoning in stacks/STACK/stack.json;
   set AGENT_CMD to use another agent. It runs in the work directory, reads the prompt on stdin, and must write JSONL
   events to stdout and its final message to $AGENT_LAST_MESSAGE.
3. Copies back only what the agent wrote: the code into stacks/STACK/STEP/ (and, after step 1, the generator output
   into stacks/STACK/scaffold/), its final report into reports/, its scrubbed transcript into transcripts/, and a
   record into runs.json.

Then verify with tools/check.sh STACK STEP, and rebuild the tables with tools/report.py.
Before step 4, benchmark step 3 (tools/bench/run.sh); before step 5, scan step 4 (tools/security/scan.sh): the
agent receives those results as its baseline.
"""
import argparse, hashlib, json, os, shutil, subprocess, sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import scrub  # noqa: E402
import workdir  # noqa: E402

ROOT = workdir.ROOT
HARNESS_INPUTS = {"realworld_spec", ".scaffold", "perf", "security", "ENVIRONMENT.md"}
NEVER = {".git", "vendor", "deps", "_build", "target", "node_modules", ".DS_Store", "master.key", ".hex", ".mix"}
RUNTIME = {"tmp", "log"}  # kept only as the generator's .keep placeholders


def ignorer(root):
    def ignore(directory, names):
        here = Path(directory)
        top = here == Path(root)
        runtime = any(part in RUNTIME for part in here.relative_to(root).parts)
        return [n for n in names if n in NEVER or (top and n in HARNESS_INPUTS) or n.startswith(".env")
                or (runtime and n != ".keep" and not (here / n).is_dir())]
    return ignore


def now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def usage(events):
    totals = {"input": 0, "cached_input": 0, "output": 0, "reasoning_output": 0, "commands": 0}
    for e in events:
        if e.get("type") == "turn.completed":
            u = e.get("usage", {})
            totals["input"] += u.get("input_tokens", 0)
            totals["cached_input"] += u.get("cached_input_tokens", 0)
            totals["output"] += u.get("output_tokens", 0)
            totals["reasoning_output"] += u.get("reasoning_output_tokens", 0)
        if e.get("type") == "item.completed" and (e.get("item") or {}).get("type") == "command_execution":
            totals["commands"] += 1
    totals["cost"] = totals["input"] - totals["cached_input"] + totals["output"]
    return totals


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("stack"), parser.add_argument("step")
    parser.add_argument("--deny", action="append", default=[], help="extra private strings to redact (regex)")
    args = parser.parse_args()
    stack_dir = ROOT / "stacks" / args.stack
    stack = json.loads((stack_dir / "stack.json").read_text())
    prompt = ROOT / "steps" / f"{args.step}.md"
    work = ROOT / ".work" / f"{args.stack}-{args.step}"
    logs = ROOT / ".work" / f"{args.stack}-{args.step}.logs"
    workdir.materialize(args.stack, args.step, work, before=True)
    logs.mkdir(parents=True, exist_ok=True)
    events_path, last = logs / "events.jsonl", logs / "last.md"

    agent = stack["agent"]
    command = os.environ.get("AGENT_CMD") or (
        f"codex exec -m {agent['model']} -c 'model_reasoning_effort=\"{agent['reasoning']}\"' -s workspace-write "
        "-c sandbox_workspace_write.network_access=true --skip-git-repo-check --json -o \"$AGENT_LAST_MESSAGE\" -")
    started = now()
    with open(prompt) as stdin, open(events_path, "w") as stdout:
        exit_code = subprocess.call(command, shell=True, cwd=work, stdin=stdin, stdout=stdout,
                                    env={**os.environ, "AGENT_LAST_MESSAGE": str(last)})
    finished = now()

    target = stack_dir / args.step
    if target.exists():
        shutil.rmtree(target)
    shutil.copytree(work, target, ignore=ignorer(work))
    if args.step.startswith("1-") and (work / ".scaffold").is_dir():
        shutil.rmtree(stack_dir / "scaffold", ignore_errors=True)
        shutil.copytree(work / ".scaffold", stack_dir / "scaffold", ignore=ignorer(work / ".scaffold"))

    events = scrub.scrub_file(events_path, work, stack_dir / "transcripts" / args.step, args.deny,
                              header={"title": f"{stack['name']} · {args.step}", "Prompt": f"[steps/{args.step}.md](../../../steps/{args.step}.md)"})
    if last.exists():
        report = scrub.Scrubber(work, args.deny).text(last.read_text()).replace("/work/app/", f"../{args.step}/")
        (stack_dir / "reports").mkdir(exist_ok=True)
        (stack_dir / "reports" / f"{args.step}.md").write_text(report)

    record = {"step": args.step, "kind": "build", "session_id": next((e.get("thread_id") for e in events if e.get("thread_id")), None),
              "agent": agent if not os.environ.get("AGENT_CMD") else {"command": "custom (AGENT_CMD)"},
              "started": started, "finished": finished,
              "seconds": int((datetime.fromisoformat(finished[:-1]) - datetime.fromisoformat(started[:-1])).total_seconds()),
              "exit": exit_code, "prompt": f"steps/{args.step}.md",
              "prompt_sha256": hashlib.sha256(prompt.read_bytes()).hexdigest(), "tokens": usage(events),
              "verified": None}
    runs_path = stack_dir / "runs.json"
    runs = json.loads(runs_path.read_text()) if runs_path.exists() else []
    runs = [r for r in runs if not (r["step"] == args.step and r["kind"] == "build")] + [record]
    runs_path.write_text(json.dumps(runs, indent=1) + "\n")
    print(f"{args.stack} {args.step}: agent exited {exit_code}; now run tools/check.sh {args.stack} {args.step}")


if __name__ == "__main__":
    main()
