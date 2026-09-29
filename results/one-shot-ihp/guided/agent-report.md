Built the Conduit backend on IHP and verified it against the fixed client and a fresh production database.

**Checks passed:** the development and production gates each passed all 17 API files, the WebSocket protocol check, four browser tests, and 13 security files. `nix flake check --impure` passed; `stylish-haskell` completed and HLint reported no hints. LiquidHaskell proved the 0–100 room count bound and rejected a temporary false 0–99 bound. The production image archive is 770,524,203 bytes.

The main rule owners are [Api/Policy.hs](/work/app/Api/Policy.hs), [Api/Articles.hs](/work/app/Api/Articles.hs), [Api/Shares.hs](/work/app/Api/Shares.hs), [Api/Live.hs](/work/app/Api/Live.hs), and [Application/Schema.sql](/work/app/Application/Schema.sql). [AGENTS.md](/work/app/AGENTS.md) maps routes, jobs, migrations, and proof boundaries.

IHP runs the HTTP controller, typed SQL persistence, migrations, WebSocket app, and durable export worker in one container. Aeson, JWT, cryptonite, STM, and Haskell sum types cover the remaining boundaries. Build failures exposed an IHP job decoder requirement for `BIGINT`, a `JobStatus` name collision, and a schema parser that rejects `CREATE DOMAIN`; the migration and typed SQL boundary contain those adaptations.

Presence is held in process memory, so the current room coordination supports the specified single app instance.