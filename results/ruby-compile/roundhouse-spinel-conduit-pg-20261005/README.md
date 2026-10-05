# Roundhouse + Spinel: compiled Conduit, v7

**Compiled Conduit builds and passes the fresh-production gate on October 5 upstream heads, with 11 local Roundhouse patches and no Spinel patches.** Upstream retired one whole patch and parts of three others, shrinking the net patch diff from +3,243 to +3,126 lines. The app's login throttle can now raise inside `Mutex#synchronize`, as the Rails original does; two app substitutions remain.

This is a separately labelled **compile variant**, built with a locally patched compiler. It is not the measured one-shot source. **No timing was run** for v7 because the host was shared. The [v4 benchmark](../roundhouse-spinel-conduit-pg-20260930/README.md#benchmark) remains the speed reference and says nothing about v7.

## What changed since v6

| | [v6 (Oct 4)](../roundhouse-spinel-conduit-pg-20261004/README.md) | v7 (Oct 5) |
| --- | --- | --- |
| Roundhouse | `ac1fa43e` + 12 patches | `2b2deff7` + **11 patches**; 85 commits later |
| Net Roundhouse diff | +3,243/−224 | **+3,126/−211** |
| Spinel | `b7d04a903`, unpatched | `c1d108abe`, unpatched; 632 commits later |
| App vs Rails reference-1 | 16 files, +184/−46 | 16 files, **+180/−44** |
| Production gate | pass | **pass** |

**Retired by upstream.** Patch 75's constant-resolution repair and tests are now entirely upstream. Three other patches shrink:

| Upstream change | Removed locally | Patch |
| --- | --- | --- |
| [#427](https://github.com/rubys/roundhouse/pull/427), `444932b1` | Struct, Mutex and JSON::ParserError fix | **75 retired** |
| [#338](https://github.com/rubys/roundhouse/pull/338), `01cf474b` | ActionController::API class | 10 trimmed |
| [804cfee3](https://github.com/rubys/roundhouse/commit/804cfee3), [365b5c99](https://github.com/rubys/roundhouse/commit/365b5c99) | ANY/HEAD route dispatch | 10 trimmed |
| [6623399c](https://github.com/rubys/roundhouse/commit/6623399c275af1542185536deb0d182a11f2ecba) | connection cleanup, WebSocket ensure/retire | 20 trimmed |
| [#289](https://github.com/rubys/roundhouse/pull/289), `7910a309` | password-writer super helper and test | 61 trimmed |

The upstream API class is unchanged; the nosniff default now uses the typed Base initializer. The rebase preserves upstream's body-size checks, WebSocket frame cap and explicit HEAD precedence. Patch 61 still supplies virtual-writer dispatch for an explicitly present nil value.

[#431](https://github.com/rubys/roundhouse/pull/431) fixes finder receiver preservation, not patch 60's other relation behavior or patch 74's integer bounds. Its six execution tests pass on the integrated series ([log](evidence/roundhouse-tests/relation-finders.log)). It retires no hunk here. The [audit](evidence/patch-audit.json), [per-patch scoreboard](evidence/patch-count-comparison.json) and [patch diff](evidence/patch-range-diff.txt) record the decisions. Headline line counts are the net integrated diff; per-patch totals count overlapping edits separately.

## Patches

| Patch | v7 | Why it stays |
| --- | --- | --- |
| [00](patches/roundhouse/00-interval.patch) | kept | GoodJob interval columns |
| [10](patches/roundhouse/10-api-mode-json.patch) | trimmed | JSON controllers, headers and errors |
| [20](patches/roundhouse/20-raw-websocket.patch) | trimmed | Faye's raw WebSocket API |
| [30](patches/roundhouse/30-jobs-boot.patch) | rebased | boot hooks and job drain |
| [50](patches/roundhouse/50-postgresql-lane.patch) | rebased | libpq, structure.sql and codecs |
| [60](patches/roundhouse/60-rails-surface.patch) | rebased | class state, relations and uniqueness |
| [61](patches/roundhouse/61-secure-password-super-and-nil.patch) | trimmed | supplied-nil virtual writers |
| [70](patches/roundhouse/70-linear-pg-placeholder-rewrite.patch) | kept | PostgreSQL placeholder rewriting |
| [71](patches/roundhouse/71-record-lock-and-error-predicate.patch) | rebased | record locks and error predicates |
| [72](patches/roundhouse/72-pg-async-cache.patch) | kept | async libpq and statement cache |
| [74](patches/roundhouse/74-integer-query-range.patch) | rebased | integer query bounds |

The PostgreSQL patches (50, 70, 72) stay because this upstream pin has no PostgreSQL runtime; [roundhouse#91](https://github.com/rubys/roundhouse/issues/91) tracks that work. No new local patch was needed.

## App workarounds

Each restoration was gated separately. One passes and is kept:

| Reference code | v7 result |
| --- | --- |
| Raise inside `Mutex#synchronize` | **Pass**, including 429 rate limiting; restored ([log](evidence/gates/reverts/throttle-raise.log)) |
| Full reference LoginThrottle, or `reject!` alone | 500 instead of 401: missing Array dispatch; keep `select` ([logs](evidence/gates/reverts/)) |
| `association(:author).loaded?` | strict analysis rejects `association` on Article; keep direct read ([log](evidence/gates/reverts/author-loaded.log)) |

Only LoginThrottle changes from v6, apart from the [ledger](variant/source/COMPILE-VARIANT.md). The [source comparison](evidence/source-control.json) and [delta](variant/delta.json) record it; owned size is [6,958 tokens](variant/size.json), excluding structure.sql.

## Validation

| Check | Result |
| --- | --- |
| Fresh-production gate, unmodified | **Pass**: 17/17 Hurl files, live protocol, 4/4 browser, 13/13 security ([compiled](evidence/gates/compiled-v7-production-gate.log), [same source on Rails](evidence/gates/variant-v7-on-rails-production-gate.log)) |
| Control: v6 source on v7 toolchain | Pass ([log](evidence/gates/control-v6-source-on-v7-toolchain-production-gate.log)) |
| Common HTTP probe | 21/21 contract, 3/3 quality ([record](evidence/compiled-v7-common-http-probe.json)) |
| Edge script, 166 recorded responses | 0 differences from v6; the same 7 from Rails reference-1 ([summary](evidence/edge/summary.json), [differences](evidence/edge/v7-rails-diff.log)) |
| Roundhouse tests | 72 passed, 5 ignored in 18 focused suites ([log](evidence/roundhouse-tests/focused.log)); 6 finder tests passed separately |
| Runtime typing | Fully-typed-body check passes; concrete-type check fails: 574 untyped sites, ceiling 537. Both pass unpatched ([patched](evidence/roundhouse-tests/runtime-types-patched.log), [upstream](evidence/roundhouse-tests/runtime-types-upstream.log)) |

The seven edge differences concern whitespace-only email updates, numeric passwords accepted as strings, and one null-password error instead of two, including subsequent reads/logins. Each edge run also makes 25 setup registrations, so it sends 191 scripted requests plus readiness polling. This is a behavior check, not a benchmark.

## Still to do

- **Upstream the remaining patches.** The PostgreSQL runtime and concrete typing remain blockers; the typing ceiling was not raised.
- **Two app substitutions remain:** boxed-Array `reject!` dispatch and Roundhouse's `association(:name)` analysis.
- **Configuration:** `SPINEL_WORKERS=4` is explicit, not derived from CPU quota. Intervals remain strings pending a Duration design. Other application limits remain in the ledger.

## Reproduce

You need Docker with BuildKit, git, bash and python3, plus network access to upstream repositories and registries. Run from the repository root. Resources use `conduit-v7-`, port **4440**, and git-ignored `reproduce/build/` scratch.

```bash
R=results/ruby-compile/roundhouse-spinel-conduit-pg-20261005
"$R/reproduce/prepare-toolchain.sh"
L=$R/reproduce/with-docker-lock.py
python3 "$L" "$R/reproduce/build-images.sh" toolchain compiled cruby reference
python3 "$L" "$R/reproduce/run-gate.sh" compiled 4440
python3 "$L" "$R/reproduce/run-gate.sh" rails 4440
python3 "$L" python3 "$R/reproduce/run-common-probe.py" rails conduit-v7-app:compiled /tmp/v7-probe.json
python3 "$L" python3 "$R/evidence/edge/edge_diff.py" run conduit-v7-app:compiled 4440 /tmp/v7-edge.json
```

`prepare-toolchain.sh` applies the checksummed series to the [full pinned SHAs](run.json) and verifies both vendor digests. `run-gate.sh` verifies frozen input hashes and runs the unmodified host gate. The wrapper takes the repository's shared Docker lock; naming and local BuildKit configuration are handled outside the frozen scripts.

Fresh upstream clones applied all 11 patches and reproduced both digests ([log](evidence/reproduction/prepare-toolchain.log)). That context rebuilt compiled image `sha256:1f06d57a…` ([build](evidence/reproduction/build-images.log), [image records](evidence/image-provenance.json)), and the package's source passed the gate. Apt layers are not bit-reproducible across hosts. The [manifest](reproduce/gated-source.sha256) pins all 75 gated source files, excluding the ledger:

```bash
(cd "$R/variant/source" && shasum -a 256 -c ../../reproduce/gated-source.sha256)
```
