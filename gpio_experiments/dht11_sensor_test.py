import time
import board
import adafruit_dht

# GPIO27
dht = adafruit_dht.DHT11(board.D27)

print("Reading DHT11...")

while True:
    try:
        temp = dht.temperature
        hum = dht.humidity

        if temp is not None and hum is not None:
            print(f"Temp: {temp}°C | Humidity: {hum}%")
        else:
            print("Sensor returned None")

    except RuntimeError:
        # DHT11 is slow and sometimes flaky
        print("Retrying...")

    time.sleep(2)
