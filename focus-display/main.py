# Focus Display - Main Entry Point
# Inkplate 6PLUS focus timer with Google Calendar integration

import network
import ntptime
import machine
import time
import esp32
from machine import Pin
import config

# Wake button GPIO (Inkplate 6PLUS wake button)
WAKE_BUTTON_PIN = 36

# Import after config to avoid issues
from display import FocusDisplay
from calendar_sync import CalendarSync

try:
    import secrets
except ImportError:
    print("ERROR: secrets.py not found. Copy secrets.py.example to secrets.py and configure it.")
    raise


def connect_wifi():
    """Connect to WiFi network."""
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)

    if wlan.isconnected():
        return True

    print(f"Connecting to WiFi: {secrets.WIFI_SSID}")
    wlan.connect(secrets.WIFI_SSID, secrets.WIFI_PASSWORD)

    # Wait for connection (max 30 seconds)
    timeout = 30
    while not wlan.isconnected() and timeout > 0:
        time.sleep(1)
        timeout -= 1

    if wlan.isconnected():
        print(f"Connected! IP: {wlan.ifconfig()[0]}")
        return True
    else:
        print("WiFi connection failed")
        display.show_error("WiFi connection failed")
        return False


def sync_time():
    """Sync time with NTP server."""
    try:
        ntptime.settime()
        print("Time synced with NTP")
        return True
    except Exception as e:
        print(f"NTP sync failed: {e}")
        return False


def get_local_time_with_offset(utc_time, offset_hours):
    """
    Apply timezone offset to UTC time.
    Returns (hour, minute) in local time.

    Note: This is a simplified version that doesn't handle DST.
    For production, you'd want a proper timezone library.
    """
    year, month, day, hour, minute, second, weekday, yearday = utc_time
    hour = (hour + offset_hours) % 24
    return hour, minute


def is_dst_europe(month, day, weekday):
    """
    Check if date is in European DST (last Sunday of March to last Sunday of October).
    Simplified check - not perfectly accurate for edge cases.
    """
    if month < 3 or month > 10:
        return False
    if month > 3 and month < 10:
        return True
    # March or October - check if past last Sunday
    # weekday: 0=Monday, 6=Sunday
    last_sunday = day - ((weekday + 1) % 7)
    if month == 3:
        return day >= (31 - 6 + (weekday + 1) % 7)  # Rough approximation
    return day < (31 - 6 + (weekday + 1) % 7)  # October


def is_dst_us(month, day, weekday):
    """
    Check if date is in US DST (2nd Sunday of March to 1st Sunday of November).
    Simplified check.
    """
    if month < 3 or month > 11:
        return False
    if month > 3 and month < 11:
        return True
    # March: after 2nd Sunday, November: before 1st Sunday
    return month == 3 and day > 14 or month == 11 and day < 8


def get_world_times(utc_time):
    """Get times for all three cities."""
    year, month, day, hour, minute, second, weekday, yearday = utc_time

    # Calculate DST offsets
    europe_dst = is_dst_europe(month, day, weekday)
    us_dst = is_dst_us(month, day, weekday)

    # Barcelona: UTC+1 (CET) or UTC+2 (CEST)
    bcn_offset = 2 if europe_dst else 1
    bcn_hour = (hour + bcn_offset) % 24

    # New York: UTC-5 (EST) or UTC-4 (EDT)
    ny_offset = -4 if us_dst else -5
    ny_hour = (hour + ny_offset) % 24

    # San Francisco: UTC-8 (PST) or UTC-7 (PDT)
    sf_offset = -7 if us_dst else -8
    sf_hour = (hour + sf_offset) % 24

    return {
        "barcelona": (bcn_hour, minute),
        "new_york": (ny_hour, minute),
        "san_francisco": (sf_hour, minute),
    }


def check_evening_mode(local_hour, minutes_until_next):
    """
    Check if we should show evening mode.
    Evening mode: after 7 PM AND no meetings until tomorrow.
    """
    is_evening = local_hour >= config.EVENING_MODE_START_HOUR

    # No upcoming meeting, or next meeting is > 12 hours away (tomorrow)
    no_meetings_today = minutes_until_next is None or minutes_until_next > 12 * 60

    return is_evening and no_meetings_today


