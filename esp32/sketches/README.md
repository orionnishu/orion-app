# Legacy Arduino IDE sketches

Drop original `.ino` files here to keep the raw source during migration.

Recommended process:
1. Copy original `.ino` files into this folder unchanged.
2. Convert one sketch at a time into `../src/main.cpp`.
3. Build with `pio run` and verify serial logs with `pio device monitor`.
