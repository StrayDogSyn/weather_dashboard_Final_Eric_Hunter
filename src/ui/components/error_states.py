#!/usr/bin/env python3
"""
Error State Components for Weather Dashboard
Provides visual error states for different scenarios with user-friendly interfaces.

NOTE: Most error display functionality has been moved to:
- src/ui/components/common/error_display.py (ErrorDisplay, InlineErrorDisplay)
- src/ui/components/common/loading_spinner.py (LoadingSpinner, ShimmerLoader)

This file maintains legacy components for backward compatibility.
"""

import logging
import socket
import threading
import tkinter as tk
import time
from enum import Enum
from typing import Callable, Optional

from ..theme_manager import theme_manager
from .common.error_display import ErrorDisplay, InlineErrorDisplay
from .common.loading_spinner import LoadingSpinner, ShimmerLoader


class NetworkStatus(Enum):
    """Network connectivity status."""

    ONLINE = "online"
    OFFLINE = "offline"
    CHECKING = "checking"


class ErrorStateComponent:
    """Base class for error state components."""

    def __init__(self, parent: tk.Widget):
        self.parent = parent
        self.logger = logging.getLogger(__name__)
        self.frame = None
        self.is_visible = False

    def show(self):
        """Show the error state."""
        if not self.is_visible:
            self._create_frame()
            self.is_visible = True

    def hide(self):
        """Hide the error state."""
        if self.is_visible and self.frame:
            self.frame.destroy()
            self.frame = None
            self.is_visible = False

    def _create_frame(self):
        """Create the error state frame. Override in subclasses."""


class OfflineIndicator(ErrorStateComponent):
    """Shows offline status with cached data indicator."""

    def __init__(self, parent: tk.Widget, cached_data_available: bool = True):
        super().__init__(parent)
        self.cached_data_available = cached_data_available
        self.network_status = NetworkStatus.CHECKING
        self._start_network_monitoring()

    def _create_frame(self):
        """Create the offline indicator frame."""
        # Get current theme colors
        current_theme = theme_manager.get_current_theme()
        warning_bg = current_theme.get("WARNING", "#ffc107")
        warning_text = current_theme.get("BACKGROUND", "#2b2b2b")

        self.frame = tk.Frame(self.parent, bg=warning_bg, relief="solid", bd=1)
        self.frame.pack(fill="x", padx=5, pady=2)

        # Offline icon
        icon_label = tk.Label(
            self.frame, text="📡", font=("Arial", 12), bg=warning_bg, fg=warning_text
        )
        icon_label.pack(side="left", padx=(8, 4), pady=4)

        # Status message
        if self.cached_data_available:
            message = "You're offline. Showing cached data."
        else:
            message = "You're offline. Some features may be unavailable."

        status_label = tk.Label(
            self.frame, text=message, font=("Arial", 9), bg=warning_bg, fg=warning_text
        )
        status_label.pack(side="left", padx=(0, 8), pady=4)

        # Retry button
        retry_btn = tk.Button(
            self.frame,
            text="Check Connection",
            font=("Arial", 8),
            bg=warning_text,
            fg=warning_bg,
            relief="flat",
            padx=8,
            pady=2,
            command=self._check_network,
        )
        retry_btn.pack(side="right", padx=(4, 8), pady=4)

    def _start_network_monitoring(self):
        """Start monitoring network connectivity."""

        def monitor_network():
            while True:
                try:
                    old_status = self.network_status
                    self.network_status = self._check_connectivity()

                    if old_status != self.network_status:
                        self.parent.after(0, self._update_visibility)

                    time.sleep(30)  # Check every 30 seconds
                except Exception as e:
                    self.logger.error(f"Network monitoring error: {e}")
                    time.sleep(60)  # Wait longer on error

        monitor_thread = threading.Thread(target=monitor_network, daemon=True)
        monitor_thread.start()

    def _check_connectivity(self) -> NetworkStatus:
        """Check network connectivity."""
        try:
            # Try to connect to a reliable host
            socket.create_connection(("8.8.8.8", 53), timeout=3)
            return NetworkStatus.ONLINE
        except (socket.error, OSError):
            return NetworkStatus.OFFLINE

    def _check_network(self):
        """Manual network check triggered by user."""

        def check_async():
            self.network_status = NetworkStatus.CHECKING
            self.parent.after(0, self._update_visibility)

            self.network_status = self._check_connectivity()
            self.parent.after(0, self._update_visibility)

        threading.Thread(target=check_async, daemon=True).start()

    def _update_visibility(self):
        """Update visibility based on network status."""
        if self.network_status == NetworkStatus.OFFLINE:
            self.show()
        else:
            self.hide()


