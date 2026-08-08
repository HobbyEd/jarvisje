#!/bin/bash
#
# One-time setup for systemd units on the Ubuntu production host (.15):
#   - sogyo-ollama.service   → docker compose up -d ollama
#   - sogyo-chatbot.service  → docker compose up -d app  (After ollama)
#
# Run ONCE on the server (with sudo):
#   sudo bash setup-sogyo-service.sh
#
# Manual control after install:
#   sudo systemctl status sogyo-ollama sogyo-chatbot
#   sudo systemctl restart sogyo-ollama
#   sudo systemctl restart sogyo-chatbot
#

set -euo pipefail

APP_DIR="/home/evdillen/sogyo-chatbot"
OLLAMA_UNIT="/etc/systemd/system/sogyo-ollama.service"
CHATBOT_UNIT="/etc/systemd/system/sogyo-chatbot.service"

echo "==> Configuring systemd services for Sogyo stack"
echo "    Ollama unit:  $OLLAMA_UNIT"
echo "    Chatbot unit: $CHATBOT_UNIT"
echo "    Compose dir:  $APP_DIR"

mkdir -p "$APP_DIR" \
  /home/evdillen/sogyo-chatbot-data \
  /home/evdillen/sogyo-ollama

if [[ ! -f "$APP_DIR/docker-compose.yaml" ]]; then
  echo "WARNING: $APP_DIR/docker-compose.yaml not found."
  echo "Copy infra/ubuntu-x64/docker-compose.prod-local.yaml there first."
fi

# Optional: copy server-deploy helper if present next to this script
if [[ -f "$(dirname "$0")/server-deploy.sh" ]]; then
  cp "$(dirname "$0")/server-deploy.sh" "$APP_DIR/server-deploy.sh"
  chmod +x "$APP_DIR/server-deploy.sh"
  echo "Copied server-deploy.sh to $APP_DIR/"
fi

# ---------------------------------------------------------------------------
# sogyo-ollama.service — starts only the ollama compose service
# ---------------------------------------------------------------------------
tee "$OLLAMA_UNIT" > /dev/null << 'EOF'
[Unit]
Description=Sogyo Ollama (Gemma 3 4B) Docker Compose Service
Documentation=https://github.com/ollama/ollama
Requires=docker.service
After=docker.service network-online.target
Wants=network-online.target

[Service]
Type=oneshot
RemainAfterExit=yes
User=root
Group=root
WorkingDirectory=/home/evdillen/sogyo-chatbot
Environment=HOME=/home/evdillen
Environment=IMAGE_TAG=latest

ExecStart=/usr/bin/docker compose up -d ollama
ExecStop=/usr/bin/docker compose stop ollama
ExecReload=/usr/bin/docker compose up -d --force-recreate ollama

TimeoutStartSec=300
TimeoutStopSec=120

[Install]
WantedBy=multi-user.target
EOF

# ---------------------------------------------------------------------------
# sogyo-chatbot.service — starts only the app; waits for ollama unit
# ---------------------------------------------------------------------------
tee "$CHATBOT_UNIT" > /dev/null << 'EOF'
[Unit]
Description=Sogyo Chatbot Docker Compose Service
Documentation=file:///home/evdillen/sogyo-chatbot/docker-compose.yaml
Requires=docker.service sogyo-ollama.service
After=docker.service network-online.target sogyo-ollama.service
Wants=network-online.target

[Service]
Type=oneshot
RemainAfterExit=yes
User=root
Group=root
WorkingDirectory=/home/evdillen/sogyo-chatbot
Environment=HOME=/home/evdillen
Environment=IMAGE_TAG=latest

ExecStart=/usr/bin/docker compose up -d app
ExecStop=/usr/bin/docker compose stop app
ExecReload=/usr/bin/docker compose up -d --force-recreate app

TimeoutStartSec=300
TimeoutStopSec=120

[Install]
WantedBy=multi-user.target
EOF

echo "==> Reloading systemd daemon..."
systemctl daemon-reload

echo "==> Enabling services (auto-start on boot)..."
systemctl enable sogyo-ollama.service sogyo-chatbot.service

echo "==> Starting services..."
systemctl restart sogyo-ollama.service
systemctl restart sogyo-chatbot.service

echo ""
echo "==> Status:"
systemctl status sogyo-ollama.service --no-pager || true
echo ""
systemctl status sogyo-chatbot.service --no-pager || true

echo ""
echo "==> Done."
echo "    Boot order: docker → sogyo-ollama → sogyo-chatbot"
echo "    Control:"
echo "      sudo systemctl status  sogyo-ollama sogyo-chatbot"
echo "      sudo systemctl restart sogyo-ollama"
echo "      sudo systemctl restart sogyo-chatbot"
echo "      sudo systemctl stop    sogyo-chatbot   # app only"
echo "      sudo systemctl stop    sogyo-ollama    # ollama only"
