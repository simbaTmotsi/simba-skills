#!/usr/bin/env bash
# pg-restore-test.sh: prove a dump actually restores. Starts a throwaway
# Postgres container (no published ports, no named volume), loads the dump,
# counts user tables, then removes the container.
#
# Usage: pg-restore-test.sh <dump.sql.gz> [postgres-image]
#   The image should match the major version of the source server,
#   e.g. postgres:16 or pgvector/pgvector:pg16.
# Configuration:
#   MIN_TABLES   fail if fewer user tables than this are restored (default: 1)
set -euo pipefail

DUMP="${1:?usage: pg-restore-test.sh <dump.sql.gz> [image]}"
IMAGE="${2:-postgres:16}"
MIN_TABLES="${MIN_TABLES:-1}"
NAME="pg-restore-test-$$"

[ -r "$DUMP" ] || { echo "cannot read $DUMP"; exit 1; }
gzip -t "$DUMP"

cleanup() { docker rm -f "$NAME" >/dev/null 2>&1 || true; }
trap cleanup EXIT

docker run -d --name "$NAME" -e POSTGRES_HOST_AUTH_METHOD=trust "$IMAGE" >/dev/null
for _ in $(seq 1 60); do
  docker exec "$NAME" pg_isready -U postgres >/dev/null 2>&1 && break
  sleep 1
done

# A pg_dumpall file recreates roles that may already exist ("postgres"), so a
# few "already exists" errors are expected. Real failures show in the count.
gzip -dc "$DUMP" | docker exec -i "$NAME" psql -U postgres -q -o /dev/null 2>&1 \
  | grep -v 'already exists' | head -20 || true

total=0
for db in $(docker exec "$NAME" psql -U postgres -Atc \
    "select datname from pg_database where not datistemplate and datname <> 'postgres'"); do
  n=$(docker exec "$NAME" psql -U postgres -d "$db" -Atc \
    "select count(*) from information_schema.tables where table_schema not in ('pg_catalog','information_schema')")
  echo "  $db: $n tables"
  total=$((total + n))
done

echo "restored $total user tables from $DUMP"
[ "$total" -ge "$MIN_TABLES" ] || { echo "RESTORE TEST FAILED"; exit 1; }
echo "RESTORE TEST OK"
