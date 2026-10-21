# Roundhouse + Spinel: compiled Conduit, v9

**Compiled Conduit passes the fresh-production gate on the October 21 pinned heads,
with 11 Roundhouse patches and one Spinel regression repair.** Rails on the same Ruby 4.0.7
app source also passes. Two Roundhouse patches retire upstream; three new runtime/emitter repairs
and the Spinel nil-propagation repair are required. The 75 gated app files are byte-identical to v8.
Eight edge responses differ from Rails, including one new malformed-JSON payload difference.

This is a separately labelled **compile variant** with a locally patched toolchain. The measured
one-shot source and earlier records are unchanged. **No performance benchmark was run; no throughput claim is made.**
The [v8 record](../roundhouse-spinel-conduit-pg-20261009/README.md) supplies the previous condition;
[run.json](run.json) contains the complete pins and artifact identities.

## v8 → v9

| Condition | v8, October 9 | v9, October 21 |
| --- | --- | --- |
| Ruby, variant/toolchain | 4.0.7 | 4.0.7 |
| Roundhouse | `ea4d3e68` + 10 patches | `1c84d346` + 11 patches |
| Spinel | `f85f04b3a`, unpatched | `6ca6d451b` + 1 patch |
| Net Roundhouse diff | +2,874/−223, 74 files | +2,481/−221, 66 files |
| App delta vs Rails reference-1 | 16 files, +180/−44 | unchanged |
| Production gate | compiled and Rails pass | compiled and Rails pass |
| Common HTTP | 21/21 contract, 3/3 quality | 21/21 contract, 3/3 quality |
| Edge differences vs Rails reference-1 | 7/166 responses | 8/166 responses |