def is_weekend(weekday):
    """Check if it's a weekend. weekday: 0=Monday, 6=Sunday."""
    return weekday >= 5  # Saturday=5, Sunday=6


def sleep_until_refresh(seconds):
    """Sleep until next refresh. Uses light sleep in dev mode."""
    if config.DEV_MODE:
        print(f"DEV MODE: light sleep for {seconds} seconds (device stays responsive)...")
        time.sleep(seconds)
    else:
        print(f"Entering deep sleep for {seconds} seconds...")
        # Configure wake button to also wake from deep sleep
        wake_pin = Pin(WAKE_BUTTON_PIN, Pin.IN)
        esp32.wake_on_ext0(pin=wake_pin, level=esp32.WAKEUP_ALL_LOW)
        machine.deepsleep(seconds * 1000)


def main():
    """Main application loop."""
    print("Focus Display starting...")

    # Initialize display
    display = FocusDisplay()

    # Connect to WiFi (silently - keep old display visible)
    if not connect_wifi():
        display.show_error("WiFi failed")
        sleep_until_refresh(60)  # Retry in 1 minute
        return

    # Sync time
    if not sync_time():
        display.show_error("Time sync failed")
        sleep_until_refresh(60)
        return

    # Initialize calendar
    calendar = CalendarSync(
        client_id=secrets.GOOGLE_CLIENT_ID,
        client_secret=secrets.GOOGLE_CLIENT_SECRET,
        refresh_token=secrets.GOOGLE_REFRESH_TOKEN,
        calendar_id=secrets.CALENDAR_ID,
    )

    # Fetch calendar events
    utc_time = time.gmtime()
    events = calendar.get_upcoming_events(utc_time)

    if events is None:
        display.show_error("Calendar sync failed")
        sleep_until_refresh(60)
        return

    # Get next meeting
    minutes_until_next, next_title, next_time_str = calendar.get_next_meeting(events, utc_time)

    # Get world times (need local hour for refresh interval calculation)
    times = get_world_times(utc_time)
    local_hour = times["barcelona"][0]
    weekday = utc_time[6]  # 0=Monday, 6=Sunday

    # Determine current refresh interval based on time of day and weekend
    if is_weekend(weekday):
        current_refresh_interval = config.SCREEN_REFRESH_INTERVAL_NIGHT  # 1 hour on weekends
    elif config.WORK_HOURS_START <= local_hour < config.WORK_HOURS_END:
        current_refresh_interval = config.SCREEN_REFRESH_INTERVAL_DAY
    else:
        current_refresh_interval = config.SCREEN_REFRESH_INTERVAL_NIGHT

    # Round down to account for refresh interval - ensures we never show stale "you have time"
    # when a meeting is actually imminent
    if minutes_until_next is not None:
        refresh_minutes = current_refresh_interval // 60
        minutes_until_next = max(0, minutes_until_next - refresh_minutes)

    # Check evening mode
    local_hour = times["barcelona"][0]
    is_evening = check_evening_mode(local_hour, minutes_until_next)

    # Render display
    display.render(
        times=times,
        is_evening_mode=is_evening,
        minutes_until_next=minutes_until_next,
        next_meeting_title=next_title,
        next_meeting_time=next_time_str,
        force_full=True,  # First render is always full refresh
    )

    print(f"Display updated. Next meeting in {minutes_until_next} minutes." if minutes_until_next else "No upcoming meetings.")

    # Determine refresh interval based on time of day and weekend
    if is_weekend(weekday):
        refresh_interval = config.SCREEN_REFRESH_INTERVAL_NIGHT
        print(f"Weekend mode - refreshing in {refresh_interval // 60} minutes (press WAKE for manual refresh)")
    elif config.WORK_HOURS_START <= local_hour < config.WORK_HOURS_END:
        refresh_interval = config.SCREEN_REFRESH_INTERVAL_DAY
        print(f"Work hours - refreshing in {refresh_interval // 60} minutes (press WAKE for manual refresh)")
    else:
        refresh_interval = config.SCREEN_REFRESH_INTERVAL_NIGHT
        print(f"Night mode - refreshing in {refresh_interval // 60} minutes (press WAKE for manual refresh)")

    # Sleep until next refresh (wake button also triggers refresh)
    sleep_until_refresh(refresh_interval)


# Run main on boot
if __name__ == "__main__":
    main()
