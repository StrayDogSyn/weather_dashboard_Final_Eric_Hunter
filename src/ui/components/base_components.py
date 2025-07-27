#!/usr/bin/env python3
"""
Base UI Components - Glassmorphic Design Foundation

This module implements the core glassmorphic UI components that serve as
the foundation for the entire weather dashboard interface, demonstrating:
- Advanced CustomTkinter widget customization
- Glassmorphic design principles with RGBA transparency
- Responsive design patterns and dynamic theming
- Professional component architecture with inheritance
- Accessibility and usability best practices
"""

import customtkinter as ctk
from tkinter import font as tkfont
from typing import Dict, Any, Optional, Callable, Union, Tuple
from PIL import Image, ImageFilter, ImageDraw, ImageFont
import math
from datetime import datetime
from enum import Enum

from ...utils.logger import LoggerMixin
from ..theme_manager import ThemeManager, WeatherTheme, GlassEffect


class ComponentSize(Enum):
    """
    Standard component sizes for consistent UI scaling.

    This enum demonstrates professional UI design patterns
    with standardized sizing for visual consistency.
    """
    SMALL = "small"
    MEDIUM = "medium"
    LARGE = "large"
    EXTRA_LARGE = "xl"


class AnimationState(Enum):
    """
    Animation states for interactive components.

    This enum supports smooth UI transitions and
    professional interaction feedback.
    """
    IDLE = "idle"
    HOVER = "hover"
    ACTIVE = "active"
    DISABLED = "disabled"


