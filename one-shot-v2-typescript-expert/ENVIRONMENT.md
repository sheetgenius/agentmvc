# TypeScript expert environment

## Prepared stack and contract

Node.js 24, TypeScript 5.9, AdonisJS 7, Lucid 22, and PostgreSQL 17. Serve port
4107 on `0.0.0.0`. The product-free scaffold, lockfile, Node toolchain image,
and dependencies are prepared. The spec, client, shared prompt, measurement
rules, security checks, harness, and `.scaffold/` are read-only. Work only in
this directory. You may add maintained libraries to the app.

The client requires `Authorization: Token <JWT>` and a raw WebSocket protocol.
Adonis's first-party API tokens are opaque, and Transmit is SSE. `jose` and
`ws` are preinstalled for those protocol edges. Keep them inside an otherwise
ordinary Adonis application: routes, controllers, request validation, Lucid
migrations/models, hash service, authorization, database queue, service
provider, and compiled release. Authenticate once at each HTTP or socket
entrance. Do not hand-roll password hashing or token signatures.

## Fast loop and broker commands

- `harness/db.sh start 4107` starts disposable PostgreSQL. Run migrations with
  `harness/ts.sh run node ace migration:run --force`; Lucid regenerates
  `database/schema.ts` after migrations. It is generated code; do not edit it.
- `harness/ts.sh start|logs|stop` controls the watched development server.
  `harness/ts.sh worker-start|worker-logs|worker-stop` controls a separate
  development queue worker. The production image starts its own worker.
- `harness/ts.sh run COMMAND...` runs a **short, one-shot** command in Node 24;
  it has a three-minute limit. Never put a server, watcher, `queue:work`, or
  another persistent command through `run`. The broker kills and removes a
  timed-out command container. `harness/ts.sh build|test` have bounded limits.
- Use a focused request against the running server after a coherent edit.
  `harness/ts.sh run npm run typecheck`, `npm run lint`, and `npm test` are
  focused checks. Expand the lint and format scripts to cover every new
  production folder, including `providers/`, and run them before final gates.
  Then run
  `harness/check-all.sh 4107`, stop development and worker containers, and run
  `harness/check-production.sh 4107` against a fresh database.

## Expert implementation notes

The preceding pilot passed the acceptance gates but exposed choices that hid
TypeScript's strengths. Treat these as specific design targets, not a file
layout or mandatory abstraction scheme:

1. **One decoding boundary per request, in contract order.** Use compiled
   Vine validators with `request.validateUsing` for body and query inputs,
   including the contract's outer `user`, `article`, or `comment` object. The
   result is inferred; derive named output types from the validator when a
   service needs them. For protected updates, authenticate and check the
   capability **before** disclosing article data or field errors. The draft
   update precedence is authentication, existence/visibility, ownership,
   revision (including invalid and stale), then content-field validation.
   Shared-link updates check the key before field validation. A staged
   revision validator followed by a content validator can preserve this order.
   Verify that the pinned Vine number rule does not coerce a string revision
   into an accepted integer. Vine normally omits unknown object properties:
   where the contract requires rejection, check original keys explicitly at
   the permitted stage. Map Vine errors once to the contract's `errors`
   object and status. Keep transport validation separate from decisions.
2. **Make the caller explicit.** Model anonymous and signed-in callers as a
   discriminated `Viewer` union. Resolve the JWT once in middleware or a small
   entrance helper and give handlers a typed authenticated path; avoid `id=0`
   sentinels, `required` booleans, and non-null assertions. Bouncer abilities
   or policies are useful if they receive that verified user. Its default HTTP
   middleware reads `ctx.auth.user`, so configure a compatible JWT guard or
   construct a Bouncer instance deliberately. A pure domain predicate may be
   the simpler canonical owner where HTTP, jobs, and sockets all need it;
   Bouncer must delegate to that owner rather than duplicate the rule.
3. **Name each product decision once.** Visibility, ownership, draft
   publication, stale revisions, password policy, share-key hashing, and room
   admission need discoverable owners. The policy must distinguish direct
   reads (the owner may see a draft), public lists and feeds (drafts excluded
   even for the owner), and the owner's draft list. Keep filtering in
   PostgreSQL and put each operation's predicate next to its named policy;
   do not load collections and filter them in TypeScript. Give author and
   shared-link edits distinct validated inputs, then converge on one content
   commit with an atomic revision compare-and-swap. Avoid author/share flags.
4. **Use Lucid where its types buy clarity.** Put schema changes in migrations;
   generate schema classes and extend them for ordinary records and writes.
   Keep a short, explicit boundary for any raw query result. Use set-oriented,
   parameterized SQL when it states a list projection, aggregate, or atomic
   update more clearly than a model query. List, feed, and drafts must use a
   fixed number of statements as page size and catalog size grow. Restrict
   correlated aggregates to the returned page, backed by useful indexes;
   query count alone does not bound database work. A manual `as Row` cast is
   an assertion, not proof of the query result's shape.
5. **Use the language to expose closed cases.** Prefer discriminated unions
   for status and socket events, exhaustive `switch`/`never` checks, `satisfies`
   for protocol tables and response shapes, and small generics only when they
   remove repetitive plumbing. A brand is useful for an ID that could be
   confused with another ID. Avoid `any`, broad `Record<string, unknown>` after
   validation, positional tuples, clever compression, and assertions used to
   silence type errors. Keep controllers thin, but do not move all behavior
   into one giant service.
6. **Separate state from delivery.** Give the raw WebSocket protocol one typed
   event owner. Admit a socket under the room's cap before sending `ready`,
   send outside any lock, and preserve revision ordering and revocation. After
   an awaited lookup or write, check that the socket is still open, admitted,
   and on an active link before sending or retaining membership. Keep room
   state scoped to a room. If presence and the cap remain process-local,
   record that limit explicitly. Register the HTTP-server upgrade hook once.
7. **Prove the important changes cheaply.** Small direct tests should cover
   the password rule at registration and update, visibility for a draft owner
   and stranger, author and shared edits through the same commit, stale
   revisions, publication, and room admission. Keep test source separate from
   app-size measurements. The full gates still decide contract acceptance.

The scaffold configures Adonis's PostgreSQL queue. A worker must process
durable export jobs in the production container. The pinned queue's public
dispatch API has no shared Lucid transaction parameter, so use a durable
outbox or startup reconciliation with an idempotent worker so a crash cannot
leave a permanent pending export. Do not write into the queue's private
tables. The image receives only
`DATABASE_URL`, `SECRET_KEY_BASE`, and `PORT`; its startup migrates a fresh
database, starts the worker, and serves HTTP and WebSockets. The Dockerfile
compiles TypeScript and copies production output and runtime dependencies;
verify jobs, migrations, and generated schema load without a TypeScript
loader or development dependencies. The worker and server must reap each
other on exit and respond to container termination signals.
`AGENTS.md` should point future agents to rule owners and extension paths in
about 40 lines, with honest notes on process-local state.

Before using an unfamiliar API, inspect its installed signature or official
documentation. Adonis's [Vine validation](https://docs.adonisjs.com/guides/basics/validation),
[Bouncer authorization](https://docs.adonisjs.com/guides/auth/authorization),
[Lucid schema generation](https://lucid.adonisjs.com/docs/schema-generation),
and [database queue](https://docs.adonisjs.com/guides/digging-deeper/queues)
are useful starting points; the pinned package behavior is decisive.
