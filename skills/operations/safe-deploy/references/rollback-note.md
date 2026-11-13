# Rollback note template

Fill every field. Write "none" rather than leaving one blank.

```markdown
# Deploy <project> <YYYY-MM-DD HH:MM TZ>

## What shipped
- Git: <old-sha> -> <new-sha> (<branch>)
- Commits: <one line each>
- Services recreated: <list>
- Migrations applied: <list, or none>
- Hand-run SQL or data changes: <list, or none>
- Env changes (names only): <list, or none>

## Backup
- File: <path>
- Size and table count: <size>, <n> tables
- Verified with: <command>

## Verification
- Container status: <summary>
- Health checks: <url or endpoint -> status>
- Errors in logs since deploy: <none, or excerpt>

## Rollback
1. Code: `docker tag <app>:pre-<old-sha> <app>:<running-tag>` for each app image,
   then `docker compose up -d --no-deps <app-services>`.
2. Schema: <is the old code compatible with the new schema? If not, the down
   migration or SQL to reverse it>.
3. Data: restore from the backup above only if data was damaged:
   `docker exec -i <db-container> pg_restore -U <db-user> -d <db-name> --clean < <backup-file>`
   (this overwrites everything written since the backup; ask first).

## Follow-ups
- <interrupted jobs to re-run, warnings seen, cleanup of old images or dumps>
```
