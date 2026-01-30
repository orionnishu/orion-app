#!/usr/bin/env bash
set -Eeuo pipefail

LOG_FILE="/var/log/orion/admin-actions.log"
TIMESTAMP="$(date '+%Y-%m-%d %H:%M:%S')"

{
  echo "========================================"
  echo "ACTION: wakemypc"
  echo "START : $TIMESTAMP"
  echo "========================================"

  # Actual action with output captured
  echo "Sending WoL packet to 192.168.50.255 (MAC: A0:CE:C8:0A:4A:1D)..."
  if wakeonlan -i 192.168.50.255 A0:CE:C8:0A:4A:1D 2>&1; then
    echo "WoL packet sent successfully."
  else
    echo "ERROR: Failed to send WoL packet (exit code: $?)"
  fi

  echo "END   : $(date '+%Y-%m-%d %H:%M:%S')"
  echo
} >> "$LOG_FILE"