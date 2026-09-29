Built the Conduit backend and documented its rule owners in [AGENTS.md](/work/app/AGENTS.md).

[Users.hs](/work/app/app/Users.hs) and [Auth.hs](/work/app/app/Auth.hs) own accounts and authentication; [Articles.hs](/work/app/app/Articles.hs) and [Domain.hs](/work/app/app/Domain.hs) own article rules and validation; [Shares.hs](/work/app/app/Shares.hs) owns live editing; and [Exports.hs](/work/app/app/Exports.hs) owns durable snapshots. [Main.hs](/work/app/app/Main.hs) binds these rules to Servant routes. [Db.hs](/work/app/app/Db.hs) applies numbered migrations; [001_init.sql](/work/app/migrations/001_init.sql) enforces database invariants.

The running app uses GHC2021 and Servant’s typed routes, Warp/WAI, STM and `wai-websockets`, Hasql/PostgreSQL, `jose` for signed tokens, bcrypt for passwords, and `crypton` for share keys. Servant has no built-in job queue, so the export worker runs in the same container against a durable PostgreSQL queue.

**Final checks pass:** both `check-all.sh` and the fresh-database `check-production.sh` passed all 17 API files, the live protocol, four browser tests, and 13 security files. Fourmolu and HLint passed; the focused [revision and revocation test](/work/app/tests/rules.py) passed. An initial API failure for empty-bio normalization was fixed. A migration startup gap found in review was also fixed, then both gates were repeated.

Measured executable backend: **861 owned** nonblank, noncomment lines / **13,784 `o200k_base` tokens**; **905 lines / 14,075 tokens** including unchanged scaffold. Tests: 77 lines / 755 tokens; project docs: 19 lines / 492 tokens. No generated source was counted.

Known limit: one Hasql connection serializes database requests; exact filtered article counts scan the matching set.