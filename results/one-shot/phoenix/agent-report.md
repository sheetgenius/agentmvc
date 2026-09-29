Built the complete Conduit backend and left the shared editor and read-only fixtures unchanged.

**Checks passed:** the development and fresh-database production gates each passed all 17 API files, the WebSocket protocol check, 4 browser tests, and 13 security files. `mix precommit`, formatter check, and warning-free compilation also passed.

[Data rules](/work/app/lib/conduit/data.ex) own draft visibility, article updates, revision conflicts, and serialization. The [API controller](/work/app/lib/conduit_web/api_controller.ex) owns HTTP authorization and responses. [Rooms](/work/app/lib/conduit/rooms.ex) and the [socket handler](/work/app/lib/conduit_web/live_socket.ex) own presence, updates, revocation, and the 100-editor cap. [Oban](/work/app/lib/conduit/export_worker.ex) runs durable exports; the [Dockerfile](/work/app/Dockerfile) migrates the database on startup.

During verification, I fixed missing rate-limit initialization, blank-field database errors, development stack-trace responses, test sandbox startup, and a production port conflict. Presence and login counters are process local; article and export data are stored in PostgreSQL.