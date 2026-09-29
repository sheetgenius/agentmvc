Implemented the Conduit backend and documented its rule map in [AGENTS.md](/work/app/AGENTS.md).

The main rule owners are [article_policy.ts](/work/app/app/services/article_policy.ts) for visibility and permissions, [articles.ts](/work/app/app/services/articles.ts) for lists and revision writes, [shares.ts](/work/app/app/services/shares.ts) and [live.ts](/work/app/app/services/live.ts) for links and sockets, and [build_export.ts](/work/app/app/jobs/build_export.ts) for export snapshots.

The app uses Adonis routes, middleware, exceptions, Lucid migrations and database queries, its PostgreSQL queue, and an Ace recovery command. Password hashing uses Adonis scrypt; JWTs use `jose`; sockets use `ws`. TypeScript caller unions and a database revision compare and swap carry the main permission and conflict rules.

**Checks pass:** formatter, linter, typecheck, three unit tests, and both complete development and fresh production gates. Each gate passed 17 API files, the live protocol check, four browser tests, and 13 security files. The first development gate exposed blank fields that the body parser converted to `null`; the input rule was fixed and the complete gate passed on rerun.

Measured against `.scaffold/`: 1,108 owned backend nonblank, noncomment lines and 10,875 `o200k_base` tokens; whole backend: 1,555 lines and 14,400 tokens. Test source is 78 lines; agent docs are 32 nonblank lines. Generated Lucid schema is excluded.

Known limits: presence and the room cap are process local, so this deployment runs one backend instance. Input decoding is centralized in typed helpers rather than compiled Vine validators, and ordinary persistence uses parameterized Lucid database queries rather than Lucid models.