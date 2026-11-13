# disk-alert.sh

This is the source of `disk-alert.sh`, kept as Markdown because the plugin directory does not accept executable files from unverified publishers. Do not retype it. Extract it exactly with the command in this skill's `SKILL.md`, which copies everything between the two fence lines below.

````bash
#!/usr/bin/env bash
# disk-alert.sh: warn well before a filesystem fills. Silent below the
# threshold; above it, logs, names the biggest Docker container logs (the usual
# culprit), and optionally pushes to an ntfy topic. Run hourly from cron.
#
# Configuration (all optional, via environment):
#   THRESHOLD  percent used that triggers a warning (default: 80)
#   MOUNTS     space-separated mount points to check (default: "/")
#   LOG        log file (default: $HOME/backups/disk-alert.log)
#   NTFY_URL   optional ntfy topic URL, e.g. https://ntfy.sh/<your-topic>
set -euo pipefail

THRESHOLD="${THRESHOLD:-80}"
MOUNTS="${MOUNTS:-/}"
LOG="${LOG:-$HOME/backups/disk-alert.log}"
mkdir -p "$(dirname "$LOG")"
host="$(hostname)"

for m in $MOUNTS; do
  use=$(df --output=pcent "$m" | tail -1 | tr -dc '0-9')
  [ "$use" -ge "$THRESHOLD" ] || continue

  msg="DISK WARNING on $host: $m is ${use}% full (threshold ${THRESHOLD}%)"
  echo "$(date '+%F %T') $msg" >> "$LOG"

  # Needs non-interactive sudo (sudo -n) to read Docker's log dir; skipped quietly otherwise.
  biglogs=$(sudo -n sh -c 'du -h /var/lib/docker/containers/*/*-json.log 2>/dev/null | sort -rh | head -3' 2>/dev/null || true)
  if [ -n "$biglogs" ]; then
    { echo "  biggest container logs:"; echo "$biglogs"; } >> "$LOG"
  fi

  if [ -n "${NTFY_URL:-}" ]; then
    curl -fsS -H "Title: $host disk ${use}%" -d "$msg"$'\n'"$biglogs" "$NTFY_URL" >/dev/null || true
  fi
done
````
