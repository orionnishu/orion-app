#!/usr/bin/env bash
set -euo pipefail

echo "=== ORION DEPLOY START ==="

APP_DIR="$HOME/server"
SERVICE_NAME="orion-app"

cd "$APP_DIR"

echo "[1/3] Fetching latest code..."
git fetch origin
git status

read -p "Pull latest changes from main? [y/N]: " confirm
if [[ "$confirm" != "y" ]]; then
  echo "Aborted."
  exit 0
fi

git pull origin main

echo "[2/3] Restarting service..."
sudo systemctl restart "$SERVICE_NAME"

echo "[3/3] Checking service status..."
sudo systemctl status "$SERVICE_NAME" --no-pager

echo "=== ORION DEPLOY COMPLETE ==="