# IHP one-shot agent, run 1

| | |
| --- | --- |
| Prompt | [frozen prompt](../frozen-prompt.md) |

Outputs longer than 40 lines are cut here; the `.jsonl` file next to this one has them in full.

**Agent:**

I’ll read the contract, framework scaffold, and harness instructions first, then implement the backend and run the required checks.

```sh
$ /bin/zsh -c "pwd && rg --files -g 'ENVIRONMENT.md' -g 'MEASUREMENT.md' -g 'realworld_spec/**' -g 'harness/README.md' -g 'AGENTS.md' -g '"'!realworld_spec/frontend/node_modules/**'"' | head -100"
```
<details><summary>output (exit 0)</summary>

```
/work/app
AGENTS.md
MEASUREMENT.md
ENVIRONMENT.md
```

</details>

```sh
$ /bin/zsh -c 'ls -la && find realworld_spec harness -maxdepth 3 -type f | sort'
```
<details><summary>output (exit 0)</summary>

```
total 384
drwxr-xr-x  39 user  staff   1248 Sep 28 09:58 .
drwxr-xr-x   3 user  staff     96 Sep 28 09:58 ..
drwxr-xr-x   3 user  staff     96 Sep 28 08:47 .claude
-rw-r--r--   1 user  staff      3 Sep 28 08:57 .dockerignore
-rw-r--r--   1 user  staff   1190 Sep 28 08:47 .envrc
-rw-r--r--   1 user  staff    192 Sep 28 08:47 .ghci
-rw-r--r--   1 user  staff     40 Sep 28 08:47 .gitattributes
drwxr-xr-x   3 user  staff     96 Sep 28 08:47 .github
-rw-r--r--   1 user  staff    385 Sep 28 09:09 .gitignore
drwxr-xr-x  30 user  staff    960 Sep 28 08:57 .scaffold
-rw-r--r--   1 user  staff  14640 Sep 28 08:47 .stylish-haskell.yaml
-rw-r--r--   1 user  staff   2396 Sep 28 08:47 AGENTS.md
-rw-r--r--   1 user  staff   1992 Sep 28 08:47 App.cabal
drwxr-xr-x   7 user  staff    224 Sep 28 08:47 Application
-rw-r--r--   1 user  staff   2396 Sep 28 08:47 CLAUDE.md
drwxr-xr-x   4 user  staff    128 Sep 28 08:47 Config
-rw-r--r--   1 user  staff    119 Sep 28 08:57 Dockerfile
-r--r--r--   1 user  staff   2042 Sep 28 09:01 ENVIRONMENT.md
-r--r--r--   1 user  staff   5019 Sep 28 01:45 EXPERIMENT.md
-r--r--r--   1 user  staff  13205 Sep 28 09:58 FIXTURE.json
-r--r--r--   1 user  staff   2630 Sep 28 01:46 MEASUREMENT.md
-rw-r--r--   1 user  staff    271 Sep 28 08:51 Main.hs
-rw-r--r--   1 user  staff    660 Sep 28 08:47 Makefile
-r--r--r--   1 user  staff   4291 Sep 28 01:45 PROMPT.md
drwxr-xr-x   3 user  staff     96 Sep 28 08:51 Proof
-rw-r--r--   1 user  staff   2192 Sep 28 08:47 README.md
-rw-r--r--   1 user  staff     46 Sep 28 08:47 Setup.hs
drwxr-xr-x   4 user  staff    128 Sep 28 08:47 Test
-rw-r--r--   1 user  staff    226 Sep 28 08:47 WorkerMain.hs
-rw-r--r--   1 user  staff    328 Sep 28 08:47 default.nix
-rw-r--r--   1 user  staff  59799 Sep 28 08:51 flake.lock
-rw-r--r--   1 user  staff   6580 Sep 28 09:04 flake.nix
drwxr-xr-x  15 user  staff    480 Sep 28 09:58 harness
-rw-r--r--   1 user  staff    113 Sep 28 08:47 hie.yaml
drwxr-xr-x   3 user  staff     96 Sep 28 08:47 lib
drwxr-xr-x   8 user  staff    256 Sep 28 09:58 realworld_spec
drwxr-xr-x   3 user  staff     96 Sep 28 09:58 security
-rwxr-xr-x   1 user  staff     30 Sep 28 08:47 start
drwxr-xr-x   6 user  staff    192 Sep 28 08:47 static
[... 52 more lines]
```

</details>

```sh
$ /bin/zsh -c 'cat ENVIRONMENT.md MEASUREMENT.md harness/README.md realworld_spec/features/{drafts/drafts,exports/exports,live-editing/live-editing}.md realworld_spec/frontend/src/{api,editor,live}.js'
```
<details><summary>output (exit 0)</summary>

```
# Environment

- Stack: IHP 1.6.0 on GHC 9.10.3, LiquidHaskell 0.9.10.1.2 and Z3 4.16.0, with PostgreSQL. The upstream product-free IHP boilerplate and a small checked refinement example are already present. Do not regenerate the project.
- Port: 4104. Bind the backend to `0.0.0.0` in its container. The fixed JSON API and raw WebSocket client use this port.
- Toolchain: `harness/ihp.sh run COMMAND...` executes inside the pinned Nix container, mounting only your workspace and a dedicated Nix store. It has network access for dependencies and no Docker socket. `harness/ihp.sh build` builds IHP's release binary, and `start|logs|stop` control the development backend. The Nix store is prewarmed. You may edit `flake.nix` to add libraries, but keep `liquidhaskell` and `pkgs.z3` on the Haskell compilation path so refinements are checked during builds.
- Proofs: `Proof/Invariant.hs` shows an active LiquidHaskell plugin. Put useful domain refinements in the compiled application's modules so the release build checks them. Ordinary Haskell types and IHP schema-generated types remain useful for the rest.
- PostgreSQL 17: `harness/db.sh start 4104` creates a disposable database, accessible from the toolchain as `postgres://agentmvc:agentmvc@host.docker.internal:54104/agentmvc`; `harness/db.sh stop 4104` removes it. Keep `Application/Schema.sql` and production migrations in sync.
- Production: IHP's Nix flake builds the app, worker and migration runner into one application image. Its `Dockerfile` wraps that image for the fixed gate. The container receives only `DATABASE_URL`, `SECRET_KEY_BASE`, and `PORT`. The startup script derives IHP's session secret, applies migrations, starts the durable worker, and serves the API and WebSocket endpoint.
- Checks: `harness/check-all.sh 4104` and `harness/check-production.sh 4104` use the same frozen protocol, browser and security checks as the other stacks. The coordinator builds and loads the IHP Nix image before the production Dockerfile. The client, spec and harness are read-only.
# Measurement boundary

