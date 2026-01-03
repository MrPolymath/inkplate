# Google Calendar sync for Focus Display
import urequests
import ujson
import time
import config


class CalendarSync:
    def __init__(self, client_id, client_secret, refresh_token, calendar_id="primary"):
        self.client_id = client_id
        self.client_secret = client_secret
        self.refresh_token = refresh_token
        self.calendar_id = calendar_id
        self.access_token = None
        self.token_expires = 0

    def _refresh_access_token(self):
        """Get a new access token using the refresh token."""
        url = "https://oauth2.googleapis.com/token"
        data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "refresh_token": self.refresh_token,
            "grant_type": "refresh_token",
        }

        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        body = "&".join(f"{k}={v}" for k, v in data.items())

        try:
            response = urequests.post(url, data=body, headers=headers)
            if response.status_code == 200:
                result = response.json()
                self.access_token = result["access_token"]
                # Token expires in ~1 hour, refresh 5 min early
                self.token_expires = time.time() + result.get("expires_in", 3600) - 300
                response.close()
                return True
            else:
                print(f"Token refresh failed: {response.status_code}")
                try:
                    error_body = response.text
                    print(f"Token error: {error_body[:500]}")
                except:
                    pass
                response.close()
                return False
        except Exception as e:
            print(f"Token refresh error: {e}")
            return False

    def _ensure_token(self):
        """Ensure we have a valid access token."""
        if self.access_token is None or time.time() >= self.token_expires:
            return self._refresh_access_token()
        return True

    def _format_datetime_for_api(self, year, month, day, hour=0, minute=0):
        """Format datetime for Google Calendar API (RFC3339)."""
        return f"{year:04d}-{month:02d}-{day:02d}T{hour:02d}:{minute:02d}:00Z"

    def get_upcoming_events(self, current_time, days_ahead=2):
        """
        Fetch upcoming events from Google Calendar.

        Args:
            current_time: tuple (year, month, day, hour, minute, second, weekday, yearday)
            days_ahead: how many days ahead to fetch

        Returns:
            List of events with 'summary', 'start_time' (as tuple), 'start_datetime' (ISO string)
        """
        if not self._ensure_token():
            return None

        year, month, day, hour, minute, second, _, _ = current_time

        # Build time range
        time_min = self._format_datetime_for_api(year, month, day, hour, minute)

        # Simple days ahead calculation (not handling month boundaries perfectly)
        end_day = day + days_ahead
        end_month = month
        end_year = year
        # Basic overflow handling
        if end_day > 28:  # Safe for all months
            end_day = end_day - 28
            end_month += 1
            if end_month > 12:
                end_month = 1
                end_year += 1
        time_max = self._format_datetime_for_api(end_year, end_month, end_day, 23, 59)

        # Build API URL
        base_url = f"{config.CALENDAR_API_BASE}/calendars/{self.calendar_id}/events"
        params = (
            f"?timeMin={time_min}"
            f"&timeMax={time_max}"
            f"&singleEvents=true"
            f"&orderBy=startTime"
            f"&maxResults=10"
        )
        url = base_url + params

        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Accept": "application/json",
        }

        try:
            response = urequests.get(url, headers=headers)
            if response.status_code == 200:
                data = response.json()
                events = []
                for item in data.get("items", []):
                    # Skip declined events
                    if item.get("status") == "cancelled":
                        continue

                    # Check attendee status if present
                    attendees = item.get("attendees", [])
                    declined = False
                    for att in attendees:
                        if att.get("self") and att.get("responseStatus") == "declined":
                            declined = True
                            break
                    if declined:
                        continue

                    # Get start time
                    start = item.get("start", {})
                    start_dt = start.get("dateTime") or start.get("date")

                    if start_dt:
                        events.append({
                            "summary": item.get("summary", "No title"),
                            "start_datetime": start_dt,
                            "start_time": self._parse_datetime(start_dt),
                        })

                response.close()
                return events
            else:
                print(f"Calendar API error: {response.status_code}")
                try:
                    error_body = response.text
                    print(f"Error details: {error_body[:500]}")
                except:
                    pass
                response.close()
                return None
        except Exception as e:
            print(f"Calendar fetch error: {e}")
            return None

    def _parse_datetime(self, dt_string):
        """
        Parse ISO datetime string to tuple (year, month, day, hour, minute).
        Handles both 'YYYY-MM-DD' and 'YYYY-MM-DDTHH:MM:SS+XX:XX' formats.
        """
        try:
            # Handle date-only format (all-day events)
            if "T" not in dt_string:
                parts = dt_string.split("-")
                return (int(parts[0]), int(parts[1]), int(parts[2]), 0, 0)

            # Split date and time
            date_part, time_part = dt_string.split("T")
            year, month, day = map(int, date_part.split("-"))

            # Handle time (strip timezone info)
            time_clean = time_part.split("+")[0].split("-")[0].split("Z")[0]
            time_parts = time_clean.split(":")
            hour = int(time_parts[0])
            minute = int(time_parts[1]) if len(time_parts) > 1 else 0

            return (year, month, day, hour, minute)
        except Exception as e:
            print(f"Parse datetime error: {e}, input: {dt_string}")
            return (2000, 1, 1, 0, 0)

    def get_next_meeting(self, events, current_time):
        """
        Find the next meeting from a list of events.

        Returns:
            tuple (minutes_until, title, formatted_time) or (None, None, None)
        """
        if not events:
            return None, None, None

        year, month, day, hour, minute = current_time[:5]
        current_minutes = hour * 60 + minute

        for event in events:
            evt_year, evt_month, evt_day, evt_hour, evt_minute = event["start_time"]

            # Same day event
            if evt_year == year and evt_month == month and evt_day == day:
                evt_minutes = evt_hour * 60 + evt_minute
                if evt_minutes > current_minutes:
                    minutes_until = evt_minutes - current_minutes
                    # Format time as 12h
                    period = "AM" if evt_hour < 12 else "PM"
                    h12 = evt_hour % 12 or 12
                    time_str = f"{h12}:{evt_minute:02d} {period}"
                    return minutes_until, event["summary"], time_str

            # Future day event
            elif (evt_year, evt_month, evt_day) > (year, month, day):
                # Calculate rough minutes until (for display purposes)
                # This is simplified - just show it's tomorrow
                period = "AM" if evt_hour < 12 else "PM"
                h12 = evt_hour % 12 or 12
                time_str = f"Tomorrow {h12}:{evt_minute:02d} {period}"

                # Rough estimate: remaining today + hours tomorrow
                remaining_today = (24 * 60) - current_minutes
                tomorrow_minutes = evt_hour * 60 + evt_minute
                minutes_until = remaining_today + tomorrow_minutes

                return minutes_until, event["summary"], time_str

        return None, None, None
