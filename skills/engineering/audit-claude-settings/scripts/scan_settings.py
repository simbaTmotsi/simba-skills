#!/usr/bin/env python3
"""Scan Claude Code settings files for risky permission rules.

Subcommands:
  scan FILE...            Print a categorised report. Secrets are masked.
  remove FILE ID...       Remove entries by id (e.g. allow:12 dirs:0), rewrite, re-parse.
  mask                    Read text on stdin, print it with secrets masked.

Ids are "<list>:<index>" where list is allow, ask, deny or dirs
(additionalDirectories). Indexes refer to the file as it is when scanned,
so always remove against a fresh scan.

Standard library only. Never prints an unmasked secret.
"""
import json
import os
import re
import sys
from collections import Counter

LISTS = {"allow": "allow", "ask": "ask", "deny": "deny", "dirs": "additionalDirectories"}

SECRET_PATTERNS = [
    # env assignments: PGPASSWORD=..., FOO_TOKEN=..., API_KEY=...
    re.compile(r"(?i)\b([A-Z0-9_]*(?:PASSWORD|PASSWD|PWD|TOKEN|SECRET|API_?KEY|ACCESS_?KEY)[A-Z0-9_]*\s*=\s*)(['\"]?)([^\s'\"]+)"),
    # --password=..., --token=..., --api-key ...
    re.compile(r"(?i)(--(?:password|passwd|token|api-key|apikey|secret)[= ])(['\"]?)([^\s'\"]+)"),
    # mysql -pSECRET (glued)
    re.compile(r"(\b(?:mysql|mariadb|mysqldump)\b[^|;&]*?\s-p)()([^\s'\"]+)"),
    # Authorization / API key headers
    re.compile(r"(?i)((?:authorization:\s*(?:bearer|basic|token)\s+)|(?:x-api-key:\s*)|(?:private-token:\s*))(['\"]?)([^\s'\"]+)"),
    # curl -u user:pass
    re.compile(r"(\s-u\s+['\"]?[^:\s'\"]+:)()([^\s'\"@]+)"),
    # scheme://user:pass@host
    re.compile(r"([a-z][a-z0-9+.-]*://[^:/\s@'\"]+:)()([^@\s'\"]+)(?=@)"),
    # well-known token prefixes
    re.compile(r"()()\b((?:ghp_|gho_|ghs_|github_pat_|glpat-|sk-|xox[abpr]-|AKIA)[A-Za-z0-9_\-]{8,})"),
    # long opaque value after = or :
    re.compile(r"([=:]\s*)(['\"]?)([A-Za-z0-9+/_\-]{20,}={0,2})(?=['\"\s)]|$)"),
]

TEMP_RE = re.compile(r"(/(?:private/)?tmp/[^\s'\")*]*|/var/tmp/[^\s'\")*]*|/dev/shm/[^\s'\")*]*|/var/folders/[^\s'\")*]*|[^\s'\"(]*/scratchpad[^\s'\")*]*)")
WW_PREFIXES = ("/tmp", "/private/tmp", "/var/tmp", "/dev/shm")
EXEC_WORDS = r"(?:bash|sh|zsh|python3?|node|perl|ruby|source|\.|chmod\s+\+x|exec)"


KNOWN_PREFIX = re.compile(r"^(ghp_|gho_|ghs_|github_pat_|glpat-|sk-|xox[abpr]-|AKIA)")


def mask_value(v):
    """Hide the whole value; keep only a well-known token prefix, which names the kind."""
    trail = ""
    while v.endswith(")"):
        v, trail = v[:-1], trail + ")"
    m = KNOWN_PREFIX.match(v)
    prefix = m.group(1) if m else ""
    return f"{prefix}<masked:{len(v)}>{trail}"


def mask(text):
    found = False
    for pat in SECRET_PATTERNS:
        def repl(m):
            nonlocal found
            val = m.group(3)
            if pat is SECRET_PATTERNS[-1] and (val.startswith("/") or not re.search(r"\d", val)):
                return m.group(0)  # path or plain word, not a secret
            found = True
            return m.group(1) + m.group(2) + mask_value(val)
        text = pat.sub(repl, text)
    return text, found


