#!/bin/bash
# Upload project from local machine to VPS and install.
# Usage: ./deploy/upload.sh user@your-server-ip

set -euo pipefail

if [ $# -lt 1 ]; then
    echo "Usage: $0 user@server-ip"
    echo "Example: $0 root@123.45.67.89"
    exit 1
fi

SERVER="$1"
REMOTE_DIR="/opt/english-tutor-bot"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "==> Uploading to ${SERVER}:${REMOTE_DIR}"
ssh "${SERVER}" "mkdir -p ${REMOTE_DIR}"
rsync -avz --exclude venv --exclude .git --exclude __pycache__ --exclude 'data/*.db' --exclude data/audio \
    "${SCRIPT_DIR}/" "${SERVER}:${REMOTE_DIR}/"

echo "==> Running install script on server"
ssh "${SERVER}" "chmod +x ${REMOTE_DIR}/deploy/install.sh && bash ${REMOTE_DIR}/deploy/install.sh"

echo ""
echo "Upload complete. SSH to server and:"
echo "  nano ${REMOTE_DIR}/.env"
echo "  systemctl start english-tutor"
