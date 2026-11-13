# Changelog

## 0.2.0 (2026-11-14)

- **Layout:** the plugin now lives in `plugin/`, so the folder submitted to the Claude plugin directory holds only skills, docs and the manifest. Repo tooling stays at the root.
- **Helper scripts ship as Markdown.** The seven scripts used by `server-maintenance`, `audit-claude-settings` and `lint-project-skills` are now `scripts/<name>.md` files. Each skill extracts them byte for byte with one `awk` command into a directory the user owns (never `/tmp`) before running them, so you can read every line first. Behaviour is unchanged.
- CI checks that `plugin/` holds only allowed file types, and parses and shellchecks the embedded scripts.

## 0.1.1 (2026-11-13)

- **report-skill-failure**: quote the description so YAML parsers read it correctly.
- Contributor instructions moved to `AGENTS.md` (imported by `.claude/CLAUDE.md`), so the plugin root no longer ships a `CLAUDE.md`.
- CI now fails on unquoted frontmatter values that contain `: ` or ` #`.

## 0.1.0 (2026-11-13)

First release.

- **production-safe-loops**: checks what a test suite, repro loop, migration or import will write to, and refuses to run it against production.
- **lint-project-skills**: finds skills and subagents that never load, risky skills missing a manual-only guard, drifted copies of upstream skills, and name collisions.
- **report-skill-failure**: drafts compliant bug reports for mattpocock/skills, and never posts without the user's yes.
- **safe-deploy**: production deploys with pre-flight checks, a database backup, verification and a rollback note.
- **server-maintenance**: Postgres backups with restore tests, disk alerts, Docker cleanup and a hardening review.
- **audit-claude-settings**: finds credentials and risky rules in Claude Code permission settings, and removes the ones you approve.
- Eval suite in `evals/`, contribution rules, and CI checks for structure, hidden Unicode, download-and-run patterns, hard-coded URLs and leaked secrets.
