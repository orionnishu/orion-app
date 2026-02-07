#!/usr/bin/env python3
"""
GPIO Diagnostic - Continuously reads the pin state
Helps debug wiring issues!
"""

from gpiozero import Button
import time

BUTTON_PIN = 17

print("🔍 GPIO17 Pin State Monitor")
print("="*40)
print("Watching the pin state every 0.3 seconds...")
print("If wired correctly:")
print("  - Should show '1' (HIGH) when NOT pressed")
print("  - Should show '0' (LOW) when PRESSED")
print("\nPress Ctrl+C to exit\n")

button = Button(BUTTON_PIN, pull_up=True)

try:
    while True:
        state = "PRESSED (0)" if button.is_pressed else "NOT PRESSED (1)"
        print(f"GPIO17 state: {state}", end='\r')
        time.sleep(0.3)
except KeyboardInterrupt:
    print("\n\nDone!")
