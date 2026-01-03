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
        """Format focus time as 'Xh Ymin' or 'Ymin'."""
        if minutes < 0:
            return "0min"
        hours = minutes // 60
        mins = minutes % 60
        if hours > 0:
            return f"{hours}h {mins}min"
        return f"{mins}min"

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

        # Main message - "You can focus for the next"
        self.display.setFont(self.font_medium)
        self.display.printText(focus_x, layout["focus_message_y"], "You can focus for")
        self.display.printText(focus_x, layout["focus_message_y"] + 50, "the next")

        # Focus time (extra large and prominent)
        self.display.setFont(self.font_xlarge_bold)
        focus_str = self.format_focus_time(minutes_until_next)
        self.display.printText(focus_x, layout["focus_time_y"], focus_str)

        # Horizontal separator line (below 80px text)
        line_y = layout["focus_time_y"] + 100
        self.display.drawLine(focus_x, line_y, focus_x + 500, line_y, 1)

        # Next meeting info
        self.display.setFont(self.font_small)
        if next_meeting_title:
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

    def render(self, times, is_evening_mode, minutes_until_next=None,
               next_meeting_title=None, next_meeting_time=None, force_full=False):
        """
        Render the complete display.

        Args:
            times: dict with world clock times
            is_evening_mode: True if after 7 PM with no meetings
            minutes_until_next: minutes until next meeting (if not evening mode)
            next_meeting_title: title of next meeting
            next_meeting_time: formatted time string of next meeting
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

        # Decide refresh type
        self.partial_refresh_count += 1
        full_refresh_needed = (
            force_full or
            self.partial_refresh_count >= (config.FULL_REFRESH_INTERVAL // config.SCREEN_REFRESH_INTERVAL)
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
