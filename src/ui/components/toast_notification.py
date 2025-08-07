#!/usr/bin/env python3
"""
Toast Notification System for Weather Dashboard
Provides user-friendly notifications with different types and auto-dismiss functionality.
"""

import logging
import threading
import time
import tkinter as tk
from dataclasses import dataclass
from enum import Enum
from typing import Callable, Optional

class ToastType(Enum):
    """Types of toast notifications."""

    SUCCESS = "success"
    ERROR = "error"
    INFO = "info"
    WARNING = "warning"

@dataclass
class ToastConfig:
    """Configuration for toast notifications."""

    type: ToastType
    message: str
    duration: Optional[float] = None  # None means persistent
    action_text: Optional[str] = None
    action_callback: Optional[Callable] = None
    dismissible: bool = True

class ToastNotification:
    """Individual toast notification widget."""

    def __init__(
        self,
        parent: tk.Widget,
        config: ToastConfig,
        on_dismiss: Callable[["ToastNotification"], None],
    ):
        self.parent = parent
        self.config = config
        self.on_dismiss = on_dismiss
        self.logger = logging.getLogger(__name__)

        # Create the toast frame
        self.frame = tk.Frame(parent, relief="raised", bd=1)
        self._setup_styling()
        self._create_widgets()

        # Auto-dismiss timer
        self.dismiss_timer = None
        if config.duration:
            self._start_dismiss_timer()

    def _setup_styling(self):
        """Setup styling based on toast type."""
        colors = {
            ToastType.SUCCESS: {"bg": "#28a745", "fg": "#ffffff", "border": "#1e7e34"},
            ToastType.ERROR: {"bg": "#dc3545", "fg": "#ffffff", "border": "#bd2130"},
            ToastType.INFO: {"bg": "#17a2b8", "fg": "#ffffff", "border": "#117a8b"},
            ToastType.WARNING: {"bg": "#ffc107", "fg": "#212529", "border": "#e0a800"},
        }

        style = colors[self.config.type]
        self.frame.configure(
            bg=style["bg"], highlightbackground=style["border"], highlightthickness=2,
            relief="raised", bd=2
        )
        self.colors = style

    def _create_widgets(self):
        """Create the toast widgets."""
        # Icon based on type
        icons = {
            ToastType.SUCCESS: "✓",
            ToastType.ERROR: "✗",
            ToastType.INFO: "ℹ",
            ToastType.WARNING: "⚠",
        }

        # Icon label
        icon_label = tk.Label(
            self.frame,
            text=icons[self.config.type],
            font=("Arial", 12, "bold"),
            bg=self.colors["bg"],
            fg=self.colors["fg"],
        )
        icon_label.pack(side="left", padx=(8, 4), pady=8)

        # Message label
        message_label = tk.Label(
            self.frame,
            text=self.config.message,
            font=("Arial", 9),
            bg=self.colors["bg"],
            fg=self.colors["fg"],
            wraplength=250,
            justify="left",
        )
        message_label.pack(side="left", padx=(0, 8), pady=8, fill="x", expand=True)

        # Action button (if provided)
        if self.config.action_text and self.config.action_callback:
            action_btn = tk.Button(
                self.frame,
                text=self.config.action_text,
                font=("Arial", 8),
                bg=self.colors["fg"],
                fg=self.colors["bg"],
                relief="flat",
                padx=8,
                pady=2,
                command=self._handle_action,
            )
            action_btn.pack(side="right", padx=(4, 8), pady=8)

        # Dismiss button (if dismissible)
        if self.config.dismissible:
            dismiss_btn = tk.Button(
                self.frame,
                text="×",
                font=("Arial", 12, "bold"),
                bg=self.colors["bg"],
                fg=self.colors["fg"],
                relief="flat",
                padx=4,
                pady=0,
                command=self.dismiss,
            )
            dismiss_btn.pack(side="right", padx=(0, 4), pady=8)

    def _handle_action(self):
        """Handle action button click."""
        try:
            if self.config.action_callback:
                self.config.action_callback()
        except Exception as e:
            self.logger.error(f"Error in toast action callback: {e}")
        finally:
            self.dismiss()

    def _start_dismiss_timer(self):
        """Start the auto-dismiss timer."""

        def dismiss_after_delay():
            time.sleep(self.config.duration)
            try:
                self.parent.after(0, self.dismiss)
            except tk.TclError:
                pass  # Widget may have been destroyed

        self.dismiss_timer = threading.Thread(target=dismiss_after_delay, daemon=True)
        self.dismiss_timer.start()

    def dismiss(self):
        """Dismiss the toast notification."""
        try:
            if self.dismiss_timer and self.dismiss_timer.is_alive():
                # Timer will handle dismissal
                pass

            self.frame.destroy()
            self.on_dismiss(self)
        except tk.TclError:
            pass  # Widget already destroyed

