"""Status Bar Component

Displays application status, connection state, and system information.
"""

import customtkinter as ctk
import tkinter as tk
from datetime import datetime
from typing import Optional, Dict, Any
import threading
import time

from ui.theme import DataTerminalTheme
from utils.formatters import format_file_size


class StatusIndicator(ctk.CTkFrame):
    """Individual status indicator with icon and text."""
    
    STATUS_COLORS = {
        "online": DataTerminalTheme.SUCCESS,
        "offline": DataTerminalTheme.ERROR,
        "warning": DataTerminalTheme.WARNING,
        "loading": DataTerminalTheme.PRIMARY,
        "idle": DataTerminalTheme.TEXT_SECONDARY
    }
    
    STATUS_SYMBOLS = {
        "online": "●",
        "offline": "●",
        "warning": "⚠",
        "loading": "◐",
        "idle": "○"
    }
    
    def __init__(self, parent, label: str, status: str = "idle", **kwargs):
        """Initialize status indicator."""
        super().__init__(parent, **kwargs)
        
        self.label_text = label
        self.current_status = status
        
        # Configure frame
        self.configure(
            fg_color="transparent",
            height=25
        )
        
        # Create widgets
        self._create_widgets()
        self._setup_layout()
        self._update_display()
    
    def _create_widgets(self) -> None:
        """Create indicator widgets."""
        # Status icon
        self.status_icon = ctk.CTkLabel(
            self,
            text=self.STATUS_SYMBOLS[self.current_status],
            font=(DataTerminalTheme.FONT_FAMILY, 12, "bold"),
            text_color=self.STATUS_COLORS[self.current_status],
            width=20
        )
        
        # Status label
        self.status_label = ctk.CTkLabel(
            self,
            text=self.label_text,
            font=(DataTerminalTheme.FONT_FAMILY, 10),
            text_color=DataTerminalTheme.TEXT_SECONDARY
        )
    
    def _setup_layout(self) -> None:
        """Arrange widgets."""
        self.status_icon.pack(side="left", padx=(0, 5))
        self.status_label.pack(side="left")
    
    def _update_display(self) -> None:
        """Update visual display based on current status."""
        color = self.STATUS_COLORS.get(self.current_status, DataTerminalTheme.TEXT_SECONDARY)
        symbol = self.STATUS_SYMBOLS.get(self.current_status, "○")
        
        self.status_icon.configure(
            text=symbol,
            text_color=color
        )
    
    def set_status(self, status: str) -> None:
        """Update status."""
        if status in self.STATUS_COLORS:
            self.current_status = status
            self._update_display()
    
    def set_label(self, label: str) -> None:
        """Update label text."""
        self.label_text = label
        self.status_label.configure(text=label)