The objective is usable semantic domain density for agent-maintained codebases of more than three million lines. The fixed product contract makes backend source size a comparable proxy for how much code expresses the same domain behavior. Size alone does not establish ease of navigation or safe modification; the reviewer also examines rule ownership, framework use in the running application, and the amount of context a future change would require.

The one-shot comparison measures backend application code added to each untouched framework scaffold. The reviewer reports both nonblank lines and `o200k_base` tokens. The qualitative review checks clear terseness; whether product rules are explicit, local, and easy for an agent to find and change; which domain behavior is supplied by the framework or chosen libraries; and how the language expresses the remaining logic without repetitive plumbing.

- **Owned source:** nonblank, noncomment lines added or changed against `.scaffold/`, including application logic, migrations, dependency manifests, and application configuration.
- **Whole backend:** all nonblank lines in the final application source, including the scaffold and comments.
- **Excluded from both:** `realworld_spec/`, `security/`, `harness/`, the shared frontend, prompt and environment files, tests, lockfiles, generated schema/entities, dependency caches, build output, Markdown, formatter/linter configuration, Dockerfiles, and check scripts.

Agent-written project docs, including `AGENTS.md`, are reported separately in nonblank lines and `o200k_base` tokens added or changed against `.scaffold/`, with a brief review of whether they help a future agent locate and extend domain behavior. Frozen inputs and generated dependency docs are excluded. Docs are not counted as executable backend source or treated as free evidence of code density.

The same per-stack file rules already used by `tools/measure.py` in the exploratory study apply. The reviewer records both counts and any generated-file classification before comparing results; moving product rules into excluded files is outside the contract. Shared editor and harness size and preparation effort are reported separately.

Agent effort runs from prompt delivery through the final response. Record elapsed time, uncached input and output tokens, check attempts, failures, and fixes. Independently rerun the development and production gates after the agent stops. Runtime measurements use the same production topology and direct protocol load for all stacks, with repeated nearby runs and background host load recorded.
# Fixed acceptance commands

Start your backend on the port in `ENVIRONMENT.md`, then run `harness/check-all.sh PORT`. It runs the complete Hurl API suite, direct WebSocket protocol check, four Playwright browser tests, and the 13 security files. Run your stack's formatter and linter too. `harness/db.sh start PORT` creates a disposable local PostgreSQL and prints `DATABASE_URL`; `harness/db.sh stop PORT` removes only that labelled container. These commands use a coordinator service. The Docker daemon and host socket are not available in the agent sandbox.

`harness/check-production.sh PORT` builds the Dockerfile in this workspace, starts a fresh PostgreSQL and one backend container with only `DATABASE_URL`, `SECRET_KEY_BASE`, and `PORT`, then runs the same checks. The backend image must apply its migrations on startup. The independent reviewer invokes the same host-owned gate after the agent stops.

`check-live.sh` uses the browser image prepared before the agent session. It checks the image ID in `browser-image-id`, mounts the editor read-only, copies it to temporary writable space inside the container, and runs the exact same tests for every stack. There is no browser download during a check. The backend must be reachable on the host port. The runner uses the host network; its network route and browser startup are preflighted before workspaces are handed to agents.

Phoenix agents use `harness/phoenix.sh run mix ...` for commands in the pinned Elixir container, and `harness/phoenix.sh start|logs|stop` for its development server. The container mounts only this workspace and has no Docker socket.

These files, the spec, the client, and the prompt are shared fixture inputs. Leave them unchanged. The coordinator checks their hashes before and after every delegated action.
# Feature: article drafts, publishing and edit conflicts

This extends the RealWorld backend spec. Everything in the base spec still holds, and the original 13 Hurl files must keep passing. The acceptance tests for this feature are in `hurl/drafts.hurl` and `hurl/errors_drafts.hurl`. As with the base spec, where the prose and the suite disagree, the suite wins.

## Article fields
[... 376 more lines]
```

</details>

```sh
$ /bin/zsh -c 'find Application Config -type f | sort && cat App.cabal Config/Routes.hs Config/Config.hs Application/Schema.sql Main.hs Dockerfile && cat harness/ihp.sh'
```
<details><summary>output (exit 1)</summary>

```
Application/Fixtures.sql
Application/Helper/Controller.hs
Application/Helper/View.hs
Application/Migration/.gitkeep
Application/Schema.sql
Application/Script/Prelude.hs
Config/Config.hs
Config/nix/haskell-packages/.keep
Config/nix/hosts/production/configuration.nix
Config/nix/hosts/production/hardware-configuration.nix
Config/nix/hosts/production/host.nix
Config/nix/nixpkgs-config.nix
-- This file is only a stub file, please see default.nix for adding dependencies.
--
-- Learn more about dependency management in IHP: https://ihp.digitallyinduced.com/Guide/package-management.html
--
-- If you're looking at this file because you're trying to integrate a HLS or other tooling with your IHP project, check out the documentation on Editors and Tooling: https://ihp.digitallyinduced.com/Guide/editors.html
--
-- This cabal file is inside your project as some haskell tools only work when there's a cabal file. It's not actually used for anything besides providing support for haskell tools.
--

name:                App
version:             0.1.0.0
-- synopsis:
-- description:
license:             AllRightsReserved
license-file:        LICENSE
author:              Developers
maintainer:          developers@example.com
-- copyright:
-- category:
build-type:          Simple
cabal-version:       >=1.10

executable App
  main-is:             Main.hs
  -- other-modules:
  -- other-extensions:
  build-depends:
  	ihp,
