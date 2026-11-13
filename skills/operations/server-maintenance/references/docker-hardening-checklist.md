# Docker host hardening checklist

The goal: stop the most common way a single Docker host silently dies (a runaway container log, or image and volume bloat, filling the root disk), then add resource caps, backups, alerts and a quick exposure check.

Investigate first. Show findings before changing anything. Every change below that restarts the daemon or recreates containers needs the user's go-ahead.

## 0. Investigate (read-only)

```bash
df -h /                                                    # how full is root?
sudo du -h -x -d1 / 2>/dev/null | sort -rh | head          # biggest top-level dirs
sudo du -h -x -d1 /var/lib 2>/dev/null | sort -rh | head   # usually /var/lib/docker
docker system df                                           # images, volumes, build cache
sudo sh -c 'du -h /var/lib/docker/containers/*/*-json.log 2>/dev/null | sort -rh | head'
docker ps -a --format '{{.Names}}\t{{.Image}}\t{{.Status}}'  # anything crash-looping?
free -h; nproc                                             # headroom for limits
cat /etc/docker/daemon.json 2>/dev/null                    # current daemon config
```

If one log file is huge, identify its container (`docker inspect <id> --format '{{.Name}}'`). Truncating reclaims space without stopping the container, but it discards that log history, so ask first:

```bash
sudo truncate -s 0 /var/lib/docker/containers/<id>/<id>-json.log
```

Then find out why it logged so much (`docker logs --tail 30 <name>`). A crash loop is a separate bug from the disk symptom.

## 1. Log rotation (the root fix)

**Host-wide default**, protecting every container including ones outside compose. Merge into `/etc/docker/daemon.json` without clobbering existing keys:

```json
{
  "log-driver": "json-file",
  "log-opts": { "max-size": "100m", "max-file": "3" }
}
```

```bash
python3 -m json.tool /etc/docker/daemon.json   # validate before restarting
sudo systemctl restart docker                  # restarts every container; ask first
```

**Per project**, so the setting travels with the compose file:

```yaml
    logging:
      driver: json-file
      options: { max-size: "50m", max-file: "3" }
```

Both apply only to newly created containers. Existing ones keep their old settings until recreated (`docker compose up -d --force-recreate`). Verify with `docker inspect <c> --format '{{.HostConfig.LogConfig}}'`.

## 2. Keep a full disk from killing the OS

- True isolation needs a separate volume for Docker's data (set `"data-root"` in `daemon.json` after mounting it). Without one, rely on the disk alert.
- Keep ext4's default 5% root reserve. It is the buffer that keeps SSH usable at "100%".
- Set memory limits (section 3) so one container cannot take the whole box down.

## 3. Resource limits

```bash
docker stats --no-stream --format '{{.Name}}\t{{.MemUsage}}'   # "/ <total RAM>" means no limit
```

Cap generously, around 2 to 3 times observed peak:

```yaml
    deploy:
      resources:
        limits: { memory: 1g }
```

Apply with `docker compose up -d --force-recreate` (brief downtime; ask first).

## 4. Postgres backups

Use `scripts/pg-backup.sh`. The traps it avoids:

- Never `docker exec -t` when piping a dump: the pseudo-TTY corrupts or truncates output.
- Read credentials inside the container, never hard-code them.
- Verify with `gzip -t`, and periodically prove a restore with `scripts/pg-restore-test.sh`.
- Retention is a disk budget: size it from dump size times copies kept.
- Backups on the same disk as the database protect against mistakes, not disk loss. Copy them off the host too.

## 5. Disk alert

`scripts/disk-alert.sh` hourly, warning at 80%. Test once by running it with `THRESHOLD=1`.

## 6. Weekly housekeeping

`scripts/docker-maintenance.sh`. Also cap build cache in `daemon.json`:

```json
"builder": { "gc": { "enabled": true, "defaultKeepStorage": "10GB" } }
```

## 7. Exposure and default credentials

```bash
docker ps --format '{{.Names}}\t{{.Ports}}' | grep -E '0\.0\.0\.0|:::'   # published to all interfaces
grep -rEil 'changeme|example|default' --include='*compose*' --include='.env*' <project-dirs>
```

- Bind internal services (databases, caches, object storage, admin UIs) to `127.0.0.1:`.
- Docker's published ports bypass `ufw`'s INPUT rules, so a firewall alone does not hide them.
- Replace placeholder secrets with real ones in an uncommitted `.env`.

## Done when

- [ ] No single container log over a few hundred MB; rotation verified on a recreated container
- [ ] `daemon.json` has log options and builder GC, validated, daemon restarted
- [ ] Long-running services have memory limits
- [ ] DB backups run, pass `gzip -t`, rotate, and one restore test has passed
- [ ] Disk alert fires below 100% (tested with a low threshold)
- [ ] No placeholder secrets; nothing internal published on all interfaces
