# AdonisJS brief

## Rule ownership

- Name visibility, ownership, publication, stale revisions, password policy, share-key hashing and room admission once each. Keep predicates and durable invariants in PostgreSQL.
- Give author and shared-link edits distinct validated inputs feeding one content commit with an atomic revision compare-and-swap, not mode flags.
- Take the article lock for keyed edits, rotation and revocation. Recheck the active share under that lock, and notify after commit.
- Give socket events one typed owner. After each awaited lookup or write, confirm the socket is open, admitted and on an active link before sending.

## Use what the framework provides

- Use Vine, Lucid migrations and models, the hash service and the database queue. Never hand-roll password hashing or token signatures.
- Use `jose` for JWTs and `ws` for raw sockets. Adonis API tokens are opaque and Transmit is SSE.
- Resolve the JWT once into a discriminated `Viewer` union. Add Bouncer only if it delegates to the domain predicate and the owner gets clearer and smaller.
- Serialize login attempts per email across the awaited lookup and hash, and sweep expired entries.

## Bounded queries

- Keep list, feed and drafts at a fixed statement count as page and catalog grow.
- Restrict correlated aggregates to the returned page, backed by indexes. Query count alone does not bound database work.
- Use parameterized SQL where it states a projection more clearly. Do not let Lucid hydration add per-row work.

## Boundaries

- Decode each request once with compiled Vine validators via `request.validateUsing`, including the outer envelope, and infer types from them.
- Authenticate and check capability before revealing article data or field errors. Stage a revision validator before the content validator.
- Vine omits unknown properties. Check original keys where the contract rejects extras, and map Vine errors once to the contract envelope.
- Give raw rows an explicit boundary, since an `as Row` cast is an assertion, not proof. Use `satisfies` for response shapes.

## Production

- Ship compiled output with runtime dependencies, and verify jobs, migrations and generated schema load without a TypeScript loader.
- Migrate, start the worker, then serve HTTP and WebSockets. Make worker and server reap each other and honor termination signals.
- Document process-local presence, cap and login state as one-instance limits.

## Known traps

- Check whether the pinned Vine `number()` rule accepts numeric strings. Put no range rule on the revision, since a stale value of any size is a conflict, not a validation error.
- The pinned queue's dispatch API takes no Lucid transaction. Use a durable outbox or startup reconciliation with an idempotent worker, and never write its private tables.
- Bouncer's default middleware reads `ctx.auth.user`. Configure a compatible JWT guard or construct Bouncer deliberately.
- The scaffold's body-parser config trims JSON strings through `trimWhitespaces`. Turn it off for JSON so stored text round-trips exactly.
- An unhandled `error` event on a `ws` socket crashes Node, and an invalid UTF-8 frame raises one. Listen for it on every socket and terminate that socket.

## Source

Distilled from `one-shot-v2-typescript-expert/ENVIRONMENT.md`, `docs/typescript-track.md`, `results/one-shot-v2-typescript-expert/README.md` and `results/one-shot-v2-typescript-expert/expert-1/REFERENCE-NEXT.md`.

Draft seed for practitioner review. Not a frozen experiment input.
