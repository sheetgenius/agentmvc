# Roundhouse + Spinel: compiled Conduit, v16

**Patch 20 retires entirely after [Roundhouse #1727](https://github.com/roundhouse-rb/roundhouse/pull/1727).**
On the November 2 v16 pins, Roundhouse `b744c1345` retains five patches and Spinel `ccc1e0f9e` retains zero.
The live protocol passes over the upstream Faye adapter. The production gate, common HTTP checks,
edge comparison and boot recovery pass. JSON headers still match Rails in 41/41 responses across
11 shapes on these pins. Patch 10 remains entirely absent.

This is a separately labelled **compile variant** in the compile program. The app is byte-identical
to v15; measured one-shot source, frozen inputs and earlier records are unchanged.
**No performance benchmark was run; no throughput claim is made.** The
[v15 record](../roundhouse-spinel-conduit-pg-20261102/README.md) supplies the previous condition;
[run.json](run.json) records this condition's pins, patch counts, checks and artifact identities.

## v15 to v16

| Condition | v15, November 2 UTC | v16, November 2 UTC |
| --- | --- | --- |
| Roundhouse | `71e32fe70` + 6 patches | `b744c1345` + 5 patches |
| Spinel | `b57099972` + 0 patches | `ccc1e0f9e` + 0 patches |
| Net Roundhouse diff | +2,046/-89, 42 files | +1,758/-89, 38 files |
| Compiled production gate | API 17/17, live, browser 4/4, security 13/13 | same checks pass |
| Common HTTP | 21/21 contract, 3/3 quality | same checks pass |
| Normalized edge comparison | 0/166 differ from v14 | 0/166 differ from v15 |
| Pending export at boot | done; timestamp present | done; timestamp present |
| Direct JSON headers | 41/41 match Rails across 11 shapes | same comparison passes |

The v16 heads were fixed at 2026-11-02T21:46:22.856578Z and did not move. Full revisions are
Roundhouse main `b744c13458afb2105ee2c8e371c2c688a4e0c620` and Spinel master
`ccc1e0f9e80e8ab59cb49692655ef138ba1c8c2c`. Native execution is aarch64 Linux; toolchain and
oracle Ruby are 4.0.7. All 75 manifested app files and the complete source-tree digest match v15.
See [final pins](evidence/final-pins.json) and [source verification](evidence/source-verification.json).
Patch-size counts include tests and documentation, as in v15. These are different toolchain
conditions, not paired performance measurements.

## Patch 20: upstream replaces the whole adapter

Credit goes to [Roundhouse #1727](https://github.com/roundhouse-rb/roundhouse/pull/1727), merged as
`72fcc769f`, for the bounded Faye adapter over Tep. V16 drops the complete local patch, including
its adapter, scaffold wiring and test. No replacement bridge hunk or app repair is used.

On the v16 retained series, the live check passes authorization, presence, revision broadcasts,
stale-write rejection, reconnect and revocation over the upstream Faye adapter. Browser checks
include room-capacity retry and dirty-draft retention. Upstream's Faye implementation, scaffold
boot require and all four Tep lifecycle production files remain byte-identical to the pin.
The local scaffold-main change belongs to patch 30's boot recovery. See
[live gate scope](evidence/live-gate-scope.json), [source replay checks](evidence/source-verification-extra.json)
and the [production gate receipt](evidence/execution/final-gate-01.json).
The separate #1727 socket-mode suite was not rerun here.

## Direct JSON comparison

For the v16 retained series, all 41 JSON responses across 11 top-level shapes match initialized
Rails 8.1.4 in status, shape and Content-Type. They include callback/rescue paths and login-throttle
rejection. Every compared JSON response sends `application/json; charset=utf-8`.
Complete app bodies were not compared to Rails. See the [header comparison](evidence/header-comparison.json),
[native requests](evidence/headers-compiled-corrected.json) and [Rails requests](evidence/headers-rails.json).

The full app oracle uses Rails 8.1.4 on Ruby 4.0.7, API-only, production, `load_defaults 8.1`.
Its image changes only the frozen app's Rails dependency pin and lock, from Rails 8.1.3.1 to 8.1.4;
the compared Ruby/config source bytes are unchanged. The unchanged minimal API fixture returns
200, `{"ok":true}` and the UTF-8 JSON header; initialized Rails 8.1.4 oracles under defaults 8.0
and 8.1 agree. See [oracle source verification](evidence/oracle-source-verification.json),
[minimal native result](evidence/final-synthetic-json-header.json) and
[initialized Rails results](evidence/rails-synthetic-oracles.json).

The frozen production gate and normalized edge comparison do not compare Content-Type. The direct
header observations supply that check. Header rejection at the throttle does not establish peer isolation.

## Rebase and remaining series

The [applied series](patches/roundhouse/series), [size comparison](evidence/diff-size.json) and
[combined diff](evidence/roundhouse-full-combined.diff) preserve the v16 inputs. Spinel's series is empty.

| Patch | v16 retained diff | Rebase onto the v16 pins |
| --- | --- | --- |
| 30 | +419/-1 | applies directly |
| 50 | +1,008/-22 | documentation append point only |
| 74 | +236/-26 | applies directly |
| 80 | +87/-40 | applies directly |
| 84 | +8/-0 | applies directly |

**Patch 50 needed only a documentation rebase.** #1727 adds “Raw Faye WebSockets” at the point
where patch 50 appends PostgreSQL documentation in `docs/guide/spinel.md`. The resolution keeps
both complete sections. Every retained addition and removal, including the PostgreSQL documentation
text, is identical to v15. All five rebased patches apply cleanly in a second fresh replay.
See [initial applications](evidence/rebase-applications.json), [rebase note](evidence/rebase-notes.txt),
[content comparison](evidence/patch-content-comparison.json) and [fresh replay](evidence/fresh-replay.json).

Patch 50 retains v15's S09 SQL-placeholder append repair; its speed was not remeasured.
Other upstream context includes [#1733](https://github.com/roundhouse-rb/roundhouse/pull/1733)
for native argument forwarding and [#1724](https://github.com/roundhouse-rb/roundhouse/pull/1724)
for gzip/SHA admission and buffered-call refusals. Spinel includes
[#10778](https://github.com/matz/spinel/pull/10778) for streamed HTTP response bodies and
[#10796](https://github.com/matz/spinel/pull/10796) for incremental AES-GCM output, plus the key/IV
reset follow-up. These are upstream changes on the recorded pins, not local patches.
The [upstream context](evidence/upstream-context.json) and [overlap inventory](evidence/upstream-overlap.json)
preserve the revision metadata and changed paths.

## Omission evidence is carried from v15

**No other omissions were rerun on the v16 pins.** The retained patches' need is carried from
v15 and its cited v14/v13 records, rather than re-proven here. Passing the retained series does
not prove every retained hunk necessary or establish global minimality.

On the v15 pins, omitting 80 and 84 together passed check, emission and native compilation, then
an authenticated WebSocket subscription raised a Room/Integer TypeError. That combined omission
was not repeated in v16 and does not establish individual necessity. See the
[v15 omission result](../roundhouse-spinel-conduit-pg-20261102/evidence/omit-80-84-live.json)
and [v15 omission conditions](../roundhouse-spinel-conduit-pg-20261102/README.md#omission-control-80-and-84-still-fail-together).

## Validation, identities and limits

The v16 compiled image, production gate, boot recovery and direct header probe serve the same native
binary, SHA-256 `d69e7129cb2888dea4593f6b6f98f8b47939d1fce4176060088bdb28ba7e55c1`.
The retained build keeps all 167 RBS sidecars, including 35 app sidecars. Exact image/compiler/server
identities are in [artifact identities](evidence/artifact-identities.json) and [run.json](run.json).
The [measurement summary](evidence/measurement.json) binds the accepted gates and probes.

Malformed request JSON remains an observed difference: native returns HTML 400, while the Rails
oracle returns JSON 400. V14 records the same native HTML body. This control is excluded from the
41 JSON comparisons above. It is a limit, not a pass.

V14's two-peer login-throttle isolation probe remains a limit. On the verified v13 control and
both v14 cases, after one peer exhausts its budget, a distinct second peer receives 429 where
the probe expects 401. Those probes exited nonzero. **The two-peer probe was not rerun in v15 or v16.**
See the [v14 observed limit](../roundhouse-spinel-conduit-pg-20261101/evidence/case-b-transport.json).

The full Rails production gate was not rerun; unchanged app source carries v13's Ruby 4.0.7 Rails
gate as a separate condition. V16's Rails 8.1.4 checks are the direct header and minimal-fixture
oracles above. No full Roundhouse suite, general Rails/PostgreSQL/ActiveJob parity, separate Faye
socket-mode suite, alternate server mode or performance is claimed. Production excludes app tests;
patch 50's emitted-test lowering stays outside this gate.

## Reproduce

Use Docker with BuildKit, Git, Bash and Python. Run from the AgentMVC root with a fresh build directory,
port 4505 and `conduit-v16-` resources. Set `AGENTMVC_DOCKER_LOCK` to the canonical shared host lock.
On the compile-program host, also wrap each Docker command with its existing `flock.py --shared`
and workshop suite lock; capacity comes from the central `suite.lock.slots` dial.

```bash
R=results/ruby-compile/roundhouse-spinel-conduit-pg-20261102-v16
L=$R/reproduce/with-docker-lock.py
export AGENTMVC_DOCKER_LOCK="${AGENTMVC_DOCKER_LOCK:-$PWD/.work/lane-docker.lock}"
export BUILD_DIR=/tmp/conduit-v16-reproduce RECOVERY_BUILD_DIR=/tmp/conduit-v16-reproduce
export PROBE_BUILD_DIR=/tmp/conduit-v16-reproduce/probes
python3 "$R/reproduce/prepare-toolchain.py" "$BUILD_DIR"
python3 "$L" "$R/reproduce/fresh-build.sh" "$R/reproduce/build-images.sh" toolchain compiled
python3 "$L" "$R/reproduce/run-gate.sh" compiled 4505
python3 "$L" python3 "$R/reproduce/run-common-probe.py" rails conduit-v16-app:compiled /tmp/v16-common.json
python3 "$L" python3 "$R/evidence/edge/edge_diff.py" run conduit-v16-app:compiled 4505 /tmp/v16-edge.json
python3 "$R/evidence/edge/edge_diff.py" diff "$R/evidence/edge/v15-baseline.json" /tmp/v16-edge.json
python3 "$L" python3 "$R/evidence/recovery/probe.py" reproduce conduit-v16-app:compiled done
python3 "$L" python3 "$R/reproduce/header-probe.py" compiled conduit-v16-app:compiled reproduce
python3 "$L" python3 "$R/reproduce/synthetic-json-header.py" final 'application/json; charset=utf-8'
```

The header probe writes fresh results under `PROBE_BUILD_DIR`. To repeat its Rails oracle, build
`toolchain/Dockerfile.rails-oracle` from `variant/source`, then run the header probe with `rails` and
that image tag. The measured dependency resolution is preserved in
[oracle Gemfile](evidence/rails814-Gemfile) and [lock](evidence/rails814-Gemfile.lock).
The minimal Rails oracle entry point is `reproduce/synthetic-rails-oracle.rb`.

All source and patch manifests must verify before building. Recorded evidence is immutable; write
new results outside it. Official dependency fetches are recorded in [fetch audit](evidence/fetch-audit.json).
Step wall times include shared-lock waits and are not performance measurements. Apt layers and a fresh
Rails dependency resolution are not bit-reproducible across hosts; preserve the measured lock when
comparing the oracle condition.

## Cleanup

The measurement removed all owned containers, networks, image tags and build/source folders.
BuildKit cache mounts remain under the no-prune rule. No volume removal or prune ran. See
[cleanup](evidence/cleanup.json), [final verification](evidence/final-verification.json) and
[publication boundaries](evidence/publication.json).
