# Pitfalls

Each item is a problem that earlier AgentMVC runs hit or exposed, with what to do about it or what the harness already does.

## Harness and isolation

- An agent that can read the parent repository, a sibling workdir or the host Docker socket can see answers it should not. Before measured runs, confirm with a disposable probe agent that those accesses fail while `harness/db.sh start` and `stop` still work, and afterwards audit each transcript for reads of another stack's source.
- A reused Codex home, or one with memories on, can carry earlier sessions into a measured run. `tools/one_shot_agent.py` refuses a home that has sessions or lacks `approval_policy = "never"`, `memories = false` and `default_permissions = "workspace-only"`; give any new launcher the same checks and compare config hashes across stacks.
- Agents reach Docker only through the broker in `tools/one_shot_broker.py`, which binds to loopback, maps one distinct token to each stack and accepts only named check and database actions. Add a named action there instead of giving an agent the host Docker socket.
- Any edit to the prompt, harness, broker, client, spec or scaffold changes the common input, and `tools/one_shot_agent.py` refuses to launch against a stale manifest. Refreeze with `tools/one_shot.py freeze`, move old workdirs aside, `prepare` new ones, and keep any launch stopped for the change out of scored effort.
- A harness defect found during a measured session cannot be fixed without invalidating that session's common input. Before freezing, run `tools/one_shot.py preflight` and also drive every broker action each stack will use, including a migration and a restart through the development bridge.
- Shared caches can defeat separate workdirs. Keep every cache per run, as the scored runs did: a workdir-local bundle for Rails, Mix and Hex caches for Phoenix, a Cargo home and target directory for Loco, and a private Nix store for IHP.
- The workspace sandbox denies temp and cache paths outside the workdir, and `tools/one_shot_agent.py` passes the host `TMPDIR` through, so Bundler, RuboCop and the first Rust compile failed. Point `TMPDIR` and tool caches inside the workdir, or tell the agent to.
- The development server and the production gate share a port in each stack environment, and Phoenix and IHP agents hit that collision. Stop the development server before running the production gate.
- Host Chromium cannot launch inside the macOS sandbox, and an older Linux image or a CDN download gave the wrong build or timed out. Run browser tests in the Playwright image pinned by `one-shot/harness/Dockerfile.browser`, which skips the browser download.
- Playwright writes `test-results` beside its tests, which failed on the read-only fixture mount. `one-shot/harness/run-live-container.sh` runs the suite from a scratch copy; keep it that way.
- Rails answers a request that lacks `Accept: application/json` with 406, and that missing header broke the seeder, the load generator, the scanner, a smoke test and the demo. Send the header from every new script that calls an app.
- A spec or client bug that surfaces after launch fails every agent for the wrong reason. Validate each new feature with a throwaway implementation on separate ports before freezing, including a deliberately slow variant for polling tests; this caught a Retry-state bug in the live-editing client.
- The original editor in `frontend/src/` adopts every save response, so a late response can overwrite newer state. The one-shot client in `one-shot/frontend/` fixes this and has a browser test for it; build on that client.
- A shared Playwright cache put unrelated local worktree paths into two transcripts, and a regex redaction once stalled on a long build-output line. `tools/scrub.py` handles both now; read scrubbed output before publishing and test scrubber changes on a large sample.

## Measurement

- Agent reports and agent-run checks are not results. Before a run counts, rerun the development and production gates from the finished workdir, starting the app the way the agent's own entry points do.
- Deleting a failed setup attempt hides why a number was rerun. Keep the failed record, fix the cause, and rerun only the affected part.
- `tools/measure.py` silently skips any file whose extension is missing from the stack's `stack.json`, which once dropped every Rails `.jbuilder` view from both the size count and the comprehension reading copy. When you add a stack or a file type, list the extensions in a finished workdir and compare them with what was counted.
- Excluding a directory by name hid Phoenix's real `lib/conduit/` code when only the root `conduit/` alias was meant, and made Phoenix look smaller than Rails. Exclude by exact path, as `tools/one_shot_publish.py` now does, and read the counted file list for missing domain code.
- An agent may copy installer-generated schema into a hand-written migration, which inflates its owned code. Set generated-code rules before launch; this study counts installer queue schema as generated even inside a migration, and reports the cost both ways.
- Uncached agent tokens swing with prompt caching: one comprehension run doubled its count while its total input rose only 5%. Report total input processed as well as uncached input plus output.
- Nonzero command counts include exploratory commands and deliberate server stops, and failed brokered attempts mix code errors with environment and startup errors. Do not read either as a defect count.
- Formatters and languages lay code out differently: Loco averaged 6.7 tokens per line against 8.1 for Rails and 8.8 for Phoenix, and IHP's Haskell lines carry 11 to 13. Compare size in tokens, not lines.
- Agent wall-clock time includes toolchain and browser setup, such as a container per Phoenix `mix` command, Loco compiles, IHP Nix builds and moving Playwright into a Linux container. Do not read it as implementation effort alone.
- A crashed security analyzer can look like a clean scan with 0 findings. If you add a static scan, record analyzer errors as failures.
- An agent that only has the baseline scan cannot see findings its own fix adds; Phoenix's secure headers plug raised a Content-Security-Policy finding aimed at HTML pages. Rescan the final image and judge each new finding against a JSON API.
- Code size reproduced within 4% across runs of one prompt, so size gaps between stacks are reliable. Effort and speed are not; see the prompts section.

