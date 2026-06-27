# Shared deploy helpers (standalone copy for self-bot repo).
# shellcheck shell=bash

tg_deploy_init() {
  export DOCKER_BUILDKIT=1
}

tg_deploy_server_bootstrap_env_snippet() {
  cat <<'EOF'
if [ ! -f .env ]; then
  if [ ! -f .env.example ]; then
    echo "Missing .env.example on server" >&2
    exit 1
  fi
  cp .env.example .env
  chmod 600 .env
  echo "Created .env from .env.example"
fi
EOF
}

tg_deploy_server_build_snippet() {
  cat <<'EOF'
export DOCKER_BUILDKIT=1
docker compose build \
  --build-arg PIP_INDEX_URL=https://pypi.org/simple \
  --build-arg PIP_TRUSTED_HOST=pypi.org
docker compose up -d --remove-orphans --force-recreate
EOF
}
