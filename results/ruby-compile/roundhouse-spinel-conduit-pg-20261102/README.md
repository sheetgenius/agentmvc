# Roundhouse + Spinel: compiled Conduit, v15

**Patch 10 retires entirely after [Roundhouse #1713](https://github.com/roundhouse-rb/roundhouse/pull/1713).**
On the November 2 pins, Roundhouse `71e32fe70` retains six patches and Spinel `b57099972` retains zero.
The production gate, common HTTP checks, edge comparison and boot recovery pass. Direct JSON headers
match Rails in all 41 comparisons across 11 shapes. The frozen gate alone cannot see the charset.

This is a separately labelled **compile variant** in the compile program. The app is byte-identical
to v14; measured one-shot source, frozen inputs and earlier records are unchanged.
**No performance benchmark was run; no throughput claim is made.** The
[v14 record](../roundhouse-spinel-conduit-pg-20261101/README.md) supplies the previous condition;
[run.json](run.json) records this condition's pins, patch counts, checks and artifact identities.

## v14 to v15

| Condition | v14 Case B, November 1 UTC | v15, November 2 UTC |
| --- | --- | --- |
| Roundhouse | `7766b5cee` + 7 patches | `71e32fe70` + 6 patches |
| Spinel | `0ed86eae9` + 0 patches | `b57099972` + 0 patches |
| Net Roundhouse diff | +2,108/-106, 46 files | +2,046/-89, 42 files |
| Compiled production gate | API 17/17, live, browser 4/4, security 13/13 | same checks pass |
| Common HTTP | 21/21 contract, 3/3 quality | same checks pass |
| Normalized edge comparison | 0/166 differ from v13 | 0/166 differ from v14 |
| Pending export at boot | done; timestamp present | done; timestamp present |
| Direct JSON Content-Type | residual 10 hunk required | upstream matches Rails |

The v15 heads were fixed at 2026-11-02T20:30:55Z and did not move. Full revisions are Roundhouse main
`71e32fe7096717c95347e966b332ab130f474f75` and Spinel master
`b570999724ea9249fb91654bcef704fc9e20fdbc`. Native execution is aarch64 Linux; toolchain and oracle
Ruby are 4.0.7. All 75 manifested app files and the complete source-tree digest match v14. See
[final pins](evidence/final-pins.json) and [source verification](evidence/source-verification.json).
Patch-size counts include tests and documentation, as in v14; these are different toolchain conditions,
not paired performance measurements.

## Patch 10: upstream replaces the last hunk

Credit goes to [Roundhouse #1713](https://github.com/roundhouse-rb/roundhouse/pull/1713), merged as
`71e32fe70`, for preserving the response charset when rendering a content type. V14 retained one
original +3/-1 bridge hunk because `GET /api/tags` otherwise sent `application/json` instead of
`application/json; charset=utf-8`. V15 drops all of patch 10, with no substitute hunk or app repair.

For the v15 retained series, all 41 JSON responses across 11 top-level shapes match initialized Rails
8.1.4 in status, shape and Content-Type. They cover users, profiles, articles, comments, shares, exports,
tags, health and errors, including callback/rescue paths and login-throttle rejection. Every compared
JSON response sends `application/json; charset=utf-8`. Complete app bodies were not compared to Rails.
See the [header comparison](evidence/header-comparison.json),
[native requests](evidence/headers-compiled-corrected.json) and [Rails requests](evidence/headers-rails.json).

The full app oracle uses Rails 8.1.4 on Ruby 4.0.7, API-only, production, `load_defaults 8.1`.
Its image changes only the frozen app's Rails dependency pin and lock, from Rails 8.1.3.1 to 8.1.4;
the compared Ruby/config source bytes are unchanged. The unchanged v14 minimal API fixture also returns
200, `{"ok":true}` and the UTF-8 JSON header; initialized Rails 8.1.4 oracles under defaults 8.0 and 8.1
agree. See [oracle source verification](evidence/oracle-source-verification.json),
[minimal native fixture result](evidence/final-synthetic-json-header.json) and
[initialized Rails results](evidence/rails-synthetic-oracles.json).

The frozen production gate and normalized edge comparison do not compare Content-Type. These direct
header observations supply the check that distinguished v14's successful gate from its charset regression.

## Rebase and remaining series

The [applied series](patches/roundhouse/series), [size comparison](evidence/diff-size.json) and
[combined diff](evidence/roundhouse-full-combined.diff) preserve the v15 inputs. Spinel's series is empty.

| Patch | v15 retained diff | v15 result with series retained |
| --- | --- | --- |
| 20 | +288/-0 | Faye adapter retained; live passes |
| 30 | +419/-1 | boot recovery passes |
| 50 | +1,008/-22 | corrected S09 version; PostgreSQL gate passes |
| 74 | +236/-26 | API passes |
| 80 | +87/-40 | combined 80/84 omission fails live |
| 84 | +8/-0 | same combined omission |

[Roundhouse #1688](https://github.com/roundhouse-rb/roundhouse/pull/1688) supersedes patch 20's local
Tep lifecycle edits. The rebase keeps all four upstream Tep production files unchanged: `net.rb`,
`server_threaded.rb`, `websocket/connection.rb` and `websocket/driver.rb`. It retains the Faye adapter
and scaffold boot/dispatch wiring. The lifecycle test now acknowledges the peer close before joining
and explicitly models deadline expiry. Its old assertion fails first; the adapted test passes on CRuby
4.0.7. This test change does not alter upstream lifecycle production behavior. Exact conflicting hunks
and results are in [initial rebase attempts](evidence/rebase-initial-attempts.json),
[test before](evidence/patch20-test-before.json) and [test after](evidence/patch20-test-after.json).

Patches other than 20 apply directly and preserve their supplied added/removed code. Patch 50 includes
the previously measured S09 SQL-placeholder append repair; its performance was not remeasured in v15.
See [patch content comparisons](evidence/patch-content-comparison.json) and
[fresh replay](evidence/fresh-replay.json).

[Roundhouse #1723](https://github.com/roundhouse-rb/roundhouse/pull/1723), merged as `ce9177157`,
rewrote route ingestion and helpers. It caused no patch-application conflict; the retained v15 series
passes the production gate and matches v14's normalized edge responses. The patch 20 rebase follows
the upstream lifecycle work, rather than a route repair. Other overlapping context includes #1695's
content-type writer, #1661's JSON defaults, #1607's finder/model changes and #1729's class-body replay.
The [overlap inventory](evidence/upstream-overlap.json) preserves the changed paths and commits.

## Omission control: 80 and 84 still fail together

On the same v15 compiler pins and production-filtered source, dropping 80 and 84 together leaves
20/30/50/74. Check, emission and native compilation pass. One authenticated WebSocket subscription
then raises `TypeError: no implicit conversion of LiveRooms::Room into Integer` and closes.
No full API/browser/security gate ran for this omission. This proves the combined omission fails;
it does not re-prove each patch's individual necessity.

The omission's generated RBS narrows `LiveRooms.join` to `Symbol?` and the broadcast room parameter to
`Symbol`; the retained series keeps the relevant returns and parameters untyped. See the
[live result](evidence/omit-80-84-live.json), [generated signatures](evidence/omit-80-84-live-rooms.rbs)
and [check/emission summary](evidence/omit-80-84-summary.json).

**The other omissions were not rerun.** Their need is carried from v14, which carried it from v13.
There is no separate omit-20 gate or renewed necessity claim for every retained line.
At the measurement's final refresh, [#1011](https://github.com/roundhouse-rb/roundhouse/pull/1011)
and [#1727](https://github.com/roundhouse-rb/roundhouse/pull/1727) were open; these are historical
statuses in the [recorded snapshot](evidence/pending-prs-final.json). Neither PR was built in v15.

## Validation, identities and limits

The v15 compiled image, production gate, boot recovery and direct header probe serve the same native
binary, SHA-256 `d41fa6df14e7476b54d022b557490e41f5efd4a3bf84a58ba04de9a8937e1cdd`.
The retained build keeps all 167 RBS sidecars, including 35 app sidecars. The combined omission uses
a distinct compiler and native executable. Exact image/compiler/server identities are in
[artifact identities](evidence/artifact-identities.json) and [run.json](run.json).
The [measurement summary](evidence/measurement.json) binds the accepted gates and probes.

Malformed request JSON remains an observed difference: native returns HTML 400, while the Rails oracle
returns JSON 400. V14 records the same native HTML body. Patch 10's JSON-only normalization cannot change
this path, so it is excluded from the 41 JSON comparisons above. This is a limit, not a pass.

V14's two-peer login-throttle isolation probe also remains a limit. On the verified v13 control and both
v14 cases, after one peer exhausts its budget, a distinct second peer receives 429 where the probe expects
401. All those transport probes exited nonzero. **The two-peer probe was not rerun in v15.** The header
probe's throttle rejection does not establish peer isolation. See the
[v14 observed limit](../roundhouse-spinel-conduit-pg-20261101/evidence/case-b-transport.json).

The full Rails production gate was not rerun; unchanged app source carries v13's Ruby 4.0.7 Rails gate
as a separate condition. V15's Rails 8.1.4 checks are the direct header and minimal-fixture oracles above.
No full Roundhouse suite, general Rails/PostgreSQL/ActiveJob parity, global minimality, alternate server
mode or performance is claimed. Production excludes app tests; patch 50's emitted-test lowering stays
outside this gate. Preparation failures remain in the evidence and are excluded from accepted results,
including an initial omission that accidentally included app tests and a live classifier corrected to
check the logged exception. The accepted omission uses the exact production source export.

## Reproduce

Use Docker with BuildKit, Git, Bash and Python. Run from the AgentMVC root with a fresh build directory,
port 4503 and `conduit-v15-` resources. Set `AGENTMVC_DOCKER_LOCK` to the canonical shared host lock.
On the compile-program host, also wrap each Docker command with its existing `flock.py --shared`
and workshop suite lock; capacity comes from the central `suite.lock.slots` dial.

```bash
R=results/ruby-compile/roundhouse-spinel-conduit-pg-20261102
L=$R/reproduce/with-docker-lock.py
export AGENTMVC_DOCKER_LOCK="${AGENTMVC_DOCKER_LOCK:-$PWD/.work/lane-docker.lock}"
export BUILD_DIR=/tmp/conduit-v15-reproduce RECOVERY_BUILD_DIR=/tmp/conduit-v15-reproduce
export PROBE_BUILD_DIR=/tmp/conduit-v15-reproduce/probes
python3 "$R/reproduce/prepare-toolchain.py" "$BUILD_DIR"
python3 "$L" "$R/reproduce/fresh-build.sh" "$R/reproduce/build-images.sh" toolchain compiled
python3 "$L" "$R/reproduce/run-gate.sh" compiled 4503
python3 "$L" python3 "$R/reproduce/run-common-probe.py" rails conduit-v15-app:compiled /tmp/v15-common.json
python3 "$L" python3 "$R/evidence/edge/edge_diff.py" run conduit-v15-app:compiled 4503 /tmp/v15-edge.json
python3 "$R/evidence/edge/edge_diff.py" diff "$R/evidence/edge/v14-baseline.json" /tmp/v15-edge.json
python3 "$L" python3 "$R/evidence/recovery/probe.py" reproduce conduit-v15-app:compiled done
python3 "$L" python3 "$R/reproduce/header-probe.py" compiled conduit-v15-app:compiled reproduce
python3 "$L" python3 "$R/reproduce/synthetic-json-header.py" final 'application/json; charset=utf-8'
```

The header probe writes fresh results under `PROBE_BUILD_DIR`. To repeat its Rails oracle, build
`toolchain/Dockerfile.rails-oracle` from `variant/source`, then run the header probe with `rails` and
that image tag. The measured dependency resolution is preserved in
[oracle Gemfile](evidence/rails814-Gemfile) and [lock](evidence/rails814-Gemfile.lock).
The minimal Rails oracle entry point is `reproduce/synthetic-rails-oracle.rb`.

All source and patch manifests must verify before building. Recorded evidence is immutable; write new
results outside it. Official dependency fetches are recorded in [fetch audit](evidence/fetch-audit.json).
Step wall times include shared-lock waits and are not performance measurements. Apt layers and a fresh
Rails dependency resolution are not bit-reproducible across hosts; preserve the measured lock when
comparing the oracle condition.

## Cleanup

The measurement removed all owned containers, networks, image tags and build/source folders.
BuildKit cache mounts remain under the no-prune rule. No volume removal or prune ran. See
[cleanup](evidence/cleanup.json), [final verification](evidence/final-verification.json) and
[publication boundaries](evidence/publication.json).
