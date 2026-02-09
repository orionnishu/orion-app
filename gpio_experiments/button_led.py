from gpiozero import Button, LED
from signal import pause

# GPIO pins (BCM numbering)
BUTTON_PIN = 17
LED_PIN = 18

button = Button(
    BUTTON_PIN,
    pull_up=False,      # external pull-down resistor
    bounce_time=0.1
)

led = LED(LED_PIN)

print("Button → LED demo")
print("Press button to turn LED ON")

# Event-based control (clean & efficient)
button.when_pressed = led.on
button.when_released = led.off

pause()  # keep program running
