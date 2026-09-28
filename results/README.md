# Run ledger

[runs.jsonl](runs.jsonl) holds one line of JSON per scored agent run. It is the only run output kept in Git. Transcripts, agent reports, gate logs and raw benchmark streams stay in the local `results/<run>/` folders, which Git ignores, until they are archived.

Print the ledger as a table, or show the current reference run for each stack:

```bash
python3 tools/ledger.py table
python3 tools/ledger.py best
```

## Fields

| Field | Meaning |
| --- | --- |
| `id` | Date, stack, prompt and run number, such as `2026-09-27-rails-density-1` |
| `prompt` | The prompt's short name and the SHA-256 of the exact text the agent received |
| `brief` | The stack brief appended to the prompt, if any |
| `fixture_sha256` | The frozen-input manifest the run used |
| `agent` | Agent tool, model and reasoning setting |
| `effort` | Wall time, uncached input plus output tokens, total input processed, output tokens and commands |
| `gates` | The independent development and fresh-database production gates, with the number of attempts |
| `code` | Owned tokens and lines added to the scaffold, whole-app tokens, and tokens of agent-written docs |
| `runtime` | Means over the measurement rounds: single-article and article-list throughput, SQL statements per list request, peak memory, cold start, image size, and WebSocket delivery p95 at 500 subscribers |
| `review` | The reviewer's verdict on framework use, with a note |
| `archive` | The archive holding the run's transcript and logs, with its checksum |

The framework verdict has three values:
- **yes:** the framework runs the production app through its conventional paths;
- **partial:** the framework runs the app, but the agent routed around one of its conventions;
- **no:** the production app bypasses the framework.

## Reference apps

Each stack's reference app in `stacks/<stack>/reference/` is the run that:

1. used the current baseline prompt, `one-shot/PROMPT.md`, with no brief;
2. passed both independent gates;
3. did not bypass the framework;
4. has the fewest owned tokens among those runs.

`tools/ledger.py best` applies this rule, and `tools/reference.py` copies the winning app and checks that its measured size matches its ledger row. Near ties are noise at this sample size, so settle them with more runs rather than by picking.

## Archives

The runs recorded so far have not been archived yet. Their full output exists only on the machine that ran them, and the `archive` field is empty until it is uploaded. For new runs, archive `results/<run>/<stack>/` and any runtime folder, then record the archive's name and SHA-256 in the row.

## What these rows cover

- Ten runs on 27 and 28 September 2026, all with Codex CLI 0.157.1 running `gpt-6-sol` at `xhigh`.
- The `first` prompt preceded the current baseline. It asked for stack idioms, but the Loco agent still wrote a standalone server; the baseline now rules that out explicitly.
- The `density` prompt is the current baseline.
- The `ihp-expert` brief ran once, as a diagnostic.
- IHP's runtime rows came from an unoptimized single-core build made by the harness, and were measured in separate sessions from the other stacks.
