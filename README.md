# simba-skills

**Six skills that stop your AI coding agent from hurting production, and keep its own setup clean.**

Made for people who run their apps on their own server (Docker, Postgres, a VPS) and use an AI agent such as Claude Code on that same machine. That setup is convenient, but it means one wrong test run, repro loop or deploy can hit live data. These skills put guard rails around exactly those moments.

## Quick start (Claude Code)

**1. Add this repo as a plugin source and install it:**

```bash
claude plugin marketplace add simbaTmotsi/simba-skills
claude plugin install simba-skills@simba-skills
```

**2. Restart Claude Code.** That's it. The skills now work in every project.

**3. Try one:** type `/simba-skills:server-maintenance` in any session, or just ask Claude to run your tests and watch `production-safe-loops` check where they will write first.

> Using Cursor, Codex, Copilot or another agent? Run `npx skills@latest add simbaTmotsi/simba-skills` instead. Pick one install method, not both, or you'll get every skill twice.

## What's inside

There are two kinds of skill:

- **Automatic**: the agent uses it on its own when the situation fits. You can also type it.
- **You type it**: only runs when you type `/simba-skills:<name>`. Everything that deploys, deletes, or changes settings is in this group, so the agent can never start it by itself.

| Skill | What it does for you | How it starts |
|---|---|---|
| `production-safe-loops` | Before running tests, repro loops, migrations or imports, checks what they will actually write to, and refuses if that's your live database or site. | Automatic |
| `lint-project-skills` | Finds skills that silently never load, risky skills that the agent could trigger by itself, and copied skills that have gone out of date. | Automatic |
| `report-skill-failure` | When one of [Matt Pocock's skills](https://github.com/mattpocock/skills) misbehaves, drafts a bug report in the format that repo accepts. Never posts without your yes. | Automatic |
| `safe-deploy` | Deploys to production step by step: checks, shows you the plan, backs up the database, deploys, verifies, and writes down how to roll back. | You type it |
| `server-maintenance` | Sets up nightly database backups (with a restore test), disk-space alerts, Docker cleanup, and a security review for your server. | You type it |
| `audit-claude-settings` | Scans your Claude Code permission settings for passwords, tokens and risky rules that piled up, and removes the ones you approve. | You type it |

## Examples

- **You:** "fix the failing signup test." **Agent:** notices your `.env` points at the production database, and runs the test against a throwaway test database instead.
- **You:** `/simba-skills:safe-deploy`. **Agent:** finds how this project deploys, lists the commits and migrations going out, asks you to confirm, takes a backup, deploys, checks the logs and health page, and saves a rollback note.
- **You:** "why isn't my deploy skill showing up?" **Agent:** finds it was saved as `deploy.md` instead of `deploy/SKILL.md`, and offers to move it.
- **You:** `/simba-skills:audit-claude-settings`. **Agent:** backs up your settings, lists the risky rules with secrets hidden, removes what you approve, and reminds you to change any password that was stored there.

## Keeping it up to date

Turn on auto-update once and new versions arrive whenever Claude Code starts. Add `"autoUpdate": true` to this marketplace in `~/.claude/settings.json`:

```json
"extraKnownMarketplaces": {
  "simba-skills": {
    "source": { "source": "github", "repo": "simbaTmotsi/simba-skills" },
    "autoUpdate": true
  }
}
```

Or update by hand at any time:

```bash
claude plugin update simba-skills@simba-skills
```

To remove it: `claude plugin uninstall simba-skills@simba-skills`.

## Good to know

- **Nothing risky happens silently.** Every step that deletes, deploys, pushes or installs a scheduled job asks you first.
- **Secrets stay hidden.** Skills mask passwords and tokens in their output. If one was ever stored in plain text, they tell you to change it, because deleting it is not enough.
- **Works on its own.** You don't need Matt Pocock's skills. If you have them, `production-safe-loops` also guards the loops his `tdd` and `diagnosing-bugs` skills build.
- **Built for Linux servers running Docker.** The server and deploy skills assume Docker Compose and Postgres, and adapt to whatever deploy scripts your project already has.

## Contributing

Contributions are welcome when they are useful and safe. Read [SCOPE.md](./SCOPE.md) for the bar and [CONTRIBUTING.md](./CONTRIBUTING.md) for how. In short:

- **A skill did the wrong thing?** [Open a bug report](https://github.com/simbaTmotsi/simba-skills/issues/new?template=bug.yml) with what you asked, what the agent did, and what you expected.
- **Hit a gap in real use?** [Open an idea](https://github.com/simbaTmotsi/simba-skills/issues/new?template=idea.yml) before writing code.
- **Found a security problem?** Report it privately, as described in [SECURITY.md](./SECURITY.md).

Every pull request is checked automatically and reviewed by the maintainer before it can merge.

## License

MIT
