#!/usr/bin/env bash
# Hydrogram user-session entrypoint (self-bot, not Bot API polling).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if [ -f .venv/bin/python ]; then
  exec .venv/bin/python -m app.main
fi

if command -v poetry >/dev/null 2>&1; then
  exec poetry run python -m app.main
fi

exec python -m app.main
