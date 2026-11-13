# pg-backup.sh

This is the source of `pg-backup.sh`, kept as Markdown because the plugin directory does not accept executable files from unverified publishers. Do not retype it. Extract it exactly with the command in this skill's `SKILL.md`, which copies everything between the two fence lines below.

````bash
#!/usr/bin/env bash
# pg-backup.sh: dump every running Postgres container, gzip it, verify the
# archive, and keep the newest N dumps per container.
#
# Containers are auto-detected by image name, so a new Postgres stack is picked
# up without editing this file. Each dump uses the container's own
# POSTGRES_USER and POSTGRES_PASSWORD, read inside the container, so no
# credentials live in this script, the host process list, or the log.
#
# Configuration (all optional, via environment):
#   BACKUP_DIR      where dumps go              (default: $HOME/backups/postgres)
#   KEEP            dumps to keep per container (default: 7)
#   KEEP_OVERRIDES  per-container retention, e.g. "big-db=2,other-db=14"
#   INCLUDE_REGEX   only back up containers whose name matches (default: all)
#   EXCLUDE_REGEX   skip containers whose name matches (default: none)
#   IMAGE_REGEX     images treated as Postgres  (default: postgres|pgvector|postgis|timescale)
#   LOG             log file                    (default: $HOME/backups/pg-backup.log)
#   NTFY_URL        optional ntfy topic URL for failure alerts
#   DRY_RUN=1       list what would be dumped and pruned, change nothing
set -euo pipefail

BACKUP_DIR="${BACKUP_DIR:-$HOME/backups/postgres}"
KEEP="${KEEP:-7}"
KEEP_OVERRIDES="${KEEP_OVERRIDES:-}"
INCLUDE_REGEX="${INCLUDE_REGEX:-.*}"
EXCLUDE_REGEX="${EXCLUDE_REGEX:-^$}"
IMAGE_REGEX="${IMAGE_REGEX:-postgres|pgvector|postgis|timescale}"
LOG="${LOG:-$HOME/backups/pg-backup.log}"
DRY_RUN="${DRY_RUN:-0}"
STAMP="$(date +%Y%m%d-%H%M%S)"

# Retention is a disk budget, not a time window: a 10GB dump kept 7 deep costs
# 70GB. Keep large databases shallow via KEEP_OVERRIDES.
declare -A KEEP_FOR=()
IFS=',' read -ra pairs <<< "$KEEP_OVERRIDES"
for p in "${pairs[@]}"; do
  [ -n "$p" ] && KEEP_FOR["${p%%=*}"]="${p#*=}"
done

mkdir -p "$BACKUP_DIR" "$(dirname "$LOG")"
exec > >(tee -a "$LOG") 2>&1
echo "===== pg-backup $STAMP (dry run: $DRY_RUN) ====="

# Find running Postgres containers, skipping metric exporters.
mapfile -t CONTAINERS < <(
  docker ps --format '{{.Names}}\t{{.Image}}' \
  | awk -F'\t' -v img="$IMAGE_REGEX" 'tolower($2) ~ img && tolower($2) !~ /exporter/ {print $1}' \
  | grep -E "$INCLUDE_REGEX" | grep -vE "$EXCLUDE_REGEX" || true
)

if [ "${#CONTAINERS[@]}" -eq 0 ]; then
  echo "No Postgres containers found."; exit 0
fi

fail=0
failed=()
for c in "${CONTAINERS[@]}"; do
  dir="$BACKUP_DIR/$c"
  out="$dir/${c}-${STAMP}.sql.gz"
  keep="${KEEP_FOR[$c]:-$KEEP}"
  echo "--> $c -> $out (keep $keep)"
  if [ "$DRY_RUN" = "1" ]; then
    ls -1t "$dir"/*.sql.gz 2>/dev/null | tail -n +"$((keep))" | sed 's/^/    would prune: /' || true
    continue
  fi
  mkdir -p "$dir"
  # pg_dumpall captures every database plus roles and globals.
  # Never use `docker exec -t`: a pseudo-TTY mangles piped output and can
  # truncate large dumps. pipefail makes a pg_dumpall error fail this step.
  if docker exec "$c" sh -c \
       'PGPASSWORD="${POSTGRES_PASSWORD:-}" pg_dumpall -U "${POSTGRES_USER:-postgres}" -w' \
       | gzip > "$out" \
     && gzip -t "$out" \
     && [ "$(gzip -dc "$out" | head -c 4096 | wc -c)" -gt 0 ]; then
    echo "    ok ($(du -h "$out" | cut -f1)), gzip integrity verified"
    # Prune only after a verified dump: newest $keep stay, the rest go.
    ls -1t "$dir"/*.sql.gz 2>/dev/null | tail -n +"$((keep+1))" | xargs -r rm -f
  else
    echo "    FAILED"
    rm -f "$out"
    failed+=("$c")
    fail=1
  fi
done

# Cron discards exit codes, so surface failures somewhere a human will see.
if [ "$fail" -ne 0 ]; then
  msg="pg-backup FAILED for: ${failed[*]}"
  echo "$msg"
  logger -t pg-backup "$msg" || true
  if [ -n "${NTFY_URL:-}" ]; then
    curl -fsS -H "Title: $(hostname) backup failure" -d "$msg" "$NTFY_URL" >/dev/null || true
  fi
fi

echo "===== done (exit $fail) ====="
exit "$fail"
````
