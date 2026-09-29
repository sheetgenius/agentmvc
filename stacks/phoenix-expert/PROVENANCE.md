# Phoenix expert scaffold provenance

This is a copy of the repository's [product-free Phoenix generator snapshot](../phoenix/scaffold/) with infrastructure prepared for the expert diagnostic. The source snapshot is Phoenix 1.8's `phx.new` JSON API project. It contains no Conduit product rules.

The expert condition adds a health endpoint, a release migration entry point, PostgreSQL-backed Oban infrastructure, and a multi-stage compiled-release Dockerfile. It predeclares maintained password and JWT libraries and an adapter for the fixed raw WebSocket contract. Generator-only telemetry and DNS-discovery services were removed because the JSON contract has no use for them. The dependency lock comes from the already-built [eight-step Phoenix app](../phoenix/8-live-editing/mix.lock); product-free preflight verifies `mix deps.get` leaves it unchanged before freeze.

The scaffold's short `AGENTS.md` replaces generator advice about LiveView templates, which are outside this JSON API task. All added infrastructure is visible in `.scaffold/` and excluded from the measured agent-owned application size.