class APIErrorDisplay(ErrorStateComponent):
    """Shows API error with retry functionality."""

    def __init__(
        self, parent: tk.Widget, error_message: str, retry_callback: Optional[Callable] = None
    ):
        super().__init__(parent)
        self.error_message = error_message
        self.retry_callback = retry_callback
        self.retry_count = 0
        self.max_retries = 3

    def _create_frame(self):
        """Create the API error frame."""
        # Get current theme colors
        current_theme = theme_manager.get_current_theme()
        error_bg = current_theme.get("ERROR", "#dc3545")
        bg_color = current_theme.get("BACKGROUND", "#2b2b2b")
        text_color = current_theme.get("TEXT", "#ffffff")

        self.frame = tk.Frame(self.parent, bg=bg_color, relief="solid", bd=1)
        self.frame.pack(fill="both", expand=True, padx=5, pady=5)

        # Error icon
        icon_label = tk.Label(self.frame, text="⚠️", font=("Arial", 24), bg=bg_color, fg=error_bg)
        icon_label.pack(pady=(20, 10))

        # Error title
        title_label = tk.Label(
            self.frame,
            text="Oops! Something went wrong",
            font=("Arial", 14, "bold"),
            bg=bg_color,
            fg=text_color,
        )
        title_label.pack(pady=(0, 10))

        # Error message
        message_label = tk.Label(
            self.frame,
            text=self._get_user_friendly_message(),
            font=("Arial", 10),
            bg=bg_color,
            fg=text_color,
            wraplength=300,
            justify="center",
        )
        message_label.pack(pady=(0, 20))

        # Action buttons
        button_frame = tk.Frame(self.frame, bg=bg_color)
        button_frame.pack(pady=(0, 20))

        if self.retry_callback and self.retry_count < self.max_retries:
            retry_btn = tk.Button(
                button_frame,
                text=f"Try Again ({self.max_retries - self.retry_count} left)",
                font=("Arial", 10),
                bg=error_bg,
                fg=text_color,
                relief="flat",
                padx=15,
                pady=5,
                command=self._handle_retry,
            )
            retry_btn.pack(side="left", padx=(0, 10))

        dismiss_btn = tk.Button(
            button_frame,
            text="Dismiss",
            font=("Arial", 10),
            bg=current_theme.get("SECONDARY", "#6c757d"),
            fg=text_color,
            relief="flat",
            padx=15,
            pady=5,
            command=self.hide,
        )
        dismiss_btn.pack(side="left")

    def _get_user_friendly_message(self) -> str:
        """Convert technical error to user-friendly message."""
        error_lower = self.error_message.lower()

        if "timeout" in error_lower or "connection" in error_lower:
            return "We're having trouble connecting to our servers. Please check your internet connection and try again."
        elif "api key" in error_lower or "unauthorized" in error_lower:
            return "There's an issue with our weather service. We're working to fix it."
        elif "rate limit" in error_lower or "too many requests" in error_lower:
            return (
                "We're receiving a lot of requests right now. Please wait a moment and try again."
            )
        elif "not found" in error_lower:
            return (
                "We couldn't find weather data for this location. Please try a different location."
            )
        else:
            return "We encountered an unexpected error. Please try again in a few moments."

    def _handle_retry(self):
        """Handle retry button click."""
        self.retry_count += 1
        self.hide()

        if self.retry_callback:
            try:
                self.retry_callback()
            except Exception as e:
                self.logger.error(f"Retry callback error: {e}")
                # Show error again if retry fails
                self.parent.after(1000, self.show)


