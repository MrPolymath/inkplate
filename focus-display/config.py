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

# Three-column layout (for 1024x758 screen)
# Column 1: Clocks (~150px) | Column 2: Focus (~450px) | Column 3: Timeline (~400px)
LAYOUT = {
    # Left column - compact world clocks
    "clocks_x": 25,
    "clocks_width": 140,
    "clock_1_y": 120,    # BCN
    "clock_2_y": 330,    # NY
    "clock_3_y": 540,    # SF

    # First divider (between clocks and focus)
    "divider1_x": 175,

    # Middle column - focus info
    "focus_x": 195,
    "focus_width": 420,
    "focus_message_y": 180,
    "focus_time_y": 320,
    "focus_next_y": 520,

    # Second divider (between focus and timeline)
    "divider2_x": 620,

    # Right column - timeline
    "timeline_x": 640,
    "timeline_width": 370,
    "timeline_hour_x": 650,      # Hour labels
    "timeline_bar_x": 710,       # Start of meeting bars
    "timeline_bar_width": 280,   # Width for meeting bars
    "timeline_start_hour": 8,
    "timeline_end_hour": 20,
    "timeline_top_y": 60,
    "timeline_row_height": 55,   # ~55px per hour for 12 hours

    # Battery indicator
    "battery_x": 940,
    "battery_y": 30,
}
