#!/usr/bin/env bash
set -Eeuo pipefail

LOG_FILE="/var/log/orion/admin-actions.log"
TIMESTAMP="$(date '+%Y-%m-%d %H:%M:%S')"

{
  echo "========================================"
  echo "ACTION: sleepmypc"
  echo "START : $TIMESTAMP"
  echo "========================================"

  # Actual action with output captured
  echo "Sending sleep command to PC (192.168.50.2)..."
  if ssh -o ConnectTimeout=5 -o BatchMode=yes pkaga@192.168.50.2 "schtasks /run /tn SleepMyPC" 2>&1; then
    echo "Sleep command sent successfully."
  else
    echo "ERROR: Failed to send sleep command (exit code: $?)"
  fi

  echo "END   : $(date '+%Y-%m-%d %H:%M:%S')"
  echo
} >> "$LOG_FILE"