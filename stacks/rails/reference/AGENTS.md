# Conduit backend rule map

- Rails routes in `config/routes.rb` lead to conventional controllers in `app/controllers/api`. Controllers own request order, access checks, response codes, and permitted fields.
- `User`, `Article`, `Share`, and their associations own persistence invariants. Draft visibility is `Article.visible_to`; article revisions and slug assignment are in `Article`. `ConduitJson` owns the public response shapes.
- `Token` issues and verifies HS256 credentials. Share keys have a separate capability boundary in `Share.authorized`; only their SHA-256 digests are stored.
- `LiveSocket` handles Puma Rack hijack and WebSocket frames. `LiveRooms` owns atomic admission, presence, the 100 editor cap, revision broadcasts, and revocation for the single backend instance.
- `ExportJob` builds stored snapshots through Rails Active Job and Solid Queue. Queue tables live in the primary PostgreSQL database; the Puma plugin runs the worker in the production container.
- Run `harness/check-all.sh 4101` against a server and `bin/rubocop`. `harness/check-production.sh 4101` checks the Docker image with a fresh database. Keep `realworld_spec`, `security`, and `harness` untouched.
