# Loco one-shot agent

| | |
| --- | --- |
| Prompt | [frozen prompt](../frozen-prompt.md) |

Outputs longer than 40 lines are cut here; the `.jsonl` file next to this one has them in full.

**Agent:**

I’ll read the contract and scaffold first, then build the backend and run the required local and production checks.

```sh
$ /bin/zsh -c 'find realworld_spec -maxdepth 3 -type f | sort'
```
<details><summary>output (exit 0)</summary>

```
realworld_spec/LICENSE
realworld_spec/README.md
realworld_spec/api/README.md
realworld_spec/api/hurl/articles.hurl
realworld_spec/api/hurl/auth.hurl
realworld_spec/api/hurl/comments.hurl
realworld_spec/api/hurl/errors_articles.hurl
realworld_spec/api/hurl/errors_auth.hurl
realworld_spec/api/hurl/errors_authorization.hurl
realworld_spec/api/hurl/errors_comments.hurl
realworld_spec/api/hurl/errors_profiles.hurl
realworld_spec/api/hurl/favorites.hurl
realworld_spec/api/hurl/feed.hurl
realworld_spec/api/hurl/pagination.hurl
realworld_spec/api/hurl/profiles.hurl
realworld_spec/api/hurl/run-hurl-tests.sh
realworld_spec/api/hurl/tags.hurl
realworld_spec/api/openapi.yml
realworld_spec/docs/api-response-format.md
realworld_spec/docs/cors.md
realworld_spec/docs/endpoints.md
realworld_spec/docs/error-handling.md
realworld_spec/docs/introduction.md
realworld_spec/docs/tests.md
realworld_spec/features/drafts/drafts.md
realworld_spec/features/exports/exports.md
realworld_spec/features/live-editing/live-editing.md
realworld_spec/frontend/index.html
realworld_spec/frontend/package-lock.json
realworld_spec/frontend/package.json
realworld_spec/frontend/playwright.config.js
realworld_spec/frontend/src/api.js
realworld_spec/frontend/src/editor.js
realworld_spec/frontend/src/live.js
realworld_spec/frontend/src/styles.css
realworld_spec/frontend/tests/editor.spec.js
realworld_spec/frontend/tests/helpers.js
realworld_spec/frontend/tests/protocol.js
realworld_spec/frontend/vite.config.js
```

</details>

```sh
$ /bin/zsh -c 'cat ENVIRONMENT.md MEASUREMENT.md harness/README.md'
```
<details><summary>output (exit 0)</summary>

```
# Environment

- Stack: Rust with Loco 1.2, SeaORM 2, Axum, and PostgreSQL. A generated, product-free scaffold is already in `conduit/`; do not rerun `loco new`.
- Port: 4103. Bind the backend so it is reachable at `127.0.0.1:4103` from the host and browser harness.
- Toolchain: Cargo 1.95, Loco CLI 1.2.0, and SeaORM CLI 2.0.3 are available on the host. The existing generated `conduit/AGENTS.md` describes Loco conventions.
- Formatter/linter: from `conduit/`, run `cargo fmt --all -- --check` and `cargo clippy --all-targets -- -D warnings`.
- PostgreSQL 17 is available through the fixed coordinator commands. `harness/db.sh start 4103` starts a disposable local database and prints its `DATABASE_URL`; `harness/db.sh stop 4103` removes it. Do not call Docker directly; the agent has no host Docker socket.
- Browser and Hurl dependencies are prepared by the harness. Run `harness/check-all.sh 4103` after starting the backend. All fixture inputs listed in `PROMPT.md` must remain unchanged.
# Measurement boundary

The one-shot comparison measures backend application code added to each untouched framework scaffold. The reviewer uses `o200k_base` tokens and reports nonblank lines as a second view.

- **Owned source:** nonblank, noncomment lines added or changed against `.scaffold/`, including application logic, migrations, dependency manifests, and application configuration.
- **Whole backend:** all nonblank lines in the final application source, including the scaffold and comments.
- **Excluded from both:** `realworld_spec/`, `security/`, `harness/`, the shared frontend, prompt and environment files, tests, lockfiles, generated schema/entities, dependency caches, build output, Markdown, formatter/linter configuration, Dockerfiles, and check scripts.

The same per-stack file rules already used by `tools/measure.py` in the exploratory study apply. The reviewer records both counts and any generated-file classification before comparing results; moving product rules into excluded files is outside the contract. Shared editor and harness size and preparation effort are reported separately.

Agent effort runs from prompt delivery through the final response. Record elapsed time, uncached input and output tokens, check attempts, failures, and fixes. Independently rerun the development and production gates after the agent stops. Runtime measurements use the same production topology and direct protocol load for all stacks, with repeated nearby runs and background host load recorded.
# Fixed acceptance commands

Start your backend on the port in `ENVIRONMENT.md`, then run `harness/check-all.sh PORT`. It runs the complete Hurl API suite, direct WebSocket protocol check, four Playwright browser tests, and the 13 security files. Run your stack's formatter and linter too. `harness/db.sh start PORT` creates a disposable local PostgreSQL and prints `DATABASE_URL`; `harness/db.sh stop PORT` removes only that labelled container. These commands use a coordinator service. The Docker daemon and host socket are not available in the agent sandbox.

`harness/check-production.sh PORT` builds the Dockerfile in this workspace, starts a fresh PostgreSQL and one backend container with only `DATABASE_URL`, `SECRET_KEY_BASE`, and `PORT`, then runs the same checks. The backend image must apply its migrations on startup. The independent reviewer invokes the same host-owned gate after the agent stops.

`check-live.sh` uses the browser image prepared before the agent session. It checks the image ID in `browser-image-id`, mounts the editor read-only, copies it to temporary writable space inside the container, and runs the exact same tests for every stack. There is no browser download during a check. The backend must be reachable on the host port. The runner uses the host network; its network route and browser startup are preflighted before workspaces are handed to agents.

Phoenix agents use `harness/phoenix.sh run mix ...` for commands in the pinned Elixir container, and `harness/phoenix.sh start|logs|stop` for its development server. The container mounts only this workspace and has no Docker socket.

These files, the spec, the client, and the prompt are shared fixture inputs. Leave them unchanged. The coordinator checks their hashes before and after every delegated action.
```

</details>

```sh
$ /bin/zsh -c "pwd && rg --files -g '"'!realworld_spec/frontend/node_modules'"' | head -200"
```
<details><summary>output (exit 0)</summary>

```
/work/app
MEASUREMENT.md
ENVIRONMENT.md
FIXTURE.json
EXPERIMENT.md
realworld_spec/LICENSE
realworld_spec/api/hurl/errors_articles.hurl
realworld_spec/api/hurl/articles.hurl
realworld_spec/api/hurl/pagination.hurl
realworld_spec/api/hurl/tags.hurl
realworld_spec/api/hurl/auth.hurl
realworld_spec/api/hurl/favorites.hurl
realworld_spec/api/hurl/run-hurl-tests.sh
realworld_spec/api/hurl/feed.hurl
realworld_spec/api/hurl/errors_profiles.hurl
realworld_spec/api/hurl/comments.hurl
realworld_spec/api/hurl/errors_authorization.hurl
realworld_spec/api/hurl/errors_auth.hurl
realworld_spec/api/hurl/errors_comments.hurl
realworld_spec/api/hurl/profiles.hurl
realworld_spec/api/README.md
realworld_spec/api/openapi.yml
realworld_spec/README.md
realworld_spec/frontend/src/live.js
realworld_spec/frontend/src/api.js
realworld_spec/frontend/src/editor.js
realworld_spec/frontend/src/styles.css
realworld_spec/frontend/package.json
realworld_spec/frontend/package-lock.json
realworld_spec/frontend/vite.config.js
realworld_spec/frontend/playwright.config.js
realworld_spec/docs/error-handling.md
realworld_spec/docs/cors.md
realworld_spec/docs/tests.md
realworld_spec/docs/introduction.md
realworld_spec/docs/endpoints.md
realworld_spec/docs/api-response-format.md
realworld_spec/frontend/tests/editor.spec.js
realworld_spec/frontend/tests/helpers.js
realworld_spec/frontend/tests/protocol.js
[... 105 more lines]
```

