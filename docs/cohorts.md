# How to read the results

Every number in AgentMVC belongs to a setup (a "condition"): the model, prompt, stack guidance, starting scaffold, build protocol and checks that produced it. This page explains how setups are recorded and which comparisons they support. The [glossary](glossary.md) defines the terms.

## The cohort index

The [cohort index](../results/cohorts.json) makes recorded model, prompt and fixture identities visible across the historical runs. It is a navigation index over existing evidence. Its `series` labels describe where results live; they do not assert that every entry in a series is a matched experiment.

Every currently indexed measured coding session records **`gpt-6-sol` with `xhigh` reasoning**. The original runs and later Go/Python and expert pilots record Codex CLI 0.157.1; Clojure records 0.159.0. There is no measured `gpt-6.1-sol` comparison in this history. Agent identity comes from each recorded run, never from a current `stack.json` setting.

## The comparison tuple

Read a result as this combination, rather than as a language or model score:

| Dimension | Evidence to retain and compare |
| --- | --- |
| Stack and starting point | Framework/library assembly, product-free scaffold, per-stack guidance and predecessor source for a sequential step |
| Build protocol | Eight sequential prompts, one full-product prompt, or a read-only comprehension task; identify the phase and repeat |
| Agent | Recorded model, reasoning setting and CLI version |
| Inputs and execution | Prompt hash, base and effective fixture identities, toolchain/browser images and isolation/launch record |
| Output role | Measured coding output, unscored repaired reference, infrastructure preflight, reader or other diagnostic |
| Evaluated source and gate | Exact available source identity, independent development/production verdicts and the gate's scope |

Hold the other dimensions fixed when asking what a model change caused. Sequential effort includes intermediate work and repeated gates; a one-shot has all features from the outset. A shared expert prompt hash also does not imply shared scaffolds, guidance or adapters. The [Go one-shot adapter record](../results/one-shot-v2-go-expert/pilot-1/effective-fixture.json) and [Clojure adapter record](../results/lanes/clojure/8-live-editing/effective-fixture.json) illustrate why the effective fixture matters.

## What is indexed

The deterministic [generator](../tools/cohort_index.py) reads entries in `stacks/*/runs.json`, result `run.json` files, infrastructure `preflight.json` files and numbered reference directories. It does not modify those files or start any coding, build, browser or benchmark process. Individual runtime trials and every check attempt remain in their existing reports; this index does not turn them into extra coding sessions.

| Role | Meaning |
| --- | --- |
| `measured-coding` | A timed coding session with a recorded run. This includes exploratory pilots and repeated IHP builds; the role does not imply identical conditions or successful gates. |
| `reader` | A read-only comprehension session, with its own model and grading evidence. |
| `reference` | A separately preserved maintainer repair. Its model/CLI remain unknown unless separately recorded; it never inherits the parent's agent identity or coding effort. |
| `preflight` | Infrastructure preparation, including the excluded IHP agent probes and retained failed Clojure attempts. |
| `diagnostic` | A separately labeled experiment: the IHP guided coding run, the Ruby compiler feasibility probe, or the compiled Rails variant built with patched Roundhouse and Spinel. The guided run retains its recorded model and distinct prompt/fixture; it is excluded from the three scored IHP builds. |

Each entry links its `record`, results directory, prompt, fixture, published source/manifest, and available gate evidence. Paths are relative to the repository root. A suffix such as `#/9` is a JSON Pointer into an array; nested gate and grade pointers identify their recorded fields. Stack, protocol and role can be classified from directory names. Model, reasoning and CLI are copied only from that entry's historical run record, preserving the original spelling.

**`null` means unknown or no matching published link. Two unknown values do not establish a match.** The original eight-step records lack whole-source hashes and most early fixture hashes. Some early one-shot reports retain local workdir references and source inventories without a published source snapshot. The index leaves those gaps visible; it does not hash today's source and call it a historical identity. Prompt links are included only when the current file bytes match the recorded prompt hash; fixture links match the recorded manifest identity. Hashes must be interpreted with their manifest's file scope.

Gate status is taken from gate records, not from a coding process's exit code. A passing frozen gate says what that gate checked. Supplemental review can still find missing behavior, and a reference can pass or fail independently of its parent. Read the linked evidence for those distinctions. A reference created before publication can appear with unknown source and no verdict until its evidence is published and the index is regenerated.

## Refreshing or querying the index

From the repository root:

```sh
python3 tools/cohort_index.py
python3 tools/cohort_index.py --check
```

For example, list measured coding identities without mixing in repairs or readers:

```sh
python3 - <<'PY'
import json
from pathlib import Path
for row in json.loads(Path("results/cohorts.json").read_text())["entries"]:
    if row["role"] == "measured-coding":
        print(row["stack"], row["protocol"], row["model"], row["reasoning"],
              row["condition"], row["record"])
PY
```

## A future GPT-6.1 cohort

Two useful experiments answer different questions:

1. **Matched model comparison:** replay selected archived prompts, scaffolds, guidance, checks and execution conditions with `gpt-6.1-sol`, keeping reasoning fixed and recording any unavoidable CLI or environment drift. Fresh repetitions are needed to understand run variability. A CLI change alongside the model must remain visible as another changed dimension.
2. **Refreshed baseline:** streamline prompts and repair harness friction, then launch fresh GPT-6.1 builds under a new fixture and result root. This measures the combined revised condition. To isolate the model within those revised inputs, run both models on the same new fixture.

Preserve existing result roots and their failed attempts. Record the new cohort's model and conditions in its own launch/run metadata. The [baseline refresh assessment](baseline-refresh.md) identifies the proposed prompt and harness work; neither document launches a GPT-6.1 run.

[Experiment v3](experiment-v3.md) proposes the next cohort. It changes the contract to two instances, splits each stack's guidance into a neutral environment and an optional practitioner brief, and runs both arms on the same new fixture. Its results form a new baseline and are not pooled with the conditions above.
