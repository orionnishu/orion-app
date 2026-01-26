#!/usr/bin/env bash
set -Eeuo pipefail

LOG_FILE="/var/log/orion/admin-actions.log"
TIMESTAMP="$(date '+%Y-%m-%d %H:%M:%S')"

{
  echo "========================================"
  echo "ACTION: sleepmypc"
  echo "START : $TIMESTAMP"
  echo "========================================"
} >> "$LOG_FILE"

# ---- Actual action (unchanged behavior) ----
ssh pkaga@192.168.50.2 "schtasks /run /tn SleepMyPC"

{
  echo "END   : $(date '+%Y-%m-%d %H:%M:%S')"
  echo
} >> "$LOG_FILE"