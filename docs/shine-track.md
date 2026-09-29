# Framework-native optimization track

This track asks how good each finished Conduit app can be when an expert uses the language and framework deliberately. It is separate from the frozen one-shot runs. Those workdirs, prompts, transcripts, and measurements remain immutable. Changes happen in named copies with an origin manifest and are reported as revisions, never silently substituted into the scored tables.

The target has four simultaneous parts: complete product correctness, obvious ownership of domain rules, concise code that a fresh agent can change safely, and an efficient production service. A smaller token count is useful only when a reader can still find a rule and its tests. A faster request path is useful only if it preserves security, revision semantics, job durability, and live delivery.

Agent-built candidates use a short feedback ladder. With the development server already running, `tools/quick-smoke.sh PORT` checks boot and the list response in seconds. The agent then runs the one relevant Hurl file or compiler/linter command for its edit. The independent development and fresh-production suites, release build, and repeated measurements run once for a finished candidate. The quick smoke is feedback, not an acceptance result. Expert reference revisions in this directory are diagnostics; scored implementations remain agent-built.

## Comparable work

1. **Build-only pass.** Keep application source fixed. Use the stack's intended production build and runtime settings: Rails with a measured Puma worker/thread setting, Phoenix as a release instead of `mix phx.server`, Loco's release binary, and IHP's `optimized-prod-server` with an explicit GHC capability count. Verify each final artifact boots a fresh database and runs its worker. Record compiler flags, process count, image size, cold start, and all runtime limits. Any build-only gain is labeled separately from a code change.
2. **Framework and code pass.** Review each production entry point and canonical rule owners. Move repeated or stringly product logic to the smallest natural model, context, service, type, or database invariant. Use native routing, generated records/query facilities, jobs, and realtime facilities where they fit this fixed client contract. Remove N+1 paths, keep filters and pagination bounded in the database, and make request bodies narrow enough to reject mass assignment. Record libraries used and the behavior they replace.
3. **Independent verification.** Once a candidate is finished, rerun the full development and fresh-production suites, including the direct socket, browser, and security checks. Benchmark the *same built image* twice in opposite scenario order under the existing 2 CPU / 1 GiB app and database limits, retaining SQL counts and raw streams. Measure owned source tokens/lines, largest file share, docs, dependencies, and build effort. Preserve failed attempts and incomplete candidates.
4. **Evolution check.** Give a fresh reader a cross-cutting product change and measure navigation, correctness, and change cost. The [workshop handoff plan](semantic-density-workshop.md) defines this question. A reference app that is elegant to its author but hard for another agent to extend has not met the target.

The four stacks need equivalent product behavior and resource limits, but their frameworks need room to use different internals. A single-container contract, fixed Lit client, and raw WebSocket protocol remain constraints of this track; a later framework-native UI track should allow LiveView, Rails-integrated UI, and each stack's preferred client protocol without pooling those numbers with this API study.

## Production-build audit before source edits

| Existing semantic-density app | Observed artifact | First controlled change |
| --- | --- | --- |
| Rails | Production Dockerfile, Bootsnap, one Puma worker by default, eight threads | Measure an explicit 2-worker setting and its database pool under the same 2-CPU cap; keep source fixed. |
| Phoenix | `MIX_ENV=prod` compile, then `mix ecto.migrate && mix phx.server` in an Elixir builder image | Build a release and run its migration task and server from a runtime image. |
| Loco | `cargo build --release` in a builder stage, binary and config in slim Debian | Treat as the production-build control; profile code/query changes before changing compiler flags. |
| IHP | Custom Nix image runs `unoptimized-prod-server`, with no `-N` RTS setting; measured image is about 4.36 GB | Copy the guided implementation, use `optimized-prod-server` and `-N2` for the server, and then test a smaller image layout. |

The [IHP deployment guide](https://ihp.digitallyinduced.com/Guide/deployment.html) recommends the optimized production target and documents server and worker runtime settings. The [GHC runtime guide](https://downloads.haskell.org/ghc/9.10.3/docs/users_guide/runtime_control.html) explains that omitting `-N` leaves one capability. These are build hypotheses to test, not retroactive corrections to the frozen results. The guided IHP run demonstrates one-query lists and typed routing, but uses more owned source and agent time; its performance and maintenance value must be judged separately.

## Reporting

Show the original, build-only, and code-refined results side by side, with direct links to each source snapshot, gate, transcript or change log, and raw measurement. Do not infer language causality from one agent or one host run. In particular, a module split is evidence of clearer boundaries only when rule ownership is explicit and a fresh agent can use it; smaller largest-file share alone does not prove that.
