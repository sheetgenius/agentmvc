# Conduit API

A Phoenix 1.8 backend for the RealWorld API, with drafts, durable article exports, and shared live editing. PostgreSQL is the only external service. The production image starts a Mix release, migrates a fresh database, and runs Phoenix and Oban in one container.

See [AGENTS.md](AGENTS.md) for the product rule owners and local commands. The external editor uses `GET /api/shares/:id/live` as a raw JSON WebSocket. Phoenix routes the upgrade through Bandit and WebSockAdapter; a supervised room process manages presence and admission, while each socket process sends its own frames. Presence and the 100-member cap are local to this one-instance backend. Article data, shares, exports, and jobs are stored in PostgreSQL.
