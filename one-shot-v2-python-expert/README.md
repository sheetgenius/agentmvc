# Python expert diagnostic

The Python lane uses Django and Django Ninja with PostgreSQL, Channels,
Procrastinate and Uvicorn. Read the [stack decision](../stacks/python/STACK.md)
and [environment](ENVIRONMENT.md) for the exact condition. It uses the same
[expert prompt](../one-shot-v2-expert/PROMPT.md), measurement boundary, frozen
Conduit contract, Lit client and acceptance checks as the existing expert lanes.

The product-free scaffold supplies a health endpoint, persistence configuration,
ASGI routing, third-party queue integration and production packaging. It contains
no Conduit behavior. The separate eight-step run begins from that same scaffold;
it does not hand its implementation to the one-shot agent. Neither path changes
the historical Rails, Phoenix and Loco artifacts.

Product-free container preflight has passed: reload, transactional durable
queue, worker restart, raw sockets and fresh production startup. The
[preflight proof](../results/lanes/python/preflight.json) records pins and
checks. The coordinator still verifies workspace isolation and freezes the
inputs before measured launch. Run effort is recorded when
available; full sessions and raw streams are scrubbed and published outside Git.
