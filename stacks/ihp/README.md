# IHP

IHP 1.6.0 on GHC 9.10.3 with LiquidHaskell 0.9.10.1.2, Z3 4.16.0 and PostgreSQL.

- `scaffold/` is the untouched, product-free generator output every IHP run starts from.
- `reference/` is the current reference app: run `2026-09-28-ihp-density-1` in the [ledger](../../results/runs.jsonl), built from the baseline prompt. The rule that picks it is in [results/README.md](../../results/README.md).
- `stack.json` holds the port, the agent settings and the measurement rules.
- `briefs/expert.md` is a stack brief that `tools/ihp_guided.py` appends to the baseline prompt.

| Reference run | |
| --- | ---: |
| Code the agent wrote | 10,197 tokens, 683 lines |
| Whole backend | 12,350 tokens |
| Agent time | 73.5 min |
| Agent tokens, uncached input plus output | 451,865 |
| Development gate | pass |
| Production gate | pass |
| Single article | 3,976 req/s |
| Article list | 372 req/s at 21 SQL statements per request |
| Framework use | partial |

One catch-all API action matches method and path by hand. Measured on the harness image, an -O0 build on one core.

The agent's own map of where each product rule lives is the "Conduit rule map" section of [reference/AGENTS.md](reference/AGENTS.md).

```bash
.venv/bin/python tools/measure.py ihp        # re-measure the reference app
```

IHP runs on its own track because its toolchain runs through Nix; see [docs/running.md](../../docs/running.md). The reference app's Dockerfile expects the Nix-built image that the harness produces.
