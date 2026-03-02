#!/bin/bash

# Configuration
DB_PATH="$HOME/server/services/pi-monitor/db/pi-monitor.db"
LOG_PATH="$HOME/server/services/pi-monitor/logs/pi-monitor.log"
TS=$(/bin/date "+%Y-%m-%d %H:%M:%S")
SOURCE="pi-monitor"

# --- Temperatures (robust parsing) ---
CPU_TEMP=$(/usr/bin/sensors | awk '
/cpu_thermal/ {found=1}
found && /temp1:/ {print $2; exit}
')

BOARD_TEMP=$(/usr/bin/sensors | awk '
/rp1_adc/ {found=1}
found && /temp1:/ {print $2; exit}
')

# --- Fan ---
FAN_RPM=$(/usr/bin/sensors | awk '/fan1:/ {print $2 " RPM"}')
FAN_PWM=$(/usr/bin/sensors | awk '/pwm1:/ {print $2}')

# --- CPU frequency ---
FREQ=$(awk '{print int($1/1000) " MHz"}' /sys/devices/system/cpu/cpu0/cpufreq/scaling_cur_freq)

# --- Memory & Load ---
RAM_USED=$(/usr/bin/free -m | awk '/Mem:/ {print $3}')
LOAD=$(/usr/bin/uptime | awk -F'load average:' '{print $2}')
LOAD_1M=$(echo "$LOAD" | cut -d',' -f1 | tr -d ' ')

# --- CPU Stress Index ---
# Formula: (load_1m / cores) / (freq_mhz / max_freq)
CORES=4
MAX_FREQ=2500
FREQ_NUM=$(echo "$FREQ" | sed 's/ MHz//')
CPU_STRESS=$(/home/orion/server/venv/bin/python3 -c "
l = float('${LOAD_1M}' or 0)
f = float('${FREQ_NUM}' or 1)
stress = (l / $CORES) / (f / $MAX_FREQ) if f > 0 else 0
print(f'{stress:.3f}')
" 2>/dev/null)
CPU_STRESS=${CPU_STRESS:-0}

# --- Room Sensor (DHT11 via ESP32 MQTT) ---
# Read retained telemetry from ESP32 over MQTT (JSON: {"temp":25.0,"hum":60.0})
DHT_JSON=$(mosquitto_sub -h 192.168.0.103 -t "orion/esp32/telemetry/dht" -C 1 -W 3 2>/dev/null)
ROOM_TEMP=$(echo "$DHT_JSON" | /home/orion/server/venv/bin/python3 -c "import sys,json; d=json.load(sys.stdin); print(d['temp'])" 2>/dev/null)
ROOM_HUM=$(echo "$DHT_JSON" | /home/orion/server/venv/bin/python3 -c "import sys,json; d=json.load(sys.stdin); print(d['hum'])" 2>/dev/null)

# --- [COMMENTED OUT] Original GPIO reading (DHT11 on Pi GPIO 27) ---
# Restore this block if sensor is moved back to the Pi.
# DHT_OUTPUT=$(/home/orion/server/venv/bin/python3 -u -c "
# import board, adafruit_dht, time
# d = adafruit_dht.DHT11(board.D27, use_pulseio=False)
# for _ in range(5):
#     try:
#         t, h = d.temperature, d.humidity
#         if t is not None and h is not None:
#             print(f'{t},{h}')
#             break
#     except: pass
#     time.sleep(2)
# d.exit()
# " 2>/dev/null)
# ROOM_TEMP=$(echo "$DHT_OUTPUT" | cut -d',' -f1)
# ROOM_HUM=$(echo "$DHT_OUTPUT" | cut -d',' -f2)

ROOM_SQL=""
if [ -n "$ROOM_TEMP" ] && [ -n "$ROOM_HUM" ]; then
    ROOM_SQL=", ('$TS','$SOURCE', 'room_temp', '$ROOM_TEMP', 'C'), ('$TS','$SOURCE', 'room_humidity', '$ROOM_HUM', '%')"
fi

# --- Storage (All real disks) ---
# We loop through all real mounts and build SQL inserts and log entry
DISK_SQL=""
DISK_LOG=""
while read -r line; do
    # line format: /dev/sda2 14G 11G 2.6G 81% /mnt
    FILESYSTEM=$(echo "$line" | awk '{print $1}')
    SIZE=$(echo "$line" | awk '{print $2}')
    USED=$(echo "$line" | awk '{print $3}')
    AVAIL=$(echo "$line" | awk '{print $4}')
    PERCENT=$(echo "$line" | awk '{print $5}' | sed 's/%//')
    MOUNT=$(echo "$line" | awk '{print $6}')

    # Create a slug for the name: e.g. disk_usage_mnt
    SLUG=$(echo "$MOUNT" | sed 's|^/|root|; s|^root$|os|; s|/|_|g; s|_root|root|g')
    METRIC_NAME="disk_usage_$SLUG"
    
    DISK_SQL+=", ('$TS','$SOURCE', '$METRIC_NAME', '$PERCENT', '%')"
    DISK_LOG+=" | $SLUG:$PERCENT%"
done < <(df -h | grep '^/dev/')

# --- Log ---
echo "$TS | CPU:$CPU_TEMP | Board:$BOARD_TEMP | Fan:$FAN_RPM ($FAN_PWM) | Freq:$FREQ | RAM:$RAM_USED | Load:$LOAD | Stress:$CPU_STRESS | Room:${ROOM_TEMP}C/${ROOM_HUM}%$DISK_LOG" >> "$LOG_PATH"

# --- DB entry ---
sqlite3 "$DB_PATH" <<EOF
INSERT INTO metrics (ts, source, name, value, unit) VALUES
('$TS','$SOURCE', 'cpu_temp', '${CPU_TEMP%°C}', 'C'),
('$TS','$SOURCE', 'board_temp', '${BOARD_TEMP%°C}', 'C'),
('$TS','$SOURCE', 'fan_rpm', '${FAN_RPM% RPM}', 'RPM'),
('$TS','$SOURCE', 'fan_pwm', '${FAN_PWM%\%}', '%'),
('$TS','$SOURCE', 'cpu_freq', '${FREQ% MHz}', 'MHz'),
('$TS','$SOURCE', 'ram_used', '$RAM_USED', 'MB'),
('$TS','$SOURCE', 'load_1m', '$LOAD_1M', 'load'),
('$TS','$SOURCE', 'cpu_stress', '$CPU_STRESS', 'index')$ROOM_SQL$DISK_SQL;
EOF
