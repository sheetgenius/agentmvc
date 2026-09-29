# Rails expert toolchain provenance

The scaffold was copied from the repository's original product-free Rails 8.1
API scaffold. Its framework and Ruby versions remain pinned. This expert
condition adds GoodJob for a PostgreSQL Active Job queue, bcrypt and jwt for
the fixed auth protocol, Faye WebSocket for raw frames over Puma, rack-cors
for the separate fixed client, and a production Dockerfile with eager loading
and Bootsnap precompilation. All transitive gem versions are in
`scaffold/Gemfile.lock`, including the Linux platform.

The preflight report records the exact toolchain image ID, fixture hash,
development reload, queue/database migration, raw WebSocket round trip,
production health, and isolation results. Only product-free capabilities are
tested before the measured agent starts.
