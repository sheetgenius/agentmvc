# Contributing to AgentMVC

AgentMVC is an evergreen comparison and a set of reference implementations. The question is how well an agent can build and keep improving a large application in each language and framework. Make a lane better, show what changed, and leave enough evidence for the next contributor to climb from there. Small, useful improvements are welcome; you do not need to rerun the entire study for each one.

Start with the [repository map](README.md#repository-map), the [current results](results/README.md), and the prompt for the lane you want to improve. The one-shot prompts are also reusable starting points for your own projects.

## Two kinds of work

- **One-shot study:** An agent gets a frozen prompt, fixture, and checks, then builds in one measured session. Preserve its exact output. A new prompt, model, environment, or human edit creates a newly labeled condition. Never quietly change an earlier result.
- **Reference lane:** Improve the best current implementation through as many agent or human iterations as useful. You may change the code, prompt guidance, dependencies, and tooling. Record what helped. The goal is excellent, readable, domain-rich code and a production-ready app, not a one-session score.

Keep these labels visible in PRs and result pages. A reference improvement can teach us more than another one-shot, but its effort and runtime numbers cannot be pooled with a frozen run.

## Submit a practitioner brief

A practitioner brief is up to 500 words of stack-specific guidance from someone who knows the stack. [briefs/README.md](briefs/README.md) has the rules, the template and draft seeds. Check yours with `python3 tools/brief_check.py`, and include your prediction of what it will change. Maintainers run each brief with and without it on the same inputs, as [experiment v3](docs/experiment-v3.md) describes, so a brief's effect is reported for its own stack only.

## Propose a lane improvement

Open a focused PR with:

1. **Question and change.** Name the lane and the problem you found. Link the prior source revision or result, and explain the design choice in plain language. A short series of commits that shows the diagnosis, implementation, and measurement is better than a polished final diff with no trail.
2. **Source and provenance.** Link the exact code revision. Say whether an agent, a person, or both wrote it. For a one-shot, link the frozen prompt and fixture hash, plus model and tool version. For an iterative reference, link the prompt or guidance that materially shaped the change when available.
3. **Checks.** Run the lane’s relevant development and production gates. Include commands and outcomes, including a failure that explains a fix. Add a focused test when it protects a rule or regression; a one-line refactor does not need a new test.
4. **Measurements, when claiming an improvement.** Compare before and after with the same workload, seed, machine, resource limits, and repeated rounds. Give raw measurements or a link to them, not just the best number. For code size, say what files the count includes. For performance, report correctness and SQL work too; a faster endpoint that skips work is not a win.

Agent token usage, wall time, source tokens, and line counts are useful context **when readily available**. Record the counting method and scope. They are not a contribution requirement or a universal quality score. In a long-running reference lane, cumulative inference is especially hard to compare across people and tools.

For a new language lane, first make its environment and gates reproducible. Disclose any scaffold or framework guidance supplied to the agent. A working, honest pilot is more useful than a broad but unverified claim.

## Transcripts and private data

Do not add agent transcripts, agent final reports, chat exports, raw credentials, local workdirs, or account details to Git; `.gitignore` keeps the usual file names out. The historical transcripts, agent reports and comprehension answers have left the working tree too. [`results/message-archive.json`](results/message-archive.json) lists each one with its checksum and the commit that still holds it, and `git show COMMIT:PATH` restores any of them. A short decision note and links to the code, prompt, checks, and measurements are usually enough.

If a transcript helps reviewers, publish it separately as a private or public gist or release attachment after scrubbing **and reading the output yourself**. `tools/scrub.py` handles Codex JSONL and plain-text transcripts:

```bash
python3 tools/scrub.py events.jsonl /path/to/agent-work /tmp/agentmvc-session --deny 'private-host|account-name'
python3 tools/scrub.py notes.txt /path/to/agent-work /tmp/agentmvc-notes --plain --deny 'private-host|account-name'
```

The first command writes `.jsonl` and `.md`; the second writes `.txt`. The scrubber replaces common keys, tokens, emails, usernames, hostnames, and local paths, then refuses to write if recognized sensitive material remains. It cannot identify every private value. Use `--deny` for your own account, organization, host, or project names, inspect the final files, and then link the external copy in the PR. Keep the original transcript local.

Please keep the PR description short: **what improved, what passed, what was measured, and what remains uncertain.** The [methodology](docs/methodology.md) explains the older scored study; it is a record of that experiment, not a mandatory process for every reference improvement.
