# Docs

- [Methodology](methodology.md): the app, the agents, the steps, and how each thing is measured.
- [One-shot comparison](one-shot-contract.md): the full-spec backend experiment and its [prepared workspaces](../one-shot/README.md).
- [Expert-guided tracks](../one-shot-v2-expert/README.md): the shared safe-evolution prompt with separate [TypeScript results](../results/one-shot-v2-typescript-expert/README.md) and [Phoenix results](../results/one-shot-v2-phoenix-expert/pilot-1/README.md). The [Phoenix design notes](phoenix-expert-track.md) record its setup. Guided results are reported separately from the earlier one-shots.
- **Findings**, with hypotheses recorded before the applicable benchmark, scan, and reading steps:
  - [Size](findings/size.md): how much code the same app takes, step by step;
  - [Change cost](findings/change-cost.md): what each step cost in code and agent effort;
  - [Speed](findings/speed.md): benchmarks before and after tuning, and the noise;
  - [Security](findings/security.md): what each framework protects for free, and what hardening took;
  - [Comprehension](findings/comprehension.md): how well a fresh agent reads each codebase;
  - [Polish](findings/polish.md): what a free polish pass changed;
  - [Background jobs](findings/background-jobs.md): what a durable job-backed feature cost;
  - [Live editing](findings/live-editing.md): what the three real-time implementations cost and where their designs differ.
- [Caveats](caveats.md): what these results can and can't tell you.
- [Research log](research-log.md): the session in time order, including every fault.
