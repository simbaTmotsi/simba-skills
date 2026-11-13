# Privacy policy

Effective 13 November 2026. Applies to the simba-skills plugin and skills published at https://github.com/simbaTmotsi/simba-skills.

## Summary

simba-skills has no server, no accounts, no analytics and no telemetry. The maintainer receives no data from you. The skills run inside your AI agent, on your machine, with your permissions.

## What the skills read and store, on your machine only

- **Database backups.** `server-maintenance` makes full copies of your Postgres databases. Those copies contain whatever your databases hold, which can include personal data about your own users. They are written only to a folder on your server that you choose, and are deleted on the retention schedule you set.
- **Bug report drafts.** `report-skill-failure` reads your agent session transcripts to describe a skill failure, removes secrets and identifying details, and saves the draft to `~/.claude/skill-failure-reports/`.
- **Settings, project files, env files and logs.** `audit-claude-settings`, `lint-project-skills`, `safe-deploy` and `production-safe-loops` read these to run their checks. Secret values are masked in anything they display. A backup of your settings file is made before any change.

## What can leave your machine, and only when you set it up or approve it

- **Alerts to a notification service you choose.** If you set `NTFY_URL`, `server-maintenance` sends short alerts to that address: the server's hostname plus either its disk usage and the names of its largest container logs, or the names of database containers whose backup failed. Never database contents. The service you choose handles that data under its own policy.
- **GitHub issues.** `report-skill-failure` can post a redacted bug report to github.com/mattpocock/skills through your own GitHub CLI login, and only after you explicitly approve that specific report. GitHub's privacy policy applies to what is posted.

Nothing else is sent anywhere by these skills.

## Your AI agent

The agent that runs these skills (for example Claude Code) processes what the skills read as part of your session, under that agent provider's own terms and privacy policy. simba-skills does not change what your agent provider receives beyond what your session already includes.

## Children

simba-skills is a developer tool and is not intended for anyone under 18.

## Changes and contact

Changes to this policy are made in this file, and its history is public in the repository. Questions: open an issue at https://github.com/simbaTmotsi/simba-skills/issues. Security concerns: report privately through the repository's Security tab.
