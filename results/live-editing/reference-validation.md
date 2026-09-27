# Step 8 fixture validation

The throwaway in-memory server in [`tools/reference-live/server.mjs`](../../tools/reference-live/server.mjs) was used only to validate the frozen step-8 client and checks. It is outside all measured stack snapshots and does not satisfy the production or PostgreSQL requirements.

Run it with `node tools/reference-live/server.mjs`, then run:

```sh
BASE_URL=http://host.docker.internal:4199 spec/bin/run-hurl - features/live-editing/hurl/live-editing.hurl
spec/features/live-editing/bin/check 4199
(cd frontend && npm run build)
```

Before the fixture freeze, the first Playwright run found that Retry left the Lit page on “Opening editor…” after a successful `ready` message. The client now returns to the editor on `ready`, and the Room full test also verifies that an edit saved while the room is full appears after Retry.

Final reference validation on 2026-09-27: 18/18 new Hurl requests, direct protocol check, 3/3 Playwright tests, and Vite build passed. The frozen fixture SHA-256 is `5cf8a83f3be200afe9a90f6d3db9b11958ea7db824e13d8dfa8d7db7cdf1bf65`; individual file hashes are in [`fixture-manifest.json`](../../spec/features/live-editing/fixture-manifest.json).

The later independent review script [`tools/live-review.mjs`](../../tools/live-review.mjs) also passed against the reference. It checks unauthorized browser access, a save after revocation, repeated save/subscription races, owner edits reaching subscribers, and 105 concurrent admission attempts. It was kept outside the frozen materials and was not available to backend agents.
