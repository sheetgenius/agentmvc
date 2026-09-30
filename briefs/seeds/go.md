# Go brief

## Rule ownership

- Keep each policy and state transition in one named owner, with direct tests and an `AGENTS.md` map.
- Send author and share edits through one save that reads the row `FOR UPDATE`, applies changes, commits, then broadcasts. Express the entrances as typed inputs, not boolean modes.
- Publish with a conditional draft-to-published update. Let database constraints own invariants every writer must obey.
- Insert the export and its River job in one transaction. Keep workers idempotent and complete only pending exports.
- Own room state explicitly. Prefer article-scoped room locks, since one global mutex spanning database work serializes unrelated articles.

## Use what the framework provides

- Use x/crypto password hashing and golang-jwt with an explicitly allowed algorithm.
- Use Huma operations with typed input and output structs on chi. Map errors to Conduit's envelope centrally through Huma's `StatusError` and `NewError`.
- Pass Bun's embedded `tx.Tx` to River's `InsertTx`, and start and stop River with the HTTP server.
- Use mutexes, channels and contexts for bounded admission, cancellation and per-client send queues.
- Make login admission atomic and expiring by reserving in-flight attempts before password verification.

## Bounded queries

- Keep filtering, ordering, counting and pagination in PostgreSQL, and load relations for a whole page.
- Compose scopes as query functions. Use Bun builders for ordinary CRUD and parameterized SQL for set operations and atomic updates.
- Leave bodies out of list selects with Bun's `ExcludeColumn`. Batching once cut an anonymous list from 62 statements to 5.

## Boundaries

- Check authentication and resource authority before body validation where the contract orders it.
- Keep exact request types separate from persisted records and public outputs when permissions differ. Do not turn typed inputs back into maps.
- Presence, null and zero are distinct, and pointers alone cannot express all three. Test the wire boundary instead of trusting encoding/json zero values.
- On shared edits, validate the exact outer envelope and trailing JSON after share authorization. Leave ordinary routes unchanged.

## Production

- Compile an optimized static binary into a nonroot minimal runtime image, with SQL migrations embedded.
- Migrate, start River, then serve HTTP and WebSocket without another application service.
- On SIGTERM, finish in-flight requests before closing the pool.
- Document process-local room membership as a single-instance limit.

## Known traps

- `encoding/json` sets a `*int` to nil for both a missing key and an explicit null. Decode such fields through `json.RawMessage`, which stays empty only when the key is missing.
- An unlocked read that rewrites every field risks losing concurrent disjoint edits. Lock first or update only supplied columns.
- Closing TCP right after a write caused client protocol errors. Close sockets with a normal WebSocket closing handshake.
- Both measured builds fell back to hand-written `map[string]json.RawMessage` decoding and dropped or barely used Huma. Decode through typed Huma operations instead.

## Source

Distilled from `one-shot-v2-go-expert/ENVIRONMENT.md`, `results/lanes/go/README.md` and `results/lanes/EXPERT-REVIEW.md`.

Draft seed for practitioner review. Not a frozen experiment input.