# LoadingState class moved to src/ui/components/common/loading_spinner.py
# Use LoadingSpinner or ShimmerLoader components instead
class LoadingState(ErrorStateComponent):
    """Legacy loading state - use LoadingSpinner instead."""
    
    def __init__(self, parent, message: str = "Loading...", show_progress: bool = False):
        super().__init__(parent)
        self.spinner = LoadingSpinner(parent, text=message)
        
    def show(self):
        self.spinner.start()
        
    def hide(self):
        self.spinner.stop()
        
    def update_progress(self, value: float, message: str = None):
        if message:
            self.spinner.set_text(message)


# InputValidationError class moved to src/ui/components/common/error_display.py
# Use InlineErrorDisplay component instead
class InputValidationError(ErrorStateComponent):
    """Legacy validation error - use InlineErrorDisplay instead."""
    
    def __init__(self, parent, target_widget, error_message: str, hint: str = None):
        super().__init__(parent)
        message = f"{error_message}. {hint}" if hint else error_message
        self.error_display = InlineErrorDisplay(parent, message, "error")
        
    def show(self):
        self.error_display.show()
        
    def hide(self):
        self.error_display.hide()


class ErrorStateManager:
    """Manages different error states for a component."""

    def __init__(self, parent: tk.Widget):
        self.parent = parent
        self.active_errors = {}
        self.logger = logging.getLogger(__name__)

    def show_offline(self, cached_data_available: bool = True) -> OfflineIndicator:
        """Show offline indicator."""
        if "offline" not in self.active_errors:
            offline_indicator = OfflineIndicator(self.parent, cached_data_available)
            self.active_errors["offline"] = offline_indicator
        return self.active_errors["offline"]

    def show_api_error(
        self, error_message: str, retry_callback: Callable = None
    ) -> ErrorDisplay:
        """Show API error using new ErrorDisplay component."""
        self.clear_error("api_error")  # Clear existing API error
        api_error = ErrorDisplay(
            self.parent, 
            "API Error", 
            error_message, 
            retry_callback=retry_callback
        )
        api_error.show()
        self.active_errors["api_error"] = api_error
        return api_error

    def show_loading(
        self, message: str = "Loading...", show_progress: bool = False
    ) -> LoadingSpinner:
        """Show loading state using new LoadingSpinner component."""
        self.clear_error("loading")  # Clear existing loading state
        loading_state = LoadingSpinner(self.parent, text=message)
        loading_state.start()
        self.active_errors["loading"] = loading_state
        return loading_state

    def show_validation_error(
        self, target_widget, error_message: str, hint: str = None
    ) -> InlineErrorDisplay:
        """Show input validation error using new InlineErrorDisplay component."""
        error_key = f"validation_{id(target_widget)}"
        self.clear_error(error_key)  # Clear existing validation error

        message = f"{error_message}. {hint}" if hint else error_message
        validation_error = InlineErrorDisplay(self.parent, message, "error")
        validation_error.show()
        self.active_errors[error_key] = validation_error
        return validation_error

    def clear_error(self, error_type: str):
        """Clear a specific error type."""
        if error_type in self.active_errors:
            self.active_errors[error_type].hide()
            del self.active_errors[error_type]

    def clear_all_errors(self):
        """Clear all active errors."""
        for error in list(self.active_errors.values()):
            error.hide()
        self.active_errors.clear()

    def has_error(self, error_type: str) -> bool:
        """Check if a specific error type is active."""
        return error_type in self.active_errors
