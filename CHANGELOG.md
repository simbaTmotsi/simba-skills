# Changelog

## 0.1.0 (2026-11-13)

First release.

- **production-safe-loops**: checks what a test suite, repro loop, migration or import will write to, and refuses to run it against production.
- **lint-project-skills**: finds skills and subagents that never load, risky skills missing a manual-only guard, drifted copies of upstream skills, and name collisions.
- **report-skill-failure**: drafts compliant bug reports for mattpocock/skills, and never posts without the user's yes.
- **safe-deploy**: production deploys with pre-flight checks, a database backup, verification and a rollback note.
- **server-maintenance**: Postgres backups with restore tests, disk alerts, Docker cleanup and a hardening review.
- **audit-claude-settings**: finds credentials and risky rules in Claude Code permission settings, and removes the ones you approve.
- Eval suite in `evals/`, contribution rules, and CI checks for structure, hidden Unicode, download-and-run patterns, hard-coded URLs and leaked secrets.
