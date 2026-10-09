# Roundhouse + Spinel: compiled Conduit, v8

**Compiled Conduit uses Ruby 4.0.7 and passes the fresh-production gate on October 9 upstream heads,
with 10 local Roundhouse patches and no Spinel patches.** Upstream retires the supplied-nil password
writer patch and parts of five others. Patch 10 remains +333/−60 in 23 files; upstream supplies its
409/422 reason phrases. Two app substitutions remain.

This is a separately labelled **compile variant**, built with a locally patched compiler. It is not
the measured one-shot source. **No timing was run** on the shared host, and no throughput claim is
made for v8. The [v4 benchmark](../roundhouse-spinel-conduit-pg-20260930/README.md#benchmark) remains
the historical speed reference.

## What changed since v7

**Ruby 4.0.7 replaces 3.3.2** in the variant and toolchain build stages. The same variant passes the
unmodified gate on Rails with Ruby 4.0.7. Gemfile and Gemfile.lock are unchanged. Published
[v7](../roundhouse-spinel-conduit-pg-20261005/README.md) and
[v6](../roundhouse-spinel-conduit-pg-20261004/README.md) stay byte-identical
([manifest check](evidence/historical-packages-preserved.json)).

| | v7 (Oct 5) | v8 (Oct 9) |
| --- | --- | --- |
| Ruby, variant/toolchain | 3.3.2 | **4.0.7** |
| Roundhouse | `2b2deff7` + 11 patches | `ea4d3e68` + **10 patches** |
| Spinel | `c1d108abe`, unpatched | `f85f04b3a`, unpatched |
| Net Roundhouse diff | +3,126/−211 | **+2,874/−223** |
| App vs Rails reference-1 | 16 files, +180/−44 | **unchanged** |
| Production gate | pass | **pass**, compiled and Ruby 4.0.7 Rails |

**Retired by upstream.** The [scoreboard](evidence/patch-count-comparison.json) names every change
and gives each v7 patch's old and current counts.

| Upstream change | Removed locally | Patch |
| --- | --- | --- |
| [#492](https://github.com/rubys/roundhouse/pull/492), `7eef3e91` | supplied-nil secure-password writer dispatch | **61 retired** |
| [#498](https://github.com/rubys/roundhouse/pull/498), `a3a7f5a6` | 409/422 reason phrases, two lines | 10 trimmed |
| [#493](https://github.com/rubys/roundhouse/pull/493), `561ade09` | scoped `exists?` Hash conditions and signature | 74 trimmed |
| [#442](https://github.com/rubys/roundhouse/pull/442), `6a90ec00`, `514a35bb`, `0264ca75` | library class instance variable initializer ordering | 60 trimmed |
| [#671](https://github.com/rubys/roundhouse/pull/671), `71b18af4` | manual `with_lock` analysis registration | 71 trimmed |
| [#648](https://github.com/rubys/roundhouse/pull/648), `80283c96` | duplicate JSONB enum and schema ingestion | 50 rebased |

Since v7, [#441](https://github.com/rubys/roundhouse/pull/441), `f8fa7108`, also replaces patch 60's
SecurityUtils runtime/signature/shipping work. [65d69088](https://github.com/rubys/roundhouse/commit/65d690883e02880ecb8c14194f65d01a033c6314)
replaces Relation spawn/copy; [#494](https://github.com/rubys/roundhouse/pull/494), `a184e2b7`, replaces
the model `find_by` facade; [#438](https://github.com/rubys/roundhouse/pull/438), `74f61e16`, replaces
the scoped finder override. These were already in the unpublished October 7 template. This package
replaces that unpublished build as v8.

[#466](https://github.com/rubys/roundhouse/pull/466), `dbf99aa`, and
[#467](https://github.com/rubys/roundhouse/pull/467), `6610d160`, strengthen Tep request framing.
Their Content-Length refusal and incomplete-body checks are preserved. They do not supply request
header exposure or peer propagation and retire no such local hunk.

**Removed after gating.** Patch 70, Patch 72 pass their isolated removal gates. They are omitted from the final combined series, which passes all production gates and comparisons. These are gate-only removals; no upstream implementation is credited for unchanged behavior ([trials](evidence/patch-ablation/results.json), [selection](evidence/patch-ablation/selection.json)).

## Patches

| Patch | v8 decision | Per-patch lines |
| --- | --- | --- |
| [00](patches/roundhouse/00-interval.patch) | kept | +10/−1 |
| [10](patches/roundhouse/10-api-mode-json.patch) | trimmed | +333/−60 |
| [20](patches/roundhouse/20-raw-websocket.patch) | rebased | +350/−17 |
| [30](patches/roundhouse/30-jobs-boot.patch) | trimmed | +420/−1 |
| [50](patches/roundhouse/50-postgresql-lane.patch) | rebased | +967/−29 |
| [60](patches/roundhouse/60-rails-surface.patch) | trimmed | +359/−46 |
| 61 | retired | +0/−0 |
| 70 | retired | +0/−0 |
| [71](patches/roundhouse/71-record-lock-and-error-predicate.patch) | trimmed | +82/−0 |
| 72 | retired | +0/−0 |
| [74](patches/roundhouse/74-integer-query-range.patch) | trimmed | +244/−30 |
| [80](patches/roundhouse/80-gradual-return-stabilization.patch) | new | +87/−40 |
| [81](patches/roundhouse/81-reload-receiver-type.patch) | new | +24/−1 |

The net integrated diff is +2,874/−223 in 74 files. Per-patch sums are
+2,876/−225; overlapping edits count separately.
See the [range diff](evidence/patch-range-diff.txt) and [upstream log](evidence/upstream/roundhouse-since-template.log).

Patch 30 keeps boot-hook ingestion and invocation, +420/−1 in eight files. Removing the whole patch
passes the fresh-production gate, but leaves a durable pending export pending at startup. The
retained boot code recovers it; the final ten-patch image passes the same supplemental check
([without 30](evidence/recovery/no30.json), [final image](evidence/recovery/final10.json)). Queue/dequeue,
adapter-state mutex and per-job connection-lease refinements are removed because the gate does not
require them. This trim is not upstream coverage.

Patch 80 is new relative to v7 and inherited from the unpublished October 7 template. Removing it
passes all 17 API files, then breaks live editing with `TypeError: no implicit conversion of
LiveRooms::Room into Integer` ([trial](evidence/patch-ablation/no80.log),
[server](evidence/patch-ablation/no80-app.log)). Unknown return arms must survive stabilization.

Upstream's new `db_pg.rb` is a spinel-pg shim that project generation does not select at this pin
([0d467e0c](https://github.com/rubys/roundhouse/commit/0d467e0c)). It stays byte-identical; the local,
gate-selected libpq backend is named `db_libpq.rb`. PostgreSQL generation keeps upstream's JSONB
schema distinction, generated-column INSERT behavior and public locking API. PostgreSQL-specific
transaction/reload integration, text-array codecs and integer-width bounds remain local.
Removing backend selection causes 18 native refusals for missing PostgreSQL codec, insert and
locking methods. Removing patch 60's independent files fails strict emission on scoped
`find_or_create_by!` in favorites and profiles ([dependency trials](evidence/patch-ablation/surface-results.json)).

**A new current-head repair, patch 81, preserves the model receiver of `reload`.** Upstream
[c523d780](https://github.com/rubys/roundhouse/commit/c523d7807941aa8f1224a24820443fa2898eb593)
changes its catalog return to ActiveRecord::Base. The app then loses ArticleShare/Article methods
after reload. Fresh `Widget.find(id).reload.label` passes on parent `8fda5b88` and fails on that commit
([paired checks](evidence/reload/introduction.json)). Assigning the concrete receiver during model
registration fixes the gate; the fresh example executes natively on Linux and macOS
([public source](evidence/reload/public-app/), [Linux](evidence/reload/native-linux.log)).

## Patch 10: what remains

Only the 409/422 reason-table entries retire since v7: +335/−60 becomes **+333/−60**, still in
**23 files**. The [59-hunk ledger](evidence/patch10/hunks.json) identifies each retained range,
its failure, a small fresh generic Rails example and its coverage. Signatures, registration,
initialization, reset and shared-helper callsites support the runtime behavior; comments and tests
are not additional features.

| Remaining behavior | Failure it prevents |
| --- | --- |
| Response headers and integer statuses | missing `set_header`, absent nosniff, dynamic integer code rejected |
| BadRequest and ParseError | unresolved exception constants in API rescue handlers |
| Request headers and authorization | empty or missing bearer-token access; case-sensitive header lookup |
| Keyed validation errors | `to_hash` rejected or attributes lost; stale messages after a second validation |
| Callback/rescue JSON and handler order | JSON body not encoded; inherited rescue wins over subclass |
| HTTP envelope, UTC and peer address | wrong charset/empty-response header, `+00:00` suffix, empty `remote_ip` |

The unmodified production gate directly covers authentication, JSON errors, keyed messages and
nosniff. Fresh public runtime probes fail **11/11** on unpatched heads and pass **11/11** with the
retained patch ([results](evidence/patch10/runtime-results.json)). The generic API's stock analysis
fails on missing exception/error surfaces; patched analysis and emission have zero errors
([results](evidence/patch10/public-probes.json)). Native generic HTTP: **15/15 checks pass**
([record](evidence/patch10/patch10-http.json)). Tableless forms, overlapping subclass rescues,
304 header omission, UTC suffix and peer isolation have supplemental coverage; the frozen app does
not independently isolate every branch.

Five fresh emitted validator cases pass, including association, password/confirmation, length and
keyed-message behavior. Four fail: current source ingestion ignores inclusion, format and
numericality, also on v7 and the October 7 template. Their IR helper callsites are mechanical
dependencies of the shared keyed-message helper, not a claim that these source declarations work
([execution](evidence/patch10/patch10-validator-execution-final.log),
[provenance](evidence/patch10/validation-ingestion-provenance.json)). Dynamic error owner/message
expressions execute once ([fresh example](evidence/patch10/snippets/dynamic_errors.rb),
[execution](evidence/patch10/dynamic-errors-execution.log)). All public examples were written fresh.

## App workarounds

Each remaining substitution was restored and gated separately; neither passes.

| Reference code | v8 result |
| --- | --- |
| `association(:author).loaded?` | analysis rejects `association` on Article, despite successful lowering/emission ([log](evidence/gates/reverts/author.log)) |
| Full reference LoginThrottle | 500 instead of 401: Array `reject!` dispatch missing ([gate](evidence/gates/reverts/throttle.log), [app log](evidence/gates/reverts/throttle-app.log)) |

Keep the direct author read and `select` assignment. The raise inside `Mutex#synchronize`, restored
in v7, remains unchanged. No new app substitution is added. Only `.ruby-version` and Dockerfile
change from v7, excluding the [v8 ledger section](variant/source/COMPILE-VARIANT.md#v8-ruby-407-2026-10-09).
The ledger retains its earlier v2–v7 history. Owned size remains
[6,958 tokens](variant/size.json), excluding structure.sql
([source comparison](evidence/source-control.json), [delta](variant/delta.json)).

## Validation

| Check | v8 result |
| --- | --- |
| Fresh-production gate, unmodified | **Pass**: 17/17 API files, live protocol, 4/4 browser, 13/13 security ([compiled](evidence/gates/compiled-v8-production-gate.log), [Ruby 4.0.7 Rails](evidence/gates/variant-v8-on-rails-production-gate.log)) |
| v7 source on new toolchain | **Pass** ([control](evidence/gates/control-v7-source-on-v8-toolchain-production-gate.log)) |
| Pending export at startup | **Recovered** by the final image; without patch 30 it stays pending ([record](evidence/recovery/final10.json)) |
| Common HTTP probe | **21/21 contract, 3/3 quality** ([record](evidence/compiled-v8-common-http-probe.json)) |
| Edge script, 166 responses | **0 differences from v7; 7 from Rails reference-1** ([summary](evidence/edge/summary.json), [diff](evidence/edge/v8-rails-diff.log)) |
| Focused Roundhouse suites | 68 passed, 11 ignored in 15 suites; 18 return unit tests separately ([summary](evidence/roundhouse-tests/focused-summary.json)) |
| Current Spinel regression probes | #7833 and #7834 pass natively; zero local Spinel patches ([record](evidence/upstream-risks/spinel-probes.json)) |
| Runtime typing | fully typed bodies pass; concrete check fails: 330 sites, ceiling 316; unpatched heads pass both ([concrete](evidence/roundhouse-tests/runtime-concrete-types.log), [upstream](evidence/roundhouse-tests/runtime-types-upstream.log)) |

Each edge run sends 25 setup registrations plus 166 recorded requests: **191 scripted requests**,
with readiness polling additional. Rails reference-1 retains its frozen Ruby 3.3.2. The response
records and diffs show the exact differences; this is a behavior check, with no throughput measurement.

The seven Rails differences are unchanged from v7: whitespace email updates and the later login,
the error payload for a nil password, and numeric password coercion with later login effects.
They remain outside the frozen production checks ([cases](evidence/edge/summary.json),
[full responses](evidence/edge/v8-rails-diff.log)).

The default Roundhouse suite stops at 41 missing generated real-blog fixtures; unpatched heads have
the same 41 failures. This is not a passing full CI run. SQLite SQL visitor tests pass 18/18;
PostgreSQL mode passes 12/18, with six SQLite-shaped assertions left visible
([default attempt](evidence/roundhouse-tests/default-suite-attempt.log),
[PostgreSQL](evidence/roundhouse-tests/arel-postgresql.log)).

## Still to do

- Upstream the remaining compiler/runtime work, including receiver preservation, PostgreSQL
  generation and concrete typing. The typing ceiling is unchanged.
- Support the two remaining app substitutions: boxed-Array `reject!` dispatch and `association`
  admission in analysis. Upstream's lowering alone does not pass the production build.
- Preserve source validation declarations for inclusion, format and numericality. Public probes
  also expose a model class instance variable initializer gap: `@calls has no known type`
  ([fresh example](evidence/upstream-risks/public_model_initializer.rs),
  [execution](evidence/upstream-risks/model-initializer.log)). Library initializer ordering is fixed by #442.
- Configuration remains explicit: `SPINEL_WORKERS=4`; interval columns are strings pending a
  Duration design. Other application limits remain in the ledger.

## Reproduce

You need Docker with BuildKit, git, bash and python3, plus network access. Run from the repository
root. Resources use `conduit-v8b-`, port **4451**, and git-ignored `reproduce/build/` scratch.
`reproduce/with-docker-lock.py` serializes Docker steps; set `AGENTMVC_DOCKER_LOCK` to a lock file shared with any other Docker work on the host.

```bash
R=results/ruby-compile/roundhouse-spinel-conduit-pg-20261009
"$R/reproduce/prepare-toolchain.sh"
L=$R/reproduce/with-docker-lock.py
python3 "$L" "$R/reproduce/build-images.sh" toolchain compiled cruby reference
python3 "$L" "$R/reproduce/run-gate.sh" compiled 4451
python3 "$L" "$R/reproduce/run-gate.sh" rails 4451
python3 "$L" python3 "$R/reproduce/run-common-probe.py" rails conduit-v8b-app:compiled /tmp/v8-probe.json
python3 "$L" python3 "$R/evidence/edge/edge_diff.py" run conduit-v8b-app:compiled 4451 /tmp/v8-edge.json
python3 "$L" python3 "$R/evidence/recovery/probe.py" reproduce conduit-v8b-app:compiled done
```

Full pins are Roundhouse `ea4d3e682c86d817b2617b5862ed9a14d634f7eb` and Spinel
`f85f04b3abef4b0540406948c56db7a51a420122` ([record](run.json)). Fresh AgentMVC clones at
`286af4f` and fresh public upstream clones apply the 10-patch series and reproduce both vendor digests
([prepare](evidence/reproduction/verify-clone-prepare.log)). That context rebuilds the compiled image
and passes the unmodified gate ([build](evidence/reproduction/verify-clone-build.log),
[gate](evidence/reproduction/verify-clone-gate.log), [result](evidence/reproduction/verify-clone-result.json)).
Apt layers are not bit-reproducible across hosts. The resource adapter leaves the frozen host scripts
unchanged, prefixes resources and stops Docker work if a container start exceeds 120 seconds.

The [source manifest](reproduce/gated-source.sha256) pins 75 gated files, excluding the ledger:

```bash
(cd "$R/variant/source" && shasum -a 256 -c ../../reproduce/gated-source.sha256)
```
