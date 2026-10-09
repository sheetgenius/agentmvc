# Experiment v3: one-shot builds of a two-instance Conduit with semantic search

Status: proposal, decided on 2026-10-05. Nothing here is frozen or has run.

Everything before v3 was exploration: eight-step lanes, expert one-shots, reviewed references and a compiled Rails variant. v3 keeps one simple protocol and makes the product closer to real work:

- **One-shot only.** Each stack is built in one agent session, from a product-free scaffold, against one frozen contract.
- **One run per stack per condition.** Volume comes from conditions accruing over time: a new model, prompt, brief or contract version is a new condition with its own run. Single runs vary, and code size varied far less than effort and speed in the IHP repeats. So read code size with more confidence than effort or speed.
- **Two app instances.** Presence, room caps, throttles and job deduplication must hold across both instances, coordinated only through PostgreSQL.
- **Semantic search with pgvector.** It follows the shape of BitterClip's transcript search, so the builds also test what a BitterClip-like Rails app needs.
- **Neutral guidance.** Each stack gets an environment file with toolchain facts only. Practitioner briefs come later, each as its own condition.

Earlier results stay published as exploratory evidence under their own conditions. v3 results start a new baseline and are never pooled with them.

## Contract v3

The product keeps everything the current contract requires: the RealWorld API, drafts with edit conflicts, durable exports and live shared editing. Two things are added.

### Two instances

The draft below becomes `spec/features/multi-instance/` in a new fixture version. It stays out of `spec/` until then, because `spec/` is hashed into the existing fixtures.

- **Deployment.** The harness starts two app containers from the same image, one PostgreSQL and a reverse proxy it supplies. HTTP requests are spread across both instances, and each WebSocket stays on the instance that accepted it.
- **Services.** PostgreSQL only: no Redis and no message broker. `LISTEN`/`NOTIFY`, tables and advisory locks are allowed.
- **Resources.** Each app container gets 1 CPU and 512 MiB, so the app tier keeps the earlier 2-CPU total. PostgreSQL keeps 2 CPUs and 1 GiB.
- **Invariants across instances:**
  - presence counts include editors on both instances;
  - the 100-editor cap is exact, including when joins race;
  - revoking or rotating a link disconnects its sockets on both instances;
  - a save on one instance reaches subscribers on the other, with increasing revisions;
  - an export requested twice at once is built once;
  - failed-login throttling counts attempts on both instances together.

### Search

The draft becomes `spec/features/search/`, under the same rule.

- **Endpoint.** `GET /api/articles/search?q=…` returns the usual multiple-articles envelope plus a `semantic` field: `complete`, or `unavailable` when the embedding service failed. The exact shape and limits are settled while drafting the spec.
- **Visibility.** The same rule as the public article list: published articles only, never drafts, not even the author's own.
- **Order.** Keyword matches from PostgreSQL full-text search over title, description and body come first. Semantic matches fill the remaining slots by cosine distance, without repeating a keyword match.
- **Embeddings.** A durable background job calls the harness's embedding service, an OpenAI-compatible `/v1/embeddings` endpoint whose URL, model name and dimension come from the environment. It stores each vector in a pgvector column with the model name and a hash of the embedded text. A changed title, description or body, or a different model name, makes the embedding stale. Search uses only current embeddings.
- **Failure.** If embedding the query fails or exceeds its timeout, search returns the keyword results with `semantic: "unavailable"`, never an error.
- **Database.** PostgreSQL 17 with pgvector, pinned by image digest. Indexing is the agent's choice, but the gate expects the exact cosine ranking on its fixture, so an approximate index must not change those results.

### The embedding stand-in

The gate never runs a model. The harness supplies a small service that answers like a provider:

- **Known text** (the fixture articles and the test queries) gets real vectors. They were computed once with a small open-weights model under a permissive licence and frozen to a file with a checksum.
- **Unknown text**, such as articles that other suites create with random titles, gets a deterministic vector derived from the text. The checks compute the same function, so every expected ranking is known in advance.
- **A switch** lets a check make the service fail or stall.

The model is used only to regenerate the frozen file and to make `tools/lane_demo.sh` search work offline. Rerunning it can change the last digits of the floats on another CPU or runtime version, so the file, not the model, is the source of truth.

## Checks

