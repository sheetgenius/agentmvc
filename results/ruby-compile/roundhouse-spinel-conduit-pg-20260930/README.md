# Roundhouse + Spinel: compiled Conduit on PostgreSQL

**A compiled build of the Rails Conduit app passes the same fresh-production gate as the Rails app and served 2.0–5.4× the requests per second of Rails given the same 2-CPU budget.** The range is the per-scenario median of four alternating rounds. It is a separately labeled **compile variant** of the current Rails reference, built with locally patched Roundhouse and Spinel. It is not the measured one-shot source and not an unmodified upstream toolchain.

The [v2026.9.18 feasibility result](../roundhouse-spinel-v2026.9.18/README.md) still stands for that release and the frozen source.

## What was built

| Piece | What it is |
| --- | --- |
| Source | [Compile variant v4](variant/source/) of [Rails reference-1](../../one-shot-v2-rails-expert/pilot-1/reference-1/source/), still a valid Rails 8.1 app. Every difference and its behavioral impact is in [COMPILE-VARIANT.md](variant/source/COMPILE-VARIANT.md); the full [diff](variant/reference-to-variant.diff) is alongside it. |
| Compiler | Roundhouse `main` @ `25609ca3` (2026-09-30) with [17 local patches](patches/roundhouse/series), and Spinel `813def1f` with [two patches](patches/spinel/): cgroup-aware worker count, and a GC-rooting fix (below). No `--allow-unsupported`, no stubs, no edited emitted code. |
| Image | [Three-stage Dockerfile](toolchain/Dockerfile.production): strict `roundhouse check`, emit with `RH_DATABASE_ADAPTER=postgresql`, `spin build` (clang), then Debian slim with libpq5 and jemalloc. **119 MB**, versus 324 MB for Rails. No worker count is baked in: Spinel derives OS workers from the container's cgroup CPU quota at boot and logs the count. [Toolchain recipe](toolchain/Dockerfile.toolchain), [manifest](patches/roundhouse/SHA256SUMS), [provenance](run.json). |

## Gates and parity

| Check | Compiled v4 | Same v4 source on Rails |
| --- | --- | --- |
| Fresh-production gate (`tools/one_shot_host/check-production.sh`, unmodified). Builds the image, fresh PostgreSQL 17, only `DATABASE_URL`/`SECRET_KEY_BASE`/`PORT`. | **Pass**: 17/17 API, drafts, exports and live Hurl files; live protocol; 4/4 Playwright; 13/13 security ([log](evidence/gates/compiled-v4-production-gate.log)) | **Pass** ([log](evidence/gates/variant-v4-on-rails-production-gate.log)) |
| Development checks | Binary on PostgreSQL 17 with the API, live and security checks: pass on two fresh databases with the final toolchain ([v4-dev-a](evidence/lead-verify/v4-dev-a/), [v4-dev-b](evidence/lead-verify/v4-dev-b/); earlier v2 runs and one failing pre-fix run are kept alongside) | Zeitwerk, RuboCop (51 files, no offenses), 21 tests / 115 assertions ([logs](evidence/gates/variant-v4-rails-dev/)) |
| Common reviewer HTTP probe (not a frozen gate) | **21/21 contract, 3/3 quality** ([probe](evidence/compiled-v4-common-http-probe.json)) | Reference: 21/21, 3/3 |

Control: the unmodified Rails reference passes the same production gate in this workspace ([log](evidence/gates/reference-control-production-gate.log)).

## Benchmark

The benchmark used the unchanged [`tools/bench/bench.py`](../../../tools/bench/bench.py) and `load.js` (SHA-256 `d9eb2fbc…` / `9057777b…`, as in the published symmetry runs): nine scenarios, the same seed and 16 k6 VUs. Each run had a 3 s warmup and 15 s of measurement, with app and PostgreSQL each limited to `--cpus=2 --memory=1g`. Five configurations ran **four rounds in alternating order** (1→5, 5→1, 1→5, 5→1). **All 20 runs had zero failed checks.** [Runner](evidence/bench/run_paired.py) · [aggregation](evidence/bench/aggregate.md) · [per-run results](evidence/bench/) · [worker counts](evidence/bench/workers.json).

| Configuration | Workers inside the declared budget (2 CPU, 1 GiB) |
| --- | --- |
| `rails-ref-1proc` | Rails reference-1 image as recorded: one Puma process, 3 threads |
| `rails-ref-auto` | Same image with `WEB_CONCURRENCY=auto`: Puma derives **2 workers** × 3 threads from the quota (concurrent-ruby `available_processor_count` = 2.0) |
| `cruby-v4-1proc` | The compile variant's source on CRuby/Rails with one Puma process, as a control for source changes |
| `compiled-v4` | Compiled, **4 OS workers** = ceil(2 CPU × 2). Factor 2 is the PostgreSQL lane's documented rule, measured on a separate DB fixture before this benchmark. |
| `compiled-v4-k1` | Compiled, **2 OS workers** = ceil(quota), via `SPINEL_WORKER_FACTOR=1` |

