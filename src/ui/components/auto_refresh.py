"""Auto-refresh Component

Handles automatic weather data updates with configurable intervals.
"""

import threading
from datetime import datetime, timedelta
from typing import Callable, Optional

import customtkinter as ctk

from ..theme import DataTerminalTheme


class AutoRefreshComponent(ctk.CTkFrame):
    """Auto-refresh component with manual controls."""

    def __init__(self, parent, refresh_callback: Callable[[], None], ui_updater=None):
        super().__init__(parent, fg_color="transparent")

        self.refresh_callback = refresh_callback
        self.ui_updater = ui_updater or parent  # Use parent if no ui_updater provided
        self.auto_refresh_enabled = True
        self.refresh_interval = 300  # 5 minutes default
        self.last_refresh = None
        self.refresh_thread: Optional[threading.Thread] = None
        self.stop_refresh = threading.Event()

        # Create UI
        self._create_refresh_ui()

        # Don't start auto-refresh automatically
        # It will be started when the user enables it via the toggle

    def _create_refresh_ui(self):
        """Create the refresh control UI."""
        # Main frame
        self.refresh_frame = ctk.CTkFrame(
            self,
            fg_color=DataTerminalTheme.CARD_BG,
            corner_radius=8,
            border_color=DataTerminalTheme.BORDER,
            border_width=1,
            height=60,
        )
        self.refresh_frame.grid(row=0, column=0, padx=10, pady=5, sticky="ew")
        self.refresh_frame.grid_columnconfigure(1, weight=1)

        # Manual refresh button
        self.refresh_button = ctk.CTkButton(
            self.refresh_frame,
            text="🔄 Refresh",
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color=DataTerminalTheme.PRIMARY,
            hover_color=DataTerminalTheme.HOVER,
            text_color=DataTerminalTheme.BACKGROUND,
            width=100,
            height=32,
            command=self.manual_refresh,
        )
        self.refresh_button.grid(row=0, column=0, padx=15, pady=15, sticky="w")

        # Status and controls frame
        status_frame = ctk.CTkFrame(self.refresh_frame, fg_color="transparent")
        status_frame.grid(row=0, column=1, padx=15, pady=15, sticky="ew")
        status_frame.grid_columnconfigure(0, weight=1)

        # Last refresh time
        self.last_refresh_label = ctk.CTkLabel(
            status_frame,
            text="Last updated: Never",
            font=ctk.CTkFont(size=11),
            text_color=DataTerminalTheme.TEXT_SECONDARY,
        )
        self.last_refresh_label.grid(row=0, column=0, sticky="w")

        # Next refresh countdown
        self.next_refresh_label = ctk.CTkLabel(
            status_frame,
            text="Next update: --:--",
            font=ctk.CTkFont(size=11),
            text_color=DataTerminalTheme.TEXT_SECONDARY,
        )
        self.next_refresh_label.grid(row=1, column=0, sticky="w")

        # Auto-refresh toggle
        self.auto_refresh_switch = ctk.CTkSwitch(
            self.refresh_frame,
            text="Auto-refresh",
            font=ctk.CTkFont(size=11),
            text_color=DataTerminalTheme.TEXT,
            fg_color=DataTerminalTheme.BORDER,
            progress_color=DataTerminalTheme.PRIMARY,
            button_color=DataTerminalTheme.TEXT,
            button_hover_color=DataTerminalTheme.PRIMARY,
            command=self.toggle_auto_refresh,
        )
        self.auto_refresh_switch.grid(row=0, column=2, padx=15, pady=15, sticky="e")
        self.auto_refresh_switch.select()  # Start enabled

        # Refresh interval selector
        self.interval_frame = ctk.CTkFrame(self.refresh_frame, fg_color="transparent")
        self.interval_frame.grid(row=0, column=3, padx=(0, 15), pady=15, sticky="e")

        interval_label = ctk.CTkLabel(
            self.interval_frame,
            text="Interval:",
            font=ctk.CTkFont(size=11),
            text_color=DataTerminalTheme.TEXT_SECONDARY,
        )
        interval_label.grid(row=0, column=0, padx=(0, 5))

        self.interval_selector = ctk.CTkOptionMenu(
            self.interval_frame,
            values=["1 min", "5 min", "10 min", "15 min", "30 min"],
            font=ctk.CTkFont(size=11),
            fg_color=DataTerminalTheme.CARD_BG,
            button_color=DataTerminalTheme.PRIMARY,
            button_hover_color=DataTerminalTheme.HOVER,
            text_color=DataTerminalTheme.TEXT,
            dropdown_fg_color=DataTerminalTheme.CARD_BG,
            dropdown_text_color=DataTerminalTheme.TEXT,
            width=80,
            height=28,
            command=self.change_interval,
        )
        self.interval_selector.grid(row=0, column=1)
        self.interval_selector.set("5 min")  # Default

        # Progress bar for refresh countdown
        self.refresh_progress = ctk.CTkProgressBar(
            self.refresh_frame,
            width=200,
            height=4,
            progress_color=DataTerminalTheme.PRIMARY,
            fg_color=DataTerminalTheme.BORDER,
        )
        self.refresh_progress.grid(
            row=1, column=0, columnspan=4, padx=15, pady=(0, 10), sticky="ew"
        )
        self.refresh_progress.set(0)

        # Start countdown update
        self.update_countdown()

    def manual_refresh(self):
        """Trigger manual refresh."""
        self.refresh_button.configure(text="🔄 Refreshing...", state="disabled")

        # Run refresh in thread to avoid blocking UI
        def refresh_thread():
            try:
                # Schedule the refresh callback on the main thread using ui_updater
                if hasattr(self.ui_updater, "schedule_update"):
                    self.ui_updater.schedule_update(self._safe_refresh_callback)
                else:
                    # Fallback to direct after call
                    self.after(0, self._safe_refresh_callback)
                self.last_refresh = datetime.now()
                self.after(0, self._refresh_complete)
            except Exception as e:
                print(f"Refresh error: {e}")
                self.after(0, self._refresh_error)

        threading.Thread(target=refresh_thread, daemon=True).start()

    def _refresh_complete(self):
        """Handle successful refresh completion."""
        self.refresh_button.configure(text="🔄 Refresh", state="normal")
        self.update_last_refresh_display()

    def _refresh_error(self):
        """Handle refresh error."""
        self.refresh_button.configure(text="❌ Error", state="normal")
        # Reset button text after 3 seconds
        self.after(3000, lambda: self.refresh_button.configure(text="🔄 Refresh"))

    def toggle_auto_refresh(self):
        """Toggle auto-refresh on/off."""
        self.auto_refresh_enabled = self.auto_refresh_switch.get()

        if self.auto_refresh_enabled:
            self.start_auto_refresh()
        else:
            self.stop_auto_refresh()

    def change_interval(self, value: str):
        """Change refresh interval."""
        interval_map = {"1 min": 60, "5 min": 300, "10 min": 600, "15 min": 900, "30 min": 1800}

        self.refresh_interval = interval_map.get(value, 300)

        # Restart auto-refresh with new interval
        if self.auto_refresh_enabled:
            self.stop_auto_refresh()
            self.start_auto_refresh()

    def start_auto_refresh(self):
        """Start auto-refresh thread."""
        if self.refresh_thread and self.refresh_thread.is_alive():
            return

        self.stop_refresh.clear()
        self.refresh_thread = threading.Thread(target=self._auto_refresh_loop, daemon=True)
        self.refresh_thread.start()

    def stop_auto_refresh(self):
        """Stop auto-refresh thread."""
        self.stop_refresh.set()
        if self.refresh_thread:
            self.refresh_thread.join(timeout=1)

    def _auto_refresh_loop(self):
        """Auto-refresh loop running in background thread."""
        while not self.stop_refresh.is_set():
            if self.auto_refresh_enabled:
                try:
                    # Schedule the refresh callback on the main thread using ui_updater
                    if hasattr(self.ui_updater, "schedule_update"):
                        self.ui_updater.schedule_update(self._safe_refresh_callback)
                        self.last_refresh = datetime.now()
                        self.ui_updater.schedule_update(self.update_last_refresh_display)
                    else:
                        # Fallback to direct after call
                        self.after(0, self._safe_refresh_callback)
                        self.last_refresh = datetime.now()
                        self.after(0, self.update_last_refresh_display)
                except Exception as e:
                    print(f"Auto-refresh error: {e}")

            # Wait for interval or until stopped
            self.stop_refresh.wait(self.refresh_interval)

    def _safe_refresh_callback(self):
        """Safely execute refresh callback on main thread."""
        try:
            if self.refresh_callback:
                self.refresh_callback()
        except Exception as e:
            print(f"Refresh callback error: {e}")

    def update_countdown(self):
        """Update countdown display and progress bar."""
        if not self.auto_refresh_enabled or not self.last_refresh:
            self.next_refresh_label.configure(text="Auto-refresh disabled")
            self.refresh_progress.set(0)
        else:
            # Calculate time until next refresh
            next_refresh_time = self.last_refresh + timedelta(seconds=self.refresh_interval)
            now = datetime.now()
            time_until_refresh = next_refresh_time - now

            if time_until_refresh.total_seconds() <= 0:
                self.next_refresh_label.configure(text="Refreshing...")
                self.refresh_progress.set(1.0)
            else:
                # Format time remaining
                total_seconds = int(time_until_refresh.total_seconds())
                minutes = total_seconds // 60
                seconds = total_seconds % 60

                self.next_refresh_label.configure(text=f"Next update: {minutes:02d}:{seconds:02d}")

                # Update progress bar
                elapsed = self.refresh_interval - time_until_refresh.total_seconds()
                progress = max(0, min(1, elapsed / self.refresh_interval))
                self.refresh_progress.set(progress)

        # Schedule next update
        self.after(1000, self.update_countdown)

    def update_last_refresh_display(self):
        """Update the last refresh time display."""
        if self.last_refresh:
            time_str = self.last_refresh.strftime("%I:%M:%S %p")
            self.last_refresh_label.configure(text=f"Last updated: {time_str}")
        else:
            self.last_refresh_label.configure(text="Last updated: Never")

    def set_refresh_callback(self, callback: Callable[[], None]):
        """Update the refresh callback function."""
        self.refresh_callback = callback

    def force_refresh(self):
        """Force an immediate refresh (programmatic)."""
        if self.refresh_callback:
            try:
                self.refresh_callback()
                self.last_refresh = datetime.now()
                self.update_last_refresh_display()
            except Exception as e:
                print(f"Force refresh error: {e}")

    def get_refresh_status(self) -> dict:
        """Get current refresh status information."""
        return {
            "auto_refresh_enabled": self.auto_refresh_enabled,
            "refresh_interval": self.refresh_interval,
            "last_refresh": self.last_refresh,
            "is_refreshing": self.refresh_button.cget("state") == "disabled",
        }

    def destroy(self):
        """Clean up when component is destroyed."""
        self.stop_auto_refresh()
        super().destroy()