- **Existing suites:** the API, drafts, exports, live editing, browser and security checks, all through the proxy.
- **Cross-instance:** one check per invariant above. For example, 60 editors join through one instance and 40 through the other, and the next join on either must be refused.
- **Search:**
  - drafts never appear;
  - keyword matches come first, with no duplicates;
  - semantic results match the exact ranking, computed in single precision with ties broken by ID;
  - an edited article is found by its new text once its job has run;
  - with the service failing or stalled, keyword results still return with `semantic: "unavailable"`;
  - a search with a full-size query vector finishes within a time limit.
- **Validation before freezing:** a throwaway reference implementation must pass every check. Deliberately broken variants must fail:
  - presence kept in one process's memory;
  - a per-instance editor cap;
  - revocation that reaches only one instance;
  - search that returns drafts;
  - embeddings never refreshed after an edit;
  - an error response when the embedding service fails.

The common reviewer probes stay supplemental and are reported beside the gate, as before.

## Runs

- **First wave:** Rails, Phoenix, AdonisJS, Go, Python, Clojure and Rust, one run each, on `gpt-6.1-sol` at `xhigh`. The model, reasoning and CLI come from a per-condition launch configuration and are recorded with each run.
- **Rust uses Axum and SQLx.** This is the stack most teams would reach for in a Rust rewrite, the question this project began with. Given the choice, the first one-shot agent also wrote Axum and SQLx inside the Loco scaffold. SQLx's `PgListener` covers cross-instance notifications, and the `pgvector` crate supports SQLx.
- **Pilot:** Rails runs first, to shake out the proxy, the stand-in and the checks before the other stacks launch.
- **Later conditions:** IHP and Servant once their toolchains run under the same runner, Loco if a Rails-style Rust framework is wanted, then briefs, new models and prompt changes, each as its own condition.

## Measurements

| Area | What to record |
| --- | --- |
| Correctness | The gate, cross-instance checks and search checks; reviewer probes separately |
| Code | Owned and whole-backend tokens and lines against the scaffold |
| Effort | Wall time, uncached input plus output tokens, commands and gate attempts |
| Runtime | One paired session through the proxy: the nine HTTP workloads, socket fan-out and search |
| Compiled Rails | Unscored: compile the Rails build with Roundhouse and Spinel, then run the gate |

Search is benchmarked at two catalog sizes. At 500 articles the database work is tiny, so the app dominates. At the large size the database dominates, as it does in BitterClip. Set the large size from the live transcript-window count of BitterClip's largest account, once a Bitter CLI read reports it. Until then, use 100,000 articles. A local probe on random 1,536-dimension vectors took 255–270 ms for an exact search at 100,000 rows, against about 1 ms with an HNSW index. The large catalog's vectors are a release download, like the existing raw data.

## Changeability

v3 doesn't chain sessions. To test whether a fresh agent can safely change a build, run an occasional hand-off study, labeled separately: give one frozen change task, such as the [private articles draft](../one-shot-v2-expert/HANDOFF-DRAFT.md), to a fresh agent working on a stack's v3 build.

## Repository

The restructure starts from the `clean-slate` branch: one runner, a run ledger, one reference app per stack, and the docs on running, pitfalls and findings. Earlier results move into a labeled exploratory archive that stays reachable. The rules on frozen inputs and agent messages don't change.

## Before launch

1. Draft the multi-instance and search specs outside `spec/`, including the search response shape.
2. Build the proxy harness and the embedding stand-in. Choose the model, then generate and checksum the vector file.
3. Write the checks, and validate them against the throwaway reference and the broken variants.
4. Write each stack's neutral environment file from the [template](../briefs/ENVIRONMENT-TEMPLATE.md), and apply the prompt fixes from the [baseline refresh](baseline-refresh.md).
5. Prepare the Rust stack, which has no current scaffold. Choose and document its crates, build a product-free scaffold with packaging, and keep a Cargo home and target directory per run.
6. Run every stack through one runner, including Rails, Phoenix and AdonisJS, which used per-track scripts.
7. Freeze every input, register the condition in the [cohort index](cohorts.md), run the Rails pilot, then the rest.

## Open questions

- **Embedding model and dimension.** Small permissive models give 384–1,024 dimensions, while BitterClip uses 1,536. The time-limit check uses whatever the contract fixes.
- **Exact ranking or a recall threshold.** Should an agent that adds an approximate index be held to exact results on the small fixture, or to a recall threshold?
- **Large catalog size.** It's waiting on the BitterClip account count.
- **The runner.** Will the restructure keep the lane runner or the `clean-slate` one-shot tools?
