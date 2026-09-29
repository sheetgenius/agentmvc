# Failed attempts and corrections

The scrubbed command transcripts are the complete record of attempts, including exploratory commands that returned nonzero. The counts below include those exploratory commands and deliberate server interruption, so they are not counts of product defects. Independent gate logs are linked from the [results index](README.md).

| Stack | Nonzero commands in measured session | Material failures encountered before final agent pass |
| --- | ---: | --- |
| Rails | 18 of 70 | Bundler and RuboCop initially used temp/cache paths denied by the workspace sandbox. The first API pass rejected an empty password update. The live check timed out waiting for an `updated` WebSocket message. Security checks exposed development exception traces. The agent corrected these, then passed development, production, and RuboCop. |
| Phoenix | 15 of 82 | The broker's Elixir container started in `/work/app/conduit` although the Phoenix scaffold was at `/work/app`; the agent made a local symlink alias and fetched dependencies there. Early syntax/compile errors and API validation failures followed. Security checks exposed development traces, and scaffold tests needed sandbox setup. One production attempt collided with its still running development port. The agent corrected these and passed both gates and format/compile checks. |
| Loco | 5 of 40 | Initial Rust compilation failed with the sandbox temp/toolchain path; the first complete API pass found that an empty bio serialized as a string instead of `null`. The formatter initially failed. A development server command exited 130 when stopped. The agent corrected the product and formatting failures, then passed its development, production, formatter, and Clippy checks. |

The Phoenix path mismatch was a frozen harness defect, not backend behavior. It was discovered during the measured session; changing the frozen broker would have invalidated the common input. The symlink alias is inside that agent's directory and is excluded from backend code size. Loco's passing server uses Axum directly in the Loco scaffold; that framework departure is assessed separately in the [results index](README.md).

## Runtime setup

Rails HTTP round 1 completed with all nine scenarios and no failed k6 checks. The first direct WebSocket attempt stopped before any application workload: the benchmark's `pg_isready` probe accepted PostgreSQL's temporary initialization server, which then restarted before the final probe. Its raw error record is [preserved](runtime/live/rails-round1-setup-failure.json). The readiness probe now checks TCP, which only the final PostgreSQL server opens in this image. The completed HTTP round was retained, and the live workload was rerun from an empty benchmark database.

The HTTP sampler's `foreign_container_cpu_percent_max` also includes the k6 load generator because Docker gave that container an automatic name. It is labeled as non-app container activity in the [runtime method](runtime/README.md) and is not interpreted as pure background CPU. The latency and throughput samples, host load, and independent live-container samples remain intact.
