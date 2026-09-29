Implemented the Conduit backend, including the RealWorld API, drafts, exports, and shared live editing.

**Rule owners:** [Accounts](/work/app/lib/conduit/accounts.ex) owns identity and follows; [Articles](/work/app/lib/conduit/articles.ex) owns visibility, publication, revisions, and discovery; [Shares](/work/app/lib/conduit/shares.ex) owns editing capabilities; [Exports](/work/app/lib/conduit/exports.ex) owns snapshots. [AGENTS.md](/work/app/AGENTS.md) maps the extension paths.

The running app uses Phoenix routes, plugs, and controllers; Ecto schemas, migrations, SQL pagination, and locked transactions; Oban jobs; Joken JWTs; Bcrypt passwords; and Bandit/WebSockAdapter with supervised rooms for the fixed raw WebSocket protocol. Database constraints enforce persistent state and reference rules.

**Final checks passed:** formatter, warning-free compile, 5 project tests, and both development and fresh-database production gates. Each complete gate passed 237 API requests, the WebSocket protocol check, 4 browser tests, and all 13 security files. Earlier failures in error rendering, null and wrong-type inputs, and login limiting were fixed before these final runs.

Owned backend source measures **1,359 nonblank, noncomment lines / 13,460 `o200k_base` tokens** against `.scaffold/`; whole backend source is **1,626 lines / 16,732 tokens**. New tests add 75 such lines / 903 tokens; project docs add 705 tokens. The room cap, presence, and login-limit counts are process-local, consistent with the specified one-container topology; those counts reset on restart.