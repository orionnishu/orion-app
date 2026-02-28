#!/usr/bin/env python3
"""Minimal helper to migrate a single Arduino .ino sketch into PlatformIO src/main.cpp.

Usage:
  python3 tools/migrate_ino.py sketches/MySketch.ino [src/main.cpp]
"""

from __future__ import annotations

import pathlib
import sys


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: python3 tools/migrate_ino.py <input.ino> [output.cpp]")
        return 1

    src_path = pathlib.Path(sys.argv[1]).resolve()
    out_path = (
        pathlib.Path(sys.argv[2]).resolve()
        if len(sys.argv) >= 3
        else pathlib.Path(__file__).resolve().parents[1] / "src" / "main.cpp"
    )

    if not src_path.exists():
        print(f"Input file not found: {src_path}")
        return 2

    content = src_path.read_text(encoding="utf-8")

    if "#include <Arduino.h>" not in content:
        content = "#include <Arduino.h>\n\n" + content

    header = (
        "// Auto-generated from Arduino IDE sketch via tools/migrate_ino.py\n"
        f"// Source: {src_path.name}\n\n"
    )

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(header + content, encoding="utf-8")

    print(f"Wrote: {out_path}")
    print("Next steps:")
    print("  1) pio run")
    print("  2) pio run -t upload")
    print("  3) pio device monitor")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
