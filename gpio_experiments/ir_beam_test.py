from gpiozero import DigitalInputDevice
from time import sleep

beam = DigitalInputDevice(17, pull_up=False)

print("IR Beam test")

while True:
    print("Value:", beam.value)
    sleep(0.5)