class GlassFrame(ctk.CTkFrame, LoggerMixin):
    """
    Base glassmorphic frame component.

    This class implements the core glassmorphic design principles
    including transparency, blur effects, and dynamic theming.
    It serves as the foundation for all other UI components.
    """

    def __init__(
        self,
        parent,
        glass_effect: Optional[GlassEffect] = None,
        size: ComponentSize = ComponentSize.MEDIUM,
        **kwargs
    ):
        # Set up glassmorphic styling
        self.glass_effect = glass_effect or GlassEffect()
        self.size = size
        self.theme_manager = ThemeManager()

        # Apply glass styling to kwargs
        glass_config = self._get_glass_config()
        kwargs.update(glass_config)

        super().__init__(parent, **kwargs)

        # Initialize component state
        self.animation_state = AnimationState.IDLE
        self._hover_callbacks: list[Callable] = []
        self._click_callbacks: list[Callable] = []

        # Set up event bindings for interactivity
        self._setup_event_bindings()

        self.logger.debug(f"GlassFrame initialized with size {size.value}")

    def _get_glass_config(self) -> Dict[str, Any]:
        """
        Generate CustomTkinter configuration for glassmorphic styling.

        Returns:
            Configuration dictionary for CTkFrame
        """
        # Get size-specific dimensions
        size_config = self._get_size_config()

        # Get glassmorphic frame configuration
        glass_config = self.theme_manager.get_glass_frame_config()
        bg_color = glass_config.get("fg_color", "#1a1a1a")
        border_color = glass_config.get("border_color", "#333333")

        return {
            'fg_color': bg_color,
            'border_color': border_color,
            'border_width': self.glass_effect.border_width,
            'corner_radius': self.glass_effect.corner_radius,
            'width': size_config['width'],
            'height': size_config['height']
        }

    def _get_size_config(self) -> Dict[str, int]:
        """
        Get size configuration based on component size.

        Returns:
            Size configuration dictionary
        """
        size_configs = {
            ComponentSize.SMALL: {'width': 200, 'height': 150},
            ComponentSize.MEDIUM: {'width': 300, 'height': 200},
            ComponentSize.LARGE: {'width': 400, 'height': 300},
            ComponentSize.EXTRA_LARGE: {'width': 600, 'height': 400}
        }

        return size_configs.get(self.size, size_configs[ComponentSize.MEDIUM])

    def _setup_event_bindings(self) -> None:
        """
        Set up event bindings for interactive behavior.

        This method demonstrates professional event handling
        for responsive UI interactions.
        """
        # Mouse enter/leave for hover effects
        self.bind("<Enter>", self._on_mouse_enter)
        self.bind("<Leave>", self._on_mouse_leave)

        # Click events
        self.bind("<Button-1>", self._on_click)

        # Focus events for accessibility
        self.bind("<FocusIn>", self._on_focus_in)
        self.bind("<FocusOut>", self._on_focus_out)

    def _on_mouse_enter(self, event) -> None:
        """
        Handle mouse enter event for hover effects.

        Args:
            event: Tkinter event object
        """
        if self.animation_state != AnimationState.DISABLED:
            self.animation_state = AnimationState.HOVER
            self._apply_hover_effect()

            # Call registered hover callbacks
            for callback in self._hover_callbacks:
                try:
                    callback(True)  # True for hover start
                except Exception as e:
                    self.logger.error(f"Error in hover callback: {e}")

    def _on_mouse_leave(self, event) -> None:
        """
        Handle mouse leave event to remove hover effects.

        Args:
            event: Tkinter event object
        """
        if self.animation_state == AnimationState.HOVER:
            self.animation_state = AnimationState.IDLE
            self._remove_hover_effect()

            # Call registered hover callbacks
            for callback in self._hover_callbacks:
                try:
                    callback(False)  # False for hover end
                except Exception as e:
                    self.logger.error(f"Error in hover callback: {e}")

    def _on_click(self, event) -> None:
        """
        Handle click event.

        Args:
            event: Tkinter event object
        """
        if self.animation_state != AnimationState.DISABLED:
            self.animation_state = AnimationState.ACTIVE
            self._apply_click_effect()

            # Call registered click callbacks
            for callback in self._click_callbacks:
                try:
                    callback(event)
                except Exception as e:
                    self.logger.error(f"Error in click callback: {e}")

            # Return to hover state after click
            self.after(150, lambda: setattr(self, 'animation_state', AnimationState.HOVER))

    def _on_focus_in(self, event) -> None:
        """
        Handle focus in event for accessibility.

        Args:
            event: Tkinter event object
        """
        # Add focus indicator
        self.configure(border_width=self.glass_effect.border_width + 1)

    def _on_focus_out(self, event) -> None:
        """
        Handle focus out event.

        Args:
            event: Tkinter event object
        """
        # Remove focus indicator
        self.configure(border_width=self.glass_effect.border_width)

    def _apply_hover_effect(self) -> None:
        """
        Apply visual hover effect.

        This method demonstrates smooth UI transitions
        for enhanced user experience.
        """
        # Increase opacity slightly for hover effect
        hover_bg = "#333333"  # Simplified glassmorphic hover background
        hover_border = "#555555"  # Simplified glassmorphic hover border

        self.configure(
            fg_color=hover_bg,
            border_color=hover_border
        )

    def _remove_hover_effect(self) -> None:
        """
        Remove visual hover effect and return to normal state.
        """
        # Return to original colors
        glass_config = self._get_glass_config()
        self.configure(
            fg_color=glass_config['fg_color'],
            border_color=glass_config['border_color']
        )

    def _apply_click_effect(self) -> None:
        """
        Apply visual click effect.

        This provides immediate feedback for user interactions.
        """
        # Slightly darker for click effect
        click_bg = "#222222"  # Simplified click background

        self.configure(fg_color=click_bg)

        # Return to hover state after brief delay
        self.after(100, self._apply_hover_effect)

    def add_hover_callback(self, callback: Callable[[bool], None]) -> None:
        """
        Add callback for hover events.

        Args:
            callback: Function to call on hover (receives bool for hover state)
        """
        self._hover_callbacks.append(callback)

    def add_click_callback(self, callback: Callable) -> None:
        """
        Add callback for click events.

        Args:
            callback: Function to call on click
        """
        self._click_callbacks.append(callback)

    def set_enabled(self, enabled: bool) -> None:
        """
        Enable or disable the component.

        Args:
            enabled: Whether component should be enabled
        """
        if enabled:
            self.animation_state = AnimationState.IDLE
            self.configure(state="normal")
        else:
            self.animation_state = AnimationState.DISABLED
            self.configure(state="disabled")

            # Apply disabled styling
            disabled_bg = "#666666"  # Simplified disabled background
            self.configure(fg_color=disabled_bg)

    def update_theme(self, weather_theme: WeatherTheme) -> None:
        """
        Update component theme based on weather conditions.

        Args:
            weather_theme: Weather-specific theme configuration
        """
        self.theme_manager.apply_weather_theme(weather_theme)

        # Reapply glass configuration with new theme
        glass_config = self._get_glass_config()
        self.configure(
            fg_color=glass_config['fg_color'],
            border_color=glass_config['border_color']
        )

        self.logger.debug(f"Theme updated to {weather_theme.name}")


