#!/usr/bin/env bash
# Push self-bot to github.com/mamahoos/telegram-selfbot and open a PR.
# Prerequisites: gh auth login, SSH access to GitHub as mamahoos.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

REPO="mamahoos/telegram-selfbot"
BRANCH="feat/selfbot-full-implementation"
REMOTE="${REMOTE:-origin}"

echo "==> secrets check"
./scripts/check-secrets.sh

if ! gh auth status >/dev/null 2>&1; then
  echo "ERROR: run 'gh auth login' first" >&2
  exit 1
fi

if ! git remote get-url "$REMOTE" >/dev/null 2>&1; then
  git remote add "$REMOTE" "git@github.com:${REPO}.git"
fi

if ! git ls-remote "$REMOTE" HEAD >/dev/null 2>&1; then
  echo "==> creating GitHub repo ${REPO} (with README on main for PR base)"
  gh repo create "$REPO" --public --add-readme --remote="$REMOTE"
fi

echo "==> fetch ${REMOTE}"
git fetch "$REMOTE"

git checkout "$BRANCH"

if git ls-remote --heads "$REMOTE" main | grep -q main; then
  echo "==> rebase ${BRANCH} onto ${REMOTE}/main"
  git rebase "${REMOTE}/main"
fi

echo "==> push ${BRANCH}"
git push -u "$REMOTE" "$BRANCH" --force-with-lease

PR_URL="$(gh pr list --repo "$REPO" --head "$BRANCH" --json url -q '.[0].url' 2>/dev/null || true)"
if [ -n "$PR_URL" ]; then
  echo "$PR_URL"
  exit 0
fi

gh pr create \
  --repo "$REPO" \
  --base main \
  --head "$BRANCH" \
  --title "feat: full selfbot — AI, discuss pipeline, secure defaults" \
  --body "$(cat <<'EOF'
## Summary

- Hydrogram user-session selfbot with plugin architecture (media, reactions, stickers, stream, awk, tag, utility).
- **`.ai`** — fast LLM answers with Hermes-style Markdown → Telegram HTML formatting.
- **`.answer`** — 4-layer discuss pipeline (analyze → worldview draft → tone polish → sanitize) driven by local profile files.
- Security: `.gitignore` + `scripts/check-secrets.sh`; personal profile/voice corpus and `deploy.env` never committed; deploy host via env only.

## Test plan

- [ ] `poetry install && poetry run pytest`
- [ ] `./scripts/check-secrets.sh`
- [ ] Copy `.env.example` → `.env`, login, run `.help` and `.ai`
- [ ] Copy profile templates → `data/profile.md` + voice files for `.answer`

EOF
)"

echo "==> done"
