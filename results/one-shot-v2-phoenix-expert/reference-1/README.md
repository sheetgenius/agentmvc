# Phoenix expert reference 1

This is an **unscored diagnostic revision** of the measured [Phoenix pilot](../pilot-1/README.md). The pilot's source and measurements remain unchanged. Apply [the patch](reference-1.patch) to its [source snapshot](../pilot-1/source/) to inspect or rebuild this revision; the patch dry-runs cleanly against the original workdir. [Source hashes](source-hashes.json) bind the nine changed files to the pilot source hash `96c0d9798699d5d9f485115de8becda9fda98876a9edd11885792d635e9df74d`. The frozen fixture remains `fe4624b0126a9ed83bd69df09f4d8ff5eef40f519db38c1a52efcd7a22e8a36e`.

The revision adds **329 agent-owned tokens and 41 agent-owned code lines** under the same measurement rules: 12,145 → 12,474 tokens and 1,359 → 1,400 lines. Whole-backend size moves from 15,237 → 15,573 tokens. It keeps Phoenix routing, Ecto queries/changesets, the locked article commit, Oban jobs, PubSub, and the compiled release from the measured implementation.

## Changes

- Author edits resolve visibility and ownership before decoding the article envelope. The locked commit rechecks both rules, and shared edits use the same locked write with a capability check and exact allowed input shape.
- Slug stems are capped so an accepted 255-character title fits the stored slug. A migration changes the title column to `text`, preserving the Ecto grapheme limit for decomposed Unicode.
- Export and comment identifiers outside PostgreSQL `bigint` range resolve as missing resources.
- The tag filter uses PostgreSQL array containment, which can use the existing GIN index. A migration extends the published-article ordering index with `id` for the actual `(inserted_at, id)` tie-break order. Count and page share the same Ecto filter.
- Focused tests cover edit precedence and success, direct context visibility, share input shape, long and Unicode titles, identifier boundaries, and tag count/page agreement.

## Validation

The final revision passed [format, warnings-as-errors compile, and ExUnit](focused-checks.json): [9 tests, 0 failures](test.log). It passed the [independent development gate](development.json) in 122.4 seconds and the [fresh production gate](production.json) in 82.0 seconds. Both gate logs are retained ([development](development.log), [production](production.log)); development passed 17/17 API files, live protocol, four browser tests, and 13/13 security files. The production build uses a compiled release. The final production image used for the probe is `sha256:574d2567e559f076c60711c23bbd57082efefd24b2f1681eacea31c6d2d7019e`.

The [held-out replay](held-out.json) uses that image and a fresh database with 10,000 additional articles. Stranger edits with a malformed body return 403; missing-article edits with a malformed body return 404. A 255-character title creates successfully (201), and 100-digit export/comment identifiers return 404. The tag-filter HTTP request returns 200. [The probe](held-out-probe.py) records the exact response bodies, image, fixture, and patch hashes.

The PostgreSQL `EXPLAIN` probes use a **representative `SELECT id` filter/order query**, not the exact SQL emitted by the Ecto article loader. For the rare tag, the count uses the GIN bitmap index: 101 matches and zero rows removed by filter. The representative first-page query uses the new composite ordering index: 20 matches after filtering 1,881 nonmatching rows, versus 9,901 before the index. The [query trial](tag-query-trial.json) also records sparse/common tag plans and a slower materialized-CTE alternative. The index improves this seeded case; tag-page row visits are still **not universally bounded**, and this probe does not prove which plan the full Ecto projection uses.

This revision has no new repeated runtime benchmark. The pilot's throughput and code-size measurements remain properties of the unchanged measured candidate. Remaining source-level limits include process-local live room membership, no delete notification for a connected live room, and an export assembled from separately read article and comment data without one database snapshot.
