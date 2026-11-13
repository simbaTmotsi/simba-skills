# classify_copy.sh

This is the source of `classify_copy.sh`, kept as Markdown because the plugin directory does not accept executable files from unverified publishers. Do not retype it. Extract it exactly with the command in this skill's `SKILL.md`, which copies everything between the two fence lines below.

````bash
#!/usr/bin/env bash
# Classify a copied skill folder against its upstream git repo.
#
# Usage: classify_copy.sh LOCAL_SKILL_DIR UPSTREAM_REPO_DIR UPSTREAM_SKILL_PATH
#   LOCAL_SKILL_DIR      e.g. .claude/skills/tdd
#   UPSTREAM_REPO_DIR    a full (not shallow) clone of the upstream repo
#   UPSTREAM_SKILL_PATH  the skill's folder inside upstream, e.g. skills/engineering/tdd
#
# Per file: current | stale (matches an older upstream blob) | edited | local-only
# Overall:  current | stale copy | locally edited
# Read-only: never writes to either side.
set -euo pipefail

if [ $# -ne 3 ]; then
  sed -n '2,10p' "$0"; exit 2
fi
local_dir=${1%/}; up=$2; up_path=${3%/}

if [ "$(git -C "$up" rev-parse --is-shallow-repository)" = "true" ]; then
  echo "upstream clone is shallow; run: git -C $up fetch --unshallow" >&2; exit 2
fi

overall=current
while IFS= read -r -d '' f; do
  rel=${f#"$local_dir"/}
  upfile="$up_path/$rel"
  h=$(git hash-object "$f")
  latest=$(git -C "$up" rev-parse -q --verify "HEAD:$upfile" 2>/dev/null || true)
  if [ -z "$latest" ] && ! git -C "$up" log -1 --format=%H -- "$upfile" | grep -q .; then
    printf '%-14s %s\n' "local-only" "$rel"
    overall="locally edited"
    continue
  fi
  if [ "$h" = "$latest" ]; then
    printf '%-14s %s\n' "current" "$rel"; continue
  fi
  # Walk upstream history of this file (following renames), newest first,
  # and find the newest commit whose version of the file has our blob hash.
  match=$(git -C "$up" log --follow --format='C %h %cs' --raw --no-abbrev -- "$upfile" |
    awk -v h="$h" '$1=="C"{c=substr($2,1,12)" "$3; next} $1 ~ /^:/ && $4==h {print c; exit}')
  if [ -n "$match" ]; then
    printf '%-14s %s (matches upstream %s)\n' "stale" "$rel" "$match"
    [ "$overall" = current ] && overall="stale copy"
  else
    printf '%-14s %s\n' "edited" "$rel"
    overall="locally edited"
    if [ -n "$latest" ]; then
      git -C "$up" show "HEAD:$upfile" | git diff --no-index --stat -- - "$f" || true
    fi
  fi
done < <(find "$local_dir" -type f -not -path '*/.git/*' -print0 | sort -z)

# Files upstream has that the copy lacks also mean the copy is behind.
missing=$(git -C "$up" ls-tree -r --name-only HEAD -- "$up_path/" | while read -r p; do
  [ -e "$local_dir/${p#"$up_path"/}" ] || echo "${p#"$up_path"/}"; done)
if [ -n "$missing" ]; then
  echo "$missing" | sed 's/^/missing-here   /'
  [ "$overall" = current ] && overall="stale copy"
fi

echo "OVERALL: $overall"
````
