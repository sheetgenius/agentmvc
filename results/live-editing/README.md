# Step 8: live shared editing

Three single-instance backends implemented the same [contract](../../spec/features/live-editing/live-editing.md) from their step-7 snapshots. Each agent received the same [prompt](../../steps/8-live-editing.md), frozen [Lit editor](../../frontend/), and acceptance files. The prompt SHA-256 was `f44ffb88bcf65bfe59f9841d1c8c81f32220c4b06a25fefdc5119e74b42c85d9`; the complete fixture SHA-256 was `5cf8a83f3be200afe9a90f6d3db9b11958ea7db824e13d8dfa8d7db7cdf1bf65`. [Individual hashes](../../spec/features/live-editing/fixture-manifest.json) and all three `runs.json` records agree. The client and checks were validated against a [throwaway reference server](reference-validation.md) before the backend agents started.

The [findings](../../docs/findings/live-editing.md) interpret the results and record two follow-up issues found by code review.

## Acceptance and demo

Independent reruns of `tools/check.sh STACK 8-live-editing` passed for all three published snapshots. Each development and production gate passed all 17 Hurl files, the direct socket protocol suite, and all three Playwright tests. Each production gate also passed all 13 security files. Stack formatters and linters were green. The frozen materials were unchanged in all three agent workdirs and independent check workdirs.

