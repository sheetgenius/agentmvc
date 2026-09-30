# IHP brief

## Rule ownership

- Keep draft visibility, ownership, publication, revision expectations, pagination bounds and room admission in a small pure policy core, with IO, decoding and SQL at its edges.
- Enforce foreign keys, one active share, valid status and revision, and status-to-publication-time consistency in PostgreSQL. Keep `Application/Schema.sql` and migrations consistent.
- Do not scatter visibility, ownership, revision or editing-key checks across route branches and SQL strings. Document where a constraint backs an HTTP check.
- Prove at least one numeric invariant, such as bounded room admission or revision monotonicity, with LiquidHaskell on a module the app calls. Confirm a false refinement fails first.
- Give each live room one concurrency owner. Admit atomically under the cap and send outside the lock.

## Use what the framework provides

- Let IHP own the HTTP application, persistence, migrations, WebSocket integration and job worker.
- Use `hashPassword` and `verifyPassword` where the generated user model fits, and a maintained JWT library. Avoid handwritten crypto formats.
- Use generated records and query builders for single-record CRUD, and typed parameterized SQL for set reads, export snapshots and the revision compare-and-swap.
- Try `CanRoute` with one sum-type constructor and `Controller` action per endpoint, matched exhaustively, instead of stringly dispatch.

## Bounded queries

- Push filters, visibility, ordering, counts and pagination into the database, and inspect statements per request.
- Never filter a fetched catalog in Haskell or look up authors, favorites or tags per article.
- Passing the gates did not bound queries. Unguided lists made 21, about 64 and about 2,081 statements; a set-oriented list made one.

## Boundaries

- Decode into endpoint-specific types or a small shared decoder, with required, nonblank and unknown-field checks centralized.
- Default generic Aeson decoding does not reject unknown fields. Set `rejectUnknownFields` where extras must fail.
- Keep shared-edit input narrower than owner-edit input.
- Encode responses and socket events in a few named functions or types. Verify `requestBodyJSON`, `renderJsonWithStatusCode` and `respondAndExit` against this API's status codes.

## Production

- Start after PostgreSQL is ready, and fail startup if migration fails.
- Ship one image running migrations, server and job worker, since IHP's default worker image is separate. Keep it minimal where practical; agents' Nix images reached 4.4 GB.
- Test fresh production early. Treat presence as per-instance state and state the multi-instance limit.

## Known traps

- The pinned schema compiler rejects inline `REFERENCES`, inline `CHECK`, `TIMESTAMPTZ` and `STABLE`. Use separate `ALTER TABLE` constraints, `TIMESTAMP WITH TIME ZONE` and plain `LANGUAGE SQL`.
- Do not name an enum `JobStatus`, which collides with IHP's job type.
- A generated migration turned `SERIAL` IDs into `INT` without sequence defaults. Check inserts.
- The typed SQL quasiquoter rejected a `Maybe Text` parameter in `COALESCE`. Use generated record updates for optional fields.
- The controller context is the WAI request and vault. Do not rely on unverified `putContext` or `fromContext` examples.

## Source

Distilled from `results/one-shot-ihp/guided/expert-brief.md` and `results/one-shot-ihp/README.md`.

Draft seed for practitioner review. Not a frozen experiment input.
