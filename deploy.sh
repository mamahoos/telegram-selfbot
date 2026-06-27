#!/usr/bin/env bash
# Rsync self-bot to server, build on server, compose up.
# .env is created on the server from .env.example only (never synced from laptop).
#
# Server target: copy deploy.env.example → deploy.env (gitignored) or export:
#   DEPLOY_HOST, DEPLOY_USER, DEPLOY_REMOTE
#
# Optional credentials in environment (written to server .env only):
#   API_ID, API_HASH, PHONE_NUMBER, LLM_API_KEY, LLM_API_BASE_URL, LLM_MODEL
#
# DEPLOY_NO_START=1  — rsync + build only (no docker compose up)
# SYNC_DATA=1        — rsync data/ (excludes *.session*; keeps session on server)
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
# shellcheck source=scripts/deploy-common.sh
source "${ROOT}/scripts/deploy-common.sh"
tg_deploy_init

if [ -f "${ROOT}/deploy.env" ]; then
  set -a
  # shellcheck source=/dev/null
  source "${ROOT}/deploy.env"
  set +a
fi

HOST="${DEPLOY_HOST:?Set DEPLOY_HOST in deploy.env (see deploy.env.example)}"
USER="${DEPLOY_USER:-root}"
BOT_NAME="$(basename "$ROOT")"
REMOTE="${DEPLOY_REMOTE:-/srv/tg-bots/${BOT_NAME}}"
APP_UID=10001
APP_GID=10001
SSH="ssh -o BatchMode=yes -o StrictHostKeyChecking=accept-new"

echo "==> ${USER}@${HOST}:${REMOTE}"

$SSH "${USER}@${HOST}" "mkdir -p '${REMOTE}'"

echo "==> rsync"
rsync -avz --delete \
  --include '.env.example' \
  --filter=':- .gitignore' \
  --exclude '.git/' \
  --exclude '.env' \
  --exclude '.env.local' \
  --exclude 'deploy.env' \
  --exclude 'data/' \
  --exclude 'logs/' \
  --exclude 'tmp/' \
  -e "$SSH" \
  "${ROOT}/" "${USER}@${HOST}:${REMOTE}/"

if [ "${SYNC_DATA:-}" = "1" ]; then
  echo "==> rsync data/ (profile + state; excluding session files)"
  rsync -avz \
    --exclude '*.session' \
    --exclude '*.session-shm' \
    --exclude '*.session-wal' \
    -e "$SSH" \
    "${ROOT}/data/" "${USER}@${HOST}:${REMOTE}/data/"
fi

if [ -n "${API_ID:-}" ] || [ -n "${API_HASH:-}" ] || [ -n "${PHONE_NUMBER:-}" ] || \
   [ -n "${LLM_API_KEY:-}" ] || [ -n "${LLM_API_BASE_URL:-}" ] || [ -n "${LLM_MODEL:-}" ]; then
  echo "==> update credentials on server .env"
  $SSH "${USER}@${HOST}" bash -s <<EOF
set -eu
cd '${REMOTE}'
$(tg_deploy_server_bootstrap_env_snippet)
for pair in \
  "API_ID:${API_ID:-}" \
  "API_HASH:${API_HASH:-}" \
  "PHONE_NUMBER:${PHONE_NUMBER:-}" \
  "LLM_API_KEY:${LLM_API_KEY:-}" \
  "LLM_API_BASE_URL:${LLM_API_BASE_URL:-}" \
  "LLM_MODEL:${LLM_MODEL:-}"; do
  key="\${pair%%:*}"
  val="\${pair#*:}"
  [ -n "\$val" ] || continue
  if grep -q "^\${key}=" .env; then
    sed -i "s|^\${key}=.*|\${key}=\${val}|" .env
  else
    printf '%s=%s\n' "\$key" "\$val" >> .env
  fi
done
chmod 600 .env
EOF
fi

echo "==> docker compose build (on server)"
$SSH "${USER}@${HOST}" bash -s <<EOF
set -eu
cd '${REMOTE}'
$(tg_deploy_server_bootstrap_env_snippet)
mkdir -p data logs tmp
chown -R ${APP_UID}:${APP_GID} data logs tmp
chmod 700 data
export DOCKER_BUILDKIT=1
docker compose build \
  --build-arg PIP_INDEX_URL=https://pypi.org/simple \
  --build-arg PIP_TRUSTED_HOST=pypi.org
if [ "${DEPLOY_NO_START:-}" = "1" ]; then
  echo "DEPLOY_NO_START=1 — skipping docker compose up"
  docker compose ps -a || true
else
$(tg_deploy_server_build_snippet | tail -n +3)
  docker compose ps
  docker compose logs --tail=40 selfbot
fi
EOF

if [ "${DEPLOY_NO_START:-}" = "1" ]; then
  echo ""
  echo "==> deployed (not started). First login on server:"
  echo "    ssh ${USER}@${HOST}"
  echo "    cd ${REMOTE}"
  echo "    docker compose run --rm -it selfbot"
  echo "    # after login succeeds:"
  echo "    docker compose up -d"
fi

echo "==> done."