[... 72 more lines]
```

</details>

```sh
$ /bin/zsh -c 'cat flake.nix && cat harness/check-all.sh && cat harness/check-api.sh && cat realworld_spec/api/hurl/auth.hurl'
```
<details><summary>output (exit 0)</summary>

```
{
    inputs = {
        ihp.url = "github:digitallyinduced/ihp/v1.6";
        nixpkgs.follows = "ihp/nixpkgs";
        nixpkgs-nixos.follows = "ihp/nixpkgs-nixos";
        flake-parts.follows = "ihp/flake-parts";
        devenv.follows = "ihp/devenv";
        systems.follows = "ihp/systems";
        devenv-root = {
            url = "file+file:///dev/null";
            flake = false;
        };
    };

    outputs = inputs@{ self, nixpkgs, nixpkgs-nixos, ihp, flake-parts, systems, ... }:
        flake-parts.lib.mkFlake { inherit inputs; } {

            systems = import systems;
            imports = [ ihp.flakeModules.default ];

            perSystem = { pkgs, self', ... }: {
                ihp = {
                    appName = "app"; # Change this to your project name
                    enable = true;
                    projectPath = ./.;
                    packages = with pkgs; [
                        z3
                    ];
                    haskellPackages = p: with p; [
                        # Haskell dependencies go here
                        p.ihp
                        liquidhaskell
                        # IHP builds app-lib with this list, where the proof plugin needs Z3.
                        pkgs.z3
                        base
                        wai
                        text
                        # ihp-mail           # Email support: https://ihp.digitallyinduced.com/Guide/mail.html
                        # ihp-datasync       # Real-time DataSync
                        # ihp-job-dashboard  # Job dashboard UI
[... 350 more lines]
```

</details>

```sh
$ /bin/zsh -c "cat harness/ihp.sh && cat AGENTS.md && cat realworld_spec/api/hurl/run-hurl-tests.sh && rg -n '"'^(GET|POST|PUT|DELETE)|HTTP [0-9]|jsonpath'"' realworld_spec/api/hurl/*.hurl | tail -100"
```
<details><summary>output (exit 0)</summary>

````
#!/usr/bin/env bash
set -euo pipefail
root="$(cd "$(dirname "$0")/.." && pwd)"
action="${1:?usage: harness/ihp.sh run COMMAND...|build|start|logs|stop}"
shift
case "$action" in
  run) exec python3 "$root/harness/check-client.py" ihp-run 4104 "$@";;
  build|start|logs|stop) exec python3 "$root/harness/check-client.py" "ihp-$action" 4104 "$@";;
  *) exit 2;;
esac
# Hoogle

When you need to find functions, look up type signatures, discover data structures, or read documentation for any Haskell package used in this project, use Hoogle. It indexes all packages from `flake.nix`, so it's the primary way to explore available APIs and read Hackage-style documentation without leaving the dev environment.

```bash
hoogle search "Text -> ByteString"   # Search by type signature, function name, or data type
# Hoogle web UI at http://localhost:8002 - browse and read full Hackage docs for all project packages
```

# SQL

Use `sqlQueryTyped [typedSql| ... |]` / `sqlExecTyped [typedSql| ... |]` for application SQL. Raw `sqlQuery` is disallowed for normal app queries because it bypasses Postgres type inference and can hide decoder mismatches like `count(*)` returning `int8`. Only use raw/unsafe SQL for narrow cases where typed SQL cannot work, and leave a comment explaining why.

# Migrations

When you create a migration in `Application/Migration/`, set the revision prefix from the **current Unix timestamp** — run `date +%s` and use that exact number, then add a description: `Application/Migration/$(date +%s)-<description>.sql`. **Never hand-pick or round the number** (e.g. taking the latest revision and bumping it to a round value). IHP records only the numeric revision in `schema_migrations`, so if two migrations share a revision — which happens easily when parallel branches both round to the same "nice" number — IHP runs ONE and silently SKIPS the other. The skipped migration's columns/tables never get created while the merged code expects them, so the next deploy fails every affected query with `column … does not exist`. A raw `date +%s` is second-precise and monotonic, so parallel branches always get distinct, correctly-ordered revisions. If a duplicate still slips through, repair it with an idempotent migration at a fresh unique revision that re-applies whichever side was skipped — don't renumber a migration that may already have run somewhere.

# Tests

Run the full project test suite with:

```bash
nix flake check --impure
```

Use this command as the canonical verification step before handing off changes that affect application behavior, SQL, generated code, Nix configuration, dependencies, or CI. For fast local iteration, focused GHCi checks are fine, but `nix flake check --impure` is the full project check.
#!/usr/bin/env bash
set -euo pipefail

DIR="$(cd "$(dirname "$0")" && pwd)"
[... 115 more lines]
````

</details>

**Agent:**

The scaffold has no product code yet. I’ll use IHP’s controller routing and schema for the API, and check the framework APIs before adding the shared socket and export paths.

```sh
$ /bin/zsh -c "harness/ihp.sh run hoogle search 'Controller'"
```
<details><summary>output (exit 0)</summary>

```
warning: not writing modified lock file of flake 'path:/work/app':
• Updated input 'devenv-root':
    'file:///dev/null?narHash=sha256-d6xi4mKdjkX2JFicDIv5niSzpyI0m/Hnm8GGAIU04kY%3D'
  → 'file:///work/app/.devenv/root?narHash=sha256-RScnLzLSmvahu0uqPsszHjjw2EisOaZSUbuoPh7DTBk%3D'
Running tasks     devenv:enterShell

Running           devenv:files:cleanup
Succeeded         devenv:files:cleanup (2.28ms)
Running           devenv:enterShell
Succeeded         devenv:enterShell (3.37ms)
Running           devenv:enterTest
No command        devenv:enterTest
1 Skipped, 2 Succeeded
IHP.ControllerSupport class (Show controller, Eq controller) => Controller controller
module IHP.LoginSupport.Helper.Controller
module IHP.IDE.CodeGen.Controller
module IHP.IDE.Data.Controller
module IHP.IDE.Logs.Controller
module IHP.IDE.ToolServer.Helper.Controller
module IHP.ControllerSupport
IHP.ControllerSupport type ControllerContext = Request
module IHP.FileStorage.ControllerFunctions
module IHP.Pagination.ControllerFunctions
-- plus more results not shown, pass --count=20 to see more
```

</details>

```sh
$ /bin/zsh -c "harness/ihp.sh run hoogle search --count=30 'IHP.RouterSupport' && harness/ihp.sh run hoogle search --count=30 'IHP.Server' && harness/ihp.sh run hoogle search --count=30 'websockets'"
```
<details><summary>output (exit 0)</summary>

```
warning: not writing modified lock file of flake 'path:/work/app':
• Updated input 'devenv-root':
    'file:///dev/null?narHash=sha256-d6xi4mKdjkX2JFicDIv5niSzpyI0m/Hnm8GGAIU04kY%3D'
  → 'file:///work/app/.devenv/root?narHash=sha256-RScnLzLSmvahu0uqPsszHjjw2EisOaZSUbuoPh7DTBk%3D'
Running tasks     devenv:enterShell

Running           devenv:files:cleanup
Succeeded         devenv:files:cleanup (5.28ms)
Running           devenv:enterShell
Succeeded         devenv:enterShell (3.37ms)
Running           devenv:enterTest
No command        devenv:enterTest
1 Skipped, 2 Succeeded
module IHP.RouterSupport
warning: not writing modified lock file of flake 'path:/work/app':
• Updated input 'devenv-root':
    'file:///dev/null?narHash=sha256-d6xi4mKdjkX2JFicDIv5niSzpyI0m/Hnm8GGAIU04kY%3D'
  → 'file:///work/app/.devenv/root?narHash=sha256-RScnLzLSmvahu0uqPsszHjjw2EisOaZSUbuoPh7DTBk%3D'
Running tasks     devenv:enterShell

Running           devenv:files:cleanup
Succeeded         devenv:files:cleanup (2.65ms)
Running           devenv:enterShell
Succeeded         devenv:enterShell (2.87ms)
Running           devenv:enterTest
No command        devenv:enterTest
1 Skipped, 2 Succeeded
module IHP.Server
IHP.IDE.ToolServer.Layout serverIcon :: Markup
IHP.AutoRefresh getOrCreateAutoRefreshServer :: (?request :: Request) => IO (IORef AutoRefreshServer)
IHP.AutoRefresh globalAutoRefreshServerVar :: MVar (Maybe (IORef AutoRefreshServer))
IHP.AutoRefresh.Types data AutoRefreshServer
IHP.AutoRefresh.Types AutoRefreshServer :: [Subscription] -> [AutoRefreshSession] -> !Set Text -> PGListener -> AutoRefreshServer
IHP.AutoRefresh.Types newAutoRefreshServer :: PGListener -> AutoRefreshServer
module IHP.IDE.LiveReloadNotificationServer
IHP.IDE.PortConfig toolServerPort :: PortConfig -> !PortNumber
module IHP.IDE.StatusServer
IHP.IDE.StatusServer clearStatusServer :: IORef [ByteString] -> IORef [ByteString] -> Clients -> IO ()
IHP.IDE.StatusServer withStatusServer :: (?context :: Context) => IORef Bool -> (MVar () -> MVar (MVar ()) -> IORef [ByteString] -> IORef [ByteString] -> Clients -> IO a) -> IO a
module IHP.IDE.ToolServer
[... 32 more lines]
```

</details>

```sh
$ /bin/zsh -c "harness/ihp.sh run sh -c 'ghc-pkg field ihp import-dirs | head; which hoogle; hoogle search --count=15 \"CustomRoute\"'"
```
<details><summary>output (exit 0)</summary>

```
warning: not writing modified lock file of flake 'path:/work/app':
• Updated input 'devenv-root':
    'file:///dev/null?narHash=sha256-d6xi4mKdjkX2JFicDIv5niSzpyI0m/Hnm8GGAIU04kY%3D'
  → 'file:///work/app/.devenv/root?narHash=sha256-RScnLzLSmvahu0uqPsszHjjw2EisOaZSUbuoPh7DTBk%3D'
Running tasks     devenv:enterShell

Running           devenv:files:cleanup
Succeeded         devenv:files:cleanup (2.76ms)
Running           devenv:enterShell
Succeeded         devenv:enterShell (2.96ms)
Running           devenv:enterTest
No command        devenv:enterTest
1 Skipped, 2 Succeeded
import-dirs: /nix/store/yndj0c9ygzjp9bbyf8m76vvfpgycn9i6-ihp-1.6.0/lib/ghc-9.10.3/lib/aarch64-linux-ghc-9.10.3-8de3/ihp-1.6.0-KmerG64wamZIOmRxRr7595
/nix/store/zvjdsagcg5nh6kafh4741m2jq6j7yjh3-ghc-9.10.3-with-packages/bin/hoogle
IHP.RouterSupport customRoutes :: AutoRoute controller => Parser controller
```

</details>

```sh
$ /bin/zsh -c "harness/ihp.sh run hoogle search --count=50 'IHP.Server run' && harness/ihp.sh run hoogle search --count=50 'FrameworkConfig -> Application' && harness/ihp.sh run hoogle search --count=30 'Middleware'"
```
<details><summary>output (exit 0)</summary>

```
warning: not writing modified lock file of flake 'path:/work/app':
• Updated input 'devenv-root':
    'file:///dev/null?narHash=sha256-d6xi4mKdjkX2JFicDIv5niSzpyI0m/Hnm8GGAIU04kY%3D'
  → 'file:///work/app/.devenv/root?narHash=sha256-RScnLzLSmvahu0uqPsszHjjw2EisOaZSUbuoPh7DTBk%3D'
Running tasks     devenv:enterShell

Running           devenv:files:cleanup
Succeeded         devenv:files:cleanup (6.54ms)
Running           devenv:enterShell
Succeeded         devenv:enterShell (4.44ms)
Running           devenv:enterTest
No command        devenv:enterTest
1 Skipped, 2 Succeeded
IHP.IDE.ToolServer runToolServer :: (?context :: Context) => ToolServerApplication -> State -> IO ()
warning: not writing modified lock file of flake 'path:/work/app':
• Updated input 'devenv-root':
    'file:///dev/null?narHash=sha256-d6xi4mKdjkX2JFicDIv5niSzpyI0m/Hnm8GGAIU04kY%3D'
  → 'file:///work/app/.devenv/root?narHash=sha256-RScnLzLSmvahu0uqPsszHjjw2EisOaZSUbuoPh7DTBk%3D'
Running tasks     devenv:enterShell

Running           devenv:files:cleanup
Succeeded         devenv:files:cleanup (2.58ms)
Running           devenv:enterShell
Succeeded         devenv:enterShell (2.57ms)
Running           devenv:enterTest
No command        devenv:enterTest
1 Skipped, 2 Succeeded
IHP.ControllerSupport startWebSocketAppAndFailOnHTTP :: forall webSocketApp application . (?request :: Request, ?respond :: Respond, InitControllerContext application, ?application :: application, Typeable application, WSApp webSocketApp) => webSocketApp -> Application
IHP.RouterSupport runAction' :: forall application controller . (Controller controller, InitControllerContext application, ?application :: application, Typeable application, Typeable controller) => controller -> Application
Unsafe.Coerce unsafeCoerce :: a -> b
Unsafe.Coerce unsafeCoerceUnlifted :: forall (a :: UnliftedType) (b :: UnliftedType) . a -> b
Unsafe.Coerce unsafeCoerceAddr :: forall (a :: TYPE 'AddrRep) (b :: TYPE 'AddrRep) . a -> b
Unsafe.Coerce unsafeCoerce# :: a -> b
GHC.Exts unsafeCoerce# :: a -> b
Basement.Compat.Primitive unsafeCoerce# :: a -> b
GHC.Internal.Exts unsafeCoerce# :: forall (r1 :: RuntimeRep) (r2 :: RuntimeRep) (a :: TYPE r1) (b :: TYPE r2) . a -> b
GHC.Internal.Unsafe.Coerce unsafeCoerce :: a -> b
GHC.Internal.Unsafe.Coerce unsafeCoerceUnlifted :: forall (a :: UnliftedType) (b :: UnliftedType) . a -> b
GHC.Internal.Unsafe.Coerce unsafeCoerceAddr :: forall (a :: TYPE 'AddrRep) (b :: TYPE 'AddrRep) . a -> b
GHC.Internal.Unsafe.Coerce unsafeCoerce# :: a -> b
[... 82 more lines]
```

</details>

```sh
$ /bin/zsh -c "harness/ihp.sh run hoogle search --count=30 'respondJson' && harness/ihp.sh run hoogle search --count=30 'renderJson' && harness/ihp.sh run hoogle search --count=30 'requestBody' && harness/ihp.sh run hoogle search --count=30 'route'"
```
<details><summary>output (exit 0)</summary>

```
warning: not writing modified lock file of flake 'path:/work/app':
• Updated input 'devenv-root':
    'file:///dev/null?narHash=sha256-d6xi4mKdjkX2JFicDIv5niSzpyI0m/Hnm8GGAIU04kY%3D'
  → 'file:///work/app/.devenv/root?narHash=sha256-RScnLzLSmvahu0uqPsszHjjw2EisOaZSUbuoPh7DTBk%3D'
Running tasks     devenv:enterShell

Running           devenv:files:cleanup
Succeeded         devenv:files:cleanup (3.77ms)
Running           devenv:enterShell
Succeeded         devenv:enterShell (3.13ms)
Running           devenv:enterTest
No command        devenv:enterTest
1 Skipped, 2 Succeeded
No results found
warning: not writing modified lock file of flake 'path:/work/app':
• Updated input 'devenv-root':
    'file:///dev/null?narHash=sha256-d6xi4mKdjkX2JFicDIv5niSzpyI0m/Hnm8GGAIU04kY%3D'
  → 'file:///work/app/.devenv/root?narHash=sha256-RScnLzLSmvahu0uqPsszHjjw2EisOaZSUbuoPh7DTBk%3D'
Running tasks     devenv:enterShell

Running           devenv:files:cleanup
Succeeded         devenv:files:cleanup (3.73ms)
Running           devenv:enterShell
Succeeded         devenv:enterShell (4.22ms)
Running           devenv:enterTest
No command        devenv:enterTest
1 Skipped, 2 Succeeded
GHC.Utils.Json renderJSON :: JsonDoc -> SDoc
Distribution.Utils.Json renderJson :: Json -> ByteString
Hackage.Security.JSON renderJSON :: ToJSON WriteJSON a => RepoLayout -> a -> ByteString
Hackage.Security.Server renderJSON :: ToJSON WriteJSON a => RepoLayout -> a -> ByteString
IHP.Controller.Render renderJson :: (?request :: Request, ?respond :: Respond, ToJSON json) => json -> IO ResponseReceived
Hackage.Security.JSON renderJSON_NoLayout :: ToJSON Identity a => a -> ByteString
Hackage.Security.Server renderJSON_NoLayout :: ToJSON Identity a => a -> ByteString
IHP.Controller.Render renderJson' :: (?request :: Request, ?respond :: Respond) => ResponseHeaders -> ToJSON json => json -> IO ResponseReceived
IHP.Controller.Render renderJsonWithStatusCode :: (?request :: Request, ?respond :: Respond, ToJSON json) => Status -> json -> IO ResponseReceived
warning: not writing modified lock file of flake 'path:/work/app':
• Updated input 'devenv-root':
    'file:///dev/null?narHash=sha256-d6xi4mKdjkX2JFicDIv5niSzpyI0m/Hnm8GGAIU04kY%3D'
  → 'file:///work/app/.devenv/root?narHash=sha256-RScnLzLSmvahu0uqPsszHjjw2EisOaZSUbuoPh7DTBk%3D'
[... 84 more lines]
```

</details>

```sh
$ /bin/zsh -c "harness/ihp.sh run hoogle search --count=50 'AutoRoute' && harness/ihp.sh run hoogle search --count=30 'WSApp' && harness/ihp.sh run hoogle search --count=30 'sqlQueryTyped'"
```
<details><summary>output (exit 0)</summary>

```
warning: not writing modified lock file of flake 'path:/work/app':
• Updated input 'devenv-root':
    'file:///dev/null?narHash=sha256-d6xi4mKdjkX2JFicDIv5niSzpyI0m/Hnm8GGAIU04kY%3D'
  → 'file:///work/app/.devenv/root?narHash=sha256-RScnLzLSmvahu0uqPsszHjjw2EisOaZSUbuoPh7DTBk%3D'
Running tasks     devenv:enterShell

Running           devenv:files:cleanup
Succeeded         devenv:files:cleanup (3.02ms)
Running           devenv:enterShell
Succeeded         devenv:enterShell (2.61ms)
Running           devenv:enterTest
No command        devenv:enterTest
1 Skipped, 2 Succeeded
IHP.RouterSupport class Data controller => AutoRoute controller
IHP.RouterSupport autoRoute :: AutoRoute controller => Parser controller
IHP.RouterSupport autoRouteWithIdType :: (AutoRoute controller, ?request :: Request, ?respond :: Respond, Data idType) => (ByteString -> Maybe idType) -> Parser controller
IHP.Router.Types data TypedAutoRouteError
IHP.RouterSupport buildAutoRouteMap :: (AutoRoute controller, Controller controller, InitControllerContext application, Typeable application, Typeable controller) => HashMap ByteString (application -> Application)
warning: not writing modified lock file of flake 'path:/work/app':
• Updated input 'devenv-root':
    'file:///dev/null?narHash=sha256-d6xi4mKdjkX2JFicDIv5niSzpyI0m/Hnm8GGAIU04kY%3D'
  → 'file:///work/app/.devenv/root?narHash=sha256-RScnLzLSmvahu0uqPsszHjjw2EisOaZSUbuoPh7DTBk%3D'
Running tasks     devenv:enterShell

Running           devenv:files:cleanup
Succeeded         devenv:files:cleanup (3.57ms)
Running           devenv:enterShell
Succeeded         devenv:enterShell (3.01ms)
Running           devenv:enterTest
No command        devenv:enterTest
1 Skipped, 2 Succeeded
IHP.WebSocket class WSApp state
IHP.AutoRefresh data AutoRefreshWSApp
IHP.WebSocket startWSApp :: (WSApp state, ?request :: Request, ?modelContext :: ModelContext) => state -> Connection -> IO ()
warning: not writing modified lock file of flake 'path:/work/app':
• Updated input 'devenv-root':
    'file:///dev/null?narHash=sha256-d6xi4mKdjkX2JFicDIv5niSzpyI0m/Hnm8GGAIU04kY%3D'
  → 'file:///work/app/.devenv/root?narHash=sha256-RScnLzLSmvahu0uqPsszHjjw2EisOaZSUbuoPh7DTBk%3D'
Running tasks     devenv:enterShell

[... 8 more lines]
```

</details>

```sh
$ /bin/zsh -c "harness/ihp.sh run sh -c 'find /nix/store -path \"*/IHP/RouterSupport.hs\" -o -path \"*/IHP/WebSocket.hs\" 2>/dev/null | head'"
```
<details><summary>output (exit 0)</summary>

```
warning: not writing modified lock file of flake 'path:/work/app':
• Updated input 'devenv-root':
    'file:///dev/null?narHash=sha256-d6xi4mKdjkX2JFicDIv5niSzpyI0m/Hnm8GGAIU04kY%3D'
  → 'file:///work/app/.devenv/root?narHash=sha256-RScnLzLSmvahu0uqPsszHjjw2EisOaZSUbuoPh7DTBk%3D'
Running tasks     devenv:enterShell

Running           devenv:files:cleanup
Succeeded         devenv:files:cleanup (2.96ms)
Running           devenv:enterShell
Succeeded         devenv:enterShell (2.88ms)
Running           devenv:enterTest
No command        devenv:enterTest
1 Skipped, 2 Succeeded
/nix/store/bg95c3k9x9ihrinjy1l991c1rp1k86xw-source/ihp/IHP/RouterSupport.hs
/nix/store/bg95c3k9x9ihrinjy1l991c1rp1k86xw-source/ihp/IHP/WebSocket.hs
/nix/store/c4nshrzgy5nld94likhl2j4jqc56bkni-source/IHP/RouterSupport.hs
/nix/store/c4nshrzgy5nld94likhl2j4jqc56bkni-source/IHP/WebSocket.hs
```

</details>

```sh
$ /bin/zsh -c "harness/ihp.sh run sh -c 'sed -n \"1,260p\" /nix/store/c4nshrzgy5nld94likhl2j4jqc56bkni-source/IHP/RouterSupport.hs; sed -n \"1,200p\" /nix/store/c4nshrzgy5nld94likhl2j4jqc56bkni-source/IHP/WebSocket.hs'"
```
<details><summary>output (exit 0)</summary>

```
warning: not writing modified lock file of flake 'path:/work/app':
• Updated input 'devenv-root':
    'file:///dev/null?narHash=sha256-d6xi4mKdjkX2JFicDIv5niSzpyI0m/Hnm8GGAIU04kY%3D'
  → 'file:///work/app/.devenv/root?narHash=sha256-RScnLzLSmvahu0uqPsszHjjw2EisOaZSUbuoPh7DTBk%3D'
Running tasks     devenv:enterShell

Running           devenv:files:cleanup
Succeeded         devenv:files:cleanup (4.59ms)
Running           devenv:enterShell
Succeeded         devenv:enterShell (5.30ms)
Running           devenv:enterTest
No command        devenv:enterTest
1 Skipped, 2 Succeeded
{-# LANGUAGE AllowAmbiguousTypes, UndecidableInstances, LambdaCase, ScopedTypeVariables #-}
module IHP.RouterSupport (
CanRoute (..)
, HasPath (..)
, AutoRoute (..)
, runAction
, runAction'
, get
, post
, startPage
, frontControllerToWAIApp
, withPrefix
, FrontController (..)
, defaultRouter
, parseRoute
, catchAll
, mountFrontController
, createAction
, updateAction
, urlTo
, parseUUID
, parseId
, parseIntegerId
, remainingText
, parseText
, webSocketApp
, webSocketAppWithCustomPath
[... 343 more lines]
```

</details>

```sh
$ /bin/zsh -c "harness/ihp.sh run sh -c 'rg -n \""'^get ::|''^post ::|''^catchAll ::|''^webSocket|''^onlyAllowMethods|''^remainingText|''^withPrefix" /nix/store/c4nshrzgy5nld94likhl2j4jqc56bkni-source/IHP/RouterSupport.hs; sed -n "570,760p" /nix/store/c4nshrzgy5nld94likhl2j4jqc56bkni-source/IHP/RouterSupport.hs; rg -n "customMiddleware|option" /nix/store/c4nshrzgy5nld94likhl2j4jqc56bkni-source/IHP/FrameworkConfig.hs | head -30'"'"
```
<details><summary>output (exit 0)</summary>

```
warning: not writing modified lock file of flake 'path:/work/app':
• Updated input 'devenv-root':
    'file:///dev/null?narHash=sha256-d6xi4mKdjkX2JFicDIv5niSzpyI0m/Hnm8GGAIU04kY%3D'
  → 'file:///work/app/.devenv/root?narHash=sha256-RScnLzLSmvahu0uqPsszHjjw2EisOaZSUbuoPh7DTBk%3D'
Running tasks     devenv:enterShell

Running           devenv:files:cleanup
Succeeded         devenv:files:cleanup (2.74ms)
Running           devenv:enterShell
Succeeded         devenv:enterShell (2.49ms)
Running           devenv:enterTest
No command        devenv:enterTest
1 Skipped, 2 Succeeded
sh: line 1: rg: command not found
actionPrefixText
    | "Web." `Text.isPrefixOf` moduleName = "/"
    | "IHP." `Text.isPrefixOf` moduleName = "/"
    | Text.null moduleName = "/"
    | otherwise = "/" <> Text.toLower (getPrefix moduleName) <> "/"
    where
        moduleName :: Text
        moduleName = Text.pack $ Typeable.typeOf (error "unreachable" :: controller)
                |> Typeable.typeRepTyCon
                |> Typeable.tyConModule

        getPrefix :: Text -> Text
        getPrefix t = fst (Text.breakOn "." t)
{-# NOINLINE actionPrefixText #-}

-- | Strips the "Action" suffix from action names
--
-- >>> stripActionSuffixByteString "ShowUserAction"
-- "ShowUser"
--
-- >>> stripActionSuffixByteString "UsersAction"
-- "UsersAction"
--
-- >>> stripActionSuffixByteString "User"
-- "User"
stripActionSuffixByteString :: ByteString -> ByteString
[... 166 more lines]
```

</details>

```sh
$ /bin/zsh -c "harness/ihp.sh run sh -c 'grep -nE \""'^(get|post|catchAll|webSocketApp|webSocketRoute|onlyAllowMethods|remainingText|withPrefix) ::" /nix/store/c4nshrzgy5nld94likhl2j4jqc56bkni-source/IHP/RouterSupport.hs'"'"
```
<details><summary>output (exit 0)</summary>

```
warning: not writing modified lock file of flake 'path:/work/app':
• Updated input 'devenv-root':
    'file:///dev/null?narHash=sha256-d6xi4mKdjkX2JFicDIv5niSzpyI0m/Hnm8GGAIU04kY%3D'
  → 'file:///work/app/.devenv/root?narHash=sha256-RScnLzLSmvahu0uqPsszHjjw2EisOaZSUbuoPh7DTBk%3D'
Running tasks     devenv:enterShell

Running           devenv:files:cleanup
Succeeded         devenv:files:cleanup (6.48ms)
Running           devenv:enterShell
Succeeded         devenv:enterShell (3.95ms)
Running           devenv:enterTest
No command        devenv:enterTest
1 Skipped, 2 Succeeded
800:get :: (Controller action
830:post :: (Controller action
872:onlyAllowMethods :: (?request :: Request, ?respond :: Respond) => [StdMethod] -> Parser ()
889:webSocketApp :: forall webSocketApp application.
974:webSocketRoute :: forall webSocketApp application.
1229:catchAll :: forall action application. (Controller action, InitControllerContext application, Typeable action, ?application :: application, Typeable application, Data action) => action -> ControllerRoute application
1256:remainingText :: Parser Text
```

</details>

```sh
$ /bin/zsh -c "harness/ihp.sh run sh -c 'sed -n \"790,850p\" /nix/store/c4nshrzgy5nld94likhl2j4jqc56bkni-source/IHP/RouterSupport.hs; sed -n \"880,1015p\" /nix/store/c4nshrzgy5nld94likhl2j4jqc56bkni-source/IHP/RouterSupport.hs; sed -n \"1220,1270p\" /nix/store/c4nshrzgy5nld94likhl2j4jqc56bkni-source/IHP/RouterSupport.hs'"
```
<details><summary>output (exit 0)</summary>

```
warning: not writing modified lock file of flake 'path:/work/app':
• Updated input 'devenv-root':
    'file:///dev/null?narHash=sha256-d6xi4mKdjkX2JFicDIv5niSzpyI0m/Hnm8GGAIU04kY%3D'
  → 'file:///work/app/.devenv/root?narHash=sha256-RScnLzLSmvahu0uqPsszHjjw2EisOaZSUbuoPh7DTBk%3D'
Running tasks     devenv:enterShell

Running           devenv:files:cleanup
Succeeded         devenv:files:cleanup (2.74ms)
Running           devenv:enterShell
Succeeded         devenv:enterShell (3.10ms)
Running           devenv:enterTest
No command        devenv:enterTest
1 Skipped, 2 Succeeded
-- __Example:__
--
-- > instance FrontController WebApplication where
-- >     controllers = [
-- >             get "/my-custom-page" NewSessionAction
-- >         ]
--
-- The request @GET \/my-custom-page@ is now executing NewSessionAction
--
-- Also see 'post'.
get :: (Controller action
    , InitControllerContext application
    , ?application :: application
    , Typeable application
    , Typeable action
    ) => ByteString -> action -> ControllerRoute application
get path action = ControllerRouteParser $ do
    string path
    pure $ \waiRequest waiRespond -> do
        wrapRouterException do
            case parseMethod (requestMethod waiRequest) of
                Right GET -> pure ()
                Right HEAD -> pure ()
                Right method -> throwIO UnexpectedMethodException { allowedMethods = [GET, HEAD], method }
                Left err -> throwIO BadHttpMethodException { method = err }
        runAction' action waiRequest waiRespond
{-# INLINABLE get #-}
[... 220 more lines]
```

</details>

```sh
$ /bin/zsh -c "harness/ihp.sh run sh -c 'grep -n \"startWebSocketAppAndFailOnHTTP\" /nix/store/c4nshrzgy5nld94likhl2j4jqc56bkni-source/IHP/ControllerSupport.hs; sed -n \"550,605p\" /nix/store/c4nshrzgy5nld94likhl2j4jqc56bkni-source/IHP/ControllerSupport.hs; grep -n \"data RootApplication\\|type RootApplication\" /nix/store/c4nshrzgy5nld94likhl2j4jqc56bkni-source/IHP/*hs'"
```
<details><summary>output (exit 0)</summary>

```
warning: not writing modified lock file of flake 'path:/work/app':
• Updated input 'devenv-root':
    'file:///dev/null?narHash=sha256-d6xi4mKdjkX2JFicDIv5niSzpyI0m/Hnm8GGAIU04kY%3D'
  → 'file:///work/app/.devenv/root?narHash=sha256-RScnLzLSmvahu0uqPsszHjjw2EisOaZSUbuoPh7DTBk%3D'
Running tasks     devenv:enterShell

Running           devenv:files:cleanup
Succeeded         devenv:files:cleanup (4.56ms)
Running           devenv:enterShell
Succeeded         devenv:enterShell (2.52ms)
Running           devenv:enterTest
No command        devenv:enterTest
1 Skipped, 2 Succeeded
25:, startWebSocketAppAndFailOnHTTP
238:{-# INLINE startWebSocketAppAndFailOnHTTP #-}
239:startWebSocketAppAndFailOnHTTP :: forall webSocketApp application. (?request :: Request, ?respond :: Respond, InitControllerContext application, ?application :: application, Typeable application, WebSockets.WSApp webSocketApp) => webSocketApp -> Application
240:startWebSocketAppAndFailOnHTTP initialState = startWebSocketApp @webSocketApp @application initialState (?respond $ responseLBS HTTP.status400 [(hContentType, "text/plain")] "This endpoint is only available via a WebSocket")
/nix/store/c4nshrzgy5nld94likhl2j4jqc56bkni-source/IHP/FrameworkConfig.hs:216:data RootApplication = RootApplication deriving (Eq, Show)
```

</details>

```sh
$ /bin/zsh -c "harness/ihp.sh run sh -c 'grep -R -n -m 5 \"sqlQueryTyped \\[typedSql\" /nix/store/c4nshrzgy5nld94likhl2j4jqc56bkni-source 2>/dev/null | head -20; grep -R -n -m 5 \"CREATE TABLE users\" /nix/store/c4nshrzgy5nld94likhl2j4jqc56bkni-source 2>/dev/null | head -10'"
```
<details><summary>output (exit 0)</summary>

```
warning: not writing modified lock file of flake 'path:/work/app':
• Updated input 'devenv-root':
    'file:///dev/null?narHash=sha256-d6xi4mKdjkX2JFicDIv5niSzpyI0m/Hnm8GGAIU04kY%3D'
  → 'file:///work/app/.devenv/root?narHash=sha256-RScnLzLSmvahu0uqPsszHjjw2EisOaZSUbuoPh7DTBk%3D'
Running tasks     devenv:enterShell

Running           devenv:files:cleanup
Succeeded         devenv:files:cleanup (3.73ms)
Running           devenv:enterShell
Succeeded         devenv:enterShell (2.83ms)
Running           devenv:enterTest
No command        devenv:enterTest
1 Skipped, 2 Succeeded
/nix/store/c4nshrzgy5nld94likhl2j4jqc56bkni-source/IHP/ModelSupport.hs:308:-- > unsafeSqlExec "CREATE TABLE users ()" ()
/nix/store/c4nshrzgy5nld94likhl2j4jqc56bkni-source/IHP/ModelSupport.hs:327:-- > unsafeSqlExecDiscardResult "CREATE TABLE users ()" ()
```

</details>

```sh
$ /bin/zsh -c "harness/ihp.sh run hoogle search --count=30 'query @' && harness/ihp.sh run hoogle search --count=30 'fetchOneOrNothing' && harness/ihp.sh run hoogle search --count=30 'createRecord' && harness/ihp.sh run hoogle search --count=30 'filterWhere'"
```
<details><summary>output (exit 0)</summary>

```
warning: not writing modified lock file of flake 'path:/work/app':
• Updated input 'devenv-root':
    'file:///dev/null?narHash=sha256-d6xi4mKdjkX2JFicDIv5niSzpyI0m/Hnm8GGAIU04kY%3D'
  → 'file:///work/app/.devenv/root?narHash=sha256-RScnLzLSmvahu0uqPsszHjjw2EisOaZSUbuoPh7DTBk%3D'
Running tasks     devenv:enterShell

Running           devenv:files:cleanup
Succeeded         devenv:files:cleanup (4.42ms)
Running           devenv:enterShell
Succeeded         devenv:enterShell (3.50ms)
Running           devenv:enterTest
No command        devenv:enterTest
1 Skipped, 2 Succeeded
package aeson
package base
package bytestring
package containers
package filepath
package lens
package lens-aeson
package mtl
package optparse-applicative
package text
package wreq
package ghc
package Cabal
package Cabal-syntax
package Diff
package HTTP
package HUnit
package OneTuple
package Only
package QuickCheck
package RSA
package SHA
package StateVar
package adjunctions
package ansi-terminal
package ansi-terminal-types
package appar
[... 78 more lines]
```

</details>

```sh
$ /bin/zsh -c "harness/ihp.sh run sh -c 'find /nix/store/c4nshrzgy5nld94likhl2j4jqc56bkni-source -path \"*Job*\" -type f | head -20; grep -R -n -m 3 \"instance Job\" /nix/store/c4nshrzgy5nld94likhl2j4jqc56bkni-source | head -15'"
```
<details><summary>output (exit 0)</summary>

```
warning: not writing modified lock file of flake 'path:/work/app':
• Updated input 'devenv-root':
    'file:///dev/null?narHash=sha256-d6xi4mKdjkX2JFicDIv5niSzpyI0m/Hnm8GGAIU04kY%3D'
  → 'file:///work/app/.devenv/root?narHash=sha256-RScnLzLSmvahu0uqPsszHjjw2EisOaZSUbuoPh7DTBk%3D'
Running tasks     devenv:enterShell

Running           devenv:files:cleanup
Succeeded         devenv:files:cleanup (4.25ms)
Running           devenv:enterShell
Succeeded         devenv:enterShell (2.86ms)
Running           devenv:enterTest
No command        devenv:enterTest
1 Skipped, 2 Succeeded
/nix/store/c4nshrzgy5nld94likhl2j4jqc56bkni-source/IHP/Job/Queue/Fetch.hs
/nix/store/c4nshrzgy5nld94likhl2j4jqc56bkni-source/IHP/Job/Queue/Pool.hs
/nix/store/c4nshrzgy5nld94likhl2j4jqc56bkni-source/IHP/Job/Queue/Result.hs
/nix/store/c4nshrzgy5nld94likhl2j4jqc56bkni-source/IHP/Job/Queue/STM.hs
/nix/store/c4nshrzgy5nld94likhl2j4jqc56bkni-source/IHP/Job/Queue/StatusInstances.hs
/nix/store/c4nshrzgy5nld94likhl2j4jqc56bkni-source/IHP/Job/Queue/Watch.hs
/nix/store/c4nshrzgy5nld94likhl2j4jqc56bkni-source/IHP/Job/Queue.hs
/nix/store/c4nshrzgy5nld94likhl2j4jqc56bkni-source/IHP/Job/Runner/MainLoop.hs
/nix/store/c4nshrzgy5nld94likhl2j4jqc56bkni-source/IHP/Job/Runner/WorkerLoop.hs
/nix/store/c4nshrzgy5nld94likhl2j4jqc56bkni-source/IHP/Job/Runner.hs
/nix/store/c4nshrzgy5nld94likhl2j4jqc56bkni-source/IHP/Job/Types/BackoffStrategy.hs
/nix/store/c4nshrzgy5nld94likhl2j4jqc56bkni-source/IHP/Job/Types/Class.hs
/nix/store/c4nshrzgy5nld94likhl2j4jqc56bkni-source/IHP/Job/Types/Status.hs
/nix/store/c4nshrzgy5nld94likhl2j4jqc56bkni-source/IHP/Job/Types/Worker.hs
/nix/store/c4nshrzgy5nld94likhl2j4jqc56bkni-source/IHP/Job/Types.hs
/nix/store/c4nshrzgy5nld94likhl2j4jqc56bkni-source/Test/Test/JobQueueSpec.hs
```

</details>

```sh
$ /bin/zsh -c "cat WorkerMain.hs && harness/ihp.sh run sh -c 'sed -n \"1,160p\" /nix/store/c4nshrzgy5nld94likhl2j4jqc56bkni-source/IHP/Job/Types/Class.hs; sed -n \"1,110p\" /nix/store/c4nshrzgy5nld94likhl2j4jqc56bkni-source/IHP/Job/Runner.hs'"
```
<details><summary>output (exit 0)</summary>

```
warning: not writing modified lock file of flake 'path:/work/app':
• Updated input 'devenv-root':
    'file:///dev/null?narHash=sha256-d6xi4mKdjkX2JFicDIv5niSzpyI0m/Hnm8GGAIU04kY%3D'
  → 'file:///work/app/.devenv/root?narHash=sha256-RScnLzLSmvahu0uqPsszHjjw2EisOaZSUbuoPh7DTBk%3D'
Running tasks     devenv:enterShell

Running           devenv:files:cleanup
Succeeded         devenv:files:cleanup (2.82ms)
Running           devenv:enterShell
Succeeded         devenv:enterShell (2.89ms)
Running           devenv:enterTest
No command        devenv:enterTest
1 Skipped, 2 Succeeded
{-# LANGUAGE AllowAmbiguousTypes #-}
module IHP.Job.Types.Class
( Job (..)
) where

import IHP.Prelude
import IHP.FrameworkConfig.Types (FrameworkConfig)
import IHP.Job.Types.BackoffStrategy (BackoffStrategy (..))

class Job job where
    perform :: (?modelContext :: ModelContext, ?context :: FrameworkConfig) => job -> IO ()

    maxAttempts :: (?job :: job) => Int
    maxAttempts = 10

    timeoutInMicroseconds :: Maybe Int
    timeoutInMicroseconds = Nothing

    -- | While jobs are typically fetch using pg_notiy, we have to poll the queue table
    -- periodically to catch jobs with a @run_at@ in the future
    --
    -- By default we only poll every minute
    queuePollInterval :: Int
    queuePollInterval = 60 * 1000000

    -- | How many jobs of this type can be executed at the same time
    --
[... 34 more lines]
```

</details>

