# Rails brief

## Rule ownership

- Name visibility and edit authority once. Direct reads show authors their own drafts, public lists and feeds exclude drafts even for the author, and the owner's draft list has its own scope.
- Converge author and keyed edits on one named, atomic content commit with explicit entrances, not a boolean mode. Pass it the author or share, and verify the share belongs to the article.
- Enforce invariants with unique indexes, foreign keys and check constraints. Keep consequential transitions out of unrelated callbacks, and map each owner in `AGENTS.md`.
- Keep the export job idempotent, and make sure a crash between export commit and enqueue cannot leave it pending. Test that path.
- Give socket wire events one owner. Admit under the room cap, send outside the room lock, and broadcast when publication increments the revision.

## Use what the framework provides

- Hash passwords with `has_secure_password` and bcrypt. Sign tokens with the `jwt` gem and an explicitly allowed algorithm.
- Queue exports through GoodJob, the PostgreSQL-backed Active Job adapter.
- Serve the raw socket with Faye WebSocket over Puma's Rack hijack, upgraded through the Rails application. The client does not speak Action Cable envelopes.
- Recheck a share key under the row lock or generation guard that orders rotation and revocation. Use parameterized SQL for compare-and-swap.

## Bounded queries

- Page in SQL first, then `includes` or `preload` associations and page-scoped follow and favorite aggregates.
- Count, filter and page the same relation. Consider `strict_loading` while building list endpoints.
- Return all comments when no page limit is requested. A default 100-comment cap can silently truncate threads.

## Boundaries

- Authenticate, then check visibility, ownership or share key, expected revision, and editable fields. Reveal no article data or field errors before the key check.
- Strong parameters protect assignment. Check exact object shape separately where the contract rejects extras.
- Params read a missing key and an explicit null as the same `nil`. Check key presence where the contract treats them differently.

## Production

- Install production gems, precompile Bootsnap caches, and boot with eager loading and YJIT. Ruby has no native compiled release here.
- Prepare the database in the entrypoint, then start Rails with GoodJob's embedded executor inside the server.
- Presence and the room cap may stay process-local under the one-instance contract. Document that limit, especially before enabling multiple Puma workers.

## Known traps

- This project's Minitest 6 setup has no `stub`. Use explicit temporary method replacement.
- Valid scalar JSON can pass a parse rescue, then raise when indexed. Accept only JSON objects as socket subscription messages.
- Collecting retired share links before taking the article lock can let a concurrent rotation revoke links without notifying their sockets. Collect them under the lock.
- Check the login throttle before password verification, and evict stale throttle and room keys from long-lived maps.

## Source

Distilled from `one-shot-v2-rails-expert/ENVIRONMENT.md`, `results/one-shot-v2-rails-expert/pilot-1/SOURCE_REVIEW.md` and `results/one-shot-v2-rails-expert/pilot-1/reference-1/README.md`.

Draft seed for practitioner review. Not a frozen experiment input.
