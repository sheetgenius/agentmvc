# Domain signal map and framework use

This is a file-level review of the three finished one-shot workdirs, not an additional numeric score. The [source inventories](rails/source-files.json), [Phoenix inventory](phoenix/source-files.json), and [Loco inventory](loco/source-files.json) list every counted source path and its contribution. Paths below are relative to each stack's `.work/one-shot-semantic-density/STACK/` directory. The authentic scaffolds remain in the whole-backend count; owned source is the change against each untouched scaffold.

| Behavior | Rails rule owner | Phoenix rule owner | Loco rule owner |
| --- | --- | --- | --- |
| Identity, login, follows | `app/models/user.rb`, `app/models/token.rb`, `app/controllers/api/{users,user,profiles}_controller.rb` | `lib/conduit/accounts.ex`, `lib/conduit/user.ex`; HTTP translation in `lib/conduit_web/controllers/api_controller.ex` | `conduit/src/controllers/people.rs` and `common.rs`; queries in `conduit/src/models/realworld.rs` |
| Article visibility, lists, drafts | `app/models/article.rb` scopes plus `app/controllers/api/articles_controller.rb` | `lib/conduit/content.ex` query and authorization functions | `conduit/src/controllers/articles.rs` plus `conduit/src/models/realworld.rs` SQL |
| Revision, publish, share capability | `Article` callbacks, `ArticlesController`, `SharesController`, `Share`; revision checks occur at both HTTP update entrances | `Content.update/4`, `Content.publish/1`, and share functions in the same context | `articles.rs`, `shares.rs`, and compare-and-update SQL in `realworld.rs` |
| Live editing and room cap | `app/models/live_socket.rb` and `live_rooms.rb` | `lib/conduit_web/live_socket.ex` and `lib/conduit/rooms.ex` | `conduit/src/controllers/shares.rs` |
| Durable exports | `app/jobs/export_job.rb`, `app/models/export.rb`, Solid Queue configuration | `lib/conduit/exports.ex`, `export_worker.ex`, Oban application configuration | `conduit/src/controllers/people.rs`, `workers/export.rs`, Loco queue configuration |
| Public JSON | `app/serializers/conduit_json.rb` and controller responses | `Content.represent/3` and `ApiController` | JSON values in controller and `realworld.rs` functions |

## What the source counts do and do not say

| Stack | Owned source | Whole backend | Agent-written docs | Largest owned files |
| --- | ---: | ---: | ---: | --- |
| Rails | 5,454 tokens / 638 lines | 10,475 tokens | 259 tokens / 7 lines | `articles_controller.rb` 707 tokens; application controller 444; live socket 397 |
| Phoenix | 8,954 tokens / 990 lines | 13,399 tokens | 263 tokens / 8 lines | `content.ex` 2,254 tokens; API controller 2,039; accounts 694 |
| Loco | 11,437 tokens / 1,240 lines | 21,503 tokens | 325 tokens / 9 lines | `articles.rs` 3,418 tokens; `shares.rs` 2,220; `people.rs` 2,096 |

Rails uses associations, scopes, validations, controller actions, and callbacks to express much of the product in short files. A reader must still trace a rule through those conventions: a revision increments in `Article`, while stale-revision and ownership responses are in the article and share controllers. Its guide names these owners.

Phoenix uses Ecto schemas, changesets, queries, contexts, and pattern-matched results. `Content` gives article policies a prominent owner, but that module and the API controller are each large. A fresh agent's ability to change one policy without widening those modules is a useful next test. Its guide names the contexts and transport boundary.

Loco's running application uses Loco `Hooks`, routes, migrations, and the PostgreSQL-backed worker. Conduit persistence is primarily bound SQL through SeaORM's connection interface, with dynamic JSON values across the domain and HTTP boundary. The scaffold's generated user/auth code remains in the whole-backend count, while the Conduit API uses separate `rw_users` code. This is valid passing software and a concrete framework-use observation; it does not demonstrate what SeaORM entities or stronger Rust domain types would do for change cost. The agent itself reported an article-list scaling limit: matching IDs are collected before pagination and page entries are rendered with separate queries.

All three implement the frozen client's direct WebSocket protocol with custom adapters or handlers, rather than a framework-native browser client. The current run therefore compares a common API and protocol. A separate native-client track is described in the [workshop plan](../../docs/semantic-density-workshop.md).

## Evolution questions prompted by this review

- Can a fresh agent add organization visibility once and have all list, direct-read, share, export, and socket paths honor it? Count the paths it must find and change, not only the final lines.
- Can the revision and share rules be migrated without a second source of truth or broken old data?
- Does using SeaORM entities or explicit Rust types in a Loco follow-up improve rule locality enough to offset more source and build context? Keep that follow-up separate from the scored one-shot.
- Do the short project guides reduce a fresh agent's search and incorrect edits? Measure actual navigation events rather than rewarding docs for existing.

The first two questions are shared product changes for all stacks. The Loco-specific question is a labeled diagnostic; it must not be mixed into a same-prompt ranking.
