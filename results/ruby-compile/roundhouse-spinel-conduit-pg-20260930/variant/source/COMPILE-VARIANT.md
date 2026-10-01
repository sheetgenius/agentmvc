# Conduit compile variant v2

**Accepted on the complete 12-patch integrated series plus patch 70.** Native
API 17/17, security 13/13, live protocol PASS, and Playwright 4/4 pass. The
same Rails source passes the production gate under CRuby. No action is needed.
This ledger describes every delivered file differing from the reference;
it supersedes the inherited v1 ledger.

Reference: `results/one-shot-v2-rails-expert/pilot-1/reference-1/source`.
The input was copied from `workers/w11-conduit-pg/variant`, without changing
that worker's files. Evidence paths below are relative to the w15 directory.

## Acceptance and exact delta

| Gate | Result | Receipt |
| --- | --- | --- |
| Native API | 17/17; 237 requests | `runs/08-native-full/gates.log` |
| Native security | 13/13; 52 requests | Same receipt |
| Native protocol/browser | PASS; 4/4 | Same receipt |
| Rails production | All four gates pass | `runs/rails-production-01/gates.log` |
| Rails development | Zeitwerk, RuboCop, 21 tests pass | `runs/rails-dev-01/` |

The final emitter's fresh output is byte-identical across **337 files** to
what built the accepted native executable. Source comments and this ledger
therefore do not invalidate the binary receipt. See
`logs/delivery-emission-comparison.json`. Strict emission has zero errors;
`roundhouse check` has zero parse errors, zero errors, and 196 warnings.

The delta inventory excludes only `harness/`, `realworld_spec/`, `security/`,
and `db/structure.sql`, as requested. Exact recursive diff and counts are
`logs/reference-variant.diff`, `logs/variant-delta.json`, and
`logs/variant-delta.stat`. Regenerate with `./tools/audit-variant.py`.

- Application/runtime source: **17 files, 220 insertions, 48 deletions**.
- Inherited regression tests: **2 files, 77 insertions, 0 deletions**.
- This ledger: **1 file, 327 insertions, 0 deletions**.
- Total: **20 files, 624 insertions, 48 deletions**.

The actual per-file counts are reproduced below; additions/deletions count
lines, including comments. They are equivalent to no-index Git numstat.

```text
 COMPILE-VARIANT.md                                           |  327 (+327/-0)
 app/controllers/application_controller.rb                    |   81 (+71/-10)
 app/controllers/articles_controller.rb                       |   17 (+9/-8)
 app/controllers/comments_controller.rb                       |    8 (+4/-4)
 app/controllers/exports_controller.rb                        |    6 (+5/-1)
 app/controllers/profiles_controller.rb                       |    2 (+1/-1)
 app/controllers/shares_controller.rb                         |   16 (+9/-7)
 app/controllers/tags_controller.rb                           |    3 (+2/-1)
 app/controllers/users_controller.rb                          |   27 (+21/-6)
 app/jobs/export_articles_job.rb                              |    3 (+2/-1)
 app/models/article_export.rb                                 |    3 (+2/-1)
 app/models/user.rb                                           |    7 (+6/-1)
 app/services/article_commit.rb                               |    6 (+4/-2)
 app/services/json_cast.rb                                    |    9 (+9/-0)
 app/services/live_rooms.rb                                   |   13 (+11/-2)
 app/services/login_throttle.rb                               |    9 (+6/-3)
 app/services/token_codec.rb                                  |   52 (+52/-0)
 config/initializers/recover_exports.rb                       |    6 (+6/-0)
 test/controllers/compile_variant_contract_test.rb            |   39 (+39/-0)
 test/services/token_codec_test.rb                            |   38 (+38/-0)
 20 files changed, 624 insertions(+), 48 deletions(-)
```

## Framework forms restored

