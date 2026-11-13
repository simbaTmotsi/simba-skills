# simba-skills

Agent skills for running self-hosted production safely. They come from running several Docker-hosted apps on one Linux box, where the agent, the test suite and the live deployment all share a host, and from keeping Claude Code's own settings and skills in good shape.

They work alongside [Matt Pocock's skills](https://github.com/mattpocock/skills): `production-safe-loops` guards the feedback loops that `tdd` and `diagnosing-bugs` build, and `report-skill-failure` turns a misbehaving skill into a compliant upstream issue.

## Install

Pick one route. Installing both gives you every skill twice.

**Claude Code plugin** (namespaced as `/simba-skills:<name>`):

```bash
claude plugin marketplace add simbaTmotsi/simba-skills
claude plugin install simba-skills@simba-skills
```

**Any other agent, or files you can edit** (skills.sh):

```bash
npx skills@latest add simbaTmotsi/simba-skills
```

## Engineering

### User-invoked

- **[audit-claude-settings](./skills/engineering/audit-claude-settings/SKILL.md)**: Audit Claude Code permission settings for leaked credentials, stale temp-path rules, risky allow rules and rule pile-up, then clean up what you approve.

### Model-invoked

- **[production-safe-loops](./skills/engineering/production-safe-loops/SKILL.md)**: Check what a test suite, repro loop, migration or import will actually write to, and refuse to run it against production.
- **[lint-project-skills](./skills/engineering/lint-project-skills/SKILL.md)**: Find skills and subagents that never load, risky skills missing a manual-only guard, drifted copies of upstream skills, and name collisions.
- **[report-skill-failure](./skills/engineering/report-skill-failure/SKILL.md)**: Draft a compliant bug report for mattpocock/skills when one of its skills misbehaves in a real session. Never posts without your yes.

## Operations

### User-invoked

- **[safe-deploy](./skills/operations/safe-deploy/SKILL.md)**: Deploy a project to production with pre-flight checks, a database backup, verification, and a written rollback note.
- **[server-maintenance](./skills/operations/server-maintenance/SKILL.md)**: Set up or review routine maintenance on a self-hosted Docker box: Postgres backups with restore tests, disk alerts, Docker cleanup, and a hardening review.

## Principles

- Anything that deploys, edits settings, deletes data or installs scheduled jobs is user-invoked, so the model can never start it on its own.
- Every destructive or outward-facing step asks first.
- Secrets are masked in output, and a credential that was ever stored in plain text gets rotated, not just deleted.

## License

MIT
