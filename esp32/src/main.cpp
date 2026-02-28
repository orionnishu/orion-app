#include <Arduino.h>

// Starter sketch for ESP32 DevKit in PlatformIO.
// To migrate from Arduino IDE:
// 1) Copy your .ino logic into setup() and loop().
// 2) Move helper functions above loop() or add forward declarations.
// 3) Add any needed #include lines at top of this file.

void setup() {
  Serial.begin(115200);
  delay(500);

  Serial.println();
  Serial.println("ORION ESP32 project booted.");
}

void loop() {
  static uint32_t last = 0;
  const uint32_t now = millis();

  if (now - last >= 1000) {
    last = now;
    Serial.printf("uptime_ms=%lu\n", static_cast<unsigned long>(now));
  }
}