All `TEMPORARY(w10)` labels are removed. The supported reference forms are
back: bang find/create with association objects, case-insensitive uniqueness
validations, typed duplicate-error predicates, SecurityUtils, `.to_set`,
association-plus-scope chains, export association creation, and
`left_joins` aggregation. All four article locking paths use the reference
`with_lock`. `FavoritesController`, `Article`, and `ArticleShare` are now
byte-identical to the reference. Native gates exercise these restorations.

Patch 70 adds the missing model-instance `with_lock` analysis registration,
plus symbolic `errors.of_kind?` lowering over retained structured errors.
Only two literal Symbol arguments are claimed; other predicates still fail
strict emission explicitly. The runtime body and RBS signature are shared.
The patch contains no application-specific name or Spinel source changes.

Some old labels overstated what patch 60 fixed. The remaining `loaded?`,
model-class recovery iteration, association lookup, and computed alias
limitations below were reproduced on the full series rather than assumed
resolved. Every remaining source workaround has a reason comment.

## File-by-file ledger

### `app/controllers/application_controller.rb`

Reason: native parameters retain string values rather than typed JSON and
strong-parameter objects. `json_body`, `object!`, wrappers, scalar filtering,
`JsonCast`, and `param` preserve JSON request types, lazy parse failure order,
and malformed-JSON 400 responses. An explicit field array avoids the
controller-rest-parameter ingest gap; symbol attribute keys satisfy generated
constructors. TokenCodec replaces unsupported JWT gem dispatch. The author
reader removes an unsupported association `loaded?` call whose two reference
branches already return the same author. Set calls and error projections
have been restored.

Impact: **edge-case differences**, outside the accepted JSON contract:

- Object inputs supplied solely by URL-encoded forms or bracketed query
  parameters are rejected with 422 instead of becoming Rails parameter objects.
- The inherited native `param` lane does not implement Rails' body-over-query
  merge for GET JSON bodies with conflicting filter/pagination keys. CRuby
  continues to use Rails' merged `params` for these scalar reads.
- String `strip` differs from Rails Unicode `blank?`: Unicode-whitespace-only
  login fields proceed to authentication instead of the blank-field 422;
  NUL-only strings are treated as blank by `strip`, unlike Rails `blank?`.
- Authentication has the TokenCodec edge differences described below.

The author simplification, symbol keys, sets, default pagination after integer
conversion, and parser rescue have **no contract behavior difference**.
`runs/06-gates-workspace/app.log` proves the unresolved author reader.

### `app/controllers/articles_controller.rb`

Reason: filters use the parsing helper; JSON objects use string keys and the
scalar filter. Explicit `key?` plus indexing avoids Spinel's absent-key
`Hash#fetch` Array-default bug. `ArticleCommit` receives the typed Hash rather
than unsupported `to_unsafe_h`. Association scope revocation is restored.

Impact: **none within the contract**. Inherits the parameter-input and commit
edge cases documented in their owning files. Absent tags still become `[]`;
explicit invalid or null tags still fail validation.

### `app/controllers/comments_controller.rb`

Reason: use the parsing helper for scalar parameters and cast a raw JSON body
like Rails' string attribute writer. `.to_set` is restored.

Impact: **none within the contract**; inherits the object-input limitations
from ApplicationController.

### `app/controllers/exports_controller.rb`

Reason: explicit integer-query serialization prevents PostgreSQL 22P02/500 for
nonnumeric export IDs and retains Rails' numeric-prefix behavior. Owner lookup
uses `user_id` directly: the controller association rewrite still derives
nonexistent `current_user_id` from the ivar name. Association creation is restored.

Impact: **none for exercised IDs and authorization**. Native parsing of
integers outside the machine range is not established. Rails' full integer
range/serialization semantics are not claimed. The bad generated lookup is
retained in `runs/03-lock-and-errors/out/app/controllers/exports_controller.rb`.

### `app/controllers/profiles_controller.rb`

Reason: the sole delta is `param(:username)` for lazy JSON parse ordering.
The original bang find/create and association values are restored.

