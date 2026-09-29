# Phoenix expert diagnostic

The existing Phoenix results show two separable opportunities. The original semantic-density build passed the complete product and security gates with 8,954 owned backend tokens. Its list path issued about 42 SQL statements per anonymous request. A separate Ecto query revision reduced that path to four statements and raised paired throughput from about 1.1k to about 4.0k requests/s. A compiled Mix release reduced its image from 1,673 MB to 165 MB. These are observations for those source copies and workloads, not an Elixir language ceiling. See [the original run](../results/one-shot-semantic-density/README.md) and [the Phoenix shine diagnostics](../results/shine/phoenix/README.md).

The new [expert environment](../one-shot-v2-phoenix-expert/ENVIRONMENT.md) keeps the shared safe-evolution prompt and contract while preparing Phoenix's normal application path. The product-free scaffold includes Ecto, Oban, JWT and password libraries, raw WebSocket adapter, and a compiled release. It gives the agent a short edit-to-response loop plus fixed development and fresh-production checks. It leaves all Conduit rules for the measured agent.

The implementation target is a small set of named owners:

| Concern | Strong Phoenix expression | Existing failure to watch |
| --- | --- | --- |
| Visibility and discovery | Composable Ecto scopes and explicit author/capability queries in a context | Draft policies split between slug reads and list filters |
| Input and errors | Changesets plus strict wire-shape checks, then tagged domain results | `cast/4` silently ignores fields outside its permitted set |
| Revision and editing | One atomic content commit, separate author and keyed entrances | Boolean `shared?` mode and revoked-link race |
| Lists | Page query first, batch preloads and aggregates, constant statement budget | Per-article author and favorite queries |
| Exports | Export row and Oban job in one Ecto transaction, idempotent worker | Pending export without durable job after a partial failure |
| Live editing | Bandit/WebSockAdapter for the fixed raw protocol, supervised per-room admission and PubSub delivery | A singleton process serializing database checks and fanout |
| Delivery | Mix release with migration before Phoenix/Oban starts | Unoptimized or oversized runtime image |

These APIs are documented by [Phoenix JSON controllers](https://phoenix.hexdocs.pm/json_and_apis.html), [Ecto changesets](https://ecto.hexdocs.pm/Ecto.Changeset.html), [Ecto transactions](https://ecto.hexdocs.pm/Ecto.Multi.html), [Oban's transaction-aware insert](https://oban.hexdocs.pm/Oban.html), [Phoenix PubSub](https://phoenix-pubsub.hexdocs.pm/Phoenix.PubSub.html), [WebSockAdapter](https://hexdocs.pm/websock_adapter/WebSockAdapter.html), and [Phoenix releases](https://phoenix.hexdocs.pm/releases.html). In particular, Phoenix Channels use their own message envelope, while the fixed editor speaks raw WebSocket frames; WebSockAdapter is a narrow protocol extension through the Phoenix endpoint.

The expert condition is a guided diagnostic, with its own fixture hash and source snapshot. It is separate from the v1 same-prompt comparison and the eight-step history. A later handoff experiment can test whether the rule map actually helps a fresh agent add a private-article policy without leaking it through lists, counts, exports, or share links. That task should be frozen before any handoff agent sees it.