class ToastManager:
    """Manages multiple toast notifications."""

    def __init__(self, parent: tk.Widget):
        self.parent = parent
        self.toasts = []
        self.logger = logging.getLogger(__name__)

        # Create container for toasts
        self.container = tk.Frame(parent)
        # Position toasts in top-center for better visibility
        self.container.place(relx=0.5, rely=0.0, anchor="n", x=0, y=60)

        # Default durations
        self.default_durations = {
            ToastType.SUCCESS: 3.0,
            ToastType.ERROR: None,  # Persistent
            ToastType.INFO: 5.0,
            ToastType.WARNING: 5.0,
        }

    def show_toast(
        self,
        toast_type: ToastType,
        message: str,
        duration: Optional[float] = None,
        action_text: Optional[str] = None,
        action_callback: Optional[Callable] = None,
        dismissible: bool = True,
    ) -> ToastNotification:
        """Show a toast notification."""
        # Use default duration if not specified
        if duration is None:
            duration = self.default_durations.get(toast_type)

        config = ToastConfig(
            type=toast_type,
            message=message,
            duration=duration,
            action_text=action_text,
            action_callback=action_callback,
            dismissible=dismissible,
        )

        toast = ToastNotification(self.container, config, self._on_toast_dismissed)
        self.toasts.append(toast)

        # Position the toast
        self._reposition_toasts()

        return toast

    def show_success(self, message: str, duration: float = 3.0) -> ToastNotification:
        """Show a success toast."""
        return self.show_toast(ToastType.SUCCESS, message, duration)

    def show_error(
        self, message: str, action_text: str = None, action_callback: Callable = None
    ) -> ToastNotification:
        """Show an error toast (persistent by default)."""
        return self.show_toast(
            ToastType.ERROR, message, action_text=action_text, action_callback=action_callback
        )

    def show_info(self, message: str, duration: float = 5.0) -> ToastNotification:
        """Show an info toast."""
        return self.show_toast(ToastType.INFO, message, duration)

    def show_warning(self, message: str, duration: float = 5.0) -> ToastNotification:
        """Show a warning toast."""
        return self.show_toast(ToastType.WARNING, message, duration)

    def _on_toast_dismissed(self, toast: ToastNotification):
        """Handle toast dismissal."""
        if toast in self.toasts:
            self.toasts.remove(toast)
            self._reposition_toasts()

    def _reposition_toasts(self):
        """Reposition all toasts vertically."""
        y_offset = 0
        for toast in self.toasts:
            try:
                toast.frame.pack(fill="x", pady=(0, 8))
                y_offset += toast.frame.winfo_reqheight() + 8
            except tk.TclError:
                pass  # Toast may have been destroyed

    def clear_all(self):
        """Clear all toast notifications."""
        for toast in self.toasts.copy():
            toast.dismiss()

    def clear_type(self, toast_type: ToastType):
        """Clear all toasts of a specific type."""
        for toast in self.toasts.copy():
            if toast.config.type == toast_type:
                toast.dismiss()
