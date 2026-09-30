# Clojure track conditions

This track adds two independent paths through the fixed Conduit product:
the [original eight successive prompts](../../../steps/) and one fresh build
using the [unchanged expert-v2 prompt](../../../one-shot-v2-expert/PROMPT.md).
The goal is idiomatic, concise domain code, correct behavior, and a practical
production build. Clojure is a new dated condition; earlier runs stay intact.

## Preparation and isolation

The [stack decision](../../../stacks/clojure/SELECTION.md) explains the selected
libraries and alternatives. A maintainer-authored, product-free scaffold provides
health, lifecycle wiring, development commands and JVM packaging. It supplies
no Conduit models, policies, endpoint handlers, projections, room state or jobs.
Throwaway integration tests prove the environment before its exact files and
toolchain image are frozen. Preparation effort is separate from measured coding.

Each coding session receives a new Codex home with memory and subagents off,
no interactive approvals, and a single writable application directory. An actual
isolation probe must demonstrate denied parent/sibling reads, denied writes to
frozen inputs, and denied host Docker socket access before coding starts.
Dependency commands run inside a workspace-scoped container. The fixed broker
exposes checks and builds without giving the coding agent Docker control.

The Clojure coordinator extends the existing runner through a new adapter;
it does not edit earlier frozen helpers. The adapter and its dependencies are
included in the new fixture hash. PostgreSQL readiness requires TCP from the
start, incorporating the startup correction disclosed in the Go/Python runs.
The prompt, protocol, client and acceptance assertions remain unchanged.

## Coding, gates and review

Sequential step 1 starts from the scaffold. Each following step starts from its
independently checked predecessor, in a fresh coding session. The one-shot also
starts from the scaffold, with no access to sequential work. The measured model
and reasoning setting are recorded in each run; coordinator review is separate.
The first Clojure session records Codex CLI 0.159.0, while the earlier Go/Python
and Rails expert runs record 0.157.1. The model and reasoning setting remain
`gpt-6-sol` and `xhigh`; this CLI version difference is part of the dated condition.

Independent development gates apply at every step; fresh production gates begin
at step 3. The final apps include drafts, durable exports, shared editing,
WebSockets, presence, conflicts and the room cap. Tests and formatting/linting
run through the recorded toolchain. Failed commands and failed attempts remain
part of the evidence. A published measured source is never patched afterward.

Final applications also receive the same common HTTP, favorite-filter and
shared-envelope reviewer probes used for Go/Python. Those observations remain
separate from the frozen acceptance verdict. Necessary repairs become separately
labeled, unscored reference revisions, with their own checks and source hashes.

Fresh read-only readers answer the original twelve comprehension questions after
steps 1 and 6. Reviewers save source-derived answer keys before launching the
readers. These small-app questions can hit a scoring ceiling; they do not establish
comprehension of a million-line codebase.

## Size, runtime and publication

Use the existing `o200k_base` source measurer and Clojure-specific file rules.
Report whole and owned backend tokens/lines, with tests and Markdown separately.
JARs, class files, dependencies and compiler/editor caches are excluded. The
unchanged scaffold is the owned-code baseline, and generated source must be
identified rather than hidden in build-output exclusions.

Production runs an AOT-compiled JVM application. This compiles Clojure namespaces
to JVM bytecode; JVM JIT compilation still occurs at runtime. AOT is not a claim
of a native executable or of eliminating warmup costs. The image and runtime
configuration are part of the implementation and recorded with each result.

Final runtime uses the existing nine HTTP workloads, two reversed-order rounds,
16 virtual users, 3-second warmup and 15-second samples. App and PostgreSQL each
receive 2 CPUs and 1 GiB. Socket checks cover 10, 100 and 500 subscribers, with
20 saves per scenario. These short samples do not establish fully warmed JVM
steady-state performance; preserve that limitation when comparing results.
Step-4 tuning retains the earlier short feedback windows as a separate condition.

Record effort when available, exact source/image identities, all gate results,
reviewer findings, tuning attempts and raw measurements. Full scrubbed transcripts
and compressed raw streams are published as external release assets with hashes;
they stay outside Git. Results and source guides are kept in the repository.

## Reproduction commands

Run these commands from the repository root with the project virtual environment,
Docker, Node.js, zstd and the recorded authenticated Codex CLI available. The
frozen toolchain and browser image IDs must be present locally. For a new,
unfrozen condition, preparation is:

```sh
.venv/bin/python tools/clojure_track_preflight.py
.venv/bin/python tools/clojure_lane.py freeze clojure
```

An existing `stacks/clojure/lane-fixture.json` is immutable. Preserve its inputs,
preflight proof and image identities; `freeze` verifies those identities and
refuses replacement. Rebuilding a different image or changing an input requires
a separately recorded condition. Do not rerun preparation over an active or
published condition.

