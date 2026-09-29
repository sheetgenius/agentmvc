The Conduit backend is complete, and both acceptance gates are green.

- **Development:** 17 HTTP files (239 requests), live WebSocket protocol, 4 browser tests, and all 13 security files passed.
- **Production:** The Docker image started with fresh PostgreSQL, applied migrations, and passed the same suite. `bin/rubocop` passed on 41 files.

Rails owns routing, controllers, Active Record persistence and migrations, and Active Job exports through PostgreSQL-backed Solid Queue. [Article](/work/app/app/models/article.rb) owns draft visibility, revisions, and slugs; [ConduitJson](/work/app/app/serializers/conduit_json.rb) owns response shapes. [Share](/work/app/app/models/share.rb) verifies editing keys; [LiveSocket](/work/app/app/models/live_socket.rb) and [LiveRooms](/work/app/app/models/live_rooms.rb) handle the focused WebSocket extension, presence, revocation, and the 100-editor cap. [AGENTS.md](/work/app/AGENTS.md) maps these rules for future changes.

Early checks caught empty-field normalization, null-password validation, and Puma’s blocked temporary directory in the local sandbox; all were fixed. Solid Queue’s fork mode crashed locally on macOS, so the container runs its durable worker in async supervisor mode. Presence remains in memory, as specified for one backend instance.