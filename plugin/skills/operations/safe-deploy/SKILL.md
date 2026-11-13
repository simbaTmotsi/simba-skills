---
name: safe-deploy
description: Deploy a project to production with pre-flight checks, a database backup, verification, and a written rollback note.
disable-model-invocation: true
---

# Safe deploy

A production deploy for a project running on a host you can reach. Every step that changes running state needs the user's explicit go-ahead in this conversation. Touch only this project's containers and services; other stacks on the same host (shared proxies, other apps) are off limits.

## 1. Discover how this project deploys (read-only)

Find the existing path before inventing one. Look at, in parallel:

- `docker-compose*.yml` / `compose*.yaml`, `Dockerfile*`, `.env*` examples
- deploy or manage scripts (`scripts/`, `bin/`, `Makefile`, `justfile`, `package.json` scripts)
- CI and CD config (`.github/workflows/`, `.gitlab-ci.yml`), systemd units that start the stack on boot
- `README`, `CLAUDE.md`, `AGENTS.md`, `docs/` for deploy notes, past incidents and "never do X" rules
- the running state: `docker compose ps`, `docker ps --format '{{.Names}}\t{{.Image}}\t{{.Status}}'`

Write down: which services are app services (safe to recreate) versus stateful ones (database, cache, search, proxy), how migrations run, where health endpoints live, and any scheduled jobs that must not be interrupted. If CI deploys on merge, stop: the deploy is a merge, not this procedure.

See [references/deploy-gotchas.md](references/deploy-gotchas.md) for traps that recur across stacks.

## 2. Pre-flight (read-only, run in parallel)

- `git status --short` and `git log --oneline origin/<branch>..HEAD`: what ships, and is it committed and pushed? Uncommitted code has no rollback point.
- The project's tests on the changed areas, against a test database, never production.
- Compose config validates: `docker compose --env-file <env> config -q`.
- The env file exists and has every variable the new code reads (compare against the example file; report names only, never values).
- Disk headroom: `df -h` and `docker system df`. A build plus a backup needs room.
- Pending migrations: list what will run (for example `makemigrations --check`, `prisma migrate status`, `alembic current` vs `heads`). Flag anything destructive (drops, renames, type changes) or long-running.
- Scheduled jobs: is a cron job, worker task or import running now, or due soon? Do not deploy over one.

Stop and report if anything fails.

## 3. Show the plan and get approval

List the commits, migrations, env changes, which services will be recreated, expected downtime, and the rollback path. Ask the user to confirm before going further.

## 4. Back up the database

Take a fresh dump before anything changes, using the project's own backup script if one exists. Otherwise, for Postgres:

```bash
f="$BACKUP_DIR/<project>-pre-deploy-$(date +%Y%m%d-%H%M%S).dump"
docker exec <db-container> sh -c 'pg_dump -U "$POSTGRES_USER" -Fc "$POSTGRES_DB"' > "$f"
ls -la "$f"; docker exec -i <db-container> pg_restore -l < "$f" | grep -c 'TABLE DATA'
```

The file must be non-empty and the table count sane. No verified backup, no deploy.

## 5. Deploy (irreversible step: confirm again)

Restate in one line what is about to happen and wait for a yes. Then:

1. Record the rollback point: current git SHA and the running image ID of each app service. Tag those images (`docker tag <image-id> <app>:pre-<sha>`) so rollback is one command.
2. Build with the project's build command. If the project has a secrets-in-image check, run it and stop on any finding.
3. Recreate only the app services: `docker compose up -d --no-deps <app-services>`.
4. Run migrations the way the project does, if they are not run on container start.
5. Confirm each app container runs the new image ID.

## 6. Verify

Before any polling or retry loop against production, call the Skill tool with "production-safe-loops".

- `docker compose ps`: every service up and healthy, no restart loops.
- Logs since the deploy, per app service: `docker logs --since 10m <container> 2>&1 | grep -iE 'traceback|error|fatal| 5[0-9]{2} '`.
- Health endpoints and the public URL return the expected status codes.
- One read-only request that exercises real data (a list page or API call). Do not create, edit or delete production records to test.
- Migrations recorded as applied.

If anything is broken, report it with the log lines and offer the rollback. Do not roll back without a yes.

## 7. Write the rollback note

Save a note using [references/rollback-note.md](references/rollback-note.md) wherever the project keeps deploy records (ask if unclear), and show it to the user. It must be specific enough that someone else could roll back without this conversation.
