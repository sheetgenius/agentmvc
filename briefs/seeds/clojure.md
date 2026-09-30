# Clojure brief

## Rule ownership

- Represent domain facts as immutable maps. Give each rule one owner namespace behind thin handlers, and avoid macros or generic repositories unless they remove real repetition.
- Share one locked write between author and capability edits. Recheck the capability under the article lock that rotation and revocation also take.
- Enforce invariants for every writer with database constraints in Migratus SQL migrations.
- Enqueue with `proletarian.job/enqueue!` on the `next.jdbc/with-transaction` connection. Complete only uncompleted exports, so retries cannot replace a snapshot.
- Broadcast after edits, publication, rotation, revocation and deletion. If handlers own broadcasts, every new write caller must notify too.

## Use what the framework provides

- Use Buddy with explicit `:argon2id` for passwords, and `buddy.sign.jwt/unsign` with an explicit algorithm and required claims.
- Use Reitit route data, Malli schemas and Muuntaja JSON middleware at the boundary.
- Let Integrant start and stop the pool, migrations, worker, rooms and Jetty.
- Use Ring's `:ring.websocket/listener`, and send and close through `ring.websocket`.

## Bounded queries

- Keep filtering, ordering, pagination and counts in PostgreSQL, parameterized with HoneySQL or JDBC placeholders.
- Load associations and viewer flags for a page in bounded set queries, and reuse public projections.
- Join comment authors instead of querying per comment, and leave bodies out of list selects.
- Compute favorite totals separately from favorite membership filters.

## Boundaries

- Authenticate before decoding and coercion where the contract requires it. Remap Reitit's default 400 coercion errors centrally to the contract's status and envelope.
- Reitit and Malli strip extra keys by default. On strict shared routes, use a closed schema with `:strip-extra-keys false`.
- Use `contains?` when presence matters, since missing, null, false, empty and zero can differ.
- Check that an owner-edit payload is a map after ownership checks, and parse IDs without throwing.
- Keep contract JSON field names explicit in projections. Never create keywords from arbitrary user keys.

## Production

- Build a JVM AOT uberjar that carries migrations and resources, and run it as non-root on a JRE image.
- Migrate, start workers, then serve HTTP and WebSocket in one JVM.
- Give the pool spare connections, since workers hold one while handlers run.
- Stop HTTP admission, drain workers, then close the pool.

## Known traps

- `buddy.hashers/verify` returns a truthy map even on failure, so check `:valid`. `unsign` accepts a missing `exp`, so require it where the contract does.
- Functions passed to `swap!` may run more than once. Keep sends outside atom updates and locks.
- `worker/start!` returns a boolean, so keep the worker object. Proletarian defaults to no retries, so configure bounded retries.
- next.jdbc returns qualified column keys by default. Choose result builders explicitly.
- Argon2id allocates its full memory cost for every hash, so concurrent logins can exhaust a bounded JVM heap. Bound concurrent hashing with a semaphore sized to the heap, and reserve login admission before password work.

## Source

Distilled from `one-shot-v2-clojure-expert/ENVIRONMENT.md`, `results/lanes/clojure/CODE-GUIDE.md` and `results/lanes/clojure/EXPERT-REVIEW.md`.

Draft seed for practitioner review. Not a frozen experiment input.