## Runtime benchmarks

- The benchmark host is a shared workstation, and identical images drifted by up to about 1.5x between sessions while unrelated work used 3 to 5 of its 18 CPUs. Compare before and after only within one session, claim nothing under 1.5x, and record background CPU for every scenario.
- When endpoints that nobody changed also move, suspect drift. Rerun the baseline image in the same session as a control; this withdrew one claimed Rails slowdown.
- Agents that benchmark in parallel with each other get noisy numbers. Benchmark finished images yourself, one at a time, in at least two nearby rounds in opposite stack order with fresh databases.
- `pg_isready` over the Unix socket can pass against PostgreSQL's temporary init server, which then restarts, and a fresh instance once still refused connections at a 30-second deadline. `tools/one_shot_live_bench.py` probes over TCP with a longer deadline, but the older `tools/bench/bench.py` still probes the socket.
- `foreign_container_cpu_percent_max` also counts the k6 load generator, because Docker gave that container an automatic name. Read it as non-app container activity, not pure background load.
- Passing every gate does not bound SQL work: three IHP apps made 21, about 64 and about 2,081 statements per list request. Record SQL per request, which does not depend on timing, beside every throughput number.
- The socket benchmark sends five saves per second, and sampled backend CPU stayed at or below 4.2% of one CPU. It shows correct delivery, not capacity, so do not rank latency or claim saturation from it.

## Prompts and agent behavior

- Without an explicit rule, an agent may bypass the assigned framework: the first one-shot Loco agent wrote a standalone Axum and SQLx server inside the Loco scaffold. Say in the prompt that the framework must run the production app.
- Under a "fewest tokens" goal, agents drop types at boundaries, such as untyped JSON in Loco and IHP, and hand-roll token signing or password hashing. Ask explicitly for maintained crypto libraries and typed request decoding.
- Single runs are noisy: three IHP runs from one prompt varied 1.65x in agent time and from about 1 to 372 article-list requests per second. Rank prompts on several runs each.
- A prompt with extra expert advice is a different experiment. Give it its own fixture hash and label, and never pool its runs with identical-prompt runs.
- Expert advice can be wrong for the pinned version: preparing the IHP brief caught several sketches that did not compile or named functions that do not exist. Compile every sketch against the pinned toolchain before it goes into a prompt.
- The gates check behavior, not query bounds, rule ownership or proofs. If one of those matters, ask for it in the prompt and measure it yourself.

## Rails

- The Rails production images ran one Puma process, which can use about one of the two CPUs each container gets, and no agent added workers, even when tuning. Set a measured worker count before comparing speed, for example through `WEB_CONCURRENCY`; two workers gave about 1.7x on most endpoints and raised idle memory from 143 to 254 MB.
- Rails 8 expects Solid Queue to have its own database, so using the app database means copying about 2,000 tokens of installer schema into a migration. Classify that migration by comparing its body with the installed gem's template, as `tools/one_shot_publish.py` does; matching an earlier run's filename failed when the date prefix changed.
- On macOS, Solid Queue's forked worker crashed on fork safety during local checks. Keep any workaround scoped to local checks rather than production.
- Faye WebSocket writes must run on the EventMachine loop. The first Rails socket updates never reached subscribers until the agent scheduled its sends there.
- Rails agents install gems in a workdir-local `vendor/bundle`, and a reviewer gate that looked in `vendor/gems` failed before the app ran. `tools/one_shot_independent.py` now uses `vendor/bundle` when it exists.

## Phoenix

- The Phoenix one-shot image ran `mix phx.server` from the full Elixir image, about 1.7 GB, instead of a release. Ask for a release, and do not compare that image's size with other stacks.
- The broker runs Phoenix's toolchain container in `/work/app/conduit`, but the scaffold's `mix.exs` sits at `/work/app`, so agents add a root `conduit/` symlink alias. Align the two in the next frozen fixture; until then, exclude only that exact root path from size counts.
- Sobelow's JSON output needs Jason, which Sobelow's archive does not bundle, so Sobelow once failed silently and would have reported 0 findings. If you run Sobelow, put the project's compiled Jason on its path.
- Phoenix reads `force_ssl` at compile time, so enabling it to clear Sobelow's HTTPS finding broke the HTTP-based production gate. Terminate TLS at a proxy and document that, as the agent did.

