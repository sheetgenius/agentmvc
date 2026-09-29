# Supplemental source review — pending live confirmation

This review inspected the published Python `4-tune` checkpoint. It did not
change measured sources, frozen inputs, or the common reviewer probe, and was
not delivered to measured agents. The full step-8 and one-shot review may
supersede these observations. No performance improvement is claimed.

## Favorite filter hypothesis

[`api.py:345`](../../stacks/python/4-tune/conduit/api.py#L345) filters
`favorites__username` before
[`models.py:25`](../../stacks/python/4-tune/conduit/models.py#L25) annotates
`Count("favorites")`. This appears to restrict the total to the selected user's
favorite row. An article with two favorites should still report
`favoritesCount: 2` in either user's filtered list. Django documents that
[filtering before annotation constrains aggregation](https://docs.djangoproject.com/en/6.0/topics/db/aggregation/#order-of-annotate-and-filter-clauses).
This is a source-based hypothesis awaiting live confirmation.

[`tools/lane_favorites_probe.py`](../../tools/lane_favorites_probe.py) is a
separately labeled supplemental diagnostic for equal application to final Go
and Python apps. It creates a unique author, two favoriters, a reader and an
article in an already-running disposable database. For anonymous requests and
all four users, it compares direct reads with lists having no favorite filter,
the first favorite filter, and the second. All lists share a unique tag scope
to exclude unrelated data. It repeats after removing the first favorite,
checking membership, global counts and viewer-relative flags. It leaves its
data for inspection. JSON contains safe case metadata, never response bodies,
tokens, email addresses, passwords, exception messages, or request URLs.

Example for a later reviewer run:

```sh
python3 tools/lane_favorites_probe.py --base-url http://127.0.0.1:4111 --timeout 10 --output /tmp/python-favorites.json
```

Exit codes: `0` all cases pass; `1` assertions fail; `2` setup or transport fails.
The script follows common reviewer HTTP conventions without modifying that
probe. It is outside the frozen acceptance suite. No live run has been made.
Local validation used in-memory fake HTTP responses: all 48 cases passed for
correct behavior; simulating the filtered-count bug failed the expected 10
cases. Syntax, strict integer/boolean checks and output redaction were also
checked without network requests.

## Query execution observation

[`api.py:368`](../../stacks/python/4-tune/conduit/api.py#L368) adds the favorite
aggregate before slicing. SQL grouping precedes the final ordering and limit;
the actual cost requires PostgreSQL plan inspection. Two statements per
anonymous list do not establish bounded page work. A later reference can
compare the current plan with a true ordered page boundary followed by
enrichment, or correlated counts and suitable indexes. Measure count and page
queries separately with `EXPLAIN (ANALYZE, BUFFERS)` as data grows. Preserve the
filtered total and omission of article bodies from summaries.

## Input and domain ownership observation

[`api.py:240`](../../stacks/python/4-tune/conduit/api.py#L240) declares every
article change as `Any`; the update endpoint at line 397 owns the transaction,
authority, revision, validation and mutation rules. It correctly checks strict
integer revisions before content validation. A later reference should preserve
that ordering while validating strict input types at a narrow boundary and
sharing one transactional content operation between author and keyed edits.
Also reconcile accepted title/tag lengths with the model's 255-character
storage limits. Tests should cover omitted versus null fields, boolean/string
revisions, stale revision plus invalid content, capability denial plus invalid
content, long strings, and concurrent author/keyed edits. Judge final rule
ownership after step 8, when both edit paths exist.
