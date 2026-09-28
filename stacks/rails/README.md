# Rails

Ruby on Rails 8.1 (API-only) with Active Record, Jbuilder and PostgreSQL.

- `scaffold/` is the untouched, product-free generator output every Rails run starts from.
- `reference/` is the current reference app: run `2026-09-27-rails-density-1` in the [ledger](../../results/runs.jsonl), built from the baseline prompt. The rule that picks it is in [results/README.md](../../results/README.md).
- `stack.json` holds the port, the agent settings and the measurement rules.

| Reference run | |
| --- | ---: |
| Code the agent wrote | 5,454 tokens, 638 lines |
| Whole backend | 10,475 tokens |
| Agent time | 11.8 min |
| Agent tokens, uncached input plus output | 150,876 |
| Development gate | pass |
| Production gate | pass |
| Single article | 517 req/s |
| Article list | 134 req/s at 25 SQL statements per request |
| Framework use | yes |

The agent's own map of where each product rule lives is [reference/AGENTS.md](reference/AGENTS.md).

```bash
.venv/bin/python tools/measure.py rails        # re-measure the reference app
tools/one_shot_demo.sh rails                  # run it with the shared editor
```
