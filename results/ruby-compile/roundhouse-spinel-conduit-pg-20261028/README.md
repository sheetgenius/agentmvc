# Roundhouse + Spinel: compiled Conduit, v11

**Compiled Conduit passes the fresh-production gate on the October 28 heads with 10 Roundhouse patches
and 1 Spinel patch (v10: 11 + 2).** Upstream changes retire Roundhouse 85, Spinel 91 and 92, three hunk
groups of patch 10 and the Hash `exists?` hunks of patch 74. One new Spinel patch, 93, answers a Spinel
regression: since `0e7b469de` (#9941), a block given a boxed digit String past the Integer word raises
`RangeError`, so 100-digit IDs answered 500 instead of 404. Patch 50 also extends its keyless-insert guard
to the save override that Roundhouse #1295 added. The 75 gated app files are byte-identical to v10, and
Rails on the same source also passes.

This is a separately labelled **compile variant** with a locally patched toolchain. The measured
one-shot source and earlier records are unchanged. **No performance benchmark was run; no throughput claim
is made.** The [v10 record](../roundhouse-spinel-conduit-pg-20261022/README.md) supplies the previous
condition; [run.json](run.json) holds the pins and artifact identities.

## v10 → v11

| Condition | v10, October 22 | v11, October 28 |
| --- | --- | --- |
| Roundhouse | `0f6fb0c7` + 11 patches | `295abf08` + 10 patches |
| Spinel | `ca9717054` + 2 patches | `3b397d7bc` + 1 patch |
| Net Roundhouse diff | +2,455/−213, 63 files | +2,394/−175, 56 files |
| Net Spinel diff | +11/−3, 2 files | +5/−0, 1 file |
| Production gate | compiled and Rails pass | compiled and Rails pass |
| Common HTTP | 21/21 contract, 3/3 quality | 21/21 contract, 3/3 quality; 19/21 without 93 |
| Edge vs Rails reference-1 | 8/166 responses | 5/166, all among v10's 8 |

The [patch scoreboard](evidence/patch-count-comparison.json), [integrated Roundhouse diff](evidence/roundhouse-final-combined.diff),
[Spinel diff](evidence/spinel-final-combined.diff), [source verification](evidence/source-verification.json)
and [edge summary](evidence/edge/summary.json) support this comparison.

The input series is v10's final series. Heads were observed at 2026-10-28T08:37Z
([pins](evidence/final-pins.json)). Fresh public checkouts replay both series to the built vendor trees
([replay](evidence/fresh-replay-03.log)). "Candidate-01" below is the final Roundhouse series without
Spinel 93; its gate passed, and its common HTTP probe found the regression that 93 repairs.

## Patch scoreboard

| Patch | Decision | Lines | Without it |
| --- | --- | --- | --- |
| [10](patches/roundhouse/10-api-mode-json.patch) | retained; three hunk groups retired | +84/−1 | 8/17 API files: 401, 403, 404 and 422 become 500 |
| [20](patches/roundhouse/20-raw-websocket.patch) | retained; applies cleanly | +347/−16 | `roundhouse check` refuses `EventMachine` and `Faye::WebSocket` |
| [30](patches/roundhouse/30-jobs-boot.patch) | retained; context rebase | +419/−1 | gate passes; boot leaves the export `pending` |
| [50](patches/roundhouse/50-postgresql-lane.patch) | retained; context rebase, 3 adaptations | +1,015/−24 | Roundhouse does not compile |
| [60](patches/roundhouse/60-rails-surface.patch) | retained; context rebase | +190/−32 | emission refuses: no `find_or_create_by!` |
| [74](patches/roundhouse/74-integer-query-range.patch) | retained; Hash `exists?` hunks retired | +236/−26 | 16/17 API files: a non-numeric export ID is 500 |
| [80](patches/roundhouse/80-gradual-return-stabilization.patch) | retained; one line rebased | +87/−40 | live protocol fails |
| [82](patches/roundhouse/82-upstream-regression-quoted-bulk-update.patch) | retained; applies cleanly | +2/−4 | 16/17 API files: `UPDATE ""article_shares""` |
| [83](patches/roundhouse/83-upstream-regression-temporal-initialize.patch) | retained; applies cleanly | +6/−31 | 5/17 API files: Time into String on create |
| [84](patches/roundhouse/84-upstream-regression-mixed-parameter-arm.patch) | retained; applies cleanly | +8/−0 | live protocol fails, as without 80 |
| [Spinel 93](patches/spinel/93-upstream-regression-speculative-slot-to-i.patch) | **new** regression repair | +5/−0 | common HTTP 19/21: 100-digit IDs are 500 |
| [85](../roundhouse-spinel-conduit-pg-20261022/patches/roundhouse/85-upstream-regression-thruster-cache-enumeration.patch) | **retired** (Spinel `e38e53c22`) | v10: +7/−1 | — |
| [Spinel 91](../roundhouse-spinel-conduit-pg-20261022/patches/spinel/91-upstream-regression-late-hash-return.patch) | **retired** (matz/spinel#10012) | v10: +11/−0 | — |
| [Spinel 92](../roundhouse-spinel-conduit-pg-20261022/patches/spinel/92-upstream-regression-digest-instance-new.patch) | **retired** (matz/spinel#10041) | v10: +0/−3 | — |

"Applies cleanly" patches keep identical +/− lines; only hunk metadata changed. The
[scoreboard](evidence/patch-count-comparison.json), [retirement checks](evidence/retirement-checks.json) and
[omission results](evidence/omission-results.json) give each decision's evidence. Both series have SHA256SUMS,
and the [production Dockerfile](toolchain/Dockerfile.production) checks both manifest digests.

**Every retained patch still fails without it.** Each one-patch omission is the final series minus that
patch, Spinel 93 included, built on the same heads. All ten builds compiled Roundhouse from their own sources;
the nine that produced a toolchain carry nine distinct Roundhouse binaries, none equal to the final one
([identities](evidence/omission-results.json)). Without 50, the build stops at 74's call to 50's
`postgresql_enabled` ([build](evidence/execution/build-without-50-build-02.log)); 50 is also the libpq backend
the gate's PostgreSQL needs. Without 60, `roundhouse check` passes but emission refuses two controllers
([build](evidence/execution/build-without-60-build-02.log)). Without 30, the frozen gate, common HTTP and edge
comparison pass, but the boot-recovery probe leaves the seeded export `pending`
([recovery](evidence/omissions/without-30/recovery.json)). Without 80 or 84, the API suite passes, but the live
socket endpoint raises `TypeError: no implicit conversion of LiveRooms::Room into Integer`
([app log](evidence/execution/without-80-gate-02-app.log)). The other failures are in the captured app logs:
[10](evidence/execution/without-10-gate-02-app.log), [74](evidence/execution/without-74-gate-02-app.log),
[82](evidence/execution/without-82-gate-02-app.log) and [83](evidence/execution/without-83-gate-02-app.log).
Without 93, which is candidate-01 exactly, the gate passes and common HTTP is 19/21.

**Retirements.** Each retired patch or hunk is absent from the final series, and the final build and full
gate pass without it. Every retiring commit is an ancestor of the v11 pin and not of the v10 pin.

- **Spinel 91**, the late-Hash return: [matz/spinel#10012](https://github.com/matz/spinel/pull/10012). The
  three-line late-Hash program also matches CRuby on the final toolchain ([conformance](evidence/conformance/results.json)).
- **Spinel 92**, `OpenSSL::Digest#new`: [matz/spinel#10041](https://github.com/matz/spinel/pull/10041).
  None of 92 remains: `def new = clone.reset` is still in `packages/openssl/openssl/digest.rb`, and the
  app now compiles with it.
- **Roundhouse 85**, the Thruster cache loop: Spinel
  [`e38e53c22`](https://github.com/matz/spinel/commit/e38e53c220f37c77d2636e3ad77c1dbaa9be5325) makes the
  handle the only String representation. `thruster_cache.rb:244` is unchanged and now compiles.
- **Patch 10**'s response and rescue hunks: [rubys/roundhouse#1198](https://github.com/rubys/roundhouse/pull/1198)
  (`set_header`, computed statuses) and [#1201](https://github.com/rubys/roundhouse/pull/1201) (ParseError,
  `rescue_from` order). Its computed `errors.add` message hunk is retired by `07a85824d`, merged in
  [#1352](https://github.com/rubys/roundhouse/pull/1352).
- **Patch 74**'s Hash `exists?` hunks: [rubys/roundhouse#1218](https://github.com/rubys/roundhouse/pull/1218).

**Rebase adaptations, not regressions.** 30 and 60 conflicted on context only. 74 passes the new
`runtime_relation` argument, and 80 uses `HashMap::default()` for the fixed-hasher map (#1412). 50 gains three
adaptations: it maps its own `TextArray` column type in a new exhaustive match; it adds `Db._unscoped_tables`,
mirroring upstream `db_pg`, which #1218's runtime calls; and it extends its keyless guard to #1295's save
override (below).

**Excluded evidence.** The candidate-01 one-patch omissions read stale state from the shared Cargo target
cache, so they are superseded ([record](evidence/regressions/invalid-omission-cache.json)). 74, 80, 82, 83 and
84 never compiled Roundhouse and reused without-60's binary; 20 and 50 compiled with a stale build-script file
list. Builds now refresh source mtimes inside the Docker lock ([`fresh-build.sh`](reproduce/fresh-build.sh)),
each build log must show "Compiling roundhouse", and each toolchain's binary hash is recorded.

## New upstream regressions

**Huge IDs, Spinel 93.** Candidate-01's common HTTP probe fell to 19/21: a 100-digit export or comment ID
answered 500 with `RangeError: integer overflow parsing`, where Rails answers 404
([probe](evidence/compiled-v11-common-http-probe.json)). The reduction is two lines:

```ruby
pr = proc { |a| puts a }
pr.call(["9" * 100, 1][0])
```

CRuby 4.0.7 and v10's Spinel print the digits; v11's Spinel raises
([reductions](evidence/regressions/huge-id/reduce-final/v11.json)), as did master `b41d475f5`. A full-DAG
bisect on native builds names `0e7b469de`, "A boxed String's to_i parses as a typed one's does" (fixes
[#9941](https://github.com/matz/spinel/issues/9941)); its parent `b9baf92b3` is good, and both were rebuilt
from clean ([bisect](evidence/regressions/huge-id/bisect.json)). The call site fills each boxed argument's
`sp_int` slot with `sp_poly_slot_arg`, which now parses a String with the raising `to_i`. In Conduit that call
is the `hash.each` in `Relation#hash_conditions`, reached from `find_by(id: param(:id))`
([classification](evidence/regressions/huge-id/classification.json)). The slot is speculative, and the
runtime's own comment says such a fill must not raise; #9298 fixed the same for a Float. Patch 93 restores the
pre-#9941 `strtoll` read for the speculative slot only; `to_i` itself is untouched, and Spinel's #9941 test
still passes. With 93, 1,835 of 1,844 Spinel test programs in a proc and block subset pass; the other 9 fail
identically without it ([subset](evidence/regressions/huge-id/spinel-subset-with-93.json)).
Roundhouse is not involved: the final and candidate-01 toolchains carry the same Roundhouse binary
([identity](evidence/execution/roundhouse-binary-final-01.log)).

After these pins, the regression was reported as [matz/spinel#10462](https://github.com/matz/spinel/issues/10462)
and fixed on master by [`3ca03ede9`](https://github.com/matz/spinel/commit/3ca03ede9188da07cffd4c012607d106e4efd9e7),
which reads the String in that slot as patch 93 does. A native build of `3ca03ede9` prints the digits
(checked at publication), so 93 should retire at the next pin.

**Keyless save, Roundhouse #1295.** An earlier v11 gate passed only 13 of 17 API files: favorite and follow
inserts raised `NotImplementedError: id=: subclasses must override`
([gate](evidence/execution/compiled-gate-02.log), [app log](evidence/execution/compiled-gate-02-app.log)).
[#1295](https://github.com/rubys/roundhouse/pull/1295) adds a Ruby-family `save_after_validation` override in
`connection.rb` that assigns `self.id = _adapter_insert` unconditionally, which bypasses patch 50's keyless
guard in `base.rb`. A first-parent bisect on the actual method bodies, with v10's guard held constant, names
merge `f6aa93ef3` (branch commit `e7d195bca`); its parent `7f20914d5` passes
([bisect](evidence/regressions/keyless-save/bisect.json), [repro](evidence/regressions/keyless-save/reduced.rb)).
Patch 50 now guards the override too. This is a local adaptation, not an upstream regression: upstream never
guarded keyless inserts, and at `7f20914d5` a keyless save already raised from `base.rb` (checked at
publication). Open [#1263](https://github.com/rubys/roundhouse/pull/1263), which adds that guard, covers only
`base.rb`; it predates #1295 and now conflicts, so a rebase must also guard the override.

## Validation

| Check | v11 result |
| --- | --- |
| Compiled fresh-production gate | 17/17 API files, live protocol, 4/4 browser, 13/13 security |
| Same app on Ruby 4.0.7 Rails | same checks pass; source identical to the final condition |
| Common HTTP probe | 21/21 contract, 3/3 quality; 19/21 without 93 |
| Edge comparison | 5/166 vs Rails reference-1, all among v10's 8; 3/166 vs v10; 0/166 vs candidate-01 |
| Pending export at boot | pending → done, completed timestamp present |
| Fresh patch replay | both vendor digests match; both manifests verify |
| Ruby conformance controls | late Hash and String alias match CRuby; the frozen-literal gap remains |

Evidence: [compiled gate](evidence/execution/compiled-gate-04.log), [Rails gate](evidence/execution/rails-gate-01.log),
[common probe](evidence/compiled-v11-common-http-probe-final.json), [edge summary](evidence/edge/summary.json),
[recovery](evidence/recovery/final.json), [conformance](evidence/conformance/results.json).
The gate's app binary (`server_sha256` `1c0ad401…`) runs from the recorded compiled image
([identity](evidence/execution/compiled-gate-04-app-binary.json)). The three edge responses that changed since
v10 now match Rails: whitespace-only email updates are refused as blank, so later logins with the old email
still work. That is likely #1164 ("blank means Rails' blank?"), not bisected. A fresh Rails reference-1 run
matches v10's recorded Rails run on all 166 responses, so the edge harness did not drift. Earlier gates:
[compiled-gate-02](evidence/execution/compiled-gate-02.log) predates the keyless guard, and
[compiled-gate-03](evidence/execution/compiled-gate-03.log) is candidate-01 (no 93; passes).

## Timings against v10

| Measure | v10 | v11 |
| --- | --- | --- |
| Toolchain + compiled build | 598 s (Spinel 89.7 s) | 234 s (Spinel 59.3 s) |
| Cargo build / app spin build | 164.6 s / 285.0 s | 103.7 s / 55.5 s |
| Compiled gate (app build in it) | 313 s (202.1 s) | 265 s (61.0 s) |
| Rails gate | 45.1 s | 21.8 s |
| Analysis / emission peak RSS | 41,124 / 51,068 KiB | 45,492 / 55,656 KiB |

Peak RSS comes from each final compiled gate's build and rose 11% and 9%. Wall times fell, but this shared host
varies 2x within an hour, so neither direction is a measured compiler change ([timings](evidence/timing-vs-v10.json)).
One outlier: the hardening check `s09_oversized_body` (a 2 MB article with 2,000 tags) passes but took 182 s in
the final gate and 121 s in candidate-01's, against 65 s in v10's final gate and 0.2 s on Rails. It was not
investigated. The compiled image is 121.3 MB, as in v10.

## Reproduce

Use Docker with BuildKit, git, bash and python3. Run from the AgentMVC repository root.
Use a lock shared with every other Docker job on the host, `conduit-v11-` resources and port **4481**.
The [adapter](reproduce/bin/docker) leaves frozen host scripts unchanged and stops work if a container start
exceeds 120 seconds. [`fresh-build.sh`](reproduce/fresh-build.sh) refreshes the Roundhouse source mtimes inside
the lock, so a shared Cargo cache cannot serve a stale binary. The [publication inventory](evidence/publication.json)
describes the retained evidence and omitted scratch artifacts; no binary or generated build tree is required
in Git.

```bash
R=results/ruby-compile/roundhouse-spinel-conduit-pg-20261028
L=$R/reproduce/with-docker-lock.py
export AGENTMVC_DOCKER_LOCK=.work/lane-docker.lock BUILD_DIR=/tmp/v11-build RECOVERY_BUILD_DIR=/tmp/v11-build
python3 "$R/reproduce/prepare-toolchain.py" "$BUILD_DIR"
python3 "$L" "$R/reproduce/fresh-build.sh" "$R/reproduce/build-images.sh" toolchain compiled cruby reference
python3 "$L" "$R/reproduce/run-gate.sh" compiled 4481
python3 "$L" "$R/reproduce/run-gate.sh" rails 4481
python3 "$L" python3 "$R/reproduce/run-common-probe.py" rails conduit-v11-app:compiled /tmp/v11-common.json
python3 "$L" python3 "$R/evidence/edge/edge_diff.py" run conduit-v11-app:compiled 4481 /tmp/v11-edge.json
python3 "$L" python3 "$R/evidence/recovery/probe.py" reproduce conduit-v11-app:compiled done
```

Roundhouse is pinned to `295abf08bd5004922669f73bf090def8e3852fe6`; Spinel to
`3b397d7bc96c2324190c0f2f857e1973e24dca84`. The toolchain step fetches both from their public repositories,
replays both patch series and verifies each manifest and vendor-tree digest. Apt layers are not
bit-reproducible across hosts. Final patch, image, source and binary identities are in [run.json](run.json).

The [source manifest](reproduce/gated-source.sha256) pins the 75 gated files, excluding the ledger:

```bash
(cd "$R/variant/source" && shasum -a 256 -c ../../reproduce/gated-source.sha256)
```
