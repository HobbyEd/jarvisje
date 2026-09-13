#!/usr/bin/env bash
#
# One-time host cutover on <host> (enterprise):
#   ~/sogyo-chatbot      → ~/jarvisje-chatbot
#   ~/sogyo-chatbot-data → ~/jarvisje-chatbot-data
#
# Leaves ~/sogyo-ollama and container sogyo-ollama (Gemma) running.
# Creates a symlink ~/sogyo-chatbot → ~/jarvisje-chatbot so existing
# systemd units (WorkingDirectory=.../sogyo-chatbot) keep working until
# they can be updated with sudo.
#
# Usage (from a machine with SSH to enterprise):
#   ./scripts/cutover-dirs-on-15.sh
#
set -euo pipefail

HOST="${DEPLOY_HOST:-<user>@<host>}"

ssh -o BatchMode=yes "$HOST" bash -s <<'EOF'
set -euo pipefail
cd ~

if [[ -d jarvisje-chatbot && -d jarvisje-chatbot-data ]]; then
  echo "Already cut over: jarvisje-chatbot and jarvisje-chatbot-data exist."
  ls -ld jarvisje-chatbot jarvisje-chatbot-data sogyo-chatbot sogyo-chatbot-data 2>/dev/null || true
  exit 0
fi

if [[ ! -d sogyo-chatbot || ! -d sogyo-chatbot-data ]]; then
  echo "ERROR: expected ~/sogyo-chatbot and ~/sogyo-chatbot-data" >&2
  ls -ld sogyo-chatbot sogyo-chatbot-data 2>/dev/null || true
  exit 1
fi

echo "==> Stop app container only (leave sogyo-ollama / Gemma)"
docker stop sogyo-chatbot-app 2>/dev/null || true
docker rm sogyo-chatbot-app 2>/dev/null || true

echo "==> Rename directories"
mv sogyo-chatbot-data jarvisje-chatbot-data
mv sogyo-chatbot jarvisje-chatbot

echo "==> Symlink old compose path for systemd (no sudo required)"
ln -sfn ~/jarvisje-chatbot ~/sogyo-chatbot

echo "==> Result"
ls -ld jarvisje-chatbot jarvisje-chatbot-data sogyo-chatbot sogyo-ollama
docker ps --filter name=sogyo-ollama --format '{{.Names}} {{.Status}}'
EOF

echo "==> Cutover dirs done on $HOST"
