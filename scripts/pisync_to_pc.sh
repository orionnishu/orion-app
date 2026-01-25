#!/usr/bin/env bash
set -Eeuo pipefail

# ===============================
# CONFIG
# ===============================
SRC_DIR="/mnt/orion-nas/users/ruchi_realme/Camera/"
DEST_USER="pkaga"
DEST_HOST="192.168.50.2"
DEST_DIR="/d/pisync/inbound"

LOG_DIR="/var/log/pisynctopc"
TIMESTAMP="$(date '+%Y-%m-%d_%H-%M-%S')"
LOG_FILE="$LOG_DIR/pisync_$TIMESTAMP.log"

SSH_OPTS="-o BatchMode=yes -o StrictHostKeyChecking=accept-new"
RSYNC_OPTS=(
  -avt
  --progress
  --stats
  --partial
  --human-readable
  --remove-source-files
)

# ===============================
# PRE-FLIGHT
# ===============================
mkdir -p "$LOG_DIR"

exec > >(tee -a "$LOG_FILE") 2>&1

echo "========================================"
echo " Pi → Windows Sync (MOVE MODE)"
echo " Time: $(date)"
echo " Source: $SRC_DIR"
echo " Destination: $DEST_USER@$DEST_HOST:$DEST_DIR"
echo " Log: $LOG_FILE"
echo "========================================"

# Verify source exists
if [[ ! -d "$SRC_DIR" ]]; then
  echo "ERROR: Source directory does not exist"
  exit 1
fi

# Verify SSH connectivity
echo "Checking SSH connectivity..."
ssh $SSH_OPTS "$DEST_USER@$DEST_HOST" "echo SSH_OK" >/dev/null
echo "SSH OK"

# ===============================
# SYNC (COPY + DELETE FILES)
# ===============================
echo "Starting rsync (files will be removed from source after successful transfer)..."

rsync "${RSYNC_OPTS[@]}" \
  -e "ssh $SSH_OPTS" \
  "$SRC_DIR" \
  "$DEST_USER@$DEST_HOST:$DEST_DIR"

# ===============================
# CLEANUP EMPTY DIRECTORIES
# ===============================
echo "Removing empty subdirectories from source (keeping root)..."
find "$SRC_DIR" -mindepth 1 -type d -empty -delete

echo "========================================"
echo " Sync completed successfully"
echo " End time: $(date)"
echo "========================================"