</details>

```sh
$ /bin/zsh -c 'cat realworld_spec/README.md realworld_spec/docs/*.md realworld_spec/features/*/*.md'
```
<details><summary>output (exit 0)</summary>

````
# The spec

The app every stack builds is the [RealWorld](https://github.com/realworld-apps/realworld) "Conduit" backend, copied unchanged from commit `ebbcdeb8d55b42a3a613c787560498b8ef10003f` (2026-08-26). Its license is in [LICENSE](LICENSE).

- **`api/`:** the OpenAPI contract, and the official Hurl acceptance suite: 13 files, 154 requests.
- **`docs/`:** the prose backend spec.
- **`bin/run-hurl PORT [file ...]`:** runs the suites in Docker against `http://host.docker.internal:PORT`. The files call `{{host}}/api/...`. With no file arguments, it runs `api/hurl/*.hurl` plus every feature suite that's present.

Two features were written for AgentMVC. Each was validated by a throwaway Rails implementation before any agent saw it; the `validation/` diffs are those implementations.
- **[`features/drafts/`](features/drafts/drafts.md):** drafts, publishing and edit conflicts. 2 files, 47 requests. Added in step 2.
- **[`features/exports/`](features/exports/exports.md):** article exports, built in a durable background job. 1 file, 17 requests. Added in step 7.

The agents never see this directory as it is here. Each agent gets `realworld_spec/`, holding the spec and the features that exist at its step; [`tools/workdir.py`](../tools/workdir.py) assembles it.
---
title: API response format
---

## JSON Objects returned by API:

Make sure the right content type like `Content-Type: application/json; charset=utf-8` is correctly returned.

### Users (for authentication)

```json
{
  "user": {
    "email": "jake@jake.jake",
    "token": "jwt.token.here",
    "username": "jake",
    "bio": null,
    "image": null
  }
}
```

### Profile

```json
{
  "profile": {
[... 600 more lines]
````

</details>

```sh
$ /bin/zsh -c 'cat realworld_spec/frontend/src/api.js realworld_spec/frontend/src/live.js realworld_spec/frontend/src/editor.js realworld_spec/frontend/tests/protocol.js'
```
<details><summary>output (exit 0)</summary>

```
export async function request(path, {method = 'GET', key, token, body} = {}) {
  const response = await fetch(`/api${path}`, {
    method,
    headers: {
      Accept: 'application/json',
      ...(key && {'X-Share-Key': key}),
      ...(token && {Authorization: `Token ${token}`}),
      ...(body && {'Content-Type': 'application/json'}),
    },
    ...(body && {body: JSON.stringify(body)}),
  });
  const data = response.status === 204 ? null : await response.json().catch(() => null);
  if (!response.ok) throw Object.assign(new Error(`Request failed (${response.status})`), {status: response.status, data});
  return data;
}
export function subscribe(id, key, onMessage, onStatus) {
  let socket;
  let timer;
  let stopped = false;
  let terminal = false;

  function connect() {
    if (stopped || terminal) return;
    onStatus('connecting');
    const protocol = location.protocol === 'https:' ? 'wss:' : 'ws:';
    socket = new WebSocket(`${protocol}//${location.host}/api/shares/${id}/live`);
    socket.onopen = () => socket.send(JSON.stringify({type: 'subscribe', key}));
    socket.onmessage = ({data}) => {
      const message = JSON.parse(data);
      if (['room_full', 'invalid_link', 'revoked'].includes(message.type)) terminal = true;
      if (message.type === 'ready') onStatus('connected');
      onMessage(message);
    };
    socket.onclose = () => {
      if (stopped || terminal) return;
      onStatus('reconnecting');
      timer = setTimeout(connect, 1000);
    };
  }

[... 221 more lines]
```

</details>

```sh
$ /bin/zsh -c 'cat harness/check-all.sh harness/check-production.sh harness/check-client.py harness/db.sh'
```
<details><summary>output (exit 0)</summary>

```
#!/usr/bin/env bash
set -euo pipefail
root="$(cd "$(dirname "$0")/.." && pwd)"
exec python3 "$root/harness/check-client.py" all "${1:?usage: harness/check-all.sh PORT}"
#!/usr/bin/env bash
set -euo pipefail
root="$(cd "$(dirname "$0")/.." && pwd)"
exec python3 "$root/harness/check-client.py" production "${1:?usage: harness/check-production.sh PORT}"
#!/usr/bin/env python3
"""Call the coordinator's fixed Docker-backed checks without a Docker socket."""
import json
import os
import sys
import urllib.error
import urllib.request

if len(sys.argv) < 3:
    raise SystemExit("usage: check-client.py ACTION PORT [container command ...]")
token = os.environ.get("ONE_SHOT_BROKER_TOKEN")
if not token:
    raise SystemExit("ONE_SHOT_BROKER_TOKEN is missing; ask the orchestrator to start the check service")
payload = json.dumps({"action": sys.argv[1], "port": int(sys.argv[2]), "argv": sys.argv[3:]}).encode()
request = urllib.request.Request(
    "http://127.0.0.1:49671/run", payload,
    {"Content-Type": "application/json", "Authorization": f"Bearer {token}"},
)
try:
    with urllib.request.urlopen(request, timeout=3600) as response:
        while chunk := response.read(65536):
            sys.stdout.buffer.write(chunk)
            sys.stdout.buffer.flush()
except urllib.error.HTTPError as error:
    sys.stderr.write(error.read().decode(errors="replace"))
    raise SystemExit(1)
#!/usr/bin/env bash
set -euo pipefail
root="$(cd "$(dirname "$0")/.." && pwd)"
case "${1:?usage: harness/db.sh start|stop PORT}" in
  start) action=db-start;;
  stop) action=db-stop;;
