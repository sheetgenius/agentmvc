# Feature: shared live article editing

This extends the RealWorld API, drafts, and exports. All existing behavior and acceptance files continue to pass. The shared Lit client in `realworld_spec/frontend/` is a read-only consumer of this contract. Prose and checks in this directory define the new behavior; where they disagree, the checks win.

## Editing links

An article has at most one active editing link. Its author can create or rotate the link with `POST /api/articles/:slug/share` using their normal `Authorization: Token` credential. Return `201` with `{ "share": { "id": string, "key": string } }`. Both strings are opaque and URL-safe; `key` has at least 128 bits of cryptographic randomness. Creating another link revokes the previous one. `DELETE /api/articles/:slug/share` revokes the active link and returns `204` (also if none is active). Non-authors receive the same visibility/ownership errors as other article mutations. Neither endpoint exposes an existing key after creation.

The server stores only a cryptographic hash of the key. The shared frontend forms a URL such as `http://localhost:5173/edit/<id>#key=<key>`. The fragment is not sent with the page request. A holder sends the key in the `X-Share-Key` HTTP header or the first WebSocket `subscribe` message. A share ID remains attached to the same article even if its title or slug changes. A revoked or unknown ID/key pair is indistinguishable and returns `404` for HTTP requests.

Anyone with the active link can read and edit **that article only**, without a user account. The capability grants no access to other articles, user data, publishing, deletion, comments, tags, or link management. It is valid for drafts and published articles. The author may still use every existing endpoint with their normal token.

## Shared JSON API

`GET /api/shares/:id/article` with `X-Share-Key` returns `200` and exactly:

```json
{"article":{"slug":"example","title":"Example","body":"Body","revision":1}}
```

`PUT /api/shares/:id/article` with `X-Share-Key` accepts exactly `{ "article": { "title": string, "body": string, "revision": integer } }` and returns the same representation. Both text fields are required. Their validations and slug changes follow the existing article update behavior. A successful update increments `revision` exactly once and atomically; two updates based on the same revision cannot both succeed. A stale revision returns `409` with `{ "errors": { "revision": ["is stale"] }, "article": <current shared article> }`. Invalid fields or types return `422` without a mutation. The share key is checked before any article data or validation errors are disclosed.

The old `PUT /api/articles/:slug` remains unchanged. The share route uses the same revision-checked update rule on a stable article identity, because changing a title may change the slug.

## Live socket

Connect to `/api/shares/:id/live` as a WebSocket. The server sends no article data or presence until it receives and validates the first client message:

```json
{"type":"subscribe","key":"<share key>"}
```

An invalid, revoked, or missing key receives `{ "type": "invalid_link" }` and a close. An unauthed socket that sends no valid subscription closes within five seconds. Neither counts toward presence or the room cap.

On admission, send exactly one initial message:

```json
{"type":"ready","article":{"slug":"example","title":"Example","body":"Body","revision":1},"presence":1}
```

Every committed edit after `ready` produces an `updated` message with the same `article` shape and a greater revision. The server may coalesce intermediate revisions under load, but must never send an older revision after a newer one. A client that reconnects receives a fresh `ready` snapshot of the latest committed article. A save racing with subscription must appear in either `ready` or a later `updated` message; it must not be lost between them. Broadcasts happen after the database commit.

Every admitted socket counts as one connected editor, including multiple tabs or browsers with the same link. Broadcast `{ "type": "presence", "count": integer }` when the count changes. Presence is advisory and in memory; it is not an identity roster or a stored article field. This step uses one backend instance.

The room admits at most **100 authorized sockets per article**. Admission is atomic. If full, the 101st valid subscriber receives `{ "type": "room_full", "limit": 100 }` and a close, without an article or presence message. Invalid subscribers never consume a slot. When an admitted socket closes, its slot is released and the remaining clients receive the new count. A retry after a slot opens can join and receives the latest snapshot.

Revocation ends every active subscription for that link with `{ "type": "revoked" }` and a close. Later GET, PUT, and subscribe attempts fail. A newly created link may access the article independently of the old one.

## Client behavior

The shared frontend has a copyable editing link, title and body fields, Save, a connection indicator, presence count, and explicit conflict and room-full states. It never uses browser-to-browser messaging for article updates. On a remote update, an untouched form adopts the new article. A form with unsaved local edits keeps its draft and base revision while showing that a newer server revision exists. Its next save receives a `409` and offers an explicit action to load the server version. Room full is a full-page state with Retry; Retry opens a new socket. The link works in another browser with no previous login.

## Checks and topology

The Hurl suite checks the shared HTTP contract and existing suites continue to run. Shared protocol tests check socket admission, ordering, presence, reconnection, revocation, and the 100-connection cap. Playwright opens independent browser contexts using the same link to check the visible behavior. Both `bin/check` and `bin/check-production` must run these shared checks. The production backend remains one container, backed by its existing PostgreSQL, with only `DATABASE_URL`, `SECRET_KEY_BASE`, and `PORT` supplied. No Redis or other service is required.