class GlassButton(ctk.CTkButton, LoggerMixin):
    """
    Glassmorphic button component with advanced styling.

    This class extends CTkButton with glassmorphic design principles
    and professional interaction patterns.
    """

    def __init__(
        self,
        parent,
        text: str = "Button",
        glass_effect: Optional[GlassEffect] = None,
        size: ComponentSize = ComponentSize.MEDIUM,
        icon: Optional[str] = None,
        **kwargs
    ):
        self.glass_effect = glass_effect or GlassEffect()
        self.size = size
        self.theme_manager = ThemeManager()
        self.icon_path = icon

        # Apply glass styling
        glass_config = self._get_glass_button_config()
        kwargs.update(glass_config)

        super().__init__(parent, text=text, **kwargs)

        # Load icon if provided
        if self.icon_path:
            self._load_icon()

        self.logger.debug(f"GlassButton '{text}' initialized")

    def _get_glass_button_config(self) -> Dict[str, Any]:
        """
        Generate CustomTkinter configuration for glassmorphic button.

        Returns:
            Configuration dictionary for CTkButton
        """
        # Size-specific configurations
        size_configs = {
            ComponentSize.SMALL: {'width': 100, 'height': 32, 'font_size': 12},
            ComponentSize.MEDIUM: {'width': 140, 'height': 40, 'font_size': 14},
            ComponentSize.LARGE: {'width': 180, 'height': 48, 'font_size': 16},
            ComponentSize.EXTRA_LARGE: {'width': 220, 'height': 56, 'font_size': 18}
        }

        size_config = size_configs.get(self.size, size_configs[ComponentSize.MEDIUM])

        # Glassmorphic colors
        # Get glassmorphic button configuration
        glass_config = self.theme_manager.get_glass_button_config()
        fg_color = glass_config.get("fg_color", "#3B82F6")
        hover_color = glass_config.get("hover_color", "#60A5FA")
        text_color = glass_config.get("text_color", "#FFFFFF")

        return {
            'fg_color': fg_color,
            'hover_color': hover_color,
            'text_color': text_color,
            'border_width': self.glass_effect.border_width,
            'corner_radius': self.glass_effect.corner_radius,
            'width': size_config['width'],
            'height': size_config['height'],
            'font': ctk.CTkFont(size=size_config['font_size'], weight="normal")
        }

    def _load_icon(self) -> None:
        """
        Load and configure button icon.

        This method demonstrates professional icon handling
        with proper scaling and theming.
        """
        try:
            # Load icon image
            icon_image = Image.open(self.icon_path)

            # Scale icon based on button size
            icon_sizes = {
                ComponentSize.SMALL: 16,
                ComponentSize.MEDIUM: 20,
                ComponentSize.LARGE: 24,
                ComponentSize.EXTRA_LARGE: 28
            }

            icon_size = icon_sizes.get(self.size, 20)
            icon_image = icon_image.resize((icon_size, icon_size), Image.Resampling.LANCZOS)

            # Convert to CTkImage
            ctk_image = ctk.CTkImage(
                light_image=icon_image,
                dark_image=icon_image,
                size=(icon_size, icon_size)
            )

            self.configure(image=ctk_image)

        except Exception as e:
            self.logger.error(f"Failed to load icon {self.icon_path}: {e}")

    def set_loading(self, loading: bool) -> None:
        """
        Set button loading state with visual feedback.

        Args:
            loading: Whether button is in loading state
        """
        if loading:
            self.configure(
                text="Loading...",
                state="disabled"
            )
        else:
            self.configure(state="normal")

    def pulse_effect(self, duration: int = 1000) -> None:
        """
        Apply pulse animation effect.

        Args:
            duration: Animation duration in milliseconds
        """
        original_fg = self.cget("fg_color")
        pulse_color = "#00FF0050"

        # Animate to pulse color
        self.configure(fg_color=pulse_color)

        # Return to original color
        self.after(duration, lambda: self.configure(fg_color=original_fg))