Impact: **none within the contract**; inherits the parsing/input limitations.

### `app/controllers/shares_controller.rb`

Reason: raw JSON uses string-key reads and needs no `to_unsafe_h`.
`wrap: false` preserves this controller's different wrapper name. Scalar
route IDs use the parsing helper. Locking and association scopes are restored;
the pluck/update/result statements replace a local relation plus `tap`, whose
relation type Roundhouse cannot retain correctly.

Impact: **none within the contract**. The same active IDs are read and revoked
under the same article lock, then broadcast. Inherits object-input limitations.
Strict failures for the local relation are in `runs/01-restored/emit.log` and
`runs/02-lock-catalog/emit.log`.

### `app/controllers/tags_controller.rb`

Reason: native Relation lacks `connection`, and Connection lacks `select_values`.
Use the class connection with a named column and map its result rows.

Impact: **none**. The same SQL filters published articles and produces distinct,
ordered tags. The inherited regression test also checks publication filtering.

### `app/controllers/users_controller.rb`

Reason: typed JSON uses string-key reads and scalar filtering. Direct model
writers followed by `save!` avoid the inherited Spinel crash in the generated
RBS-seeded `update!` hash consumer. Login uses the shared blank predicate;
tokens use TokenCodec. The reference `of_kind?` and `to_hash` calls are restored.

Impact: **none within the contract**. Inherits the blank/input/JWT edge cases.
The direct writers preserve supplied-nil handling, callbacks, validation, and
single-record save behavior. The w11 reduction establishes wrong RBS-seeded
hash-update behavior, not a fully identified compiler crash root cause.

### `app/jobs/export_articles_job.rb`

Reason: the sole semantic source substitution is
`article["comments_total"]` for an unsupported computed named getter.
The original left join, grouping, attributes projection, ordering, and lock
are restored; the PostgreSQL-specific JSON aggregate workaround is removed.

Impact: **none**. Both readers return the same projected count, converted with
`to_i`. The export remains one aggregate-query snapshot followed by its locked,
idempotent completion.

### `app/models/article_export.rb`

Reason: this model-class query becomes a materialized Array before `find_each`
dispatch, including with an explicit model receiver. Use `each` for recovery.
Native boot failed with the restored form in `runs/03-lock-and-errors/app.log`;
`runs/probe-explicit-root/out/` records the unsuccessful alternate spelling.

Impact: **edge-case difference**: CRuby recovery materializes all pending
exports instead of Rails' batched, primary-key-ordered traversal. Memory use,
enqueue order, and concurrent-change observation can differ for large/changing
pending sets. Recovery still queues each observed pending export; the job is
idempotent. The fixed gate verifies the persisted export contract, not every
batching option.

### `app/models/user.rb`

Reason: the minimum-password rule uses an equivalent callback because
Roundhouse drops the validation macro's `if:` lambda. The original
case-insensitive uniqueness validations and secure-password writer are restored.

Impact: **none in HTTP validation behavior**. Condition, message, and callback
order remain the same. The custom callback's internal error type is `:invalid`
where the Rails length validator uses `:too_short`; code consuming error details
outside this application could distinguish them.

### `app/services/article_commit.rb`

Reason: raw JSON strings need Rails-equivalent attribute casting; generated
`update!` reads symbol keys. The reference locking form is restored.

Impact: **edge-case difference**: casting precedes the slug comparison.
A non-String title whose cast equals the current title does not rotate the
slug, whereas the reference compares the raw value first. Boolean titles also
use `t`/`f` for a new slug prefix rather than the reference's `true`/`false`.
Revision checks, lock/revalidation, tag checks, writes, and broadcasts match
the accepted contract. String-title edits are unaffected.

### `app/services/json_cast.rb` — added

Reason: provide Active Model's JSON scalar string cast: nil stays nil,
booleans become `t`/`f`, other scalars use `to_s`.

