#!/usr/bin/env python3
"""Repo checks for simba-skills. Runs in CI on every pull request and locally:

    python3 scripts/check.py

Exits non-zero on any failure. Warnings are printed but do not fail the run.
Standard library only.
"""
import glob
import json
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)

failures = []
warnings = []


def fail(path, msg):
    failures.append(f"{path}: {msg}")


def warn(path, msg):
    warnings.append(f"{path}: {msg}")


def tracked_files():
    out = subprocess.run(["git", "ls-files", "-z"], capture_output=True, text=True, check=True).stdout
    return [f for f in out.split("\0") if f]


def frontmatter(text):
    if not text.startswith("---\n"):
        return None, text
    end = text.find("\n---", 4)
    if end == -1:
        return None, text
    return text[4:end], text[end + 4:]


# 1. Skill structure and invocation pairing
skill_dirs = sorted(os.path.dirname(p) for p in glob.glob("skills/*/*/SKILL.md"))
for d in skill_dirs:
    skill_md = f"{d}/SKILL.md"
    fm, _ = frontmatter(open(skill_md, encoding="utf-8").read())
    if fm is None:
        fail(skill_md, "missing YAML frontmatter")
        continue
    name = re.search(r"^name:\s*(.+)$", fm, re.M)
    desc = re.search(r"^description:\s*(.+)$", fm, re.M)
    if not name or name.group(1).strip().strip("\"'") != os.path.basename(d):
        fail(skill_md, "frontmatter `name` must equal the folder name")
    if not desc or not desc.group(1).strip():
        fail(skill_md, "missing `description`")
    elif len(desc.group(1).strip().strip("\"'")) > 1024:
        fail(skill_md, "description is over 1024 characters")
    for line in fm.splitlines():
        kv = re.match(r"^([A-Za-z_-]+):\s+(.*)$", line)
        if kv and kv.group(2) and kv.group(2)[0] not in "\"'[{|>" and (": " in kv.group(2) or " #" in kv.group(2)):
            fail(skill_md, f"frontmatter `{kv.group(1)}` contains ': ' or ' #' unquoted; wrap the value in double quotes")
    user_invoked = re.search(r"^disable-model-invocation:\s*true\s*$", fm, re.M) is not None
    yaml_path = f"{d}/agents/openai.yaml"
    if not os.path.exists(yaml_path):
        fail(d, "missing agents/openai.yaml")
    else:
        policy_off = "allow_implicit_invocation: false" in open(yaml_path, encoding="utf-8").read()
        if user_invoked != policy_off:
            fail(d, "disable-model-invocation in SKILL.md and allow_implicit_invocation in agents/openai.yaml disagree")

for loose in glob.glob("skills/*/*.md"):
    if os.path.basename(loose) != "README.md":
        fail(loose, "skills must be folders with SKILL.md, not loose .md files")

# 2. Manifest and READMEs list exactly the skills that exist
plugin = json.load(open(".claude-plugin/plugin.json", encoding="utf-8"))
listed = sorted(p.rstrip("/").removeprefix("./") for p in plugin.get("skills", []))
if listed != skill_dirs:
    fail(".claude-plugin/plugin.json", f"`skills` must list exactly {skill_dirs}, found {listed}")
if not re.fullmatch(r"\d+\.\d+\.\d+", str(plugin.get("version", ""))):
    fail(".claude-plugin/plugin.json", "`version` must be MAJOR.MINOR.PATCH")
readme = open("README.md", encoding="utf-8").read()
for d in skill_dirs:
    name = os.path.basename(d)
    if f"`{name}`" not in readme and f"{d}/SKILL.md" not in readme:
        fail("README.md", f"does not mention skill `{name}`")
    bucket_readme = os.path.join(os.path.dirname(d), "README.md")
    if not os.path.exists(bucket_readme) or f"./{name}/SKILL.md" not in open(bucket_readme, encoding="utf-8").read():
        fail(bucket_readme, f"does not link ./{name}/SKILL.md")