Requests per second, median [min–max] of four rounds:

| Scenario | rails-ref-1proc | rails-ref-auto | cruby-v4-1proc | compiled-v4 | compiled-v4-k1 |
| --- | ---: | ---: | ---: | ---: | ---: |
| Anonymous article list | 543 [502–567] | 1,247 [1,232–1,264] | 563 [508–566] | **3,930** [3,193–4,180] | 3,904 [3,746–3,974] |
| Signed-in list | 416 [393–427] | 948 [944–959] | 415 [390–432] | **3,470** [3,256–3,742] | 2,928 [2,886–3,018] |
| List by tag | 516 [478–544] | 1,183 [1,174–1,195] | 515 [494–536] | **5,171** [5,070–5,663] | 4,157 [3,612–4,239] |
| Feed | 398 [328–417] | 920 [904–927] | 403 [285–417] | 2,329 [2,194–2,450] | **2,417** [2,190–2,530] |
| Single article | 630 [592–666] | 1,512 [1,454–1,562] | 653 [513–680] | 5,236 [4,868–5,484] | **5,358** [5,082–5,550] |
| Comments | 838 [770–858] | 1,727 [1,597–1,880] | 784 [702–803] | 9,956 [8,626–10,147] | **10,528** [9,586–10,607] |
| Tags | 1,596 [1,204–1,677] | 3,170 [2,704–3,213] | 1,650 [1,568–1,746] | 6,417 [6,166–6,459] | **6,449** [6,344–6,579] |
| Favorite toggle | 546 [514–560] | 989 [864–1,017] | 532 [407–558] | 2,523 [2,489–2,732] | **2,590** [2,513–2,645] |
| Create article | 553 [512–562] | 980 [945–1,076] | 544 [499–580] | 2,545 [2,370–2,805] | **2,593** [2,321–2,760] |

The fair comparison is `compiled-v4` against `rails-ref-auto`, since both are sized from the same quota. Same-round speedup, median [range]:

| Scenario | Speedup |
| --- | --- |
| Anonymous list | 3.2× [2.5–3.4] |
| Signed-in list | 3.7× [3.4–4.0] |
| By tag | 4.4× [4.2–4.8] |
| Feed | 2.5× [2.4–2.7] |
| Single article | 3.5× [3.3–3.5] |
| Comments | 5.4× [5.4–6.1] |
| Tags | 2.0× [2.0–2.3] |
| Favorite toggle | 2.6× [2.5–2.9] |
| Create | 2.5× [2.4–3.0] |

With one worker per CPU (`compiled-v4-k1`), the speedups are 2.0–5.8×. Against the recorded single-process baseline they are 4.0–12.0×.

The compiled app used far less memory, idling at 18–24 MB and peaking at 32–36 MB. Rails idled at 120 MB with one process and 282 MB with two workers. Anonymous-list p95 latency was 7–8 ms compiled against 19 ms for quota-sized Rails. The compiled app issued slightly **more** SQL per request (4.74 vs 4.00 on the list, 6.62 vs 5.98 on an article), so the gain is not from doing less database work. The CRuby run of the variant source tracks the Rails reference, so the source changes do not explain the gain either.

**Limits.**
- The workstation (Apple silicon, OrbStack, 18 cores) was shared. Foreign container CPU had a median of 68 % across scenarios, with one spike to 1,139 % during a CRuby control run; it is recorded per scenario. Under these conditions the Rails single-process list ran at 543 req/s, against 604–618 in the [published session](../../v2-expert-symmetry/README.md).
- An earlier session on the v3 build ran with 750–1,230 % foreign load. It showed similar ratios (2.8–5.5×) at roughly half the absolute rates ([evidence](evidence/bench-v3-contended-host/aggregate.md)).
- Factor 2 against factor 1 is mixed: factor 2 is faster on the three article-list scenarios (1–24 %), and factor 1 is equal or faster on the other six.
- This compares this compiled program with this Rails program on one machine. It is not a claim about Ruby versus compilers in general. Do not splice these rates into the published three-stack tables, which came from a different session.

## Porting cost

