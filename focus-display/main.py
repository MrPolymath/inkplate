# Focus Display - Main Entry Point
# Inkplate 6PLUS focus timer with Google Calendar integration
# Unified three-column layout: Clocks | Focus | Timeline
#
# Energy-optimized dual update system:
# - Time-only updates every minute (no WiFi)
# - API updates every hour (with WiFi)

import network
import ntptime
import machine
import time
import esp32
import json
from machine import Pin, RTC
import config

# Wake button GPIO (Inkplate 6PLUS wake button)
WAKE_BUTTON_PIN = 36

# RTC memory magic number to detect valid cache
CACHE_MAGIC = 0xF0C5  # "FOCS" for Focus

# Import after config to avoid issues
from display import FocusDisplay
from calendar_sync import CalendarSync

try:
    import secrets
except ImportError:
    print("ERROR: secrets.py not found. Copy secrets.py.example to secrets.py and configure it.")
    raise


# =============================================================================
# RTC Memory Cache Functions
# =============================================================================

def save_to_rtc_memory(data):
    """Save cache data to RTC memory (survives deep sleep)."""
    try:
        # Add magic number to validate cache
        data['magic'] = CACHE_MAGIC
        json_str = json.dumps(data)
        json_bytes = json_str.encode('utf-8')

        # RTC memory can hold up to 8KB
        if len(json_bytes) > 8000:
            print(f"WARNING: Cache too large ({len(json_bytes)} bytes), truncating events")
            # Truncate events list if too large
            if 'events' in data and len(data['events']) > 3:
                data['events'] = data['events'][:3]
                json_str = json.dumps(data)
                json_bytes = json_str.encode('utf-8')

        rtc = RTC()
        rtc.memory(json_bytes)
        print(f"Saved {len(json_bytes)} bytes to RTC memory")
        return True
    except Exception as e:
        print(f"Failed to save to RTC memory: {e}")
        return False


def load_from_rtc_memory():
    """Load cache data from RTC memory. Returns None if invalid/empty."""
    try:
        rtc = RTC()
        json_bytes = rtc.memory()

        if not json_bytes or len(json_bytes) == 0:
            print("RTC memory is empty")
            return None

        json_str = json_bytes.decode('utf-8')
        data = json.loads(json_str)

        # Validate magic number
        if data.get('magic') != CACHE_MAGIC:
            print("RTC memory has invalid magic number")
            return None

        print(f"Loaded cache from RTC memory ({len(json_bytes)} bytes)")
        return data
    except Exception as e:
        print(f"Failed to load from RTC memory: {e}")
        return None


# =============================================================================
# Time Functions
# =============================================================================

def get_rtc_time():
    """Get current time from ESP32 RTC. Returns tuple (year, month, day, hour, minute, second, weekday)."""
    rtc = RTC()
    dt = rtc.datetime()
    # RTC datetime format: (year, month, day, weekday, hour, minute, second, subsecond)
    year, month, day, weekday, hour, minute, second, _ = dt
    return (year, month, day, hour, minute, second, weekday)


def calculate_minutes_elapsed(last_sync_time, current_time):
    """Calculate minutes elapsed between two time tuples."""
    if last_sync_time is None:
        return float('inf')

    # Extract components
    ly, lm, ld, lh, lmin = last_sync_time[:5]
    cy, cm, cd, ch, cmin = current_time[:5]

    # Simple calculation assuming same day (handles most cases)
    if (cy, cm, cd) == (ly, lm, ld):
        return (ch * 60 + cmin) - (lh * 60 + lmin)

    # Different day - force refresh
    return float('inf')


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
        return False


def sync_time():
    """Sync time with NTP server and update RTC."""
    try:
        ntptime.settime()
        print("Time synced with NTP")
        return True
    except Exception as e:
        print(f"NTP sync failed: {e}")
        return False


def is_dst_europe(month, day, weekday):
    """Check if date is in European DST (last Sunday of March to last Sunday of October)."""
    if month < 3 or month > 10:
        return False
    if month > 3 and month < 10:
        return True
    # March or October - rough approximation
    if month == 3:
        return day >= (31 - 6 + (weekday + 1) % 7)
    return day < (31 - 6 + (weekday + 1) % 7)


