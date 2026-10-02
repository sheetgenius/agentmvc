# Roundhouse + Spinel: compiled Conduit on upstream heads

**The compiled Conduit app now builds on current Roundhouse `main` with 11 local patches and on Spinel `master` with none, and it still passes the same fresh-production gate as the Rails app.** The [v4 build](../roundhouse-spinel-conduit-pg-20260930/README.md) needed 17 Roundhouse patches and 2 Spinel patches. Our fixes, and some from other contributors, were merged upstream, so six Roundhouse patches, both Spinel patches and four app workarounds could go. The app now differs from [Rails reference-1](../../one-shot-v2-rails-expert/pilot-1/reference-1/source/) by +184/−46 lines in 16 files. It is still a separately labeled **compile variant**, built with a locally patched compiler, and it is not the measured one-shot source.

**No new benchmark.** The throughput figure below is a single sanity check against v4 on one scenario. The [v4 package](../roundhouse-spinel-conduit-pg-20260930/README.md#benchmark) holds the benchmark: 2.0–5.4× the requests per second of quota-sized Rails across nine scenarios.

## What changed from v4

| | v4 (2026-09-30) | v5 (2026-10-02) |
| --- | --- | --- |
| Roundhouse | `main` @ `25609ca3` + 17 patches (+3,401/−259) | `main` @ `5bbc4765`, 143 commits later, + **[11 patches](patches/roundhouse/series) (+3,218/−221)** |
| Spinel | `813def1f` + 2 patches | `d2c20df0`, 1,677 commits later, **[no patches](patches/spinel/README.md)** |
| Spinel defects worked around in app source | 5 | **1** |
| App delta vs reference-1 ([diff](variant/reference-to-variant.diff)) | 17 files, +217/−48 | **16 files, +184/−46** |
| Owned tokens, excluding `db/structure.sql` ([size](variant/size.json)) | 7,150 (reference: 6,085) | **6,962** |
| OS workers | 4, derived from the cgroup CPU quota by a Spinel patch | 4, set by `ENV SPINEL_WORKERS=4` in the image |
| Image | 119 MB | 119 MB |

These merged PRs made the difference:

| Upstream PR | Fix | Removed from v5 |
| --- | --- | --- |
| [spinel#6549](https://github.com/matz/spinel/pull/6549) | A poly dispatch roots its argument temporaries (v4's GC-rooting bug) | Spinel patch `poly-dispatch-arg-roots` |
| [spinel#6572](https://github.com/matz/spinel/pull/6572) | A call converted into an `--rbs` Hash parameter keeps its result | `UsersController#update` direct-writer loop |
| [spinel#6580](https://github.com/matz/spinel/pull/6580) | A Struct member named like a Struct method reads the member | `LiveRooms` Room class and nil seed |
| [spinel#6654](https://github.com/matz/spinel/pull/6654) | `fetch` on a boxed Hash returns an empty `[]` or `{}` default | `ArticlesController#create` `key?` check |
| [roundhouse#259](https://github.com/rubys/roundhouse/pull/259) | An app with no views gets a views aggregator that requires nothing | Patch 41 and a hunk of patch 10 |
| [roundhouse#260](https://github.com/rubys/roundhouse/pull/260) | A command call as an `&&`/`\|\|` operand keeps its parentheses | Patch 42 |
| [roundhouse#269](https://github.com/rubys/roundhouse/pull/269) | A class nested in a controller reopens the controller as a class | Patch 43 |
| [roundhouse#288](https://github.com/rubys/roundhouse/pull/288) | `+""` stays an unfrozen copy on the Ruby targets | Patch 62 |
| [roundhouse#246](https://github.com/rubys/roundhouse/pull/246) (dai199) | A non-string schema default seeds a new record | Patch 63 |
| [roundhouse#291](https://github.com/rubys/roundhouse/pull/291) | `id: :serial` and a hash-valued `id:` ingest as the keys they name | Overlapping hunks of patch 50 |
| [roundhouse#292](https://github.com/rubys/roundhouse/pull/292) | A partial unique index (`where:`) constrains only the rows it selects, as on Conduit's `article_shares` | Nothing: a silent schema bug found while porting |

[roundhouse#283](https://github.com/rubys/roundhouse/pull/283) (calmacleod) and [#210](https://github.com/rubys/roundhouse/pull/210), [#212](https://github.com/rubys/roundhouse/pull/212) and [#214](https://github.com/rubys/roundhouse/pull/214) (dai199) shrank patches 60 and 10.

## What was built

| Piece | What it is |
| --- | --- |
| Source | [Compile variant v5](variant/source/): v4 with four workarounds reverted, still a valid Rails 8.1 app. The [ledger](variant/source/COMPILE-VARIANT.md) explains every difference from the reference; its v5 section lists the reverts. |
| Compiler | Roundhouse `main` @ `5bbc4765` (2026-10-02, the merge of #292) with the [series](patches/roundhouse/series), and Spinel `master` @ `d2c20df0` unpatched. No `--allow-unsupported`, no stubs, no edited emitted code. |
| Image | The v4 [three-stage Dockerfile](toolchain/Dockerfile.production) on the new [toolchain](toolchain/Dockerfile.toolchain), plus `ENV SPINEL_WORKERS=4`: 2 workers per CPU for the declared 2-CPU budget, the PostgreSQL lane's rule. [Manifest](patches/roundhouse/SHA256SUMS), [provenance](run.json). |

## Patches

| Patch | v5 | Why |
| --- | --- | --- |
| [00-interval](patches/roundhouse/00-interval.patch): `t.interval` columns in `schema.rb` | kept | The upstream PR is on hold: Rails reads `interval` as a Duration, which needs a design answer first. |
| [10-api-mode-json](patches/roundhouse/10-api-mode-json.patch): API-mode JSON controllers | rebased, 29 → 27 files | #259 covers its views-aggregator hunk and #210/#212/#214 its symbol-key params. The rest is still needed. |
| [20-raw-websocket](patches/roundhouse/20-raw-websocket.patch): Faye's raw WebSocket API over tep | kept | No upstream equivalent. |
| [30-jobs-boot](patches/roundhouse/30-jobs-boot.patch): boot hooks and the job drain | kept | No upstream equivalent. |
| v4's [41](../roundhouse-spinel-conduit-pg-20260930/patches/roundhouse/41-w09-01-zero-view-aggregator.patch), [42](../roundhouse-spinel-conduit-pg-20260930/patches/roundhouse/42-w09-02-raise-boolean-operand.patch), [43](../roundhouse-spinel-conduit-pg-20260930/patches/roundhouse/43-w09-03-controller-namespace.patch) | **dropped** | #259, #260, #269 |
| [50-postgresql-lane](patches/roundhouse/50-postgresql-lane.patch): libpq `Db`, structure.sql provisioning, PG codecs | rebased | Over upstream's JSON columns, identifier quoting, #246 and #291. |
| [60-rails-surface](patches/roundhouse/60-rails-surface.patch) | rebased | Over #283; Conduit's class-side `find_or_create_by!` still needs ours. |
| [61-secure-password-super-and-nil](patches/roundhouse/61-secure-password-super-and-nil.patch) | kept | [roundhouse#289](https://github.com/rubys/roundhouse/pull/289) is open. |
| v4's [62](../roundhouse-spinel-conduit-pg-20260930/patches/roundhouse/62-mutable-string-literal.patch), [63](../roundhouse-spinel-conduit-pg-20260930/patches/roundhouse/63-primitive-schema-defaults.patch) | **dropped** | #288, #246 |
| [70](patches/roundhouse/70-linear-pg-placeholder-rewrite.patch), [71](patches/roundhouse/71-record-lock-and-error-predicate.patch), [72](patches/roundhouse/72-pg-async-cache.patch): placeholder rewrite, row locks and error predicate, async libpq | kept | PostgreSQL lane and row locks; no upstream equivalent. |
| v4's [73-cgroup-boot](../roundhouse-spinel-conduit-pg-20260930/patches/roundhouse/73-cgroup-boot.patch) | **dropped** | It depended on the Spinel cgroup patch. |
| [74-integer-query-range](patches/roundhouse/74-integer-query-range.patch) | rebased | Context conflict only. |
| Spinel `poly-dispatch-arg-roots` | **dropped** | spinel#6549 |
| Spinel `cgroup-workers` | **dropped** | Replaced by `SPINEL_WORKERS=4`, the program-level setting matz recommends ([spinel#4266](https://github.com/matz/spinel/issues/4266)). The count no longer follows `--cpus`, and the memory-budgeted GC trigger is gone ([details](patches/spinel/README.md)). |

## App workarounds

Each revert was tried alone on the v5 toolchain and kept only if the compiled production gate stayed green ([gate logs](evidence/gates/reverts/)).

| v4 workaround | Upstream fix | v5 |
| --- | --- | --- |
| `LiveRooms`: a Room class and a nil-seeded Hash | spinel#6580 | **Reverted.** The file is byte-identical to the reference again. The gate passes, and the 101st member of a full room is refused ([cap check](evidence/probes/live-room-cap.log)). |
| `ArticlesController#create`: `key?` instead of `fetch("tagList", [])` | spinel#6654 | **Reverted.** The gate passes, with 0 edge differences ([edge](evidence/edge/r2-fetch.json)). |
| `UsersController#update`: a direct-writer loop | spinel#6572 | **Reverted** to `update!(permitted(...))`. The gate passes, with 0 differences over 24 update bodies ([edge](evidence/edge/r3-update.json)). The reference's full `.permit` still needs typed JSON params: `permit` and `slice` forms changed 45 and 38 of 166 responses ([permit](evidence/edge/r3x-permit.json), [slice](evidence/edge/r3x-slice.json)). |
| `blank_value?` helper | none needed: Roundhouse already lowers `blank?` | **Reverted.** 0 differences over 13 blank login variants ([edge](evidence/edge/ap5-blank.json)). |
| `LoginThrottle`: decide under the lock, raise after it | needs the Spinel synchronize/exception stack | **Kept.** The reference form answers 500 on every failed login ([gate](evidence/gates/reverts/r4a-throttle-ref.log), [probe](evidence/probes/login-throttle.log)). |
| `article.author` instead of `association(:author).loaded?` | none | **Kept.** The reference form compiles, then every article read answers 500 ([gate](evidence/gates/reverts/ap7-loaded.log)). |

## Validation

| Check | Compiled v5 | Same v5 source on Rails |
| --- | --- | --- |
| Fresh-production gate (`tools/one_shot_host/check-production.sh`, unmodified) | **Pass**: 17/17 API, drafts, exports and live Hurl files; live protocol; 4/4 Playwright; 13/13 security ([log](evidence/gates/compiled-v5-production-gate.log)) | **Pass** ([log](evidence/gates/variant-v5-on-rails-production-gate.log)) |
| Development checks | Not rerun for v5 | Zeitwerk, RuboCop (51 files, no offenses), 21 tests / 115 assertions ([logs](evidence/gates/variant-v5-rails-dev/)) |
| Common reviewer HTTP probe (not a frozen gate) | **21/21 contract, 3/3 quality** ([probe](evidence/compiled-v5-common-http-probe.json)) | Reference: 21/21, 3/3 |
| Edge script, 166 requests (not a frozen gate) | **0 differences from compiled v4**; 7 from Rails reference-1, the same 7 as v4 (below) ([v5](evidence/edge/v5-compiled.json), [v4](evidence/edge/v4-compiled.json), [Rails](evidence/edge/rails-reference-1.json), [runner](evidence/edge/edge_diff.py)) | Not run |

Control: the unchanged v4 source on the v5 toolchain also passes the gate ([log](evidence/gates/control-v4-source-on-v5-toolchain-production-gate.log)), with 0 edge differences from v4 ([edge](evidence/edge/c0-v4src.json)).

**Sanity throughput, not a benchmark.** On the anonymous article list alone, with the v4 benchmark's budget (app and PostgreSQL each `--cpus=2 --memory=1g`, 16 VUs, 15 s), three alternating rounds each gave v5 a median of 4,307 req/s [4,066–4,308] and v4 4,148 req/s [3,406–4,271] ([summary](evidence/sanity-throughput/summary.txt)). One v4 round ran with 1,560 % foreign CPU on the shared host. The check only shows that v5 did not regress. Without the memory-budgeted GC trigger, peak memory was 30–33 MB against v4's 26–27 MB.

**Behavioral differences** are unchanged from v4 (see the [ledger](variant/source/COMPILE-VARIANT.md) and the [v4 list](../roundhouse-spinel-conduit-pg-20260930/README.md#behavioral-differences-v4-vs-rails-reference)). On the edge script, v4 and v5 differ from Rails reference-1 on the same 7 of 166 requests, from three cases:
- A whitespace-only email in a user update is stored; Rails answers 422. This is a new issue candidate: the compiled presence validation isn't `blank?`-aware.
- A numeric password is accepted as a string; the Rails reference answers 500.
- A null password reports "can't be blank" once; Rails reports it twice.

**Roundhouse's own tests** with the series: the patches' integration tests pass, but `runtime_src_integration::every_runtime_method_body_concretely_typed` fails, though it passes on unpatched `main`; it needs fixing before the runtime hunks go upstream. The same 40 library tests fail with and without the series, because the generated `fixtures/real-blog` app was absent ([logs](evidence/roundhouse-tests/)).

## Remaining blockers

| What is still local | Upstream work |
| --- | --- |
| `LoginThrottle` workaround | Spinel's synchronize/exception stack: [#7102](https://github.com/matz/spinel/pull/7102), [#7136](https://github.com/matz/spinel/pull/7136) and [#7155](https://github.com/matz/spinel/pull/7155) open, six more stacked behind them |
| `SPINEL_WORKERS=4` in the image | A Spinel RFC for a quota-aware default worker count; not opened |
| Patch 61 | [roundhouse#289](https://github.com/rubys/roundhouse/pull/289), open |
| Patches 50, 70, 72 and the `RH_DATABASE_ADAPTER` build variable | Stage (b) of [roundhouse#91](https://github.com/rubys/roundhouse/issues/91) (plan posted, awaiting a reply) and [spinel-pg #2–#5](https://github.com/rubys/spinel-pg/pulls) (open), then a Spinel `Db` over spinel-pg in place of our libpq lane |
| Patches 10, 20, 30, 60, 71, 74 | About two dozen focused Roundhouse PRs, none opened yet: API-mode controllers ([#163](https://github.com/rubys/roundhouse/issues/163), [#165](https://github.com/rubys/roundhouse/issues/165)), WebSocket lifecycle and Faye API, boot hooks and job drain, Rails-surface gaps (uniqueness, `find_or_create_by!`, `or` scopes, `left_joins`), row locks, integer ranges |
| Patch 00 | On hold until the Duration question is settled |
| Other app changes: typed JSON bodies with `permit` emulation, the HS256 token codec, the recovery initializer, small substitutions | Roundhouse RFCs for typed JSON params and a modeled `jwt` subset, plus small PRs such as lowering `association(:x).loaded?`; none opened |

## Reproduce

You need Docker with BuildKit, git, bash and python3, plus network access to GitHub, rubygems.org (Spinel's `make deps`), Docker Hub, ghcr.io and mcr.microsoft.com. Run the commands from the repository root. Scratch files go to `reproduce/build/`, which git ignores. In the commands below, `R=results/ruby-compile/roundhouse-spinel-conduit-pg-20261002`.

1. **Toolchain sources.** `$R/reproduce/prepare-toolchain.sh` clones [Roundhouse](https://github.com/rubys/roundhouse) at `5bbc4765` and [Spinel](https://github.com/matz/spinel) at `d2c20df0`, checks the patches against [SHA256SUMS](patches/roundhouse/SHA256SUMS) (whose own SHA-256, `5ae60094…`, is the toolchain tag) and applies the [series](patches/roundhouse/series). It writes the build context and compares each vendor tree with the published toolchain's.
2. **Images.** `$R/reproduce/build-images.sh` builds the toolchain image (`v5-toolchain:5ae600946b7e`, the production Dockerfile's default), then the compiled image from [variant/source](variant/source/) (`v5-conduit:compiled`). The targets `cruby reference` add the variant on CRuby and the Rails reference-1 image.
3. **Gate.** `$R/reproduce/run-gate.sh compiled 4410` (or `rails 4410` for the same source on Rails) assembles the gate workspace from `variant/source` and the frozen gate inputs, checks the inputs, and runs the unmodified `tools/one_shot_host/check-production.sh`, [as in v4](../roundhouse-spinel-conduit-pg-20260930/README.md#reproduce).
4. **Edge script.** `python3 $R/evidence/edge/edge_diff.py run IMAGE PORT OUT.json` runs the 166 requests against a fresh PostgreSQL 17, and `edge_diff.py diff A.json B.json` compares two runs.

Checked before publication (2026-10-02, same host):
- **Sources.** `prepare-toolchain.sh` from fresh clones reproduced both published vendor-tree digests. The series applies cleanly, changing 83 files, +3,218/−221.
- **Toolchain image.** It reports `roundhouse 2026.9.18 (5bbc4765)` and `spinel 2026.09.12+4484 (d2c20df0b)`, with image ID `sha256:8b77bd06…`. The apt layers are not bit-reproducible, so expect a different ID.
- **Compiled image.** `build-images.sh compiled` recompiled this package's source on the published toolchain image and produced the published image, `sha256:35e20405…` (`/app/server` SHA-256 `e8d6b30c…`). Other hosts will get a different image ID.
- **Gate.** `run-gate.sh compiled 4410` from this package passed: 17/17 Hurl files, the live protocol, 4/4 Playwright and 13/13 security.
- **Variant source.** [gated-source.sha256](reproduce/gated-source.sha256) hashes the 75 files of the gated workspace other than the ledger, and all of them match `variant/source` (`cd $R/variant/source && sha256sum -c ../../reproduce/gated-source.sha256`). `COMPILE-VARIANT.md` is the gated ledger, except that the v5 section's working-folder references now point into this package; the earlier sections are as published in v4.

Not included: the working notes (the report, the triage of further app reverts and the upstream ledger) and agent messages.