- **App source (v4 vs reference):** 17 application and config files changed, **+217 / −48 lines**. The main changes are JSON body typing with ParamsWrapper/`permit` emulation in `ApplicationController`, an in-app HS256 token codec replacing the `jwt` gem, a recovery initializer, and small substitutions. A PostgreSQL `db/structure.sql`, the ledger and two test files are added. Schema, migrations, Gemfile, `FavoritesController`, `Article` and `ArticleShare` are unchanged.
- **Owned size** ([`tools/measure.py`](../../../tools/measure.py), rails-expert rules): **7,150 tokens / 787 lines excluding `db/structure.sql`** (it is a `pg_dump`, the equivalent of the excluded `schema.rb`), and 10,423 / 1,063 including it. Reference-1 is 6,085 / 657 ([size.json](variant/size.json)).
- **Roundhouse (17 patches):** `src/` +1,042/−136, `runtime/` +1,585/−113, tests +653/−10, docs +121 lines.
  - PostgreSQL lane: libpq `Db` with async I/O and a statement cache, DATABASE_URL boot, structure.sql provisioning, RETURNING, text[]/jsonb/uuid codecs, SQLSTATE mapping, `with_lock`, integer range semantics.
  - API-mode JSON controllers.
  - Raw WebSocket: the Faye API over tep, with close/lifecycle fixes.
  - Boot hooks and a job drain.
  - Rails-surface fixes, and a quadratic SQL rewriter fixed (a 2 MB request went from 88 s to 75 ms).
- **Spinel (2 patches):** cgroup-aware worker autodetection with a memory-budgeted GC trigger, and the GC-rooting fix, both with tests. Four more Spinel defects were worked around in app source: a Struct field named `members`; `reject!` inside `Mutex#synchronize`; exception attributes lost through `synchronize`; and the `Hash#fetch` Array default.
- **Effort:** 22 Codex worker runs (`gpt-6.1-sol`, `xhigh` except a sandbox probe), about 14 worker-hours; two were stopped by the provider's content filter and two were paused by reprioritization. One Claude subagent (20 min) found the Spinel GC bug. Wall time was about 8 hours.

## Behavioral differences (v4 vs Rails reference)

No differences were observed within the frozen contract or the common probe. Outside them, per the [ledger](variant/source/COMPILE-VARIANT.md):
- JSON bodies are read with their types. Objects supplied only as form or query parameters are rejected (422), and body-over-query merging for GET requests with JSON bodies is not reproduced. Unicode-whitespace-only login fields are not treated as blank.
- The token codec is HS256-only. It rejects padded Base64 segments, and malformed claims return 401 where the `jwt`-based reference raised a 500.
- Export recovery at boot iterates pending rows without batching. The durable queue is the pending export row plus an in-process drain, not GoodJob; GoodJob's tables remain in the schema.
- The password-length rule uses a callback, so its error type is `:invalid` rather than `:too_short` (the HTTP message is the same).
- `ArticleCommit` casts before comparing titles, so a non-String title that equals the current title after casting doesn't re-slug.

## Found along the way: a Spinel GC-rooting bug

The first compiled image passed every gate, then died with SIGSEGV (exit 139, not OOM, also with one worker) under the benchmark's `create_article` load ([backtrace](evidence/crash/gdb-backtrace-sigsegv.log)).
- **Cause.** For a call on a dynamically typed receiver, Spinel's generated C computes each argument into a temporary before dispatch but roots only the receiver. A later argument's allocation can then collect an earlier one. The unrooted temporaries are positional arguments (`src/codegen_call.c:8648-8672`), keyword arguments (`:8686-8704`), and the result of a no-`else` `(expr if cond)` (`src/codegen_expr.c:3567-3578`). Conduit's `Article.new(permitted(...).merge(..., tag_list: tags.uniq, published_at: ...))` hits all three.
- **Fix.** [The patch](patches/spinel/spinel-poly-dispatch-arg-roots.patch) roots these temporaries and adds a regression test.
- **Verification.** The [deterministic repro](patches/spinel/repro-poly-dispatch/) segfaults on stock Spinel (307 corrupted values under `SPINEL_GC_STRESS=1`) and reports 0 with the patch. The Spinel corpus shows 4,881 passing tests and 2 environment-only failures, which also fail on stock. With the fix, the original create code survives about 50,000 creates under load with zero failures ([evidence](evidence/crash/)). An interim variant (v3) avoided the bug in source; v4 reverts that workaround.

## Reproduce

