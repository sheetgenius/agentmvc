# Phoenix expert reference 2

This is an **unscored diagnostic revision** of [reference 1](../reference-1/README.md), itself a repair of the [measured Phoenix pilot](../pilot-1/README.md). Read the [source](source/) directly or inspect the patches from [reference 1](reference-2-from-reference-1.patch) and the [scored pilot](reference-2-from-scored.patch). The frozen fixture remains `fe4624b0126a9ed83bd69df09f4d8ff5eef40f519db38c1a52efcd7a22e8a36e`; the measured source and results remain intact.

Reference 1 repaired edit authorization precedence, extreme identifiers, long title storage, and article filtering. Reference 2 adds a per-email login reservation before password verification. Pending plus failed attempts reach the same 20-attempt ceiling. A successful verification clears that email's failures; `finish`, `cancel`, and caller death release reservations idempotently. A `try`/`after` path also releases a reservation if verification raises and its caller rescues. Five focused concurrency tests cover burst admission, success reset, rescued errors, dead callers, and duplicate finishes. This admission policy can reject some simultaneous valid logins when 20 attempts for the same email are in flight; it is a deliberate tradeoff to enforce the burst ceiling.

| Measure | Scored pilot | Reference 1 | Reference 2 |
| --- | ---: | ---: | ---: |
| Owned backend tokens | 12,145 | 12,474 | 12,893 |
| Owned backend lines | 1,359 | 1,400 | 1,464 |
| Fixed development gate | Pass | Pass | Pass |
| Fresh production gate | Pass | Pass | Pass |
| Common reviewer HTTP contract | 16/20 | 21/21 | 21/21 |
| Common reviewer quality checks | 1/3 | 2/3 | 3/3 |

The scored pilot's common probe stopped after an early long-title failure, so its 20-check denominator is different. Reference 2 adds 419 owned tokens and 64 lines over reference 1, or 748 tokens and 105 lines over the scored pilot, using the same [size rules](size.json). Tests and documentation are excluded. [Changed files](change-summary.json), [source hashes](source-snapshot.json), and the [file inventory](source-files.json) bind the comparison.

The focused [formatter, warnings-as-errors compile, and tests](../../v2-expert-symmetry/references/phoenix-reference-2/focused-attempt2.json) passed (5 tests, 0 failures). The independent [development gate](../../v2-expert-symmetry/references/phoenix-reference-2/development.json) passed in 37.6 seconds with the full API, live, browser, and 13 security files, plus 14 ExUnit tests. The [fresh production gate](../../v2-expert-symmetry/references/phoenix-reference-2/production.json) passed in 22.4 seconds. The supplemental [common HTTP probe](../../v2-expert-symmetry/references/phoenix-reference-2/common-http.json) passed all 21 contract and 3 quality checks. Its reviewed compiled-release image is `sha256:0286614bd4745143170af6fc413b5bb011ba3210ff2f2667ddddb367889449b6` (165,666,921 bytes). Scrubbed [development](../../v2-expert-symmetry/references/phoenix-reference-2/development.log) and [production](../../v2-expert-symmetry/references/phoenix-reference-2/production.log) logs are retained.

Reference 2 has not been substituted into the scored paired runtime benchmark. A separate [short paired reference diagnostic](../../v2-expert-symmetry/reference-runtime/summary.json) measured anonymous lists and article reads in two alternating rounds; its raw streams [passed validation](../../v2-expert-symmetry/reference-runtime/raw-validation.json). It is an unscored measurement with a shorter workload.

[Machine-readable validation](validation.json) records the fixture, source, image, sizes, and gate results together.