class LoadingOverlay(ctk.CTkFrame):
    """Loading overlay for weather data fetching."""

    def __init__(self, parent):
        super().__init__(
            parent,
            fg_color=(DataTerminalTheme.BACKGROUND, DataTerminalTheme.BACKGROUND + "CC"),
            corner_radius=0,
        )

        self.loading_active = False
        self.animation_frame = 0

        # Create loading UI
        self._create_loading_ui()

    def _create_loading_ui(self):
        """Create loading animation UI."""
        # Center the loading content
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Loading container
        loading_container = ctk.CTkFrame(
            self,
            fg_color=DataTerminalTheme.CARD_BG,
            corner_radius=12,
            border_color=DataTerminalTheme.PRIMARY,
            border_width=2,
            width=300,
            height=150,
        )
        loading_container.grid(row=0, column=0)
        loading_container.grid_propagate(False)

        # Loading spinner
        self.spinner_label = ctk.CTkLabel(loading_container, text="⏳", font=ctk.CTkFont(size=48))
        self.spinner_label.grid(row=0, column=0, pady=(30, 10))

        # Loading text
        self.loading_text = ctk.CTkLabel(
            loading_container,
            text="Loading weather data...",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=DataTerminalTheme.PRIMARY,
        )
        self.loading_text.grid(row=1, column=0, pady=(0, 10))

        # Progress indicator
        self.progress_text = ctk.CTkLabel(
            loading_container,
            text="Fetching current conditions",
            font=ctk.CTkFont(size=12),
            text_color=DataTerminalTheme.TEXT_SECONDARY,
        )
        self.progress_text.grid(row=2, column=0, pady=(0, 20))

    def show_loading(self, message: str = "Loading weather data..."):
        """Show loading overlay with message."""
        self.loading_text.configure(text=message)
        self.loading_active = True
        self.place(relx=0, rely=0, relwidth=1, relheight=1)
        self.lift()
        self._animate_spinner()

    def hide_loading(self):
        """Hide loading overlay."""
        self.loading_active = False
        self.place_forget()

    def update_progress(self, message: str):
        """Update progress message."""
        if self.loading_active:
            self.progress_text.configure(text=message)

    def _animate_spinner(self):
        """Animate the loading spinner."""
        if not self.loading_active:
            return

        # Spinner animation frames
        spinner_frames = ["⏳", "⌛", "⏳", "⌛"]

        self.spinner_label.configure(
            text=spinner_frames[self.animation_frame % len(spinner_frames)]
        )
        self.animation_frame += 1

        # Schedule next frame
        self.after(500, self._animate_spinner)


