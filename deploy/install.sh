#!/bin/bash
set -euo pipefail

APP_DIR="/opt/english-tutor-bot"
SERVICE_NAME="english-tutor"

echo "==> Installing English Tutor Bot to ${APP_DIR}"

if ! command -v python3 &>/dev/null; then
    echo "python3 not found. Install: apt install python3 python3-venv python3-pip"
    exit 1
fi

mkdir -p "${APP_DIR}"

# Copy project files (run from project root on server)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
rsync -a --exclude venv --exclude .git --exclude __pycache__ --exclude data/audio \
    "${SCRIPT_DIR}/" "${APP_DIR}/"

cd "${APP_DIR}"

if [ ! -d venv ]; then
    python3 -m venv venv
fi

./venv/bin/pip install --upgrade pip
./venv/bin/pip install -r requirements.txt

if [ ! -f .env ]; then
    cp .env.example .env
    echo ""
    echo "!!! Create ${APP_DIR}/.env with BOT_TOKEN and DEEPSEEK_API_KEY"
    echo "    nano ${APP_DIR}/.env"
    echo ""
fi

mkdir -p data data/audio

cp english-tutor.service /etc/systemd/system/${SERVICE_NAME}.service
systemctl daemon-reload
systemctl enable "${SERVICE_NAME}"

echo ""
echo "Done. Next steps:"
echo "  1. Edit config:  nano ${APP_DIR}/.env"
echo "  2. Start bot:    systemctl start ${SERVICE_NAME}"
echo "  3. Check status: systemctl status ${SERVICE_NAME}"
echo "  4. View logs:    journalctl -u ${SERVICE_NAME} -f"
