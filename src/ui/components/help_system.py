#!/usr/bin/env python3
"""
Contextual Help System for Weather Dashboard
Provides tooltips, onboarding flow, feature discovery, and keyboard shortcuts.
"""

import json
import logging
import os
import threading
import time
import tkinter as tk
from dataclasses import dataclass
from enum import Enum
from typing import Dict, Optional, Tuple

class OnboardingStep(Enum):
    """Onboarding flow steps."""

    WELCOME = "welcome"
    SEARCH_LOCATION = "search_location"
    VIEW_FORECAST = "view_forecast"
    EXPLORE_FEATURES = "explore_features"
    CUSTOMIZE_SETTINGS = "customize_settings"
    COMPLETE = "complete"

@dataclass
class TooltipConfig:
    """Configuration for tooltip."""

    text: str
    delay: float = 0.5
    wrap_length: int = 200
    bg_color: str = "#2c3e50"
    fg_color: str = "white"
    font: Tuple[str, int] = ("Arial", 9)

@dataclass
class OnboardingStepData:
    """Data for an onboarding step."""

    title: str
    description: str
    target_element: Optional[str] = None
    highlight_color: str = "#3498db"
    action_text: str = "Next"
    skip_allowed: bool = True

class ToolTip:
    """Tooltip widget that appears on hover."""

    def __init__(self, widget: tk.Widget, config: TooltipConfig):
        self.widget = widget
        self.config = config
        self.tooltip_window = None
        self.show_timer = None
        self.logger = logging.getLogger(__name__)

        # Bind events
        self.widget.bind("<Enter>", self._on_enter)
        self.widget.bind("<Leave>", self._on_leave)
        self.widget.bind("<Motion>", self._on_motion)

    def _on_enter(self, event):
        """Handle mouse enter event."""
        self._schedule_show()

    def _on_leave(self, event):
        """Handle mouse leave event."""
        self._cancel_show()
        self._hide_tooltip()

    def _on_motion(self, event):
        """Handle mouse motion event."""
        if self.tooltip_window:
            self._update_position(event)

    def _schedule_show(self):
        """Schedule tooltip to show after delay."""
        self._cancel_show()
        self.show_timer = self.widget.after(int(self.config.delay * 1000), self._show_tooltip)

    def _cancel_show(self):
        """Cancel scheduled tooltip show."""
        if self.show_timer:
            self.widget.after_cancel(self.show_timer)
            self.show_timer = None

    def _show_tooltip(self):
        """Show the tooltip."""
        if self.tooltip_window:
            return

        try:
            # Create tooltip window
            self.tooltip_window = tk.Toplevel(self.widget)
            self.tooltip_window.wm_overrideredirect(True)
            self.tooltip_window.wm_attributes("-topmost", True)

            # Create tooltip content
            label = tk.Label(
                self.tooltip_window,
                text=self.config.text,
                background=self.config.bg_color,
                foreground=self.config.fg_color,
                font=self.config.font,
                wraplength=self.config.wrap_length,
                justify="left",
                relief="solid",
                borderwidth=1,
                padx=8,
                pady=4,
            )
            label.pack()

            # Position tooltip
            self._position_tooltip()

        except tk.TclError as e:
            self.logger.error(f"Error showing tooltip: {e}")

    def _hide_tooltip(self):
        """Hide the tooltip."""
        if self.tooltip_window:
            try:
                self.tooltip_window.destroy()
            except tk.TclError:
                pass
            self.tooltip_window = None

    def _position_tooltip(self):
        """Position tooltip near the widget."""
        if not self.tooltip_window:
            return

        try:
            # Get widget position
            x = self.widget.winfo_rootx()
            y = self.widget.winfo_rooty() + self.widget.winfo_height() + 5

            # Adjust if tooltip would go off screen
            screen_width = self.widget.winfo_screenwidth()
            screen_height = self.widget.winfo_screenheight()

            tooltip_width = self.tooltip_window.winfo_reqwidth()
            tooltip_height = self.tooltip_window.winfo_reqheight()

            if x + tooltip_width > screen_width:
                x = screen_width - tooltip_width - 10

            if y + tooltip_height > screen_height:
                y = self.widget.winfo_rooty() - tooltip_height - 5

            self.tooltip_window.wm_geometry(f"+{x}+{y}")

        except tk.TclError:
            pass

    def _update_position(self, event):
        """Update tooltip position based on mouse movement."""
        if self.tooltip_window:
            try:
                x = event.x_root + 10
                y = event.y_root + 10
                self.tooltip_window.wm_geometry(f"+{x}+{y}")
            except tk.TclError:

                pass

