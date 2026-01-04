# Display rendering for Focus Display - Unified Three-Column Layout
from inkplate6FLICK import Inkplate
from shared.battery import get_battery_percentage
import config

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
        # Use 2BIT mode for grey shading (0=white, 1=light grey, 2=dark grey, 3=black)
        self.display = Inkplate(Inkplate.INKPLATE_2BIT)
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

        # Time (medium bold - compact but readable)
        self.display.setFont(self.font_medium)
        time_str = self.format_time_12h(hour, minute)
        self.display.printText(x, y + 40, time_str)

        # AM/PM (small, below time)
        self.display.setFont(self.font_tiny)
        period = self.get_period(hour)
        self.display.printText(x, y + 95, period)

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

    def draw_focus_section(self, is_evening, minutes_until_next, next_title, next_time_str):
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
            self.display.printText(x, layout["focus_next_y"], f"Next: {title}")
            if next_time_str:
                self.display.printText(x, layout["focus_next_y"] + 40, f"@ {next_time_str}")

    def draw_timeline(self, events, current_hour, current_minute=0):
        """Draw the vertical timeline in right column with multi-hour event support."""
        layout = config.LAYOUT
        start_hour = layout["timeline_start_hour"]
        end_hour = layout["timeline_end_hour"]
        row_height = layout["timeline_row_height"]
        top_y = layout["timeline_top_y"]
        hour_x = layout["timeline_hour_x"]
        bar_x = layout["timeline_bar_x"]
        bar_width = layout["timeline_bar_width"]
        total_minutes = (end_hour - start_hour) * 60
        total_height = (end_hour - start_hour) * row_height

        # Colors for 2BIT mode: 0=white, 1=light grey, 2=dark grey, 3=black
        LIGHT_GREY = 1
        DARK_GREY = 2
        BLACK = 3

        # Draw hour labels and grid lines first
        self.display.setFont(self.font_tiny)
        for hour in range(start_hour, end_hour):
            row_idx = hour - start_hour
            y = top_y + row_idx * row_height

            # Hour label
            hour_label = self.format_hour_label(hour)
            self.display.printText(hour_x, y + 5, hour_label)

            # Light dotted grid line for empty hours
            line_y = y + row_height // 2
            for dot_x in range(bar_x, bar_x + bar_width, 20):
                self.display.drawPixel(dot_x, line_y, LIGHT_GREY)

        # Draw events as blocks spanning their full duration
        for evt in events:
            evt_start_hour = evt["start_hour"]
            evt_start_min = evt["start_min"]
            duration = evt["duration_min"]

            # Skip events outside our display range
            if evt_start_hour >= end_hour or evt_start_hour < start_hour:
                continue

            # Calculate Y position based on start time
            minutes_from_start = (evt_start_hour - start_hour) * 60 + evt_start_min
            evt_y = top_y + (minutes_from_start * total_height) // total_minutes

            # Calculate height based on duration
            evt_height = (duration * total_height) // total_minutes
            evt_height = max(evt_height, 20)  # Minimum height

            # Clamp to display bounds
            max_y = top_y + total_height
            if evt_y + evt_height > max_y:
                evt_height = max_y - evt_y

            # Choose color based on past/future
            fill_color = LIGHT_GREY if evt["is_past"] else DARK_GREY

            # Draw filled rectangle for the event
            self.display.fillRect(bar_x, evt_y, bar_width, evt_height, fill_color)
            # Draw border
            self.display.drawRect(bar_x, evt_y, bar_width, evt_height, BLACK)

            # Draw title inside the block
            title = evt["summary"]
            # Truncate based on available width (~12 chars fit in bar_width with tiny font)
            if len(title) > 18:
                title = title[:15] + "..."

            # Center text vertically in the block
            text_y = evt_y + (evt_height // 2) - 10
            if text_y < evt_y + 5:
                text_y = evt_y + 5

            self.display.printText(bar_x + 5, text_y, title)

        # Draw NOW marker AFTER events so it appears on top
        current_total_minutes = current_hour * 60 + current_minute
        start_minutes = start_hour * 60
        end_minutes = end_hour * 60
        if start_minutes <= current_total_minutes < end_minutes:
            # Calculate precise Y position based on minutes
            minutes_from_start = current_total_minutes - start_minutes
            now_y = top_y + (minutes_from_start * total_height) // total_minutes
            arrow_x = hour_x - 25
            self.display.printText(arrow_x, now_y - 8, ">")
            # Horizontal line at current time (from arrow to end of timeline)
            line_start_x = arrow_x + 20  # Start after the arrow
            line_end_x = bar_x + bar_width
            # Draw thick line centered on arrow using fillRect
            self.display.fillRect(line_start_x, now_y + 1, line_end_x - line_start_x, 3, BLACK)

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
               todays_events=None, current_hour=12, current_minute=0, force_full=False):
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
            current_minute: current minute (0-59) for precise NOW marker
            force_full: force a full refresh
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
                                next_meeting_title, next_meeting_time)

        # Right column: Timeline
        if todays_events is not None:
            self.draw_timeline(todays_events, current_hour, current_minute)

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
