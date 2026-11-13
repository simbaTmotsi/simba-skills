# Engineering

Skills that guard code work and keep the agent's own setup healthy.

## User-invoked

Reachable only when you type them (Claude Code: `disable-model-invocation: true`; Codex: `policy.allow_implicit_invocation: false` in `agents/openai.yaml`).

- **[audit-claude-settings](./audit-claude-settings/SKILL.md)**: Audit Claude Code permission settings for leaked credentials, stale temp-path rules, risky allow rules and rule pile-up, then clean up what you approve.

## Model-invoked

Model- or user-reachable (rich trigger phrasing so the model can reach for them).

- **[production-safe-loops](./production-safe-loops/SKILL.md)**: Check what a test suite, repro loop, migration or import will actually write to, and refuse to run it against production.
- **[lint-project-skills](./lint-project-skills/SKILL.md)**: Find skills and subagents that never load, risky skills missing a manual-only guard, drifted copies of upstream skills, and name collisions.
- **[report-skill-failure](./report-skill-failure/SKILL.md)**: Draft a compliant bug report for mattpocock/skills when one of its skills misbehaves in a real session. Never posts without your yes.
