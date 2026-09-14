#!/usr/bin/env bash
#
# Lean deploy: rsync sources → build Docker image on the production host → recreate app.
# SSH target and host paths come from gitignored `.env` (ADR-011):
#   DEPLOY_USER, DEPLOY_HOST, optional DEPLOY_SSH, HOST_HOME
# User must be in the docker group (no sudo).
#
# Secrets: copies local .env to the host compose dir (not into the image).
# Does not recreate Ollama / Gemma (container sogyo-ollama).
#
# Usage (from repo root):
#   ./scripts/deploy-to-15.sh
#   ./scripts/deploy-to-15.sh 1.0.2
#
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
TAG="${1:-latest}"
REMOTE_BASE="jarvisje-chatbot"
APP_CONTAINER="jarvisje-chatbot-app"
IMAGE="jarvisje"

cd "$ROOT"

if [[ ! -f "$ROOT/.env" ]]; then
  echo "ERROR: missing .env — cp .env.example .env and set DEPLOY_USER, DEPLOY_HOST, HOST_HOME, INGEST_TOKEN." >&2
  exit 1
fi

set -a
# shellcheck disable=SC1091
source "$ROOT/.env"
set +a

if [[ -z "${DEPLOY_USER:-}" || -z "${DEPLOY_HOST:-}" ]]; then
  echo "ERROR: .env must set DEPLOY_USER and DEPLOY_HOST." >&2
  exit 1
fi
HOST="${DEPLOY_SSH:-${DEPLOY_USER}@${DEPLOY_HOST}}"
HOST_HOME="${HOST_HOME:-/home/${DEPLOY_USER}}"

if ! grep -qE '^(INGEST_TOKEN|INDEX_TOKEN)=.+' "$ROOT/.env"; then
  echo "WARNING: .env has no non-empty INGEST_TOKEN/INDEX_TOKEN." >&2
fi

echo "==> Rsync source to $HOST:~/$REMOTE_BASE/build-src"
rsync -az --delete \
  --exclude '__pycache__' \
  --exclude '.DS_Store' \
  --exclude '.env' \
  --exclude '.env.*' \
  -e 'ssh -o BatchMode=yes' \
  src scripts web requirements.txt pyproject.toml \
  "$HOST:~/$REMOTE_BASE/build-src/"

# Never ship secrets into the build context
ssh -o BatchMode=yes "$HOST" "rm -f ~/$REMOTE_BASE/build-src/.env ~/$REMOTE_BASE/build-src/.env.*"

scp -o BatchMode=yes \
  infra/ubuntu-x64/Dockerfile \
  "$HOST:~/$REMOTE_BASE/build-src/Dockerfile"

scp -o BatchMode=yes \
  infra/ubuntu-x64/docker-compose.prod-local.yaml \
  "$HOST:~/$REMOTE_BASE/docker-compose.yaml"

echo "==> Install host .env (mode 600, not in image) — ADR-011"
scp -o BatchMode=yes "$ROOT/.env" "$HOST:~/$REMOTE_BASE/.env"
ssh -o BatchMode=yes "$HOST" "chmod 600 ~/$REMOTE_BASE/.env"

echo "==> Build & recreate app on server (tag=$TAG) — Ollama not touched"
ssh -o BatchMode=yes "$HOST" bash -s <<EOF
set -euo pipefail
cd ~/$REMOTE_BASE/build-src
docker build -t "${IMAGE}:${TAG}" -t ${IMAGE}:latest -f Dockerfile .
cd ~/$REMOTE_BASE
# Recreate only the app; leave sogyo-ollama / Gemma running
IMAGE_TAG=latest docker compose up -d --force-recreate --no-deps app
# Wait for health (embedding preload can take a minute)
ok=0
for i in \$(seq 1 36); do
  if curl -sf --max-time 5 http://127.0.0.1:8080/health >/dev/null; then
    ok=1
    break
  fi
  sleep 5
done
curl -sf --max-time 10 http://127.0.0.1:8080/health | head -c 300 || true
echo
docker ps --filter name=${APP_CONTAINER} --format '{{.Names}} {{.Status}} {{.Image}}'
docker exec ${APP_CONTAINER} python -c "import os; t=(os.getenv('INGEST_TOKEN') or os.getenv('INDEX_TOKEN') or ''); print('INGEST_TOKEN configured:', bool(t), 'len=', len(t))"
if [[ "\$ok" -ne 1 ]]; then
  echo "WARNING: health not ready yet; check docker logs ${APP_CONTAINER}" >&2
  exit 1
fi
EOF

echo "==> Done. Public: https://jarvisje.com/health"
