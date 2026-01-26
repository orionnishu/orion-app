#!/usr/bin/env bash
set -Eeuo pipefail

# ======================================
# ORION – Pi → Windows Sync (MOVE MODE)
# ======================================

# ---------- LOGGING (STANDARDISED) ----------
LOG_FILE="/var/log/orion/admin-actions.log"

mkdir -p "$(dirname "$LOG_FILE")"

exec >>"$LOG_FILE" 2>&1

echo "========================================"
echo "[$(date '+%Y-%m-%d %H:%M:%S')] START: pisync_to_pc.sh"
echo "========================================"

# ---------- CONFIG ----------
SRC_DIR="/mnt/orion-nas/users/ruchi_realme/Camera/"
DEST_USER="pkaga"
DEST_HOST="192.168.50.2"
DEST_DIR="/c/Users/pkaga/D/pisync/inbound"

SSH_OPTS="-o BatchMode=yes -o StrictHostKeyChecking=accept-new"
RSYNC_OPTS=(
  -avt
  --stats
  --human-readable
  --partial
  --remove-source-files
)

# ---------- PRE-FLIGHT ----------
echo "Time: $(date)"
echo "Source: $SRC_DIR"
echo "Destination: $DEST_USER@$DEST_HOST:$DEST_DIR"

if [[ ! -d "$SRC_DIR" ]]; then
  echo "ERROR: Source directory does not exist: $SRC_DIR"
  exit 1
fi

echo "Checking SSH connectivity..."
ssh $SSH_OPTS "$DEST_USER@$DEST_HOST" "echo SSH_OK" >/dev/null
echo "SSH OK"

echo "Verifying destination directory on Windows..."
ssh $SSH_OPTS "$DEST_USER@$DEST_HOST" "test -d '$DEST_DIR'" || {
  echo "ERROR: Destination directory does not exist: $DEST_DIR"
  exit 1
}

# ---------- SYNC ----------
echo "Starting rsync (files will be removed from source after successful transfer)..."

rsync "${RSYNC_OPTS[@]}" \
  -e "ssh $SSH_OPTS" \
  "$SRC_DIR" \
  "$DEST_USER@$DEST_HOST:$DEST_DIR"

# ---------- CLEANUP ----------
echo "Removing empty directories from source..."
find "$SRC_DIR" -mindepth 1 -type d -empty -delete

echo "========================================"
echo "[$(date '+%Y-%m-%d %H:%M:%S')] END: pisync_to_pc.sh"
echo