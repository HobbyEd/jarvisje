#!/bin/bash
#
# Server-side deploy script.
# Copied by deploy.ps1 and executed on the production host.
#
# It:
#   - Loads the new docker image from the tarball
#   - Tags it properly (versioned + latest)
#   - Sets IMAGE_TAG
#   - Recreates the app (prefer: IMAGE_TAG=latest docker compose up -d app)
#
# Usage (called from deploy.ps1):
#   ./server-deploy.sh jarvisje-master-abc1234.tar.gz
#
# Or manually:
#   ./server-deploy.sh
#
# Lean path (no sudo, app only): ./scripts/deploy-to-15.sh
#

set -euo pipefail

DEPLOY_USER="${DEPLOY_USER:-${SUDO_USER:-$(id -un)}}"
HOST_HOME="${HOST_HOME:-/home/${DEPLOY_USER}}"
DEPLOY_DIR="${HOST_HOME}/jarvisje-chatbot"
ARTIFACTS_DIR="$DEPLOY_DIR/deploy-artifacts"
IMAGE="jarvisje"
APP_CONTAINER="jarvisje-chatbot-app"

# Ensure the deploy directory is owned by the normal user (in case previous docker/sudo runs left root-owned files)
sudo chown -R "${DEPLOY_USER}:${DEPLOY_USER}" "$DEPLOY_DIR" 2>/dev/null || true

cd "$DEPLOY_DIR"

# Allow passing the tar name as argument, otherwise take the newest one
TAR_NAME="${1:-}"

if [[ -z "$TAR_NAME" ]]; then
    TAR_NAME=$(ls -t "$ARTIFACTS_DIR"/${IMAGE}-*.tar.gz 2>/dev/null | head -n 1 | xargs -r basename || true)
fi

if [[ -z "$TAR_NAME" || ! -f "$ARTIFACTS_DIR/$TAR_NAME" ]]; then
    echo "ERROR: No valid tarball found in $ARTIFACTS_DIR"
    echo "Expected something like ${IMAGE}-master-xxx.tar.gz"
    exit 1
fi

echo "==> Using artifact: $TAR_NAME"

# Also clean up any leftover old tarballs before loading (in case of previous failed runs)
find "$ARTIFACTS_DIR" -name "${IMAGE}-*.tar.gz" ! -name "$TAR_NAME" -type f -delete 2>/dev/null || true

# Diagnose port 8080
echo "==> Checking what is using port 8080 on the host:"
sudo ss -tuln 2>/dev/null | grep ':8080' || sudo netstat -tuln 2>/dev/null | grep ':8080' || echo "  (no listener found on 8080 via ss/netstat)"
docker ps -a --format '{{.ID}} {{.Names}} {{.Ports}}' | grep -E "8080|${APP_CONTAINER}|jarvisje" || echo "  No jarvisje or 8080 container found in docker ps"

# Extract the tag from the filename
# Example: jarvisje-master-bb9ddb4.tar.gz  ->  master-bb9ddb4
TAG=$(basename "$TAR_NAME" | sed -E "s/^${IMAGE}-//; s/\\.tar\\.gz$//")

# --- Cleanup to free port 8080 (app only; leave sogyo-ollama / Gemma running) ---
echo "==> Stopping chatbot unit and removing old app container..."
sudo systemctl stop sogyo-chatbot 2>/dev/null || true
docker rm -f "$APP_CONTAINER" 2>/dev/null || true

# Extra: stop any container that might be publishing 8080
docker ps -q --filter publish=8080 | xargs -r docker stop 2>/dev/null || true
docker ps -q --filter publish=8080 | xargs -r docker rm -f 2>/dev/null || true

# Note: if a non-docker process is holding the port, you may need to kill it manually:
#   sudo fuser -k 8080/tcp
# or identify it with: sudo ss -tlnp | grep 8080

# Give the kernel a moment to release the port after removing containers
sleep 2

echo "==> Loading Docker image..."
docker load -i "$ARTIFACTS_DIR/$TAR_NAME"

echo "==> Tagging image as ${IMAGE}:$TAG and ${IMAGE}:latest"
docker tag "${IMAGE}:$TAG" "${IMAGE}:latest"
# Keep the versioned tag as well (useful for rollback)
docker tag "${IMAGE}:$TAG" "${IMAGE}:$TAG"

echo "==> Starting app with IMAGE_TAG=latest (Ollama not recreated)..."
IMAGE_TAG=latest docker compose up -d --no-deps app

echo ""
echo "==> Deployment finished. Current status:"
docker compose ps
echo ""
docker images | grep -E "${IMAGE}|REPOSITORY" | head -5

echo ""
echo "==> Cleaning up old images and artifacts on server..."

# Remove the tarball we just used (no need to keep it after load)
if [[ -f "$ARTIFACTS_DIR/$TAR_NAME" ]]; then
    echo "==> Removing used tarball: $TAR_NAME"
    rm -f "$ARTIFACTS_DIR/$TAR_NAME"
fi

# Keep only the 2 most recent tarballs (current + previous for rollback)
echo "==> Keeping last 2 tarballs for rollback..."
ls -t "$ARTIFACTS_DIR"/${IMAGE}-*.tar.gz 2>/dev/null | tail -n +3 | xargs -r rm -f || true

# Get the image ID that the running container is actually using
CURRENT_IMAGE_ID=$(docker inspect "$APP_CONTAINER" --format='{{.Image}}' 2>/dev/null | sed 's/^sha256://' || true)

if [[ -n "$CURRENT_IMAGE_ID" ]]; then
    echo "==> Current running image ID: ${CURRENT_IMAGE_ID:0:12}"

    # Keep the 2 most recently created jarvisje images (current + previous)
    mapfile -t keep < <(docker images "$IMAGE" --format '{{.ID}}' | head -n 2)
    docker images "$IMAGE" --format '{{.ID}}' | while read -r img_id; do
        if [[ ! " ${keep[*]} " =~ " $img_id " ]]; then
            echo "==> Removing old image: $img_id"
            docker rmi -f "$img_id" 2>/dev/null || true
        fi
    done
else
    echo "==> Could not determine current image ID, skipping image cleanup"
fi

# Optional: remove dangling images
docker image prune -f --filter "dangling=true" 2>/dev/null || true

echo ""
echo "==> Cleanup complete. The Jarvisje app should have been restarted."
echo "    (Old images and tarballs removed. Only the newly deployed version remains.)"
echo "    Ollama / Gemma (sogyo-ollama) was not recreated."
