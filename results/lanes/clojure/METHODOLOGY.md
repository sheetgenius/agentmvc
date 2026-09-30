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
