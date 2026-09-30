# Clojure foundation provenance

This lane begins with a maintainer-authored, product-free scaffold prepared on
2026-09-30. It is inspired by Kit's focused Clojure application composition;
it is not generated from Kit and contains no copied Kit application code or
Conduit implementation. Its health route, Integrant lifecycle, configuration,
pool/migration/queue plumbing, reload loop, build files, and developer commands
were authored for this experiment before any measured coding attempt.

Direct dependency versions and source links are documented in `SELECTION.md`
and `scaffold/deps.edn`. Temurin images and the Clojure CLI/OSV binary downloads
are pinned by digest or SHA256. The preflight records the exact resolved runtime
basis, Maven/Clojars coordinates, and dependency JAR hashes. Each measured work
tree retains the untouched `.scaffold/` size baseline.

The SQL in `scaffold/resources/migrations/001-proletarian.up.sql` is adapted
from [Proletarian 1.0.115's PostgreSQL tables.sql](https://github.com/msolli/proletarian/blob/v1.0.115/database/postgresql/tables.sql).
The changes add Migratus statement separators and use the versioned migration
for one-time table/index creation. The companion down migration reverses those
objects. Proletarian is copyright © 2020–2025 Martin Solli and is distributed
under the [MIT license](https://github.com/msolli/proletarian/blob/v1.0.115/LICENSE).
The complete copyright and permission notice is retained at
`scaffold/resources/licenses/proletarian-MIT.txt`, which is also packaged in
the production uberjar with the migrated SQL.

Infrastructure preflight fixtures are generated only into a throwaway source
copy by `tools/clojure_track_preflight.py`. They test framework boundaries,
transactions, worker lifecycle, raw WebSocket, reload, and release packaging.
They are not part of the frozen scaffold or measured product implementation.
Preparatory failures and the original dependency advisory reports are retained
under `results/lanes/clojure/preflight-attempts/`; the final `preflight.json`
identifies the exact source digest and toolchain used for the lane.
