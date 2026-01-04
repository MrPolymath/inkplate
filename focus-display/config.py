# Focus Display Configuration
# Non-sensitive settings - safe to commit

# Development mode - set to True while iterating on the code
# In dev mode:
#   - Uses light sleep (device stays responsive to serial)
#   - Shorter refresh intervals (30s time updates, 1min API)
#   - Forces "work hours" behavior regardless of actual time
# In prod mode:
#   - Uses deep sleep for battery savings
#   - Normal intervals (1min time updates, 60min API during work hours)
DEV_MODE = True

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
    TIME_UPDATE_INTERVAL = 60              # 1 min in dev (same as prod for minute-precision)
    TIME_UPDATE_INTERVAL_NIGHT = 60        # 1 min in dev (faster than prod for testing)
    API_REFRESH_INTERVAL = 2 * 60          # 2 min in dev (calendar API)
    NTP_SYNC_INTERVAL = 2 * 60             # 2 min in dev
    FULL_REFRESH_INTERVAL = 2 * 60         # 2 min in dev (full screen refresh)
else:
    TIME_UPDATE_INTERVAL = 60              # 1 minute during work hours (time-only, no WiFi)
    TIME_UPDATE_INTERVAL_NIGHT = 60 * 60   # 1 hour at night
    API_REFRESH_INTERVAL = 60 * 60         # 60 minutes (calendar API refresh)
    NTP_SYNC_INTERVAL = 60 * 60            # 60 minutes (NTP time sync)
    FULL_REFRESH_INTERVAL = 30 * 60        # 30 minutes (full screen refresh to clear ghosting)

# Legacy aliases for compatibility
SCREEN_REFRESH_INTERVAL_DAY = TIME_UPDATE_INTERVAL
SCREEN_REFRESH_INTERVAL_NIGHT = TIME_UPDATE_INTERVAL_NIGHT
CALENDAR_REFRESH_INTERVAL = API_REFRESH_INTERVAL

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
