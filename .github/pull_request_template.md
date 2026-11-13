## What and why

Closes #

<!-- One problem per pull request. Link the accepted issue above. -->

## How I tested it

<!-- Which agent and version, what you asked it, and what it did with this change. -->

## Safety checklist

- [ ] Anything destructive or outward-facing asks first and is in a user-invoked skill.
- [ ] Scripts only contact addresses the user supplies, and never download and run code.
- [ ] No secrets, hostnames, IPs, paths or names from real systems.
- [ ] `python3 scripts/check.py` passes, and `shellcheck -S warning` passes on any script I changed.
- [ ] I did not bump the version in `plugin.json`.