class OnboardingOverlay:
    """Onboarding overlay that guides users through features."""

    def __init__(self, parent: tk.Widget, steps: Dict[OnboardingStep, OnboardingStepData]):
        self.parent = parent
        self.steps = steps
        self.current_step = OnboardingStep.WELCOME
        self.overlay_window = None
        self.is_active = False
        self.logger = logging.getLogger(__name__)

        # User preferences
        self.prefs_file = "data/onboarding_prefs.json"
        self.user_prefs = self._load_preferences()

    def start_onboarding(self):
        """Start the onboarding flow."""
        if self.user_prefs.get("completed", False):
            return  # User has already completed onboarding

        self.is_active = True
        self.current_step = OnboardingStep.WELCOME
        self._show_step()

    def _show_step(self):
        """Show the current onboarding step."""
        if not self.is_active or self.current_step not in self.steps:
            return

        step_data = self.steps[self.current_step]

        # Create overlay
        self._create_overlay()

        # Create step content
        self._create_step_content(step_data)

        # Highlight target element if specified
        if step_data.target_element:
            self._highlight_element(step_data.target_element, step_data.highlight_color)

    def _create_overlay(self):
        """Create the overlay window."""
        if self.overlay_window:
            self.overlay_window.destroy()

        self.overlay_window = tk.Toplevel(self.parent)
        self.overlay_window.wm_overrideredirect(True)
        self.overlay_window.wm_attributes("-topmost", True)
        self.overlay_window.wm_attributes("-alpha", 0.9)

        # Make overlay cover entire screen
        self.overlay_window.geometry(
            f"{self.parent.winfo_screenwidth()}x{self.parent.winfo_screenheight()}+0+0"
        )
        self.overlay_window.configure(bg="black")

    def _create_step_content(self, step_data: OnboardingStepData):
        """Create content for the current step."""
        # Content frame
        content_frame = tk.Frame(
            self.overlay_window, bg="white", relief="raised", bd=2, padx=20, pady=20
        )
        content_frame.place(relx=0.5, rely=0.5, anchor="center")

        # Title
        title_label = tk.Label(
            content_frame,
            text=step_data.title,
            font=("Arial", 16, "bold"),
            bg="white",
            fg="#2c3e50",
        )
        title_label.pack(pady=(0, 10))

        # Description
        desc_label = tk.Label(
            content_frame,
            text=step_data.description,
            font=("Arial", 11),
            bg="white",
            fg="#34495e",
            wraplength=400,
            justify="left",
        )
        desc_label.pack(pady=(0, 20))

        # Buttons
        button_frame = tk.Frame(content_frame, bg="white")
        button_frame.pack()

        # Skip button
        if step_data.skip_allowed:
            skip_btn = tk.Button(
                button_frame,
                text="Skip Tour",
                font=("Arial", 10),
                bg="#95a5a6",
                fg="white",
                relief="flat",
                padx=15,
                pady=5,
                command=self._skip_onboarding,
            )
            skip_btn.pack(side="left", padx=(0, 10))

        # Next/Action button
        action_btn = tk.Button(
            button_frame,
            text=step_data.action_text,
            font=("Arial", 10),
            bg="#3498db",
            fg="white",
            relief="flat",
            padx=15,
            pady=5,
            command=self._next_step,
        )
        action_btn.pack(side="left")

    def _highlight_element(self, element_id: str, color: str):
        """Highlight a specific element."""
        # This would need to be implemented based on how elements are identified
        # For now, we'll just log the intention
        self.logger.info(f"Highlighting element: {element_id} with color: {color}")

    def _next_step(self):
        """Move to the next step."""
        steps_list = list(OnboardingStep)
        current_index = steps_list.index(self.current_step)

        if current_index < len(steps_list) - 1:
            self.current_step = steps_list[current_index + 1]
            if self.current_step == OnboardingStep.COMPLETE:
                self._complete_onboarding()
            else:
                self._show_step()
        else:
            self._complete_onboarding()

    def _skip_onboarding(self):
        """Skip the onboarding flow."""
        self._complete_onboarding()

    def _complete_onboarding(self):
        """Complete the onboarding flow."""
        self.is_active = False
        if self.overlay_window:
            self.overlay_window.destroy()
            self.overlay_window = None

        # Save completion status
        self.user_prefs["completed"] = True
        self._save_preferences()

    def _load_preferences(self) -> Dict:
        """Load user preferences."""
        try:
            if os.path.exists(self.prefs_file):
                with open(self.prefs_file, "r") as f:
                    return json.load(f)
        except Exception as e:
            self.logger.error(f"Error loading preferences: {e}")
        return {}

    def _save_preferences(self):
        """Save user preferences."""
        try:
            os.makedirs(os.path.dirname(self.prefs_file), exist_ok=True)
            with open(self.prefs_file, "w") as f:
                json.dump(self.user_prefs, f, indent=2)
        except Exception as e:
            self.logger.error(f"Error saving preferences: {e}")

