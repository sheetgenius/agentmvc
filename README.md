# AgentMVC

**One app, built and evolved by AI agents in every stack, and measured the same way.**

AgentMVC gives an AI coding agent one spec and one prompt, and has it build the same backend in each stack: the [RealWorld](https://github.com/realworld-apps/realworld) "Conduit" API. Each implementation then goes through the seven steps a real product does:
1. build it;
2. add a feature;
3. package it for production;
4. make it fast;
5. harden it;
6. polish it;
7. add a feature that runs in a background job.

Every step is checked against the same acceptance suite. Every step is measured the same way: code size, the cost of each change, speed, security, and how well a fresh agent can read the result.

[TodoMVC](https://todomvc.com) let developers compare frameworks by reading the same app. AgentMVC compares stacks by what agents build in them: how much code the same product takes, and what that code buys.

<!-- stats:start -->
| | [Rails](stacks/rails/) (Ruby) | [Phoenix](stacks/phoenix/) (Elixir) | [Loco](stacks/loco/) (Rust) |
| --- | ---: | ---: | ---: |
| Code an agent reads, after the last step (tokens) | 4,847 | 9,062 (1.87×) | 12,884 (2.66×) |
| Lines of code, after the last step | 579 | 1,045 (1.80×) | 1,928 (3.33×) |
| Code to add drafts, step 2 (tokens) | 632 | 1,190 (1.88×) | 1,689 (2.67×) |
| Code to add a background job, step 7 (tokens) | 526 | 953 (1.81×) | 1,566 (2.98×) |
| Article list after tuning, median of runs (req/s) | 259 | 4,990 (19×) | 5,403 (21×) |
| Peak memory under load, after tuning | 128 MB | 177 MB | 104 MB |
| Docker image | 334 MB | 165 MB | 140 MB |
| Cold start | 1.2 s | 1.2 s | 0.3 s |
| Security checks passed, before → after hardening (of 13) | 11 → 13 | 10 → 13 | 11 → 13 |
| Fresh agent's comprehension score, after steps 1 and 6 (of 12) | 12 · 11.5 | 11.5 · 12 | 11.5 · 11.5 |
| Agent effort, all steps (tokens, wall-clock) | 648k tokens, 71 min | 657k tokens (1.01×), 73 min (1.02×) | 852k tokens (1.31×), 88 min (1.24×) |
<!-- stats:end -->

Code size is counted in LLM tokens (`o200k`) and lines, over the application source an agent would read. Ratios are relative to Rails. Speed was measured on one machine, with each app and its database limited to 2 CPUs and 1 GB, under 16 concurrent users. Per-step detail is in [`stacks/`](stacks/) and [the findings](docs/findings/).

![Code size of each stack after every step](results/charts/growth.svg)

![Each stack's size relative to Rails after every step](results/charts/ratio.svg)

## What the numbers show

- **The same app took 1.9× the code in Phoenix and 2.7× in Rust.**
  - After all seven steps, Phoenix needs 1.87× Rails' tokens and Loco 2.66×.
  - In lines, Loco is 3.3× Rails, because `rustfmt` lays code out vertically.
- **The gap held as the app grew.** From step 1 to step 7, Rails grew 38%, and Phoenix and Loco 46% each. Phoenix stayed within 1.76–1.93× Rails, and Loco within 2.51–2.76×. The ratio moved most at the tuning step, where batching queries took far more code outside Rails, and less elsewhere. Over this range, each stack grew roughly in proportion to Rails, not faster and faster. The app only grew 38%, though, which is too narrow to say how the gap behaves in a much larger codebase. [Size →](docs/findings/size.md)
- **Every feature cost the same multiple.** Adding drafts took 1.88× Rails' code in Phoenix and 2.67× in Loco. Adding a background-job feature took 1.81× and 2.98×. [Change cost →](docs/findings/change-cost.md)
- **Agent effort grew less than code did.** Over the seven steps, Phoenix took about the same agent tokens and time as Rails, and Loco 1.3× the tokens and 1.2× the time. Every step passed in every stack.
- **Phoenix and Loco were about 20× faster on the same 2 CPUs.**
  - Every first draft had the same N+1 queries. Once each agent fixed them, Phoenix and Loco served 19× and 21× Rails' article-list throughput.
  - Rails' fix was the smallest.
  - Rails ran a single Puma process. Two worker processes gain it about 1.7×. [Speed →](docs/findings/speed.md)
- **Reading was closer than writing.** Fresh agents scored 11.5–12 out of 12 on questions about every codebase, reading only 1.2–1.75× Rails' input. [Comprehension →](docs/findings/comprehension.md)
- **Security reached parity by different routes:** Rails' built-in features, Loco's types, and a library in Phoenix. [Security →](docs/findings/security.md)
- **A free polish pass shrank nothing.** Every agent moved rules to where its stack expects them, and every codebase changed size by less than 1%. [Polish →](docs/findings/polish.md)

## The app and the steps

The app is the RealWorld "Conduit" backend: users, profiles, follows, articles, comments, favorites and tags. It's defined by the [pinned spec](spec/) and its public Hurl acceptance suite of 154 requests, run unmodified. Two features were added for AgentMVC and validated before any agent saw them: [drafts](spec/features/drafts/drafts.md) (47 more requests) and [exports built in a background job](spec/features/exports/exports.md) (17 more).

| Step | The agent is asked to | Prompt |
| --- | --- | --- |
| 1 | Build the app from the spec, clean, terse and idiomatic | [`1-build`](steps/1-build.md) |
| 2 | Add drafts, publishing and edit conflicts | [`2-add-drafts`](steps/2-add-drafts.md) |
| 3 | Package it for production, with a check against the production image | [`3-package`](steps/3-package.md) |
| 4 | Make it fast, given its benchmark results | [`4-tune`](steps/4-tune.md) |
| 5 | Harden it, given its security scan | [`5-harden`](steps/5-harden.md) |
| 6 | Polish it, with free rein, in up to three passes | [`6-polish`](steps/6-polish.md) |
| 7 | Add article exports, built in a durable background job | [`7-add-background-job`](steps/7-add-background-job.md) |

After steps 1 and 6, a fresh, read-only agent answers [12 questions about the domain](comprehension/questions.md) from the code alone.

## How it's run and measured

- **One agent per stack per step, from a byte-identical prompt.** The only stack-specific text is a short [`ENVIRONMENT.md`](stacks/rails/ENVIRONMENT.md). No agent knows about the other stacks.
- **Every step is verified** by rerunning the agent's own `bin/check`: the acceptance suite, the formatter and the linter. From step 3, `bin/check-production` runs too, against the production image. The results are recorded in each stack's `runs.json`.
- **Code size** counts the application source only. Tests, lockfiles, dependencies and generated schema are left out. [`tools/measure.py`](tools/measure.py) reads each stack's rules from its `stack.json`.
- **Speed** is measured with k6 against each production image, with SQL statements counted per request.
- **Security** is 13 black-box checks, plus OSV-Scanner and the stack's own analyzer where one exists.
- **Every agent session is published,** with its report and scrubbed transcript, next to the code in [`stacks/`](stacks/).

[The methodology](docs/methodology.md) covers the details. [The research log](docs/research-log.md) records what went wrong along the way, and how it was handled.

## Add a stack

Go, Django, Laravel, Spring, .NET, Gleam: any stack can join. An implementation is built by an agent from the shared prompts, never by hand. That's what makes the numbers comparable.

1. Add `stacks/<name>/stack.json` and `ENVIRONMENT.md`, starting from an existing stack.
2. Run the steps with [`tools/run-step.py`](tools/run-step.py). It records the session and scrubs the transcript.
3. Verify each step with [`tools/check.sh`](tools/check.sh), then run [`tools/report.py`](tools/report.py) to update the tables and charts.
4. Open a pull request. Steps 1 and 2 are enough to join the table; all seven complete the picture.

[CONTRIBUTING.md](CONTRIBUTING.md) has the full checklist. It also covers other ways to help: rerunning a stack with another model, grading the comprehension answers as a second reviewer, or proposing a new step.

## Why this exists

AgentMVC started as R&D at [BitterClip](https://bitterclip.com), a Rails product with about 3 million tokens of application code, more than three times a 1-million-token context window. Its founder, [@ruemic](https://x.com/ruemic), kept hearing that everything should move to Rust because agents would do all the reading and writing. When agents do the reading, what matters is how much of a product fits in their context, so the question became measurable: how much more code does the same product take in another stack, and what does it buy?

## Caveats

- **One model, and one run per stack per step.** Small differences are noise; the size of a gap is more reliable than its exact value.
- **RealWorld is a small CRUD API.** It has no real-time features or media processing.
- **Speed numbers come from one shared workstation.** Identical images varied by up to 1.5× between runs, so the table uses the median of several runs.
- **One reviewer wrote the feature specs, security checks and answer keys.** The hypotheses were pre-registered, and every answer key was written before grading.

The full list is in [docs/caveats.md](docs/caveats.md).

## Reproduce

```bash
pip install -r tools/requirements.txt
python3 tools/measure.py rails                   # code size at every step
python3 tools/report.py                          # rebuild results/, the charts and the table above
tools/check.sh rails 7-add-background-job        # rerun a step's checks (needs Docker and the stack's toolchain)
tools/bench/run.sh rails 4-tune                  # benchmark a step's production image
tools/security/scan.sh rails 5-harden            # scan it
```

## Repository map

```
spec/                 the app: RealWorld's API spec and Hurl suite (MIT), plus the two added features
steps/                the seven prompts and the comprehension prompt, identical for every stack
stacks/<stack>/       stack.json, ENVIRONMENT.md, scaffold/ (generator output), the code after each step,
                      reports/, transcripts/ and runs.json
comprehension/        questions, answer keys, grades and every answer
results/              sizes, benchmarks, security scans and charts
docs/                 methodology, findings, caveats and the research log
tools/                run a step, check it, measure, benchmark, scan, scrub a transcript, rebuild the report
```

## License

MIT; see [LICENSE](LICENSE). The RealWorld spec in `spec/` is MIT-licensed by its authors; see [spec/LICENSE](spec/LICENSE).
