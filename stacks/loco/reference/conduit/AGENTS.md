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

## More

- Docs: <https://loco.rs/docs/>
- Framework agent guide: <https://loco.rs/AGENTS.md>

## Conduit rule map

- `migration/src/m20260928_000001_realworld.rs` owns the PostgreSQL schema; Loco applies it at startup in both environments.
- `src/models/realworld.rs` owns bound SQL access, article views, slugs, atomic revision changes, and export snapshots. All new Conduit persistence belongs here or in a focused model beside it.
- `src/controllers/people.rs` owns accounts, profiles, follows, login throttling, and export requests. `src/workers/export.rs` builds snapshots through Loco's PostgreSQL queue.
- `src/controllers/articles.rs` owns article visibility, ownership, lifecycle, lists, tags, favorites, and comments. It uses the model's revision update for normal edits.
- `src/controllers/shares.rs` owns capability validation and the in-memory WebSocket room. It uses the same model revision update for shared edits. The room lock owns admission and presence; broadcasts follow committed writes.
- `src/controllers/common.rs` owns the RealWorld error envelope and signed Token authentication.
- `src/app.rs` registers every HTTP route and background worker. `config/{development,production}.yaml` selects PostgreSQL and the durable queue; `Dockerfile` runs Loco's server and worker together.

Run `harness/check-all.sh 4103` against a started development server, and `harness/check-production.sh 4103` against the image. Run `cargo fmt --all -- --check` and `cargo clippy --all-targets -- -D warnings` from `conduit/` after changes.