# 3. Text hygiene and safety over every tracked text file
TEXT_EXT = (".md", ".yml", ".yaml", ".json", ".sh", ".py", ".txt")
HIDDEN = re.compile("[​-‏‪-‮⁠-⁤⁦-⁩﻿\U000e0000-\U000e007f]")
DASHES = re.compile("[–—]")
HOME_PATH = re.compile(r"(?<![\w$~])/(home|Users)/[A-Za-z0-9_.-]+")
DANGEROUS = [
    (re.compile(r"\b(curl|wget)\b[^\n|]*\|\s*(sudo\s+)?(ba|z)?sh\b"), "pipes a download straight into a shell"),
    (re.compile(r"base64\s+(-d|--decode)[^\n|]*\|\s*(ba|z)?sh\b"), "decodes and executes hidden content"),
    (re.compile(r"\beval\s+[\"']?\$\((curl|wget)"), "evaluates downloaded code"),
    (re.compile(r"\brm\s+-[a-zA-Z]*r[a-zA-Z]*f?\s+(/|~|\$HOME)\s*($|[;&|])", re.M), "deletes a root or home directory"),
    (re.compile(r"\bchmod\s+(-R\s+)?777\b"), "makes files world-writable"),
    (re.compile(r"/dev/tcp/|\bnc\b[^\n]*\s-e\s"), "opens a reverse shell"),
    (re.compile(r"--no-verify\b"), "skips git hooks"),
    (re.compile(r"dangerously-skip-permissions|bypassPermissions"), "turns off the agent's permission checks"),
]
URL = re.compile(r"https?://[^\s\"'`)<>]+")
ALLOWED_URL_HOSTS = ("example.com", "ntfy.sh/<", "github.com/simbaTmotsi/", "github.com/mattpocock/", "code.claude.com/")

for f in tracked_files():
    if not f.endswith(TEXT_EXT) or f == "scripts/check.py":
        continue
    text = open(f, encoding="utf-8", errors="replace").read()
    for lineno, line in enumerate(text.splitlines(), 1):
        where = f"{f}:{lineno}"
        if HIDDEN.search(line):
            fail(where, "contains invisible or direction-changing Unicode characters (possible hidden instructions)")
        if DASHES.search(line):
            fail(where, "contains an em or en dash; rewrite the sentence")
        if HOME_PATH.search(line):
            fail(where, "contains an absolute home directory path; use ~ or a placeholder")
        for pattern, why in DANGEROUS:
            if pattern.search(line):
                fail(where, f"{why}; this needs a maintainer's explicit sign-off")
        if f.endswith((".sh", ".py")) and not line.lstrip().startswith("#"):
            for url in URL.findall(line):
                if not any(h in url for h in ALLOWED_URL_HOSTS):
                    fail(where, f"script contacts a hard-coded URL ({url}); make it a setting the user supplies")

# 4. Risky skills that the model could start on its own
RISKY = re.compile(r"\b(docker (compose )?(up|down|rm|system prune)|crontab -|git push|DROP (TABLE|DATABASE)|TRUNCATE|rm -rf|kubectl (apply|delete)|terraform apply)\b")
for d in skill_dirs:
    fm, body = frontmatter(open(f"{d}/SKILL.md", encoding="utf-8").read())
    user_invoked = fm is not None and re.search(r"^disable-model-invocation:\s*true\s*$", fm, re.M)
    if not user_invoked and RISKY.search(body):
        warn(f"{d}/SKILL.md", "model-invoked skill mentions a destructive or outward-facing command; confirm it only describes, never runs, it without asking")

for w in warnings:
    print(f"::warning::{w}" if os.environ.get("GITHUB_ACTIONS") else f"warning: {w}")
for e in failures:
    print(f"::error::{e}" if os.environ.get("GITHUB_ACTIONS") else f"error: {e}")
print(f"{len(skill_dirs)} skills checked, {len(failures)} failures, {len(warnings)} warnings")
sys.exit(1 if failures else 0)