class KeyboardShortcutOverlay:
    """Overlay showing keyboard shortcuts."""

    def __init__(self, parent: tk.Widget, shortcuts: Dict[str, str]):
        self.parent = parent
        self.shortcuts = shortcuts
        self.overlay_window = None
        self.is_visible = False

        # Bind the '?' key to show shortcuts
        self.parent.bind_all("<KeyPress-question>", self._toggle_shortcuts)
        self.parent.bind_all("<KeyPress-Escape>", self._hide_shortcuts)

    def _toggle_shortcuts(self, event):
        """Toggle keyboard shortcuts overlay."""
        if self.is_visible:
            self._hide_shortcuts()
        else:
            self._show_shortcuts()

    def _show_shortcuts(self, event=None):
        """Show keyboard shortcuts overlay."""
        if self.is_visible:
            return

        self.is_visible = True

        # Create overlay
        self.overlay_window = tk.Toplevel(self.parent)
        self.overlay_window.wm_overrideredirect(True)
        self.overlay_window.wm_attributes("-topmost", True)
        self.overlay_window.wm_attributes("-alpha", 0.95)

        # Position overlay
        self.overlay_window.geometry("400x500+100+100")
        self.overlay_window.configure(bg="#2c3e50")

        # Title
        title_label = tk.Label(
            self.overlay_window,
            text="Keyboard Shortcuts",
            font=("Arial", 16, "bold"),
            bg="#2c3e50",
            fg="white",
        )
        title_label.pack(pady=(20, 10))

        # Shortcuts list
        shortcuts_frame = tk.Frame(self.overlay_window, bg="#2c3e50")
        shortcuts_frame.pack(fill="both", expand=True, padx=20, pady=10)

        for shortcut, description in self.shortcuts.items():
            shortcut_frame = tk.Frame(shortcuts_frame, bg="#2c3e50")
            shortcut_frame.pack(fill="x", pady=2)

            # Shortcut key
            key_label = tk.Label(
                shortcut_frame,
                text=shortcut,
                font=("Arial", 10, "bold"),
                bg="#34495e",
                fg="white",
                padx=8,
                pady=2,
                relief="raised",
            )
            key_label.pack(side="left")

            # Description
            desc_label = tk.Label(
                shortcut_frame,
                text=description,
                font=("Arial", 10),
                bg="#2c3e50",
                fg="#ecf0f1",
                anchor="w",
            )
            desc_label.pack(side="left", padx=(10, 0), fill="x", expand=True)

        # Close instruction
        close_label = tk.Label(
            self.overlay_window,
            text="Press '?' or Escape to close",
            font=("Arial", 9),
            bg="#2c3e50",
            fg="#95a5a6",
        )
        close_label.pack(pady=(10, 20))

    def _hide_shortcuts(self, event=None):
        """Hide keyboard shortcuts overlay."""
        if not self.is_visible:
            return

        self.is_visible = False
        if self.overlay_window:
            self.overlay_window.destroy()
            self.overlay_window = None