Impact: **none as a string attribute cast**. Its placement before slug
comparison has the ArticleCommit edge difference above.

### `app/services/live_rooms.rb`

Reason: an explicit Room avoids Spinel's `Struct#members` collision with the
member field. A deleted nil seed selects the boxed-key hash needed for socket
keys. The original association-plus-scope broadcast query is restored.

Impact: **none for room behavior**. Locking, member maps, presence, cap,
ordering, and revocation match the contract. Room is internally a class rather
than a Struct, with no Struct introspection or externally supplied constructor.

### `app/services/login_throttle.rb`

Reason: eager initialization is restored, without lazy duplication. `select`
replaces `reject!` on the boxed Array that the default-block Hash produces;
the exact integrated regression was missing `Array#reject!` dispatch. The
limit is decided under the mutex and the Failure raised after leaving it,
because Spinel loses custom exception attributes raised through synchronize.

Impact: **none for the application's finite timestamp values**. The same
email/IP key, strict 60-second cutoff, append, and >20 decision are protected
by the same lock. Replacing the private Array changes allocation and object
identity, which the application does not expose. Security s13 proves the 21st
failed request returns 429; failed login requests return 401 again.

### `app/services/token_codec.rb` — added

Reason: the JWT gem is not compiled; implement the application's HS256
encode/decode path with binary SHA256 HMAC and the restored SecurityUtils.

Impact: **none for issued tokens and the frozen JWT/security contract**.
HS256 interoperability, exp/nbf boundaries, binary/long-key HMAC, and tampering
are covered by inherited tests. **Edge-case differences**, empirically checked
under CRuby in `logs/jwt-edge-probe.log`: correctly signed tokens with padded
Base64 segments are rejected although JWT accepts them; non-object payloads
and nonscalar exp values become authentication 401 instead of the reference
controller's TypeError/NoMethodError 500. This is an app codec, not complete JWT
or arbitrary token-claim parity. The dependency remains for reference tests.

### `config/initializers/recover_exports.rb` — added

Reason: native boot hooks do not execute the Docker entrypoint's Rails runner;
recover after server initialization instead. Guard with `defined?(Rails::Server)`
so migrations, tests, and runner invocations do not gain this boot action.

Impact: **edge-case difference under CRuby**: production already queues recovery
in the unchanged Docker entrypoint; server boot can queue it again. A development
server also gains recovery. Duplicate jobs are idempotent and exports persist,
but enqueue count and startup work differ. Native boot recovers once.

### `test/controllers/compile_variant_contract_test.rb` — added

Reason: inherited regression coverage for registration/token interoperability,
duplicate identity status/messages, invalid registration, and published tags.

Impact: **none in deployed application behavior**; tests are Docker-excluded.

### `test/services/token_codec_test.rb` — added

Reason: inherited HMAC, JWT interoperability, expiry/not-before, algorithm,
signature, and malformed-token regression coverage.

Impact: **none in deployed application behavior**; tests are Docker-excluded.

### `COMPILE-VARIANT.md` — added

Reason: the authoritative source-difference, behavioral-impact, and acceptance
ledger required for v2. Counts include this file itself.

Impact: **none**; documentation only.

## Excluded infrastructure and limits

The unchanged gate copies are excluded from the application delta. The full
PostgreSQL structure dump is also excluded as requested; native boot creates
all 14 tables, including GoodJob and Rails metadata tables. It was inherited
from w11's real migration dump; schema.rb and migrations match the reference.

Native jobs use the integrated job drain rather than all GoodJob gem features.
The room and throttle state remain process-local, as in the reference. Arbitrary
integer ranges, unsupported input media, full JWT functionality, and concurrent
recovery batches are outside the acceptance claim. The large native security
body took 111.4 seconds versus 347 ms in Rails at v2 time; root cause (quadratic string building in the PG
placeholder rewriter) was fixed by roundhouse patch 70 (w16); with it the 2 MB POST takes ~75 ms natively.
No unsupported-emission switch, stub, edited emitted source, or changed gate
fixture was used for acceptance.


