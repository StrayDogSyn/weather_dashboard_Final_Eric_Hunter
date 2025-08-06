from datetime import datetime

from src.ui.styles.layout_styles import LayoutStyles
import customtkinter as ctk

class StatusBarComponent(ctk.CTkFrame):
    """Professional status bar component with status, connection, and time display."""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.is_destroyed = False
        self.scheduled_calls = []
        self.status_label = None
        self.connection_label = None
        self.time_label = None
        self._setup_status_bar()
        self._start_time_update()

    def _setup_status_bar(self):
        """Setup the status bar with status, connection, and time displays."""
        # Configure grid
        self.grid_columnconfigure(1, weight=1)

        # Status section (left)
        status_frame = ctk.CTkFrame(self, fg_color="transparent")
        status_frame.grid(row=0, column=0, sticky="w", padx=LayoutStyles.PADDING["small"])

        self.status_label = ctk.CTkLabel(
            status_frame, text="Ready", font=ctk.CTkFont(size=11), text_color=("#6b7280", "#9ca3af")
        )
        self.status_label.pack(side="left", padx=(0, LayoutStyles.SPACING["normal"]))

        # Connection indicator
        self.connection_label = ctk.CTkLabel(
            status_frame,
            text="🟢 Connected",
            font=ctk.CTkFont(size=11),
            text_color=("#10b981", "#34d399"),
        )
        self.connection_label.pack(side="left")

        # Time section (right)
        time_frame = ctk.CTkFrame(self, fg_color="transparent")
        time_frame.grid(row=0, column=2, sticky="e", padx=LayoutStyles.PADDING["small"])

        self.time_label = ctk.CTkLabel(
            time_frame,
            text=self._get_current_time(),
            font=ctk.CTkFont(size=11),
            text_color=("#6b7280", "#9ca3af"),
        )
        self.time_label.pack(side="right")

    def _get_current_time(self):
        """Get formatted current time."""
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def _start_time_update(self):
        """Start the time update loop."""
        self._update_time()

    def _update_time(self):
        """Update time display."""
        try:
            if self.is_destroyed or not self.winfo_exists():
                return

            current_time = self._get_current_time()
            if self.time_label:
                self.time_label.configure(text=current_time)

            # Schedule next update
            call_id = self.safe_after(1000, self._update_time)
            if call_id:
                self.scheduled_calls.append(call_id)

        except tk.TclError:
            # Widget has been destroyed, stop the timer
            return

    def safe_after(self, delay, callback):
        """Safely schedule a callback, handling widget destruction."""
        try:
            if not self.is_destroyed and self.winfo_exists():
                return self.after(delay, callback)
        except tk.TclError:
            pass
        return None

    def update_status(self, status_text, status_type="info"):
        """Update the status display.

        Args:
            status_text (str): The status message to display
            status_type (str): Type of status - 'info', 'success', 'warning', 'error'
        """
        if not self.status_label:
            return

        # Color mapping for different status types
        colors = {
            "info": ("#6b7280", "#9ca3af"),
            "success": ("#10b981", "#34d399"),
            "warning": ("#f59e0b", "#fbbf24"),
            "error": ("#ef4444", "#f87171"),
        }

        color = colors.get(status_type, colors["info"])
        self.status_label.configure(text=status_text, text_color=color)

    def update_connection_status(self, is_connected, message=""):
        """Update the connection status display.

        Args:
            is_connected (bool): Whether the connection is active
            message (str): Optional custom message
        """
        if not self.connection_label:
            return

        if is_connected:
            text = f"🟢 {message}" if message else "🟢 Connected"
            color = ("#10b981", "#34d399")
        else:
            text = f"🔴 {message}" if message else "🔴 Disconnected"
            color = ("#ef4444", "#f87171")

        self.connection_label.configure(text=text, text_color=color)

    def show_loading(self, message="Loading..."):
        """Show loading status."""
        self.update_status(f"⏳ {message}", "info")

    def show_success(self, message="Operation completed"):
        """Show success status."""
        self.update_status(f"✅ {message}", "success")

    def show_error(self, message="An error occurred"):
        """Show error status."""
        self.update_status(f"❌ {message}", "error")

    def show_warning(self, message="Warning"):
        """Show warning status."""
        self.update_status(f"⚠️ {message}", "warning")

    def clear_status(self):
        """Clear the status display."""
        self.update_status("Ready", "info")

    def cleanup(self):
        """Clean up scheduled callbacks."""
        self.is_destroyed = True

        # Cancel all scheduled calls
        for call_id in self.scheduled_calls:
            try:
                self.after_cancel(call_id)
            except (tk.TclError, ValueError):
                pass

        self.scheduled_calls.clear()

    def destroy(self):
        """Override destroy to ensure cleanup."""
        self.cleanup()
        super().destroy()
