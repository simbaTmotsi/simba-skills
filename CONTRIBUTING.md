# Contributing

Thanks for helping. Read [SCOPE.md](./SCOPE.md) first: it is the bar every change is judged against.

## Where things go

| You have | Do this |
| --- | --- |
| A skill did the wrong thing | Open a [bug report](https://github.com/simbaTmotsi/simba-skills/issues/new?template=bug.yml) |
| A gap you hit in real use | Open an [idea](https://github.com/simbaTmotsi/simba-skills/issues/new?template=idea.yml) before writing code |
| A security problem | Report it privately: see [SECURITY.md](./SECURITY.md). Do not open a public issue |
| A fix for an issue marked `accepted` | Open a pull request |

Pull requests without an `accepted` issue are usually closed, so agree on the problem first. Small fixes to wording that is wrong (not just different) are the exception.

## Making a pull request

1. Fork the repo and create a branch.
2. Keep to one problem per pull request.
3. Follow the conventions in [AGENTS.md](./AGENTS.md). In short: each skill is a folder with `SKILL.md` and `agents/openai.yaml`; anything destructive is user-invoked; no em dashes; no private details.
4. Run the checks locally: `python3 scripts/check.py` (and `shellcheck` on any script you touch).
5. Do not bump the version in `plugin.json`. The maintainer does that when releasing.
6. Fill in the pull request template, including how you tested the change in a real agent session.

## How review works

- Every pull request needs the checks to pass and an approving review from the maintainer before it can merge.
- The checks look for broken skill structure, invisible Unicode, download-and-run patterns, hard-coded URLs in scripts, private paths, leaked secrets and em dashes. Passing them is necessary, not sufficient.
- The maintainer reads every changed line, including scripts, with the safety rules in SCOPE.md in mind.
- GitHub Actions do not run on an outside contributor's pull request until the maintainer approves them.

## Using an AI agent to contribute

Welcome, but you own what you submit. Keep issues short with the repro first, and check that the agent did not add private details from your own projects.
