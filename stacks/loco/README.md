# Loco (Rust)

Loco 1.2 (JSON API) with SeaORM 2, Axum and PostgreSQL.

Built and evolved by Codex CLI 0.157.1, model `gpt-6-sol` at `xhigh` reasoning. [`ENVIRONMENT.md`](ENVIRONMENT.md) is everything the agent was told about the stack; [`scaffold/`](scaffold/) is the untouched generator output.

| Step | Code | Size (tokens) | Added or changed (tokens) | Agent tokens | Time | Report | Transcript |
| --- | --- | ---: | ---: | ---: | ---: | --- | --- |
| 1. Build | [`1-build/`](1-build/) | 8,804 | 8,142 | 228,773 | 20.2 min | [report](reports/1-build.md) | [transcript](transcripts/1-build.md) |
| 2. Add drafts | [`2-add-drafts/`](2-add-drafts/) | 10,202 | 1,689 | 96,555 | 15.8 min | [report](reports/2-add-drafts.md) | [transcript](transcripts/2-add-drafts.md) |
| 3. Package | [`3-package/`](3-package/) | 10,194 | 46 | 75,165 | 7.3 min | [report](reports/3-package.md) | [transcript](transcripts/3-package.md) |
| 4. Tune | [`4-tune/`](4-tune/) | 11,112 | 1,318 | 105,128 | 18.7 min | [report](reports/4-tune.md) | [transcript](transcripts/4-tune.md) |
| 5. Harden | [`5-harden/`](5-harden/) | 11,339 | 225 | 94,115 | 7.7 min | [report](reports/5-harden.md) | [transcript](transcripts/5-harden.md) |
| 6. Polish | [`6-polish/`](6-polish/) | 11,373 | 655 | 129,109 | 8.9 min | [report](reports/6-polish.md) | [transcript](transcripts/6-polish.md) |
| 7. Add a background job | [`7-add-background-job/`](7-add-background-job/) | 12,884 | 1,566 | 123,307 | 9.6 min | [report](reports/7-add-background-job.md) | [transcript](transcripts/7-add-background-job.md) |

Comprehension runs (read-only): [after-1-build](transcripts/comprehension-after-1-build.md), [after-6-polish](transcripts/comprehension-after-6-polish.md).
