# docker-maintenance.sh

This is the source of `docker-maintenance.sh`, kept as Markdown because the plugin directory does not accept executable files from unverified publishers. Do not retype it. Extract it exactly with the command in this skill's `SKILL.md`, which copies everything between the two fence lines below.

````bash
#!/usr/bin/env bash
# docker-maintenance.sh: weekly housekeeping so Docker does not silently
# re-accumulate disk. Only removes things no container references.
#
# Volumes are NOT pruned by default. Volumes hold data (databases, uploads),
# and on Docker Engine older than 23.0 `docker volume prune` removes every
# unused volume, named ones included. Opt in with PRUNE_VOLUMES=1, which
# only ever prunes anonymous volumes.
#
# Configuration (all optional, via environment):
#   BUILD_CACHE_AGE  prune build cache older than this (default: 168h)
#   PRUNE_VOLUMES=1  also prune unused anonymous volumes
#   LOG              log file (default: $HOME/backups/docker-maintenance.log)
#   DRY_RUN=1        report what would be reclaimed, change nothing
set -euo pipefail

BUILD_CACHE_AGE="${BUILD_CACHE_AGE:-168h}"
PRUNE_VOLUMES="${PRUNE_VOLUMES:-0}"
DRY_RUN="${DRY_RUN:-0}"
LOG="${LOG:-$HOME/backups/docker-maintenance.log}"
mkdir -p "$(dirname "$LOG")"
exec > >(tee -a "$LOG") 2>&1
echo "===== docker-maintenance $(date +%F) (dry run: $DRY_RUN) ====="

echo "[df before]"; df -h / | awk 'NR==1 || $NF=="/"'
docker system df

if [ "$DRY_RUN" = "1" ]; then
  echo "[dangling images]"; docker images -f dangling=true
  [ "$PRUNE_VOLUMES" = "1" ] && { echo "[unused volumes]"; docker volume ls -f dangling=true; }
  echo "===== dry run done ====="; exit 0
fi

# Build cache not used within BUILD_CACHE_AGE.
docker builder prune -f --filter "until=$BUILD_CACHE_AGE"
# Dangling (untagged) images only. Never touches tagged or in-use images.
docker image prune -f

if [ "$PRUNE_VOLUMES" = "1" ]; then
  # Engine 23+: prunes anonymous volumes only, unless --all is passed.
  server_major=$(docker version --format '{{.Server.Version}}' | cut -d. -f1)
  if [ "$server_major" -ge 23 ]; then
    docker volume prune -f
  else
    echo "Skipping volume prune: Engine $server_major would remove named volumes too."
  fi
fi

echo "[df after]"; df -h / | awk 'NR==1 || $NF=="/"'
echo "===== done ====="
````
