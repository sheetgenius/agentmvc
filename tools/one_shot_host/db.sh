#!/usr/bin/env bash
# Disposable PostgreSQL for local development in a one-shot workspace.
set -euo pipefail
action="${1:?usage: harness/db.sh start|stop PORT}"
port="${2:?usage: harness/db.sh start|stop PORT}"
db_port="$((port + 50000))"
name="agentmvc-one-shot-db-$port"
image='postgres:17-alpine@sha256:742f40ea20b9ff2ff31db5458d127452988a2164df9e17441e191f3b72252193'
case "$action" in
  start)
    docker run -d --name "$name" --label agentmvc.one-shot=true \
      -p "127.0.0.1:$db_port:5432" \
      -e POSTGRES_USER=agentmvc -e POSTGRES_PASSWORD=agentmvc -e POSTGRES_DB=agentmvc \
      "$image" >/dev/null
    for attempt in {1..60}; do
      if docker exec "$name" pg_isready -U agentmvc -d agentmvc >/dev/null 2>&1; then break; fi
      sleep 1
    done
    docker exec "$name" pg_isready -U agentmvc -d agentmvc >/dev/null
    echo "DATABASE_URL=postgres://agentmvc:agentmvc@127.0.0.1:$db_port/agentmvc"
    ;;
  stop)
    label="$(docker inspect "$name" --format '{{index .Config.Labels "agentmvc.one-shot"}}' 2>/dev/null || true)"
    if [[ "$label" == true ]]; then docker rm -f "$name" >/dev/null; fi
    ;;
  *) echo 'usage: harness/db.sh start|stop PORT' >&2; exit 2;;
esac
