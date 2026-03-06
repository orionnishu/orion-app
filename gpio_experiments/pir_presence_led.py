from gpiozero import MotionSensor, LED
from time import time, sleep
import subprocess
import os

PIR_PIN = 17
LED_PIN = 18

# Configuration
OFF_DELAY = 40  # seconds after last motion

# Script paths
SCRIPTS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts")
WAKEMYPC_SCRIPT = os.path.join(SCRIPTS_DIR, "wakemypc.sh")
SLEEPMYPC_SCRIPT = os.path.join(SCRIPTS_DIR, "sleepmypc.sh")

pir = MotionSensor(PIR_PIN)
led = LED(LED_PIN)

last_motion_time = None
led_on = False

def run_script(script_path, action_name):
    """Run a shell script and handle errors."""
    try:
        result = subprocess.run([script_path], capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            print(f"  → {action_name} script executed successfully")
        else:
            print(f"  → {action_name} script failed with code {result.returncode}")
            if result.stderr:
                print(f"    Error: {result.stderr.strip()}")
    except subprocess.TimeoutExpired:
        print(f"  → {action_name} script timed out")
    except Exception as e:
        print(f"  → {action_name} script error: {e}")

print("Presence detection started")
print("LED ON while you are present")
print(f"LED OFF after {OFF_DELAY} seconds of no motion")
print(f"Wake script: {WAKEMYPC_SCRIPT}")
print(f"Sleep script: {SLEEPMYPC_SCRIPT}")
print("Waiting for PIR to stabilize (30–60 sec)...")

def on_motion():
    global last_motion_time, led_on
    last_motion_time = time()

    if not led_on:
        led.on()
        led_on = True
        print("Motion detected → LED ON, waking computer")
        run_script(WAKEMYPC_SCRIPT, "wakemypc")
    else:
        print("Motion detected → still present, keeping computer awake")

pir.when_motion = on_motion

while True:
    if led_on and last_motion_time is not None:
        elapsed = time() - last_motion_time

        if elapsed >= OFF_DELAY:
            led.off()
            led_on = False
            last_motion_time = None
            print(f"No motion for {OFF_DELAY}s → LED OFF, putting computer to sleep")
            run_script(SLEEPMYPC_SCRIPT, "sleepmypc")

    sleep(1)
