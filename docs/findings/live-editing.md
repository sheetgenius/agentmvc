# Live editing: how did the three implementations do?

Step 8 added a revocable public editing link, revision-checked saves, WebSocket updates, presence, and a 100-connection room cap. The [protocol, Lit client, and checks](../../spec/features/live-editing/live-editing.md) were frozen before one measured agent run per stack. The client and its tests are [reported separately](../../results/live-editing/) and excluded from backend code size.

## Result

All three agents reached DONE. Independent reruns passed the development and production gates: all 17 Hurl files, the socket protocol suite, three Playwright browser tests, and all 13 production security files. A separate post-run review also checked 105 concurrent admission attempts, revocation, owner edits, and subscription/save races. These are meaningful correctness results for the specified single-instance design, not proof that every concurrency interleaving is covered.

| | Rails | Phoenix | Loco |
| --- | ---: | ---: | ---: |
| Step-8 backend code added or changed, tokens | 1,490 | 3,024 (2.03×) | 3,823 (2.57×) |
| Whole backend after step 8, tokens | 6,259 | 12,029 (1.92×) | 16,653 (2.66×) |
| Agent effort, uncached tokens | 175,988 | 195,947 | 180,266 |
| Agent wall time, minutes | 25.2 | 25.5 | 26.7 |

This was the largest post-build feature addition in the study. Compared with step 7's background job, it took 2.83× the code in Rails, 3.17× in Phoenix, and 2.44× in Loco. Yet the three agent runs took nearly the same wall time. Browser setup inside the agents' macOS sandboxes contributed to that time, so the timings do not isolate framework implementation effort.

## What the code shows

- **Rails used the least application code.** [`ArticleShare`](../../stacks/rails/8-live-editing/app/models/article_share.rb) holds the capability rule, and [`ShareRoom`](../../stacks/rails/8-live-editing/app/services/share_room.rb) keeps admission, presence, and ordered broadcasts together. The WebSocket path needed Faye and EventMachine; the agent's first broadcasts failed until it scheduled writes on the event loop. Room admission also holds one global mutex during database reads, and [`ShareSocket`](../../stacks/rails/8-live-editing/app/services/share_socket.rb) starts a timeout thread for each new socket. Those choices are simple at this study's scale but deserve a higher-churn test before extrapolating.
- **Phoenix has the most direct fit for connected clients.** [`LiveRooms`](../../stacks/phoenix/8-live-editing/lib/conduit/live_rooms.ex) uses a supervised process, monitors socket processes, and serializes admission and presence. [`ShareSocket`](../../stacks/phoenix/8-live-editing/lib/conduit_web/share_socket.ex) tracks the last revision per client. The tradeoff is that one room process handles every article and performs database reads during joins and update broadcasts. The current five-saves-per-second load did not test when that process becomes a bottleneck.
- **Loco makes concurrency and recovery explicit.** [`Hub` and `Room`](../../stacks/loco/8-live-editing/conduit/src/models/live_rooms.rs) use a short global map lock, per-room admission locks, and broadcast channels. A lagging subscriber resynchronizes from the database in the [socket handler](../../stacks/loco/8-live-editing/conduit/src/controllers/shares.rs). The shared-save transaction rechecks the capability before writing. This is the most code, and the build/check path incurred Rust compilation cost. Code review also found that leaving the last socket decrements its count but does not remove the now-empty room from `Hub.rooms`; repeated visits to many distinct articles can retain room objects until links are revoked. The present tests measure connected rooms, not long-term room churn.

Rails remained the most compact, while Phoenix's process model expressed presence and disconnect handling clearly. Loco's per-room structure avoids Phoenix's single room-process queue, at the cost of more machinery. Those are design observations; this run does not establish a general maintainability or scalability winner.

## Load result and limits

Two direct-protocol rounds sent 20 HTTP saves at five per second with 10, 100, and 500 subscribers. The 500 subscribers were spread over five articles to respect the cap. All **25,200 expected deliveries** arrived with no missing, duplicate, or regressed revisions. Delivery p95 ranged from 15.3–33.6 ms for Rails, 7.4–21.4 ms for Phoenix, and 13.0–20.0 ms for Loco across the six stack/scenario combinations and two rounds. [Raw samples and resource measurements](../../results/live-editing/) are published.

The host carried substantial unrelated load, and several percentiles moved sharply between rounds. Sampled active backend CPU never exceeded 4.2% of one CPU at five saves per second. The benchmark shows that each implementation handled this fixed workload. It does not support a latency ranking, a saturation claim, or a conclusion about multiple backend instances. Presence and admission are intentionally in memory on one instance.

## Follow-up found by code review

The frozen [shared editor](../../frontend/src/editor.js) protects a dirty draft when a socket update arrives. Its `save()` then unconditionally adopts the HTTP response. If the user types while that request is in flight, or a newer socket update arrives before an older save response, that response can replace the newer local or server state. The current browser tests do not exercise that ordering. This is a **shared-client issue**, not a difference among the three backends; it should be tested and fixed in a separately labeled follow-up so the measured fixture remains reproducible.

The [run report](../../results/live-editing/README.md) has the full measurement table, agent reports, scrubbed transcripts, and [failure history](../../results/live-editing/failures.md).
