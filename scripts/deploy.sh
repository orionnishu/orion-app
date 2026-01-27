#!/usr/bin/env bash
set -Eeuo pipefail

# ===============================
# CONFIG
# ===============================
APP_DIR="$HOME/server"
SERVICE_NAME="orion-server.service"
#LOG_DIR="/var/log/orion"
#LOG_FILE="$LOG_DIR/deploy.log"
LOG_FILE="/var/log/orion/admin-actions.log

AUTO_YES=false
if [[ "${1:-}" == "--yes" ]]; then
  AUTO_YES=true
fi

# ===============================
# LOGGING
# ===============================
#mkdir -p "$LOG_DIR"
exec > >(tee -a "$LOG_FILE") 2>&1

echo "========================================"
echo " ORION DEPLOY START"
echo " Time: $(date)"
echo " Auto mode: $AUTO_YES"
echo "========================================"

cd "$APP_DIR"

echo "[1/3] Fetching latest code..."
git fetch origin
git status

if [[ "$AUTO_YES" == false ]]; then
  read -r -p "Pull latest changes from main? [y/N]: " confirm
  if [[ "$confirm" != "y" ]]; then
    echo "Aborted by user."
    exit 0
  fi
fi

git pull origin main

echo "[2/3] Restarting service..."
sudo systemctl restart "$SERVICE_NAME"

echo "[3/3] Verifying service state..."
if ! sudo systemctl is-active --quiet "$SERVICE_NAME"; then
  echo "❌ Service failed to start"
  sudo systemctl status "$SERVICE_NAME" --no-pager
  exit 1
fi

sudo systemctl status "$SERVICE_NAME" --no-pager

echo "========================================"
echo " ORION DEPLOY COMPLETE"
echo " End time: $(date)"
echo "========================================"