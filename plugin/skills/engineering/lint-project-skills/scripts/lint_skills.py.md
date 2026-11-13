# lint_skills.py

This is the source of `lint_skills.py`, kept as Markdown because the plugin directory does not accept executable files from unverified publishers. Do not retype it. Extract it exactly with the command in this skill's `SKILL.md`, which copies everything between the two fence lines below.

````python
#!/usr/bin/env python3
"""Lint Claude Code skills and subagents. Read-only.

Usage: lint_skills.py [ROOT ...]

Each ROOT is a skills dir, an agents dir or a commands dir; the kind is taken
from the last path component (skills / agents / commands). With no ROOT, scans
.claude/{skills,agents,commands} under the current directory and
~/.claude/{skills,agents}.

Prints a markdown table of findings. Risky-skill hits are keyword matches:
read the skill before reporting them. Drift against upstream is not checked
here; see classify_copy.sh.
"""
import os
import re
import sys
from collections import defaultdict

RISKY = [
    (r"\bdeploy(s|ing|ment)?\b", "deploy"),
    (r"\bprod(uction)?\b", "production"),
    (r"\bgit\s+push\b|\bpush\s+--force\b|--force-with-lease", "git push"),
    (r"\b(npm|pnpm|yarn|cargo|twine|gem)\s+publish\b|\bpoetry\s+publish\b", "publish"),
    (r"\bkubectl\s+(apply|delete|rollout|scale)\b|\bhelm\s+(upgrade|install|uninstall)\b", "kubernetes write"),
    (r"\bterraform\s+(apply|destroy)\b|\bpulumi\s+up\b", "infra apply"),
    (r"\bDROP\s+(TABLE|DATABASE|SCHEMA)\b|\bTRUNCATE\b|\bDELETE\s+FROM\b", "destructive SQL"),
    (r"\brm\s+-[a-z]*r[a-z]*f|\brm\s+-[a-z]*f[a-z]*r", "rm -rf"),
    (r"\bmigrat(e|ion)s?\b", "migration"),
    (r"\bsend(s|ing)?\s+(an?\s+)?(email|e-mail|message|slack|sms|notification)|\bwebhook\b|\bpost\s+to\s+slack\b", "sends outward"),
    (r"\bssh\s+\S+@|\bscp\s|\brsync\s.*:", "remote host"),
]
NAME_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")


def frontmatter(path):
    """Minimal YAML frontmatter reader: top-level `key: value`, block scalars."""
    try:
        text = open(path, encoding="utf-8").read()
    except (OSError, UnicodeDecodeError) as e:
        return None, "", f"unreadable: {e}"
    if not text.startswith("---"):
        return None, text, "no frontmatter block"
    end = text.find("\n---", 3)
    if end == -1:
        return None, text, "frontmatter not closed"
    block, body = text[3:end].strip("\n"), text[end + 4:]
    fm, key = {}, None
    for line in block.splitlines():
        m = re.match(r"^([A-Za-z0-9_-]+):\s*(.*)$", line)
        if m and not line.startswith((" ", "\t")):
            key, val = m.group(1), m.group(2).strip()
            if val in (">", "|", ">-", "|-", ">+", "|+"):
                val = ""
            fm[key] = val.strip("'\"")
        elif key and line.startswith((" ", "\t")):
            fm[key] = (fm[key] + " " + line.strip()).strip()
        elif line.strip() and not line.strip().startswith("#"):
            return fm, body, f"unparsed frontmatter line: {line.strip()[:40]}"
    return fm, body, None


def kind_of(root):
    base = os.path.basename(os.path.normpath(root))
    return base if base in ("skills", "agents", "commands") else "skills"


def level_of(root):
    home = os.path.realpath(os.path.expanduser("~/.claude"))
    return "personal" if os.path.realpath(root).startswith(home + os.sep) else "project"


