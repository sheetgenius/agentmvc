# Loco

Loco 1.2 (JSON API) with SeaORM 2, Axum and PostgreSQL.

- `scaffold/` is the untouched, product-free generator output every Loco run starts from.
- `reference/` is the current reference app: run `2026-09-27-loco-density-1` in the [ledger](../../results/runs.jsonl), built from the baseline prompt. The rule that picks it is in [results/README.md](../../results/README.md).
- `stack.json` holds the port, the agent settings and the measurement rules.

| Reference run | |
| --- | ---: |
| Code the agent wrote | 11,437 tokens, 1,240 lines |
| Whole backend | 21,503 tokens |
| Agent time | 19.7 min |
| Agent tokens, uncached input plus output | 243,185 |
| Development gate | pass after 2 attempts |
| Production gate | pass |
| Single article | 7,470 req/s |
| Article list | 607 req/s at 21 SQL statements per request |
| Framework use | partial |

Loco runs startup, routes, migrations and the worker; persistence is bound SQL with untyped JSON rather than SeaORM entities.

The agent's own map of where each product rule lives is [reference/conduit/AGENTS.md](reference/conduit/AGENTS.md).

```bash
.venv/bin/python tools/measure.py loco        # re-measure the reference app
tools/one_shot_demo.sh loco                  # run it with the shared editor
```
