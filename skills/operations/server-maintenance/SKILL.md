---
name: server-maintenance
description: Set up or review routine maintenance on a self-hosted Docker box (Postgres backups, disk alerts, Docker cleanup, hardening).
disable-model-invocation: true
---

# Server maintenance

Routine care for a single self-hosted Linux host running Docker: scheduled Postgres backups, an hourly disk alert, weekly Docker cleanup, all installed via cron, plus a hardening review.

The scripts in [scripts/](scripts/) are generic and configured by environment variables (each documents its own at the top). The full review lives in [references/docker-hardening-checklist.md](references/docker-hardening-checklist.md).

Investigate before changing anything. Ask the user before every step marked **(ask)**.

## 1. Survey (read-only, run in parallel)

```bash
df -h; docker system df
docker ps --format '{{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}'
crontab -l 2>/dev/null; ls /etc/cron.d 2>/dev/null
systemctl list-timers --no-pager 2>/dev/null | head -20
docker version --format '{{.Server.Version}}'
cat /etc/docker/daemon.json 2>/dev/null
```

Look for existing backup, alert or cleanup jobs before adding new ones. If something already covers a job, review it against the sections below instead of duplicating it. Report what exists, what is missing, and what looks wrong.

## 2. Choose an install location

Agree with the user on a directory for the scripts (for example `~/server-maintenance`), a backup directory (`$BACKUP_DIR`) and a log directory. Prefer a backup location on a different disk from Docker's data; if there is only one disk, say so and recommend an off-host copy.

Copy the scripts there and `chmod +x` them. Keep any per-host settings in a small env file next to them (for example `maintenance.env`, mode 600), not in the scripts.

## 3. Postgres backups

`scripts/pg-backup.sh` finds every running Postgres container by image, runs `pg_dumpall` with the container's own credentials, gzips, verifies with `gzip -t`, and prunes to `KEEP` dumps per container only after a verified dump.

1. Run it once with `DRY_RUN=1` to show which containers it finds and what it would prune.
2. Estimate the disk budget: latest dump size times `KEEP`, per container. Set `KEEP_OVERRIDES` for large databases. Use `INCLUDE_REGEX` or `EXCLUDE_REGEX` if some containers should be skipped.
3. Run it for real once and check the log and `ls -la $BACKUP_DIR/*/`.
4. Offer a restore test: `scripts/pg-restore-test.sh <dump> <image matching the server's major version>`. It uses a throwaway container with no published ports and removes it afterwards.

Pruning deletes old backups. **(ask)** before the first real run if existing dumps would be pruned.

## 4. Disk alert

`scripts/disk-alert.sh` is silent below `THRESHOLD` (default 80) and, above it, logs the usage and the largest container logs, and posts to `NTFY_URL` if set. Test it once with `THRESHOLD=1` so the user sees an alert arrive.

## 5. Weekly Docker cleanup

`scripts/docker-maintenance.sh` prunes old build cache and dangling images. It does not touch volumes unless `PRUNE_VOLUMES=1`, and even then only anonymous volumes on Engine 23+. Never add `docker system prune -a` or `docker volume prune --all`: they remove tagged rollback images and named data volumes.

Run it with `DRY_RUN=1` first and show the output. **(ask)** before the first real run.

## 6. Install the schedule (ask)

Show the exact lines, then append them to the user crontab without clobbering existing entries:

```cron
# server-maintenance
0 * * * *  . <dir>/maintenance.env; <dir>/disk-alert.sh
30 2 * * * . <dir>/maintenance.env; <dir>/pg-backup.sh
0 4 * * 0  . <dir>/maintenance.env; <dir>/docker-maintenance.sh
```

Pick times that avoid the host's busy windows and any app jobs found in step 1. Install with `(crontab -l 2>/dev/null; cat new-lines) | crontab -`, then `crontab -l` to confirm. The env file must `export` its variables.

## 7. Hardening review

Work through [references/docker-hardening-checklist.md](references/docker-hardening-checklist.md). Sections 0 and 7 are read-only. Anything that restarts the Docker daemon, recreates containers or truncates logs causes downtime or data loss. **(ask)** for each.

## 8. Report

Finish with a short table: each job, its schedule, where it logs, the last result, and anything still open from the checklist's "Done when" list.
