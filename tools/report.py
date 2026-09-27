"""Rebuild everything derived from the data in this repository.

Usage: python3 tools/report.py            (needs tiktoken and matplotlib: pip install -r tools/requirements.txt)

Writes:
- results/sizes.json          code size of every stack at every step, and what each step added or changed;
- results/charts/*.svg|png    the charts in the README and the findings pages;
- stacks/<stack>/README.md    each stack's steps, with links to its code, report and transcript;
- README.md                   the table between the stats markers.
"""
import json, re, statistics, sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.ticker import FuncFormatter  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
import measure  # noqa: E402

ROOT = measure.ROOT
RESULTS = ROOT / "results"
REFERENCE = "rails"  # ratios are relative to this stack
STEP_NAMES = {"1-build": "Build", "2-add-drafts": "Add drafts", "3-package": "Package", "4-tune": "Tune",
              "5-harden": "Harden", "6-polish": "Polish", "7-add-background-job": "Add a background job",
              "8-live-editing": "Live shared editing"}
SHORT = {"1-build": "Build", "2-add-drafts": "Add\ndrafts", "3-package": "Package", "4-tune": "Tune",
         "5-harden": "Harden", "6-polish": "Polish", "7-add-background-job": "Add\njob",
         "8-live-editing": "Live\nediting"}
STATS_START, STATS_END = "<!-- stats:start -->", "<!-- stats:end -->"

plt.rcParams.update({"font.family": "sans-serif", "font.size": 11, "axes.spines.top": False,
                     "axes.spines.right": False, "svg.fonttype": "none", "figure.facecolor": "white",
                     "axes.facecolor": "white", "axes.edgecolor": "#888", "axes.labelcolor": "#333",
                     "xtick.color": "#333", "ytick.color": "#333"})
THOUSANDS = FuncFormatter(lambda v, _p: f"{v:,.0f}")


def load(path):
    try:
        return json.loads(Path(path).read_text())
    except (OSError, ValueError):
        return None


def stacks():
    """Every stack, reference first, then in the order they were added."""
    loaded = {p.parent.name: measure.load_stack(p.parent.name) for p in (ROOT / "stacks").glob("*/stack.json")}
    return dict(sorted(loaded.items(), key=lambda kv: (kv[0] != REFERENCE, kv[1].get("order", 100), kv[0])))


def ratio(value, ref):
    if value is None or ref in (None, 0) or value == ref:
        return ""
    r = value / ref
    return f" ({r:.0f}×)" if r >= 10 else f" ({r:.2f}×)"


def cell(value, ref=None, unit="", digits=0):
    if value is None:
        return "–"
    return f"{value:,.{digits}f}{unit}" + ratio(value, ref)


# ---------------------------------------------------------------------------------------------------- data

def speed(stack, step_prefix, scenario):
    """Median req/s of every benchmark run of this stack's code at or after the given step."""
    values = []
    for path in sorted((RESULTS / "speed").glob(f"*-{stack}.json")):
        step = int(path.name.split("-")[0])
        data = load(path)
        if step >= step_prefix and data and scenario in data.get("scenarios", {}):
            values.append(data["scenarios"][scenario]["rps"])
    return statistics.median(values) if values else None


def speed_run(stack, run):
    return load(RESULTS / "speed" / f"{run}-{stack}.json")


def security(stack, step):
    data = load(RESULTS / "security" / f"{step}-{stack}.json")
    return None if not data else data["core_passed"] + data["defense_in_depth_passed"]


def runs(stack):
    return load(ROOT / "stacks" / stack / "runs.json") or []


def effort(stack):
    builds = [r for r in runs(stack) if r["kind"] == "build"]
    if not builds:
        return None, None, 0
    return (sum(r["tokens"]["cost"] for r in builds), sum(r["seconds"] for r in builds) / 60, len(builds))


def comprehension(stack, when):
    grades = load(ROOT / "comprehension" / "grades.json") or {}
    return (grades.get(when) or {}).get(stack, {}).get("score")


# ---------------------------------------------------------------------------------------------------- tables

