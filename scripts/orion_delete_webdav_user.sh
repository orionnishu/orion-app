#!/usr/bin/env bash
set -Eeuo pipefail

# ===============================
# CONFIG
# ===============================
LOG_FILE="/var/log/orion/admin-actions.log"
BASE_DIR="/mnt/orion-nas/users"
HTPASSWD_FILE="/etc/nginx/dav/users.htpasswd"

# ===============================
# LOGGING
# ===============================
exec > >(tee -a "$LOG_FILE") 2>&1

echo "========================================"
echo " WebDAV USER DELETE"
echo " Time: $(date)"
echo "========================================"

# ===============================
# PRE-FLIGHT
# ===============================
if [[ "$EUID" -ne 0 ]]; then
  echo "❌ Must be run as root"
  exit 1
fi

USERNAME="${1:-}"
DELETE_FLAG="${2:---delete-data}"

if [[ -z "$USERNAME" ]]; then
  echo "Usage: sudo $0 <username> [--delete-data|--keep-data]"
  exit 2
fi

USER_DIR="$BASE_DIR/$USERNAME"

echo "User to delete: $USERNAME"
echo "Delete data flag: $DELETE_FLAG"

# ===============================
# REMOVE FROM HTPASSWD
# ===============================
if [[ -f "$HTPASSWD_FILE" ]]; then
  if grep -q "^${USERNAME}:" "$HTPASSWD_FILE"; then
    # Create temp file without the user
    grep -v "^${USERNAME}:" "$HTPASSWD_FILE" > "${HTPASSWD_FILE}.tmp"
    mv "${HTPASSWD_FILE}.tmp" "$HTPASSWD_FILE"
    echo "✔ Removed from htpasswd"
  else
    echo "ℹ User not found in htpasswd"
  fi
else
  echo "⚠ htpasswd file not found"
fi

# ===============================
# DATA FOLDER
# ===============================
if [[ "$DELETE_FLAG" == "--delete-data" ]]; then
  if [[ -d "$USER_DIR" ]]; then
    rm -rf "$USER_DIR"
    echo "✔ Deleted data folder: $USER_DIR"
  else
    echo "ℹ Data folder does not exist"
  fi
else
  echo "ℹ Keeping data folder (--keep-data)"
fi

echo "========================================"
echo " WebDAV USER DELETE COMPLETE"
echo " End time: $(date)"
echo "========================================"
