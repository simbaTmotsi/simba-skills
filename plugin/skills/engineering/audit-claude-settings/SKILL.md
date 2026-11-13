---
name: audit-claude-settings
description: Audit Claude Code permission settings for leaked credentials, stale temp-path rules, risky allow rules and rule pile-up, then clean up what you approve.
disable-model-invocation: true
---

# Audit Claude Settings

Every "Yes, and don't ask again" adds an exact command to an allow list. After a few months the list holds hundreds of one-off rules, and some of them carry whatever was on the command line: passwords, bearer tokens, database URLs, scripts in `/tmp`. This skill finds those rules, shows them to the user with secrets masked, and removes only what the user approves.

Nothing is changed without an explicit yes. Broadening a permission is never done here, only proposed.

## Files in scope

- `~/.claude/settings.json` (user)
- `.claude/settings.json` (project, usually committed to git)
- `.claude/settings.local.json` (project, personal, usually gitignored)

Ask which of these to audit; default to all that exist. Managed (enterprise) settings are out of scope: report them if found, never edit them.

Each file may hold `permissions.allow`, `permissions.ask`, `permissions.deny` and `permissions.additionalDirectories`. Audit all four.

## Helper script

The scanner ships as Markdown at [scripts/scan_settings.py.md](scripts/scan_settings.py.md), because the plugin directory does not accept executable files. Before step 2, extract it from this skill's folder into a directory only the user can write (never `/tmp`). Extract with `awk`, which copies exactly the lines between the two fence lines; never retype the code.

```bash
d=~/.cache/simba-skills/audit-claude-settings; mkdir -p "$d" && chmod 700 "$d"
awk '/^````/{f=!f; next} f' scripts/scan_settings.py.md > "$d/scan_settings.py"
```

It needs only the Python standard library. Below, `$d` is that directory.

## Rules for handling secrets

- **Never `cat`, `Read` or otherwise print a settings file whole.** That copies every secret into the transcript. Use the scanner, which masks values.
- When you quote a rule, quote the masked form. Never echo a secret back, even to confirm it.
- Removal is by rule id (for example `allow:117`), so you never need to type the secret.

## Procedure

1. **Back up.** For each file in scope, copy it beside itself with a timestamp, keeping permissions:
   `cp -p settings.json settings.json.bak-$(date +%Y%m%d-%H%M%S)`
   Tell the user where the backups are. The backups contain the same secrets, so they get deleted (or kept off any shared disk) once the user is happy.
2. **Scan.** Run `python3 "$d/scan_settings.py" scan <file>...`. It prints a categorised report: see [CATEGORIES.md](CATEGORIES.md) for what each category means and how it is detected.
3. **Review the hits yourself.** The scanner is pattern-based. Drop obvious false positives (a rule that mentions `token` as a word, not a value) and add anything it missed that you can see in the masked output. Say which you changed and why.
4. **Present the report** grouped by category, most dangerous first:
   1. Credentials in rules
   2. Executes from a world-writable directory
   3. Over-broad `additionalDirectories`
   4. Temp or scratchpad paths that no longer exist
   5. One-off exact-command pile-up (counts per command, not every rule)

   For each group give the ids, masked rules and a one-line reason. End with totals: rules per file, flagged per category.
5. **Ask what to remove.** Offer sensible batches ("all credential rules", "all stale temp paths") and let the user strike individual ids. Wait for an explicit answer.
6. **Remove.** `python3 "$d/scan_settings.py" remove <file> allow:117 allow:203 ...`. The script re-reads the file, drops exactly those entries, writes it back with 2-space indentation and re-parses it. If the user's file used different formatting, say that the diff will show whitespace changes.
7. **Validate.** Re-run `scan` on the file and confirm it parses and the removed ids are gone. If anything fails, restore from the backup and stop.
8. **Rotate.** If any credential rule was found, say plainly: **deleting the rule does not un-leak the secret.** It sat in plaintext on disk, possibly in backups, and possibly in session transcripts under `~/.claude/projects/`. Every such credential must be rotated at its source (new password, revoked token). List which services the user needs to rotate, by kind ("a database password", "an API token for the deploy service"), not by value.
9. **Check git.** If a flagged rule lived in a committed `.claude/settings.json`, run `git log -p --follow -- .claude/settings.json` piped through the scanner's `mask` mode (`... | python3 "$d/scan_settings.py" mask`) to see whether it was ever pushed. If it was, rotation is mandatory and history rewriting is the user's decision.

## Optional: consolidation proposal

If the one-off pile-up is large, propose (do not apply) a handful of wildcard rules that would cover the read-only majority, for example `Bash(git log:*)` or `Bash(ls:*)`. State the trade-off: each wildcard grants more than the exact rules it replaces. Never propose wildcards for interpreters, shells, package managers that run scripts, `ssh`, `curl` to arbitrary hosts, or anything under `/tmp`. Only after the user picks specific wildcards, add those and remove the exact rules they cover, in one approved edit.

## Point out the other lists

Remind the user that settings also support `permissions.deny` (always blocked) and `permissions.ask` (always prompts). As far as the docs describe, deny is checked first, then ask, then allow. A good outcome of this audit is often a short deny list, for example reads of `.env` files or `Bash(rm -rf:*)`, rather than a longer allow list.

## Done when

- Backups exist and the user knows where.
- The user approved every removal, and each edited file parses.
- The rotation reminder was given for every credential found, even ones the user chose not to remove.
