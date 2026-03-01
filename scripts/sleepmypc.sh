#!/usr/bin/env bash
set -Eeuo pipefail

LOG_FILE="/var/log/orion/admin-actions.log"
TIMESTAMP="$(date '+%Y-%m-%d %H:%M:%S')"
PC_HOSTNAME="orion-desktoppc-wifi"

{
  echo "========================================"
  echo "ACTION: sleepmypc"
  echo "START : $TIMESTAMP"
  echo "========================================"

  # Actual action with output captured
  echo "Sending sleep command to PC ($PC_HOSTNAME)..."
  if ssh -o ConnectTimeout=5 -o BatchMode=yes pkaga@$PC_HOSTNAME "schtasks /run /tn SleepMyPC" 2>&1; then
    echo "Sleep command sent successfully."
  else
    echo "ERROR: Failed to send sleep command (exit code: $?)"
  fi

  echo "END   : $(date '+%Y-%m-%d %H:%M:%S')"
  echo
} >> "$LOG_FILE"