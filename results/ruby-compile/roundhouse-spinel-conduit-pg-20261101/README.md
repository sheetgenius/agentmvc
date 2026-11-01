# Roundhouse + Spinel: compiled Conduit, v14

**Patch 60 retires; patch 10 reduces to one original JSON-header hunk.** On the November 1 pins,
Roundhouse `7766b5ceea` retains seven patches and Spinel `0ed86eae9` retains zero. This Case B series
passes the production gate, common HTTP checks, edge comparison and boot recovery while preserving
v13's UTF-8 JSON Content-Type. Case A, with six Roundhouse patches, passes those same checks but loses
the charset. The frozen gate alone cannot see that difference.

This is a separately labelled **compile variant** in the compile program. The app is byte-identical
to v13; the measured one-shot source, frozen inputs and earlier records are unchanged.
**No performance benchmark was run; no throughput claim is made.** The
[v13 record](../roundhouse-spinel-conduit-pg-20261030/README.md) supplies the previous condition;
[run.json](run.json) records this condition's pins, patch counts, checks and artifact identities.

## v13 to v14

| Condition | v13, October 30 | v14 Case B, November 1 UTC |
| --- | --- | --- |
| Roundhouse | `75672b31ef` + 8 patches | `7766b5ceea` + 7 patches |
| Spinel | `97cea860aa` + 0 patches | `0ed86eae9` + 0 patches |
| Net Roundhouse diff | +2,340/-131, 54 files | +2,108/-106, 46 files |
| Production gate | compiled and Rails pass | compiled passes; Rails result inherited |
| Common HTTP | 21/21 contract, 3/3 quality | 21/21 contract, 3/3 quality |
| Edge comparison | recorded baseline | 0/166 differ from v13 |
| Pending export at boot | done; timestamp present | done; timestamp present |

The v14 heads were observed at 2026-11-01T07:26:09Z and remain fixed across both cases. Spinel's
default branch is `master`. Full revisions, manifests and vendor-tree digests are in the
[initial pins](evidence/initial-pins.json), [Case A pins](evidence/case-a-pins.json) and
[Case B pins](evidence/case-b-pins.json). All 75 manifested app files and the complete app-tree
digest match v13; see [source verification](evidence/source-verification.json).

## Cases and patch scoreboard

Both v14 cases use the same upstream heads, app and frozen gate inputs. B differs from A only by
the original charset-normalization hunk of patch 10.

| v14 condition | Roundhouse patches | Net Roundhouse diff | Result |
| --- | --- | --- | --- |
| A: omit all 10 and 60 | 6 | +2,105/-105, 46 files | gate passes; charset lost |
| B: retain one 10 hunk | 7 | +2,108/-106, 46 files | gate passes; charset preserved |

Spinel has zero local patches in both v14 cases. Each case passes API 17/17, live protocol,
browser 4/4 and security 13/13; common HTTP passes 21/21 contract and 3/3 quality checks.
Each case matches all 166 normalized edge responses from v13 and completes a committed pending
export seeded before startup, without an enqueue request, with a completion timestamp.
See the [Case A summary](evidence/case-a-summary.json) and [Case B summary](evidence/case-b-summary.json).
These results exclude the supplemental two-peer login-throttle limit described below.

| Patch | v14 application | v14 retained diff | Decision and evidence |
| --- | --- | --- | --- |
| 10 | one original hunk | +3/-1, 1 file | retain JSON charset; A loses it |
| 20 | direct | +347/-16 | retain; live passes with it |
| 30 | automatic context merge | +419/-1 | retain; boot recovery passes with it |
| 50 | automatic context merge | +1,008/-22 | retain; PostgreSQL gate passes with it |
| 60 | absent | no local diff | retire; export and recovery pass |
| 74 | direct | +236/-26 | retain; API passes with it |
| 80 | direct | +87/-40 | retain; live passes with it |
| 84 | direct | +8/-0 | retain; live passes with it |

**The other six omissions were not rerun.** Their need is carried from v13's omission failures,
rather than re-proven on these v14 heads. Passing with them retained establishes that the series
works in this condition; it does not establish fresh necessity for each patch or every retained line.

The [Case B series](patches/roundhouse/series), [patch counts](evidence/patch-count-comparison.json)
and [combined diff](evidence/roundhouse-full-combined.diff) preserve the applied inputs. Case A has
its own [series](evidence/case-a/patches/roundhouse/series) and
[combined diff](evidence/case-a/roundhouse-combined.diff). Both Spinel manifests verify an empty series.

## Patch 60: upstream replaces the remaining core

