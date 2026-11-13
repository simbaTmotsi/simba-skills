# Deploy gotchas

Traps that recur across self-hosted Docker stacks. Check each against the project during discovery.

## Compose

- **`restart` keeps the old image and the old env.** `docker compose restart` does not pick up a new build or env file changes. Only recreating the container does (`docker compose up -d ...`).
- **A bare `up -d` can recreate stateful services.** If the database, cache or search service's config changed, it restarts too. Name the app services and pass `--no-deps`.
- **Single-file bind mounts go stale.** When git replaces a mounted config file (for example a proxy config), the running container keeps reading the old inode. Recreate that container (`up -d --no-deps --force-recreate <svc>`) and confirm the file inside it changed.
- **A reboot applies the working tree.** If a systemd unit or `restart: always` brings the stack up from the repo on boot, anything merged into the compose file goes live at the next reboot, possibly on an old image. Keep the deploy branch deployable and check `docker compose ps` after any reboot.
- **Shared hosts.** Other projects' containers and a shared edge proxy may run on the same host. Filter by this project's compose project name or container prefix in every command.

## Migrations

- **Schema drift.** If production's migration history does not match the repo (missing version table, hand-applied changes), running the migrator can try to replay everything. Check the migration state table before trusting the tool.
- **Destructive or slow migrations** (drops, renames, type changes, big backfills, index builds on large tables) need their own plan: run them in a maintenance window, or split them into expand and contract steps.
- **Code and schema order.** If the new code needs the new schema, migrate before switching traffic. If the old code breaks on the new schema, there is downtime; say so in the plan.
- Hand-written SQL must be idempotent, shown to the user first, and run after the backup.

## Background work

- **Workers and schedulers.** Recreating a worker kills in-flight jobs. Check for running jobs and known schedules (nightly imports, billing runs) and avoid their windows. If a job was interrupted, re-run it after the deploy, with approval.
- **Non-atomic jobs** leave partial state when killed. Prefer graceful shutdown (`stop_grace_period`) and check the job's own status table.

## Images and secrets

- Tag the running image before building so rollback does not need a rebuild.
- `.env` files copied into an image ship secrets to anyone who can pull it. Check `.dockerignore` and, if the project has one, run its image secrets scan.
- Never print env values in output or notes; report variable names only.

## Verification

- A green container status is not a working app. Hit health endpoints and one real read-only page.
- Check cookies and redirects behind a TLS-terminating proxy (Secure flag, http to https).
- Avoid tests that write audit or business records in production.
