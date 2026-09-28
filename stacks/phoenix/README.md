# Phoenix

Phoenix 1.8 (JSON API) with Ecto and PostgreSQL.

- `scaffold/` is the untouched, product-free generator output every Phoenix run starts from.
- `reference/` is the current reference app: run `2026-09-27-phoenix-density-1` in the [ledger](../../results/runs.jsonl), built from the baseline prompt. The rule that picks it is in [results/README.md](../../results/README.md).
- `stack.json` holds the port, the agent settings and the measurement rules.

| Reference run | |
| --- | ---: |
| Code the agent wrote | 8,954 tokens, 990 lines |
| Whole backend | 13,399 tokens |
| Agent time | 14.1 min |
| Agent tokens, uncached input plus output | 145,244 |
| Development gate | pass |
| Production gate | pass |
| Single article | 5,439 req/s |
| Article list | 1,044 req/s at 42 SQL statements per request |
| Framework use | yes |

The agent's own map of where each product rule lives is [reference/DOMAIN.md](reference/DOMAIN.md), with commands in [reference/AGENTS.md](reference/AGENTS.md).

```bash
.venv/bin/python tools/measure.py phoenix        # re-measure the reference app
tools/one_shot_demo.sh phoenix                  # run it with the shared editor
```
