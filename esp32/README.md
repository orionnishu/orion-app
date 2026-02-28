# ESP32 workspace (PlatformIO)

This folder lets you keep ESP32 firmware in the same ORION repository while using PlatformIO in VS Code.

## First-time setup

1. Open this repository in VS Code.
2. Open the `esp32/` folder in PlatformIO Home (or open `esp32/` as workspace root).
3. Connect your ESP32 DevKit board by USB.
4. Build:
   ```bash
   pio run
   ```
5. Upload:
   ```bash
   pio run -t upload
   ```
6. Monitor serial output:
   ```bash
   pio device monitor
   ```

## Migrate an Arduino IDE sketch

1. Save your original `.ino` in `sketches/`.
2. Convert with helper script:
   ```bash
   python3 tools/migrate_ino.py sketches/YourSketch.ino
   ```
3. Build and fix compile issues (typically missing includes, ordering, or library deps).
4. Add libraries in `platformio.ini` under `lib_deps`.

## Notes

- PlatformIO project config is in `platformio.ini`.
- Build output is generated under `.pio/` and should not be committed.
- Keep one active firmware entrypoint in `src/main.cpp`.