## Loco

- Loco's default server-only mode does not run background jobs, so the export check stays pending. Start it with `--server-and-worker`, as the agents' entries and `tools/one_shot_independent.py` do.
- Loco's model and worker generators refuse to run once the migration marker and test module they expect are deleted as leftovers. Keep them if later changes may use the generators, or the agent has to wire files by hand.
- Loco's starter ships user authentication, while Rails and Phoenix start close to empty. Compare owned code, which ignores starter code the agent never changed, as well as whole-app size.
- Rust and Loco have no mainstream equivalent of Brakeman or Sobelow. The environment's Clippy run with warnings denied is the closest static check.
- OSV reports RUSTSEC-2023-0071 in `rsa`, which arrives through `loco-rs` and `jsonwebtoken` and had no fixed release during the study. Check with `cargo tree` and the signing code whether the app uses RSA keys before counting it against the agent.

## IHP

- IHP's `unoptimized-prod-server` Nix target compiles at -O0 and skips IHP's production GHC flags, including `-with-rtsopts` with `-N`, so the server runs Haskell on one core. The scaffold's `flake.nix` builds the image from that target, so IHP runtime numbers so far are a floor; use `optimized-prod-server` with an explicit capability count for speed comparisons.
- The IHP images so far were about 4.4 GB, which reflects their Nix packaging rather than a minimum for IHP, so do not compare that size across stacks yet. IHP's documented Docker output keeps the job worker in a separate image, while this contract needs migrations, worker and server in one.
- A shared Nix store held an earlier app's source where a later agent could read it, even with separate workdirs. Give each run its own Nix store volume cloned from a product-free prewarmed base, about 22.4 GiB each; building that base is not scripted yet.
- LiquidHaskell only checks modules compiled with its plugin, so a refinement's precondition is not enforced at a call site in an unchecked module. Verify each proof with a deliberately false refinement, and put callers inside checked modules if the property matters.
- IHP run 1 set up LiquidHaskell without proving any application rule. Name the invariant you want proved in a module the running app calls; the guided run proved a 0 to 100 room bound and showed a false 0 to 99 bound failing.
- LiquidHaskell needs Z3 on the app-lib compiler PATH, which meant adding Z3 to the Haskell dependency list, and proof modules need an explicit Prelude import under IHP's compiler extensions. Keep both when you rebuild the scaffold.
- IHP's app-lib source scanner read the frozen `.scaffold` copy until fixture directories were ignored, and a product-free app has no `RunJobs` binary, so startup now runs it only when present. Keep both fixes when you rebuild the IHP scaffold or harness.
- `IHP_MIGRATION_DIR` needs a trailing slash, and a development bridge without it stopped an agent run after 39 minutes before the app ever started. Preflight must apply a migration through the same bridge the agent uses.
- `harness/ihp.sh start` builds and starts the unoptimized production server, with no file watcher or hot reload. Tell agents to batch edits and build at milestones, and expect Nix build time inside agent time.
- The pinned IHP 1.6 schema parser rejects inline `REFERENCES`, inline `CHECK`, `TIMESTAMPTZ`, `STABLE` and `CREATE DOMAIN`. Use separate `ALTER TABLE ... ADD CONSTRAINT` statements, `TIMESTAMP WITH TIME ZONE` and plain `LANGUAGE SQL`; `CREATE TYPE ... AS ENUM` works and generates a Haskell sum type.
- A custom enum named `JobStatus` collides with IHP's job type. Pick another name.
- `new-migration` fails against the dev shell's default PostgreSQL socket, which is not running under the broker, so set `DATABASE_URL` inside the command. Review the output, since a probe's migration turned `SERIAL` IDs into plain `INT` without defaults, and test inserts after a fresh migration.
- Two IHP sketches failed on the pinned version: `typedSql` rejected a `Maybe Text` inside `COALESCE`, and `putContext` and `fromContext` do not exist in IHP 1.6. Use generated record updates for optional fields, and read controller context from the WAI request and its vault.
- Typed SQL can fail with SQLSTATE 26000 from Hasql's stale prepared-statement cache, and IHP run 1 had to wrap those calls. Warn agents about it in an IHP brief, and review any such wrapper.
- `nix flake check --impure` can resolve `devenv-root` to `/dev/null` inside the container. If it does, pass `--override-input devenv-root file+file:///work/app/.devenv/root` through `harness/ihp.sh run`.
