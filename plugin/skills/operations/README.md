# Operations

Skills for deploying and running self-hosted servers.

## User-invoked

Reachable only when you type them (Claude Code: `disable-model-invocation: true`; Codex: `policy.allow_implicit_invocation: false` in `agents/openai.yaml`).

- **[safe-deploy](./safe-deploy/SKILL.md)**: Deploy a project to production with pre-flight checks, a database backup, verification, and a written rollback note.
- **[server-maintenance](./server-maintenance/SKILL.md)**: Set up or review routine maintenance on a self-hosted Docker box: Postgres backups with restore tests, disk alerts, Docker cleanup, and a hardening review.

## Model-invoked

None yet.
