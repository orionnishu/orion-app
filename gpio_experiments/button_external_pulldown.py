#!/usr/bin/env python3

from gpiozero import Button
from signal import pause

BUTTON_PIN = 17  # BCM numbering

print("=" * 50)
print("🔘 Button Test — EXTERNAL PULL-DOWN")
print("=" * 50)
print("Released  -> GPIO LOW")
print("Pressed   -> GPIO HIGH")
print("Ctrl+C to exit\n")

# IMPORTANT:
# pull_up=False means:
# - Do NOT enable internal pull-up
# - GPIO relies ONLY on external resistor
button = Button(
    BUTTON_PIN,
    pull_up=False,
    bounce_time=0.1
)

def pressed():
    print("✅ Button PRESSED (GPIO = HIGH)")

def released():
    print("⬇️ Button released (GPIO = LOW)")

button.when_pressed = pressed
button.when_released = released

pause()
