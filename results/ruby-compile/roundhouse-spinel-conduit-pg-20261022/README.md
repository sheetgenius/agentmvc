# Roundhouse + Spinel: compiled Conduit, v10

**Compiled Conduit passes the fresh-production gate on the October 22 heads with 11 Roundhouse patches
and 2 Spinel patches.** No patch from the reduced v9.1 series retires: each one is still needed or
still uncovered upstream. Two new upstream changes need new local patches: Roundhouse's Thruster cache
(85) and Spinel PR #9913's `OpenSSL::Digest#new` (92). The 75 gated app files are byte-identical to v9,
and Rails on the same source also passes.

This is a separately labelled **compile variant** with a locally patched toolchain. The measured
one-shot source and earlier records are unchanged. **No performance benchmark was run; no throughput claim
is made.** The [v9 record](../roundhouse-spinel-conduit-pg-20261021/README.md) supplies the previous
condition; [run.json](run.json) holds the pins and artifact identities.

## v9 → v10

| Condition | v9, October 21 | v10, October 22 |
| --- | --- | --- |
| Roundhouse | `1c84d346` + 11 patches | `0f6fb0c7` + 11 patches |
| Spinel | `6ca6d451b` + 1 patch | `ca9717054` + 2 patches |
| Net Roundhouse diff | +2,481/−221, 66 files | +2,455/−213, 63 files |
| Net Spinel diff | +11/−0, 1 file | +11/−3, 2 files |
| Production gate | compiled and Rails pass | compiled and Rails pass |
| Common HTTP | 21/21 contract, 3/3 quality | 21/21 contract, 3/3 quality |
| Edge vs Rails reference-1 | 8/166 responses | same 8/166; 0/166 vs v9 |

The [patch scoreboard](evidence/patch-count-comparison.json), [integrated Roundhouse diff](evidence/roundhouse-final-combined.diff),
[Spinel diff](evidence/spinel-final-combined.diff), [source verification](evidence/source-final-verification.json)
and [edge summary](evidence/edge/summary.json) support this comparison.

The input series, v9.1, is v9's with patch 00 retired upstream by #1145 and patches 10 and 60 trimmed:
10 Roundhouse patches plus Spinel 91, +2,436/−212 lines. Heads were observed at 2026-10-22T08:51Z
([pins](evidence/final-pins.json)). Fresh public checkouts replay both series to the built vendor trees
([replay](evidence/rebase/fresh-replay-final.log)).

## Patch scoreboard

| Patch | Decision | Lines |
| --- | --- | --- |
| [10](patches/roundhouse/10-api-mode-json.patch) | retained; applies cleanly | +152/−39 |
| [20](patches/roundhouse/20-raw-websocket.patch) | retained; applies cleanly | +347/−16 |
| [30](patches/roundhouse/30-jobs-boot.patch) | retained; context rebase, Prism 2 import | +419/−1 |
| [50](patches/roundhouse/50-postgresql-lane.patch) | retained; context rebase, callback shim | +999/−22 |
| [60](patches/roundhouse/60-rails-surface.patch) | retained; context rebase | +190/−32 |
| [74](patches/roundhouse/74-integer-query-range.patch) | retained; applies cleanly | +238/−27 |
| [80](patches/roundhouse/80-gradual-return-stabilization.patch) | retained; byte-identical | +87/−40 |
| [82](patches/roundhouse/82-upstream-regression-quoted-bulk-update.patch) | retained; applies cleanly | +2/−4 |
| [83](patches/roundhouse/83-upstream-regression-temporal-initialize.patch) | retained; applies cleanly | +6/−31 |
| [84](patches/roundhouse/84-upstream-regression-mixed-parameter-arm.patch) | retained; applies cleanly | +8/−0 |
| [85](patches/roundhouse/85-upstream-regression-thruster-cache-enumeration.patch) | **new** regression repair | +7/−1 |
| [Spinel 91](patches/spinel/91-upstream-regression-late-hash-return.patch) | retained; byte-identical | +11/−0 |
| [Spinel 92](patches/spinel/92-upstream-regression-digest-instance-new.patch) | **new** regression repair | +0/−3 |

"Applies cleanly" patches keep identical +/− lines; only hunk metadata changed. The
[scoreboard](evidence/patch-count-comparison.json) and [retirement checks](evidence/retirement-checks.json)
give each decision's evidence. Both series have SHA256SUMS, and the
[production Dockerfile](toolchain/Dockerfile.production) checks both manifest digests.

