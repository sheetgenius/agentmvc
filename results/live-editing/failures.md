# Step-8 failure history

This is a summary of failures and corrections. Each agent's [scrubbed transcript](README.md#acceptance-and-demo) records its own attempts in order.

| Stage | Failure | Resolution |
| --- | --- | --- |
| Fixture validation, before freeze | The 101st client's Retry received `ready` but the Lit page remained on “Opening editor…”. | The client returns to the editor on `ready`; the frozen Playwright test then passed against the [reference server](reference-validation.md). |
| Rails agent | The first socket update did not reach subscribers because Faye writes occurred off its event loop. | The agent scheduled room sends on EventMachine and reran both gates green. |
| Browser setup in all agent sandboxes | Host Chromium launch was denied by the macOS sandbox. An older Linux browser image and direct CDN install did not provide the matching Chromium build. | The agents used the matching Playwright Linux image to run the unchanged shared browser files. The image stayed outside production backends. |
| Phoenix agent | Playwright tried to remove `test-results` on a read-only fixture mount. | The agent used a temporary writable copy of the frozen client; source and checks remained unchanged. |
| Loco agent | The first Linux browser run tried to download Chromium from the CDN and timed out. A separate offline Cargo check lacked a new dependency in the default cache. | The matching Playwright image removed the download dependency; the agent populated its toolchain cache and finished both gates green. |
| Transcript publication | A shared Playwright cache listed paths to unrelated local worktrees in two transcripts. | The scrubber now removes those paths. A transcript command audit found no reads of another stack's source. |
| Load-harness smoke test | Rails returned 406 to a readiness request without a JSON `Accept` header. | The benchmark probe now requests JSON. The next smoke test passed. |
| Load round two, Rails first attempt | Fresh PostgreSQL was still rejecting connections at the 30-second readiness deadline; no workload ran. | The failed record is [preserved](rails-round2-initial-failure.json). The readiness window was lengthened, and only Rails round two was rerun. Its 10/100/500-subscriber scenarios all completed. |
| Final demo audit | The Rails readiness probe in `tools/demo.sh` lacked the JSON `Accept` header Rails requires for `/api/tags`. | The probe now sends that header. The Rails demo was rerun and printed a working editing URL. |

The independent published-snapshot gates and the separate production-image reviewer checks passed for all three stacks after these corrections.
