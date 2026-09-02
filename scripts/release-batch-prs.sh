#!/usr/bin/env bash
# Create feature branches with ≤10 files each and open PRs to develop.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

MAX_FILES=10
BASE_BRANCH="${BASE_BRANCH:-develop}"
START_BATCH="${START_BATCH:-1}"

if ! git rev-parse --git-dir >/dev/null 2>&1; then
  echo "Not a git repo"; exit 1
fi

git fetch origin
git checkout "$BASE_BRANCH" 2>/dev/null || git checkout -b "$BASE_BRANCH"
git pull origin "$BASE_BRANCH" 2>/dev/null || true

# Collect all changed paths (exclude agent skill dirs)
ALL_FILES=()
while IFS= read -r line; do
  ALL_FILES+=("$line")
done < <(
  git status --short --untracked-files=all \
    | sed 's/^.. //' \
    | grep -vE '^\.(agents|claude|cursor|devin)/' \
    | grep -v 'credentials\.json' \
    | grep -v '\.env\.prisma$' \
    | sort -u
)

if [ "${#ALL_FILES[@]}" -eq 0 ]; then
  echo "No files to commit."
  exit 0
fi

echo "Total files to batch: ${#ALL_FILES[@]}"

batch=()
batch_num=$((START_BATCH - 1))
pr_urls=()

flush_batch() {
  local n=${#batch[@]}
  [ "$n" -eq 0 ] && return
  batch_num=$((batch_num + 1))
  local branch="feature/release-batch-$(printf '%02d' "$batch_num")"
  echo ""
  echo "=== Batch $batch_num ($n files) → $branch ==="

  git checkout "$BASE_BRANCH"
  git pull origin "$BASE_BRANCH" 2>/dev/null || true
  git checkout -B "$branch"

  local added=0
  for f in "${batch[@]}"; do
    if [ -e "$f" ] || git ls-files --error-unmatch "$f" &>/dev/null; then
      git add -A -- "$f" 2>/dev/null || git add -A -- "$f"
      added=$((added + 1))
    elif git status --short "$f" 2>/dev/null | grep -q '^ D'; then
      git add -A -- "$f"
      added=$((added + 1))
    fi
  done

  if [ "$added" -eq 0 ]; then
    echo "Skip empty batch $batch_num"
    batch=()
    return
  fi

  local title="chore(release): batch $batch_num — $added files"
  git commit -m "$(cat <<EOF
$title

Grouped release commit (max $MAX_FILES files per PR).
EOF
)"

  git push -u origin "$branch" --force-with-lease

  if gh pr view "$branch" &>/dev/null; then
    url=$(gh pr view "$branch" --json url -q .url)
  else
    url=""
    for attempt in 1 2 3; do
      if url=$(gh pr create \
        --base "$BASE_BRANCH" \
        --head "$branch" \
        --title "$title" \
        --body "Release batch $batch_num ($added files). Part of staged rollout to Vercel via \`staging\` branch." 2>&1); then
        break
      fi
      sleep 3
    done
  fi
  echo "PR: $url"
  pr_urls+=("$url")

  gh pr merge "$branch" --merge --auto 2>/dev/null || gh pr merge "$branch" --merge 2>/dev/null || true

  batch=()
}

for f in "${ALL_FILES[@]}"; do
  batch+=("$f")
  if [ "${#batch[@]}" -ge "$MAX_FILES" ]; then
    flush_batch
  fi
done
flush_batch

echo ""
echo "Created $batch_num batches."
printf '%s\n' "${pr_urls[@]}"

# Ensure staging + production exist
git checkout "$BASE_BRANCH"
git pull origin "$BASE_BRANCH" 2>/dev/null || true

for env_branch in staging production; do
  if git show-ref --verify --quiet "refs/heads/$env_branch"; then
    git checkout "$env_branch"
    git merge "$BASE_BRANCH" -m "chore: sync $env_branch with $BASE_BRANCH"
  else
    git checkout -b "$env_branch"
  fi
  git push -u origin "$env_branch" --force-with-lease 2>/dev/null || git push -u origin "$env_branch"
done

git checkout "$BASE_BRANCH"
echo "Done. staging and production branches updated."
