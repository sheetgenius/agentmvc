# Documentation

## Understand the results

- [All results](../results/README.md): every experiment, grouped by setup, with links to code and measurements.
- [How to read the results](cohorts.md): why numbers belong to their setup, and how the cohort index records each session.
- [Glossary](glossary.md): the handful of terms the result pages use.

## Run and contribute

- [Running AgentMVC](running.md): try a finished app, reproduce a result, or run a new experiment.
- [Contributing](../CONTRIBUTING.md): improve a reviewed version, add a stack, or submit a practitioner brief ([briefs](../briefs/README.md)).
- [Pitfalls](pitfalls.md): what went wrong in earlier runs, and what to do instead.
- [Tools](../tools/README.md): every runner, check and probe, by job.

## What's next

- [Experiment v3](experiment-v3.md): the proposed next experiment: one-shot builds, one run per stack, of a two-instance Conduit with semantic search on pgvector.
- [Baseline refresh](baseline-refresh.md): prompt and harness fixes to make before the next measured runs.
- [Semantic-density workshop](semantic-density-workshop.md): the design notes behind the later experiments.

## How each experiment was run

- [The single-session contract](one-shot-contract.md) and its [prepared workspaces](../one-shot/README.md).
- [Expert-guided tracks](../one-shot-v2-expert/README.md), with design notes for [Phoenix](phoenix-expert-track.md) and [TypeScript](typescript-track.md).
- [Prepared lanes](../results/lanes/METHODOLOGY.md) for Go and Python, and the [Clojure track](../results/lanes/clojure/METHODOLOGY.md).
- [Framework-native optimization](shine-track.md): labeled diagnostics that push finished apps further.

## The original eight-step study

- [The study page](eight-step-study.md), with its results table and prompts.
- [Methodology](methodology.md) and [caveats](caveats.md).
- Findings, with hypotheses recorded before each measured step: [size](findings/size.md), [change cost](findings/change-cost.md), [speed](findings/speed.md), [security](findings/security.md), [comprehension](findings/comprehension.md), [polish](findings/polish.md), [background jobs](findings/background-jobs.md) and [live editing](findings/live-editing.md).
- [Research log](research-log.md): the study in time order, including every fault.

## Repository map

```
spec/                        the product contract: RealWorld spec, Hurl suites and the three added features
frontend/                    the shared Lit editor, its browser tests, and Node packages the harness uses
one-shot/, one-shot-v2*/     frozen prompts, environments and fixtures for each single-session setup
steps/                       the eight sequential prompts and the comprehension prompt
stacks/<stack>/              stack.json, the product-free scaffold, and each step's code for sequential lanes
briefs/                      the practitioner brief protocol, template and seeds
comprehension/               reader questions, answer keys and grades
results/                     one folder per setup, the cohort index, and the message archive list
docs/                        how to read and run the experiments, the next experiment, and study records
tools/                       runners, independent checks, reviewer probes, measurement and reports
```
