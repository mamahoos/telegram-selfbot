#!/usr/bin/env bash
# Deploy telegram-selfbot to the pacman host and restart the container.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
REMOTE_DIR="/opt/telegram-selfbot"
IMAGE="telegram-selfbot:latest"

cd "$ROOT"
tar czf - \
  --exclude='.venv' \
  --exclude='.git' \
  --exclude='__pycache__' \
  --exclude='.pytest_cache' \
  --exclude='tmp/*' \
  --exclude='logs/*' \
  . | ssh pacman "tar xzf - -C ${REMOTE_DIR}"

ssh pacman "set -e
chown -R 10001:10001 ${REMOTE_DIR}/data ${REMOTE_DIR}/logs ${REMOTE_DIR}/tmp
chmod -R u+rwX,g+rwX ${REMOTE_DIR}/data ${REMOTE_DIR}/logs ${REMOTE_DIR}/tmp
rm -f ${REMOTE_DIR}/data/selfbot.session-wal ${REMOTE_DIR}/data/selfbot.session-shm
cd ${REMOTE_DIR}
docker build --network=host -f docker/Dockerfile -t ${IMAGE} .
docker rm -f telegram-selfbot 2>/dev/null || true
docker run -d \\
  --name telegram-selfbot \\
  --restart unless-stopped \\
  --env-file ${REMOTE_DIR}/.env \\
  -v ${REMOTE_DIR}/data:/app/data \\
  -v ${REMOTE_DIR}/logs:/app/logs \\
  -v ${REMOTE_DIR}/tmp:/app/tmp \\
  ${IMAGE}
sleep 5
docker logs telegram-selfbot 2>&1 | tail -8
"