def stats_table(all_stacks, sizes):
    ref = REFERENCE
    last = {s: max(sizes[s], key=lambda k: int(k.split("-")[0])) if sizes[s] else None for s in all_stacks}

    def at(s, step, key):
        return sizes[s].get(step, {}).get(key)

    def final(s, key):
        return sizes[s][last[s]][key] if last[s] else None

    rows = [
        ("Code an agent reads, after the last step (tokens)", lambda s: cell(final(s, "tokens"), final(ref, "tokens") if s != ref else None)),
        ("Lines of code, after the last step", lambda s: cell(final(s, "code_lines"), final(ref, "code_lines") if s != ref else None)),
        ("Code to add drafts, step 2 (tokens)", lambda s: cell(at(s, "2-add-drafts", "step_tokens"), at(ref, "2-add-drafts", "step_tokens") if s != ref else None)),
        ("Code to add a background job, step 7 (tokens)", lambda s: cell(at(s, "7-add-background-job", "step_tokens"), at(ref, "7-add-background-job", "step_tokens") if s != ref else None)),
        ("Code to add live editing, step 8 (tokens)", lambda s: cell(at(s, "8-live-editing", "step_tokens"), at(ref, "8-live-editing", "step_tokens") if s != ref else None)),
        ("Article list after tuning, median of runs (req/s)", lambda s: cell(speed(s, 4, "list_anonymous"), speed(ref, 4, "list_anonymous") if s != ref else None)),
        ("Peak memory under load, after tuning", lambda s: cell(peak(s), None, " MB")),
        ("Docker image", lambda s: cell((speed_run(s, "4-tune") or {}).get("image_mb"), None, " MB")),
        ("Cold start", lambda s: cell((speed_run(s, "4-tune") or {}).get("cold_start_seconds"), None, " s", 1)),
        ("Security checks passed, before → after hardening (of 13)", lambda s: security_cell(s)),
        ("Fresh agent's comprehension score, after steps 1 and 6 (of 12)", lambda s: comprehension_cell(s)),
        ("Agent effort, all steps (tokens, wall-clock)", lambda s: effort_cell(s)),
    ]
    header = "| | " + " | ".join(f"[{all_stacks[s]['name']}](stacks/{s}/) ({all_stacks[s]['language']})" for s in all_stacks) + " |"
    lines = [header, "| --- |" + " ---: |" * len(all_stacks)]
    lines += [f"| {label} | " + " | ".join(fn(s) for s in all_stacks) + " |" for label, fn in rows]
    return "\n".join(lines)


def peak(s):
    run = speed_run(s, "4-tune")
    return max(x["peak_memory_mb"] for x in run["scenarios"].values()) if run else None


def security_cell(s):
    before, after = security(s, "4-tune"), security(s, "5-harden")
    return "–" if before is None and after is None else f"{before if before is not None else '–'} → {after if after is not None else '–'}"


def comprehension_cell(s):
    scores = [comprehension(s, when) for when in ("after-1-build", "after-6-polish")]
    return " · ".join("–" if v is None else f"{v:g}" for v in scores)


def effort_cell(s):
    tokens, minutes, count = effort(s)
    if not count:
        return "–"
    ref_tokens, ref_minutes, ref_count = effort(REFERENCE)
    same = s == REFERENCE
    partial = f", {count} steps" if count != ref_count else ""
    return (f"{tokens / 1000:,.0f}k tokens{'' if same else ratio(tokens, ref_tokens)}, "
            f"{minutes:.0f} min{'' if same else ratio(minutes, ref_minutes)}{partial}")


def stack_readme(name, stack, sizes):
    by_step = {r["step"]: r for r in runs(name) if r["kind"] == "build"}
    lines = [f"# {stack['name']} ({stack['language']})", "", stack["description"] + ".", "",
             f"Built and evolved by {stack['agent']['tool']}, model `{stack['agent']['model']}` at `{stack['agent']['reasoning']}` "
             "reasoning. [`ENVIRONMENT.md`](ENVIRONMENT.md) is everything the agent was told about the stack; "
             "[`scaffold/`](scaffold/) is the untouched generator output.", "",
             "| Step | Code | Size (tokens) | Added or changed (tokens) | Agent tokens | Time | Report | Transcript |",
             "| --- | --- | ---: | ---: | ---: | ---: | --- | --- |"]
    for step, size in sizes.items():
        run = by_step.get(step, {})
        lines.append(f"| {step.split('-')[0]}. {STEP_NAMES.get(step, step)} | [`{step}/`]({step}/) | {size['tokens']:,} | "
                     f"{size['step_tokens']:,} | {cell(run.get('tokens', {}).get('cost'))} | "
                     f"{cell(run['seconds'] / 60, None, ' min', 1) if run else '–'} | "
                     f"[report](reports/{step}.md) | [transcript](transcripts/{step}.md) |")
    reads = [r for r in runs(name) if r["kind"] == "comprehension"]
    if reads:
        lines += ["", "Comprehension runs (read-only): " + ", ".join(
            f"[{r['step']}](transcripts/comprehension-{r['step']}.md)" for r in reads) + "."]
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------------------------------- charts