You need Docker with BuildKit, git, bash and python3, plus network access to GitHub, rubygems.org (Spinel's `make deps`), Docker Hub, ghcr.io and mcr.microsoft.com. Run the commands from the repository root. Scratch files go to `reproduce/build/`, which git ignores. In the commands below, `R=results/ruby-compile/roundhouse-spinel-conduit-pg-20260930`.

1. **Toolchain sources.** `$R/reproduce/prepare-toolchain.sh` clones [Roundhouse](https://github.com/rubys/roundhouse) at `25609ca3` and [Spinel](https://github.com/matz/spinel) at `813def1f`. It checks the patches against [SHA256SUMS](patches/roundhouse/SHA256SUMS) (the file's own SHA-256 is `83918594…`, the toolchain tag), applies the [series](patches/roundhouse/series) and the two Spinel patches, and writes the build context (Dockerfile, flat `patches/`, patched `vendor/` trees). It then compares each vendor tree with the digest of the tree the published toolchain image was built from.
2. **Images.** `$R/reproduce/build-images.sh` builds the toolchain image (tagged `spinel-spike-lead-toolchain:83918594c522`, the default the production Dockerfile expects), then the compiled image from [variant/source](variant/source/) with [Dockerfile.production](toolchain/Dockerfile.production) (`spinel-spike-lead-conduit:v4-compiled`). Add the targets `cruby reference` to build the variant on CRuby (`…:v4-cruby`) and the Rails reference-1 image (`agentmvc-v2-expert-rails-reference-1:review`) for the benchmark. Tags can be overridden; see the script header.
3. **Gate.** `$R/reproduce/run-gate.sh compiled 4390` (or `rails 4390` for the same source on Rails) assembles a workspace from `variant/source` plus the repository's frozen gate inputs, in the same layout as the Rails expert v2 workspace: `spec/` and `one-shot/frontend/` become `realworld_spec/`, `tools/security/hurl/` becomes `security/hurl/`, and `one-shot/harness/`, `rails.sh` and `quick-smoke.sh` become `harness/`. It checks every input against `one-shot/fixture-manifest.json` and the whole set against the gated workspace. Then it runs the unmodified `tools/one_shot_host/check-production.sh`. The browser image `agentmvc-one-shot-browser:1.63.0` is built from `one-shot/harness/Dockerfile.browser` if it is missing, and its local ID is written to `harness/browser-image-id`. The published ID (`sha256:e4467f16…`) is a local build and won't match yours; the gate only requires that the workspace and the image agree.
4. **Benchmark.** Build all four images (`build-images.sh toolchain compiled cruby reference`), then run `python3 $R/evidence/bench/run_paired.py OUT --rounds 4` and `python3 $R/evidence/bench/aggregate.py OUT v4`. The runner calls the unchanged `tools/bench/bench.py` for each configuration in alternating order and needs host port 18090. The published session took about 70 minutes. `bench.py` uses `grafana/k6:latest` and `postgres:17-alpine` by tag; the image IDs used are in [summary.json](evidence/bench/summary.json). Absolute rates depend on the host, so compare ratios. The one change to the published runner: `ROOT` was an absolute local path and is now derived from the file's location; everything else is byte-identical to the file that ran (SHA-256 `bc9ce146…` before the edit).

Checked before publication (2026-10-01, same host):
- **Sources.** A fresh `prepare-toolchain.sh` gave vendor trees identical to the published build context: 12,145 files, the same contents and executable bits, and the same patch set and Dockerfile.
- **Toolchain image.** Rebuilt from that context with `--no-cache` in about 100 s; it reports `roundhouse 2026.9.18 (25609ca3)` and `spinel 2026.09.12+2807 (813def1fb)`. Its image ID differs from the published one (`sha256:45a9a5f6…`) because the apt layers are not bit-reproducible. BuildKit cache mounts for cargo were reused.
- **Compiled image.** Built on the rebuilt toolchain, the compile stage ran and produced a `/runtime` tree whose file hashes match the published image's `/app`. The final image ID was the published `sha256:872570a6…`, and `/app/server` has SHA-256 `77188a2d…`. On another host the apt layers, and possibly clang, differ, so expect a different image ID.
- **Gate.** `run-gate.sh compiled 4390` with the rebuilt toolchain passed: 17/17 Hurl files, the live protocol, 4/4 Playwright and 13/13 security. `run-gate.sh rails 4390` also passed.
- **Variant source.** [gated-source.sha256](reproduce/gated-source.sha256) hashes the 75 files of the gated workspace other than the ledger, and all of them match `variant/source` (`cd $R/variant/source && sha256sum -c ../../reproduce/gated-source.sha256`). `COMPILE-VARIANT.md` is the gated ledger with the "v4 (final, lead)" section appended after the gate.

Not included: the working notes (worker reports, dispatch ledger, upstream candidates) and the Spinel investigation's scratch directory. The [Spinel repro](patches/spinel/repro-poly-dispatch/) needs a stock Spinel `813def1f` build next to the patched one. The toolchain image contains only the patched build.
