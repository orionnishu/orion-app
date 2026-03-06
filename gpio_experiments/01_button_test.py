#!/usr/bin/env python3
"""
GPIO Experiment 01: Simple Button Reading
==========================================

WIRING INSTRUCTIONS:
1. Connect GPIO17 (Physical Pin 11) to one corner of your push button
2. Connect GND (Physical Pin 6 or 9) to the DIAGONAL OPPOSITE corner of the button

That's it! Just 2 wires needed.

HOW IT WORKS:
- We use the Pi's internal "pull-up" resistor
- When button is NOT pressed: GPIO17 reads HIGH (1)
- When button IS pressed: GPIO17 connects to GND, reads LOW (0)
- gpiozero handles all this for us!

RUN WITH: python3 01_button_test.py
STOP WITH: Ctrl+C
"""

from gpiozero import Button
from signal import pause
import time

# GPIO17 = Physical Pin 11
BUTTON_PIN = 17

print("=" * 50)
print("🔘 Button Test - GPIO Experiment 01")
print("=" * 50)
print(f"\nUsing GPIO{BUTTON_PIN} (Physical Pin 11)")
print("Make sure your button is wired correctly!")
print("\nWaiting for button presses... (Ctrl+C to exit)\n")

# Create a button object
# pull_up=True means we use internal pull-up resistor
# bounce_time=0.1 prevents multiple triggers from one press
button = Button(BUTTON_PIN, pull_up=True, bounce_time=0.1)

# Counter to track presses
press_count = 0

def on_button_pressed():
    """Called when button is pressed (going from HIGH to LOW)"""
    global press_count
    press_count += 1
    print(f"✅ Button PRESSED! (Count: {press_count})")

def on_button_released():
    """Called when button is released (going from LOW to HIGH)"""
    print("   Button released")

def on_button_held():
    """Called when button is held for more than 1 second"""
    print("   🔥 Button is being HELD!")

# Attach our functions to button events
button.when_pressed = on_button_pressed
button.when_released = on_button_released
button.when_held = on_button_held  # Default hold time is 1 second

# Keep the script running and waiting for events
try:
    pause()  # This keeps the program running
except KeyboardInterrupt:
    print(f"\n\nExiting... Total button presses: {press_count}")
    print("Goodbye! 👋")
