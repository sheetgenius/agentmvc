**Status:** DONE.

**Gate result:** 15/15 Hurl files passed; formatter and Clippy clean; final `bin/check` exit code 0.

**Where the feature landed:**

- [articles.rs](../2-add-drafts/conduit/src/controllers/articles.rs) — added draft visibility, publishing, draft listing, and revision conflict responses.
- [comments.rs](../2-add-drafts/conduit/src/controllers/comments.rs) — applied draft visibility and comment restrictions.
- [articles.rs](../2-add-drafts/conduit/src/models/articles.rs) — added lifecycle state, revision changes, and published-only queries.
- [articles.rs](../2-add-drafts/conduit/src/models/_entities/articles.rs) — mapped the three new database fields.
- [realworld.rs](../2-add-drafts/conduit/src/views/realworld.rs) — included the new fields in article responses.
- [lib.rs](../2-add-drafts/conduit/migration/src/lib.rs) — registered the draft migration.
- [m20260927_000002_drafts.rs](../2-add-drafts/conduit/migration/src/m20260927_000002_drafts.rs) — added the database columns.
- [README.md](../2-add-drafts/README.md) — documented routes, rules, and spec choices.

**Passes:** Pass 1 tightened status and revision type validation. Pass 2 centralized ownership checks and the published-article query. Both ended with a green gate; I stopped after two passes.

**Spec decisions:** Draft authors can list their draft’s comments, which are empty. Article updates ignore `status`; publishing is the only transition. Existing articles receive a publication timestamp during migration.

**Run counts:** `bin/check` 4 runs; narrower runs: 2 Cargo checks and 3 formatter runs; compile failures: 2 missing SeaORM imports.

**Friction log:**

- The schema and generated SeaORM entity needed coordinated changes because they are separate files.
- SeaORM’s transaction and query types needed explicit imports, causing the two compile failures.
- Draft visibility affected article, comment, and favorite routes, so the lookup rule needed a shared path.
- Revision conflicts needed a row lock to keep the check and update together.

**Agent-friendliness notes:** Loco routes, SeaORM queries, and Serde kept the domain rules readable. Keeping generated entity fields aligned with migrations required extra care.