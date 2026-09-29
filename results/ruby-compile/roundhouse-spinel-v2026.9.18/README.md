# Roundhouse + Spinel feasibility round

This is a **compatibility result, not a throughput result**. Roundhouse v2026.9.18 cannot strictly emit the measured Rails Conduit source for Spinel. No compiled Conduit server or comparable requests/second measurement exists in this round. The Rails source and production image were left unchanged.

## Reproduce

- Input: [measured Rails source](../../one-shot-v2-rails-expert/pilot-1/source/), from the v2 expert one-shot.
- Tool: [Roundhouse v2026.9.18](https://github.com/rubys/roundhouse/releases/tag/v2026.9.18), macOS arm64 archive SHA-256 `02910374a0c4585a3d7517d9d3a6f2e52f603b3da77c3e3f5e3225910b99ab3b`; `roundhouse --version` reported `2026.9.18 (2e286e6f)`.
- No `--allow-unsupported` output was built or benchmarked. That option inserts behavior stubs, according to the [transpile guide](https://github.com/rubys/roundhouse/blob/v2026.9.18/docs/guide/transpile.md).

From the repository root, with that Roundhouse binary on `PATH`:

```sh
roundhouse check --continue results/one-shot-v2-rails-expert/pilot-1/source
roundhouse --target spinel -o .work/ruby-compile/spinel-strict results/one-shot-v2-rails-expert/pilot-1/source
roundhouse --target spinel --survey -o .work/ruby-compile/spinel-survey results/one-shot-v2-rails-expert/pilot-1/source
```

All three commands exited 1. Outputs: [run record](run.json), [coverage check](check.log), [strict emit](strict-emit.log), [survey emit](survey-emit.log). The strict emit stopped at a nested `ClassNode` in `ApplicationController`. The continuing check reported **1 ingest gap, 17 type errors, 88 warnings, 18 gap-attributed notes**, plus **3 unknown gems: `faye-websocket`, `good_job`, `jwt`**. The survey emit reached analysis and stopped with 18 type errors. Its examples include unresolved `with_lock`, Rails parameter methods, JWT encoding, and error methods.

The larger compatibility gap is architectural. The measured app uses PostgreSQL types and constraints, GoodJob's durable queue, and a raw Faye WebSocket with direct `Thread.new`. Roundhouse's [release coverage](https://github.com/rubys/roundhouse/blob/v2026.9.18/docs/guide/rails-coverage.md) describes an in-process job queue, Action Cable sockets, and no lowering for application `Thread` calls. Its [Spinel target](https://github.com/rubys/roundhouse/blob/v2026.9.18/docs/guide/spinel.md) runs on SQLite by default. A SQLite or stubbed version would change the workload and product contract, so it cannot establish a speedup for this app. The tool may gain coverage in future versions; this result applies to the pinned release and exact source above.

The 5× throughput suggestion remains a useful hypothesis for a **parity-preserving compiled build**. The existing [paired Rails, TypeScript, and Phoenix benchmark](../../v2-expert-symmetry/) supplies a fixed Rails baseline. A future compiled Rails image should first pass the shared development and production gates, then run the same seed, 2 CPU / 1 GiB limits, request mix, and repeated alternating-order measurements.