class StatusBarFrame(ctk.CTkFrame):
    """Main status bar component."""
    
    def __init__(self, parent, **kwargs):
        """Initialize status bar."""
        super().__init__(parent, **kwargs)
        
        # Configure frame
        self.configure(
            **DataTerminalTheme.get_frame_style("accent"),
            height=35
        )
        
        # Status tracking
        self.status_data: Dict[str, Any] = {
            "api_status": "idle",
            "last_update": None,
            "request_count": 0,
            "cache_size": 0,
            "app_status": "ready"
        }
        
        # Clock update thread
        self.clock_running = False
        self.clock_thread: Optional[threading.Thread] = None
        
        # Create widgets
        self._create_widgets()
        self._setup_layout()
        
        # Start clock
        self.start_clock()
    
    def _create_widgets(self) -> None:
        """Create status bar widgets."""
        # Left section - API status
        self.left_frame = ctk.CTkFrame(
            self,
            fg_color="transparent"
        )
        
        self.api_indicator = StatusIndicator(
            self.left_frame,
            label="API: Ready",
            status="idle"
        )
        
        # Separator
        self.separator1 = ctk.CTkLabel(
            self.left_frame,
            text="|",
            font=(DataTerminalTheme.FONT_FAMILY, 10),
            text_color=DataTerminalTheme.ACCENT,
            width=10
        )
        
        # Request counter
        self.request_indicator = StatusIndicator(
            self.left_frame,
            label="Requests: 0",
            status="idle"
        )
        
        # Center section - Application status
        self.center_frame = ctk.CTkFrame(
            self,
            fg_color="transparent"
        )
        
        self.app_status_label = ctk.CTkLabel(
            self.center_frame,
            text="Weather Dashboard Ready",
            font=(DataTerminalTheme.FONT_FAMILY, 10, "bold"),
            text_color=DataTerminalTheme.TEXT_PRIMARY
        )
        
        # Right section - System info
        self.right_frame = ctk.CTkFrame(
            self,
            fg_color="transparent"
        )
        
        # Last update time
        self.update_time_label = ctk.CTkLabel(
            self.right_frame,
            text="Last Update: Never",
            font=(DataTerminalTheme.FONT_FAMILY, 9),
            text_color=DataTerminalTheme.TEXT_SECONDARY
        )
        
        # Separator
        self.separator2 = ctk.CTkLabel(
            self.right_frame,
            text="|",
            font=(DataTerminalTheme.FONT_FAMILY, 10),
            text_color=DataTerminalTheme.ACCENT,
            width=10
        )
        
        # Current time
        self.clock_label = ctk.CTkLabel(
            self.right_frame,
            text=datetime.now().strftime("%H:%M:%S"),
            font=(DataTerminalTheme.FONT_FAMILY, 10, "bold"),
            text_color=DataTerminalTheme.PRIMARY
        )
    
    def _setup_layout(self) -> None:
        """Arrange widgets."""
        # Configure main grid
        self.grid_columnconfigure(1, weight=1)  # Center expands
        
        # Pack main sections
        self.left_frame.grid(row=0, column=0, sticky="w", padx=(10, 0), pady=5)
        self.center_frame.grid(row=0, column=1, sticky="ew", pady=5)
        self.right_frame.grid(row=0, column=2, sticky="e", padx=(0, 10), pady=5)
        
        # Left section layout
        self.api_indicator.pack(side="left", padx=(0, 10))
        self.separator1.pack(side="left", padx=(0, 10))
        self.request_indicator.pack(side="left")
        
        # Center section layout
        self.app_status_label.pack(expand=True)
        
        # Right section layout
        self.update_time_label.pack(side="left", padx=(0, 10))
        self.separator2.pack(side="left", padx=(0, 10))
        self.clock_label.pack(side="left")
    
    def start_clock(self) -> None:
        """Start the clock update thread."""
        if self.clock_running:
            return
        
        self.clock_running = True
        self.clock_thread = threading.Thread(
            target=self._update_clock,
            daemon=True
        )
        self.clock_thread.start()
    
    def stop_clock(self) -> None:
        """Stop the clock update thread."""
        self.clock_running = False
    
    def _update_clock(self) -> None:
        """Update clock display every second."""
        while self.clock_running:
            try:
                current_time = datetime.now().strftime("%H:%M:%S")
                self.after(0, lambda: self.clock_label.configure(text=current_time))
                time.sleep(1)
            except tk.TclError:
                # Widget destroyed
                break
    
    def set_api_status(self, status: str, message: str = "") -> None:
        """Update API status."""
        self.status_data["api_status"] = status
        
        if message:
            label_text = f"API: {message}"
        else:
            status_messages = {
                "online": "Connected",
                "offline": "Disconnected",
                "loading": "Requesting...",
                "warning": "Limited",
                "idle": "Ready"
            }
            label_text = f"API: {status_messages.get(status, 'Unknown')}"
        
        self.api_indicator.set_status(status)
        self.api_indicator.set_label(label_text)
    
    def set_app_status(self, message: str) -> None:
        """Update application status message."""
        self.status_data["app_status"] = message
        self.app_status_label.configure(text=message)
    
    def increment_request_count(self) -> None:
        """Increment API request counter."""
        self.status_data["request_count"] += 1
        count = self.status_data["request_count"]
        
        self.request_indicator.set_label(f"Requests: {count}")
        
        # Update last update time
        self.status_data["last_update"] = datetime.now()
        update_time = self.status_data["last_update"].strftime("%H:%M:%S")
        self.update_time_label.configure(text=f"Last Update: {update_time}")
    
    def set_cache_info(self, size: int) -> None:
        """Update cache information."""
        self.status_data["cache_size"] = size
        # Could add cache indicator if needed
    
    def show_temporary_message(self, message: str, duration: int = 3000) -> None:
        """Show temporary status message."""
        original_message = self.app_status_label.cget("text")
        
        # Show temporary message
        self.app_status_label.configure(
            text=message,
            text_color=DataTerminalTheme.PRIMARY
        )
        
        # Restore original message after duration
        def restore_message():
            self.app_status_label.configure(
                text=original_message,
                text_color=DataTerminalTheme.TEXT_PRIMARY
            )
        
        self.after(duration, restore_message)
    
    def show_error_message(self, message: str, duration: int = 5000) -> None:
        """Show error message."""
        original_message = self.app_status_label.cget("text")
        
        # Show error message
        self.app_status_label.configure(
            text=f"Error: {message}",
            text_color=DataTerminalTheme.ERROR
        )
        
        # Restore original message after duration
        def restore_message():
            self.app_status_label.configure(
                text=original_message,
                text_color=DataTerminalTheme.TEXT_PRIMARY
            )
        
        self.after(duration, restore_message)
    
    def get_status_info(self) -> Dict[str, Any]:
        """Get current status information."""
        return self.status_data.copy()
    
    def destroy(self) -> None:
        """Clean up resources."""
        self.stop_clock()
        super().destroy()


class CompactStatusBar(ctk.CTkFrame):
    """Compact version of status bar for smaller interfaces."""
    
    def __init__(self, parent, **kwargs):
        """Initialize compact status bar."""
        super().__init__(parent, **kwargs)
        
        # Configure frame
        self.configure(
            **DataTerminalTheme.get_frame_style("accent"),
            height=25
        )
        
        # Create widgets
        self._create_widgets()
        self._setup_layout()
    
    def _create_widgets(self) -> None:
        """Create compact status widgets."""
        # Status indicator
        self.status_indicator = StatusIndicator(
            self,
            label="Ready",
            status="idle"
        )
        
        # Spacer
        self.spacer = ctk.CTkFrame(
            self,
            fg_color="transparent"
        )
        
        # Clock
        self.clock_label = ctk.CTkLabel(
            self,
            text=datetime.now().strftime("%H:%M"),
            font=(DataTerminalTheme.FONT_FAMILY, 9),
            text_color=DataTerminalTheme.TEXT_SECONDARY
        )
    
    def _setup_layout(self) -> None:
        """Arrange compact widgets."""
        self.grid_columnconfigure(1, weight=1)
        
        self.status_indicator.grid(row=0, column=0, sticky="w", padx=(10, 0))
        self.spacer.grid(row=0, column=1, sticky="ew")
        self.clock_label.grid(row=0, column=2, sticky="e", padx=(0, 10))
    
    def set_status(self, status: str, message: str) -> None:
        """Update status."""
        self.status_indicator.set_status(status)
        self.status_indicator.set_label(message)
    
    def update_clock(self) -> None:
        """Update clock display."""
        current_time = datetime.now().strftime("%H:%M")
        self.clock_label.configure(text=current_time)