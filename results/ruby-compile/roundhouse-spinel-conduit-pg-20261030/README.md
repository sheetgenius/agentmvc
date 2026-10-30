# Roundhouse + Spinel: compiled Conduit, v13

**No whole patch retires on the October 30 heads.** Roundhouse `75672b31ef` still needs the eight-patch
series, and Spinel `97cea860aa` needs no patch. The full series passes the production gate; every
one-patch omission fails either the build, the gate or boot recovery. Patch 50 remains because upstream's
`db_pg.rb` is not yet wired for the Spinel application target, as its own header says. Patch 60's need is
now a three-file projection and String-key core; a separate probe confirms the reduction found in v12.

This is a separately labelled **compile variant** with a locally patched toolchain. The gated app files
are byte-identical to v12. The measured one-shot source, frozen inputs and earlier records are unchanged.
**No performance benchmark was run; no throughput claim is made.** The
[v12 record](../roundhouse-spinel-conduit-pg-20261029/README.md) supplies the previous condition;
[run.json](run.json) holds this condition's pins, checks and artifact identities.

## v12 to v13

| Condition | v12, October 29 | v13, October 30 UTC |
| --- | --- | --- |
| Roundhouse | `4036ea9c5` + 8 patches | `75672b31ef` + 8 patches |
| Spinel | `d4e804c62` + 0 patches | `97cea860aa` + 0 patches |
| Net Roundhouse diff | +2,340/−131, 54 files | +2,340/−131, 54 files |
| Production gate | compiled and Rails pass | compiled and Rails pass |
| Common HTTP | 21/21 contract, 3/3 quality | 21/21 contract, 3/3 quality |
| Edge comparison | recorded baseline | 0/166 differ from v12 |
| Whole-patch omissions | all eight fail validation | same failure modes |

The v13 heads were observed at 2026-10-30T13:28:57Z. Spinel's default branch is `master`. All v13
builds and probes retain these pins across the local midnight. Full SHAs are in
[initial pins](evidence/initial-pins.json) and [final pins](evidence/final-pins.json).
The v13 input is v12's final series, with no behavioral repair or new compiler patch.

## Patch scoreboard

Each omission uses the full v13 series minus one patch, on the same heads and app.

| Patch | Rebase | Without it in v13 | Decision |
| --- | --- | --- | --- |
| 10 | direct | API 8/17; error paths return 500 | retain |
| 20 | boot context | app check refuses EM/Faye | retain |
| 30 | direct | gate passes; boot export stays pending | retain |
| 50 | direct | Rust E0425; helper used by 74 missing | retain |
| 60 | direct | API 16/17; Article `[]` raises | retain |
| 74 | direct | API 16/17; invalid export ID returns 500 | retain |
| 80 | direct | API 17/17; live endpoint fails | retain |
| 84 | direct | API 17/17; live endpoint fails | retain |

The [series](patches/roundhouse/series), [patch counts](evidence/patch-count-comparison.json),
[combined diff](evidence/roundhouse-full-combined.diff) and
[omission results](evidence/omission-results.json) preserve the full baseline. The Spinel series is
empty; its manifest still verifies.

Seven patches apply directly. Only 20 needs a context merge: upstream `d29719895` added the
`request_hooks` require at the boot anchor. Keep that require and add `faye_websocket` after it.
All per-patch added/removed line counts match v12. Both the initial conflict and its resolution are
recorded in [rebase applications](evidence/rebase-applications.json) and
[rebase notes](evidence/rebase-notes.txt). A [fresh public replay](evidence/fresh-replay-01.log) matches
both recorded vendor-tree digests.

**No patch retired at these heads.** The omission failures reproduce v12's:

- Without 10, API error responses raise
  `ArgumentError: wrong number of arguments (given 0, expected 1)`.
- Without 20, Roundhouse compiles, but the app check reports six unsupported `EventMachine` and
  `Faye::WebSocket` references in `live_rooms.rb` and `live_socket.rb`. The gate stops at that build check.
- Without 30, the full gate and common HTTP pass, and all edge responses match the full v13 series.
  The supplemental boot probe leaves its preseeded export `pending`, with no completion timestamp.
- Without 50, Roundhouse cannot compile: 74 calls 50's missing `postgresql_enabled` helper. Its gate
  preflight stops because no toolchain image was produced. The separate helper-only probe below
  removes this dependency from the backend question.
- Without 60, the export job raises `undefined method '[]' for an instance of Article` at
  `article["comments_total"]`, a projected SQL alias read with a String key. The export never reaches `done`.
- Without 74, `GET /api/user/exports/not-an-export` returns 500 instead of 404, with PostgreSQL
  SQLSTATE `22P02` for an invalid bigint.
- Without 80 or 84, the live endpoint returns 500 with
  `TypeError: no implicit conversion of LiveRooms::Room into Integer`; presence times out.

