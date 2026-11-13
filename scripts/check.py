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
import shutil
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
PLUGIN = "plugin"  # the folder submitted to the plugin directory

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
skill_dirs = sorted(os.path.dirname(p) for p in glob.glob(f"{PLUGIN}/skills/*/*/SKILL.md"))
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

for loose in glob.glob(f"{PLUGIN}/skills/*/*.md"):
    if os.path.basename(loose) != "README.md":
        fail(loose, "skills must be folders with SKILL.md, not loose .md files")

# 2. Manifest and READMEs list exactly the skills that exist
PLUGIN_JSON = f"{PLUGIN}/.claude-plugin/plugin.json"
plugin = json.load(open(PLUGIN_JSON, encoding="utf-8"))
listed = sorted(f"{PLUGIN}/" + p.rstrip("/").removeprefix("./") for p in plugin.get("skills", []))
if listed != skill_dirs:
    fail(PLUGIN_JSON, f"`skills` must list exactly {skill_dirs}, found {listed}")
if not re.fullmatch(r"\d+\.\d+\.\d+", str(plugin.get("version", ""))):
    fail(PLUGIN_JSON, "`version` must be MAJOR.MINOR.PATCH")
readme = open("README.md", encoding="utf-8").read()
for d in skill_dirs:
    name = os.path.basename(d)
    if f"`{name}`" not in readme and f"{d}/SKILL.md" not in readme:
        fail("README.md", f"does not mention skill `{name}`")
    bucket_readme = os.path.join(os.path.dirname(d), "README.md")
    if not os.path.exists(bucket_readme) or f"./{name}/SKILL.md" not in open(bucket_readme, encoding="utf-8").read():
        fail(bucket_readme, f"does not link ./{name}/SKILL.md")

market = json.load(open(".claude-plugin/marketplace.json", encoding="utf-8"))
if [p.get("source") for p in market.get("plugins", [])] != [f"./{PLUGIN}"]:
    fail(".claude-plugin/marketplace.json", f"the plugin's `source` must be ./{PLUGIN}")

# 2b. The submitted folder holds only file types any publisher may ship
ALLOWED_IN_PLUGIN = (".md", ".txt", ".json", ".yaml", ".yml", ".png", ".jpg", ".jpeg", ".gif", ".webp", ".ico")
FORBIDDEN_NAMES = ("hooks.json", ".mcp.json", ".lsp.json", "monitors.json")
for f in tracked_files():
    if not f.startswith(f"{PLUGIN}/"):
        continue
    if not f.lower().endswith(ALLOWED_IN_PLUGIN):
        fail(f, "the plugin folder may only hold Markdown, text, JSON, YAML and images; ship scripts as Markdown in a skill's scripts/ folder")
    elif os.path.basename(f) in FORBIDDEN_NAMES:
        fail(f, "hooks, MCP, LSP and monitor configs are not accepted from unverified publishers")
    elif open(f, "rb").read(2) == b"#!":
        fail(f, "files in the plugin folder must not start with #!")
    elif "/.claude-plugin/" in f and os.path.basename(f) != "plugin.json" and not f.lower().endswith(ALLOWED_IN_PLUGIN[5:]):
        fail(f, "only plugin.json and images belong in the plugin's .claude-plugin folder")

# 2c. Scripts shipped as Markdown: exactly one fenced block, and it must parse
FENCE = re.compile(r"^````(bash|python)\n(.*?)^````\s*$", re.M | re.S)
script_lines = set()
shellcheck = shutil.which("shellcheck")
with tempfile.TemporaryDirectory() as tmp:
    for f in sorted(glob.glob(f"{PLUGIN}/skills/*/*/scripts/*.md")):
        text = open(f, encoding="utf-8").read()
        blocks = list(FENCE.finditer(text))
        if len(blocks) != 1:
            fail(f, "script files must hold exactly one ````bash or ````python block")
            continue
        lang, code = blocks[0].group(1), blocks[0].group(2)
        start = text[:blocks[0].start(2)].count("\n") + 1
        script_lines.update((f, start + i) for i in range(code.count("\n")))
        out = os.path.join(tmp, os.path.basename(f)[:-3])
        open(out, "w", encoding="utf-8").write(code)
        if lang == "python":
            try:
                compile(code, f, "exec")
            except SyntaxError as e:
                fail(f, f"embedded Python does not parse: {e}")
        else:
            r = subprocess.run(["bash", "-n", out], capture_output=True, text=True)
            if r.returncode:
                fail(f, f"embedded bash does not parse: {r.stderr.strip()}")
            if shellcheck:
                r = subprocess.run([shellcheck, "-S", "warning", out], capture_output=True, text=True)
                if r.returncode:
                    fail(f, "shellcheck warnings in the embedded script:\n" + r.stdout.strip())
            elif os.environ.get("GITHUB_ACTIONS"):
                fail(f, "shellcheck is not installed on the CI runner")

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
        if (f.endswith((".sh", ".py")) or (f, lineno) in script_lines) and not line.lstrip().startswith("#"):
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
