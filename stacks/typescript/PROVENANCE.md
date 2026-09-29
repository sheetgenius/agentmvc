# TypeScript scaffold provenance

The product-free AdonisJS 7 scaffold began from the [Slim Starter Kit](https://github.com/batosai/adonisjs-slim-starter-kit), which AdonisJS lists among its community starters. AgentMVC removed the welcome route, configured PostgreSQL, Vine, and the database queue, and supplied a compiled production image. The scaffold contains no Conduit product models or handlers. The frozen package lock records exact versions; the base Node 24 image is pinned by digest. The upstream starter is MIT licensed according to its repository page.

AdonisJS supplies routing, HTTP context, validation, Lucid models and migrations, hash service, authorization, and queue integration. The benchmark client requires JWT and raw WebSockets. Those are explicit extension points for the agent, not prewritten product code. The PostgreSQL queue is experimental in this AdonisJS version, so its package version is pinned exactly.