def is_dst_us(month, day, weekday):
    """Check if date is in US DST (2nd Sunday of March to 1st Sunday of November)."""
    if month < 3 or month > 11:
        return False
    if month > 3 and month < 11:
        return True
    return month == 3 and day > 14 or month == 11 and day < 8


def get_world_times_from_rtc(rtc_time):
    """Get times for all three cities from RTC time."""
    year, month, day, hour, minute, second, weekday = rtc_time

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
    """Check if we should show evening mode (after 7 PM with no meetings today)."""
    is_evening = local_hour >= config.EVENING_MODE_START_HOUR
    no_meetings_today = minutes_until_next is None or minutes_until_next > 12 * 60
    return is_evening and no_meetings_today


def is_weekend(weekday):
    """Check if it's a weekend. weekday: 0=Monday, 6=Sunday."""
    return weekday >= 5


def is_work_hours(local_hour, weekday):
    """Check if we're in work hours (8am-8pm on weekdays).

    In DEV_MODE, always returns True to test time-only updates.
    """
    if config.DEV_MODE:
        return True  # Force work hours behavior for testing
    if is_weekend(weekday):
        return False
    return config.WORK_HOURS_START <= local_hour < config.WORK_HOURS_END


# =============================================================================
# Wake Cause Detection
# =============================================================================

def get_wake_cause():
    """Determine why the device woke up.

    Returns:
        'button' - User pressed wake button
        'timer' - Timer expired (normal wake)
        'reset' - Device was reset/powered on
    """
    reset_cause = machine.reset_cause()
    wake_reason = machine.wake_reason() if hasattr(machine, 'wake_reason') else None

    print(f"Reset cause: {reset_cause}, Wake reason: {wake_reason}")

    # DEEPSLEEP_RESET means we woke from deep sleep
    if reset_cause == machine.DEEPSLEEP_RESET:
        # Check if it was button or timer
        if wake_reason == machine.PIN_WAKE:
            print("Woke from button press")
            return 'button'
        else:
            print("Woke from timer")
            return 'timer'
    else:
        print("Fresh boot (reset/power on)")
        return 'reset'


# =============================================================================
# Sleep Functions
# =============================================================================

def calculate_seconds_until_next_minute():
    """Calculate seconds until the next minute boundary."""
    rtc = RTC()
    dt = rtc.datetime()
    current_seconds = dt[6]  # seconds field
    seconds_until_next = 60 - current_seconds
    if seconds_until_next == 60:
        seconds_until_next = 0
    return seconds_until_next


def sleep_until_refresh(seconds, sync_to_minute=False):
    """Sleep until next refresh. Uses light sleep in dev mode.

    Args:
        seconds: Base sleep duration
        sync_to_minute: If True, adjust sleep to wake at minute boundary
    """
    if sync_to_minute:
        # Calculate time until next minute boundary
        seconds_until_minute = calculate_seconds_until_next_minute()
        if seconds_until_minute > 0 and seconds_until_minute < seconds:
            # Sleep until next minute, then continue with regular interval
            actual_sleep = seconds_until_minute
            print(f"Syncing to minute boundary: sleeping {actual_sleep}s (instead of {seconds}s)")
        else:
            actual_sleep = seconds
    else:
        actual_sleep = seconds

    if config.DEV_MODE:
        print(f"DEV MODE: light sleep for {actual_sleep} seconds...")
        time.sleep(actual_sleep)
    else:
        print(f"Entering deep sleep for {actual_sleep} seconds...")
        wake_pin = Pin(WAKE_BUTTON_PIN, Pin.IN)
        esp32.wake_on_ext0(pin=wake_pin, level=esp32.WAKEUP_ALL_LOW)
        machine.deepsleep(actual_sleep * 1000)


# =============================================================================
# Main Application
# =============================================================================

