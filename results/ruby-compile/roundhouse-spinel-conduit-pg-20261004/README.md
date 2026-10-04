# Roundhouse + Spinel: compiled Conduit, v6

**Compiled Conduit still builds and passes the fresh-production gate on today's upstream heads: Roundhouse `main` with 12 local patches, and Spinel `master` with none.** Upstream merged fixes that retire parts of three patches. A new upstream regression in constant resolution needed one new patch. The app itself is unchanged from [v5](../roundhouse-spinel-conduit-pg-20261002/README.md).

This is a separately labelled **compile variant**, built with a locally patched compiler. It is not the measured one-shot source. **No timing was run** for v6, because the host was shared. The [v4 benchmark](../roundhouse-spinel-conduit-pg-20260930/README.md#benchmark) remains the reference and says nothing about v6.

## What changed since v5

| | v5 (Oct 2) | v6 (Oct 4) |
| --- | --- | --- |
| Roundhouse | `5bbc4765` + 11 patches (+3,218/−221) | `ac1fa43e`, 332 commits later, + **12 patches (+3,243/−224)** |
| Spinel | `d2c20df0`, unpatched | `b7d04a903`, 339 commits later, unpatched |
| App vs Rails reference-1 | 16 files, +184/−46 | unchanged |
| Production gate | pass | **pass** |

**Retired by upstream.** Four merged PRs replaced pieces of our patches. They removed hunks, not whole patches, so the count didn't fall:

| PR | Upstream now does | Removed from |
| --- | --- | --- |
| [#297](https://github.com/rubys/roundhouse/pull/297) | parses pg_dump's `\restrict` lines | patch 50 |
| [#304](https://github.com/rubys/roundhouse/pull/304) | allows an app with no root route | patch 10 |
| [#376](https://github.com/rubys/roundhouse/pull/376) | preloads scope-free associations | patch 50 |
| [#384](https://github.com/rubys/roundhouse/pull/384) | lowers `left_joins` in scope bodies | patch 60 |

[#299](https://github.com/rubys/roundhouse/pull/299) (`limit: 8` as bigint) also landed; v5 had no hunk for it to retire.

**A new regression, found and bisected.** The first v6 gate failed at `PUT /api/shares/:id/article`. Generated code raised "constant not supported" for `Mutex` and a local `Room` Struct, and two rescue clauses lost `JSON::ParserError`. The cause is Roundhouse commit [78169247](https://github.com/rubys/roundhouse/commit/78169247c9156acf7d2abde58dbc75e0f27685c0) ("Use Rubydex to resolve Ruby constants", [#279](https://github.com/rubys/roundhouse/pull/279)). A minimal emitted-Ruby test [passes on its parent](evidence/roundhouse-tests/stdlib-pre-rubydex.log) and [fails on it](evidence/roundhouse-tests/stdlib-at-rubydex.log). New [patch 75](patches/roundhouse/75-stdlib-constant-resolution.patch) registers `Struct`, `Mutex` and `JSON::ParserError`, keeps capability errors on targets without them, and adds an execution test. With it, the test and the full gate pass ([before](evidence/gates/initial-constant-failure.log), [after](evidence/roundhouse-tests/stdlib-constants-after.log)).

The [patch audit](evidence/patch-audit.json), [per-patch counts](evidence/patch-count-comparison.json) and [range diff](evidence/patch-range-diff.txt) record every change.

## Patches

| Patch | v6 | Why it's still needed |
| --- | --- | --- |
| [00](patches/roundhouse/00-interval.patch) | kept | GoodJob's interval column |
| [10](patches/roundhouse/10-api-mode-json.patch) | trimmed | API-mode JSON controllers and errors; [#338](https://github.com/rubys/roundhouse/pull/338) is open |
| [20](patches/roundhouse/20-raw-websocket.patch) | kept | Faye's raw WebSocket API |
| [30](patches/roundhouse/30-jobs-boot.patch) | rebased | boot hooks and job drain |
| [50](patches/roundhouse/50-postgresql-lane.patch) | trimmed | the libpq runtime, structure.sql, PostgreSQL codecs |
| [60](patches/roundhouse/60-rails-surface.patch) | trimmed | class state, relation copies, uniqueness, `find_or_create_by!` |
| [61](patches/roundhouse/61-secure-password-super-and-nil.patch) | kept | the secure-password writer; [#289](https://github.com/rubys/roundhouse/pull/289) is open |
| [70](patches/roundhouse/70-linear-pg-placeholder-rewrite.patch) | kept | PostgreSQL placeholder rewriting |
| [71](patches/roundhouse/71-record-lock-and-error-predicate.patch) | kept | record locks and error predicates |
| [72](patches/roundhouse/72-pg-async-cache.patch) | kept | async libpq and its prepared-statement cache |
| [74](patches/roundhouse/74-integer-query-range.patch) | rebased | integer query bounds |
| [75](patches/roundhouse/75-stdlib-constant-resolution.patch) | **new** | the constant-resolution regression above |

The PostgreSQL lane (50, 70, 72) stays local because upstream has no PostgreSQL runtime yet; [roundhouse#91](https://github.com/rubys/roundhouse/issues/91) plans one. The rebase also adapted patch 10 to upstream's new password validations and kept upstream's array-ID dispatch in patch 74.

## App workarounds

Both remaining workarounds were restored one at a time and gated. Neither passes yet, so both stay:

| Reference code | v6 result |
| --- | --- |
| LoginThrottle as written in Rails | failed logins answer 500 (`Array#reject!` has no dispatch), or 511 instead of 429 when raising inside `synchronize` ([logs](evidence/gates/reverts/)) |
| `association(:author).loaded?` | strict analysis rejects `association` on `Article` ([log](evidence/gates/reverts/author-loaded.log)) |

Every source file except the [ledger](variant/source/COMPILE-VARIANT.md) is byte-identical to v5 ([comparison](evidence/source-control.json)).

## Validation

| Check | Result |
| --- | --- |
| Fresh-production gate, unmodified | **Pass**: 17/17 Hurl files, live protocol, 4/4 browser, 13/13 security ([compiled](evidence/gates/compiled-v6-production-gate.log), [same source on Rails](evidence/gates/variant-v6-on-rails-production-gate.log)) |
| Control: v5's source on the v6 toolchain | Pass ([log](evidence/gates/control-v5-source-on-v6-toolchain-production-gate.log)) |
| Common HTTP probe | 21/21 contract, 3/3 quality ([record](evidence/compiled-v6-common-http-probe.json)) |
| Edge script, 166 requests | 0 differences from v5; the same 7 from Rails reference-1 as before ([summary](evidence/edge/summary.json), [the 7](evidence/edge/v6-rails-diff.log)) |
| Roundhouse tests | 49 passed in 14 focused suites ([log](evidence/roundhouse-tests/focused.log)). The runtime typing test fails with our patches, 559 untyped sites against a ceiling of 521, and passes unpatched ([log](evidence/roundhouse-tests/runtime-types-patched.log)) |

The seven edge differences are unchanged since v4: a whitespace-only email is accepted on update, a numeric password is accepted as a string, and a null password returns one error message instead of two.

## Still to do

- **Upstream the patches.** Patch 75 is a clear candidate: it's a small regression fix with a test. #338 and #289 are open, the PostgreSQL lane waits on #91, and the typing ceiling must hold before the runtime hunks can land.
- **The app's last two workarounds** need Spinel to dispatch `Array#reject!` and Roundhouse to analyse `association(:name)`.
- **Configuration:** `SPINEL_WORKERS=4` is set explicitly, not derived from the CPU quota. Intervals are still stored as strings, pending a Duration design.

## Reproduce

You need Docker with BuildKit, git, bash and python3, plus network access to the upstream repositories and registries. Run from the repository root. Resources use the `conduit-v6-` prefix, the gate uses port **4420**, and scratch goes to the git-ignored `reproduce/build/`.

```bash
R=results/ruby-compile/roundhouse-spinel-conduit-pg-20261004
"$R/reproduce/prepare-toolchain.sh"
L=$R/reproduce/with-docker-lock.py
python3 "$L" "$R/reproduce/build-images.sh" toolchain compiled cruby reference
python3 "$L" "$R/reproduce/run-gate.sh" compiled 4420
python3 "$L" "$R/reproduce/run-gate.sh" rails 4420
python3 "$L" python3 "$R/reproduce/run-common-probe.py" rails conduit-v6-app:compiled /tmp/v6-probe.json
python3 "$L" python3 "$R/evidence/edge/edge_diff.py" run conduit-v6-app:compiled 4420 /tmp/v6-edge.json
```

`prepare-toolchain.sh` verifies the patch manifest, applies the series to the pinned SHAs and checks both vendor-tree digests. `run-gate.sh` checks the frozen input hashes and runs the unmodified `tools/one_shot_host/check-production.sh`. The wrapper takes the repository's shared Docker lock.

Checked before publishing: fresh clones reproduced both vendor-tree digests and applied all 12 patches ([log](evidence/reproduction/prepare-toolchain.log)). That context rebuilt compiled image `sha256:e668f082…` ([build log](evidence/reproduction/build-images.log), [image records](evidence/image-provenance.json)); apt layers aren't bit-reproducible, so other hosts may get different image IDs. The gate passed from the package's own source, and [gated-source.sha256](reproduce/gated-source.sha256) pins the 75 gated source files:

```bash
(cd "$R/variant/source" && shasum -a 256 -c ../../reproduce/gated-source.sha256)
```
