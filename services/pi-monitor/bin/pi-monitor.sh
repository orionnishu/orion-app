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
echo "$TS | CPU:$CPU_TEMP | Board:$BOARD_TEMP | Fan:$FAN_RPM ($FAN_PWM) | Freq:$FREQ | RAM:$RAM_USED | Load:$LOAD$DISK_LOG" >> "$LOG_PATH"

# --- DB entry ---
sqlite3 "$DB_PATH" <<EOF
INSERT INTO metrics (ts, source, name, value, unit) VALUES
('$TS','$SOURCE', 'cpu_temp', '${CPU_TEMP%°C}', 'C'),
('$TS','$SOURCE', 'board_temp', '${BOARD_TEMP%°C}', 'C'),
('$TS','$SOURCE', 'fan_rpm', '${FAN_RPM% RPM}', 'RPM'),
('$TS','$SOURCE', 'fan_pwm', '${FAN_PWM%\%}', '%'),
('$TS','$SOURCE', 'cpu_freq', '${FREQ% MHz}', 'MHz'),
('$TS','$SOURCE', 'ram_used', '$RAM_USED', 'MB'),
('$TS','$SOURCE', 'load_1m', '$LOAD_1M', 'load')$DISK_SQL;
EOF
