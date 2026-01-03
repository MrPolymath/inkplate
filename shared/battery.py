import FreeSans_24px

def get_battery_percentage(display):
    """Read battery and return percentage (0-100)."""
    voltage = display.readBattery()
    if voltage <= 3.0:
        return 0
    elif voltage >= 4.2:
        return 100
    return round(((voltage - 3.0) / 1.2) * 100)

def draw_battery_indicator(display, x=940, y=30):
    """Draw battery percentage at given position (default: top right)."""
    pct = get_battery_percentage(display)
    display.setFont(FreeSans_24px)
    display.printText(x, y, f"{pct}%")
