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

print("Button → LED toggle demo")
print("Press button to turn LED ON, press again to turn LED OFF")

led_state = False # OFF initially

def toggle_led():
    """Changes the State using global variable"""
    print(f"✅ Button PRESSED! Toggling LED")
    
    global led_state
    led_state = not led_state

    if led_state:
        led.on()
        print("LED ON")
    else:
        led.off()
        print("LED OFF")

def on_button_held():
    """Called when button is held for more than 1 second"""
    global led_state
    led_state = True
    led.on()
    print("🔥 Button is being HELD! Turning LED ON, press once to turn OFF")


# Event-based control (clean & efficient)
button.when_pressed = toggle_led
button.when_held = on_button_held

pause()  # keep program running
