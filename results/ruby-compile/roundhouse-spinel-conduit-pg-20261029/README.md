# Roundhouse + Spinel: compiled Conduit, v12

**Compiled Conduit passes the fresh-production gate on the October 29 heads with 8 Roundhouse patches
and no Spinel patch (v11: 10 + 1).** Upstream retires Roundhouse 82
([#1496](https://github.com/rubys/roundhouse/pull/1496)) and 83
([#1512](https://github.com/rubys/roundhouse/pull/1512)), Spinel 93 (matz's
[`3ca03ede9`](https://github.com/matz/spinel/commit/3ca03ede9188da07cffd4c012607d106e4efd9e7), the fix for
[matz/spinel#10462](https://github.com/matz/spinel/issues/10462)), patch 60's `find_or_create_by!` hunks
([#1513](https://github.com/rubys/roundhouse/pull/1513)) and patch 50's keyless-save guard
([#1263](https://github.com/rubys/roundhouse/pull/1263)). Each of the 8 remaining patches still fails its
one-patch omission. Nothing new broke: the rebase needed context changes only. The 75 gated app files are
byte-identical to v11, and Rails on the same source also passes.

This is a separately labelled **compile variant** with a locally patched toolchain. The measured one-shot
source and earlier records are unchanged. **No performance benchmark was run; no throughput claim is made.**
The [v11 record](../roundhouse-spinel-conduit-pg-20261028/README.md) supplies the previous condition;
[run.json](run.json) holds the pins and artifact identities.

## v11 → v12

| Condition | v11, October 28 | v12, October 29 |
| --- | --- | --- |
| Roundhouse | `295abf08` + 10 patches | `4036ea9c5` + 8 patches |
| Spinel | `3b397d7bc` + 1 patch | `d4e804c62` + 0 patches |
| Net Roundhouse diff | +2,394/−175, 56 files | +2,340/−131, 54 files |
| Net Spinel diff | +5/−0, 1 file | none |
| Production gate | compiled and Rails pass | compiled and Rails pass |
| Common HTTP | 21/21 contract, 3/3 quality | 21/21, 3/3; huge IDs 404 with no Spinel patch |
| Edge vs Rails reference-1 | 5/166 responses | the same 5/166; 0/166 vs v11 |

Heads were observed at 2026-10-29T11:11:15Z with `git ls-remote` ([pins](evidence/initial-pins.json)).
Since v11's pins, Roundhouse gained 130 commits and Spinel 185. The input series is v11's final series
minus 82, 83 and Spinel 93. A fresh public replay of both series matches the recorded vendor digests
([replay](evidence/fresh-replay-01.log)). The [scoreboard](evidence/patch-count-comparison.json),
[integrated Roundhouse diff](evidence/roundhouse-final-combined.diff) and
[retirement checks](evidence/retirement-checks.json) support this comparison.

## Patch scoreboard

| Patch | Decision | Lines | Without it |
| --- | --- | --- | --- |
| [10](patches/roundhouse/10-api-mode-json.patch) | retained; applies cleanly | +84/−1 | 8/17 API files: 401, 403, 404, 422 become 500 |
| [20](patches/roundhouse/20-raw-websocket.patch) | retained; applies cleanly | +347/−16 | `roundhouse check` refuses `EventMachine`, `Faye::WebSocket` |
| [30](patches/roundhouse/30-jobs-boot.patch) | retained; applies cleanly | +419/−1 | gate passes; boot leaves the export `pending` |
| [50](patches/roundhouse/50-postgresql-lane.patch) | retained; **keyless guard retired** | +1,008/−22 | Roundhouse does not compile |
| [60](patches/roundhouse/60-rails-surface.patch) | retained; **bang hunks retired** | +151/−25 | now builds; 16/17: export job's `article["comments_total"]` raises |
| [74](patches/roundhouse/74-integer-query-range.patch) | retained; context rebase | +236/−26 | 16/17 API files: a non-numeric export ID is 500 |
| [80](patches/roundhouse/80-gradual-return-stabilization.patch) | retained; applies cleanly | +87/−40 | live protocol fails |
| [84](patches/roundhouse/84-upstream-regression-mixed-parameter-arm.patch) | retained; applies cleanly | +8/−0 | live protocol fails, as without 80 |
| [82](../roundhouse-spinel-conduit-pg-20261028/patches/roundhouse/82-upstream-regression-quoted-bulk-update.patch) | **retired** (#1496) | v11: +2/−4 | — |
| [83](../roundhouse-spinel-conduit-pg-20261028/patches/roundhouse/83-upstream-regression-temporal-initialize.patch) | **retired** (#1512) | v11: +6/−31 | — |
| [Spinel 93](../roundhouse-spinel-conduit-pg-20261028/patches/spinel/93-upstream-regression-speculative-slot-to-i.patch) | **retired** (`3ca03ede9`) | v11: +5/−0 | — |

"Applies cleanly" patches keep identical +/− lines; only hunk metadata changed. The Spinel series is empty;
its manifest still verifies, so the recipe's layout is unchanged.

**Every retained patch still fails without it.** Each omission is the final series minus that one patch,
built on the same heads ([results](evidence/omission-results.json)). All eight builds compiled Roundhouse
from their own sources ("Compiling roundhouse" in every log); the seven that produced a toolchain carry
seven distinct Roundhouse binaries, none equal to the final `81186a4d…`. Without 84 or 80 the API suite
passes, but the live socket endpoint raises `TypeError: no implicit conversion of LiveRooms::Room into
Integer` ([app log](evidence/omissions/without-84/conduit-v12-gate-conduit-v12-ws-compiled-680-app.log)).
Without 10, error answers become 500 with `ArgumentError: wrong number of arguments (given 0, expected 1)`.
Without 74, `GET /api/user/exports/not-an-export` hits PostgreSQL's bigint cast. Without 20, the image build
stops at `roundhouse check` ([build](evidence/execution/build-without-20-01.log)). Without 50, Cargo stops at
74's call to 50's `postgresql_enabled` ([build](evidence/execution/build-without-50-01.log)). Without 30, the
gate, common HTTP (21/21) and edge comparison (0/166 vs final) pass, but the boot-recovery probe leaves the
seeded export `pending` ([recovery](evidence/omissions/without-30/recovery-without-30.json)). All of these
match v11.

**Without 60 is the one change in kind.** In v11 its emission refused `find_or_create_by!`; now the image
builds, and the gate fails 16/17 on exports only: the export job raises `undefined method '[]' for an instance
of Article` at `article["comments_total"]`, a projected SQL alias read with a String key
([app log](evidence/omissions/without-60/conduit-v12-gate-conduit-v12-ws-compiled-13935-app.log)). So 60 is
needed now for its projection and `[]` hunks; see the probe below for the rest of it.

## Retirements

Each retired patch or hunk is absent from the final series, and the final build and full gate pass without
it. Every retiring commit is an ancestor of the v12 pin and not of the v11 pin
([checks](evidence/retirement-checks.json)), except one dead text substitution noted below.

- **Roundhouse 82**, the doubled table quotes in `update_all`:
  [#1496](https://github.com/rubys/roundhouse/pull/1496) (merge `669a42ee2`). `update_all` now quotes
  `@model.table_name` once through the adapter instead of reusing the already-quoted `_table_sql`.
- **Roundhouse 83**, a Time stored into the raw String slot on create:
  [#1512](https://github.com/rubys/roundhouse/pull/1512) (merge `3578a8ca2`). `synth_initialize` normalizes
  temporal inputs before the raw writer sees them.
- **Spinel 93**, 100-digit IDs raising `RangeError`: matz's
  [`3ca03ede9`](https://github.com/matz/spinel/commit/3ca03ede9188da07cffd4c012607d106e4efd9e7), committed to
  master (no PR) as the fix for [matz/spinel#10462](https://github.com/matz/spinel/issues/10462), the regression v11 found.
  `sp_poly_slot_i` now reads a boxed String with `strtoll`, the same code as 93. Both 100-digit ID cases in
  common HTTP answer 404 ([probe](evidence/compiled-v12-common-http-probe.json)).
- **Patch 60's `find_or_create_by!` hunks**: [#1513](https://github.com/rubys/roundhouse/pull/1513)
  (merge `4036ea9c5`, the pinned head). It inlines Conduit's two blockless bang calls with record-valued
  conditions, including the one under `unless`, as `find_by` + `new` + `save!`
  ([emitted](evidence/emitted-excerpts.txt)). Dropped: all of 60's `first_or_create.rs` (its branch
  wrapping is now upstream verbatim; the `first_or_create!` claim), the three `find_or_create_by!`
  admissions in `scope_chain.rs`, and their test. 60 goes from +190/−32 to +151/−25.
- **Patch 50's keyless-save guard** in `base.rb` and `connection.rb`:
  [#1263](https://github.com/rubys/roundhouse/pull/1263) (merge `11dc38fcb`). `save` skips `id=` when
  `primary_key` is nil, and a plain `create_table id: false` now emits `primary_key` as nil. Conduit's
  `db/schema.rb` declares `favorites` and `follows` that way. #1263 as merged covers only this guard: 50's
  two test-emission hunks (CZ50-24 and CZ50-25 in the ledger) stay local, and the gate cannot exercise them
  because the image build excludes `test/`.
- **Two dead text substitutions in patch 50's `postgresql_files`**, which matched nothing: the
  `active_support_ext.rb` one, already dead at the v11 pin (upstream `2d7a585dc`), and the `qcol` one in
  `relation.rb`, dead since `bd51b6974` ([#1484](https://github.com/rubys/roundhouse/pull/1484)) quotes that
  column itself. The emitted Spinel tree is byte-identical with and without them (451 files). 50 goes from
  +1,015/−24 to +1,008/−22.

**Rebase adaptations, not regressions.** 50 conflicted on context with upstream `6bb468425` (Oct 28 11:20Z,
after the v11 pin), a PostgreSQL `Dialect` for the Ruby target: the Arel visitor keeps upstream's dialect
code beside 50's `RH_DATABASE_ADAPTER` branches, which the Spinel target still needs, since only the Ruby
target scopes the new dialect. `target_files_inner` now runs both 50's `postgresql_files` and upstream's new
`apply_spinel_int_overflow` (`5fa181268`). 74 conflicted on context only: `column_predicate` keeps upstream's
new column quoting (`bd51b6974`) and adds 74's integer-limit check after it.

## New upstream regressions

None. The reduced series passes the gate on the first build, and no omission fails in a new way except
without-60, whose new failure is the expected next layer once #1513 lowers the bang calls.

## Probe: how much of 60 is still needed

This probe is **not part of the series**. 60 was cut to its projection and String `[]` hunks, in
`base.rb`, `base.rbs` and `model_to_library/schema.rs` (+47/−20; [patches](evidence/probes/60core/patches)).
Dropped: the typed-record `.id` predicates, zero-argument scope entries, `find_each` and `update_all` class
roots, the `to_set` require, and the tests. Emission changes: `require "set"` disappears, and
`ArticleShare.active(…)` replaces `__scope_active__0(…)`. It passes everything the final passes: the gate
(17/17, live, 4/4, 13/13), common HTTP (21/21, 3/3), the edge comparison (0/166 vs the final) and boot
recovery ([result](evidence/probes/60core/result.json)). When those hunks stopped mattering was not
bisected; v11 never tested them separately. The series keeps the full rebased 60, because the one-patch
omissions ran against it; the next pin can start from the probe's 60.

## Validation

| Check | v12 result |
| --- | --- |
| Compiled fresh-production gate | 17/17 API files, live protocol, 4/4 browser, 13/13 security |
| Same app on Ruby 4.0.7 Rails | same checks pass; source identical to v11 |
| Common HTTP probe | 21/21 contract, 3/3 quality |
| Edge comparison | 5/166 vs Rails reference-1, the same 5 as v11; 0/166 vs v11 |
| Pending export at boot | pending → done, completed timestamp present |
| Fresh patch replay | both vendor digests match; both manifests verify |

Evidence: [compiled gate](evidence/execution/compiled-gate-01.log), [Rails gate](evidence/execution/rails-gate-01.log),
[common probe](evidence/compiled-v12-common-http-probe.json), [edge summary](evidence/edge/summary.json),
[recovery](evidence/recovery/recovery-final.json), [source verification](evidence/source-verification.json).
The gate's app binary (`server_sha256` `74968722…`) runs from the recorded compiled image
([identity](evidence/execution/container-logs/conduit-v12-gate-conduit-v12-ws-compiled-95082-app-binary.json)).
The edge baseline is v11's recorded fresh Rails reference-1 run; Rails reference-1 was not rebuilt.

## Timings against v11

| Measure | v11 | v12 |
| --- | --- | --- |
| Toolchain + compiled build | 234 s (Spinel 59.3 s) | 244 s (Spinel 46.2 s) |
| Cargo build / app spin build | 103.7 s / 55.5 s | 128.0 s / 40.1 s |
| Compiled gate (app build in it) | 265 s (61.0 s) | 230 s (41.3 s) |
| Rails gate | 21.8 s | 26.5 s |
| Analysis / emission peak RSS | 45,492 / 55,656 KiB | 45,896 / 56,656 KiB |

The Cargo figure includes a cold dependency build, because the cache mounts now carry this condition's
`conduit-v12-cargo-*` ids (v11 reused v10's). Peak RSS comes from each final compiled gate's build and rose
1% and 2%. This host is shared, so wall times are records, not measurements ([timings](evidence/timing-vs-v11.json)).
The hardening check `s09_oversized_body` again passes slowly: 156 s, against 182 s in v11 and 65 s in v10;
not investigated. The compiled image is 121.4 MB (v11: 121.3 MB).

## Reproduce

Use Docker with BuildKit, git, bash and python3. Run from the AgentMVC repository root. Use a lock shared
with every other Docker job on the host, `conduit-v12-` resources and port **4491**. The
[adapter](reproduce/bin/docker) leaves frozen host scripts unchanged and stops work if a container start
exceeds 120 seconds. [`fresh-build.sh`](reproduce/fresh-build.sh) refreshes the Roundhouse source mtimes
inside the lock, so a shared Cargo cache cannot serve a stale binary. No binary or generated build tree is
required in Git.

```bash
R=results/ruby-compile/roundhouse-spinel-conduit-pg-20261029
L=$R/reproduce/with-docker-lock.py
export AGENTMVC_DOCKER_LOCK=.work/lane-docker.lock BUILD_DIR=/tmp/v12-build RECOVERY_BUILD_DIR=/tmp/v12-build
python3 "$R/reproduce/prepare-toolchain.py" "$BUILD_DIR"
python3 "$L" "$R/reproduce/fresh-build.sh" "$R/reproduce/build-images.sh" toolchain compiled
python3 "$L" "$R/reproduce/run-gate.sh" compiled 4491
python3 "$L" "$R/reproduce/run-gate.sh" rails 4491
python3 "$L" python3 "$R/reproduce/run-common-probe.py" rails conduit-v12-app:compiled /tmp/v12-common.json
python3 "$L" python3 "$R/evidence/edge/edge_diff.py" run conduit-v12-app:compiled 4491 /tmp/v12-edge.json
python3 "$L" python3 "$R/evidence/recovery/probe.py" reproduce conduit-v12-app:compiled done
```

Roundhouse is pinned to `4036ea9c5db615e831971c0b4f8629e6405ffca0`; Spinel to
`d4e804c62772189004ee7d147dd6436b2aff5730` (`2026.10.25+1053`). The toolchain step fetches both from their
public repositories, replays both series and verifies each manifest and vendor-tree digest. Apt layers are
not bit-reproducible across hosts. The recipe is v11's with v12 names, port, pins and manifests; the only
other change is the cache ids. Final patch, image, source and binary identities are in [run.json](run.json).

The [source manifest](reproduce/gated-source.sha256) pins the 75 gated files, excluding the ledger:

```bash
(cd "$R/variant/source" && shasum -a 256 -c ../../reproduce/gated-source.sha256)
```

**Cleanup.** No `conduit-v12-` containers or networks remain, and no volume or prune operation ran
([cleanup](evidence/cleanup.json)). The `conduit-v12-` images and Cargo cache mounts are kept, since the
rules allow removing only containers. Build folders were deleted after the run. One step record is an
operator error: `probe-60core-recovery-01` failed before any Docker work because a shell variable was unset;
`-02` is the real run.

## Notes (chronological)

- 11:11Z: heads pinned. Input series: v11's final series minus 82, 83 and Spinel 93.
- Applying v11's patches one by one to the bare v12 head: 10, 20, 30, 80 and 84 apply cleanly;
  50, 60 and 74 need a rebase; 82, 83 and Spinel 93 no longer apply because upstream changed the
  same lines.
- **82 is retired by [rubys/roundhouse#1496](https://github.com/rubys/roundhouse/pull/1496)**
  (merge `669a42ee2`): `update_all` now quotes `@model.table_name` once through the adapter, not
  `_table_sql`.
- **83 is retired by [rubys/roundhouse#1512](https://github.com/rubys/roundhouse/pull/1512)**
  (merge `3578a8ca2`): `synth_initialize` normalizes temporal inputs before the raw String writer.
- **Spinel 93 is retired by matz/spinel
  [`3ca03ede9`](https://github.com/matz/spinel/commit/3ca03ede9188da07cffd4c012607d106e4efd9e7)**, the fix
  for [matz/spinel#10462](https://github.com/matz/spinel/issues/10462): `sp_poly_slot_i` reads a boxed
  String with `strtoll`, the same code as 93.
- **Patch 50, rebased:** its keyless-save guard in `base.rb` and `connection.rb` is retired by
  [#1263](https://github.com/rubys/roundhouse/pull/1263) (merge `11dc38fcb`), which skips `id=` when
  `primary_key` is nil. Conduit's `db/schema.rb` declares `favorites` and `follows` with `id: false`,
  so #1263 marks both tables keyless. Two context conflicts came from upstream `6bb468425` (a PostgreSQL
  `Dialect` for the Ruby target, Oct 28 11:20Z): the visitor keeps upstream's dialect code and patch 50's
  `RH_DATABASE_ADAPTER` branches side by side, and `target_files_inner` runs both `postgresql_files` and
  upstream's new `apply_spinel_int_overflow`. Two of 50's text substitutions matched nothing and were
  trimmed: the `active_support_ext.rb` one, already dead at the v11 pin (upstream `2d7a585dc`), and the
  `qcol` one, dead since `bd51b6974` (#1484) quotes that column itself. The emitted Spinel tree is
  byte-identical with and without the two lines (451 files).
- **Patch 60, rebased:** its `find_or_create_by!` hunks are retired by
  [#1513](https://github.com/rubys/roundhouse/pull/1513) (merge `4036ea9c5`), which inlines Conduit's
  two blockless bang calls, including the one under `unless`. Dropped: all of `first_or_create.rs`
  (branch wrapping, now identical upstream; the `first_or_create!` claim), the three `find_or_create_by!`
  admissions in `scope_chain.rs`, and their test. Kept: projections, `read_attribute`, String `[]` keys,
  typed-record `.id` predicates, zero-argument scope entries, `find_each` and `update_all` class roots,
  `to_set`.
- **Patch 74, rebased:** context only; `column_predicate` keeps upstream's new column quoting
  (`bd51b6974`) and adds 74's integer-limit check after it.
- Local check: the rebased Roundhouse builds with Rust 1.98.1, `roundhouse check` reports 0 errors, and
  strict Spinel emission succeeds on the gated source.
- 11:23Z: a fresh public replay of both series matches the recorded vendor digests
  ([replay](evidence/fresh-replay-01.log)). Toolchain plus compiled image: 244 s
  ([build](evidence/execution/build-final-01.log)); "Compiling roundhouse" is in the log; the toolchain's
  Roundhouse binary is `81186a4d…`. Cargo caches use new `conduit-v12-cargo-*` ids (v11 shared v10's).
- 11:28Z: **the compiled fresh-production gate passes**: 17/17 API files, live protocol, 4/4 browser,
  13/13 security, exit 0 in 230 s ([gate](evidence/execution/compiled-gate-01.log)). The hardening
  check `s09_oversized_body` again passes slowly: 156 s (v11 182 s, v10 65 s).
- 11:32Z: common HTTP 21/21 contract and 3/3 quality; both 100-digit ID cases answer 404 with no Spinel
  patch ([probe](evidence/compiled-v12-common-http-probe.json)). Edge comparison: 0/166 responses differ from
  v11's final, and the same 5/166 differ from Rails reference-1 as in v11 ([edge](evidence/edge/summary.json)).
  Boot recovery: the seeded export goes pending → done ([recovery](evidence/recovery/recovery-final.json)).
  The same source on Ruby 4.0.7 Rails passes the gate ([Rails gate](evidence/execution/rails-gate-01.log)).
- 11:33Z: one-patch omissions started, smallest patch first: 84, 10, 80, 60, 74, 20, 30, 50.
- Without 84: built (Roundhouse recompiled), gate exit 1: API 17/17, then the live protocol times out
  waiting for presence; the app log shows `TypeError: no implicit conversion of LiveRooms::Room into
  Integer` on `GET /api/shares/:id/live`, as in v11. **84 stays.**
- Without 10: built, gate exit 4: API 8/17; 401, 403, 404 and 422 answers become 500 with `ArgumentError:
  wrong number of arguments (given 0, expected 1)`, as in v11. **10 stays.**
- Without 80: built, gate exit 1: API 17/17, live protocol fails with the same `LiveRooms::Room` into
  Integer `TypeError` as without 84, as in v11. **80 stays.**
- Without 60: **the build now succeeds** (in v11 emission refused `find_or_create_by!`; #1513 lowers it
  now). Gate exit 4: API 16/17; the export job raises `undefined method '[]' for an instance of Article`
  (`article["comments_total"]`, a projected SQL alias read with a String key), so
  `GET /api/user/exports/:id` stays `pending` where the test expects `done`. **60 stays**, for its
  projection and `[]` hunks at least.
- Without 74: built, gate exit 4: API 16/17; `GET /api/user/exports/not-an-export` answers 500 with
  `SQLSTATE 22P02: invalid input syntax for type bigint`, as in v11. **74 stays.**
- Without 20: Roundhouse compiles (binary `5da9b2fa…`), but the image build stops at `roundhouse check`:
  six `error[unsupported]` constants, `EventMachine` and `Faye::WebSocket` in `live_rooms.rb` and
  `live_socket.rb`, as in v11. The gate's first step builds the same Dockerfile, so it fails too.
  **20 stays.**
- Without 30: the gate passes (17/17, live, 4/4, 13/13), common HTTP is 21/21 + 3/3 and the edge run
  matches the final on 0/166 differences, but the boot-recovery probe leaves the seeded export `pending`
  (expected `done`), as in v11 ([recovery](evidence/omissions/without-30/recovery-without-30.json)).
  **30 stays.**
- Without 50: Roundhouse does not compile: `error[E0425]: cannot find function postgresql_enabled`, which
  74 calls; 50 is also the libpq backend the gate's PostgreSQL needs. As in v11. **50 stays.**
- 12:07Z: all eight omissions done; every retained patch fails without it. Each build log shows
  "Compiling roundhouse", and each toolchain that built carries its own Roundhouse binary
  ([results](evidence/omission-results.json)).
- 12:08Z: extra probe, not part of the series: 60 cut to its projection and String `[]` hunks
  (+47/−20), to see whether its other hunks still matter.
- 12:15Z: the probe passes the gate (17/17, live, 4/4, 13/13), common HTTP 21/21 + 3/3, and the edge run
  (0/166 vs the final). Boot recovery: pending → done (`probe-60core-recovery-02`; `-01` failed before any
  Docker work on an unset shell variable).
- 12:18Z: cleanup check: no `conduit-v12-` containers or networks remain; images and cache mounts kept.