def chart_steps(sizes):
    return sorted({step for s in sizes.values() for step in s}, key=lambda k: int(k.split("-")[0]))


def growth_chart(all_stacks, sizes, out):
    steps = chart_steps(sizes)
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.6))
    for ax, key, title in ((axes[0], "tokens", "Code an agent reads, in tokens"), (axes[1], "code_lines", "Lines of code")):
        top = 0
        for s, stack in all_stacks.items():
            xs = [i for i, step in enumerate(steps) if step in sizes[s]]
            ys = [sizes[s][steps[i]][key] for i in xs]
            if not ys:
                continue
            ax.plot(xs, ys, marker="o", color=stack["color"], linewidth=2.2)
            ax.annotate(stack["name"], (xs[-1], ys[-1]), xytext=(6, 0), textcoords="offset points", va="center",
                        color=stack["color"], fontweight="bold")
            top = max(top, max(ys))
        ax.set_xticks(range(len(steps)), [SHORT.get(s, s) for s in steps])
        ax.set_xlim(-0.3, len(steps) - 0.2)
        ax.set_ylim(0, top * 1.12)
        ax.yaxis.set_major_formatter(THOUSANDS)
        ax.grid(axis="y", color="#e6e6e6")
        ax.set_axisbelow(True)
        ax.set_title(title, loc="left", fontweight="bold")
    fig.suptitle("The same app, grown through the same steps", x=0.01, ha="left", fontsize=14, fontweight="bold")
    fig.tight_layout()
    save(fig, out, "growth")


def ratio_chart(all_stacks, sizes, out):
    steps = chart_steps(sizes)
    fig, ax = plt.subplots(figsize=(8.5, 4.6))
    ref = sizes[REFERENCE]
    top = 1.0
    for s, stack in all_stacks.items():
        if s == REFERENCE:
            continue
        for key, style, what in (("tokens", "-", "tokens"), ("code_lines", "--", "lines")):
            xs = [i for i, step in enumerate(steps) if step in sizes[s] and step in ref]
            ys = [sizes[s][steps[i]][key] / ref[steps[i]][key] for i in xs]
            if ys:
                ax.plot(xs, ys, style, marker="o", color=stack["color"], linewidth=2.2, label=f"{stack['name']}, {what}")
                top = max(top, max(ys))
    ax.axhline(1, color=all_stacks[REFERENCE]["color"], linewidth=1.5)
    ax.annotate(f"{all_stacks[REFERENCE]['name']} = 1×", (0, 1), xytext=(0, 6), textcoords="offset points",
                color=all_stacks[REFERENCE]["color"])
    ax.set_xticks(range(len(steps)), [SHORT.get(s, s) for s in steps])
    ax.set_ylim(0, top * 1.1)
    ax.set_ylabel(f"× {all_stacks[REFERENCE]['name']} at the same step")
    ax.grid(axis="y", color="#e6e6e6")
    ax.set_axisbelow(True)
    ax.legend(frameon=False, loc="lower right", ncol=2)
    ax.set_title(f"Size relative to {all_stacks[REFERENCE]['name']}: flat means growing at the same rate", loc="left",
                 fontweight="bold")
    fig.tight_layout()
    save(fig, out, "ratio")


def change_cost_chart(all_stacks, sizes, out):
    steps = [s for s in chart_steps(sizes) if not s.startswith("1-")]
    fig, ax = plt.subplots(figsize=(10, 4.6))
    width = 0.8 / max(len(all_stacks), 1)
    for i, (s, stack) in enumerate(all_stacks.items()):
        xs = [x + (i - (len(all_stacks) - 1) / 2) * width for x, step in enumerate(steps) if step in sizes[s]]
        ys = [sizes[s][step]["step_tokens"] for step in steps if step in sizes[s]]
        ax.bar(xs, ys, width, color=stack["color"], label=stack["name"])
    ax.set_xticks(range(len(steps)), [SHORT.get(s, s) for s in steps])
    ax.yaxis.set_major_formatter(THOUSANDS)
    ax.grid(axis="y", color="#e6e6e6")
    ax.set_axisbelow(True)
    ax.legend(frameon=False)
    ax.set_ylabel("Code added or changed, tokens")
    ax.set_title("What each step cost in code", loc="left", fontweight="bold")
    fig.tight_layout()
    save(fig, out, "change-cost")


