# Research log

Everything below ran on 27 September 2026; times are UTC. Each step's three agents ran in parallel. After every run, the reviewer reran its checks independently before the step counted. Hypotheses were written down before each benchmarked, scanned or read step ran.

- **02:12–02:32, step 1 (build).** All three DONE. Rerun: 13/13 acceptance files, lint clean.
- **02:45, a counting fault, found and fixed.** The first comprehension launch after step 1 was stopped. `measure.py` didn't recognize `.jbuilder` files, so Rails' views were missing from both its reading copy and its size.
  - After the fix, Rails' step-1 size is 3,514 tokens. An inventory of every file type across the implementations found nothing else uncounted.
  - All three comprehension runs were rerun from 02:48 to 02:51.
- **02:53–03:09, step 2 (drafts).** Before launch, the feature spec was validated by a throwaway Rails implementation that passed all 15 files. All three DONE, 15/15.
- **03:05–03:19, step 3 (package).** All three DONE. Both checks passed, including the suite against each production image.
- **03:27, a benchmark fault, caught before any result was kept.** The seeder and load generator sent no `Accept` header, and Rails answers such requests with 406. The harness now sends `Accept: application/json` for every stack.
- **03:27–03:37:** the step-3 images were benchmarked, one at a time.
- **03:38–03:59, step 4 (tune).** All three DONE. Each agent ran its own benchmarks, in parallel with the others, so they were noisy; only the reviewer's runs are published.
- **04:01–04:24:** the tuned images were benchmarked. Endpoints that no agent had changed also looked slower, so the step-3 images were benchmarked again as a same-session control.
- **04:24–04:34, a sensitivity check, and one claim withdrawn.**
  - The tuned Rails image was run with two Puma workers, then with one as a control. The control ran 1.28–1.54× faster than the same image at 04:01, so the apparent Rails slowdown on single-record endpoints was drift, and was withdrawn.
  - **The cause:** unrelated workloads on the same machine, at times using 3–5 of its 18 CPUs.
  - **Rules from here on:** compare within a session only; claim nothing under 1.5×; record the background CPU for every scenario.
- **04:35–04:49, the security baseline, and two scanner faults fixed before any agent saw results.**
  - The scanner's readiness probe had the same missing `Accept` header.
  - Sobelow's JSON output needs the Jason library, which Sobelow's archive doesn't bundle. It failed silently, and would have shown as "0 findings".
  - Both were fixed, and analyzer errors now show as failures. Rails and Phoenix were rescanned.
- **04:50–04:59, step 5 (harden).** All three DONE: 15/15 acceptance files and 13/13 security checks against each production image.
- **05:01–05:10, step 6 (polish).** All three DONE. No codebase changed size by more than 1%.
- **05:03–05:10, step 7 specified.**
  - The exports feature was validated by a throwaway Rails implementation, run on separate ports so it couldn't disturb the running agents. A deliberately slowed variant proved the polling test.
  - A measurement rule was set before launch: installer-generated queue schema counts as generated schema.
- **05:11–05:21, step 7 (background job).** All three DONE: 16/16 acceptance files and 13/13 security checks. The Rails agent copied Solid Queue's generated schema into a migration, so its cost is reported both ways.
- **05:12–05:14:** the comprehension runs after step 6. Rails' agent-token count doubled while its total input rose only 5%, a prompt-cache effect. Total input processed is now reported alongside, and the step-1 comparison is caveated.
- **05:23–05:43, the step-7 benchmark block.** The tuned and polished images ran back to back for each stack, with the background load recorded. There was no regression, and the background-load readings showed the drift mechanism directly.
- **08:26–08:36, step 8 fixture prepared.** A shared live-editing protocol, 210-line Lit editor, HTTP/socket checks and three-browser Playwright suite passed against a throwaway Node server outside the measured stacks. The prompt and fixture were hashed and frozen before launch. The first reference browser run found and fixed a Room full Retry state bug before the freeze.
- **08:36–09:03, step 8 (live shared editing).** One measured agent run each for Rails, Phoenix and Loco, all DONE. Each final development and production gate passed 17/17 Hurl files, the socket and browser suites, and 13/13 production security files. Sandboxed macOS Chromium was unavailable; the agents used the same matching Linux Playwright image. Rails' first socket propagation failed until its writes were scheduled on EventMachine. [Failure history →](../results/live-editing/failures.md)
- **09:03–09:09, independent verification.** Every published snapshot passed a fresh rerun of both gates. The one-command demo and a separate reviewer check passed on all three production images. The reviewer also corrected transcript scrubbing after a shared Playwright cache listed unrelated local worktree paths.
- **09:10–09:16, direct socket load.** Two close measurement rounds ran in forward and reverse stack order, with 10, 100 and 500 subscribers. All 25,200 expected updates arrived without duplicates or revision regressions. A missing JSON `Accept` header was fixed in the smoke-test readiness probe. Fresh PostgreSQL was slow to accept connections before Rails round two; that failed startup attempt was preserved and only Rails round two was rerun. Background host load remained high, so the [raw step-8 results](../results/live-editing/) are reported without a narrow latency ranking.

Every session's transcript is in its stack's `transcripts/`, and every record is in its `runs.json`.
