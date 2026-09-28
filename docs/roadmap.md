# Roadmap

The one-shot baseline measures what an agent builds from scratch. The open question is what happens after: how safely a fresh agent can find a rule and change it as the system grows. That is where typed stacks should earn their extra code, and nothing measures it yet.

## Experiments

1. **Handoffs.** Fresh agents, with no context from the builder, change a reference app. Each change is the same product request in every stack, with public and held-out checks and a reference implementation frozen before any scored run.
   - **Organizations and roles.** Workspaces, membership roles and article visibility across lists, direct reads, editing links, exports and sockets. It tests whether one policy has one owner.
   - **An evolving workflow.** Review and scheduled publication, with durable state transitions, cancellation and an audit trail. It changes an existing rule rather than only adding endpoints.
   - **A compatibility change.** Move a permission or revision rule to a new model while previously issued links and old rows keep working through a migration.
   - **A two-instance incident.** Two app instances on one database, one restarted during activity, with checks on presence, room caps, revocation and job idempotency.

   Measure correctness and regressions, agent effort, navigation such as time to the right file, files opened and wrong owners visited, the size of each change, and duplicated rules.
2. **A native-client track.** Specify browser journeys instead of a fixed client, and let each stack use its own UI and real-time path: Hotwire, LiveView and IHP's own. Count all application-owned client and server code, and keep these results separate from the API baseline.
3. **More runs and a second model.** At least three runs per stack and prompt, and all four stacks on a second model.

## Harness work

- **A brief launcher for every stack.** Generalize `tools/ihp_guided.py`, which appends a brief to the baseline prompt but is fixed to IHP run 4.
- **The IHP Nix store.** Script the product-free base store build and the per-run copy that `docs/running.md` describes.
- **Representative production builds.** IHP's `optimized-prod-server` with an explicit capability count, a measured Puma worker count for Rails, and a release build for Phoenix.
- **Held-out acceptance checks,** so prompts and briefs can't be tuned to the visible suite.
- **The Phoenix toolchain path.** The broker runs Phoenix commands in a `conduit/` subdirectory the scaffold doesn't have, so agents create a symlink alias. Align the two.
- **A revised baseline prompt.** Ask for typed request decoding, maintained crypto libraries, bounded list queries and a short agent guide, based on [pitfalls.md](pitfalls.md).
- **Archives for the September runs.** Upload their transcripts and logs, and fill in the ledger's archive fields.
- **Navigation events.** Record files opened and searches during agent sessions, so handoff experiments can measure navigation directly.

Present results as a profile per stack and show where rankings differ, rather than as one weighted score.