Gate logs are under `evidence/execution/without-N-gate-01.log`; app logs and recovery results are under
`evidence/omissions/without-N/`. Build failures are not counted as runtime API failures. In particular,
30 passes the ordinary gate but fails the supplemental recovery condition.

## PostgreSQL: driver overlap leaves Spinel wiring local

Upstream's `runtime/spinel/db_pg.rb` implements the Db contract over spinel-pg or the pg gem.
Its header says the Ruby target ships it as `runtime/db.rb`, followed by “Spinel's wiring (`pg` as a
spin dependency) follows.” The Ruby target selects it through `Dialect::for_app` and
`apply_postgresql_tree`. The Spinel application target still selects SQLite. Conduit's recipe emits
that Spinel target with `RH_DATABASE_ADAPTER=postgresql`.
The pinned header and target-selection code are preserved in
[upstream excerpts](evidence/upstream-excerpts.txt).

The v13 **50-helper-only probe** keeps only 50's five-line environment helper, allowing 74 to compile.
Roundhouse and the native executable compile, then production image packaging fails: the emitted Db
uses SQLite FFI and there is no `db/structure.sql`, which the production Dockerfile requires.
No production image was made, so this is not a PostgreSQL runtime failure.
See the [probe result](evidence/probes/50-helper-only/result.json),
[emission manifest](evidence/emission-50-helper-only.json) and
[emitted excerpts](evidence/emission-50-helper-only-excerpts.txt). The
[full-series emission](evidence/emission-full-gated-excerpts.txt) instead includes libpq and schema boot.

In this v13 condition, 50's retained integration covers these groups:

| Group | Local integration | Coverage |
| --- | --- | --- |
| Backend and boot | runtime swap, libpq, structure load | fresh PostgreSQL server |
| SQL and writes | quoting, booleans, RETURNING, inserts | Conduit persistence |
| Arrays | TextArray schema, IR and codecs | PostgreSQL `tag_list` |
| Row locks | reload and `prepare_locked` | app `with_lock` paths |
| Placeholders | libpq lexer and relation binds | raw SQL and bound queries |
| Environment | `postgresql_enabled` helper | also used by 74 |
| Test emission | group-count and model-chain lowering | app tests excluded by gate |
| Other surface | UUID keys, truncation, docs, tests | necessity not established here |

Upstream already offers overlapping driver capabilities: queries, field/OID results, SQLSTATE,
transactions, pools and caches. Replacing the local driver requires reconciling backend selection,
boot, statement handles, schema and codecs. The local `prepare_schema`, `prepare_locked` and
`insert_returning_int` helpers are not upstream's statement API. This is a separate integration task;
no such adaptation is included in the full v13 series. These groups do not establish independent
necessity for every hunk.

**The named PostgreSQL changes were already in v12.** PRs 1481, 1485 and 1486 are ancestors of both
pins. PR 1502 is new to v13, but its first-parent merge delta changes tests and documentation only.
[Ancestry checks](evidence/upstream-overlap.json) preserve the chronology. The keyless-save guard
already retired in v12 remains absent; it is not a new v13 retirement.

## Jobs at boot: recovery remains local

Patch 30 lifts app `after_initialize` registrations and invokes them after database and queue setup,
before workers and HTTP start. The upstream gem-loading commits `e0687cfd13` and `00e6fc2308` preserve
source-gem file programs, requires and autoload order. Both already existed at the v12 pin; neither
replaces this app initializer extraction or the server's hook invocation.

In the v13 supplemental recovery condition, a committed pending export is seeded before server startup
and no enqueue request is sent. The [full series](evidence/recovery/recovery-final.json) completes it
with a timestamp; [without 30](evidence/omissions/without-30/recovery-without-30.json), it stays pending
with a null timestamp. The ordinary gate creates its export after boot and cannot detect this gap.

## Patch 60: the need is now a three-file core

The v13 **60core probe** retains only the projection and String-key `[]` hunks in
`runtime/ruby/active_record/base.rb`, `runtime/ruby/active_record/base.rbs` and
`src/lower/model_to_library/schema.rs`: +47/−20, versus full 60 at +151/−25. These keep extra projected
attributes and let the export job read `article["comments_total"]`.

This reduced v13 condition passes the full gate: 17/17 API, live protocol, 4/4 browser and 13/13 security.
It also passes common HTTP (21/21 contract, 3/3 quality), boot recovery, and the edge comparison
(0/166 differences from the full v13 series). See the [probe result](evidence/probes/60core/result.json)
and [ready reduced patch](evidence/probes/60core/patches/60-rails-surface.patch).

The other 60 hunks are unnecessary for this Conduit condition: record `.id` predicates, zero-argument
scope entries, `find_each`/`update_all` class roots, the `to_set` require and tests. V12 had already
demonstrated the reduction; this confirms it on the new pins and credits no new upstream fix.
The probe has its own manifest and images. The recorded full series keeps the full rebased 60 because
the one-patch omissions ran against that baseline.

## Validation and identities

