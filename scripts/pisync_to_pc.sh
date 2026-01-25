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
  --human-readable
  --partial
  --remove-source-files
)

# Wake/sleep controls
WAKE_CMD="wakemypc"
SLEEP_CMD="sleepmypc"
MAX_WAKE_RETRIES=10
WAKE_SLEEP_SEC=2

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

# ===============================
# CHECK / WAKE PC
# ===============================
echo "Checking if destination PC is reachable via SSH..."

attempt=1
while true; do
  if ssh $SSH_OPTS "$DEST_USER@$DEST_HOST" "bash -lc 'echo SSH_OK'" >/dev/null 2>&1; then
    echo "Destination PC is ONLINE"
    break
  fi

  if (( attempt > MAX_WAKE_RETRIES )); then
    echo "ERROR: PC did not come online after $MAX_WAKE_RETRIES attempts"
    exit 1
  fi

  if (( attempt == 1 )); then
    echo "PC is OFFLINE — sending wake signal..."
    $WAKE_CMD
  else
    echo "Waiting for PC to wake (attempt $attempt/$MAX_WAKE_RETRIES)..."
  fi

  sleep "$WAKE_SLEEP_SEC"
  ((attempt++))
done

# ===============================
# VERIFY DESTINATION DIRECTORY (MSYS)
# ===============================
echo "Verifying destination directory on Windows..."
ssh $SSH_OPTS "$DEST_USER@$DEST_HOST" \
  "bash -lc '[[ -d \"$DEST_DIR\" ]]'" \
  || { echo "ERROR: Destination directory does not exist: $DEST_DIR"; exit 1; }

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

# ===============================
# PUT PC TO SLEEP
# ===============================
echo "Sync complete — putting PC to sleep..."
$SLEEP_CMD || echo "WARNING: sleepmypc failed (continuing)"

echo "========================================"
echo " Sync completed successfully"
echo " End time: $(date)"
echo "========================================"