The two coding paths use independent sessions. The pipeline performs isolation,
coding, publication and independent gates for each checkpoint before advancing:

```sh
.venv/bin/python tools/clojure_lane.py pipeline clojure --through 8
.venv/bin/python tools/clojure_lane.py one-shot clojure
```

Published checkpoints and sessions are retained on a repeated invocation; a
failed independent gate stops progression. Session descriptors live under
`.work/lanes/clojure-PHASE-1/control/session.json`, where `PHASE` is the full
step directory name or `one-shot`. These are execution instructions, not a
claim that either path has completed.

After steps 1 and 6 have independently verified snapshots, prepare fresh readers:

```sh
.venv/bin/python tools/clojure_evidence.py comprehension-prepare --session .work/lanes/clojure-1-build-1/control/session.json
.venv/bin/python tools/clojure_evidence.py comprehension-prepare --session .work/lanes/clojure-6-polish-1/control/session.json
```

A reviewer now derives each twelve-question answer key from its source snapshot,
saves it outside the reader workspace, and records its hash and save time in
`key-preparation.json` before viewing any reader answer. Using keys saved at the
following paths, launch each reader once:

```sh
.venv/bin/python tools/clojure_evidence.py comprehension-run --session .work/lanes/clojure-1-build-1/control/session.json --answer-key .work/clojure-answer-keys/after-1-build.md
.venv/bin/python tools/clojure_evidence.py comprehension-run --session .work/lanes/clojure-6-polish-1/control/session.json --answer-key .work/clojure-answer-keys/after-6-polish.md
```

Grade the answers separately against those saved keys, with source references
for all twelve scores. Reader evidence goes under `comprehension/`; release
validation requires `key-preparation.json` and `grades.json` with the timestamps
and hashes checked by `reader_graded` in `tools/clojure_artifacts.py`.

After both final applications have passed their independent gates, run the
supplemental probes on their exact published snapshots:

```sh
.venv/bin/python tools/clojure_evidence.py parity
.venv/bin/python tools/clojure_evidence.py share --session .work/lanes/clojure-8-live-editing-1/control/session.json
.venv/bin/python tools/clojure_evidence.py share --session .work/lanes/clojure-one-shot-1/control/session.json
```

Wait until all measured coding processes have stopped before runtime measurement
or artifact export. The measured runtime command selects the two fixed Clojure
finals; it preserves the first runtime directory and its failures:

```sh
.venv/bin/python tools/clojure_evidence.py runtime --condition measured
.venv/bin/python tools/clojure_evidence.py validate --condition measured
.venv/bin/python tools/clojure_artifacts.py export-feedback
.venv/bin/python tools/clojure_artifacts.py export-checks
.venv/bin/python tools/clojure_artifacts.py inspect
.venv/bin/python tools/clojure_artifacts.py package v1
.venv/bin/python tools/clojure_artifacts.py verify v1
```

Packaging requires nine verified coding sessions, two graded readers, the
reviewer evidence for selected finals, and 72 measured HTTP raw streams. Repairs
remain unscored references; reference runtime requires explicit `--session`
arguments with `--condition reference`. Choose a new artifact version for a new
package. Export and packaging validate scrubbed evidence and hashes locally;
they do not upload assets. Archives are written under `.work/clojure-artifacts/`
and their manifest under this results directory.

The two published unscored repairs use `reference-1`. Their repeated runtime
selects both source-bound sessions explicitly:

```sh
.venv/bin/python tools/clojure_evidence.py runtime --condition reference --session .work/lanes/clojure-8-live-editing-reference-1/control/session.json --session .work/lanes/clojure-one-shot-reference-1/control/session.json
.venv/bin/python tools/clojure_evidence.py validate --condition reference
```

The final package retains 72 original and 72 reference HTTP raw streams, plus
the tuning feedback, socket results, transcripts and failed check attempts.
Reference editing time is excluded from measured agent effort. See the
[sequential repair record](8-live-editing/reference-1/REPAIRS.md) and
[one-shot repair record](ONE-SHOT-REFERENCE-REPAIRS.md) for scope and validation.

## Preserved preparation findings

The [preparation attempts](preflight-attempts/) retain an initial syntax error
in a throwaway test and two later source-hash rejections while preparation was
still changing. The initial advisory scan found older Jetty and Bouncy Castle
transitives. The final scaffold pins Jetty 12.1.13 and Bouncy Castle 1.86;
[final preflight](preflight.json) verified the coherent 90-artifact runtime graph
and recorded zero OSV findings at scan time. These preparation results do not
count as measured application coding or as a general security guarantee.
