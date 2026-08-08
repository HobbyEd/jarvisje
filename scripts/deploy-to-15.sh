#!/usr/bin/env bash
#
# Lean deploy: rsync sources → build Docker image on 192.168.165.15 → recreate app.
# Requires SSH key access as evdillen; user must be in the docker group (no sudo).
#
# Usage (from repo root):
#   ./scripts/deploy-to-15.sh
#   ./scripts/deploy-to-15.sh 0.6.3
#
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
HOST="${DEPLOY_HOST:-evdillen@192.168.165.15}"
TAG="${1:-latest}"
REMOTE_BUILD="$HOME/sogyo-chatbot/build-src"
# Expand remote home via ssh
REMOTE_BASE="sogyo-chatbot"

cd "$ROOT"

echo "==> Rsync source to $HOST:~/$REMOTE_BASE/build-src"
rsync -az --delete \
  --exclude '__pycache__' \
  --exclude '.DS_Store' \
  -e 'ssh -o BatchMode=yes' \
  src scripts web requirements.txt pyproject.toml \
  "$HOST:~/$REMOTE_BASE/build-src/"

scp -o BatchMode=yes \
  infra/ubuntu-x64/Dockerfile \
  "$HOST:~/$REMOTE_BASE/build-src/Dockerfile"

scp -o BatchMode=yes \
  infra/ubuntu-x64/docker-compose.prod-local.yaml \
  "$HOST:~/$REMOTE_BASE/docker-compose.yaml"

echo "==> Build & recreate app on server (tag=$TAG)"
ssh -o BatchMode=yes "$HOST" bash -s <<EOF
set -euo pipefail
cd ~/$REMOTE_BASE/build-src
docker build -t "sogyo-chatbot:${TAG}" -t sogyo-chatbot:latest -f Dockerfile .
cd ~/$REMOTE_BASE
IMAGE_TAG=latest docker compose up -d --force-recreate --no-deps app
sleep 4
curl -sf --max-time 10 http://127.0.0.1:8080/health | head -c 300
echo
docker ps --filter name=sogyo-chatbot-app --format '{{.Names}} {{.Status}} {{.Image}}'
EOF

echo "==> Done. Public: https://jarvisje.com/health"