def classify(kind, rule, home):
    masked, has_secret = mask(rule)
    cats = []
    if has_secret:
        cats.append("credential")
    temps = TEMP_RE.findall(rule)
    if kind == "dirs":
        p = os.path.expanduser(rule).rstrip("/") or "/"
        broad = {"/", "/tmp", "/private/tmp", "/var/tmp", "/dev/shm", home, "/home", "/Users"}
        if p in broad or os.path.dirname(p) == home and os.path.basename(p) in ("Documents", "Desktop", "Downloads", "src", "code", "projects"):
            cats.append("broad-directory")
    elif temps and kind == "allow":
        body = rule
        if re.search(rf"(?:^|\(|\s|&&|;){EXEC_WORDS}\s+(?:/private)?/(?:tmp|var/tmp|dev/shm)/", body) or \
           re.search(r"\(\s*(?:/private)?/(?:tmp|var/tmp|dev/shm)/", body) or \
           (re.search(r"/scratchpad/", body) and re.search(rf"(?:\(|\s){EXEC_WORDS}\s+\S*/scratchpad/", body)):
            cats.append("world-writable-exec")
    for t in temps:
        t = t.rstrip("*:").rstrip("/")
        if t and t not in WW_PREFIXES and not os.path.exists(t):
            cats.append("stale-temp-path")
            break
    if kind == "allow" and rule.startswith("Bash(") and "*" not in rule:
        inner = rule[5:-1]
        if len(inner) > 60 or re.search(r"&&|;|\||<<|\n", inner):
            cats.append("one-off")
    return masked, cats


ORDER = ["credential", "world-writable-exec", "broad-directory", "stale-temp-path", "one-off"]


def load(path):
    with open(path) as f:
        return json.load(f)


def scan(paths):
    home = os.path.expanduser("~").rstrip("/")
    for path in paths:
        print(f"\n=== {path} ===")
        try:
            data = load(path)
        except FileNotFoundError:
            print("  (not found)")
            continue
        except json.JSONDecodeError as e:
            print(f"  INVALID JSON: {e}")
            continue
        perms = data.get("permissions", {}) or {}
        buckets = {c: [] for c in ORDER}
        oneoff_heads = Counter()
        for key, field in LISTS.items():
            entries = perms.get(field, []) or []
            print(f"  {field}: {len(entries)} entries")
            for i, rule in enumerate(entries):
                if not isinstance(rule, str):
                    continue
                masked, cats = classify(key, rule, home)
                if not cats:
                    continue
                top = next(c for c in ORDER if c in cats)
                if top == "one-off":
                    head = rule[5:-1].strip().split()[0] if rule[5:-1].strip() else "?"
                    oneoff_heads[os.path.basename(head)] += 1
                    buckets["one-off"].append(f"{key}:{i}")
                else:
                    extra = [c for c in cats if c != top]
                    tag = f"  [+{', '.join(extra)}]" if extra else ""
                    buckets[top].append(f"  {key}:{i}  {masked}{tag}")
        for cat in ORDER:
            items = buckets[cat]
            print(f"\n  -- {cat}: {len(items)}")
            if cat == "one-off":
                for head, n in oneoff_heads.most_common():
                    print(f"     {n:4d}  {head} ...")
                if items:
                    print(f"     ids: {' '.join(items)}")
            else:
                for line in items:
                    print("   " + line)


def remove(path, ids):
    data = load(path)
    perms = data.get("permissions", {})
    drop = {}
    for ident in ids:
        key, _, idx = ident.partition(":")
        if key not in LISTS or not idx.isdigit():
            sys.exit(f"bad id: {ident}")
        drop.setdefault(LISTS[key], set()).add(int(idx))
    for field, idxs in drop.items():
        entries = perms.get(field, [])
        bad = [i for i in idxs if i >= len(entries)]
        if bad:
            sys.exit(f"{field} has no index {bad}; re-scan first. Nothing written.")
        perms[field] = [e for i, e in enumerate(entries) if i not in idxs]
    tmp = path + ".tmp-audit"
    st = os.stat(path)
    with open(tmp, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")
    os.chmod(tmp, st.st_mode)
    load(tmp)  # raises if somehow invalid
    os.replace(tmp, path)
    load(path)
    print(f"removed {sum(len(v) for v in drop.values())} entries from {path}; JSON re-parsed OK")


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    cmd = sys.argv[1]
    if cmd == "scan":
        scan(sys.argv[2:] or [os.path.expanduser("~/.claude/settings.json"), ".claude/settings.json", ".claude/settings.local.json"])
    elif cmd == "remove" and len(sys.argv) >= 4:
        remove(sys.argv[2], sys.argv[3:])
    elif cmd == "mask":
        for line in sys.stdin:
            sys.stdout.write(mask(line)[0])
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main()
