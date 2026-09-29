# Why this Go stack

The target is a JSON API backed by PostgreSQL with jobs and a fixed raw
WebSocket client. It rewards clear product functions, relations, bounded
queries, and a short feedback loop. Go has no single framework that supplies
Rails' complete model, job and socket conventions; this lane composes focused
libraries on the standard `net/http` interface.

| Layer | Selection | Reason and practical cost |
| --- | --- | --- |
| HTTP | Huma v2.39.1 on chi v5.3.2 | Typed input/output structs own decoding, validation and API documentation. Error envelopes and authorization order need deliberate contract adaptation. |
| Persistence | Bun v1.2.18 on pgx v5.11.0 | Struct models, relation loading, and composable SQL query builders avoid a generated persistence API. Relation names and SQL expressions are strings, so focused tests still matter. |
| Migrations | Goose v3.28.0 | Versioned SQL embedded into the binary and migration locking. Schema changes are explicit reviewed files. |
| Jobs | River v0.47.0 | PostgreSQL durability, typed workers, retries, and enqueue in the same transaction as Bun writes. No Redis or separate application service. |
| Sockets | coder/websocket v1.8.15 | Standard HTTP upgrade and context-aware raw WebSocket reads/writes, matching the fixed client. The application owns rooms and wire events. |
| Auth libraries | golang-jwt v5.3.1, x/crypto v0.57.0 | Maintained token verification and password hashing implementations. No product auth scheme is scaffolded. |
| Development | Go 1.27.1, Air v1.67.4 | Native compiler, cached builds, automatic restart, gofmt, go vet and the race detector. |
| Security analysis | gosec v2.29.0, govulncheck v1.8.0 | Static application findings and reachable known vulnerabilities, alongside the shared black-box security contract. |

Ent was the strongest alternative persistence choice. It offers generated
typed queries and associations, but adds code generation and a separate
schema/migration workflow. SQLC provides excellent checked query boundaries
but requires explicit result shapes and query functions for ordinary CRUD.
Both remain useful later diagnostic lanes; the first Go entry chooses Bun's
smaller source surface for this contract. GORM is mature and concise, but Bun's
SQL-oriented composition and documented shared transactions with River make
the query and job boundaries easy to inspect.

Gin and Echo are mature HTTP choices. Huma adds typed inputs and schema
validation to avoid a handwritten binding layer. Fiber's fasthttp foundation
changes HTTP integration details; retaining `net/http` gives this lane direct
interoperability with chi, Huma and coder/websocket. Buffalo's integrated
generator and Pop model layer offer Rails-like conventions, but its broader
server-rendered application machinery brings little benefit to this fixed
JSON/socket contract. These are design judgments, not measured rankings.

## Verified upstream interfaces

- [Huma request validation](https://huma.rocks/features/request-validation/):
  `omitempty` controls presence independently of pointer types; `nullable`
  controls nulls; JSON schema tags express constraints and additional fields.
- [Huma custom errors](https://huma.rocks/features/response-errors/):
  `huma.StatusError` plus `huma.NewError` adapt a nonstandard error envelope.
- [Huma middleware](https://huma.rocks/features/middleware/): router middleware
  and Huma middleware run before handler decoding, enabling auth precedence.
- [Bun relations](https://bun.uptrace.dev/guide/relations.html): `Relation`
  loads belongs-to/has-one joins and has-many collections through declared tags.
- [River with Bun](https://riverqueue.com/docs/bun): `tx.Tx` exposes `*sql.Tx`
  for `InsertTx`; `NewWithPgxListener` shares the SQL pool and has a separate
  LISTEN connection pool for prompt worker wakeup.
- [River migrations](https://riverqueue.com/docs/migrations): `rivermigrate`
  supports a pinned `TargetVersion`; River 0.47.0's database/sql driver ships
  main migrations 1–7. Goose runs this as a nontransactional migration because
  River itself uses one transaction per migration.
- [Goose](https://github.com/pressly/goose): embedded SQL through `NewProvider`
  and PostgreSQL session locking through `WithSessionLocker`.
- [coder/websocket](https://github.com/coder/websocket): raw protocol on
  standard Go HTTP, context cancellation, and read limits.

## Fairness and accounting

Use the same shared expert one-shot prompt and contract as the existing lanes;
record the stack-specific environment as a separate frozen input. The eight
historical step prompts retain their order and feature boundaries. Do not
call the completed one-shot an eight-step run. These are new dated conditions,
not retroactive replacements for the historical framework versions.

Application Go, SQL, startup scripts and module declarations count as owned
source. Unchanged scaffold and dependency downloads are excluded using the
same scaffold comparison used by the other lanes. If an agent adds generation,
retain the generator inputs and report generated bytes/tokens separately.
