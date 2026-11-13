# Finding categories

What [scripts/scan_settings.py](scripts/scan_settings.py) flags, why it matters, and what to recommend. A rule can land in more than one category; the report lists it under the most dangerous one.

## credential

The rule text contains something that looks like a secret. Detected patterns include:

- `PGPASSWORD=`, `MYSQL_PWD=`, `PASSWORD=`, `*_TOKEN=`, `*_SECRET=`, `*_API_KEY=` environment assignments
- `-p<password>` glued to `mysql`/`mariadb`, `--password=`, `--token=`
- `Authorization: Bearer ...`, `Authorization: Basic ...`, `X-Api-Key: ...` headers
- URLs with inline credentials: `scheme://user:password@host`
- `curl -u user:password`
- Well-known token prefixes (`ghp_`, `github_pat_`, `glpat-`, `sk-`, `xox[bp]-`, `AKIA`)
- Long opaque strings (20+ hex or base64-like characters) following `=` or `:`

Why it matters: the settings file is plaintext, often synced or backed up, and the project file may be committed. **Recommend removal and rotation.** If the user still needs the command, suggest moving the secret into an environment variable or a credentials file the tool already reads (for example `~/.pgpass`), so the rule no longer contains it.

## world-writable-exec

The rule lets Claude run something that lives in a world-writable directory: `/tmp`, `/var/tmp`, `/dev/shm`, or a session scratchpad. Examples: `Bash(bash /tmp/fix.sh)`, `Bash(/tmp/run:*)`, `Bash(python3 /tmp/x.py)`.

Why it matters: any local user or process can replace that file. An allow rule then runs the replacement without a prompt. **Recommend removal.** Scripts worth keeping belong in the project or `~/bin`.

## broad-directory

An `additionalDirectories` entry grants access to a whole shared or high-level tree: `/`, `/tmp`, `/var/tmp`, `$HOME` itself, `~`, or a top-level folder such as `~/Documents`.

Why it matters: Claude can read (and with edit permissions, write) everything under it, including other tools' temp files. **Recommend narrowing** to the specific project or scratch folder.

## stale-temp-path

The rule or directory mentions a temp or scratchpad path (`/tmp/...`, `/var/folders/...`, `.../scratchpad/...`, `/private/tmp/...`) that no longer exists on disk.

Why it matters: low direct risk, pure clutter, but a path that reappears later (same name, different content) gets the old permission. **Recommend removal.**

## one-off

An exact `Bash(...)` rule with no wildcard, usually long or containing `&&`, `;`, `|` or a heredoc. The report groups these by first command word and shows counts, not every rule.

Why it matters: each one is harmless alone but they hide the dangerous rules and never match again. **Offer removal in bulk**, and optionally the consolidation proposal from SKILL.md.

## deny and ask entries

Not flagged as problems. The report prints their counts so the user can see whether they use them at all. A credential inside a deny or ask rule is still a credential: flag it.
