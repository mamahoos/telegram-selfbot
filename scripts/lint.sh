#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
poetry run ruff check src tests
poetry run ruff format --check src tests
poetry run mypy src
