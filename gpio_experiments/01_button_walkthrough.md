# GPIO Button Reading - Complete Walkthrough

**Date**: February 7, 2026  
**Goal**: Read a push button input on Raspberry Pi 5 using GPIO

---

## What We Built

A simple circuit that detects button presses using:
- **GPIO17** (Physical Pin 11) as input
- **GND** (Physical Pin 6) as ground reference
- **Internal pull-up resistor** (no external resistor needed!)

---

## Hardware Concepts Explained

### The Push Button (4-Pin)

```
  Pin 1 ────[   ]──── Pin 2     ← Connected internally
             │ │
  Pin 3 ────[   ]──── Pin 4     ← Connected internally
```

- Pins 1-2 are always connected (one side of button)
- Pins 3-4 are always connected (other side of button)  
- When **pressed**: All 4 pins connect together
- For our circuit: We only need **2 pins** (diagonal corners)

### Pull-Up Resistor (Why We Don't Need an External One)

**The Problem**: When a button isn't pressed, the GPIO pin is "floating" - not connected to anything. This causes random readings (sometimes 0, sometimes 1).

**The Solution**: A "pull-up" resistor connects the pin to 3.3V, giving it a default HIGH (1) state.

**Pi 5 Advantage**: The Pi has internal pull-up resistors we can enable in software!

```
            3.3V
              │
              ▼
         [Internal Pull-Up]  ← Enabled with: Button(pin, pull_up=True)
              │
              ├──────────────→ GPIO17 reads HIGH (1) when not pressed
              │
           [BUTTON]
              │
              ▼
             GND              → GPIO17 reads LOW (0) when pressed
```

### Breadboard Wiring

```
RASPBERRY PI 5                          BREADBOARD
                                    
     Pin 6 (GND) ──────────────────→ Row 6, Column A
                                            │
     Pin 11 (GPIO17) ──────────────→ Row 5, Column A
                                            │
                              A   B   C   D   E │ F   G   H
                            ┌────────────────────────────────┐
                         5  │ 🔵──────────────🔘═══🔘        │
                            │                  (button)      │
                         6  │ ⚫──────────────🔘═══🔘        │
                            └────────────────────────────────┘
```

---

## Software Concepts Explained

### Library: gpiozero

We used `gpiozero` - a beginner-friendly Python library that abstracts GPIO complexity:

```python
from gpiozero import Button

# Create button on GPIO17 with internal pull-up enabled
button = Button(17, pull_up=True, bounce_time=0.1)
```

**Key Parameters**:
- `17` → GPIO pin number (BCM numbering, not physical pin)
- `pull_up=True` → Enable internal pull-up resistor
- `bounce_time=0.1` → Ignore multiple triggers within 100ms (debouncing)

### Event-Based vs. Polling

**Polling** (our diagnostic script):
```python
while True:
    if button.is_pressed:
        print("Pressed!")
    time.sleep(0.3)
```
- Continuously checks the button state
- Can miss fast presses if sleep is too long
- Uses more CPU

**Event-Based** (our main script):
```python
button.when_pressed = on_button_pressed
button.when_released = on_button_released
pause()  # Keep program running
```
- Callbacks fire instantly when button state changes
- More efficient, never misses a press
- Preferred for real applications

### Pi 5 Specifics

Pi 5 uses a different GPIO chip than older Pis:
- Old Pis: `RPi.GPIO` library
- Pi 5: Requires `lgpio` backend (gpiozero uses this automatically)

---

## Issues We Encountered & Solutions

### Issue 1: "GPIO busy" Error

```
lgpio.error: 'GPIO busy'
```

**What Happened**: The previous Python script was terminated but didn't properly release the GPIO pin. The operating system still thought the pin was in use.

**Why It Happens**: 
- When a script using GPIO is killed abruptly (Ctrl+C, timeout, or forced termination)
- The `lgpio` library doesn't always get a chance to cleanup
- The GPIO pin remains "claimed" by the dead process

**Solution**: Kill all Python processes and wait for the OS to release the pins:
```bash
sudo pkill -9 -f python3
sleep 2
```

**Prevention**: Always use try/except with cleanup, or let `gpiozero` handle it (which we did).

---

### Issue 2: Script Not Detecting Presses Initially

**What Happened**: The first time we ran the button test, it showed 0 button presses even though you were pressing something.

**Why It Happened**: The button wasn't physically wired to the Pi yet! You were pressing a button that wasn't connected.

**Lesson**: Always verify your wiring before assuming software issues.

---

### Issue 3: Confusing Pin Numbering

**The Problem**: Raspberry Pi has multiple pin numbering schemes:

| Scheme | GPIO17 Pin |
|--------|------------|
| BCM (Broadcom) | 17 |
| Physical/Board | 11 |
| WiringPi | 0 |

**Our Solution**: We used BCM numbering in code (`Button(17)`) but referenced Physical pin numbers in wiring instructions (Pin 11) since that's what you see on the board.

**Reference Diagram**:
```
                3.3V  (1)  (2)  5V
               GPIO2  (3)  (4)  5V
               GPIO3  (5)  (6)  GND  ← Physical Pin 6
               GPIO4  (7)  (8)  GPIO14
                 GND  (9)  (10) GPIO15
             GPIO17 (11)  (12) GPIO18
                        ↑
                   Physical Pin 11 = GPIO17 in code
```

---

## Scripts We Created

### [00_pin_diagnostic.py](file:///home/orion/server/gpio_experiments/00_pin_diagnostic.py)

**Purpose**: Debug wiring issues by continuously showing the pin state.

**Key Features**:
- Polls the GPIO every 0.3 seconds
- Shows `PRESSED (0)` or `NOT PRESSED (1)`
- Useful for verifying wiring before running the main script

---

### [01_button_test.py](file:///home/orion/server/gpio_experiments/01_button_test.py)

**Purpose**: Demonstrate event-based button detection.

**Key Features**:
- `when_pressed` callback → Fires when button goes from HIGH to LOW
- `when_released` callback → Fires when button goes from LOW to HIGH
- `when_held` callback → Fires when button held for 1+ second
- Tracks total press count

---

## Key Takeaways

1. **Minimal wiring**: Just 2 wires needed (GPIO + GND) thanks to internal pull-up
2. **BCM vs Physical**: Always be clear which numbering you're using
3. **GPIO cleanup matters**: Kill stale processes if you get "GPIO busy"
4. **Event-based is better**: Use callbacks instead of polling for real apps
5. **Test incrementally**: Start with diagnostic scripts before complex logic

---

## Next Steps

Now that you understand button input, you could explore:
- **LED Output**: Light up an LED when button is pressed
- **Multiple Inputs**: Add more buttons on different GPIO pins  
- **Web Integration**: Show button state on your Orion dashboard
- **Sensors**: Read analog sensors (requires ADC) or digital sensors