class GlassLabel(ctk.CTkLabel, LoggerMixin):
    """
    Glassmorphic label component with enhanced typography.

    This class provides professional text display with
    glassmorphic styling and responsive typography.
    """

    def __init__(
        self,
        parent,
        text: str = "Label",
        glass_effect: Optional[GlassEffect] = None,
        size: ComponentSize = ComponentSize.MEDIUM,
        text_style: str = "normal",  # normal, heading, subheading, caption
        **kwargs
    ):
        self.glass_effect = glass_effect or GlassEffect()
        self.size = size
        self.text_style = text_style
        self.theme_manager = ThemeManager()

        # Apply glass styling
        glass_config = self._get_glass_label_config()
        kwargs.update(glass_config)

        super().__init__(parent, text=text, **kwargs)

        self.logger.debug(f"GlassLabel '{text}' initialized with style {text_style}")

    def _get_glass_label_config(self) -> Dict[str, Any]:
        """
        Generate CustomTkinter configuration for glassmorphic label.

        Returns:
            Configuration dictionary for CTkLabel
        """
        # Typography configurations
        typography_configs = {
            "normal": {"weight": "normal", "size_multiplier": 1.0},
            "heading": {"weight": "bold", "size_multiplier": 1.5},
            "subheading": {"weight": "bold", "size_multiplier": 1.2},
            "caption": {"weight": "normal", "size_multiplier": 0.8}
        }

        # Size-specific base font sizes
        base_sizes = {
            ComponentSize.SMALL: 11,
            ComponentSize.MEDIUM: 13,
            ComponentSize.LARGE: 15,
            ComponentSize.EXTRA_LARGE: 17
        }

        typography = typography_configs.get(self.text_style, typography_configs["normal"])
        base_size = base_sizes.get(self.size, 13)
        font_size = int(base_size * typography["size_multiplier"])

        # Text color with glassmorphic styling
        text_color = "#FFFFFF"

        return {
            'text_color': text_color,
            'font': ctk.CTkFont(
                size=font_size,
                weight=typography["weight"]
            )
        }

    def set_text_with_animation(self, new_text: str, animation_duration: int = 300) -> None:
        """
        Set text with fade animation.

        Args:
            new_text: New text to display
            animation_duration: Animation duration in milliseconds
        """
        # Fade out
        self.configure(text_color=("gray70", "gray30"))

        # Change text and fade in
        def change_text():
            self.configure(text=new_text)
            glass_config = self._get_glass_label_config()
            self.configure(text_color=glass_config['text_color'])

        self.after(animation_duration // 2, change_text)

    def set_highlight(self, highlighted: bool) -> None:
        """
        Set text highlight state.

        Args:
            highlighted: Whether text should be highlighted
        """
        if highlighted:
            highlight_color = "#FFD700"
            self.configure(text_color=highlight_color)
        else:
            glass_config = self._get_glass_label_config()
            self.configure(text_color=glass_config['text_color'])


class GlassEntry(ctk.CTkEntry, LoggerMixin):
    """
    Glassmorphic entry component with enhanced input handling.

    This class provides professional text input with
    glassmorphic styling and validation support.
    """

    def __init__(
        self,
        parent,
        placeholder_text: str = "Enter text...",
        glass_effect: Optional[GlassEffect] = None,
        size: ComponentSize = ComponentSize.MEDIUM,
        validation_callback: Optional[Callable[[str], bool]] = None,
        **kwargs
    ):
        self.glass_effect = glass_effect or GlassEffect()
        self.size = size
        self.theme_manager = ThemeManager()
        self.validation_callback = validation_callback
        self.is_valid = True

        # Apply glass styling
        glass_config = self._get_glass_entry_config()
        kwargs.update(glass_config)

        super().__init__(parent, placeholder_text=placeholder_text, **kwargs)

        # Set up validation
        if self.validation_callback:
            self.bind("<KeyRelease>", self._on_text_change)
            self.bind("<FocusOut>", self._on_focus_out)

        self.logger.debug(f"GlassEntry initialized with placeholder '{placeholder_text}'")

    def _get_glass_entry_config(self) -> Dict[str, Any]:
        """
        Generate CustomTkinter configuration for glassmorphic entry.

        Returns:
            Configuration dictionary for CTkEntry
        """
        # Size configurations
        size_configs = {
            ComponentSize.SMALL: {'width': 150, 'height': 28, 'font_size': 11},
            ComponentSize.MEDIUM: {'width': 200, 'height': 32, 'font_size': 13},
            ComponentSize.LARGE: {'width': 250, 'height': 36, 'font_size': 15},
            ComponentSize.EXTRA_LARGE: {'width': 300, 'height': 40, 'font_size': 17}
        }

        size_config = size_configs.get(self.size, size_configs[ComponentSize.MEDIUM])

        # Glassmorphic colors
        fg_color = "#2a2a2a"

        border_color = "#444444"

        text_color = "#FFFFFF"

        placeholder_color = "#888888"

        return {
            'fg_color': fg_color,
            'border_color': border_color,
            'text_color': text_color,
            'placeholder_text_color': placeholder_color,
            'border_width': self.glass_effect.border_width,
            'corner_radius': self.glass_effect.corner_radius,
            'width': size_config['width'],
            'height': size_config['height'],
            'font': ctk.CTkFont(size=size_config['font_size'])
        }

    def _on_text_change(self, event) -> None:
        """
        Handle text change for validation.

        Args:
            event: Tkinter event object
        """
        if self.validation_callback:
            text = self.get()
            self.is_valid = self.validation_callback(text)
            self._update_validation_styling()

    def _on_focus_out(self, event) -> None:
        """
        Handle focus out event for validation.

        Args:
            event: Tkinter event object
        """
        if self.validation_callback:
            text = self.get()
            self.is_valid = self.validation_callback(text)
            self._update_validation_styling()

    def _update_validation_styling(self) -> None:
        """
        Update styling based on validation state.

        This method provides visual feedback for input validation.
        """
        if self.is_valid:
            # Valid styling
            glass_config = self._get_glass_entry_config()
            self.configure(border_color=glass_config['border_color'])
        else:
            # Invalid styling
            error_color = "#FF0000"
            self.configure(border_color=error_color)

    def set_error_state(self, error: bool, message: str = "") -> None:
        """
        Set entry error state with optional message.

        Args:
            error: Whether entry is in error state
            message: Error message to display
        """
        self.is_valid = not error
        self._update_validation_styling()

        if error and message:
            # Could implement tooltip or status message here
            self.logger.debug(f"Entry error: {message}")

    def get_validated_text(self) -> Optional[str]:
        """
        Get text only if validation passes.

        Returns:
            Text if valid, None otherwise
        """
        text = self.get()

        if self.validation_callback:
            if self.validation_callback(text):
                return text
            else:
                return None

        return text


class GlassProgressBar(ctk.CTkProgressBar, LoggerMixin):
    """
    Glassmorphic progress bar component.

    This class provides professional progress indication
    with glassmorphic styling and smooth animations.
    """

    def __init__(
        self,
        parent,
        glass_effect: Optional[GlassEffect] = None,
        size: ComponentSize = ComponentSize.MEDIUM,
        **kwargs
    ):
        self.glass_effect = glass_effect or GlassEffect()
        self.size = size
        self.theme_manager = ThemeManager()

        # Apply glass styling
        glass_config = self._get_glass_progress_config()
        kwargs.update(glass_config)

        super().__init__(parent, **kwargs)

        self.logger.debug("GlassProgressBar initialized")

    def _get_glass_progress_config(self) -> Dict[str, Any]:
        """
        Generate CustomTkinter configuration for glassmorphic progress bar.

        Returns:
            Configuration dictionary for CTkProgressBar
        """
        # Size configurations
        size_configs = {
            ComponentSize.SMALL: {'width': 150, 'height': 8},
            ComponentSize.MEDIUM: {'width': 200, 'height': 12},
            ComponentSize.LARGE: {'width': 300, 'height': 16},
            ComponentSize.EXTRA_LARGE: {'width': 400, 'height': 20}
        }

        size_config = size_configs.get(self.size, size_configs[ComponentSize.MEDIUM])

        # Glassmorphic colors
        fg_color = "#444444"

        progress_color = "#00FF00"

        return {
            'fg_color': fg_color,
            'progress_color': progress_color,
            'width': size_config['width'],
            'height': size_config['height'],
            'corner_radius': self.glass_effect.corner_radius // 2
        }

    def animate_to_value(self, target_value: float, duration: int = 1000) -> None:
        """
        Animate progress bar to target value.

        Args:
            target_value: Target progress value (0.0 to 1.0)
            duration: Animation duration in milliseconds
        """
        current_value = self.get()
        steps = 50
        step_duration = duration // steps
        step_increment = (target_value - current_value) / steps

        def animate_step(step: int):
            if step <= steps:
                new_value = current_value + (step_increment * step)
                self.set(new_value)
                self.after(step_duration, lambda: animate_step(step + 1))

        animate_step(1)


# Utility functions for component creation
def create_glass_card(
    parent,
    title: str,
    content_widget: Optional[ctk.CTkBaseClass] = None,
    size: ComponentSize = ComponentSize.MEDIUM
) -> GlassFrame:
    """
    Create a standardized glass card component.

    Args:
        parent: Parent widget
        title: Card title
        content_widget: Optional content widget to embed
        size: Card size

    Returns:
        Configured GlassFrame card
    """
    card = GlassFrame(parent, size=size)

    # Add title
    title_label = GlassLabel(
        card,
        text=title,
        text_style="heading",
        size=ComponentSize.MEDIUM
    )
    title_label.pack(pady=(10, 5), padx=10, anchor="w")

    # Add content widget if provided
    if content_widget:
        content_widget.pack(pady=5, padx=10, fill="both", expand=True)

    return card


def create_glass_toolbar(
    parent,
    buttons: list[Dict[str, Any]],
    size: ComponentSize = ComponentSize.MEDIUM
) -> GlassFrame:
    """
    Create a standardized glass toolbar component.

    Args:
        parent: Parent widget
        buttons: List of button configurations
        size: Toolbar size

    Returns:
        Configured GlassFrame toolbar
    """
    toolbar = GlassFrame(parent, size=size)
    toolbar.configure(height=60)  # Fixed height for toolbar

    # Create buttons
    for i, button_config in enumerate(buttons):
        button = GlassButton(
            toolbar,
            text=button_config.get('text', f'Button {i+1}'),
            size=ComponentSize.SMALL,
            command=button_config.get('command'),
            icon=button_config.get('icon')
        )
        button.pack(side="left", padx=5, pady=10)

    return toolbar


if __name__ == "__main__":
    # Test the glassmorphic components
    import tkinter as tk

    root = tk.Tk()
    root.title("Glassmorphic Components Test")
    root.geometry("800x600")

    # Create test components
    frame = GlassFrame(root, size=ComponentSize.LARGE)
    frame.pack(pady=20, padx=20)

    label = GlassLabel(frame, text="Glassmorphic Label", text_style="heading")
    label.pack(pady=10)

    button = GlassButton(frame, text="Glass Button")
    button.pack(pady=5)

    entry = GlassEntry(frame, placeholder_text="Enter text...")
    entry.pack(pady=5)

    progress = GlassProgressBar(frame)
    progress.pack(pady=10)
    progress.set(0.7)

    root.mainloop()