| Check | Full v13 series |
| --- | --- |
| Compiled fresh-production gate | 17/17 API, live, 4/4 browser, 13/13 security |
| Same source on Ruby 4.0.7 Rails | same checks pass |
| Common HTTP | 21/21 contract, 3/3 quality |
| Edge vs recorded v12 | 0/166 responses differ |
| Pending export at boot | pending to done; timestamp present |
| Fresh patch replay | both manifests and vendor digests match |

Evidence: [compiled gate](evidence/execution/compiled-gate-01.log),
[Rails gate](evidence/execution/rails-gate-01.log),
[common HTTP](evidence/compiled-v13-common-http-probe.json), [edge summary](evidence/edge/summary.json),
[recovery](evidence/recovery/recovery-final.json) and
[source verification](evidence/source-verification.json).
The v13 edge comparison uses v12's recorded compiled run. V12 records the existing differences from
the earlier fresh Rails reference-1 run; that edge baseline was not rebuilt here.

The full v13 compiled tag and production gate serve the same native binary, `ac9dce1624a5…`, from
image `c81577a740e7…`. The gate captures the image ID and binary hash before cleanup. Each omission
logs a fresh Roundhouse compilation. The seven successful omission compilations produce distinct
compiler binaries, all different from the full control; without 50 produces none. The auxiliary
probes also have distinct compiler binaries. See [identity validation](evidence/identity-validation.json),
[gate summaries](evidence/gate-summaries.json) and [artifact validation](evidence/artifact-validation.json).

Step wall times include shared-lock queues and are not compiler performance measurements. Builds
and gates also take the shared workshop heavy lock. All Docker work takes the canonical host lock;
the small auxiliary emission capture takes that Docker lock alone.

## Reproduce

Use Docker with BuildKit, git, bash and python3. Run from the AgentMVC repository root. Set the canonical
lock shared with every other Docker job on the host. Use a fresh build directory, `conduit-v13-`
resources and port **4501**. The [adapter](reproduce/bin/docker) leaves frozen host scripts unchanged;
[fresh-build.sh](reproduce/fresh-build.sh) refreshes source mtimes inside the lock so the shared Cargo
cache cannot serve a stale compiler.

```bash
R=results/ruby-compile/roundhouse-spinel-conduit-pg-20261030
L=$R/reproduce/with-docker-lock.py
export AGENTMVC_DOCKER_LOCK="$PWD/.work/lane-docker.lock"
export BUILD_DIR=/tmp/conduit-v13-reproduce RECOVERY_BUILD_DIR=/tmp/conduit-v13-reproduce
python3 "$R/reproduce/prepare-toolchain.py" "$BUILD_DIR"
python3 "$L" "$R/reproduce/fresh-build.sh" "$R/reproduce/build-images.sh" toolchain compiled
python3 "$L" "$R/reproduce/run-gate.sh" compiled 4501
python3 "$L" "$R/reproduce/run-gate.sh" rails 4501
python3 "$L" python3 "$R/reproduce/run-common-probe.py" rails conduit-v13-app:compiled /tmp/v13-common.json
python3 "$L" python3 "$R/evidence/edge/edge_diff.py" run conduit-v13-app:compiled 4501 /tmp/v13-edge.json
python3 "$L" python3 "$R/evidence/recovery/probe.py" reproduce conduit-v13-app:compiled done
```

Roundhouse is pinned to `75672b31ef4ef5756f88ec98a90ae0bea057ff26`; Spinel to
`97cea860aa2b3c8f4b1431ca67d3e9a99feb738f` (`2026.10.25+1322`). The toolchain step fetches both public
repositories, replays both series, and verifies each manifest and vendor-tree digest. Apt layers are
not bit-reproducible across hosts. The recipe is v12's with v13 names, port, pins, manifests and cache
IDs. No binary or generated build tree is required in Git.

The [source manifest](reproduce/gated-source.sha256) pins this v13 condition's gated files:

```bash
(cd "$R/variant/source" && shasum -a 256 -c ../../reproduce/gated-source.sha256)
```

## Limits and cleanup

This checks the pinned v12 Conduit compile variant and the recorded production and supplemental
probes. It does not establish general PostgreSQL or ActiveJob parity, a globally minimal patch set,
the full Roundhouse suite, or throughput. Production excludes app tests, so 50's emitted-test lowering
hunks are outside this gate.

Two setup/capture errors are preserved: initial preparation caught a port substitution inside a
source-manifest hash and restored the unchanged manifest before Docker; the first full emission
capture included app tests excluded by production and was refused at `JWT.encode`. The corrected
capture follows Dockerignore. Cancellation of an older queued capture was denied by OS policy;
it later reused the completed artifact without a second capture.

No `conduit-v13-` containers or networks remain. Owned build folders and source checkouts were deleted;
own images and Cargo cache mounts are retained. No volume removal or prune ran, and unrelated
application resources were untouched. See [cleanup](evidence/cleanup.json).
Published evidence removes local home paths, private-resource names and secret values; patches,
manifests and app source retain their measured bytes.
