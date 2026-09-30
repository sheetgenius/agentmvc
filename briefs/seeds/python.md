# Python brief

## Rule ownership

- Put consequential transitions in model methods or domain functions and reusable predicates in custom QuerySets. Do not hide an operation in an unrelated signal.
- Name visibility and edit authority once. Send author and keyed edits through one locked commit that checks revision, writes, then broadcasts after commit.
- Enforce invariants with database constraints, since `save()` does not run `full_clean()`.
- Make the export row and its Procrastinate job atomic, and keep the task idempotent. A post-commit callback alone leaves a crash window.
- Give the outgoing socket protocol one owner. Admit atomically under the room cap, then send outside the room lock.

## Use what the framework provides

- Use `make_password`, `check_password` and the Argon2 hasher, plus PyJWT with an explicitly allowed algorithm.
- Use Ninja routers, typed schemas and auth hooks, Django many-to-many fields and Channels groups. Replacing them added plumbing.
- Use Channels `AsyncJsonWebsocketConsumer` and `URLRouter` for the raw protocol.
- Keep rate-limit state per identity and correct under concurrency. Bound concurrent Argon2 checks under the memory limit.

## Bounded queries

- Load a page with `select_related`, `prefetch_related`, `Exists` and aggregates. Page before expanding many-to-many relations.
- Apply visibility, filters, ordering, count and pagination to one consistent query, and inspect the actual SQL.
- Filter `favorited` through a membership subquery so favorite counts stay global. `distinct=True` does not recover rows the join removed.
- Annotate comment authors' follow state with `Exists`, since `select_related` does not batch it. Defer bodies on lists.

## Boundaries

- Use Pydantic strict fields and `extra="forbid"` where the contract needs them. `bool` is an `int` subclass.
- Tell omission from explicit null with `model_fields_set`.
- Where capability checks precede validation, lock, authorize, then parse the envelope in the endpoint. A typed route payload validates too early.
- Check the shared outer envelope as strictly as inner fields. An extra outer field slipped through.
- Do not keep hand-written extractors beside schemas or apply arbitrary keys through `setattr`.

## Production

- Apply migrations, then supervise Uvicorn and the Procrastinate worker in one container.
- Install locked runtime dependencies in a builder, compile bytecode, drop development dependencies and run as non-root, without a recursive ownership change that adds a layer.
- Keep one Uvicorn worker until admission and delivery are shared across processes.

## Known traps

- Django does not support async transaction blocks. Enter one complete synchronous ORM transaction through `database_sync_to_async`.
- No Redis channel layer is available. Keep room state in one process and document that limit.
- Simultaneous joins broke presence. Serialize each client's ready, presence, update and revocation sends, and read membership at presence delivery.
- Give login failure counters an expiry, and reset them after a successful login.
- A cascading delete removes rows without telling anyone. Notify admitted sockets from every write that ends access, including article deletion.

## Source

Distilled from `one-shot-v2-python-expert/ENVIRONMENT.md`, `results/lanes/python/README.md` and `results/lanes/EXPERT-REVIEW.md`.

Draft seed for practitioner review. Not a frozen experiment input.