def do_api_refresh(display, rtc_time):
    """Perform full API refresh: WiFi + NTP + Calendar API.

    Returns:
        tuple: (success, cache_data)
    """
    print("=== Full API Refresh ===")

    # Connect to WiFi
    if not connect_wifi():
        return False, None

    # Sync time with NTP
    if not sync_time():
        # Continue anyway with RTC time, but note it may drift
        print("Continuing with RTC time (may be inaccurate)")

    # Re-read RTC time after NTP sync
    rtc_time = get_rtc_time()
    utc_time = time.gmtime()

    # Initialize calendar
    calendar = CalendarSync(
        client_id=secrets.GOOGLE_CLIENT_ID,
        client_secret=secrets.GOOGLE_CLIENT_SECRET,
        refresh_token=secrets.GOOGLE_REFRESH_TOKEN,
        calendar_id=secrets.CALENDAR_ID,
    )

    # Fetch calendar events
    events = calendar.get_upcoming_events(utc_time)

    if events is None:
        print("Calendar sync failed")
        return False, None

    # Get next meeting for focus view
    result = calendar.get_next_meeting(events, utc_time)
    minutes_until_next, next_title, next_time_str = result[0], result[1], result[2]

    # Get today's events for timeline
    todays_events = calendar.get_todays_events(events, utc_time)

    # Get world times
    times = get_world_times_from_rtc(rtc_time)
    local_hour, local_minute = times["barcelona"]
    weekday = rtc_time[6]

    # Build cache data
    # Store original minutes_until_next so we can recalculate on each wake
    cache_data = {
        'events': todays_events,
        'minutes_until_next_original': minutes_until_next,  # Original value at sync time
        'next_title': next_title,
        'next_time_str': next_time_str,
        'last_api_sync': rtc_time[:5],  # (year, month, day, hour, minute)
        'last_ntp_sync': rtc_time[:5],
    }

    # Save to RTC memory
    save_to_rtc_memory(cache_data)

    return True, cache_data


def calculate_current_minutes_until_next(cache_data, minutes_elapsed):
    """Calculate current minutes until next meeting based on elapsed time.

    Args:
        cache_data: Cached data from RTC memory
        minutes_elapsed: Minutes since last API sync

    Returns:
        Current minutes until next meeting (or None if no meeting)
    """
    original = cache_data.get('minutes_until_next_original')
    if original is None:
        return None
    return max(0, original - minutes_elapsed)


def do_time_only_update(cache_data, minutes_elapsed, current_hour, current_minute):
    """Update time-related data without WiFi.

    Args:
        cache_data: Cached data from RTC memory
        minutes_elapsed: Minutes since last API sync
        current_hour: Current hour (local time)
        current_minute: Current minute

    Returns:
        Current minutes_until_next (calculated fresh from original)
    """
    print(f"=== Time-Only Update (no WiFi, {minutes_elapsed} min since API) ===")

    # Calculate current minutes until next (fresh calculation each time)
    minutes_until_next = calculate_current_minutes_until_next(cache_data, minutes_elapsed)

    # Update event is_past flags based on current time
    if 'events' in cache_data:
        current_total_minutes = current_hour * 60 + current_minute
        for evt in cache_data['events']:
            # Calculate event end time in minutes
            evt_start_min = evt.get('start_hour', 0) * 60 + evt.get('start_min', 0)
            evt_end_min = evt_start_min + evt.get('duration_min', 60)
            # Event is past if current time is after event end
            evt['is_past'] = current_total_minutes >= evt_end_min

    return minutes_until_next