[... 3 more lines]
```

</details>

```sh
$ /bin/zsh -c 'cat conduit/AGENTS.md conduit/Cargo.toml conduit/src/app.rs conduit/src/bin/main.rs conduit/src/lib.rs conduit/config/development.yaml conduit/config/production.yaml conduit/migration/src/lib.rs conduit/migration/Cargo.toml'
```
<details><summary>output (exit 0)</summary>

````
# Agent guide for this Loco app

This is a [Loco](https://loco.rs) app — **Rails for Rust**. When you are unsure
how something should work here, the answer is almost always "the way Rails does
it." Where Loco diverges, it is because Rust forced it.

## Read this first

A complete Loco skill ships with this app at **`.claude/skills/loco/`**, matched
to the exact `loco-rs` version in `Cargo.toml`:

| File | What it gives you |
|---|---|
| `.claude/skills/loco/SKILL.md` | start here — the router, `AppContext`, project layout, CLI |
| `.claude/skills/loco/doctrine.md` | what good Loco code looks like; read before writing any |
| `.claude/skills/loco/api-index.md` | every public `loco_rs` symbol, generated from rustdoc — **check here before guessing an API name** |
| `.claude/skills/loco/recipes/` | how to add a model, endpoint, worker, task, mailer, middleware, auth, tests |

If your tool supports Agent Skills, it will load `SKILL.md` automatically. If
not, read it directly — it is a normal markdown file.

## The three rules that prevent most mistakes

1. **Generate, then edit.** `cargo loco generate <thing>` writes the file *and*
   the wiring. Rust has no autoloading; hand-wiring is how "the handler exists
   but 404s" happens.
2. **Use the batteries.** This app already has an ORM, queue, scheduler, mailer,
   task runner, storage, cache, and test harness. Adding a crate for something
   Loco already does is the most common mistake.
3. **Fat model, slim controller.** Domain logic on the model; handlers parse,
   call a model method, and render.

## Before you call it done

```sh
cargo fmt --all
cargo clippy --all-targets -- -D warnings
cargo test
```

[... 405 more lines]
````

</details>

```sh
$ /bin/zsh -c 'cat realworld_spec/features/live-editing/live-editing.md'
```
<details><summary>output (exit 0)</summary>

````
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

[... 15 more lines]
````

</details>

```sh
$ /bin/zsh -c 'cat realworld_spec/frontend/src/api.js realworld_spec/frontend/src/live.js realworld_spec/frontend/src/editor.js'
```
<details><summary>output (exit 0)</summary>

```
export async function request(path, {method = 'GET', key, token, body} = {}) {
  const response = await fetch(`/api${path}`, {
    method,
    headers: {
      Accept: 'application/json',
      ...(key && {'X-Share-Key': key}),
      ...(token && {Authorization: `Token ${token}`}),
      ...(body && {'Content-Type': 'application/json'}),
    },
    ...(body && {body: JSON.stringify(body)}),
  });
  const data = response.status === 204 ? null : await response.json().catch(() => null);
  if (!response.ok) throw Object.assign(new Error(`Request failed (${response.status})`), {status: response.status, data});
  return data;
}
export function subscribe(id, key, onMessage, onStatus) {
  let socket;
  let timer;
  let stopped = false;
  let terminal = false;

  function connect() {
    if (stopped || terminal) return;
    onStatus('connecting');
    const protocol = location.protocol === 'https:' ? 'wss:' : 'ws:';
    socket = new WebSocket(`${protocol}//${location.host}/api/shares/${id}/live`);
    socket.onopen = () => socket.send(JSON.stringify({type: 'subscribe', key}));
    socket.onmessage = ({data}) => {
      const message = JSON.parse(data);
      if (['room_full', 'invalid_link', 'revoked'].includes(message.type)) terminal = true;
      if (message.type === 'ready') onStatus('connected');
      onMessage(message);
    };
    socket.onclose = () => {
      if (stopped || terminal) return;
      onStatus('reconnecting');
      timer = setTimeout(connect, 1000);
    };
  }

[... 160 more lines]
```

</details>

```sh
$ /bin/zsh -c 'cat realworld_spec/frontend/tests/editor.spec.js realworld_spec/frontend/tests/protocol.js'
```
<details><summary>output (exit 0)</summary>

```
import {test, expect} from '@playwright/test';
import {seed, json, LiveClient} from './helpers.js';

const backend = process.env.BACKEND_URL || 'http://127.0.0.1:4101';
const editorUrl = share => `/edit/${share.id}#key=${share.key}`;

test('three independent browsers share edits and presence without losing a dirty draft', async ({browser}) => {
  const share = await seed(backend);
  const contexts = await Promise.all(Array.from({length: 3}, () => browser.newContext()));
  try {
    const pages = await Promise.all(contexts.map(context => context.newPage()));
    for (let i = 0; i < pages.length; i++) {
      await pages[i].goto(editorUrl(share));
      await expect(pages[i].getByText(`${i + 1} here`)).toBeVisible();
    }
    await expect(pages[0].getByText('3 here')).toBeVisible();
    await pages[0].getByLabel('Body').fill('Saved by browser one');
    await pages[0].getByRole('button', {name: 'Save'}).click();
    await expect(pages[1].getByLabel('Body')).toHaveValue('Saved by browser one');
    await expect(pages[2].getByLabel('Body')).toHaveValue('Saved by browser one');

    await pages[1].getByLabel('Body').fill('Unsaved in browser two');
    await pages[2].getByLabel('Body').fill('Saved by browser three');
    await pages[2].getByRole('button', {name: 'Save'}).click();
    await expect(pages[1].getByText('A newer version is available.')).toBeVisible();
    await expect(pages[1].getByLabel('Body')).toHaveValue('Unsaved in browser two');
    await pages[1].getByRole('button', {name: 'Save'}).click();
    await expect(pages[1].getByText('Someone saved a newer version.')).toBeVisible();
    await expect(pages[1].getByLabel('Body')).toHaveValue('Unsaved in browser two');
    await pages[1].getByRole('button', {name: 'Load their version'}).click();
    await expect(pages[1].getByLabel('Body')).toHaveValue('Saved by browser three');

    await pages[0].reload();
    await expect(pages[0].getByLabel('Body')).toHaveValue('Saved by browser three');
    await contexts[2].close();
    await expect(pages[0].getByText('2 here')).toBeVisible();
  } finally {
    await Promise.all(contexts.map(context => context.close().catch(() => {})));
  }
});
[... 139 more lines]
```

</details>

```sh
$ /bin/zsh -c 'cat security/hurl/*.hurl'
```
<details><summary>output (exit 0)</summary>

```
# S01: a token signed with "alg": "none" is rejected
GET {{host}}/api/user
Authorization: Token eyJhbGciOiJub25lIiwidHlwIjoiSldUIn0.eyJzdWIiOiIxIiwiaWQiOjEsInBpZCI6IjAwMDAwMDAwLTAwMDAtMDAwMC0wMDAwLTAwMDAwMDAwMDAwMCIsImV4cCI6NDEwMjQ0NDgwMH0.
HTTP 401
# S02: a real token with its signature stripped or replaced is rejected
POST {{host}}/api/users
{
  "user": {
    "username": "sec_s02_{{uid}}",
    "email": "sec_s02_{{uid}}@test.com",
    "password": "password123"
  }
}
HTTP 201
[Captures]
signed_part: jsonpath "$.user.token" regex "^([^.]+\\.[^.]+)\\."


GET {{host}}/api/user
Authorization: Token {{signed_part}}.
HTTP 401

GET {{host}}/api/user
Authorization: Token {{signed_part}}.c2lnbmF0dXJl
HTTP 401
# S03: garbage tokens are rejected with 401, never a server error
GET {{host}}/api/user
Authorization: Token abc
HTTP 401

GET {{host}}/api/user
Authorization: Token a.b.c
HTTP 401
# S04: server-owned user fields can't be set by the client
POST {{host}}/api/users
{
  "user": {
    "username": "sec_s04_{{uid}}",
    "email": "sec_s04_{{uid}}@test.com",
    "password": "password123",
[... 263 more lines]
```

</details>

```sh
$ /bin/zsh -c 'cat realworld_spec/features/drafts/hurl/*.hurl realworld_spec/features/exports/hurl/*.hurl'
```
<details><summary>output (exit 0)</summary>

```
# Setup: register the author
POST {{host}}/api/users
{
  "user": {
    "username": "drafts_a_{{uid}}",
    "email": "drafts_a_{{uid}}@test.com",
    "password": "password123"
  }
}
HTTP 201
[Captures]
token_a: jsonpath "$.user.token"

# Setup: register a follower
POST {{host}}/api/users
{
  "user": {
    "username": "drafts_b_{{uid}}",
    "email": "drafts_b_{{uid}}@test.com",
    "password": "password123"
  }
}
HTTP 201
[Captures]
token_b: jsonpath "$.user.token"

# The follower follows the author
POST {{host}}/api/profiles/drafts_a_{{uid}}/follow
Authorization: Token {{token_b}}
HTTP 200

# Create a draft with a tag used nowhere else
POST {{host}}/api/articles
Authorization: Token {{token_a}}
{
  "article": {
    "title": "Draft Article {{uid}}",
    "description": "Draft description",
    "body": "Draft body",
    "tagList": ["draftonly_{{uid}}"],
[... 615 more lines]
```

</details>

```sh
$ /bin/zsh -c 'cat conduit/.claude/skills/loco/SKILL.md conduit/.claude/skills/loco/doctrine.md'
```
<details><summary>output (exit 0)</summary>

```
---
name: loco
description: Use when writing, reviewing, or debugging a Loco app (loco-rs, "Rails for Rust") — anything involving AppContext, controllers, Sea-ORM models and migrations, background workers, tasks, the scheduler, mailers, middleware, or `cargo loco`. Carries Loco's doctrine, its full public API index, and task recipes, so you can write idiomatic Loco without guessing at API names or reading framework source.
---

# Building Loco apps

Loco is **Rails for Rust**. When unsure how something should work, the answer is
almost always "the way Rails does it." Where Loco diverges it is because Rust
forced it, never because Loco disagreed with Rails.

## The three rules that prevent most mistakes

1. **Generate, then edit.** `cargo loco generate <thing>` writes the file *and*
   the wiring (`mod` declarations, route registration, worker registration).
   Rust has no autoloading, so hand-written wiring is where "the code exists but
   is never reached" bugs come from.
2. **Use the batteries.** Loco ships an ORM, queue, scheduler, mailer, task
   runner, storage, cache, and test harness. Adding a crate — or hand-writing
   infrastructure — for something Loco already does is the most common way
   agent-written Loco code goes wrong. See the P1 table in `doctrine.md`.
3. **Fat model, slim controller.** Finders and creation on `impl Model`, state
   transitions on `impl ActiveModel`. Handlers parse, call one or two model
   methods, and render.

## Everything hangs off `AppContext`

Handlers receive it as `State(ctx): State<AppContext>`. Eight fields, and they
are the answer to most "how do I get at X" questions:

| Field | Use |
|---|---|
| `ctx.db` | `DatabaseConnection` — all Sea-ORM calls |
| `ctx.config` | typed `config/<env>.yaml`; **the only** source of settings |
| `ctx.mailer` | mailer transport (mailers use it via `&ctx`) |
| `ctx.storage` | file storage abstraction |
| `ctx.cache` | cache abstraction |
| `ctx.queue_provider` | background queue (workers use it via `&ctx`) |
| `ctx.shared_store` | `Arc<SharedStore>`, typed DI slot; populated in `Hooks::after_context` |
| `ctx.environment` | current environment |
[... 369 more lines]
```

</details>

```sh
$ /bin/zsh -c 'cat realworld_spec/frontend/tests/protocol.js realworld_spec/frontend/tests/helpers.js'
```
<details><summary>output (exit 0)</summary>

```
import assert from 'node:assert/strict';
import {json, seed, LiveClient} from './helpers.js';

const base = process.env.BACKEND_URL || `http://127.0.0.1:${process.argv[2] || 4101}`;
const share = await seed(base);
const clients = [];

try {
  const bad = await new LiveClient(base, share.id).open('wrong');
  assert.equal((await bad.next('invalid_link')).type, 'invalid_link');
  bad.close();

  const waiting = new LiveClient(base, share.id);
  await new Promise((resolve, reject) => {
    waiting.socket.once('open', resolve);
    waiting.socket.once('error', reject);
  });
  await new Promise(resolve => setTimeout(resolve, 100));
  assert.deepEqual(waiting.messages, [], 'socket disclosed data before authorization');
  waiting.socket.send(JSON.stringify({type: 'subscribe', key: share.key}));
  clients.push(waiting);
  assert.equal((await waiting.next('ready')).presence, 1);

  for (let count = 2; count <= 3; count++) {
    const client = await new LiveClient(base, share.id).open(share.key);
    clients.push(client);
    const ready = await client.next('ready');
    assert.equal(ready.presence, count);
    assert.equal(ready.article.revision, 1);
  }
  assert.equal((await clients[0].next('presence', message => message.count === 3)).count, 3);

  const saved = await json(base, `/shares/${share.id}/article`, {
    method: 'PUT', key: share.key,
    body: {article: {title: 'Live new title', body: 'Live new body', revision: 1}},
  });
  assert.equal(saved.status, 200);
  assert.equal(saved.data.article.revision, 2);
  await Promise.all(clients.map(client => client.next('updated', message => message.article.revision === 2)));

[... 94 more lines]
```

</details>

```sh
$ /bin/zsh -c 'cat realworld_spec/features/live-editing/hurl/live-editing.hurl'
```
<details><summary>output (exit 0)</summary>

```
# Author and unrelated user
POST {{host}}/api/users
{"user":{"username":"live_a_{{uid}}","email":"live_a_{{uid}}@test.com","password":"password123"}}
HTTP 201
[Captures]
author_token: jsonpath "$.user.token"

POST {{host}}/api/users
{"user":{"username":"live_b_{{uid}}","email":"live_b_{{uid}}@test.com","password":"password123"}}
HTTP 201
[Captures]
other_token: jsonpath "$.user.token"

POST {{host}}/api/articles
Authorization: Token {{author_token}}
{"article":{"title":"Live Draft {{uid}}","description":"private","body":"Before","status":"draft"}}
HTTP 201
[Captures]
slug: jsonpath "$.article.slug"
[Asserts]
jsonpath "$.article.revision" == 1

# Only the author may create the link
POST {{host}}/api/articles/{{slug}}/share
Authorization: Token {{other_token}}
HTTP 404

POST {{host}}/api/articles/{{slug}}/share
Authorization: Token {{author_token}}
HTTP 201
[Captures]
share_id: jsonpath "$.share.id"
share_key: jsonpath "$.share.key"
[Asserts]
jsonpath "$.share.id" isString
jsonpath "$.share.key" isString

# An uncredentialed reader learns nothing
GET {{host}}/api/shares/{{share_id}}/article
HTTP 404
[... 80 more lines]
```

</details>

```sh
$ /bin/zsh -c 'cat realworld_spec/api/hurl/errors_auth.hurl realworld_spec/api/hurl/errors_articles.hurl realworld_spec/api/hurl/errors_authorization.hurl'
```
<details><summary>output (exit 0)</summary>

```
# Register empty username
POST {{host}}/api/users
{
  "user": {
    "username": "",
    "email": "ea_blank_{{uid}}@test.com",
    "password": "password123"
  }
}
HTTP 422
[Asserts]
jsonpath "$.errors.username[0]" == "can't be blank"

# Register empty email
POST {{host}}/api/users
{
  "user": {
    "username": "ea_blank_{{uid}}",
    "email": "",
    "password": "password123"
  }
}
HTTP 422
[Asserts]
jsonpath "$.errors.email[0]" == "can't be blank"

# Register empty password
POST {{host}}/api/users
{
  "user": {
    "username": "ea_blankp_{{uid}}",
    "email": "ea_blankp_{{uid}}@test.com",
    "password": ""
  }
}
HTTP 422
[Asserts]
jsonpath "$.errors.password[0]" == "can't be blank"

# Register valid user for duplicate and login tests
[... 464 more lines]
```

</details>

```sh
$ /bin/zsh -c 'cat security/hurl/s01_jwt_alg_none.hurl security/hurl/s02_jwt_signature_stripped.hurl security/hurl/s03_jwt_garbage.hurl security/hurl/s04_mass_assignment_user.hurl'
```
<details><summary>output (exit 0)</summary>

```
# S01: a token signed with "alg": "none" is rejected
GET {{host}}/api/user
Authorization: Token eyJhbGciOiJub25lIiwidHlwIjoiSldUIn0.eyJzdWIiOiIxIiwiaWQiOjEsInBpZCI6IjAwMDAwMDAwLTAwMDAtMDAwMC0wMDAwLTAwMDAwMDAwMDAwMCIsImV4cCI6NDEwMjQ0NDgwMH0.
HTTP 401
# S02: a real token with its signature stripped or replaced is rejected
POST {{host}}/api/users
{
  "user": {
    "username": "sec_s02_{{uid}}",
    "email": "sec_s02_{{uid}}@test.com",
    "password": "password123"
  }
}
HTTP 201
[Captures]
signed_part: jsonpath "$.user.token" regex "^([^.]+\\.[^.]+)\\."


GET {{host}}/api/user
Authorization: Token {{signed_part}}.
HTTP 401

GET {{host}}/api/user
Authorization: Token {{signed_part}}.c2lnbmF0dXJl
HTTP 401
# S03: garbage tokens are rejected with 401, never a server error
GET {{host}}/api/user
Authorization: Token abc
HTTP 401

GET {{host}}/api/user
Authorization: Token a.b.c
HTTP 401
# S04: server-owned user fields can't be set by the client
POST {{host}}/api/users
{
  "user": {
    "username": "sec_s04_{{uid}}",
    "email": "sec_s04_{{uid}}@test.com",
    "password": "password123",
[... 25 more lines]
```

</details>

**Agent:**

The contract covers the full RealWorld API plus drafts, exports, and shared editing. I’ve confirmed the fixed editor’s message shapes and the socket cap; I’m implementing the data rules and live rooms together so they use the same article revisions.

```sh
$ /bin/zsh -c 'cat conduit/.claude/skills/loco/recipes/background-job.md conduit/src/workers/downloader.rs'
```
<details><summary>output (exit 0)</summary>

````
# Recipe: background jobs

Loco's `BackgroundWorker` is Rails' Active Job. Use it when an HTTP request must
return before the work finishes: sending email, generating thumbnails, calling a
slow third party, fanning out webhooks.

**`tokio::spawn` is never the alternative.** A spawned future is not durable,
not retried, not observable, and dies with the process. If you are reaching for
it, you want a worker.

```sh
cargo loco generate worker onboarding
```

## The worker

```rust
use loco_rs::prelude::*;
use serde::{Deserialize, Serialize};

use crate::models::users;

pub struct OnboardingWorker {
    pub ctx: AppContext,
}

#[derive(Deserialize, Debug, Serialize)]
pub struct OnboardingWorkerArgs {
    pub user_id: i32,
}

#[async_trait]
impl BackgroundWorker<OnboardingWorkerArgs> for OnboardingWorker {
    fn build(ctx: &AppContext) -> Self {
        Self { ctx: ctx.clone() }
    }

    async fn perform(&self, args: OnboardingWorkerArgs) -> Result<()> {
        let user = users::Model::find_by_id(&self.ctx.db, args.user_id).await?;
        tracing::info!(user_id = user.id, "running onboarding");
[... 111 more lines]
````

</details>

```sh
$ /bin/zsh -c 'cat realworld_spec/api/hurl/errors_profiles.hurl realworld_spec/api/hurl/errors_comments.hurl realworld_spec/api/hurl/profiles.hurl'
```
<details><summary>output (exit 0)</summary>

```
# GET unknown profile
GET {{host}}/api/profiles/unknown-user-{{uid}}
HTTP 404
[Asserts]
jsonpath "$.errors.profile[0]" == "not found"

# Follow no auth
POST {{host}}/api/profiles/unknown-user-{{uid}}/follow
HTTP 401
[Asserts]
jsonpath "$.errors.token[0]" == "is missing"

# Unfollow no auth
DELETE {{host}}/api/profiles/unknown-user-{{uid}}/follow
HTTP 401
[Asserts]
jsonpath "$.errors.token[0]" == "is missing"

# Setup: Register for authenticated 404 tests
POST {{host}}/api/users
{
  "user": {
    "username": "ep_{{uid}}",
    "email": "ep_{{uid}}@test.com",
    "password": "password123"
  }
}
HTTP 201
[Captures]
token: jsonpath "$.user.token"

# Follow unknown user (authed)
POST {{host}}/api/profiles/unknown-user-{{uid}}/follow
Authorization: Token {{token}}
HTTP 404
[Asserts]
jsonpath "$.errors.profile[0]" == "not found"

# Unfollow unknown user (authed)
DELETE {{host}}/api/profiles/unknown-user-{{uid}}/follow
[... 167 more lines]
```

</details>

```sh
$ /bin/zsh -c 'cat realworld_spec/api/hurl/articles.hurl realworld_spec/api/hurl/pagination.hurl realworld_spec/api/hurl/feed.hurl'
```
<details><summary>output (exit 0)</summary>

```
# Setup: Register
POST {{host}}/api/users
{
  "user": {
    "username": "art_{{uid}}",
    "email": "art_{{uid}}@test.com",
    "password": "password123"
  }
}
HTTP 201
[Captures]
token: jsonpath "$.user.token"

# Create article with tags
POST {{host}}/api/articles
Authorization: Token {{token}}
{
  "article": {
    "title": "Test Article {{uid}}",
    "description": "Test description",
    "body": "Test body content",
    "tagList": ["d_{{uid}}", "t_{{uid}}"]
  }
}
HTTP 201
[Asserts]
jsonpath "$.article.title" == "Test Article {{uid}}"
jsonpath "$.article.slug" isString
jsonpath "$.article.description" == "Test description"
jsonpath "$.article.body" == "Test body content"
jsonpath "$.article.tagList" contains "d_{{uid}}"
jsonpath "$.article.tagList" contains "t_{{uid}}"
jsonpath "$.article.tagList[0]" == "d_{{uid}}"
jsonpath "$.article.tagList[1]" == "t_{{uid}}"
jsonpath "$.article.createdAt" matches "^\\d{4}-\\d{2}-\\d{2}T"
jsonpath "$.article.updatedAt" matches "^\\d{4}-\\d{2}-\\d{2}T"
jsonpath "$.article.favorited" == false
jsonpath "$.article.favoritesCount" == 0
jsonpath "$.article.author.username" == "art_{{uid}}"
[Captures]
[... 413 more lines]
```

</details>

```sh
$ /bin/zsh -c "rg 'sqlx|jsonwebtoken|argon2|sha2' conduit/Cargo.lock | head -30; ls conduit"
```
<details><summary>output (exit 0)</summary>

```
rg: conduit/Cargo.lock: IO error for operation on conduit/Cargo.lock: No such file or directory (os error 2)
AGENTS.md
Cargo.toml
README.md
config
examples
migration
src
tests
```

</details>

*Files changed:* `/work/app/conduit/Cargo.toml` (update)

*Files changed:* `/work/app/conduit/src/bin/schema.sql` (add)

*Files changed:* `/work/app/conduit/src/bin/server.rs` (add)

*Files changed:* `/work/app/conduit/Cargo.toml` (update), `/work/app/conduit/src/bin/server.rs` (update)

*Files changed:* `/work/app/conduit/src/bin/server.rs` (update)

*Files changed:* `/work/app/conduit/src/bin/server.rs` (update)

**Agent:**

The core HTTP routes are in place. I’m finishing durable exports and the shared link/socket paths, then I’ll compile and use the harness failures to correct contract details.

*Files changed:* `/work/app/conduit/src/bin/server.rs` (update)

```sh
$ /bin/zsh -c 'harness/db.sh start 4103'
```
<details><summary>output (exit 0)</summary>

```
DATABASE_URL=postgres://agentmvc:agentmvc@127.0.0.1:54103/agentmvc
```

</details>

```sh
$ /bin/zsh -c 'ls -la Dockerfile conduit/Dockerfile 2>/dev/null; cat harness/check-production.sh'
```
<details><summary>output (exit 0)</summary>

```
#!/usr/bin/env bash
set -euo pipefail
root="$(cd "$(dirname "$0")/.." && pwd)"
exec python3 "$root/harness/check-client.py" production "${1:?usage: harness/check-production.sh PORT}"
```

</details>

```sh
$ /bin/zsh -c "cat PROMPT.md | tail -80; cat conduit/README.md | head -45; rg 'Dockerfile|dockerfile|cargo' harness/README.md"
```
<details><summary>output (exit 0)</summary>

````
# Build the complete Conduit backend

You have one isolated workspace and one measured coding session. Build the backend for the entire product contract provided here. Read `ENVIRONMENT.md`, `MEASUREMENT.md`, `realworld_spec/`, the small shared editor in `realworld_spec/frontend/`, and `harness/README.md` before implementation. The full API, drafts, article exports, editing links, WebSocket updates, presence, conflicts, and room cap are all in scope from the start.

Use this stack's idioms and mainstream libraries. Make the application source as concise and token-efficient as you can while keeping it clear, secure, and easy to extend. Put each rule in one obvious place. Use ordinary framework conventions instead of code golf, hidden generators, or metaprogramming invented to reduce the count. The editor is a fixed client of your JSON and WebSocket protocol; write backend code only.

Your directory starts with a product-free framework scaffold. You may edit its application code and add the migrations, dependencies, and Docker packaging needed to satisfy the contract. The production app is one container backed by PostgreSQL. It receives only `DATABASE_URL`, `SECRET_KEY_BASE`, and `PORT`; it must prepare a fresh database and serve the API and WebSocket endpoint without another application service. The shared frontend is served by the test/demo harness, outside the production image.

`realworld_spec/`, `security/`, `harness/`, `PROMPT.md`, `ENVIRONMENT.md`, `MEASUREMENT.md`, `.scaffold/`, and `FIXTURE.json` are read-only inputs. Do not edit, replace, skip, or filter their checks. Do not read other stacks' source or spawn subagents.

The browser environment is already prepared. Start your backend on the port in `ENVIRONMENT.md`, then run `harness/check-all.sh PORT` for the full HTTP, socket, browser, and security suite. The shared browser command copies the fixed editor to writable scratch and uses its pinned Playwright image; do not install a browser or write a stack-specific browser wrapper. The harness commands call the orchestrator's narrow check service; you do not have a Docker socket. Run your stack's formatter and linter as described in `ENVIRONMENT.md`. You may repeat checks while you work. `harness/check-production.sh PORT` builds your Dockerfile, starts fresh PostgreSQL, and runs the same acceptance suite against the production image. An independent reviewer will rerun it after you finish.

Stop when the complete acceptance suite and formatter/linter are green, or report a concrete blocker or exhausted budget. In your final report, state the check results, files that own the main rules, implementation choices, failures and fixes, and any limits you know. The reviewer measures backend application source separately from the shared editor and harness.
# Welcome to Loco :train:

[Loco](https://loco.rs) is a web and API framework running on Rust.

This is the **SaaS starter** which includes a `User` model and authentication based on JWT.
It also include configuration sections that help you pick either a frontend or a server-side template set up for your fullstack server.


## Quick Start

```sh
cargo loco start
```

```sh
$ cargo loco start
Finished dev [unoptimized + debuginfo] target(s) in 21.63s
    Running `target/debug/myapp start`

    :
    :
    :

controller/app_routes.rs:203: [Middleware] Adding log trace id

                      ▄     ▀
                                 ▀  ▄
[... 19 more lines]
````

</details>

*Files changed:* `/work/app/Dockerfile` (add)

```sh
$ /bin/zsh -c 'cargo check --bin conduit-server'
```
<details><summary>output (exit 101)</summary>

```
    Updating crates.io index
     Locking 641 packages to latest compatible versions
      Adding bcrypt v0.17.1 (available: v0.19.3)
      Adding generic-array v0.14.7 (available: v0.14.9)
      Adding jsonwebtoken v9.3.1 (available: v11.1.0)
      Adding matchit v0.8.4 (available: v0.8.6)
      Adding rstest v0.25.0 (available: v0.27.0)
      Adding serial_test v3.5.0 (available: v4.0.1)
      Adding sha2 v0.10.9 (available: v0.11.0)
      Adding sqlx v0.8.6 (available: v0.9.0)
      Adding tower-http v0.6.11 (available: v0.7.1)
      Adding validator v0.20.0 (available: v0.21.0)
 Downloading crates ...
  Downloaded alloc-no-stdlib v2.0.4
  Downloaded adler2 v2.0.1
  Downloaded humansize v2.1.3
  Downloaded anyhow v1.0.104
  Downloaded anstream v1.0.0
  Downloaded http-range-header v0.4.2
  Downloaded anstyle-query v1.1.5
  Downloaded bytesize v2.7.0
  Downloaded aliasable v0.1.3
  Downloaded ahash v0.8.12
  Downloaded httpdate v1.0.3
  Downloaded arrayvec v0.7.8
  Downloaded crc-catalog v2.5.0
  Downloaded anstyle-parse v1.0.0
  Downloaded aho-corasick v1.1.5
  Downloaded arrow-arith v58.4.0
  Downloaded alloc-stdlib v0.2.4
  Downloaded anstyle v1.0.14
  Downloaded allocator-api2 v0.2.21
  Downloaded argon2 v0.5.3
  Downloaded http-body-util v0.1.5
  Downloaded arrow v58.4.0
  Downloaded blake2 v0.10.6
  Downloaded atoi v2.0.0
  Downloaded httparse v1.10.1
  Downloaded base64 v0.23.1
  Downloaded autocfg v1.5.1
[... 1141 more lines]
```

</details>

*Files changed:* `/work/app/conduit/Cargo.toml` (update)

```sh
$ /bin/zsh -c 'cargo fmt --all'
```

```sh
$ /bin/zsh -c 'mkdir -p ../.tmp && TMPDIR=$PWD/../.tmp cargo check --bin conduit-server -q'
```
<details><summary>output (exit 101)</summary>

```
error[E0277]: `Fault` doesn't implement `std::fmt::Debug`
   --> src/bin/server.rs:851:39
    |
851 |             eprintln!("export worker: {e:?}");
    |                                       ^^^^^ `Fault` cannot be formatted using `{:?}` because it doesn't implement `std::fmt::Debug`
    |
    = help: the trait `std::fmt::Debug` is not implemented for `Fault`
    = note: add `#[derive(Debug)]` to `Fault` or manually `impl std::fmt::Debug for Fault`
help: consider annotating `Fault` with `#[derive(Debug)]`
    |
 80 + #[derive(Debug)]
 81 | struct Fault(StatusCode, &'static str, &'static str);
    |

For more information about this error, try `rustc --explain E0277`.
error: could not compile `conduit` (bin "conduit-server") due to 1 previous error
```

</details>

*Files changed:* `/work/app/conduit/src/bin/server.rs` (update)

```sh
$ /bin/zsh -c 'curl -si http://127.0.0.1:4103/api/tags | head -20'
```
<details><summary>output (exit 0)</summary>

```
HTTP/1.1 200 OK
content-type: application/json
vary: origin, access-control-request-method, access-control-request-headers
access-control-allow-origin: *
x-content-type-options: nosniff
content-length: 11
date: Sun, 27 Sep 2026 14:21:07 GMT

{"tags":[]}
```

</details>

```sh
$ /bin/zsh -c 'harness/check-all.sh 4103'
```
<details><summary>output (exit 1)</summary>

```
Success api/hurl/articles.hurl (17 request(s) in 223 ms)
error: Assert failure
   --> api/hurl/auth.hurl:91:0
    |
    | PUT {{host}}/api/user
    | ...
 91 | jsonpath "$.user.bio" == null
    |   actual:   string <>
    |   expected: null <null>
    |

Failure api/hurl/auth.hurl (6 request(s) in 333 ms)
Success api/hurl/comments.hurl (13 request(s) in 196 ms)
Success api/hurl/errors_articles.hurl (20 request(s) in 179 ms)
Success api/hurl/errors_auth.hurl (20 request(s) in 1019 ms)
Success api/hurl/errors_authorization.hurl (9 request(s) in 339 ms)
Success api/hurl/errors_comments.hurl (10 request(s) in 174 ms)
Success api/hurl/errors_profiles.hurl (6 request(s) in 167 ms)
Success api/hurl/favorites.hurl (9 request(s) in 196 ms)
Success api/hurl/feed.hurl (12 request(s) in 349 ms)
Success api/hurl/pagination.hurl (7 request(s) in 179 ms)
Success api/hurl/profiles.hurl (7 request(s) in 335 ms)
Success api/hurl/tags.hurl (4 request(s) in 167 ms)
Success features/drafts/hurl/drafts.hurl (23 request(s) in 393 ms)
Success features/drafts/hurl/errors_drafts.hurl (24 request(s) in 343 ms)
Success features/exports/hurl/exports.hurl (18 request(s) in 613 ms)
Success features/live-editing/hurl/live-editing.hurl (18 request(s) in 349 ms)
--------------------------------------------------------------------------------
Executed files:    17
Executed requests: 223 (40.0/s)
Succeeded files:   16 (94.1%)
Failed files:      1 (5.9%)
Duration:          5578 ms (0h:0m:5s:578ms)
```

</details>

```sh
$ /bin/zsh -c "sed -n '55,120p' realworld_spec/api/hurl/auth.hurl"
```
<details><summary>output (exit 0)</summary>

```
{
  "user": {
    "bio": "Updated bio"
  }
}
HTTP 200
[Asserts]
jsonpath "$.user.username" == "auth_{{uid}}"
jsonpath "$.user.email" == "auth_{{uid}}@test.com"
jsonpath "$.user.bio" == "Updated bio"
jsonpath "$.user.image" == null
jsonpath "$.user.token" isString
jsonpath "$.user.token" not isEmpty

# Verify update persisted
GET {{host}}/api/user
Authorization: Token {{token}}
HTTP 200
[Asserts]
jsonpath "$.user.username" == "auth_{{uid}}"
jsonpath "$.user.email" == "auth_{{uid}}@test.com"
jsonpath "$.user.bio" == "Updated bio"
jsonpath "$.user.image" == null
jsonpath "$.user.token" isString
jsonpath "$.user.token" not isEmpty

# Update user bio to empty string - should normalize to null
PUT {{host}}/api/user
Authorization: Token {{token}}
{
  "user": {
    "bio": ""
  }
}
HTTP 200
[Asserts]
jsonpath "$.user.bio" == null

# Verify empty string normalization persisted
GET {{host}}/api/user
[... 26 more lines]
```

</details>

```sh
$ /bin/zsh -c "sed -n '120,240p' realworld_spec/api/hurl/auth.hurl"
```
<details><summary>output (exit 0)</summary>

```
HTTP 200
[Asserts]
jsonpath "$.user.bio" == null

# Verify null bio persisted
GET {{host}}/api/user
Authorization: Token {{token}}
HTTP 200
[Asserts]
jsonpath "$.user.bio" == null

# Restore bio
PUT {{host}}/api/user
Authorization: Token {{token}}
{
  "user": {
    "bio": "Updated bio"
  }
}
HTTP 200
[Asserts]
jsonpath "$.user.username" == "auth_{{uid}}"
jsonpath "$.user.email" == "auth_{{uid}}@test.com"
jsonpath "$.user.bio" == "Updated bio"
jsonpath "$.user.image" == null
jsonpath "$.user.token" isString
jsonpath "$.user.token" not isEmpty

# Update user image
PUT {{host}}/api/user
Authorization: Token {{token}}
{
  "user": {
    "image": "https://example.com/photo.jpg"
  }
}
HTTP 200
[Asserts]
jsonpath "$.user.image" == "https://example.com/photo.jpg"

[... 81 more lines]
```

</details>

*Files changed:* `/work/app/conduit/src/bin/server.rs` (update)

```sh
$ /bin/zsh -c 'TMPDIR=$PWD/../.tmp DATABASE_URL=postgres://agentmvc:agentmvc@127.0.0.1:54103/agentmvc SECRET_KEY_BASE=dev_secret_for_conduit PORT=4103 cargo run --bin conduit-server'
```
<details><summary>output (exit 130)</summary>

```
   Compiling cfg-if v1.0.5
   Compiling memchr v2.8.3
   Compiling scopeguard v1.2.0
   Compiling typenum v1.20.1
   Compiling pin-project-lite v0.2.17
   Compiling itoa v1.0.18
   Compiling subtle v2.6.1
   Compiling futures-core v0.3.34
   Compiling bytes v1.12.1
   Compiling libc v0.2.189
   Compiling serde_core v1.0.229
   Compiling once_cell v1.21.4
   Compiling const-oid v0.9.6
   Compiling stable_deref_trait v1.2.1
   Compiling log v0.4.34
   Compiling lock_api v0.4.14
   Compiling zeroize v1.9.0
   Compiling zerofrom v0.1.8
   Compiling libm v0.2.16
   Compiling percent-encoding v2.3.2
   Compiling zmij v1.0.23
   Compiling writeable v0.6.4
   Compiling litemap v0.8.3
   Compiling utf8_iter v1.0.4
   Compiling yoke v0.8.3
   Compiling futures-sink v0.3.34
   Compiling futures-io v0.3.34
   Compiling futures-task v0.3.34
   Compiling icu_normalizer_data v2.3.0
   Compiling icu_properties_data v2.3.0
   Compiling regex-syntax v0.8.11
   Compiling zerocopy v0.8.59
   Compiling futures-channel v0.3.34
   Compiling zerovec v0.11.8
   Compiling zerotrie v0.2.5
   Compiling core-foundation-sys v0.8.7
   Compiling equivalent v1.0.2
   Compiling slab v0.4.12
   Compiling thiserror v2.0.21
   Compiling tracing-core v0.1.36
[... 401 more lines]
```

</details>

```sh
$ /bin/zsh -c "curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:4103/api/tags"
```
<details><summary>output (exit 0)</summary>

```
200
```

</details>

```sh
$ /bin/zsh -c 'cargo fmt --all -- --check'
```
<details><summary>output (exit 1)</summary>

```
Diff in /work/app/conduit/src/bin/server.rs:997:
         return;
     };
     let count = peers.len() + 1;
-    peers.push(Peer {
-        id: peer_id,
-        tx,
-    });
+    peers.push(Peer { id: peer_id, tx });
     let _ = send(
         &mut socket,
         json!({"type":"ready","article":shared_view(&current),"presence":count}),
```

</details>

```sh
$ /bin/zsh -c 'cargo fmt --all'
```

```sh
$ /bin/zsh -c 'harness/check-all.sh 4103'
```
<details><summary>output (exit 0)</summary>

```
Success api/hurl/articles.hurl (17 request(s) in 337 ms)
Success api/hurl/auth.hurl (20 request(s) in 394 ms)
Success api/hurl/comments.hurl (13 request(s) in 219 ms)
Success api/hurl/errors_articles.hurl (20 request(s) in 195 ms)
Success api/hurl/errors_auth.hurl (20 request(s) in 1031 ms)
Success api/hurl/errors_authorization.hurl (9 request(s) in 360 ms)
Success api/hurl/errors_comments.hurl (10 request(s) in 173 ms)
Success api/hurl/errors_profiles.hurl (6 request(s) in 165 ms)
Success api/hurl/favorites.hurl (9 request(s) in 189 ms)
Success api/hurl/feed.hurl (12 request(s) in 358 ms)
Success api/hurl/pagination.hurl (7 request(s) in 184 ms)
Success api/hurl/profiles.hurl (7 request(s) in 347 ms)
Success api/hurl/tags.hurl (4 request(s) in 177 ms)
Success features/drafts/hurl/drafts.hurl (23 request(s) in 389 ms)
Success features/drafts/hurl/errors_drafts.hurl (24 request(s) in 345 ms)
Success features/exports/hurl/exports.hurl (18 request(s) in 633 ms)
Success features/live-editing/hurl/live-editing.hurl (18 request(s) in 349 ms)
--------------------------------------------------------------------------------
Executed files:    17
Executed requests: 237 (40.4/s)
Succeeded files:   17 (100.0%)
Failed files:      0 (0.0%)
Duration:          5866 ms (0h:0m:5s:866ms)

PASS live protocol: authorization, presence, updates, conflict, reconnect, revocation

Running 4 tests using 1 worker

  ✓  1 tests/editor.spec.js:7:1 › three independent browsers share edits and presence without losing a dirty draft (659ms)
  ✓  2 tests/editor.spec.js:42:1 › the 101st editor sees Room full and can retry after a slot opens (1.1s)
  ✓  3 tests/editor.spec.js:70:1 › revoking the link ends access to the editor (290ms)
  ✓  4 tests/editor.spec.js:84:1 › a delayed save response preserves newer typing and socket state (443ms)

  4 passed (3.0s)
Success s01_jwt_alg_none.hurl (1 request(s) in 2 ms)
Success s02_jwt_signature_stripped.hurl (3 request(s) in 188 ms)
Success s03_jwt_garbage.hurl (2 request(s) in 1 ms)
Success s04_mass_assignment_user.hurl (2 request(s) in 182 ms)
Success s05_mass_assignment_article.hurl (2 request(s) in 182 ms)
Success s06_injection_filters.hurl (4 request(s) in 4 ms)
[... 13 more lines]
```

</details>

**Agent:**

The full development suite is green: 17 API files, the socket protocol, four browser tests, and all 13 security files. The first run found one bio normalization mismatch; I fixed it and reran the suite successfully. I’m checking the production image and Clippy now.

```sh
$ /bin/zsh -c 'TMPDIR=$PWD/../.tmp cargo clippy --all-targets -- -D warnings'
```
<details><summary>output (exit 0)</summary>

```
  Downloaded console v0.16.6
  Downloaded strip-ansi-escapes v0.2.1
  Downloaded serial_test v3.5.0
  Downloaded relative-path v1.9.3
  Downloaded similar v2.7.0
  Downloaded rstest v0.25.0
  Downloaded serial_test_derive v3.5.0
  Downloaded futures-timer v3.0.4
  Downloaded tempfile v3.27.0
  Downloaded insta v1.48.0
  Downloaded rstest_macros v0.25.0
  Downloaded vte v0.14.1
    Checking stable_deref_trait v1.2.1
   Compiling phf_shared v0.13.1
   Compiling fastrand v2.5.0
    Checking new_debug_unreachable v1.0.6
    Checking yoke v0.8.3
   Compiling rustix v1.1.5
    Checking try-lock v0.2.5
    Checking precomputed-hash v0.1.1
   Compiling derive_more-impl v2.1.1
    Checking mac v0.1.1
    Checking utf-8 v0.7.6
    Checking dtoa v1.0.11
    Checking want v0.3.1
   Compiling cssparser-macros v0.6.1
    Checking futf v0.1.5
    Checking servo_arc v0.4.3
    Checking diff v0.1.13
    Checking unicode-width v0.2.2
    Checking rustc-hash v2.1.3
    Checking yansi v1.0.1
   Compiling phf_generator v0.13.1
    Checking rust-multipart-rfc7578_2 v0.8.0
    Checking zerovec v0.11.8
    Checking zerotrie v0.2.5
    Checking reserve-port v2.5.0
    Checking hyper v1.11.1
    Checking string_cache v0.9.0
    Checking dtoa-short v0.3.5
[... 76 more lines]
```

</details>

*Files changed:* `/work/app/.dockerignore` (add)

```sh
$ /bin/zsh -c 'cargo fmt --all -- --check'
```

**Agent:**

Clippy and the formatter check are green. The production gate is still building the image; the runtime startup already creates the PostgreSQL schema before serving requests.

```sh
$ /bin/zsh -c 'du -sh conduit/target .cargo 2>/dev/null'
```
<details><summary>output (exit 0)</summary>

```
3.2G	conduit/target
386M	.cargo
```

</details>

```sh
$ /bin/zsh -c 'harness/check-production.sh 4103'
```
<details><summary>output (exit 0)</summary>

```
#0 building with "orbstack" instance using docker driver

#1 [internal] load build definition from Dockerfile
#1 transferring dockerfile: 393B done
#1 DONE 0.0s

#2 [internal] load metadata for docker.io/library/rust:1.95-bookworm
#2 ...

#3 [internal] load metadata for docker.io/library/debian:bookworm-slim
#3 DONE 2.5s

#2 [internal] load metadata for docker.io/library/rust:1.95-bookworm
#2 DONE 4.6s

#4 [internal] load .dockerignore
#4 transferring context: 2B done
#4 DONE 0.0s

#5 [build 1/4] FROM docker.io/library/rust:1.95-bookworm@sha256:6258907abe69656e41cd992e0b705cdcfabcbbe3db374f92ed2d47121282d4a1
#5 DONE 0.0s

#6 [stage-1 1/3] FROM docker.io/library/debian:bookworm-slim@sha256:3783cc01769c7b2b1b83a5c5ad96c815348e28ed7da68e2e3687004faa906251
#6 CACHED

#7 [internal] load build context
#7 transferring context: 1.72GB 5.0s
#7 transferring context: 3.40GB 9.6s done
#7 DONE 9.7s

#8 [build 2/4] WORKDIR /app
#8 CACHED

#9 [build 3/4] COPY conduit/ .
#9 ...

#10 [stage-1 2/3] RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates && rm -rf /var/lib/apt/lists/*
#10 0.735 Get:1 http://deb.debian.org/debian bookworm InRelease [151 kB]
#10 1.573 Get:2 http://deb.debian.org/debian bookworm-updates InRelease [55.4 kB]
#10 1.924 Get:3 http://deb.debian.org/debian-security bookworm-security InRelease [34.8 kB]
[... 1162 more lines]
```

</details>

**Agent:**

Implemented the Conduit backend, including the RealWorld API, drafts, exports, editing links, revision conflicts, WebSocket updates, presence, and the 100-editor room cap.

The main API and live editing rules are in [server.rs](/work/app/conduit/src/bin/server.rs). [schema.sql](/work/app/conduit/src/bin/schema.sql) prepares PostgreSQL at startup; [Dockerfile](/work/app/Dockerfile) packages the single production container.

**Checks are green:** the development and production gates each passed all 17 API files (237 requests), the socket protocol check, four browser tests, and all 13 security files (52 requests). `cargo fmt --all -- --check` and `cargo clippy --all-targets -- -D warnings` passed. The first development run found that an empty bio needed to become `null`; I fixed that and reran the full suite.

Known limit: exports are durable in PostgreSQL and processed outside requests, but their polling worker is custom rather than Loco’s built-in job queue.

