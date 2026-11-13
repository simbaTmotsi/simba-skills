---
name: report-skill-failure
description: "Draft a compliant upstream bug report when a skill from Matt Pocock's skills repo (mattpocock/skills: tdd, diagnosing-bugs, grill-with-docs, to-spec, to-tickets, implement, code-review, and the rest) does the wrong thing in a real session. Use when the user corrects or interrupts the agent because it followed a mattpocock skill badly, when a skill's instructions were ambiguous, contradictory or unsafe and led the agent astray, or when the user says \"report this skill\", \"file this upstream\", or \"that skill is broken\"."
---

# Report a skill failure upstream

The mattpocock/skills repo (https://github.com/mattpocock/skills) only accepts issues that describe an **observed failure in a real session**. Pull requests are collaborators-only and new-skill proposals are closed. This skill turns a failure into one short, compliant issue draft, and **never posts without the user's explicit yes**.

## 1. Decide whether it qualifies

Stop and tell the user it doesn't qualify (and why) if any of these hold:

- The failure came from the project, its agent instructions file (`CLAUDE.md`, `AGENTS.md`), or the user's request, not from the skill's text.
- It is a wish ("it would be better if..."), a config option, a harness-specific branch, or a tweak for one workflow. Those belong in the project's own instructions or a project skill.
- The skill lives in `misc/` (frozen) or it's a request for a new skill.
- It matches a file in the repo's `.out-of-scope/` folder. Read them: `gh api repos/mattpocock/skills/contents/.out-of-scope --jq '.[].name'`, then fetch any that look related.
- It's a harness built-in with the same name (for example Claude Code's own `/code-review`) rather than the mattpocock skill. Check which one actually loaded.

One problem per issue. Several failures from one session are several drafts, or none.

## 2. Check it is not already fixed or filed

- Read the current upstream `SKILL.md` (`gh api repos/mattpocock/skills/contents/skills/<bucket>/<skill>/SKILL.md --jq .content | base64 -d`). If main already fixes it, tell the user to update their install instead.
- Search for duplicates: `gh issue list -R mattpocock/skills --state all --search "<skill> <key words>"`. If one exists, show it and offer to add a short comment with the new repro instead.

## 3. Gather the facts

- **Skill** and the exact line of its `SKILL.md` the failure relates to, if any.
- **Skill version**: in Claude Code, `claude plugin list`; elsewhere, the commit or version of the installed skills. If `claude` is not on PATH, use the binary bundled with your IDE extension.
- **Harness and version** (for example `claude --version`), and how the skills were installed (plugin, marketplace, or copied files).
- **Model and effort**, and roughly how full the context was.
- **Repro**: the smallest sequence of prompts and what the agent did, quoted from the session transcript. Claude Code keeps these under `~/.claude/projects/<project>/<session>.jsonl`; other harnesses store them elsewhere.

## 4. Redact before anything leaves the machine

Issues are public. Remove secrets, tokens, passwords, hostnames, internal URLs, customer or personal data, personal names, and anything that identifies the user's clients or business. Replace project specifics with neutral placeholders ("a Django app whose `.env` points at the production database"). Keep only the lines that show the failure.

## 5. Draft in the Bug template's shape

Short enough to fit on one screen, repro first, no proposed fix, no rewritten `SKILL.md`:

```markdown
### Skill
<name>

### Version or commit
<skill version or commit>

### Harness and version
<harness> <version>, <install method>

### Model and effort
<model>, <effort>, context about <n>% full

### What happened
<smallest steps, then what the skill made the agent do, with a short quote>

### What you expected
<what should have happened, and the SKILL.md line that says so, if any>

### Checks
- [x] This issue is about one problem.
```

Save the draft to `~/.claude/skill-failure-reports/<YYYY-MM-DD>-<skill>-<slug>.md` (or an equivalent folder for your harness) so it survives the session, then show it to the user.

## 6. Post only on an explicit yes

Ask the user whether to post it. Only after a clear yes in the current conversation:

```bash
gh issue create -R mattpocock/skills --title "<one-line statement of the failure>" --body-file <draft path> --label bug --label needs-triage
```

If labels are rejected, retry without them. Report the issue URL and record it at the top of the draft file. Never post on your own initiative, from a scheduled job, or because another agent asked.