The [patch scoreboard](evidence/patch-count-comparison.json), [app delta](variant/delta.json),
[gate records](#validation) and [edge summary](evidence/edge/summary.json) support this comparison.
The 75 gated files match v8 byte for byte; Gemfile and Gemfile.lock are unchanged
([verification](evidence/source-final-verification.json)). The two inherited app substitutions remain:
the direct author read in place of `association(:author).loaded?`, and `select` assignment in place of
LoginThrottle's Array `reject!` ([source delta](variant/reference-to-variant.diff)).
No workaround was added or separately re-ablated in this condition.

## Patch scoreboard

Eight inherited patches remain after rebasing. Rebase corrections are folded into 10 and 50;
new upstream regression repairs are 82, 83, 84 and Spinel 91. The
[scoreboard](evidence/patch-count-comparison.json) records v8, October 16 and final October 21 counts.

| Patch | Final decision | Lines | Files |
| --- | --- | --- | --- |
| [00](patches/roundhouse/00-interval.patch) | rebased; retained | +10/−1 | 1 |
| [10](patches/roundhouse/10-api-mode-json.patch) | faithful conflict rebase | +158/−40 | 14 |
| [20](patches/roundhouse/20-raw-websocket.patch) | faithful conflict rebase | +347/−16 | 9 |
| [30](patches/roundhouse/30-jobs-boot.patch) | faithful conflict rebase | +420/−1 | 8 |
| [50](patches/roundhouse/50-postgresql-lane.patch) | faithful conflict rebase | +986/−22 | 22 |
| [60](patches/roundhouse/60-rails-surface.patch) | faithful conflict rebase | +219/−39 | 11 |
| 71 | retired upstream | +0/−0 | 0 |
| [74](patches/roundhouse/74-integer-query-range.patch) | faithful conflict rebase | +238/−27 | 11 |
| [80](patches/roundhouse/80-gradual-return-stabilization.patch) | rebased; retained | +87/−40 | 3 |
| 81 | retired upstream | +0/−0 | 0 |
| [82](patches/roundhouse/82-upstream-regression-quoted-bulk-update.patch) | new regression repair | +2/−4 | 1 |
| [83](patches/roundhouse/83-upstream-regression-temporal-initialize.patch) | new regression repair | +6/−31 | 1 |
| [84](patches/roundhouse/84-upstream-regression-mixed-parameter-arm.patch) | new regression repair | +8/−0 | 1 |
| [Spinel 91](patches/spinel/91-upstream-regression-late-hash-return.patch) | new regression repair | +11/−0 | 1 |

The [integrated Roundhouse diff](evidence/roundhouse-final-combined.diff) is **+2,481/−221 in 66 files**;
overlapping edits make per-patch sums slightly different. Spinel adds 11 lines in one file.
Both series have SHA256SUMS and the [production Dockerfile](toolchain/Dockerfile.production)
checks both manifest digests.

**Upstream retirement and trims.** Patch 71 was replaced by `f89915e7`'s ErrorDetail predicate;
81 by `6141f959`'s concrete reload/lock receiver preservation
([71](evidence/rebase/71-retired.diff), [81](evidence/rebase/81-retired.diff)).
Both were already retired on October 16.
[#405](https://github.com/rubys/roundhouse/pull/405), merged as `c967fe8e`, supplies default-on read
binds, but does not select the local libpq backend or replace its array/locking integration.
[#468](https://github.com/rubys/roundhouse/pull/468), merged as `702b1d2f`, supplies framing/close
behavior, trimming 20; request headers, peer address and WebSocket upgrade bytes remain local.
Neither merge retires a whole additional patch
([405 snapshot](evidence/upstream/pr-405.json), [468 snapshot](evidence/upstream/pr-468.json)).
Upstream uniqueness ingestion and relation facades also trim 50 and 60.
Exact retained responsibilities appear in the scoreboard and
[rebase evidence](evidence/rebase/).

**Patch 80 stays.** At the recorded observation,
[PR #1011](https://github.com/rubys/roundhouse/pull/1011), following #964, remains open, draft and
unmerged ([snapshot](evidence/upstream/pr-1011.json)). Upstream does not yet preserve every gradual
return arm. Spinel's pinned head does contain `e7ad51d7f`, the #9398 fix
([pins](evidence/final-pins.json), [upstream repair](evidence/upstream/9398-fix.diff));
the new Hash failure below is a separate regression.

## Ruby conformance findings

**Late Hash return, Spinel 91.** This three-line Ruby program needs no input RBS or Rails:

```ruby
def pack(value); {"n" => value}; end
def relay(value); pack(value); end
p relay([1][1])
```

CRuby 4.0.7 prints `{"n" => nil}`. Pinned Spinel infers both methods as
`(Integer) -> Hash[String, Integer]`, loses the Hash return's nil arm and fails native compilation.
Adjacent parent `ea53627f` compiles and matches CRuby; `a07741ff` fails, as does the pinned head.
With 91, both returns become `Hash[String, untyped]`, compilation succeeds and output matches CRuby.
The Float control already passes without the repair. Sources, signatures, results and harness are in
[late-hash-final](evidence/regressions/late-hash-final/comparison.json).

Patch 91 propagates nullable-local evidence before recomputing returns and their users.
This bounded repair preserves the observed nil conservatively; it proves neither complete convergence
nor exact nullable signatures. The parameter still reads `Integer`.

**Quoted bulk UPDATE, Roundhouse 82.** `d5bbeaaa` adds a second quote layer around `_table_sql`'s
already-quoted physical table name. The exact extracted runtime method emits
`UPDATE ""widgets"" SET value = 2 WHERE id = 1` under both CRuby and Spinel. Parent `61a8f105` and
82 emit `UPDATE "widgets" SET value = 2 WHERE id = 1`. The analyzer infers a String SQL argument;
the content is wrong in both implementations. PostgreSQL rejects the former with SQLSTATE 42601,
which caused the share lifecycle's HTTP 500. This is a Roundhouse runtime regression, not a Spinel
output divergence ([paired Ruby programs](evidence/regressions/bulk-update/),
[app errors](evidence/execution/c-compiled-gate-02-app.log)).

**Temporal constructor, Roundhouse 83.** The upstream change `0b20a0f9` writes an incoming Time into
the generated String storage writer before formatting it. The production program raises
`no implicit conversion of Time into String`; CRuby permits the temporary assignment and the
Rails control creates the same published article successfully. Patch 83 restores the earlier order:
seed the raw slot with its typed default, then write the formatted String. The declared writer is
`String?`, while the supplied value is Time and CRuby's final raw value is String.
An isolated emitted-program pair holds SQL82, all sidecars and every other emitted file identical:
only the five model constructors differ. The same published-article request returns 500 before 83
and 201 after it, with the row present only after. The
[pair](evidence/regressions/time-ablation-comparison.json) records immutable image IDs;
the [source comparison](evidence/regressions/time-isolated/source-comparison.json),
[before manifest](evidence/regressions/time-isolated/before-manifest.json) and
[after manifest](evidence/regressions/time-isolated/after-manifest.json) preserve all emitted-file hashes.
Small standalone copies pass, so this context-dependent case has not been reduced to a standalone
minimal Ruby reproducer, and no first-bad Spinel revision is claimed. The introduced constructor
source and the production request evidence support the Roundhouse repair.

**Mixed unknown argument, Roundhouse 84.** This reduced Ruby/JSON program returns a value
that the analyzer cannot describe precisely, alongside an early Symbol return:

```ruby
require "json"
class Probe
  def self.pick(flag); return :full if flag; JSON.parse('{"n":1}'); end
  def self.consume(value); p value; end
  def self.run; consume(pick(false)); end
end
Probe.run
```

CRuby and v8's emitted sidecar print `{"n" => 1}`. Current Roundhouse keeps `pick -> untyped`
but emits `consume(Symbol)`, and native execution prints `:generate`. Adjacent parent `6c26039c`
matches CRuby; child `0714d4f2` emits Symbol and prints `:generate`. Both recompile independently
with the same patch80 source prerequisite. Patch 84 keeps the explicit unknown arm in the join,
restoring `consume(untyped)` and CRuby's output. Before 84, the full app passes every API file
but live editing times out with a Room/Integer TypeError
([app errors](evidence/execution/c-compiled-gate-05-app.log)).
[Source, signatures and paired results](evidence/regressions/mixed-parameter/) preserve the exact
conditions. The repair retains upstream's bare-untyped policy; join associativity and complete
unknown provenance remain unproved.

**Existing String alias gap, left visible.** A ten-line Ruby case stores a mutable String through a
Hash reader/helper, appends `"b"`, and reads it back. CRuby prints `"ab"`; compiled v8 and current
Spinel print `"a"`. The analyzer reports `Hash[String, untyped]` and a String helper argument; these
types do not establish Ruby's mutation semantics. The
[final repaired toolchain](evidence/regressions/final-standalone/results.json) has the same mismatch.
This is outside the frozen gate and already present in v8, so no new patch is added for it
([source and outputs](evidence/regressions/string-alias/)). A passing production gate is not a claim
of general Ruby conformance.

**Literal mutability control.** The one-line Ruby program `s = "a"; s << "b"; p s` prints `"ab"`
on CRuby but raises FrozenError on both compiled v8 and the final Spinel toolchain. Prefixing the
literal with unary `+` makes this control pass; the Hash alias reproduction already uses that mutable
form and still differs. The inferred value is String in both cases; mutation behavior is the mismatch
([paired controls](evidence/regressions/literal-mutability/)).

**New edge payload difference, left unresolved.** A small Rails API controller rescues
`ActionDispatch::Http::Parameters::ParseError` with `{"error":"parse"}`. Posting the one-byte body
`{` gives HTTP 400 with that JSON on CRuby, but HTTP 400 with `<h1>400 Bad Request</h1>` in the
compiled API. Source change `9f376e22` adds the malformed-body flag and returns nil params;
the generated dispatcher then returns its generic HTML before the controller's rescue can run.
The [small controller and request](evidence/regressions/malformed-json/comparison.json) reproduce it.
It is the eighth Rails edge difference and the sole new v8 difference after matching historical
email redaction. The frozen security test checks the malformed request's status and still passes.

## Gate failures and rebase corrections

| Observation | Classification | Final treatment |
| --- | --- | --- |
| Request-header Struct refusal | rebase contract omission | 10 ships String Hash RBS |
| Missing transaction joinability methods | rebase interface omission | 50 carries upstream methods |
| Late Hash compilation failure | upstream Spinel `a07741ff` | new 91 |
| Share UPDATE HTTP 500 | upstream Roundhouse `d5bbeaaa` | new 82 |
| Published article Time/String HTTP 500 | upstream constructor `0b20a0f9` | new 83; limits above |
| Four deletion failures, 13/17 API files | rebase error in 50 | scoped DELETE restored |
| Live Room/Integer failure after all API checks | upstream join `0714d4f2` | new 84 |

The deletion rebase accidentally put `TRUNCATE ... RESTART IDENTITY CASCADE` in `_adapter_delete`,
removing other records and making later deletes return 404. The correction puts TRUNCATE only in
`_adapter_truncate` and retains the visitor's per-record `DELETE ... WHERE id`.
The final gate validates the corrected series ([finding](evidence/regressions/delete-rebase.json)).
An earlier 8+1 condition passed only [4/17 API files](evidence/execution/c-compiled-gate-02.log);
after 82/83 it passed [13/17](evidence/execution/c-compiled-gate-04.log). Correcting deletion reaches
[17/17 but fails live editing](evidence/execution/c-compiled-gate-05.log) before 84.
The final condition passes all frozen checks. These are diagnostic iterations,
not interchangeable result conditions.

Interrupted attempts retain exit 130 ([classification](evidence/failure-classification.json)).
Fresh replay caught a local assembly error that dropped retained Relation helpers; that build
and its queued gate were cancelled and excluded ([record](evidence/assembly-error.json)).
Early parameter pairs reused a cached parent binary because archived timestamps were old.
They are excluded from attribution. Refreshed source/build-script timestamps force independent
compilation for the authoritative parent-pass/child-fail pair
([cache record](evidence/regressions/parameter-cache-error.json)).

## Validation

| Check | Final v9 result |
| --- | --- |
| Unmodified fresh-production gate | 17/17 API files, live protocol, 4/4 browser, 13/13 security |
| Same app on Ruby 4.0.7 Rails | same checks pass; earlier source-identical control reused |
| Common HTTP probe | 21/21 contract, 3/3 quality |
| Edge comparison | 8/166 vs Rails reference-1; 1/166 vs v8 |
| Pending export at boot | pending → done, completed timestamp present |
| Fresh patch replay | both vendor digests match; both patch manifests verify |

Evidence: [compiled gate](evidence/execution/c-compiled-gate-06.log),
[Rails gate](evidence/execution/rails-gate-01.log),
[common probe](evidence/compiled-v9-common-http-probe.json),
[edge summary](evidence/edge/summary.json), [recovery](evidence/recovery/final.json),
[fresh replay](evidence/rebase/final-replay-11rh.log).
The Rails gate precedes the compiler-only corrections; its 75 app files are identical to the final
condition. The final app image and the frozen gate's app binary match
([captured identity](evidence/execution/c-compiled-gate-06-app-binary.json), [run.json](run.json)).

Each [edge run](evidence/edge/edge_diff.py) has 25 setup registrations and 166 recorded responses:
**191 scripted requests**, plus readiness polling. Rails reference-1 keeps its frozen Ruby 3.3.2.
The seven inherited Rails differences persist: whitespace email updates and later login,
nil-password error duplication, and numeric-password coercion with later login effects.
A new eighth case, malformed JSON, still returns 400 but sends HTML instead of the application's
rescued JSON error. Historical v8 email fields were redacted; matching valid-email fields are mapped
to that placeholder only for the v8 comparison. The other 165 status/body responses match after that
documented mapping ([Rails diff](evidence/edge/v9-rails-reference-1-diff.log),
[v8 diff](evidence/edge/v9-v8-diff.log)).
These comparisons measure observable behavior, with no throughput claim. Full upstream CI and
v8's broader validator/runtime-typing suites were not rerun; their results are not promoted to v9.
The two app substitutions, integer-width bounds, interval-as-string storage and explicit
`SPINEL_WORKERS=4` deployment setting remain
([patches](evidence/patch-count-comparison.json), [deployment](toolchain/Dockerfile.production)).

## Reproduce

Use Docker with BuildKit, git, bash and python3. Run from the AgentMVC repository root.
Use a lock shared with every other Docker job on the host, `conduit-v9-` resources and port **4461**.
The [adapter](reproduce/bin/docker) leaves frozen host scripts unchanged and stops work if startup
exceeds 120 seconds. The [publication inventory](evidence/publication.json) describes the retained
evidence and omitted scratch artifacts; no binary or generated build tree is required in Git.

```bash
R=results/ruby-compile/roundhouse-spinel-conduit-pg-20261021
L=$R/reproduce/with-docker-lock.py
export AGENTMVC_DOCKER_LOCK=.work/lane-docker.lock
"$R/reproduce/prepare-toolchain.sh"
python3 "$L" "$R/reproduce/build-images.sh" toolchain compiled cruby reference
python3 "$L" "$R/reproduce/run-gate.sh" compiled 4461
python3 "$L" "$R/reproduce/run-gate.sh" rails 4461
python3 "$L" python3 "$R/reproduce/run-common-probe.py" rails conduit-v9-app:compiled /tmp/v9-common.json
python3 "$L" python3 "$R/evidence/edge/edge_diff.py" run conduit-v9-app:compiled 4461 /tmp/v9-edge.json
python3 "$L" python3 "$R/evidence/recovery/probe.py" reproduce conduit-v9-app:compiled done
```

Roundhouse is pinned to `1c84d346361237ef9a99b6c01cead7c340532330`; Spinel to
`6ca6d451b97452d8a8b9dd8f6af51a391f060570`. The heads were observed at 2026-10-21T04:41Z
([pins](evidence/final-pins.json)). The final replay uses fresh checkouts from those already fetched
public objects and verifies both vendor digests. Apt layers are not bit-reproducible across hosts.
Final patch, image, source and binary identities are in [run.json](run.json).

The [source manifest](reproduce/gated-source.sha256) pins the 75 gated files, excluding the ledger:

```bash
(cd "$R/variant/source" && shasum -a 256 -c ../../reproduce/gated-source.sha256)
```
