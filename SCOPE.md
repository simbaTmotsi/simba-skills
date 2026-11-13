# Scope

simba-skills keeps AI coding agents from hurting production on self-hosted servers, and keeps the agent's own setup clean. A contribution is merged only if it is **useful** and **safe**.

## Useful

At least one of these:

- **It fixes a real failure.** A skill did the wrong thing in a real session: you can say what you asked, what the agent did, and what it should have done.
- **It closes a real gap.** It covers a situation these skills are for (running tests, loops, migrations, deploys, backups or maintenance next to live systems) that they currently miss, and you hit that situation yourself.

Not in scope:

- Skills for one company, product or client. Keep those in your project's own `.claude/skills/`.
- Config options or branches for one person's workflow.
- New skills whose behaviour can be built from the existing ones.
- Rewording, restyling or reformatting without a failure behind it.

## Safe

Every change must keep these promises:

- **Nothing destructive or outward-facing happens without asking.** Deploying, deleting, pushing, sending, installing scheduled jobs and changing settings always ask first, and live in user-invoked skills.
- **No hidden behaviour.** No invisible characters, encoded payloads, or instructions that tell the agent to ignore the user, skip permission checks or hide what it does.
- **No surprise network calls.** Scripts contact only addresses the user supplies, and never download and run code.
- **No secrets or private details.** No real hostnames, IPs, paths, names, passwords or tokens. Use placeholders.
- **Secrets stay masked.** Anything that reads settings, env files or logs shows secret values masked.

These skills are installed with auto-update, so a merged change reaches every user's machine. That is why the safety bar is strict, and why every change needs a maintainer's review.
