# Phoenix expert v2 diagnostic: pilot 1

This is a **guided, unscored diagnostic**, separate from the original Phoenix one-shot and eight-step history. One measured `gpt-6-sol` agent built Conduit from a product-free Phoenix 1.8 scaffold with the byte-identical shared v2 prompt. The frozen fixture hash is `fe4624b0126a9ed83bd69df09f4d8ff5eef40f519db38c1a52efcd7a22e8a36e`; the prompt hash is `8d39c1f7f584ee1c00e5f3056c80d99214a4c0790bf23c22b0ea0f5dccabb943`.

## Outcome

**Both independently repeated standard gates pass. Post-run held-out probes reveal correctness and query-shape failures.** The agent took 1,202.9 seconds (20.0 minutes), used 183,171 uncached-input-plus-output tokens, and ran 86 commands, of which 13 failed during iteration. The development gate initially failed four times; its final run and both production attempts passed. Independent replay then passed the development gate in 36.9 seconds and a fresh production gate in 20.0 seconds.

| Independent development check | Result |
| --- | ---: |
| API contract | 17/17 files, 237 requests |
| Live protocol | Pass |
| Browser | 4/4 tests |
| Security | 13/13 files, 52 requests |
| Formatter, warnings-as-errors compile, focused tests | Pass; 5 tests |

The [run record](run.json), [check attempts](check-attempts.json), [command failures](command-failures.json), [development log](development.log), and [production log](production.log) contain the underlying results. The [transcript](transcript.md) and [agent report](agent-report.md) are scrubbed. The [source snapshot](source/) and [source hash manifest](source-snapshot.json) make the measured candidate reviewable.

## Code and runtime

The backend has **12,145 agent-owned tokens / 1,359 lines** and 15,237 whole-backend tokens / 1,735 lines under the frozen `tools/measure.py` rules. Tests and project docs are measured separately in [tests.json](tests.json) and [docs.json](docs.json); the [file inventory](source-files.json) shows what was counted. The largest owned file, `lib/conduit/articles.ex`, holds 2,973 tokens (24.5% of owned backend code).

Production image `sha256:d1320971dcf82f0cc831e8dcc5a9a6da833b306d101cd90d2a4d44cf54a92d4f` is 165.7 MB. Cold start was 1.13/1.12 seconds; idle memory was 162.0/144.2 MB. Under 16 virtual users with a three-second warmup and 15-second measurement per scenario:

| Request | Round 1 req/s | Round 2 req/s | SQL/request |
| --- | ---: | ---: | ---: |
| Anonymous article list | 5,154.7 | 5,200.2 | 4 |
| Signed-in article list | 4,095.3 | 4,088.4 | 7 |
| Article list by tag | 5,305.8 | 5,302.4 | 4 |
| Feed | 4,097.9 | 4,037.2 | 7 |
| Single article | 7,404.2 | 7,191.0 | 6 |

Both HTTP rounds had zero failed checks. The live sweep at 10, 100, and 500 subscribers had zero missing updates, duplicate revisions, or regressed revisions; p95 delivery ranged from 8.54 to 15.39 ms. [Runtime summary](runtime/summary.json), [per-round metrics and 36 compressed raw HTTP streams](runtime/http/), [raw checksums and frozen tool hashes](runtime/raw-manifest.json), and [live results](runtime/live/) are preserved. All 36 compressed streams passed [checksum, decompression, and sensitive-marker checks](runtime/raw-validation.json). The [raw archive manifest](raw-archive.json) records the checksum and 63-file verification of the separate release bundle. HTTP scenario order was fixed in both rounds; HTTP and live workload order was alternated. The benchmark field `foreign_container_cpu_percent_max` also counts its own unnamed k6 generator, so it must not be read as unrelated host load.

## Post-run diagnostic

The [held-out responses and PostgreSQL plans](held-out.json) were taken from the unchanged production image on a disposable database seeded with 10,000 extra articles. They do **not** change the scored result. The [reproduction script](held-out-probe.py) records the exact fixture, source snapshot, and image hashes.

| Probe | Observed | Intended behavior |
| --- | --- | --- |
| Stranger updates existing article with malformed envelope | 422 | 403 ownership error before body validation |
| Owner updates missing slug with malformed envelope | 422 | 404 missing article before body validation |
| Create article with accepted 255-character title | 500 | Accept or reject cleanly; generated slug must fit storage |
| Read export using 100-digit numeric ID | 500 | 404 |
| Delete comment using 100-digit numeric ID | 500 | 404 |
| Tag-filter count and page over 10,001 rows | Sequential scans; 9,900 rows filtered in each | Indexable predicate with bounded work |

The [source review](SOURCE_REVIEW.md) distinguishes behavior proved by gates or probes from issues inferred from code. The separate [unscored reference revision](../reference-1/README.md) addresses these findings; this measured source snapshot stays intact.