class ErrorDisplay(ctk.CTkFrame):
    """Error display component for weather data failures."""

    def __init__(self, parent, retry_callback: Callable[[], None]):
        super().__init__(
            parent,
            fg_color=DataTerminalTheme.CARD_BG,
            corner_radius=12,
            border_color="#FF6B6B",
            border_width=2,
        )

        self.retry_callback = retry_callback

        # Create error UI
        self._create_error_ui()

    def _create_error_ui(self):
        """Create error display UI."""
        # Error icon
        error_icon = ctk.CTkLabel(self, text="❌", font=ctk.CTkFont(size=48))
        error_icon.grid(row=0, column=0, pady=(20, 10))

        # Error title
        self.error_title = ctk.CTkLabel(
            self,
            text="Failed to load weather data",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color="#FF6B6B",
        )
        self.error_title.grid(row=1, column=0, pady=(0, 10))

        # Error message
        self.error_message = ctk.CTkLabel(
            self,
            text="Please check your internet connection and try again.",
            font=ctk.CTkFont(size=12),
            text_color=DataTerminalTheme.TEXT_SECONDARY,
            wraplength=300,
        )
        self.error_message.grid(row=2, column=0, pady=(0, 20))

        # Retry button
        retry_button = ctk.CTkButton(
            self,
            text="🔄 Retry",
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color=DataTerminalTheme.PRIMARY,
            hover_color=DataTerminalTheme.HOVER,
            text_color=DataTerminalTheme.BACKGROUND,
            width=120,
            height=36,
            command=self.retry_callback,
        )
        retry_button.grid(row=3, column=0, pady=(0, 20))

    def show_error(self, title: str, message: str):
        """Show error with custom title and message."""
        self.error_title.configure(text=title)
        self.error_message.configure(text=message)
        self.place(relx=0.5, rely=0.5, anchor="center")
        self.lift()

    def hide_error(self):
        """Hide error display."""
        self.place_forget()