Credit goes to [Roundhouse #1596](https://github.com/rubys/roundhouse/pull/1596), merged as
`136d140757`, for projected attributes and String/Symbol index access. That merge is an ancestor of
the v14 pin. The export job can read its projected SQL alias through `article["comments_total"]`
without a local patch 60. Both v14 cases pass the export API check and boot recovery without any
60 hunk or replacement app change.

V13 had already shown that its three-file projection/String-key core was sufficient, despite keeping
the full patch as its omission baseline. V14 drops the entire patch. This credits #1596 for replacing
that remaining core; it does not claim every old 60 hunk was independently necessary in v13.

## Patch 10: JSON lowering retires; the charset hunk stays

Credit goes to [Roundhouse #1646](https://github.com/rubys/roundhouse/pull/1646), merged as
`7766b5ceea`, for JSON response lowering in controller callbacks and rescue handlers. The Spinel HTTP
bridge still forwards `controller.content_type` verbatim, so that upstream change leaves a separate
header difference.

The request is `GET /api/tags` with `Accept: application/json`. In the supplemental transport condition:

| Native condition | Status and body | Content-Type |
| --- | --- | --- |
| Verified v13 full-series control | 200, `{"tags":[]}` | `application/json; charset=utf-8` |
| v14 Case A, no patch 10 | 200, `{"tags":[]}` | `application/json` |
| v14 Case B, one 10 hunk | 200, `{"tags":[]}` | `application/json; charset=utf-8` |

The UTF-8 form matches the [response-format contract](../../../spec/docs/api-response-format.md).
The [retained patch](patches/roundhouse/10-api-transport-residual.patch) is one original +3/-1 hunk
in `runtime/spinel/scaffold/main.rb`. It changes the exact `application/json` value to
`application/json; charset=utf-8` before writing the outgoing header; other media types keep their
controller-selected values. All old callback-lowering, test, request-header RBS and socket-peer hunks
from 10 remain dropped.

The frozen production gate passes in Case A even with the wrong charset. The normalized edge probe
compares status and body, so it also misses this header difference. The supplemental
[transport comparison](evidence/transport-comparison.json) is what distinguishes the recommended
Case B series from Case A. This is the smallest nonempty subset of original 10 hunks, not a proof
of a globally minimal compiler patch set.

An independent [tiny API app](evidence/synthetic-json-header/) reproduces the same difference without
Conduit models: both native cases return 200 and `{"ok":true}` at `GET /probe`, while only B sends
the UTF-8 charset. Its SQLite boot belongs only to this synthetic fixture; the measured Conduit
conditions use PostgreSQL throughout. See the [A result](evidence/case-a-synthetic-json-header.json)
and [B result](evidence/case-b-synthetic-json-header.json).

## Rebase and boot context

All six retained patches preserve their v13 added/removed line counts. Patches 30 and 50 require only
automatic context merges at the module-list and adapter-emission anchors. The recorded public series
already includes those context updates and applies directly during a fresh replay. There is no manual
behavioral repair. See [rebase applications](evidence/rebase-applications.json),
[rebase notes](evidence/rebase-notes.txt) and the fresh vendor-digest replays for
[A](evidence/fresh-replay-case-a.json) and [B](evidence/fresh-replay-case-b.json).

[Roundhouse #1651](https://github.com/rubys/roundhouse/pull/1651), merged as `40e27c25bc`, runs
initializer top-level code at boot and adds the Spinel logger require. It leaves `after_initialize`
hooks to ledger warnings. Local 30 still extracts the guarded recovery hook and invokes it after
database and ActiveJob drain setup, before workers and the listener. Patch 20's Faye require still
applies directly. Both v14 boot-recovery probes pass; no additional 20/30 repair was needed.
The [boot excerpts](evidence/boot-context.txt) and [overlap inventory](evidence/upstream-overlap.json)
preserve this context. This does not replace the unrerun omission checks.

## Validation, identities and an unchanged limit

| Check | v14 Case A | v14 Case B |
| --- | --- | --- |
| Compiled fresh-production gate | 17/17 API, live, 4/4 browser, 13/13 security | same checks pass |
| Common HTTP | 21/21 contract, 3/3 quality | same checks pass |
| Normalized edge vs v13 | 0/166 differ | 0/166 differ |
| Pending export before boot | done; timestamp present | done; timestamp present |
| Supplemental JSON charset | regresses from v13 | matches v13 |
| Supplemental two-peer login throttle | observed limit | same observed limit |

The two-peer login-throttle isolation check fails on the exact v13 native control and both v14 cases.
After one peer exhausts its budget, the distinct second peer receives 429 where the probe expects 401.
The raw transport probe exits are 1 for v13, v14 A and v14 B. This is an unchanged observed limit,
not a pass, and does not justify retaining any socket-peer hunk. See the raw
[v13 control](evidence/case-control-v13-transport.json), [A](evidence/case-a-transport.json) and
[B](evidence/case-b-transport.json). B restores the sole regression against transport checks the
verified v13 control passes: the charset check.

Within each v14 case, the production image, gate and boot-recovery probe serve the same native binary.
A and B have distinct compiler and server hashes. Case B's server is `d7c1bf5d9c12…`, in image
`505e25cc7f0d…`; the v13 transport control matches its recorded native hash exactly. See
[identity validation](evidence/identity-validation.json), [gate summaries](evidence/gate-summaries.json)
and [run.json](run.json) for full identities. No new Rails-image gate ran: the unchanged app inherits
v13's verified Ruby 4.0.7 Rails result, which remains a separate recorded condition.

## Reproduce

Use Docker with BuildKit, Git, Bash and Python. Run from the AgentMVC repository root, with a fresh
build directory, port 4501 and `conduit-v14-` resources. Set `AGENTMVC_DOCKER_LOCK` to the canonical
lock shared by all Docker jobs on the host. On the compile-program host, also take its existing
workshop heavy lock through `flock.py` with `HEAVY_SLOTS=3` around each Docker command below.

```bash
R=results/ruby-compile/roundhouse-spinel-conduit-pg-20261101
L=$R/reproduce/with-docker-lock.py
export AGENTMVC_DOCKER_LOCK="${AGENTMVC_DOCKER_LOCK:-$PWD/.work/lane-docker.lock}"
export BUILD_DIR=/tmp/conduit-v14-reproduce RECOVERY_BUILD_DIR=/tmp/conduit-v14-reproduce
export PROBE_BUILD_DIR=/tmp/conduit-v14-reproduce/probes
python3 "$R/reproduce/prepare-toolchain.py" "$BUILD_DIR"
python3 "$L" "$R/reproduce/fresh-build.sh" "$R/reproduce/build-images.sh" toolchain compiled
python3 "$L" "$R/reproduce/run-gate.sh" compiled 4501
python3 "$L" python3 "$R/reproduce/run-common-probe.py" rails conduit-v14-app:compiled /tmp/v14-common.json
python3 "$L" python3 "$R/evidence/edge/edge_diff.py" run conduit-v14-app:compiled 4501 /tmp/v14-edge.json
python3 "$L" python3 "$R/evidence/recovery/probe.py" reproduce conduit-v14-app:compiled done
python3 "$L" python3 "$R/reproduce/transport-probe.py" case-b
```

The final transport command is expected to exit 1 because it retains the observed login-throttle limit;
its JSON charset check should pass for Case B. New probe output goes under `PROBE_BUILD_DIR`, leaving
the published evidence unchanged. To run the independent header fixture on the same B toolchain:

```bash
python3 "$L" python3 "$R/reproduce/synthetic-json-header.py" case-b 'application/json; charset=utf-8'
```

The source and [manifest](reproduce/gated-source.sha256) verify from the record:

```bash
(cd "$R/variant/source" && shasum -a 256 -c ../../reproduce/gated-source.sha256)
```

Roundhouse is pinned to `7766b5ceeadf0b23c55230c29ee5adc5f249f018`; Spinel to
`0ed86eae9d877b28527c8e7eec1b60dc69533a70` (`2026.10.25+1622`). Preparation fetches those public
revisions, replays Case B's series and verifies both manifests and vendor-tree digests. Case A's inputs
are preserved separately under `evidence/case-a/`; the commands above select B. Apt layers are not
bit-reproducible across hosts. No binary or generated build tree belongs in Git.

## Limits and cleanup

This record checks the pinned Conduit compile variant and the named production and supplemental probes.
It does not establish general Rails, PostgreSQL or ActiveJob parity, alternate-server behavior,
necessity of the unrerun patches, a globally minimal series, the full Roundhouse suite or throughput.
Production excludes app tests, so patch 50's emitted-test lowering remains outside this gate.
Step wall times include shared-lock waits and are not compiler or application performance measurements.

The first synthetic launch lacked writable SQLite storage although its native compilation succeeded.
Corrected packaging creates the directory and reuses that same A binary. The
[preparation evidence](evidence/synthetic-preparation/notes.txt) preserves the failure; it changes no
production app source or result.

No owned v14 containers, networks or image tags remain. Owned build and source checkouts were removed;
BuildKit cache mounts remain. No prune or volume removal ran. See [cleanup](evidence/cleanup.json).
Published evidence removes local home paths, unrelated private-resource names and credential values;
patches, manifests and app source retain their measured bytes. The
[publication note](evidence/publication.json) records that boundary.
