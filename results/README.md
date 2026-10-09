# Results

Every experiment in AgentMVC, grouped by its setup. A setup fixes the model, prompt, stack guidance, starting scaffold, build protocol and checks. **Compare the matched groups each page identifies, and compare speed only within one benchmark session.** [How to read the results](../docs/cohorts.md) explains why, and the [cohort index](cohorts.json) records the identity of every session.

## Measured builds

Each measured coding session is preserved exactly as the agent left it. Every measured coding session so far used `gpt-6-sol` at `xhigh` reasoning through the Codex CLI: version 0.159.0 for Clojure, 0.157.1 for everything else.

| Setup | How the app was built | Stacks | Coding sessions | What sets it apart |
| --- | --- | --- | ---: | --- |
| [Expert v2, matched session](v2-expert-symmetry/README.md) | one session | Rails, Phoenix, AdonisJS | 3 | Shared v2 prompt, frozen expert guidance per stack, and speed measured together in one paired session. Track notes: [AdonisJS](one-shot-v2-typescript-expert/README.md), [Phoenix](one-shot-v2-phoenix-expert/pilot-1/README.md) |
| Expert v2, lane runner: [Go and Python](lanes/README.md), [Clojure](lanes/clojure/README.md) | one session | Go, Python, Clojure | 3 | The same prompt and approach, run through the lane runner; Go and Python were benchmarked together, Clojure separately |
| Prepared lanes: [Go and Python](lanes/README.md), [Clojure](lanes/clojure/README.md) | eight steps | Go, Python, Clojure | 24 | The original eight prompts from supplied scaffolds; Clojure ran on the newer CLI |
| v2 pilots: [Servant](one-shot-v2-servant/README.md), [AdonisJS](one-shot-v2-typescript/README.md) | one session | Servant, AdonisJS | 2 | The v2 prompt without expert guidance |
| [Semantic density](one-shot-semantic-density/README.md) | one session | Rails, Phoenix, Loco | 3 | An earlier prompt that named Rails as its model |
| [IHP track](one-shot-ihp/README.md) | one session | IHP | 3 | The semantic-density prompt, on a Nix toolchain |
| [First one-shot](one-shot/README.md) | one session | Rails, Phoenix, Loco | 3 | The earliest prompt; the Loco agent bypassed Loco for plain Axum |
| [Original eight steps](../docs/eight-step-study.md) | eight steps | Rails, Phoenix, Loco | 24 | Agents generated their own scaffolds |

An eight-step setup counts one coding session per step, so 24 sessions build three apps.

## Reviewed versions

Later repairs and improvements are published beside the build they started from, with their own checks. They have no comparable coding effort, and their numbers never replace the original build's. Each setup's page links its reviewed versions, and the [README](../README.md#explore-the-code) lists the current one for each language.

## Diagnostics and experiments

These sit outside the measured setups:

- [Compiled Conduit on PostgreSQL](ruby-compile/roundhouse-spinel-conduit-pg-20260930/README.md): the Rails reviewed version compiled to a native binary with locally patched Roundhouse and Spinel. It passes the production gate and reviewer probe, and is benchmarked in its own session.
- [Compiled Conduit on upstream heads](ruby-compile/roundhouse-spinel-conduit-pg-20261009/README.md): v8 uses Ruby 4.0.7, with 10 local Roundhouse patches and none to Spinel. It passes the production gate and common HTTP probe, including a Ruby 4.0.7 Rails control. No timing was run on the shared host.
- [Roundhouse + Spinel feasibility](ruby-compile/roundhouse-spinel-v2026.9.18/README.md): the earlier compatibility probe against the September release, with no throughput result.
- [IHP with an expert brief](one-shot-ihp/README.md#guided-diagnostic-and-integrity): a guided IHP run with a different prompt, excluded from the three scored IHP builds.
- [Framework-native optimization](../docs/shine-track.md): labeled diagnostics that push finished apps further.

## Where the speed numbers come from

Each setup measured speed in its own session on one shared workstation, with the app and PostgreSQL each limited to 2 CPUs and 1 GiB. The Rails, Phoenix and AdonisJS builds were measured together; Go and Python together; Clojure separately; compiled Rails separately. Treat speed across those sessions as indicative only. The apps also differ in how they use the two CPUs: the Rails and AdonisJS builds run as one process, while Phoenix uses both cores.

## Raw data and transcripts

Small summaries and records live in Git. Agent transcripts, agent final reports and comprehension answers are kept out of the working tree:

- **Earlier transcripts** live in Git history. [`message-archive.json`](message-archive.json) lists each with its checksum and the commit that holds it.
- **Newer transcripts and per-request HTTP streams** are release downloads: [Go and Python](https://github.com/sheetgenius/agentmvc/releases/tag/go-python-lanes-v1), [Clojure](https://github.com/sheetgenius/agentmvc/releases/tag/clojure-lane-v1), [expert-guided](raw-data-v2-expert/README.md), the [paired three-stack session](https://github.com/sheetgenius/agentmvc/releases/tag/raw-data-v2-expert-symmetry) and the [earlier raw runs](raw-data/README.md). Each has a checksum index.

The files at the top of this folder belong to the original eight-step study:

- **`sizes.json`:** each stack's code size after every step, and what each step added or changed. Generated by `tools/report.py`.
- **`charts/`:** the size charts, as SVG and PNG. Generated by `tools/report.py`.
- **`speed/<step>-<stack>.json`:** benchmarks of production images (`tools/bench/`): requests per second, latency percentiles, SQL statements per request and peak memory for every scenario, plus image size, cold start and idle memory.
  - `3-package-*`, `4-tune-*` and `6-polish-*` are the images from those steps; `*-rerun-*` are the same images benchmarked again later.
  - `sensitivity/` holds Rails with two Puma workers, a setting no agent chose, and its same-session control.
  - Runs from different sessions drifted on the shared machine, so compare within a session; see [the speed findings](../docs/findings/speed.md).
- **`security/<step>-<stack>.json`:** scans of production images (`tools/security/`): the 13 black-box checks, OSV-Scanner on the lockfile, and the stack's analyzer.
