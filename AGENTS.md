Skills live in bucket folders under `skills/`:

- `engineering/`: guarding code work and keeping the agent's own setup healthy
- `operations/`: deploying and running self-hosted servers

Every skill is a folder holding `SKILL.md` and `agents/openai.yaml`. The folder name and the frontmatter `name` match.

Every skill is either **user-invoked** (`disable-model-invocation: true` in `SKILL.md` plus `policy.allow_implicit_invocation: false` in `agents/openai.yaml`) or **model-invoked** (neither). Keep the two files in sync. Anything that deploys, edits settings, deletes data, or installs scheduled jobs is user-invoked. User-invoked descriptions are a one-line summary for a human; model-invoked descriptions keep rich trigger phrasing.

Every skill appears in the top-level `README.md`, in its bucket's `README.md` (both grouped into **User-invoked** and **Model-invoked**, with the name linked to its `SKILL.md`), and in `.claude-plugin/plugin.json`'s `skills` array. Every release that should reach installed users bumps `version` in `.claude-plugin/plugin.json` (patch for fixes and wording, minor for a new skill or changed behaviour). Installed plugins only see an update when that field changes. Run `claude plugin validate .` after touching either manifest. Contributor instructions live here in `AGENTS.md`; `.claude/CLAUDE.md` imports this file for Claude Code, so the plugin root ships no `CLAUDE.md`.

When one skill needs another, write `Call the Skill tool with "<name>"`. A user-invoked skill can never be called that way: tell the user to run it instead. A skill that dispatches a subagent says to start it with a fresh context window.

Any step that is destructive, outward-facing, or hard to reverse asks the user first.

This repo is public. Never commit hostnames, IPs, usernames, home paths, emails, client or project names, passwords, or tokens. Use placeholders such as `<db-container>` and `example.com`.

No em dashes anywhere in this repo's prose, and no en dashes or `--` standing in for one. Rewrite the sentence instead.

Contributions are judged against `SCOPE.md` and follow `CONTRIBUTING.md`. Contributors never bump the version; the maintainer does when releasing. Run `python3 scripts/check.py` before committing; CI runs it, `shellcheck` and a secret scan on every pull request.

`main` is the release channel. The Claude plugin directory auto-publishes passing versions of `main`, so every push to `main` reaches directory users within about six hours. Do day-to-day work on a branch, and push to `main` only when releasing (with the version bumped and `python3 scripts/check.py` passing). Agents never push to `main` without the maintainer's explicit approval for that push.