def lint(roots):
    findings, names = [], defaultdict(list)

    def add(sev, path, check, problem, fix):
        findings.append((sev, path, check, problem, fix))

    for root in roots:
        if not os.path.isdir(root):
            continue
        kind, level = kind_of(root), level_of(root)
        for entry in sorted(os.listdir(root)):
            p = os.path.join(root, entry)
            if entry.startswith("."):
                continue
            if kind == "commands":
                if entry.endswith(".md"):
                    names[entry[:-3]].append((level, "command", p))
                continue
            if kind == "agents":
                if not entry.endswith(".md") or not os.path.isfile(p):
                    continue
                fm, _, err = frontmatter(p)
                if err:
                    add(2, p, "bad-frontmatter", err, "add or fix the --- frontmatter block")
                    continue
                missing = [k for k in ("name", "description") if not fm.get(k)]
                if missing:
                    add(2, p, "agent-missing-fields", f"missing {', '.join(missing)}",
                        f"add {' and '.join(missing)} to frontmatter")
                names["agent:" + (fm.get("name") or entry[:-3])].append((level, "agent", p))
                continue
            # skills
            if os.path.isfile(p) and entry.lower().endswith(".md"):
                add(1, p, "loose-file", "loose .md in skills dir; never loads",
                    f"git mv {p} {os.path.join(root, entry[:-3], 'SKILL.md')}")
                continue
            if not os.path.isdir(p):
                continue
            skill_md = os.path.join(p, "SKILL.md")
            if not os.path.isfile(skill_md):
                alt = [f for f in os.listdir(p) if f.lower() == "skill.md"]
                hint = f"rename {alt[0]} to SKILL.md" if alt else "add SKILL.md or move folder out"
                add(1, p, "missing-skill-md", "no SKILL.md; never loads", hint)
                continue
            fm, body, err = frontmatter(skill_md)
            if err:
                add(2, skill_md, "bad-frontmatter", err, "fix the frontmatter YAML")
                fm = fm or {}
            name = fm.get("name") or entry
            names[name].append((level, "skill", p + (" (symlink)" if os.path.islink(p) else "")))
            if fm.get("name") and fm["name"] != entry:
                add(3, skill_md, "name-mismatch", f"name '{fm['name']}' != folder '{entry}'",
                    f"set name: {entry}")
            if not NAME_RE.match(name) or len(name) > 64:
                add(4, skill_md, "bad-name", f"name '{name}' not lowercase-hyphen or >64 chars",
                    "rename to lowercase letters, digits, hyphens")
            desc = fm.get("description", "")
            if not desc:
                add(2, skill_md, "no-description", "description missing or empty",
                    "write 'What it does. Use when ...'")
            elif len(desc) > 1024:
                add(4, skill_md, "long-description", f"description is {len(desc)} chars (>1024)",
                    "shorten to under 1024 chars")
            guarded = str(fm.get("disable-model-invocation", "")).lower() == "true"
            if not guarded:
                hits = sorted({label for rx, label in RISKY if re.search(rx, body, re.I)})
                if hits:
                    add(2, skill_md, "risky-no-guard?", "mentions: " + ", ".join(hits),
                        "read it; if it acts, add disable-model-invocation: true")

    rank = {"personal": 0, "project": 1}
    for name, where in names.items():
        if len(where) > 1:
            ordered = sorted(where, key=lambda w: (rank[w[0]], w[1] != "skill"))
            winner = ordered[0]
            add(2, "; ".join(w[2] for w in where), "name-collision",
                f"'{name}' defined {len(where)} times; likely winner: {winner[0]} {winner[1]}",
                "rename or move aside the shadowed copy")
    return findings


def main():
    roots = sys.argv[1:] or [".claude/skills", ".claude/agents", ".claude/commands",
                             os.path.expanduser("~/.claude/skills"),
                             os.path.expanduser("~/.claude/agents")]
    findings = sorted(lint(roots), key=lambda f: (f[0], f[2], f[1]))
    sev = {1: "high", 2: "medium", 3: "low", 4: "nit"}
    print("| Severity | Path | Check | Problem | Suggested fix |")
    print("|---|---|---|---|---|")
    for s, path, check, problem, fix in findings:
        cell = lambda x: x.replace("|", "\\|")
        print(f"| {sev[s]} | `{cell(path)}` | {check} | {cell(problem)} | {cell(fix)} |")
    counts = defaultdict(int)
    for f in findings:
        counts[f[2]] += 1
    print()
    print(", ".join(f"{k}: {v}" for k, v in sorted(counts.items())) or "no findings")


if __name__ == "__main__":
    main()
````
