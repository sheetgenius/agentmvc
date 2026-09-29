# Rails expert environment

Stack: Ruby 3.3.2, Rails 8.1.3.1 API mode, Active Record, Active Job with
GoodJob 4.19, PostgreSQL 17. Serve port 4109 on `0.0.0.0`. The product-free
scaffold has only `GET /health`, a queue migration, and framework plumbing.
`Gemfile.lock` pins prepared dependencies. You may add maintained gems.

Use `harness/db.sh start 4109` for disposable PostgreSQL. Run
`harness/rails.sh run bundle exec rails db:migrate` before development.
`harness/rails.sh start|logs|stop` controls the reloading Rails server;
GoodJob runs async in that process. `harness/rails.sh run COMMAND...` is for
bounded one-shot commands, `harness/rails.sh test` for project tests, and
`harness/rails.sh build` for a production image check. The coordinator runs
Docker. Do not run a persistent server or worker through `rails.sh run`.
After a coherent edit, use a focused request against the already-running
server. Run `harness/rails.sh run bundle exec rails zeitwerk:check`,
`harness/rails.sh run bundle exec rubocop`, and project tests before the full
gates. Then run `harness/check-all.sh 4109`; stop development before
`harness/check-production.sh 4109` on a fresh database.

## Expert implementation notes

Use Rails routes, controllers, models, scopes, associations, Active Record
transactions, validations, and jobs as the normal application path. A named
domain operation is appropriate where two entrances must agree on one rule.
Keep controllers legible, and keep policy ownership discoverable in
`AGENTS.md`; avoid hiding a consequential transition in an unrelated
callback. Rails' association and `includes`/`preload` APIs can remove
handwritten joins and N+1 reads. Page in SQL before loading associated data,
and consider `strict_loading` while developing list endpoints. Count, filter,
and page the same relation; a list request must do bounded work as its page
and catalog grow. Use set-oriented, parameterized SQL when it is clearer than
an association chain or required for a compare-and-swap.

Name visibility and edit authority in one place. Direct reads allow an author
to see their own draft; public lists and feeds exclude drafts even for that
author, while the owner's draft list has its own scope. Authenticate first,
then check visibility and ownership or share capability, expected revision,
and editable fields in contract order. A keyed edit must not leak article
details or validation errors before the key is checked. Author and keyed
edits should converge on one atomic content commit with explicit entrances,
not a boolean that changes validation and response shape. Recheck a share key
under the same row lock or generation guard that orders revocation and
rotation. Use unique indexes, foreign keys, and check constraints for
invariants every writer must obey.

Use `has_secure_password` with the prepared bcrypt gem and the prepared
`jwt` gem with an explicitly allowed algorithm for the required `Token`
header. Share-key hashes and password policy each need one owner. Strong
parameters protect assignment, but check exact object shape separately
where the contract rejects extras.

The client speaks raw WebSocket JSON, not Action Cable envelopes. The
prepared Faye WebSocket gem works with Puma's Rack hijack; put the upgrade
through the Rails application, and give the wire events one owner. Admit
under a 100-member room cap, then send outside the room lock. Handle
close/revocation races and slow sockets without blocking unrelated
rooms. Presence and cap may be process-local in this one-instance contract;
document that limit, especially if enabling multiple Puma workers.

GoodJob is the PostgreSQL-backed Active Job adapter in the scaffold, running
inside the production Rails server. Use an idempotent export job and ensure
a committed export cannot remain pending after a crash between record commit
and enqueue. Prove the chosen transaction or recovery path in a focused test.
The production image receives only `DATABASE_URL`, `SECRET_KEY_BASE`, and
`PORT`; its entrypoint prepares a fresh database, then starts Rails and the
embedded job executor. Ruby has no native compiled release here. The
Dockerfile installs production gems, precompiles Bootsnap caches, and boots
with eager loading and YJIT. Verify this image against the production gate.

Write direct tests for visibility, password policy at registration and
update, stale revisions, author/shared commit equivalence, share rotation,
and room admission. Replace the scaffold `AGENTS.md` with a concise rule map
and commands. Check unfamiliar gem APIs in installed source or official docs
before implementing against them.
