#!/usr/bin/env bash
# Pre-push sanity check: fail if tracked files look like secrets or personal data.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

fail=0

echo "==> Checking .gitignore coverage for sensitive paths"
for path in \
  .env \
  deploy.env \
  data/profile.md \
  data/cognitive-profile.md \
  data/telegram-voice/my-messages.txt \
  data/telegram-voice/voice.compact.txt \
  data/telegram-voice/scenario-map.md \
  scripts/deploy-pacman.sh; do
  if git check-ignore -q "$path" 2>/dev/null; then
    echo "  OK ignored: $path"
  else
    echo "  FAIL not ignored: $path"
    fail=1
  fi
done

echo ""
echo "==> Scanning files that would be committed"
patterns=(
  '188\.209\.[0-9]+\.[0-9]+'
  'sk-[A-Za-z0-9]{20,}'
  'API_HASH=[a-f0-9]{32}'
)

skip_files=(
  scripts/check-secrets.sh
)

if git rev-parse --git-dir >/dev/null 2>&1; then
  mapfile -t files < <(git ls-files 2>/dev/null || true)
  if [ "${#files[@]}" -eq 0 ]; then
    mapfile -t files < <(git add -n . 2>&1 | sed -n "s/^add '//;s/'$//p")
  fi
else
  mapfile -t files < <(git add -n . 2>&1 | sed -n "s/^add '//;s/'$//p")
fi

for f in "${files[@]}"; do
  [ -f "$f" ] || continue
  skip=0
  for s in "${skip_files[@]}"; do
    if [ "$f" = "$s" ]; then skip=1; break; fi
  done
  [ "$skip" -eq 1 ] && continue
  for pat in "${patterns[@]}"; do
    if grep -qE "$pat" "$f" 2>/dev/null; then
      echo "  FAIL pattern /$pat/ in: $f"
      fail=1
    fi
  done
done

if [ "$fail" -eq 0 ]; then
  echo ""
  echo "==> All checks passed"
  exit 0
fi

echo ""
echo "==> Fix issues above before pushing to GitHub"
exit 1
