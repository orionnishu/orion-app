#!/bin/bash

# ORION WebDAV User Provisioning Script
# Creates a new WebDAV user with proper permissions and structure
# Usage: sudo ./orion_add_webdav_user.sh <username>

set -e

if [ "$EUID" -ne 0 ]; then
  echo "❌ Please run as root (use sudo)"
  exit 1
fi

USERNAME="$1"
BASE_DIR="/mnt/orion-nas/users"
USER_DIR="${BASE_DIR}/${USERNAME}"
HTPASSWD_FILE="/etc/nginx/dav/users.htpasswd"
GROUP_NAME="orion"
NGINX_USER="www-data"

if [ -z "$USERNAME" ]; then
  echo "Usage: sudo $0 <username>"
  exit 1
fi

echo "▶️ Creating WebDAV user: $USERNAME"

# Step 1: Create directory
if [ ! -d "$USER_DIR" ]; then
  mkdir -p "$USER_DIR"
  echo "✔ Created directory $USER_DIR"
else
  echo "ℹ Directory already exists"
fi

# Step 2: Ownership and permissions
chown "$GROUP_NAME:$GROUP_NAME" "$USER_DIR"
chmod 2770 "$USER_DIR"
chmod -R g+rwX "$USER_DIR"
echo "✔ Permissions set (group-writable, setgid)"

# Step 3: Ensure nginx user is in group
if id -nG "$NGINX_USER" | grep -qw "$GROUP_NAME"; then
  echo "✔ $NGINX_USER already in group $GROUP_NAME"
else
  usermod -aG "$GROUP_NAME" "$NGINX_USER"
  echo "✔ Added $NGINX_USER to group $GROUP_NAME"
fi

# Step 4: Add to htpasswd
if [ ! -f "$HTPASSWD_FILE" ]; then
  mkdir -p "$(dirname "$HTPASSWD_FILE")"
  htpasswd -c "$HTPASSWD_FILE" "$USERNAME"
else
  htpasswd "$HTPASSWD_FILE" "$USERNAME"
fi

echo "✔ User added to htpasswd"

# Step 5: Smoke test
sudo -u "$NGINX_USER" touch "$USER_DIR/.nginx-test" && rm "$USER_DIR/.nginx-test"
echo "✔ nginx write test passed"

echo "🎉 WebDAV user '$USERNAME' provisioned successfully"
