# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Monorepo for Inkplate 6PLUS e-ink display projects. Each project lives in its own folder.

## Hardware

- **Device**: Inkplate 6PLUS (1024×758 resolution, touchscreen, front light)
- **Serial port**: `/dev/cu.usbserial-110`

## Development

- Platform: macOS
- Language: Python/MicroPython for device interaction
- Reference: https://github.com/SolderedElectronics/Inkplate-micropython

## Important: Driver

The Inkplate 6PLUS uses the **Inkplate6FLICK** driver (not Inkplate6):
```python
from inkplate6FLICK import Inkplate
```

## Common Commands

```bash
# Connect and run Python code
mpremote connect /dev/cu.usbserial-110 exec "print('hello')"

# Open interactive REPL
mpremote connect /dev/cu.usbserial-110 repl

# Run a local Python file on device
mpremote connect /dev/cu.usbserial-110 run script.py

# Copy file to device
mpremote connect /dev/cu.usbserial-110 cp local.py :main.py
```

## Basic Display Example

```python
from inkplate6FLICK import Inkplate

display = Inkplate(Inkplate.INKPLATE_1BIT)
display.begin()
display.clearDisplay()
display.printText(100, 100, "Hello!")
display.display()
```

## Fonts

**Don't scale the default font** - it gets blurry. Use pre-rendered fonts at the size you need:

```python
from inkplate6FLICK import Inkplate
import FreeSans_48px  # or FreeSans_24px, FreeSans_32px, FreeSansBold_48px

display = Inkplate(Inkplate.INKPLATE_1BIT)
display.begin()
display.setFont(FreeSans_48px)
display.printText(50, 100, "Crisp large text!")
display.display()
```

**Fonts installed on device** (`/lib/`):
- `FreeSans_24px` - body text
- `FreeSans_32px` - medium headers
- `FreeSans_48px` - large text
- `FreeSansBold_48px` - bold large text

**More fonts available**: https://github.com/SolderedElectronics/Inkplate-micropython/tree/master/Fonts

## Shared Modules

Reusable helpers in `shared/` (also on device at `/lib/shared/`):

### Battery Indicator
```python
from shared.battery import draw_battery_indicator

# Draws "XX%" in top right corner
draw_battery_indicator(display)

# Or get just the percentage
from shared.battery import get_battery_percentage
pct = get_battery_percentage(display)  # returns 0-100
```

## Git Workflow

**Important**: Multiple agents share this folder, so don't use branches.

1. **Commit directly to main** - no branches (they conflict with parallel agents)
2. **Only commit files you worked on** - don't stage unrelated changes
3. **Make small, frequent commits** to track progress
4. **Keep commit messages short** - one clear line, no co-author tags
