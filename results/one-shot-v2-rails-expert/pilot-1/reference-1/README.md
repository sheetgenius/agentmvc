# Rails expert reference 1

This is an **unscored diagnostic revision** of the [measured Rails pilot](../source/). Its [source](source/) is browsable directly; [the patch](reference-1.patch) shows every change from the [scored source](../source/). Both use the same frozen fixture, `55a085d8c6645c56e24e1144f2e9cf5ab300b9ff823b65b2d5039a23343da3b7`. The measured source and benchmark results remain intact.

The revision rejects an explicit `revision: null` without changing the article, sends revocation events for the actual retired share links, accepts only JSON object subscription messages, returns all comments when no page limit is requested, and sends a live update when a draft is published. Focused tests cover these boundaries and the existing product rules. The final test implementation uses explicit temporary method replacement because this project's Minitest 6 setup does not provide `stub`.

| Measure | Scored pilot | Reference 1 |
| --- | ---: | ---: |
| Owned backend tokens | 6,010 | 6,085 |
| Owned backend lines | 644 | 657 |
| Fixed development gate | Pass | Pass |
| Fresh production gate | Pass | Pass |
| Common reviewer HTTP contract | 20/21 | 21/21 |
| Common reviewer quality checks | 3/3 | 3/3 |

[Size details](size.json) use the same product-free Rails scaffold and `o200k_base` rules as the pilot. Tests and documentation are excluded from owned backend size. The reference adds 75 owned backend tokens and 13 lines. [Changed files](change-summary.json), [source hashes](source-snapshot.json), and the [file inventory](source-files.json) make the delta inspectable.

The independent [development gate](../../../v2-expert-symmetry/references/rails-reference-1/development.json) passed in 27.1 seconds: full API, live, browser, and 13 security files, plus Zeitwerk, RuboCop, and 14 tests with 54 assertions. The [fresh production gate](../../../v2-expert-symmetry/references/rails-reference-1/production.json) passed in 32.3 seconds. The supplemental [common HTTP probe](../../../v2-expert-symmetry/references/rails-reference-1/common-http.json) passed all 21 contract and 3 quality checks. Its reviewed image is `sha256:00999c21b297988fbe7044f727a7628d2a083fb0211ed3fbf6666b5d5af834a3` (324,044,468 bytes). Scrubbed [development](../../../v2-expert-symmetry/references/rails-reference-1/development.log) and [production](../../../v2-expert-symmetry/references/rails-reference-1/production.log) logs are retained, as are the earlier focused-test failures and the final [passing run](../../../v2-expert-symmetry/references/rails-reference-1/focused-attempt4.json).

The reference image has not been substituted into the scored paired runtime benchmark. A separate [short paired reference diagnostic](../../../v2-expert-symmetry/reference-runtime/summary.json) measured anonymous lists and article reads in two alternating rounds; its raw streams [passed validation](../../../v2-expert-symmetry/reference-runtime/raw-validation.json). It is an unscored measurement with a shorter workload.

[Machine-readable validation](validation.json) records the fixture, source, image, sizes, and gate results together.
