from gpiozero import MotionSensor, LED
from signal import pause

PIR_PIN = 17
LED_PIN = 18

pir = MotionSensor(PIR_PIN)
led = LED(LED_PIN)

print("PIR motion detection started")
print("Waiting for PIR to stabilize (30–60 seconds)...")

def motion_detected():
    print("Motion detected")
    led.on()

def motion_stopped():
    print("No motion")
    led.off()

pir.when_motion = motion_detected
pir.when_no_motion = motion_stopped

pause()