def main(force_first_boot=None):
    """Main application loop with dual update system.

    Args:
        force_first_boot: Override for dev mode. True=first boot, False=subsequent loop.
                         None=use actual wake cause detection (for prod mode).
    """
    print("\n" + "=" * 50)
    print("Focus Display starting...")
    print("=" * 50)

    # Get wake cause
    wake_cause = get_wake_cause()

    # Determine if API refresh needed based on wake cause
    if force_first_boot is not None:
        # Dev mode: use the passed flag
        force_api_refresh = force_first_boot
        if force_first_boot:
            print("First boot in dev mode - will refresh API")
        else:
            print("Subsequent loop in dev mode - checking cache")
    else:
        # Prod mode: use actual wake cause
        force_api_refresh = (wake_cause == 'button' or wake_cause == 'reset')

    # Get current time from RTC
    rtc_time = get_rtc_time()
    print(f"RTC time: {rtc_time}")

    # Get world times for display
    times = get_world_times_from_rtc(rtc_time)
    local_hour, local_minute = times["barcelona"]
    weekday = rtc_time[6]

    # Initialize display
    display = FocusDisplay()

    # Load cached data
    cache_data = load_from_rtc_memory()

    # Determine if API refresh is needed
    need_api_refresh = force_api_refresh
    minutes_elapsed = 0

    if cache_data is None:
        print("No valid cache - need API refresh")
        need_api_refresh = True
    elif not force_api_refresh:
        # Calculate time since last API sync
        last_sync = cache_data.get('last_api_sync')
        minutes_elapsed = calculate_minutes_elapsed(last_sync, rtc_time)
        print(f"Minutes since last API sync: {minutes_elapsed}")

        # Check if we need to refresh based on interval
        api_interval_minutes = config.API_REFRESH_INTERVAL // 60
        if minutes_elapsed >= api_interval_minutes:
            print(f"API refresh interval ({api_interval_minutes} min) exceeded")
            need_api_refresh = True

    # Perform appropriate update
    if need_api_refresh:
        success, new_cache_data = do_api_refresh(display, rtc_time)
        if not success:
            if cache_data is None:
                # No cache and API failed - show error
                display.show_error("Calendar sync failed")
                sleep_until_refresh(60)
                return
            # API failed but we have cache - use cached data with time adjustment
            print("API failed, using cached data")
            minutes_until_next = do_time_only_update(cache_data, minutes_elapsed, local_hour, local_minute)
        else:
            cache_data = new_cache_data
            # Re-read times after potential NTP sync
            rtc_time = get_rtc_time()
            times = get_world_times_from_rtc(rtc_time)
            local_hour, local_minute = times["barcelona"]
            weekday = rtc_time[6]
            # Get fresh minutes_until_next from the new cache
            minutes_until_next = cache_data.get('minutes_until_next_original')
    else:
        # Time-only update using cached data
        minutes_until_next = do_time_only_update(cache_data, minutes_elapsed, local_hour, local_minute)

    # Extract data from cache
    next_title = cache_data.get('next_title')
    next_time_str = cache_data.get('next_time_str')
    todays_events = cache_data.get('events', [])

    # Check evening mode
    is_evening = check_evening_mode(local_hour, minutes_until_next)

    # Determine refresh interval based on time of day
    in_work_hours = is_work_hours(local_hour, weekday)
    if in_work_hours:
        refresh_interval = config.TIME_UPDATE_INTERVAL
        print(f"Work hours - sleeping {refresh_interval} seconds")
    else:
        refresh_interval = config.TIME_UPDATE_INTERVAL_NIGHT
        print(f"Night/weekend - sleeping {refresh_interval // 60} minutes")

    # Calculate full refresh need
    force_full_display = need_api_refresh  # Full display refresh after API sync

    # Render the display
    display.render(
        times=times,
        is_evening_mode=is_evening,
        minutes_until_next=minutes_until_next,
        next_meeting_title=next_title,
        next_meeting_time=next_time_str,
        todays_events=todays_events,
        current_hour=local_hour,
        current_minute=local_minute,
        force_full=force_full_display,
    )

    print("Display updated.")
    if minutes_until_next:
        print(f"Next meeting in {minutes_until_next} minutes.")
    else:
        print("No upcoming meetings.")

    # Sleep until next update, syncing to minute boundary during work hours
    sleep_until_refresh(refresh_interval, sync_to_minute=in_work_hours)


if __name__ == "__main__":
    if config.DEV_MODE:
        # In dev mode, loop continuously since light sleep doesn't reset
        # Track first run to force API refresh only on actual first boot
        _first_run = True
        while True:
            main(force_first_boot=_first_run)
            _first_run = False
    else:
        # In prod mode, main() ends with deep sleep which resets the device
        main()
