# Go and Python: prepared-scaffold lanes

These runs extend the study with Go and Python/Django Ninja under a **prepared-scaffold condition**. The coordinator supplies a product-free scaffold, warms dependencies, and verifies the toolchain before starting each measured coding session. Scaffold preparation and preflight are outside the coding measurements. Go is supplied a Huma/chi scaffold; results must name the libraries the measured implementation actually uses, since accepting the scaffold does not establish that it retained Huma. This differs from an original condition in which an agent generates its own initial application. It must remain visible in any comparison.

This page describes the evidence procedure. It does not yet claim a completed eight-step run, a passed reviewer probe, a comprehension score, or a runtime result. Published JSON records and source snapshots establish which observations have finished.

## Inputs and session boundaries

Each sequential lane receives the exact bytes of the original [eight prompts](../../steps/). Each new step starts in a fresh isolated session from the independently checked preceding source snapshot. The Go and Python expert one-shot sessions start independently from their respective product-free scaffolds and receive the same unchanged [expert-v2 prompt](../../one-shot-v2-expert/PROMPT.md). A one-shot session receives no sequential implementation.

Stack-specific `ENVIRONMENT.md`, scaffold, runtime commands, toolchain image, and dependency preparation are separate supplied inputs. They are frozen and recorded alongside the shared prompt; “same prompt” does not mean the full environments are identical. Environment instructions adapt the historical Docker commands to the fixed coordinator broker. Per-stack fixture manifests are in [`stacks/go/`](../../stacks/go/) and [`stacks/python/`](../../stacks/python/); [Go preflight](go/preflight.json) and [Python preflight](python/preflight.json) record preparation evidence.

The agent receives its application workspace and applicable specification, client, and checks. Frozen files are read-only; the session has a fresh Codex home with memories, plugins, apps, and subagents disabled. Parent and sibling workspaces and the host Docker socket are denied. An independent isolation probe records what was tested. The coordinator runs Docker through the session broker, with Docker operations serialized by the shared resource lock.

Each measured session publishes its prompt hash, fixture hash, model, reasoning setting, token usage, elapsed time, check attempts, source manifest, application-size inventory, and independent verification record. Application size uses the supplied scaffold as its baseline. Tests and Markdown are reported separately; the historical line measurer may count Go block comments and Python docstrings as owned code. Token costs depend on prompt caching, and elapsed coding time includes waits for shared coordinator resources.

The coordinator's separate `lane_launch.py` adapter waits for the Docker resource lock before starting the measured clock. This addresses an observed Go step-4 launch timeout: the frozen broker waited for another lane's operation before binding HTTP, exceeding the launcher's ten-second deadline. That attempt started no coding process and remains recorded. The adapter can retry only this specific startup failure while both the transcript and home session directory are absent; it never replays a measured coding session. Queue duration and adapter identity are published separately. Frozen prompts, broker behavior and workspaces remain unchanged.

## Acceptance and reviewer parity

The independent development check runs the applicable frozen acceptance checks, lint, and tests. From step 3, the independent production check builds the recorded source and starts a fresh database and production container. At step 8 and in each expert one-shot, the frozen checks include the shared HTTP, security, live WebSocket, and browser suites. No agent-authored `bin/check` determines these independent results.

[`tools/lane_evidence.py`](../../tools/lane_evidence.py) adds a reviewer parity record against the **unchanged, already published and independently gated source**. It reuses `lane_check.production_app`, with the fixed three-variable application environment (`DATABASE_URL`, `SECRET_KEY_BASE`, `PORT`), fresh PostgreSQL, and 2 CPU / 1 GiB limits on both app and database. It reruns the frozen production gates and the exact [common HTTP reviewer probe](../../tools/reviewer_common_http_probe.py), including its concurrent-login diagnostic.

Full reviewer parity requires all **21 contract cases and 3 additional quality cases** to be observed and pass, plus the frozen production gates. The quality cases remain supplemental diagnostics rather than retrospectively added requirements in the measured prompt. A shortened probe caused by an earlier failure is incomplete. Socket contract parity comes from the shared frozen live suites; there is no new stack-specific socket probe. Additional source-driven diagnostics, if needed, must be separately labeled.

Parity output is stored under each session's `reviewer-parity/` directory, with scrubbed logs, probe assertions, source/image hashes, and reviewer-tool hashes.

Reviewer startup uses the separately hashed `lane_review.py` adapter to require PostgreSQL TCP readiness. The original Unix-socket check could accept PostgreSQL’s temporary initialization server before application TCP connections were possible; that caused an observed independent Go step-3 startup failure. The final HTTP runner applies the same TCP-only readiness correction around the unchanged benchmark script, whose one-second delay otherwise only masks the race. Workloads, timing windows, measured application source, and frozen agent inputs are unchanged. Socket rounds use the corrected independent production lifecycle. Existing evidence is preserved. A failure is not repaired inside the measured source or silently replaced.

