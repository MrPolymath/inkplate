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

        # Build time range - start from beginning of today to include past events
        time_min = self._format_datetime_for_api(year, month, day, 0, 0)

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

                    # Skip working location events (not real meetings)
                    event_type = item.get("eventType", "")
                    if event_type in ("workingLocation", "outOfOffice", "focusTime"):
                        continue

                    # Skip all-day events (no specific time = not a meeting)
                    start = item.get("start", {})
                    if "date" in start and "dateTime" not in start:
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

                    # Get start and end time
                    end = item.get("end", {})
                    start_dt = start.get("dateTime") or start.get("date")
                    end_dt = end.get("dateTime") or end.get("date")

                    if start_dt:
                        start_time = self._parse_datetime(start_dt)
                        end_time = self._parse_datetime(end_dt) if end_dt else start_time

                        # Calculate duration in minutes
                        start_mins = start_time[3] * 60 + start_time[4]
                        end_mins = end_time[3] * 60 + end_time[4]
                        duration = max(0, end_mins - start_mins)

                        # Get meeting type info
                        meeting_type = self._get_meeting_type(item)
                        location = item.get("location", "")

                        events.append({
                            "summary": item.get("summary", "No title"),
                            "start_datetime": start_dt,
                            "start_time": start_time,
                            "end_time": end_time,
                            "duration_min": duration,
                            "meeting_type": meeting_type,
                            "location": location,
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

    def _get_meeting_type(self, item):
        """
        Determine meeting type from calendar event.

        Returns: 'meet', 'zoom', 'teams', 'in_person', or None
        """
        # Check for Google Meet (hangoutLink or conferenceData)
        if item.get("hangoutLink"):
            return "meet"

        # Check conferenceData for other services
        conf_data = item.get("conferenceData", {})
        conf_solution = conf_data.get("conferenceSolution", {})
        conf_name = conf_solution.get("name", "").lower()

        if "meet" in conf_name or "hangout" in conf_name:
            return "meet"
        elif "zoom" in conf_name:
            return "zoom"
        elif "teams" in conf_name or "microsoft" in conf_name:
            return "teams"

        # Check entry points for URLs
        for entry in conf_data.get("entryPoints", []):
            uri = entry.get("uri", "").lower()
            if "meet.google" in uri or "hangouts" in uri:
                return "meet"
            elif "zoom.us" in uri or "zoom.com" in uri:
                return "zoom"
            elif "teams.microsoft" in uri or "teams.live" in uri:
                return "teams"

        # Check location for physical address (in-person meeting)
        location = item.get("location", "")
        if location and not any(x in location.lower() for x in ["http", "zoom", "meet", "teams"]):
            return "in_person"

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
        Find the current or next meeting from a list of events.

        Returns:
            tuple (minutes_until, title, formatted_time, meeting_type, location)
            or (None, None, None, None, None)
            - minutes_until <= 0 means currently in a meeting
            - minutes_until > 0 means time until next meeting
            - meeting_type: 'meet', 'zoom', 'teams', 'in_person', or None
        """
        if not events:
            return None, None, None, None, None

        year, month, day, hour, minute = current_time[:5]
        current_minutes = hour * 60 + minute

        for event in events:
            evt_year, evt_month, evt_day, evt_hour, evt_minute = event["start_time"]
            end_time = event.get("end_time", event["start_time"])
            end_hour, end_minute = end_time[3], end_time[4]

            # Same day event
            if evt_year == year and evt_month == month and evt_day == day:
                evt_start_minutes = evt_hour * 60 + evt_minute
                evt_end_minutes = end_hour * 60 + end_minute

                # Check if currently IN this meeting
                if evt_start_minutes <= current_minutes < evt_end_minutes:
                    # Return negative/zero to indicate "in meeting"
                    minutes_until = evt_start_minutes - current_minutes  # Will be <= 0
                    period = "AM" if evt_hour < 12 else "PM"
                    h12 = evt_hour % 12 or 12
                    time_str = f"{h12}:{evt_minute:02d} {period}"
                    return minutes_until, event["summary"], time_str, event.get("meeting_type"), event.get("location", "")

                # Check if this meeting is upcoming
                if evt_start_minutes > current_minutes:
                    minutes_until = evt_start_minutes - current_minutes
                    period = "AM" if evt_hour < 12 else "PM"
                    h12 = evt_hour % 12 or 12
                    time_str = f"{h12}:{evt_minute:02d} {period}"
                    return minutes_until, event["summary"], time_str, event.get("meeting_type"), event.get("location", "")

            # Future day event
            elif (evt_year, evt_month, evt_day) > (year, month, day):
                period = "AM" if evt_hour < 12 else "PM"
                h12 = evt_hour % 12 or 12
                time_str = f"Tomorrow {h12}:{evt_minute:02d} {period}"

                remaining_today = (24 * 60) - current_minutes
                tomorrow_minutes = evt_hour * 60 + evt_minute
                minutes_until = remaining_today + tomorrow_minutes

                return minutes_until, event["summary"], time_str, event.get("meeting_type"), event.get("location", "")

        return None, None, None, None, None

    def get_todays_events(self, events, current_time):
        """
        Filter events to only today's events, with is_past flag.

        Returns:
            List of events for today with:
            - summary, start_hour, start_min, duration_min, is_past
        """
        if not events:
            return []

        year, month, day, hour, minute = current_time[:5]
        current_minutes = hour * 60 + minute
        today_events = []

        for event in events:
            evt_year, evt_month, evt_day, evt_hour, evt_minute = event["start_time"]

            # Only include today's events
            if evt_year == year and evt_month == month and evt_day == day:
                evt_start_mins = evt_hour * 60 + evt_minute
                is_past = evt_start_mins + event.get("duration_min", 0) < current_minutes

                today_events.append({
                    "summary": event["summary"],
                    "start_hour": evt_hour,
                    "start_min": evt_minute,
                    "duration_min": event.get("duration_min", 30),
                    "is_past": is_past,
                })

        return today_events
