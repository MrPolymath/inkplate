# Display rendering for Focus Display
from inkplate6FLICK import Inkplate
from shared.battery import get_battery_percentage
import config

# Import crisp pre-rendered fonts (installed on device at /lib/)
import FreeSans_24px
import FreeSans_32px
import FreeSans_48px
import FreeSans_72px
import FreeSansBold_72px
import FreeSansBold_80px


class FocusDisplay:
    def __init__(self):
        self.display = Inkplate(Inkplate.INKPLATE_1BIT)
        self.display.begin()
        self.partial_refresh_count = 0

        # Font references for easy switching
        self.font_tiny = FreeSans_24px        # 24px for battery indicator
        self.font_small = FreeSans_32px       # 32px for small labels
        self.font_medium = FreeSans_48px      # 48px for messages
        self.font_large = FreeSans_72px       # 72px for clock times
        self.font_large_bold = FreeSansBold_72px  # 72px bold
        self.font_xlarge_bold = FreeSansBold_80px  # 80px for focus time

    def format_time_12h(self, hour, minute):
        """Format time in 12-hour format with AM/PM."""
        period = "AM" if hour < 12 else "PM"
        hour_12 = hour % 12
        if hour_12 == 0:
            hour_12 = 12
        return f"{hour_12}:{minute:02d} {period}"

    def format_focus_time(self, minutes):
        """Format focus time as 'Xh Y min' or 'Y min'."""
        if minutes < 0:
            minutes = 0
        hours = minutes // 60
        mins = minutes % 60
        if hours > 0:
            return f"{hours} h {mins} min"
        return f"{mins} min"

    def draw_battery_indicator(self):
        """Draw battery percentage in top right corner."""
        pct = get_battery_percentage(self.display)
        self.display.setFont(self.font_tiny)
        self.display.printText(940, 30, f"{pct}%")

    def draw_clock(self, x, y, city_name, hour, minute):
        """Draw a single world clock."""
        # City name (small label)
        self.display.setFont(self.font_small)
        self.display.printText(x, y, city_name)

        # Time (large)
        self.display.setFont(self.font_medium)
        time_str = self.format_time_12h(hour, minute)
        self.display.printText(x, y + 50, time_str)

    def draw_world_clocks(self, times):
        """
        Draw all three world clocks.
        times: dict with keys 'barcelona', 'new_york', 'san_francisco'
               each value is (hour, minute) tuple
        """
        layout = config.LAYOUT

        # Barcelona
        h, m = times["barcelona"]
        self.draw_clock(layout["clocks_x"], layout["clock_1_y"], "BARCELONA", h, m)

        # New York
        h, m = times["new_york"]
        self.draw_clock(layout["clocks_x"], layout["clock_2_y"], "NEW YORK", h, m)

        # San Francisco
        h, m = times["san_francisco"]
        self.draw_clock(layout["clocks_x"], layout["clock_3_y"], "SAN FRAN", h, m)

        # Draw vertical divider line (full height)
        divider_x = layout["divider_x"]
        self.display.drawLine(divider_x, layout["divider_top"],
                              divider_x, layout["divider_bottom"], 1)

    def draw_focus_mode(self, minutes_until_next, next_meeting_title, next_meeting_time):
        """Draw the focus timer display."""
        layout = config.LAYOUT
        focus_x = layout["focus_x"]

        is_busy = minutes_until_next is not None and minutes_until_next <= 0

        # Main message
        self.display.setFont(self.font_medium)
        if is_busy:
            self.display.printText(focus_x, layout["focus_message_y"], "Currently in")
            self.display.printText(focus_x, layout["focus_message_y"] + 50, "a meeting")
        else:
            self.display.printText(focus_x, layout["focus_message_y"], "You can focus for")
            self.display.printText(focus_x, layout["focus_message_y"] + 50, "the next")

        # Focus time (extra large and prominent) or meeting title if busy
        if is_busy:
            # Show current meeting title in medium font (fits better)
            self.display.setFont(self.font_medium)
            if next_meeting_title:
                # Split into two lines if needed (max ~25 chars per line)
                if len(next_meeting_title) > 25:
                    # Find a good break point
                    break_at = next_meeting_title.rfind(' ', 0, 25)
                    if break_at == -1:
                        break_at = 25
                    line1 = next_meeting_title[:break_at]
                    line2 = next_meeting_title[break_at:50].strip()
                    if len(next_meeting_title) > 50:
                        line2 = line2[:22] + "..."
                    self.display.printText(focus_x, layout["focus_time_y"], line1)
                    self.display.printText(focus_x, layout["focus_time_y"] + 55, line2)
                else:
                    self.display.printText(focus_x, layout["focus_time_y"], next_meeting_title)
            else:
                self.display.printText(focus_x, layout["focus_time_y"], "Busy")
        else:
            self.display.setFont(self.font_xlarge_bold)
            focus_str = self.format_focus_time(minutes_until_next)
            self.display.printText(focus_x, layout["focus_time_y"], focus_str)

        # Horizontal separator line (below 80px text)
        line_y = layout["focus_time_y"] + 100
        self.display.drawLine(focus_x, line_y, focus_x + 500, line_y, 1)

        # Next meeting info (only show if not busy, or show next after current)
        self.display.setFont(self.font_small)
        if next_meeting_title and not is_busy:
            # Truncate title if too long
            title = next_meeting_title[:30] + "..." if len(next_meeting_title) > 30 else next_meeting_title
            self.display.printText(focus_x, layout["focus_next_y"], f"Next: {title}")
            self.display.printText(focus_x, layout["focus_next_y"] + 35, f"@ {next_meeting_time}")

    def draw_evening_mode(self):
        """Draw the evening 'remember your priorities' display."""
        layout = config.LAYOUT
        focus_x = layout["focus_x"]

        # Main message
        self.display.setFont(self.font_medium)
        self.display.printText(focus_x, layout["focus_message_y"], "Remember your")

        # "priorities" larger
        self.display.setFont(self.font_large_bold)
        self.display.printText(focus_x, layout["focus_time_y"], "priorities")

        # Separator line
        line_y = layout["focus_time_y"] + 70
        self.display.drawLine(focus_x, line_y, focus_x + 450, line_y, 1)

        # Subtext
        self.display.setFont(self.font_small)
        self.display.printText(focus_x, layout["focus_next_y"],
                               "No meetings until tomorrow")

    def draw_page_indicator(self, current_view, total_views=2):
        """Draw page indicator dots at bottom of screen."""
        pi = config.PAGE_INDICATOR
        center_x = config.DISPLAY_WIDTH // 2
        total_width = (total_views - 1) * pi["dot_spacing"]
        start_x = center_x - total_width // 2

        for i in range(total_views):
            x = start_x + i * pi["dot_spacing"]
            y = pi["y"]
            r = pi["dot_radius"]

            if i == current_view:
                # Filled circle for current view
                self.display.fillCircle(x, y, r, 1)
            else:
                # Empty circle for other views
                self.display.drawCircle(x, y, r, 1)

    def format_hour_label(self, hour):
        """Format hour as '8 AM', '12 PM', etc."""
        period = "AM" if hour < 12 else "PM"
        h12 = hour % 12 or 12
        return f"{h12} {period}"

    def format_duration(self, minutes):
        """Format duration as '30 min' or '1 h 30 min'."""
        if minutes >= 60:
            h = minutes // 60
            m = minutes % 60
            if m > 0:
                return f"{h} h {m} m"
            return f"{h} h"
        return f"{minutes} m"

    def draw_agenda(self, events, current_hour, date_str=""):
        """
        Draw the agenda view showing 8am-8pm schedule.

        Args:
            events: List of events with start_hour, start_min, duration_min, summary, is_past
            current_hour: Current hour (0-23) for NOW marker
            date_str: Date string like "Friday, Jan 3"
        """
        layout = config.AGENDA_LAYOUT
        start_hour = layout["start_hour"]
        end_hour = layout["end_hour"]
        row_height = layout["row_height"]
        first_row_y = layout["first_row_y"]

        # Title
        self.display.setFont(self.font_medium)
        title = f"TODAY - {date_str}" if date_str else "TODAY"
        self.display.printText(layout["title_x"], layout["title_y"], title)

        # Draw battery indicator
        self.draw_battery_indicator()

        # Build a map of events by hour
        events_by_hour = {}
        for evt in events:
            h = evt["start_hour"]
            if start_hour <= h < end_hour:
                if h not in events_by_hour:
                    events_by_hour[h] = []
                events_by_hour[h].append(evt)

        # Draw each hour row
        self.display.setFont(self.font_small)
        for hour in range(start_hour, end_hour):
            row_idx = hour - start_hour
            y = first_row_y + row_idx * row_height

            # Hour label
            hour_label = self.format_hour_label(hour)
            self.display.printText(layout["hour_x"], y, hour_label)

            # Check if this is the current hour
            is_now = (hour == current_hour)

            if hour in events_by_hour:
                # Draw meeting(s) for this hour
                evt = events_by_hour[hour][0]  # Take first event if multiple
                duration = evt["duration_min"]

                # Bar width proportional to duration (30 min = ~125px, 60 min = ~250px)
                bar_width = min(duration * 4, layout["bar_width_max"])

                # Draw filled rectangle for meeting
                bar_x = layout["bar_x"]
                bar_y = y - 5
                bar_height = row_height - 15

                if evt["is_past"]:
                    # Past meetings: just outline
                    self.display.drawRect(bar_x, bar_y, bar_width, bar_height, 1)
                else:
                    # Future meetings: filled
                    self.display.fillRect(bar_x, bar_y, bar_width, bar_height, 1)
                    # Draw text in white (inverted)
                    # Note: Inkplate 1-bit doesn't support text color easily,
                    # so we'll draw text next to bar instead
                    self.display.setFont(self.font_tiny)

                # Meeting title (truncate if needed)
                title = evt["summary"]
                if len(title) > 25:
                    title = title[:22] + "..."

                # Position text after bar for filled, or inside outline for past
                if evt["is_past"]:
                    self.display.printText(bar_x + 10, y, title)
                else:
                    text_x = bar_x + bar_width + 15
                    self.display.printText(text_x, y, title)

                self.display.setFont(self.font_small)
            else:
                # Empty hour - draw dotted line
                line_y = y + 10
                for x in range(layout["bar_x"], layout["bar_x"] + layout["bar_width_max"], 20):
                    self.display.drawPixel(x, line_y, 1)
                    self.display.drawPixel(x + 1, line_y, 1)

            # NOW marker
            if is_now and start_hour <= current_hour < end_hour:
                now_x = layout["bar_x"] - 30
                self.display.printText(now_x, y, ">")

    def render_agenda(self, events, current_hour, date_str="", current_view=1, force_full=False):
        """Render the agenda view with page indicator."""
        self.display.clearDisplay()

        self.draw_agenda(events, current_hour, date_str)
        self.draw_page_indicator(current_view)

        # Decide refresh type
        self.partial_refresh_count += 1
        full_refresh_needed = (
            force_full or
            self.partial_refresh_count >= (config.FULL_REFRESH_INTERVAL // config.SCREEN_REFRESH_INTERVAL_DAY)
        )

        if full_refresh_needed:
            self.display.display()
            self.partial_refresh_count = 0
        else:
            self.display.partialUpdate()

    def render(self, times, is_evening_mode, minutes_until_next=None,
               next_meeting_title=None, next_meeting_time=None,
               current_view=0, force_full=False):
        """
        Render the focus view (view 0).

        Args:
            times: dict with world clock times
            is_evening_mode: True if after 7 PM with no meetings
            minutes_until_next: minutes until next meeting (if not evening mode)
            next_meeting_title: title of next meeting
            next_meeting_time: formatted time string of next meeting
            current_view: current view index for page indicator
            force_full: force a full refresh
        """
        self.display.clearDisplay()

        # Draw battery indicator (top right)
        self.draw_battery_indicator()

        # Draw world clocks (always shown)
        self.draw_world_clocks(times)

        # Draw main content area
        if is_evening_mode:
            self.draw_evening_mode()
        else:
            self.draw_focus_mode(minutes_until_next, next_meeting_title, next_meeting_time)

        # Draw page indicator
        self.draw_page_indicator(current_view)

        # Decide refresh type
        self.partial_refresh_count += 1
        full_refresh_needed = (
            force_full or
            self.partial_refresh_count >= (config.FULL_REFRESH_INTERVAL // config.SCREEN_REFRESH_INTERVAL_DAY)
        )

        if full_refresh_needed:
            self.display.display()
            self.partial_refresh_count = 0
        else:
            self.display.partialUpdate()

    def show_error(self, message):
        """Display an error message."""
        self.display.clearDisplay()
        self.display.setFont(self.font_large)
        self.display.printText(100, 300, "Error:")
        self.display.setFont(self.font_medium)
        self.display.printText(100, 370, message)
        self.display.display()

    def show_connecting(self):
        """Display a connecting message."""
        self.display.clearDisplay()
        self.display.setFont(self.font_large)
        self.display.printText(300, 350, "Connecting...")
        self.display.display()
