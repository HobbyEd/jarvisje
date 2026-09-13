#!/usr/bin/env bash
#
# Lean deploy: rsync sources → build Docker image on <host> → recreate app.
# Requires SSH key access as <user>; user must be in the docker group (no sudo).
#
# Secrets (ADR-011): copies local .env to the host compose dir (not into the image).
# Does not recreate Ollama / Gemma (container sogyo-ollama).
#
# Usage (from repo root):
#   ./scripts/deploy-to-15.sh
#   ./scripts/deploy-to-15.sh 1.0.2
#
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
HOST="${DEPLOY_HOST:-<user>@<host>}"
TAG="${1:-latest}"
REMOTE_BASE="jarvisje-chatbot"
APP_CONTAINER="jarvisje-chatbot-app"
IMAGE="jarvisje"

cd "$ROOT"

if [[ ! -f "$ROOT/.env" ]]; then
  echo "WARNING: no local .env found. UI indexering requires INGEST_TOKEN (ADR-011)." >&2
  echo "         cp .env.example .env  &&  edit INGEST_TOKEN=..." >&2
else
  if ! grep -qE '^(INGEST_TOKEN|INDEX_TOKEN)=.+' "$ROOT/.env"; then
    echo "WARNING: .env has no non-empty INGEST_TOKEN/INDEX_TOKEN." >&2
  fi
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

if [[ -f "$ROOT/.env" ]]; then
  echo "==> Install host .env (mode 600, not in image) — ADR-011"
  scp -o BatchMode=yes "$ROOT/.env" "$HOST:~/$REMOTE_BASE/.env"
  ssh -o BatchMode=yes "$HOST" "chmod 600 ~/$REMOTE_BASE/.env"
else
  echo "==> Skipping .env deploy (file missing locally)"
fi

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
if docker exec ${APP_CONTAINER} grep -R '<old-token-fragment>' /app/src 2>/dev/null; then
  echo "ERROR: old hardcoded token fragment still in image source" >&2
  exit 1
fi
if [[ "\$ok" -ne 1 ]]; then
  echo "WARNING: health not ready yet; check docker logs ${APP_CONTAINER}" >&2
  exit 1
fi
EOF

echo "==> Done. Public: https://jarvisje.com/health"
