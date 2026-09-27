# Background jobs: what does asynchronous work cost?

In step 7, each agent added [article exports](../../spec/features/exports/exports.md):
- `POST /api/user/exports` answers `202` with a pending export.
- A background job stores a snapshot of all the user's articles, drafts included, with comment counts.
- `GET /api/user/exports/:id` returns the snapshot.

The spec requires the stack's standard durable job system, backed by the app's own PostgreSQL, with no Redis. The production container must process jobs itself, with no extra environment.

One new Hurl file, 17 requests, polls until the job finishes. It also checks the snapshot semantics, ownership, malformed IDs and authentication. Before any agent saw the spec, a throwaway Rails implementation passed it, including a variant with a deliberately slow job.

## Hypotheses, written before the step ran

- **H1:** Rails still needs the least feature code, but the gap is smaller than for drafts, because this Rails app had removed Active Job at generation and must add a job system back, while Loco's is built in.
- **H2:** setting up the job system is a larger share of the cost in Rails than in Phoenix or Loco.
- **H3:** all three reach both checks green, with jobs running inside the single production container.

A measurement rule was also set before the run: installer-generated queue schema counts as generated schema, like `db/schema.rb`. If an agent copies it into a hand-written migration, the cost is reported both ways.

## Results

Every agent chose the job system the spec pointed to, and each was confirmed durable and PostgreSQL-backed in the code:
- **Rails:** Solid Queue in the app's database, run by the Puma plugin.
- **Phoenix:** Oban on the app's `Repo`.
- **Loco:** its `BackgroundQueue` with `kind: Postgres`, and the server started with `--server-and-worker`.

| | Rails | Phoenix | Loco |
| --- | ---: | ---: | ---: |
| Feature code, generated schema excluded, tokens | 526 | 953 (1.81×) | 1,566 (2.98×) |
| ...counting every line as written | 2,535 | 953 | 1,566 |
| Job-system setup: dependencies, configuration, startup wiring | 160 (30%) | 79 (8%) | 166 (11%) |
| Agent tokens, wall-clock time | 102k, 10.2 min | 56k, 4.7 min | 123k, 9.6 min |

## Reading

- **H1 doesn't hold: the gap didn't narrow.** Phoenix needed 1.81× Rails' code and Loco 2.98×, the same multiples as the drafts feature. That's despite the Rails app adding Active Job and a queue from nothing.
- **H2 holds.**
  - Setting up the job system was 30% of Rails' feature, against 8% in Phoenix and 11% in Loco.
  - Rails 8 expects Solid Queue to have its own database. Using the app's single database meant copying the installer's schema into a migration: 149 lines and 2,009 tokens. Counted as written, that makes setup 86% of Rails' cost.
  - Oban's setup was the lightest: a dependency, one line of configuration, a child in the supervision tree, and `Oban.Migration.up()`.
- **H3 holds.** All three process jobs inside the single production container.
- **Phoenix was the cheapest step to build:** 56k agent tokens in 4.7 minutes.
- **The friction was specific to each stack.**
  - **Rails:** the queue generator assumed a separate database. On macOS, the worker process also crashed on fork safety, which the agent fixed with a setting scoped to its `bin/check`.
  - **Loco:** its model and worker generators refused to run, because the migration marker and test module they expect had been removed as generator leftovers in step 1. The agent wired the files by hand.
  - **Phoenix:** its only friction was the Docker-only toolchain.
