# Phoenix (Elixir)

Phoenix 1.8 (JSON API) with Ecto and PostgreSQL.

Built and evolved by Codex CLI 0.157.1, model `gpt-6-sol` at `xhigh` reasoning. [`ENVIRONMENT.md`](ENVIRONMENT.md) is everything the agent was told about the stack; [`scaffold/`](scaffold/) is the untouched generator output.

| Step | Code | Size (tokens) | Added or changed (tokens) | Agent tokens | Time | Report | Transcript |
| --- | --- | ---: | ---: | ---: | ---: | --- | --- |
| 1. Build | [`1-build/`](1-build/) | 6,196 | 5,694 | 168,137 | 17.3 min | [report](reports/1-build.md) | [transcript](transcripts/1-build.md) |
| 2. Add drafts | [`2-add-drafts/`](2-add-drafts/) | 7,164 | 1,190 | 68,359 | 8.0 min | [report](reports/2-add-drafts.md) | [transcript](transcripts/2-add-drafts.md) |
| 3. Package | [`3-package/`](3-package/) | 7,197 | 82 | 68,463 | 9.1 min | [report](reports/3-package.md) | [transcript](transcripts/3-package.md) |
| 4. Tune | [`4-tune/`](4-tune/) | 7,764 | 756 | 123,896 | 18.1 min | [report](reports/4-tune.md) | [transcript](transcripts/4-tune.md) |
| 5. Harden | [`5-harden/`](5-harden/) | 8,110 | 531 | 83,546 | 9.0 min | [report](reports/5-harden.md) | [transcript](transcripts/5-harden.md) |
| 6. Polish | [`6-polish/`](6-polish/) | 8,138 | 486 | 89,156 | 6.8 min | [report](reports/6-polish.md) | [transcript](transcripts/6-polish.md) |
| 7. Add a background job | [`7-add-background-job/`](7-add-background-job/) | 9,062 | 953 | 55,586 | 4.7 min | [report](reports/7-add-background-job.md) | [transcript](transcripts/7-add-background-job.md) |

Comprehension runs (read-only): [after-1-build](transcripts/comprehension-after-1-build.md), [after-6-polish](transcripts/comprehension-after-6-polish.md).
