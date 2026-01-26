#!/usr/bin/env bash
set -Eeuo pipefail

LOG_FILE="/var/log/orion/admin-actions.log"
TIMESTAMP="$(date '+%Y-%m-%d %H:%M:%S')"

{
  echo "========================================"
  echo "ACTION: wakemypc"
  echo "START : $TIMESTAMP"
  echo "========================================"
} >> "$LOG_FILE"

# ---- Actual action (unchanged behavior) ----
wakeonlan -i 192.168.50.255 A0:CE:C8:0A:4A:1D

{
  echo "END   : $(date '+%Y-%m-%d %H:%M:%S')"
  echo
} >> "$LOG_FILE"