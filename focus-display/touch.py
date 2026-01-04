# Touch handling for Focus Display
import time
import config


class TouchHandler:
    """Handles touch input for view navigation."""

    def __init__(self, inkplate):
        self.inkplate = inkplate
        # Initialize touchscreen
        print("Initializing touchscreen...")
        self.inkplate.tsInit(1)
        print("Touchscreen initialized")

    def poll_once(self):
        """
        Check for touch and return action.

        Returns:
            "next" - right edge tapped
            "prev" - left edge tapped
            None - no touch or touch elsewhere
        """
        # First check if there's any touch at all using tsGetData
        try:
            touch_data = self.inkplate.tsGetData()
            if touch_data and len(touch_data) >= 3:
                num_fingers, x, y = touch_data[0], touch_data[1], touch_data[2]
                if num_fingers > 0:
                    print(f"Touch detected: fingers={num_fingers}, x={x}, y={y}")

                    # Check which zone
                    left = config.TOUCH_ZONES["left_edge"]
                    right = config.TOUCH_ZONES["right_edge"]

                    # Left zone: x < 100
                    if x < left[2]:
                        print("-> LEFT zone (prev)")
                        return "prev"
                    # Right zone: x > 924
                    elif x > right[0]:
                        print("-> RIGHT zone (next)")
                        return "next"
                    else:
                        print("-> CENTER (ignored)")
        except Exception as e:
            print(f"Touch error: {e}")

        return None

    def poll_for_duration(self, seconds):
        """
        Poll for touch events for a given duration.

        Args:
            seconds: How long to poll

        Returns:
            "next", "prev", or None if no touch detected
        """
        end_time = time.time() + seconds
        print(f"Polling for touch for {seconds} seconds...")

        while time.time() < end_time:
            action = self.poll_once()
            if action is not None:
                print(f"Touch action: {action}")
                # Debounce: wait for touch release
                time.sleep(0.5)
                return action

            # Small delay to avoid busy-waiting
            time.sleep(0.1)

        print("Touch polling ended - no touch detected")
        return None

    def shutdown(self):
        """Disable touchscreen to save power."""
        try:
            self.inkplate.tsShutdown()
        except:
            pass
