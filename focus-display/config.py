# Focus Display Configuration
# Non-sensitive settings - safe to commit

# Development mode - set to True while iterating on the code
# In dev mode: uses light sleep, device stays responsive to serial
# In prod mode: uses deep sleep for battery savings
DEV_MODE = False

# Display settings
DISPLAY_WIDTH = 1024
DISPLAY_HEIGHT = 758

# Timezone offsets from UTC (in seconds)
# Note: These are standard time offsets. DST is handled separately.
TIMEZONES = {
    "Barcelona": {
        "name": "Barcelona",
        "tz": "Europe/Madrid",
        "utc_offset": 1,  # CET = UTC+1 (CEST = UTC+2 in summer)
    },
    "New York": {
        "name": "New York",
        "tz": "America/New_York",
        "utc_offset": -5,  # EST = UTC-5 (EDT = UTC-4 in summer)
    },
    "San Francisco": {
        "name": "San Fran",
        "tz": "America/Los_Angeles",
        "utc_offset": -8,  # PST = UTC-8 (PDT = UTC-7 in summer)
    },
}

# Refresh intervals (in seconds)
# Dev mode uses shorter intervals for faster iteration
if DEV_MODE:
    SCREEN_REFRESH_INTERVAL_DAY = 30       # 30s in dev
    SCREEN_REFRESH_INTERVAL_NIGHT = 30     # 30s in dev
else:
    SCREEN_REFRESH_INTERVAL_DAY = 2 * 60   # 2 min during work hours (8am-8pm)
    SCREEN_REFRESH_INTERVAL_NIGHT = 60 * 60  # 1 hour at night

FULL_REFRESH_INTERVAL = 60 if DEV_MODE else 30 * 60       # 1min dev, 30min prod
CALENDAR_REFRESH_INTERVAL = 30 if DEV_MODE else 15 * 60   # 30s dev, 15min prod

# Work hours (for variable refresh rate)
WORK_HOURS_START = 8   # 8 AM
WORK_HOURS_END = 20    # 8 PM

# Evening mode settings
EVENING_MODE_START_HOUR = 19  # 7 PM local time

# Google Calendar API
CALENDAR_API_BASE = "https://www.googleapis.com/calendar/v3"
CALENDAR_SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]

# Display layout positions (for 1024x758 screen)
# Using larger fonts: 32px small, 48px medium, 72-80px large
LAYOUT = {
    # Left column - world clocks
    "clocks_x": 30,
    "clock_1_y": 80,    # Barcelona
    "clock_2_y": 300,   # New York
    "clock_3_y": 520,   # San Francisco

    # Vertical divider line - full height
    "divider_x": 340,
    "divider_top": 0,
    "divider_bottom": 758,

    # Right area - focus message
    "focus_x": 380,
    "focus_message_y": 150,
    "focus_time_y": 320,
    "focus_next_y": 560,
}