**Nothing retires.** The three conflicts are context only ([rejected hunks](evidence/rebase/)).
30 meets `0b80f927c`'s Sidekiq lines beside `ActiveJob.register_drain`
([diff](evidence/upstream/0b80f927c.diff)); upstream still runs no `after_initialize` at boot, and #902 is
unmerged. 50's rejected hunk is a `#[cfg(test)]` module at the end of `naming.rs`; no libpq lane landed
(#867, #877). 60 still adds `find_or_create_by!`; `5f0428141` added only `find_or_initialize_by`
([diff](evidence/upstream/5f0428141.diff)).
Each conflicting patch was also omitted and rebuilt ([results](evidence/omission-results.json)). Without 50,
Roundhouse does not compile: 74 uses 50's `postgresql_enabled` and `db_libpq.rb`
([build](evidence/execution/build-without-50-build-01.log)). Without 60, `roundhouse check` passes but emission
refuses two controllers: "the runtime has no `find_or_create_by!`"
([build](evidence/execution/build-without-60-build-01.log)). Without 30, the frozen gate passes, since it never
boots over a pending export ([gate](evidence/execution/without-30-gate-01.log)), but the boot-recovery probe
leaves the export `pending` ([recovery](evidence/omissions/without-30/recovery.json)).
#1162 merged, but it changes `validates … message:`, not the `errors.add` path in patch 10.
#1011 is still unmerged, so 80 stays. 82, 83 and 84 apply with their target lines unchanged.
Without 91, the three-line late-Hash program still fails C compilation at the pin
([log](evidence/execution/without91-hash-conformance-02.log)). An earlier "91 retires" probe reused a
cached compiler and is excluded ([record](evidence/regressions/invalid-without91-cache.json)).

**Rebase adaptations, not regressions.** 30's boot-hooks module imports `PrismLocation` after the Prism 2
migration (`a8868e1b1`, [upstream](evidence/upstream/a8868e1b1.diff), [build](evidence/execution/build-initial-01.log)).
50's libpq backend gains `Db._txn_callbacks`, mirroring upstream `db_pg` after `0fe90bdf8`
(`current_transaction.after_commit`, [upstream](evidence/upstream/0fe90bdf8.diff)). Without it, four Spinel
refusals name the missing method ([build](evidence/execution/build-rebase-03.log),
[classification](evidence/regressions/rebase-classification.json)).

## New upstream regressions

**Thruster cache, Roundhouse 85.** `b348b8005` adds `runtime/spinel/tep/thruster_cache.rb`
([upstream](evidence/upstream/b348b8005.diff)). In Conduit's program, line 244
`if_none_match.split(",").any? { |candidate| candidate.strip == etag }` is refused:

```text
argument __self of __enum_any?__24 (actual str_array, parameter strh_array) given a Array,
which no conversion keeps in its sp_PtrArray * slot
```

The analyzer infers `not_modified?` as `(untyped, untyped) -> bool`
([signatures](evidence/regressions/thruster-cache/application-inferred.rbs)) and settles the `any?` helper's
receiver as an Array of String handles, while `split` hands it a plain String Array. v9's Spinel refuses the
same emitted app ([log](evidence/execution/cache-application-v9-spinel-01.log)), so this is new Roundhouse
code meeting an older Spinel conversion gap, not a Spinel regression. Patch 85 uses an index loop with the
same CRuby result; with it the same app compiles on v9's Spinel
([log](evidence/execution/cache-loop-v9-spinel-01.log)). None of 29 standalone reductions reproduces the
refusal; it needs the application context
([classification](evidence/regressions/thruster-cache/classification.json)).

**`OpenSSL::Digest#new`, Spinel 92.** After the Thruster repair, C compilation fails
([log](evidence/execution/string-c-capture-01.log)):

```text
app/app/controllers/application_controller.rb:70: error: incompatible pointer types
initializing 'const char *' with an expression of type 'sp_String *'
```

Line 70 is the original source's `params[name]` inside `param(name)`, emitted as `@params[name.to_s]`.
`@params` is boxed, so the `[]` dispatch offers a Struct class arm (`LiveRooms::Room`, where `Room[x]` is
`Room.new(x)`), class-value `new` arms, and instance `new` arms for `OpenSSL::Digest` and its three
subclasses. In that combined dispatch the argument is held as a shared String handle, then boxed as a C
string. A first-parent bisect with 91 on every candidate names `2c6d6b7ff`, the merge of
[matz/spinel#9913](https://github.com/matz/spinel/pull/9913); its parent `449d8addb` compiles
([bisect](evidence/regressions/string-argument/bisect-r2.json)). Within the PR, `2388b53ab` adds
`def new = clone.reset`. Removing only that definition makes the same emitted app compile on the same
compiler ([log](evidence/execution/digest-trial-v1-app.log)); patch 92 does exactly that. CRuby has
`OpenSSL::Digest#new` and Conduit never calls it, so 92 trades an unused method for compilation; the emitter
defect remains upstream. No standalone program reproduces it yet
([comparison](evidence/regressions/digest-instance-new/comparison.json)).

The earlier "String argument at token decoding" hypothesis read line 70 of the emitted file rather than the
original source; its probes all match CRuby ([note](evidence/regressions/string-argument/classification.json)).

**Older gaps found while reducing (v9 and v10 alike, no patch).** With `Room[1, 2]`, a String-appending
class and Digest in one program, `klass.new(name.to_s)` on `Room` prints `lock=0` instead of CRuby's
`lock="a"`, and `Holder.new(Room).param(:b)` prints `nil` instead of the struct. A seven-line
`Room[1, 2]` + `@params[name.to_s]` program is refused: `undefined method '[]' for a Class`
([cases](evidence/regressions/existing-struct-gaps.json)).

## Validation

| Check | v10 result |
| --- | --- |
| Compiled fresh-production gate | 17/17 API files, live protocol, 4/4 browser, 13/13 security |
| Same app on Ruby 4.0.7 Rails | same checks pass; source identical to the final condition |
| Common HTTP probe | 21/21 contract, 3/3 quality |
| Edge comparison | 8/166 vs Rails reference-1, the same 8 as v9; 0/166 vs v9 |
| Pending export at boot | pending → done, completed timestamp present |
| Fresh patch replay | both vendor digests match; both manifests verify |
| Ruby conformance controls | late Hash matches CRuby; String alias and literal gaps as in v9 |

Evidence: [compiled gate](evidence/execution/compiled-gate-02.log), [Rails gate](evidence/execution/rails-gate-01.log),
[common probe](evidence/compiled-v10-common-http-probe.json), [edge summary](evidence/edge/summary.json),
[recovery](evidence/recovery/final.json), [conformance](evidence/conformance/results.json).
The gate's app binary (`server_sha256` `4a4b292b…`) runs from the recorded compiled image
([identity](evidence/execution/compiled-gate-02-app-binary.json)). A fresh Rails reference-1 run matches v9's
recorded Rails run on all 166 responses, so the edge harness did not drift. The earlier failing gate,
[compiled-gate-01](evidence/execution/compiled-gate-01.log), predates 85, the callback shim and 92.
Cancelled steps keep their exit codes in `evidence/execution/`. Bulky bisect build logs and probe logs that
repeat their results files are omitted; their records keep each log's size and SHA-256
([inventory](evidence/publication.json)).

## Timings against v9

| Measure | v9 | v10 |
| --- | --- | --- |
| Toolchain + compiled build | 254 s (Spinel cached) | 598 s (Spinel 89.7 s) |
| Cargo build / app spin build | 101.9 s / 141.0 s | 164.6 s / 285.0 s |
| Compiled gate (app build in it) | 244 s (146.4 s) | 313 s (202.1 s) |
| Rails gate | 28.4 s | 45.1 s |
| Analysis / emission peak RSS | 40,328 / 52,740 KiB | 41,124 / 51,068 KiB |

Memory is flat (+2%, −3%). Wall times rose, but the same emitted app's `spin build` took 123 s to 285 s
within one hour on this shared host across neighbouring compilers, so the rise is host load, not a
measured compiler slowdown ([timings](evidence/timing-vs-v9.json)). The compiled image is 121.3 MB (v9 121.1 MB).

## Reproduce

Use Docker with BuildKit, git, bash and python3. Run from the AgentMVC repository root.
Use a lock shared with every other Docker job on the host, `conduit-v10-` resources and port **4471**.
The [adapter](reproduce/bin/docker) leaves frozen host scripts unchanged and stops work if a container start
exceeds 120 seconds. The [publication inventory](evidence/publication.json) describes the retained
evidence and omitted scratch artifacts; no binary or generated build tree is required in Git.

```bash
R=results/ruby-compile/roundhouse-spinel-conduit-pg-20261022
L=$R/reproduce/with-docker-lock.py
export AGENTMVC_DOCKER_LOCK=.work/lane-docker.lock BUILD_DIR=/tmp/v10-build RECOVERY_BUILD_DIR=/tmp/v10-build
python3 "$R/reproduce/prepare-toolchain.py" "$BUILD_DIR"
python3 "$L" "$R/reproduce/build-images.sh" toolchain compiled cruby reference
python3 "$L" "$R/reproduce/run-gate.sh" compiled 4471
python3 "$L" "$R/reproduce/run-gate.sh" rails 4471
python3 "$L" python3 "$R/reproduce/run-common-probe.py" rails conduit-v10-app:compiled /tmp/v10-common.json
python3 "$L" python3 "$R/evidence/edge/edge_diff.py" run conduit-v10-app:compiled 4471 /tmp/v10-edge.json
python3 "$L" python3 "$R/evidence/recovery/probe.py" reproduce conduit-v10-app:compiled done
```

Roundhouse is pinned to `0f6fb0c7e7efa9b955c40bdd537b8a61fbe0486e`; Spinel to
`ca971705427a40e5ef5472bf76f033abbc21da3a`. The toolchain step fetches both from their public repositories,
replays both patch series and verifies each manifest and vendor-tree digest. Apt layers are not
bit-reproducible across hosts. Final patch, image, source and binary identities are in [run.json](run.json).

The [source manifest](reproduce/gated-source.sha256) pins the 75 gated files, excluding the ledger:

```bash
(cd "$R/variant/source" && shasum -a 256 -c ../../reproduce/gated-source.sha256)
```
