# Display rendering for Focus Display - Unified Three-Column Layout
from inkplate6FLICK import Inkplate
from shared.battery import get_battery_percentage
import config
import icons

# Import crisp pre-rendered fonts (installed on device at /lib/)
import FreeSans_24px
import FreeSans_32px
import FreeSans_48px
import FreeSansBold_48px
import FreeSans_72px
import FreeSansBold_72px
import FreeSansBold_80px


class FocusDisplay:
    def __init__(self):
        self.display = Inkplate(Inkplate.INKPLATE_1BIT)
        self.display.begin()
        self.partial_refresh_count = 0

        # Font references
        self.font_tiny = FreeSans_24px
        self.font_small = FreeSans_32px
        self.font_medium = FreeSansBold_48px
        self.font_large = FreeSans_72px
        self.font_large_bold = FreeSansBold_72px
        self.font_xlarge_bold = FreeSansBold_80px

    def format_time_12h(self, hour, minute):
        """Format time in 12-hour format without AM/PM (returned separately)."""
        hour_12 = hour % 12
        if hour_12 == 0:
            hour_12 = 12
        return f"{hour_12}:{minute:02d}"

    def get_period(self, hour):
        """Return AM or PM."""
        return "AM" if hour < 12 else "PM"

    def format_focus_time(self, minutes):
        """Format focus time as 'Xh Ym' or 'Ym'."""
        if minutes is None or minutes < 0:
            minutes = 0
        hours = minutes // 60
        mins = minutes % 60
        if hours > 0:
            return f"{hours}h {mins}m"
        return f"{mins}m"

    def format_hour_label(self, hour):
        """Format hour as '8a', '12p', etc."""
        period = "a" if hour < 12 else "p"
        h12 = hour % 12 or 12
        return f"{h12}{period}"

    def draw_battery_indicator(self):
        """Draw battery percentage in top right corner."""
        layout = config.LAYOUT
        pct = get_battery_percentage(self.display)
        self.display.setFont(self.font_tiny)
        self.display.printText(layout["battery_x"], layout["battery_y"], f"{pct}%")

    def draw_compact_clock(self, x, y, city_abbrev, hour, minute):
        """Draw a compact world clock with city, time, and AM/PM stacked."""
        # City abbreviation (small)
        self.display.setFont(self.font_small)
        self.display.printText(x, y, city_abbrev)

        # Time (large)
        self.display.setFont(self.font_large)
        time_str = self.format_time_12h(hour, minute)
        self.display.printText(x, y + 45, time_str)

        # AM/PM (small, below time)
        self.display.setFont(self.font_tiny)
        period = self.get_period(hour)
        self.display.printText(x, y + 115, period)

    def draw_world_clocks(self, times):
        """Draw compact world clocks in left column."""
        layout = config.LAYOUT
        x = layout["clocks_x"]

        # BCN
        h, m = times["barcelona"]
        self.draw_compact_clock(x, layout["clock_1_y"], "BCN", h, m)

        # NY
        h, m = times["new_york"]
        self.draw_compact_clock(x, layout["clock_2_y"], "NY", h, m)

        # SF
        h, m = times["san_francisco"]
        self.draw_compact_clock(x, layout["clock_3_y"], "SF", h, m)

    def draw_focus_section(self, is_evening, minutes_until_next, next_title, next_time_str,
                           meeting_type=None, location=None):
        """Draw the focus/meeting info in middle column."""
        layout = config.LAYOUT
        x = layout["focus_x"]

        is_busy = minutes_until_next is not None and minutes_until_next <= 0

        # Main message
        self.display.setFont(self.font_medium)
        if is_evening:
            self.display.printText(x, layout["focus_message_y"], "Remember")
            self.display.printText(x, layout["focus_message_y"] + 55, "your")
            # "priorities" larger
            self.display.setFont(self.font_large_bold)
            self.display.printText(x, layout["focus_time_y"], "priorities")
        elif is_busy:
            self.display.printText(x, layout["focus_message_y"], "Currently")
            self.display.printText(x, layout["focus_message_y"] + 55, "in meeting")
            # Show meeting title
            self.display.setFont(self.font_medium)
            if next_title:
                title = next_title[:20] + "..." if len(next_title) > 20 else next_title
                self.display.printText(x, layout["focus_time_y"], title)
            # Show meeting type icon
            if meeting_type:
                icon_y = layout["focus_time_y"] + 60
                icons.draw_icon(self.display, x, icon_y, meeting_type)
                # Show location text for in-person meetings
                if meeting_type == "in_person" and location:
                    self.display.setFont(self.font_tiny)
                    loc_text = location[:30] + "..." if len(location) > 30 else location
                    self.display.printText(x + 30, icon_y + 4, loc_text)
        else:
            self.display.printText(x, layout["focus_message_y"], "Focus for")
            # Focus time (extra large)
            self.display.setFont(self.font_xlarge_bold)
            focus_str = self.format_focus_time(minutes_until_next)
            self.display.printText(x, layout["focus_time_y"], focus_str)

        # Separator line
        line_y = layout["focus_time_y"] + 90
        self.display.drawLine(x, line_y, x + 380, line_y, 1)

        # Next meeting info (only if not evening and has next meeting)
        if not is_evening and next_title and not is_busy:
            self.display.setFont(self.font_small)
            title = next_title[:22] + "..." if len(next_title) > 22 else next_title
            # Show icon next to "Next:" if meeting type is known
            if meeting_type:
                icons.draw_icon(self.display, x, layout["focus_next_y"] - 2, meeting_type)
                self.display.printText(x + 30, layout["focus_next_y"], f"Next: {title}")
            else:
                self.display.printText(x, layout["focus_next_y"], f"Next: {title}")
            if next_time_str:
                time_x = x + 30 if meeting_type else x
                self.display.printText(time_x, layout["focus_next_y"] + 40, f"@ {next_time_str}")

    def draw_timeline(self, events, current_hour):
        """Draw the vertical timeline in right column."""
        layout = config.LAYOUT
        start_hour = layout["timeline_start_hour"]
        end_hour = layout["timeline_end_hour"]
        row_height = layout["timeline_row_height"]
        top_y = layout["timeline_top_y"]
        hour_x = layout["timeline_hour_x"]
        bar_x = layout["timeline_bar_x"]
        bar_width = layout["timeline_bar_width"]

        # Build events by hour
        events_by_hour = {}
        for evt in events:
            h = evt["start_hour"]
            if start_hour <= h < end_hour:
                events_by_hour[h] = evt

        self.display.setFont(self.font_tiny)

        for hour in range(start_hour, end_hour):
            row_idx = hour - start_hour
            y = top_y + row_idx * row_height

            # Hour label
            hour_label = self.format_hour_label(hour)
            self.display.printText(hour_x, y + 5, hour_label)

            # NOW marker - draw arrow and highlight
            if hour == current_hour and start_hour <= current_hour < end_hour:
                # Draw arrow pointing to this row
                arrow_x = hour_x - 25
                self.display.printText(arrow_x, y + 5, ">")
                # Draw horizontal line across the row
                self.display.drawLine(bar_x - 10, y + 15, bar_x + bar_width, y + 15, 1)

            if hour in events_by_hour:
                evt = events_by_hour[hour]
                duration = evt["duration_min"]

                # Bar width proportional to duration (max 60 min fills the width)
                scaled_width = min(duration * bar_width // 60, bar_width)

                bar_y = y
                bar_height = row_height - 10

                if evt["is_past"]:
                    # Past meetings: outline only
                    self.display.drawRect(bar_x, bar_y, scaled_width, bar_height, 1)
                else:
                    # Future meetings: filled
                    self.display.fillRect(bar_x, bar_y, scaled_width, bar_height, 1)

                # Meeting title (truncated)
                title = evt["summary"]
                if len(title) > 15:
                    title = title[:12] + "..."

                # Position text after bar for filled, inside for outline
                if evt["is_past"]:
                    self.display.printText(bar_x + 5, y + 5, title)
                else:
                    text_x = bar_x + scaled_width + 8
                    if text_x + 100 > config.DISPLAY_WIDTH:
                        text_x = bar_x + 5  # Put inside if no room
                    self.display.printText(text_x, y + 5, title)
            else:
                # Empty hour - draw light dotted line
                line_y = y + row_height // 2
                for dot_x in range(bar_x, bar_x + bar_width, 15):
                    self.display.drawPixel(dot_x, line_y, 1)

    def draw_dividers(self):
        """Draw vertical divider lines between columns."""
        layout = config.LAYOUT

        # Divider between clocks and focus
        self.display.drawLine(
            layout["divider1_x"], 50,
            layout["divider1_x"], config.DISPLAY_HEIGHT - 50, 1
        )

        # Divider between focus and timeline
        self.display.drawLine(
            layout["divider2_x"], 50,
            layout["divider2_x"], config.DISPLAY_HEIGHT - 50, 1
        )

    def render(self, times, is_evening_mode, minutes_until_next=None,
               next_meeting_title=None, next_meeting_time=None,
               todays_events=None, current_hour=12, force_full=False,
               meeting_type=None, location=None):
        """
        Render the unified three-column display.

        Args:
            times: dict with world clock times
            is_evening_mode: True if showing evening priorities
            minutes_until_next: minutes until next meeting
            next_meeting_title: title of next meeting
            next_meeting_time: formatted time string
            todays_events: list of today's events for timeline
            current_hour: current hour (0-23) for NOW marker
            force_full: force a full refresh
            meeting_type: 'meet', 'zoom', 'teams', 'in_person', or None
            location: location string for in-person meetings
        """
        self.display.clearDisplay()

        # Draw battery indicator (top right)
        self.draw_battery_indicator()

        # Draw vertical dividers
        self.draw_dividers()

        # Left column: World clocks
        self.draw_world_clocks(times)

        # Middle column: Focus info
        self.draw_focus_section(is_evening_mode, minutes_until_next,
                                next_meeting_title, next_meeting_time,
                                meeting_type, location)

        # Right column: Timeline
        if todays_events is not None:
            self.draw_timeline(todays_events, current_hour)

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