class FeatureDiscovery:
    """Animated feature discovery system."""

    def __init__(self, parent: tk.Widget):
        self.parent = parent
        self.discovered_features = set()
        self.animation_queue = []
        self.logger = logging.getLogger(__name__)

    def highlight_feature(
        self, widget: tk.Widget, feature_name: str, description: str, duration: float = 3.0
    ):
        """Highlight a new feature with animation."""
        if feature_name in self.discovered_features:
            return  # Feature already discovered

        self.discovered_features.add(feature_name)

        # Create highlight animation
        self._animate_highlight(widget, description, duration)

    def _animate_highlight(self, widget: tk.Widget, description: str, duration: float):
        """Animate feature highlight."""

        def animate():
            try:
                # Store original colors
                original_bg = widget.cget("bg")
                original_relief = widget.cget("relief")

                # Animate highlight
                highlight_colors = ["#f39c12", "#e67e22", "#d35400", "#e67e22", "#f39c12"]

                for color in highlight_colors * 2:  # Repeat animation
                    widget.configure(bg=color, relief="raised")
                    time.sleep(0.2)

                # Restore original appearance
                widget.configure(bg=original_bg, relief=original_relief)

                # Show description tooltip
                self._show_feature_tooltip(widget, description)

            except tk.TclError:
                pass  # Widget may have been destroyed

        threading.Thread(target=animate, daemon=True).start()

    def _show_feature_tooltip(self, widget: tk.Widget, description: str):
        """Show feature description tooltip."""
        tooltip_config = TooltipConfig(
            text=f"✨ New Feature: {description}", bg_color="#f39c12", fg_color="white"
        )

        # Create temporary tooltip
        tooltip = ToolTip(widget, tooltip_config)
        tooltip._show_tooltip()

        # Auto-hide after 3 seconds
        def hide_tooltip():
            time.sleep(3)
            try:
                widget.after(0, tooltip._hide_tooltip)
            except tk.TclError:
                pass

        threading.Thread(target=hide_tooltip, daemon=True).start()

class HelpSystem:
    """Main help system coordinator."""

    def __init__(self, parent: tk.Widget):
        self.parent = parent
        self.logger = logging.getLogger(__name__)

        # Initialize components
        self.tooltips = {}
        self.onboarding = None
        self.shortcuts = None
        self.feature_discovery = FeatureDiscovery(parent)

        # Default keyboard shortcuts
        default_shortcuts = {
            "?": "Show this help",
            "Ctrl+R": "Refresh weather data",
            "Ctrl+F": "Search locations",
            "Ctrl+S": "Save current location",
            "Ctrl+T": "Toggle theme",
            "Escape": "Close dialogs",
            "F5": "Refresh all data",
            "Ctrl+,": "Open settings",
        }

        self.shortcuts = KeyboardShortcutOverlay(parent, default_shortcuts)

    def add_tooltip(self, widget: tk.Widget, text: str, **kwargs) -> ToolTip:
        """Add tooltip to a widget."""
        config = TooltipConfig(text=text, **kwargs)
        tooltip = ToolTip(widget, config)
        self.tooltips[id(widget)] = tooltip
        return tooltip

    def setup_onboarding(self, steps: Dict[OnboardingStep, OnboardingStepData]):
        """Setup onboarding flow."""
        self.onboarding = OnboardingOverlay(self.parent, steps)

    def start_onboarding(self):
        """Start onboarding if configured."""
        if self.onboarding:
            self.onboarding.start_onboarding()

    def highlight_new_feature(self, widget: tk.Widget, feature_name: str, description: str):
        """Highlight a new feature."""
        self.feature_discovery.highlight_feature(widget, feature_name, description)

    def update_shortcuts(self, shortcuts: Dict[str, str]):
        """Update keyboard shortcuts."""
        if self.shortcuts:
            self.shortcuts.shortcuts.update(shortcuts)

    def remove_tooltip(self, widget: tk.Widget):
        """Remove tooltip from a widget."""
        widget_id = id(widget)
        if widget_id in self.tooltips:
            del self.tooltips[widget_id]