| Stack | Agent report | Scrubbed transcript | Independent gates | Separate reviewer checks |
| --- | --- | --- | --- | --- |
| Rails | [report](https://github.com/sheetgenius/agentmvc/blob/8c8999d8ef4c29acacd01a60d4fed1400231143d/stacks/rails/reports/8-live-editing.md) | [transcript](https://github.com/sheetgenius/agentmvc/blob/8c8999d8ef4c29acacd01a60d4fed1400231143d/stacks/rails/transcripts/8-live-editing.md) | Pass | Pass |
| Phoenix | [report](https://github.com/sheetgenius/agentmvc/blob/8c8999d8ef4c29acacd01a60d4fed1400231143d/stacks/phoenix/reports/8-live-editing.md) | [transcript](https://github.com/sheetgenius/agentmvc/blob/8c8999d8ef4c29acacd01a60d4fed1400231143d/stacks/phoenix/transcripts/8-live-editing.md) | Pass | Pass |
| Loco | [report](https://github.com/sheetgenius/agentmvc/blob/8c8999d8ef4c29acacd01a60d4fed1400231143d/stacks/loco/reports/8-live-editing.md) | [transcript](https://github.com/sheetgenius/agentmvc/blob/8c8999d8ef4c29acacd01a60d4fed1400231143d/stacks/loco/transcripts/8-live-editing.md) | Pass | Pass |

`tools/demo.sh rails|phoenix|loco` built and started each production image with PostgreSQL and the same shared editor, created a draft and editing link, and printed a usable URL. The later [review script](../../tools/live-review.mjs) passed on each production image: an invalid link in a fresh browser, a save after revocation, repeated save/subscription races, owner edits reaching subscribers, and 105 simultaneous admission attempts yielding exactly 100 ready and five room-full responses. That review script was outside the frozen agent fixture.

## Source and agent effort

Backend code sizes use the existing `o200k_base` [measurement rules](../../tools/measure.py), excluding tests, check harnesses, dependencies, generated schema, and the shared frontend. Agent effort is uncached input plus output tokens and launch-to-exit time from the measured runs.

| Stack | Step-8 added or changed tokens | Whole backend tokens | Whole backend code lines | Agent tokens | Agent minutes |
| --- | ---: | ---: | ---: | ---: | ---: |
| Rails | 1,490 | 6,259 | 770 | 175,988 | 25.2 |
| Phoenix | 3,024 | 12,029 | 1,367 | 195,947 | 25.5 |
| Loco | 3,823 | 16,653 | 2,481 | 180,266 | 26.7 |

The shared editor itself is **210 nonblank lines and 2,391 tokens** across six source files. Its browser and protocol test code is another **204 lines and 2,567 tokens**. Neither is attributed to a backend stack. The observed frontend source editing window was 6.2 minutes, and the full shared-fixture preparation window was 9.85 minutes; these file-timestamp windows include overlapping spec and validation work, so they are not precise active coding time. [Source and effort record](shared-client.json).

## Direct protocol load

The [load harness](../../tools/live-bench.py) built all three production images first, then ran two rounds in opposite stack order. Each app was one container limited to 2 CPUs and 1 GB, with PostgreSQL in a separate container under the same limits. The direct client, outside the browser and frontend, subscribed 10, 100, or 500 sockets. The 500 sockets were spread over five articles so no room exceeded its 100-connection cap. It sent 20 revision-checked HTTP PUTs at five saves per second in every scenario. Each request body was 89 bytes. Delivery time starts when the HTTP save is sent and ends when a matching socket update arrives; save time ends at the HTTP response.

Every scenario achieved five saves per second. Across both rounds and all stacks, **25,200 expected update deliveries were observed**, with zero missing, duplicate, or regressed revisions. The raw records include each save and delivery sample, plus CPU, memory, host-load, image and payload measurements.

| Stack | Subscribers | Save p95 ms, rounds 1 / 2 | Delivery p95 ms, rounds 1 / 2 | Delivery p99 ms, rounds 1 / 2 |
| --- | ---: | ---: | ---: | ---: |
| Rails | 10 | 33.9 / 15.6 | 33.6 / 15.3 | 34.4 / 24.8 |
| Rails | 100 | 32.9 / 14.1 | 32.5 / 15.3 | 39.3 / 22.0 |
| Rails | 500 | 17.3 / 16.2 | 19.1 / 17.4 | 19.6 / 40.1 |
| Phoenix | 10 | 21.4 / 13.8 | 21.4 / 14.9 | 22.2 / 21.7 |
| Phoenix | 100 | 12.7 / 14.2 | 14.4 / 17.4 | 33.2 / 26.5 |
| Phoenix | 500 | 17.0 / 5.1 | 20.9 / 7.4 | 21.7 / 8.3 |
| Loco | 10 | 15.4 / 14.5 | 15.6 / 14.8 | 17.0 / 15.9 |
| Loco | 100 | 19.1 / 13.2 | 20.0 / 14.0 | 25.2 / 17.0 |
| Loco | 500 | 12.7 / 9.1 | 13.2 / 13.0 | 13.5 / 16.5 |

Idle samples were taken after a one-second settling period while the subscribers stayed connected. CPU is Docker's percent of one CPU; memory is Docker's reported container memory in MiB. The table shows the median idle CPU sample and peak idle memory sample from each round.

| Stack | Subscribers | Idle CPU %, rounds 1 / 2 | Idle memory MiB, rounds 1 / 2 |
| --- | ---: | ---: | ---: |
| Rails | 10 | 1.83 / 1.51 | 220 / 236 |
| Rails | 100 | 0.87 / 0.44 | 256 / 232 |
| Rails | 500 | 0.43 / 0.45 | 247 / 253 |
| Phoenix | 10 | 0.23 / 0.32 | 160 / 158 |
| Phoenix | 100 | 0.33 / 0.33 | 147 / 146 |
| Phoenix | 500 | 0.53 / 0.49 | 165 / 165 |
| Loco | 10 | 0.42 / 0.31 | 30 / 6 |
| Loco | 100 | 0.44 / 1.24 | 31 / 50 |
| Loco | 500 | 0.50 / 0.41 | 74 / 94 |

The host's one-minute load was about 12–14 during these runs, and unrelated containers reached 643% combined CPU in a sample. Some memory samples and latency percentiles moved substantially between rounds. These data show that all three implementations handled the fixed workload; the small latency differences are not a stable ranking on this host. The one fresh-PostgreSQL startup failure before Rails round two and its successful rerun are preserved in the [failure history](failures.md).

Raw measurements: Rails [round 1](8-live-editing-rails-round1.json), [round 2](8-live-editing-rails-round2.json); Phoenix [round 1](8-live-editing-phoenix-round1.json), [round 2](8-live-editing-phoenix-round2.json); Loco [round 1](8-live-editing-loco-round1.json), [round 2](8-live-editing-loco-round2.json).

## Reproduce

```sh
python3 tools/live_fixture.py verify
tools/check.sh rails 8-live-editing
tools/check.sh phoenix 8-live-editing
tools/check.sh loco 8-live-editing
tools/demo.sh rails
python3 tools/live-bench.py
```

The demo prints a fragment-key URL to paste into other tabs or browsers. Set `DEMO_ORIGIN` to an origin reachable from another device. The benchmark needs Docker, Node dependencies from `frontend/package-lock.json`, and a machine with enough free resources for 500 sockets.
