#!/usr/bin/env bash
set -Eeuo pipefail

LOG_FILE="/var/log/orion/admin-actions.log"
TIMESTAMP="$(date '+%Y-%m-%d %H:%M:%S')"

# MQTT config (ESP32 power-button relay)
MQTT_HOST="192.168.0.103"
MQTT_CMD_TOPIC="orion/pc/cmd"
MQTT_STATUS_TOPIC="orion/pc/status"

# Ethernet fallback (SSH sleep task)
PC_HOSTNAME="192.168.0.102"

{
  echo "========================================"
  echo "ACTION: sleepmypc"
  echo "START : $TIMESTAMP"
  echo "========================================"

  # --- Method 1: MQTT via ESP32 ---
  esp32_status=$(mosquitto_sub -h "$MQTT_HOST" -t "$MQTT_STATUS_TOPIC" -C 1 -W 2 2>/dev/null || echo "unreachable")

  if [ "$esp32_status" = "esp32_online" ]; then
    echo "ESP32 is online. Sending sleep command via MQTT..."
    if mosquitto_pub -h "$MQTT_HOST" -t "$MQTT_CMD_TOPIC" -m "pc/on_or_off" 2>&1; then
      echo "MQTT sleep command sent successfully."
    else
      echo "ERROR: MQTT publish failed (exit code: $?)"
    fi
  else
    echo "WARNING: ESP32 is not available (status: $esp32_status). Falling back to SSH..."

    # --- Method 2: SSH via ethernet ---
    echo "Sending sleep command to PC ($PC_HOSTNAME)..."
    if ssh -o ConnectTimeout=5 -o BatchMode=yes pkaga@$PC_HOSTNAME "schtasks /run /tn SleepMyPC" 2>&1; then
      echo "SSH sleep command sent successfully."
    else
      echo "ERROR: SSH also failed (exit code: $?)"
      echo "ERROR: Both methods unavailable — ESP32 is not on, Ethernet cable is not connected."
    fi
  fi

  echo "END   : $(date '+%Y-%m-%d %H:%M:%S')"
  echo
} >> "$LOG_FILE"