## v3 additions (lead, after load testing)

v3 = v2 + two source changes, found by the benchmark smoke run, not by the functional gates.

### `app/controllers/articles_controller.rb` (create)

Before (v2 / reference shape): `Article.new(permitted(...).merge(author:, status:, published_at:, tag_list: tags.uniq, slug:))`.
After: `Article.new(permitted(...))` followed by typed writers `author=`, `status=`, `published_at=` (only when
published), `tag_list=` with fresh String copies (`tags.uniq.map { |tag| "#{tag}" }`), `slug=`.

Reason: under the benchmark's create_article load (~1,200 creates/s) the compiled binary died with SIGSEGV
(exit 139, not OOM; also with SPINEL_WORKERS=1) inside `sp_str_length` called from `Db.encode_array`
(gdb: workers/w19-load-crash/logs/debug02-gdb-live.log). Copying the JSON-derived tag strings removed the crash,
but values that still travelled through the mixed-type merged Hash were occasionally corrupted (an INSERT with
published_at year 8920956 -> PG 22008, 500). Assigning through typed writers removed both symptoms
(lead/crash: v3a/v3b 0 failures over ~24k creates; v3full1/v3full2 two full 9-scenario runs, 0 failed checks,
no 500s). Suspected Spinel defect: values extracted from boxed/heterogeneous containers (JSON-parsed strings,
Time in a mixed Hash) are not kept alive/valid across a collection. Not yet root-caused (two Codex attempts were
stopped by the provider's content filter); recorded as an upstream candidate.

Impact: **none**. Same attributes, same values, same validation and save; `published_at` stays nil for drafts
exactly as `(Time.current if status == "published")` did.

### `app/services/article_commit.rb`

`changes["tag_list"] = tags.uniq.map { |tag| "#{tag}" }` (fresh String copies), same reason. Impact: **none**.
The update path still passes a merged Hash to `update!`; it is exercised by the gates but not by the benchmark
workload, so the same latent defect may affect it under heavy concurrent editing (open risk).

v3 acceptance: compiled production gate exit 0 (prod/production-gate-v3-1.log); Rails production gate on the same
source exit 0 (gates/v3-rails-production.log).


## v4 (final, lead)

v4 = v3 with the two v3 load workarounds **reverted** (articles_controller.rb#create and article_commit.rb are
byte-identical to v2 again) and ExportsController simplified (w21):

- The v3 crash was a Spinel code-generation bug, now fixed in the toolchain: arguments of a call on a dynamically
  typed receiver (and the result temp of a no-else `(expr if cond)`) were not registered as GC roots
  (`spinel-poly-dispatch-arg-roots.patch`, root-caused by the lead's Claude subagent c01; see
  .work/ruby-compile/spinel-spike/workers/c01-spinel-lifetime). With it, the original merged-Hash create path survives
  ~50,000 creates under the benchmark load with zero failures (lead/crash/v4a, v4b).
- `app/controllers/exports_controller.rb`: the explicit integer-serialization regex/`to_i` is removed; roundhouse patch 74
  now gives Rails' out-of-range / nonnumeric integer predicate semantics generally (huge IDs -> no match -> 404).
  The only remaining delta in this file is the direct `user_id` query (association `find_by` lowering still derives a
  nonexistent `current_user_id`) plus `param(:id)`.

v4 acceptance: compiled production gate exit 0 (prod/production-gate-v4-1.log); common reviewer probe 21/21 contract,
3/3 quality (probe/compiled-v4-common-http.json); Rails production gate exit 0 (gates/v4-rails-production.log); Rails
db:prepare, Zeitwerk, RuboCop (51 files, no offenses), 21 tests / 115 assertions (gates/v4-rails-dev).
Behavioral difference removed in v4: huge numeric export/comment IDs now return 404 as in Rails.