def throughput_chart(all_stacks, out):
    scenarios = [("list_anonymous", "Article list"), ("list_signed_in", "Article list, signed in"), ("feed", "Feed"),
                 ("article", "One article")]
    fig, ax = plt.subplots(figsize=(10, 4.4))
    width = 0.8 / max(len(all_stacks), 1)
    for i, (s, stack) in enumerate(all_stacks.items()):
        runs_ = [load(p) for p in sorted((RESULTS / "speed").glob(f"*-{s}.json")) if int(p.name.split("-")[0]) >= 4]
        runs_ = [r for r in runs_ if r and "scenarios" in r]
        if not runs_:
            continue
        samples = [sorted(r["scenarios"][sc]["rps"] for r in runs_) for sc, _ in scenarios]
        medians = [statistics.median(v) for v in samples]
        xs = [x + (i - (len(all_stacks) - 1) / 2) * width for x in range(len(scenarios))]
        ax.bar(xs, medians, width, color=stack["color"], label=stack["name"])
        ax.errorbar(xs, medians, yerr=[[m - v[0] for m, v in zip(medians, samples)], [v[-1] - m for m, v in zip(medians, samples)]],
                    fmt="none", ecolor="#333", elinewidth=1, capsize=3)
        for x, m, v in zip(xs, medians, samples):
            ax.annotate(f"{m:,.0f}", (x, v[-1]), xytext=(0, 3), textcoords="offset points", ha="center", fontsize=8, color="#333")
    ax.set_xticks(range(len(scenarios)), [label for _s, label in scenarios])
    ax.yaxis.set_major_formatter(THOUSANDS)
    ax.grid(axis="y", color="#e6e6e6")
    ax.set_axisbelow(True)
    ax.legend(frameon=False, loc="upper left")
    ax.set_ylabel("Requests per second")
    ax.set_title("Throughput after tuning: 2 CPUs and 1 GB per app, 16 concurrent users", loc="left", fontweight="bold")
    fig.text(0.01, 0.01, "Bars: median of every benchmark run of the tuned code. Whiskers: lowest and highest run.",
             fontsize=9, color="#555")
    fig.tight_layout(rect=(0, 0.04, 1, 1))
    save(fig, out, "throughput")


def save(fig, out, name):
    svg = out / f"{name}.svg"
    fig.savefig(svg, metadata={"Date": None})
    svg.write_text("\n".join(line.rstrip() for line in svg.read_text().splitlines()) + "\n")
    fig.savefig(out / f"{name}.png", dpi=160, metadata={"Software": None})
    plt.close(fig)


# ---------------------------------------------------------------------------------------------------- main

def main():
    all_stacks = stacks()
    sizes = {s: measure.measure_stack(s) for s in all_stacks}
    (RESULTS / "sizes.json").write_text(json.dumps(sizes, indent=1) + "\n")
    charts = RESULTS / "charts"
    charts.mkdir(parents=True, exist_ok=True)
    growth_chart(all_stacks, sizes, charts)
    ratio_chart(all_stacks, sizes, charts)
    change_cost_chart(all_stacks, sizes, charts)
    throughput_chart(all_stacks, charts)
    for s, stack in all_stacks.items():
        (ROOT / "stacks" / s / "README.md").write_text(stack_readme(s, stack, sizes[s]))
    readme = (ROOT / "README.md").read_text()
    table = stats_table(all_stacks, sizes)
    readme = re.sub(re.escape(STATS_START) + r".*?" + re.escape(STATS_END),
                    lambda _m: f"{STATS_START}\n{table}\n{STATS_END}", readme, flags=re.S)
    (ROOT / "README.md").write_text(readme)
    print(f"report: {len(all_stacks)} stacks, {sum(len(v) for v in sizes.values())} steps measured")


if __name__ == "__main__":
    main()
