---
name: lint-project-skills
description: Lint Claude Code skills and subagents for files that never load, risky skills missing a manual-only guard, drifted copies of upstream skills, and name collisions. Use when the user asks to check, audit, lint or clean up their skills or agents, says a skill "isn't showing up" or "never triggers", mentions `.claude/skills` or `.claude/agents`, or has copied skills in from another repo.
---

# Lint Project Skills

Skills fail quietly. A file in the wrong place never loads and nothing says so; a deploy skill without a guard can be picked up by the model on its own; a copied skill keeps its old bugs after upstream fixed them. This skill finds those problems and reports them. **It is read-only until the user approves a fix.**

## Scope

Ask which to lint if it is not obvious; default to all that exist:

- Project: `.claude/skills/`, `.claude/agents/` (and the legacy `.claude/commands/`, for name collisions only)
- Personal: `~/.claude/skills/`, `~/.claude/agents/`

Plugin skills are namespaced (`plugin-name:skill-name`), so they cannot collide with these; leave installed plugins alone.

## Procedure

1. **Run the scanner.** `python3 scripts/lint_skills.py [root...]` (relative to this skill's folder; standard library only). With no arguments it scans the default roots above from the current directory. It prints a markdown table of findings.
2. **Review risky-skill hits by reading them.** The scanner flags skills whose body mentions deploying, production, deleting data, pushing, publishing or sending messages. Read each flagged `SKILL.md` and keep only the ones that really perform such an action. A skill that merely *explains* deploys is not risky.
3. **Check for copied upstream skills.** For each skill that looks copied (see [DRIFT.md](DRIFT.md) for the signs), classify it with `scripts/classify_copy.sh` as **current**, **stale copy** or **locally edited**. Ask the user for the upstream repo URL if you cannot tell. Skip symlinked skills that point into an upstream checkout: those are installs, not copies.
4. **Report** one table, most serious first:

   | Severity | Path | Problem | Suggested fix |
   |---|---|---|---|

   Order: will not load, risky without guard, name collision, stale copy, locally edited copy, metadata nits. Under the table, give counts per problem type. See [CHECKS.md](CHECKS.md) for each check's wording and fix.
5. **Ask which fixes to apply.** Offer them in batches by type. Wait for an explicit yes.
6. **Apply only the approved fixes**, in the way [CHECKS.md](CHECKS.md) describes for each. Use `git mv` inside a git repo so history follows the file. Never delete a skill; if one should go, move it aside and say where.
7. **Re-run the scanner** and show that the fixed findings are gone.

## Checks at a glance

- **Will not load:** a loose `name.md` directly in `.claude/skills/` (skills must be `name/SKILL.md`); a skill folder with no `SKILL.md` (wrong case counts as missing).
- **Metadata:** frontmatter does not parse; `name` differs from the folder name or uses characters other than lowercase letters, digits and hyphens; `description` missing, empty, or longer than 1024 characters.
- **Risky without guard:** performs a deploy, touches production, deletes data, pushes, publishes, or sends anything outward, and lacks `disable-model-invocation: true`.
- **Name collision:** the same skill name at two levels. As the Claude Code docs describe it, personal skills take precedence over project skills of the same name, so the project copy is silently shadowed. A skill and a legacy command with the same name also collide.
- **Subagents:** a file in `.claude/agents/` without frontmatter `name` or `description`, or a `name` that clashes with another agent.
- **Drift:** a copied upstream skill that is behind upstream (stale) or was edited locally (diverged).

## Things not to do

- Do not add `disable-model-invocation: true` to a skill the user relies on the model triggering, without saying that it will then only run when typed as `/name`.
- Do not "fix" a locally edited copy by overwriting it with upstream. Show the diff and let the user choose: keep, update and re-apply edits, or switch to installing from upstream.
- Do not rewrite descriptions or bodies beyond the specific finding.

## Done when

- The user has seen every finding with a suggested fix.
- Every applied fix was approved, and a re-scan confirms it.
