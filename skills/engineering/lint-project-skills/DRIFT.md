# Detecting drifted copies of upstream skills

People copy skills from public repos into `.claude/skills/`. Upstream then fixes bugs and the copy never hears about it. The goal is to sort every copied skill into one of three buckets:

- **current:** every file is byte-identical to upstream's latest version.
- **stale copy:** every file matches *some* past upstream version, but not the latest. Safe to update: nothing local would be lost.
- **locally edited:** at least one file matches no upstream version. Someone changed it; updating would discard their edits.

## Signs a skill was copied

- A `README`, comment or commit message naming a source repo.
- Frontmatter fields such as `source:`, `upstream:`, `homepage:` or `metadata:` with a URL.
- A sibling `agents/openai.yaml`, `LICENSE` or other files typical of a published skills repo.
- The same folder name as a skill in a well-known skills repo the user mentions.
- Git history: `git log --diff-filter=A --follow -- .claude/skills/<name>/SKILL.md` shows it arriving in one bulk commit.

If none of these settle it, ask the user where the skill came from. Do not guess an upstream.

## Classifying

Clone the upstream once into a scratch directory with full history (stale detection needs old versions):

```bash
git clone --quiet <upstream-url> <scratch>/upstream
```

Then, for each copied skill:

```bash
scripts/classify_copy.sh .claude/skills/<name> <scratch>/upstream <path/of/skill/in/upstream>
```

The script hashes each local file with `git hash-object` and looks for that blob in the upstream file's history (following renames). It prints a verdict per file and an overall verdict. For a stale copy it names the newest upstream commit whose version matches, so you can say how far behind it is. For a locally edited file it prints `git diff --no-index` against upstream's latest.

If the skill moved inside the upstream repo, pass its current upstream path; the script follows renames backwards.

## Reporting

One row per copied skill: name, verdict, how far behind (date of matching upstream commit), and for locally edited copies a one-line summary of what the local edit changed. Do not paste whole diffs into the table; offer them on request.
