#!/usr/bin/env bash
set -Eeuo pipefail

# ===============================
# CONFIG
# ===============================
#LOG_DIR="/var/log/orion"
#LOG_FILE="$LOG_DIR/webdav_users.log"
LOG_FILE="/var/log/orion/admin-actions.log

BASE_DIR="/mnt/orion-nas/users"
HTPASSWD_FILE="/etc/nginx/dav/users.htpasswd"
GROUP_NAME="orion"
NGINX_USER="www-data"

# ===============================
# LOGGING
# ===============================
#mkdir -p "$LOG_DIR"
exec > >(tee -a "$LOG_FILE") 2>&1

echo "========================================"
echo " WebDAV USER PROVISION START"
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
PASSWORD="${ORION_WEBDAV_PASSWORD:-}"

if [[ -z "$USERNAME" ]]; then
  echo "Usage: sudo $0 <username>"
  exit 2
fi

USER_DIR="$BASE_DIR/$USERNAME"

echo "Provisioning user: $USERNAME"

# ===============================
# DIRECTORY SETUP
# ===============================
if [[ ! -d "$USER_DIR" ]]; then
  mkdir -p "$USER_DIR"
  echo "✔ Created directory $USER_DIR"
else
  echo "ℹ Directory already exists"
fi

chown "$GROUP_NAME:$GROUP_NAME" "$USER_DIR"
chmod 2770 "$USER_DIR"
chmod -R g+rwX "$USER_DIR"
echo "✔ Permissions set"

# ===============================
# GROUP CHECK
# ===============================
if ! id -nG "$NGINX_USER" | grep -qw "$GROUP_NAME"; then
  usermod -aG "$GROUP_NAME" "$NGINX_USER"
  echo "✔ Added $NGINX_USER to group $GROUP_NAME"
else
  echo "✔ $NGINX_USER already in group"
fi

# ===============================
# HTPASSWD
# ===============================
mkdir -p "$(dirname "$HTPASSWD_FILE")"

if [[ -n "$PASSWORD" ]]; then
  echo "✔ Using non-interactive password mode"
  if [[ ! -f "$HTPASSWD_FILE" ]]; then
    printf "%s\n" "$PASSWORD" | htpasswd -c -i "$HTPASSWD_FILE" "$USERNAME"
  else
    printf "%s\n" "$PASSWORD" | htpasswd -i "$HTPASSWD_FILE" "$USERNAME"
  fi
else
  echo "ℹ Using interactive password mode"
  if [[ ! -f "$HTPASSWD_FILE" ]]; then
    htpasswd -c "$HTPASSWD_FILE" "$USERNAME"
  else
    htpasswd "$HTPASSWD_FILE" "$USERNAME"
  fi
fi

echo "✔ User added to htpasswd"

# ===============================
# SMOKE TEST
# ===============================
sudo -u "$NGINX_USER" touch "$USER_DIR/.nginx-test"
rm "$USER_DIR/.nginx-test"
echo "✔ nginx write test passed"

echo "========================================"
echo " WebDAV USER PROVISION COMPLETE"
echo " End time: $(date)"
echo "========================================"