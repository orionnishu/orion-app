#!/usr/bin/env bash
set -Eeuo pipefail

LOG_FILE="/var/log/orion/admin-actions.log"
TIMESTAMP="$(date '+%Y-%m-%d %H:%M:%S')"

# MQTT config (ESP32 power-button relay)
MQTT_HOST="192.168.0.103"
MQTT_CMD_TOPIC="orion/pc/cmd"
MQTT_STATUS_TOPIC="orion/pc/status"

# Ethernet fallback (Wake-on-LAN)
WOL_BROADCAST="192.168.50.255"
WOL_MAC="A0:CE:C8:0A:4A:1D"

{
  echo "========================================"
  echo "ACTION: wakemypc"
  echo "START : $TIMESTAMP"
  echo "========================================"

  # --- Method 1: MQTT via ESP32 ---
  esp32_status=$(mosquitto_sub -h "$MQTT_HOST" -t "$MQTT_STATUS_TOPIC" -C 1 -W 2 2>/dev/null || echo "unreachable")

  if [ "$esp32_status" = "esp32_online" ]; then
    echo "ESP32 is online. Sending wake command via MQTT..."
    if mosquitto_pub -h "$MQTT_HOST" -t "$MQTT_CMD_TOPIC" -m "pc/on_or_off" 2>&1; then
      echo "MQTT wake command sent successfully."
    else
      echo "ERROR: MQTT publish failed (exit code: $?)"
    fi
  else
    echo "WARNING: ESP32 is not available (status: $esp32_status). Falling back to WoL..."

    # --- Method 2: Wake-on-LAN via ethernet ---
    echo "Sending WoL packet to $WOL_BROADCAST (MAC: $WOL_MAC)..."
    if wakeonlan -i "$WOL_BROADCAST" "$WOL_MAC" 2>&1; then
      echo "WoL packet sent successfully."
    else
      echo "ERROR: WoL also failed (exit code: $?)"
      echo "ERROR: Both methods unavailable — ESP32 is not on, Ethernet cable is not connected."
    fi
  fi

  echo "END   : $(date '+%Y-%m-%d %H:%M:%S')"
  echo
} >> "$LOG_FILE"