# Checks and fixes

Each check, as [scripts/lint_skills.py](scripts/lint_skills.py) reports it, with the fix to suggest. Apply a fix only after the user approves it.

## loose-file (will not load)

`.claude/skills/deploy.md` sits directly in the skills folder. Claude Code only discovers skills as `<name>/SKILL.md`, so this file is ignored.

Fix:

```bash
mkdir -p .claude/skills/deploy
git mv .claude/skills/deploy.md .claude/skills/deploy/SKILL.md   # plain mv outside git
```

Then make sure it has frontmatter with `name: deploy` and a `description`. If the user meant it as a slash command rather than a skill, `.claude/commands/deploy.md` is the legacy alternative; ask which they want.

## missing-skill-md (will not load)

A folder under `skills/` with no `SKILL.md`. Common causes: `skill.md` or `Skill.md` (wrong case), the file one level too deep, or a folder of reference files with no entry point.

Fix: rename to exactly `SKILL.md`, or move it up a level. If the folder is not a skill, suggest moving it out of the skills directory.

## bad-frontmatter

No `---` block at the top, or it does not parse. Fix the YAML; the commonest cause is an unquoted description containing `: `. Quote the value.

## name-mismatch / bad-name

Frontmatter `name` differs from the folder name, or contains anything other than lowercase letters, digits and hyphens (64 characters max under the Agent Skills spec). A mismatch means the name the user types and the folder they edit disagree. Fix: change the frontmatter `name` to the folder name (renaming the folder instead changes how the skill is invoked: ask).

## no-description / long-description

The description is how the model decides to use a skill. Missing or empty means it is unlikely ever to be picked. Over 1024 characters exceeds the Agent Skills spec limit, and long descriptions may be cut short in the skill listing. Fix: propose a rewrite in the form "What it does. Use when ...", and let the user edit it.

## risky-no-guard

The skill deploys, touches production, deletes or migrates data, pushes or force-pushes, publishes packages, or sends email, chat messages or webhooks, and it lacks `disable-model-invocation: true`. Without the guard the model may decide to run it on its own.

Fix: add the line to the frontmatter:

```yaml
---
name: deploy-prod
description: Deploy the app to production.
disable-model-invocation: true
---
```

Tell the user it will now run only when they type `/deploy-prod`. If the repo also ships `agents/openai.yaml` files, the matching setting there is `policy: allow_implicit_invocation: false`.

## name-collision

The same name in two places. Report which one wins. Per the Claude Code docs: enterprise-managed beats personal, personal beats project, and a skill beats a legacy command of the same name. Plugin skills are namespaced and do not collide. Fix: rename the one the user wants to keep both of, or remove the shadowed duplicate (move it aside, do not delete).

## stale-copy / locally-edited

See [DRIFT.md](DRIFT.md). Fix for a stale copy: replace with the current upstream version, after showing the diff. For a locally edited copy: show the diff against upstream and let the user decide.

## agent-missing-fields

A subagent file in `.claude/agents/` without frontmatter `name` or `description`. The description is what routes work to the agent. Fix: add the missing field; default `name` to the file name without `.md`.