## Repeated final runtime

Final runtime is separate from implementation feedback. The tuning feedback benchmark uses **1-second warmup and 3-second measurement**. The final repeated HTTP benchmark uses the unchanged [benchmark](../../tools/bench/bench.py) with **16 virtual users, 3-second warmup, and 15-second measurement** for all nine existing scenarios: anonymous list, signed-in list, tag-filtered list, feed, article, comments, tags, favorite toggle, and article creation. Both app and database receive 2 CPU / 1 GiB; no extra application environment is supplied.

After all four original final applications pass independent and frozen production gates, the coordinator records their supplemental reviewer probes and runs two serialized measured rounds in this order. Supplemental probe failures remain visible and do not exclude an otherwise gated original application:

| Round | Application order | Workload order within each application |
| --- | --- | --- |
| 1 | Go step 8; Python step 8; Go expert one-shot; Python expert one-shot | HTTP, then sockets |
| 2 | Python expert one-shot; Go expert one-shot; Python step 8; Go step 8 | Sockets, then HTTP |

The socket round reuses the exact [`live-load.mjs`](../../tools/live-load.mjs) workload through the existing expert [runtime helper](../../tools/one_shot_live_bench.py): 10, 100, and 500 subscribers, with 20 saves per scenario. The 500 subscribers span five articles to respect the room cap. The recorded assertions require zero missing, duplicate, or regressed revisions. Each socket round uses a fresh production app and database.

Original measured runtime records belong in `runtime/measured/`, with source/image identities, tool hashes, nine k6 summaries per HTTP round, socket samples, and 18 compressed warmup/measurement streams per HTTP round (**144 raw streams** across four applications and two rounds). Compressed streams are checked with the existing decompression and sensitive-marker validator before publication, and their SHA-256 hashes are rechecked by `validate`. Synthetic seed credentials remain outside published evidence. Summary/log text uses the existing scrubber. The separate `lane_continue.py` publication adapter validates decoded JSON strings and Markdown, avoiding false email matches caused by JSON newline escapes next to Python decorators; it changes no coding input or scrub pattern.

The HTTP harness uses its existing `postgres:17-alpine` and `grafana/k6:latest` references; their actual image IDs are recorded. Independent production/socket runs use the lane's digest-pinned PostgreSQL image. Host load and the benchmark's CPU observations are retained. Its `foreign_container_cpu_percent_max` can include the unnamed k6 generator, so that metric does not establish unrelated host CPU use. The reused socket helper's legacy container-name filter can also count the lane database in its foreign-container CPU metric. Two rounds on a shared host describe the recorded workload and do not establish a causal ranking of languages or frameworks.

## Comprehension after steps 1 and 6

The reader receives the exact original [`steps/comprehension.md`](../../steps/comprehension.md), containing the [12 questions](../../comprehension/questions.md), and only the files in the published whole-app source inventory. It gets a new read-only application copy and fresh Codex home, with memories and network access disabled. A separate probe verifies source reads, denied writes and denied reads outside the copy. The configured reader model is the lane's original `gpt-6-sol` with `xhigh` reasoning; it is a new session, with no coding history.

A reviewer must write and save an answer key from the source **before launching the reader or consulting its answers**. The helper archives the key's hash before launch and never exposes the key to the reader. The reader's answer, scrubbed transcript, token usage, source identity, and prompt identity are retained in `comprehension/`. Grading is a separate source-supported review: 1 point for correct behavior and location, 0.5 for correct behavior with wrong or missing location, and 0 otherwise. No comprehension score exists until that review is published. The historical questions are close to their scoring ceiling on small applications; they do not measure comprehension of a large system.

## Coordinator commands

Run from the repository root after the relevant coding sessions and independent checks have finished. These commands create evidence; the examples are not completion claims.

```sh
.venv/bin/python tools/lane_evidence.py parity
.venv/bin/python tools/lane_evidence.py runtime
.venv/bin/python tools/lane_evidence.py validate

.venv/bin/python tools/lane_evidence.py comprehension-prepare \
  --session "$PWD/.work/lanes/go-1-build-1/control/session.json"
# Review the source and save the answer key before starting the reader.
.venv/bin/python tools/lane_evidence.py comprehension-run \
  --session "$PWD/.work/lanes/go-1-build-1/control/session.json" \
  --answer-key /absolute/path/to/source-derived-answer-key.md
```

`parity --session /absolute/path/to/session.json` evaluates one completed final session. The default `runtime --condition measured` always uses the fixed four original final applications and retains their supplemental parity outcomes. A separately labeled `runtime --condition reference --session PATH ...` measures explicitly supplied repaired snapshots only after they pass full reviewer parity, preserving originals; its artifacts go to `runtime/reference/`. Repeated rounds reverse the supplied reference order. `validate --condition reference` checks those artifacts. The comprehension commands apply only to sequential steps 1 and 6. No command overwrites an existing measured attempt or changes a frozen tool.
