#!/bin/bash

DB_PATH="$HOME/server/services/pi-monitor/db/pi-monitor.db"
LOG_PATH="$HOME/server/services/pi-monitor/logs/pi-monitor.log"

TS=$(/bin/date "+%Y-%m-%d %H:%M:%S" )

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

# --- CPU frequency (sysfs, Ubuntu-correct) ---
FREQ=$(awk '{print int($1/1000) " MHz"}' /sys/devices/system/cpu/cpu0/cpufreq/scaling_cur_freq)

# --- Memory & Load ---
RAM_USED=$(/usr/bin/free -m | awk '/Mem:/ {print $3}')
LOAD=$(/usr/bin/uptime | awk -F'load average:' '{print $2}')

# --- Log ---
echo "$TS | CPU:$CPU_TEMP | Board:$BOARD_TEMP | Fan:$FAN_RPM ($FAN_PWM) | Freq:$FREQ | RAM:$RAM_USED | Load:$LOAD" >> "$LOG_PATH"

# --- DB entry ---
#DB="/home/orion/Documents/projects/pi-monitor/pi-monitor.db"
SOURCE="pi-monitor"

sqlite3 "$DB_PATH" <<EOF
INSERT INTO metrics (ts,source, name, value, unit) VALUES
('$TS','$SOURCE', 'cpu_temp', '${CPU_TEMP%°C}', 'C'),
('$TS','$SOURCE', 'board_temp', '${BOARD_TEMP%°C}', 'C'),
('$TS','$SOURCE', 'fan_rpm', '${FAN_RPM% RPM}', 'RPM'),
('$TS','$SOURCE', 'fan_pwm', '${FAN_PWM%\%}', '%'),
('$TS','$SOURCE', 'cpu_freq', '${FREQ% MHz}', 'MHz'),
('$TS','$SOURCE', 'ram_used', '$RAM_USED', 'MB'),
('$TS','$SOURCE', 'load_1m', '$(echo "$LOAD" | cut -d',' -f1)', 'load');
EOF

