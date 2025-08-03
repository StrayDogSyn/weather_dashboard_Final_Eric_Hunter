"""Theme Configuration - Data Terminal Aesthetic

Defines colors, fonts, and styling for the modern weather dashboard.
"""

from typing import Any, Dict

import customtkinter as ctk


class DataTerminalTheme:
    """Basic theme configuration with dynamic theme support."""

    PRIMARY = "#00ff88"
    BACKGROUND = "#1a1a1a"
    CARD_BG = "#2a2a2a"
    TEXT = "#ffffff"
    TEXT_SECONDARY = "#888888"
    BORDER = "#333333"

    # Additional colors
    SUCCESS = "#00cc66"
    ACCENT = "#00d4ff"  # Changed to bright cyan for better visibility
    HOVER = "#555555"
    ERROR = "#ff4444"
    WARNING = "#ffaa00"
    INFO = "#0088ff"
    CHART_GRID = "#333333"
    CHART_PRIMARY = "#00ff88"

    # Observer pattern for theme changes
    _observers = []

    FONT_FAMILY = "Arial"
    FONT_SIZE_SMALL = 12
    FONT_SIZE_MEDIUM = 14
    FONT_SIZE_LARGE = 18
    FONT_SIZE_TINY = 10

    # Padding
    PADDING_TINY = 5
    PADDING_SMALL = 10
    PADDING_MEDIUM = 15
    PADDING_LARGE = 20

    # Border Radius
    RADIUS_LARGE = 12
    RADIUS_MEDIUM = 8
    RADIUS_SMALL = 4

    @classmethod
    def configure_customtkinter(cls) -> None:
        """Configure CustomTkinter with Data Terminal theme."""
        # Set appearance mode
        ctk.set_appearance_mode("dark")

        # Configure custom theme
        ctk.set_default_color_theme("dark-blue")  # Base theme

        # Override with custom colors
        # Note: Custom theme configuration would go here if needed
        # Currently using default dark-blue theme

        # Apply theme (Note: CustomTkinter doesn't support runtime theme changes,
        # so we'll use these colors directly in our components)

    @classmethod
    def get_font(cls, size: int = None, weight: str = "normal") -> tuple:
        """Get font configuration."""
        font_size = size or cls.FONT_SIZE_MEDIUM
        return (cls.FONT_FAMILY, font_size, weight)

    @classmethod
    def get_button_style(cls, variant: str = "primary") -> Dict[str, Any]:
        """Get button styling configuration."""
        styles = {
            "primary": {
                "fg_color": cls.PRIMARY,
                "hover_color": cls.SUCCESS,
                "text_color": cls.BACKGROUND,
                "border_color": cls.PRIMARY,
                "border_width": 1,
                "corner_radius": cls.RADIUS_MEDIUM,
                "font": cls.get_font(cls.FONT_SIZE_MEDIUM, "bold"),
            },
            "secondary": {
                "fg_color": cls.BACKGROUND,
                "hover_color": cls.HOVER,
                "text_color": cls.PRIMARY,
                "border_color": cls.PRIMARY,
                "border_width": 2,
                "corner_radius": cls.RADIUS_MEDIUM,
                "font": cls.get_font(cls.FONT_SIZE_MEDIUM),
            },
            "danger": {
                "fg_color": cls.ERROR,
                "hover_color": "#CC3333",
                "text_color": cls.TEXT,
                "border_color": cls.ERROR,
                "border_width": 1,
                "corner_radius": cls.RADIUS_MEDIUM,
                "font": cls.get_font(cls.FONT_SIZE_MEDIUM, "bold"),
            },
        }
        return styles.get(variant, styles["primary"])

    @classmethod
    def get_frame_style(cls, variant: str = "default") -> Dict[str, Any]:
        """Get frame styling configuration."""
        styles = {
            "default": {
                "fg_color": cls.CARD_BG,
                "border_color": cls.BORDER,
                "border_width": 1,
                "corner_radius": cls.RADIUS_MEDIUM,
            },
            "main": {
                "fg_color": cls.BACKGROUND,
                "border_color": cls.BACKGROUND,
                "border_width": 0,
                "corner_radius": 0,
            },
            "highlight": {
                "fg_color": cls.CARD_BG,
                "border_color": cls.PRIMARY,
                "border_width": 2,
                "corner_radius": cls.RADIUS_MEDIUM,
            },
        }
        return styles.get(variant, styles["default"])

    @classmethod
    def get_entry_style(cls) -> Dict[str, Any]:
        """Get entry field styling configuration."""
        return {
            "fg_color": cls.CARD_BG,
            "border_color": cls.BORDER,
            "border_width": 2,
            "text_color": cls.TEXT,
            "placeholder_text_color": cls.TEXT_SECONDARY,
            "corner_radius": cls.RADIUS_SMALL,
            "font": cls.get_font(cls.FONT_SIZE_MEDIUM),
        }

    @classmethod
    def get_label_style(cls, variant: str = "default") -> Dict[str, Any]:
        """Get label styling configuration."""
        styles = {
            "default": {"text_color": cls.TEXT, "font": cls.get_font(cls.FONT_SIZE_MEDIUM)},
            "title": {"text_color": cls.PRIMARY, "font": cls.get_font(cls.FONT_SIZE_LARGE, "bold")},
            "subtitle": {
                "text_color": cls.TEXT,
                "font": cls.get_font(cls.FONT_SIZE_MEDIUM, "bold"),
            },
            "caption": {
                "text_color": cls.TEXT_SECONDARY,
                "font": cls.get_font(cls.FONT_SIZE_SMALL),
            },
            "value": {
                "text_color": cls.PRIMARY,
                "font": cls.get_font(cls.FONT_SIZE_MEDIUM, "bold"),
            },
        }
        return styles.get(variant, styles["default"])

    @classmethod
    def get_switch_style(cls) -> Dict[str, Any]:
        """Get switch/toggle styling configuration."""
        return {
            "fg_color": cls.ACCENT,
            "progress_color": cls.PRIMARY,
            "button_color": cls.TEXT,
            "button_hover_color": cls.PRIMARY,
            "text_color": cls.TEXT,
            "font": cls.get_font(cls.FONT_SIZE_SMALL),
        }

    @classmethod
    def get_checkbox_style(cls) -> Dict[str, Any]:
        """Get checkbox styling configuration."""
        return {
            "fg_color": cls.CARD_BG,
            "border_color": cls.BORDER,
            "checkmark_color": cls.PRIMARY,
            "hover_color": cls.HOVER,
            "text_color": cls.TEXT,
            "font": cls.get_font(cls.FONT_SIZE_SMALL),
        }

    @classmethod
    def get_textbox_style(cls) -> Dict[str, Any]:
        """Get textbox styling configuration."""
        return {
            "fg_color": cls.CARD_BG,
            "border_color": cls.BORDER,
            "border_width": 1,
            "text_color": cls.TEXT,
            "corner_radius": cls.RADIUS_SMALL,
            "font": cls.get_font(cls.FONT_SIZE_SMALL),
        }

    @classmethod
    def get_matplotlib_style(cls) -> Dict[str, Any]:
        """Get matplotlib styling configuration."""
        return {
            "figure.facecolor": cls.BACKGROUND,
            "axes.facecolor": cls.CARD_BG,
            "axes.edgecolor": cls.BORDER,
            "axes.labelcolor": cls.TEXT,
            "axes.spines.left": True,
            "axes.spines.bottom": True,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "xtick.color": cls.TEXT,
            "ytick.color": cls.TEXT,
            "grid.color": cls.CHART_GRID,
            "grid.alpha": 0.3,
            "text.color": cls.TEXT,
            "font.family": "monospace",
            "font.size": cls.FONT_SIZE_SMALL,
            "lines.color": cls.CHART_PRIMARY,
            "patch.edgecolor": cls.BORDER,
        }

    @classmethod
    def set_active_theme(cls, theme_dict: Dict[str, Any]):
        """Set the active theme colors dynamically."""
        # Update color constants
        cls.BACKGROUND = theme_dict.get("bg", cls.BACKGROUND)
        cls.CARD_BG = theme_dict.get("card", cls.CARD_BG)
        cls.PRIMARY = theme_dict.get("primary", cls.PRIMARY)
        cls.TEXT = theme_dict.get("text", cls.TEXT)
        cls.TEXT_SECONDARY = theme_dict.get("secondary", cls.TEXT_SECONDARY)
        cls.SUCCESS = theme_dict.get("accent", cls.SUCCESS)
        cls.ERROR = theme_dict.get("error", cls.ERROR)
        cls.CHART_PRIMARY = theme_dict.get("chart_color", cls.CHART_PRIMARY)
        cls.CHART_GRID = theme_dict.get("chart_bg", cls.CHART_GRID)

        # Notify observers
        cls._notify_observers()

    @classmethod
    def add_observer(cls, callback):
        """Add an observer for theme changes."""
        if callback not in cls._observers:
            cls._observers.append(callback)

    @classmethod
    def remove_observer(cls, callback):
        """Remove an observer for theme changes."""
        if callback in cls._observers:
            cls._observers.remove(callback)

    @classmethod
    def _notify_observers(cls):
        """Notify all observers of theme changes."""
        for callback in cls._observers:
            try:
                callback()
            except Exception as e:
                print(f"Error notifying theme observer: {e}")


class WeatherTheme:
    """Weather-specific theme with glassmorphic styling for journal components."""

    def __init__(self):
        """Initialize weather theme with glassmorphic colors and fonts."""
        self.colors = {
            # Base colors from DataTerminalTheme
            "background": DataTerminalTheme.BACKGROUND,
            "text_primary": DataTerminalTheme.TEXT,
            "text_secondary": DataTerminalTheme.TEXT_SECONDARY,
            "accent": DataTerminalTheme.PRIMARY,
            "accent_light": DataTerminalTheme.SUCCESS,
            "success": DataTerminalTheme.SUCCESS,
            "warning": DataTerminalTheme.WARNING,
            "error": DataTerminalTheme.ERROR,
            "info": DataTerminalTheme.INFO,
            # Glassmorphic colors
            "glass_bg": "rgba(30, 30, 30, 0.8)",  # Semi-transparent dark
            "card_bg": DataTerminalTheme.CARD_BG,
            "card_hover": DataTerminalTheme.HOVER,
            "border": DataTerminalTheme.BORDER,
            "button_bg": DataTerminalTheme.ACCENT,
            "button_hover": DataTerminalTheme.HOVER,
            "input_bg": DataTerminalTheme.CARD_BG,
            "code_bg": DataTerminalTheme.CARD_BG,
            # For tkinter compatibility (no rgba support)
            "glass_bg_solid": DataTerminalTheme.CARD_BG,
        }

        # Override glass_bg for tkinter compatibility
        self.colors["glass_bg"] = self.colors["glass_bg_solid"]

        self.fonts = {
            "heading": (DataTerminalTheme.FONT_FAMILY, DataTerminalTheme.FONT_SIZE_LARGE, "bold"),
            "subheading": (
                DataTerminalTheme.FONT_FAMILY,
                DataTerminalTheme.FONT_SIZE_MEDIUM,
                "bold",
            ),
            "body": (DataTerminalTheme.FONT_FAMILY, DataTerminalTheme.FONT_SIZE_MEDIUM),
            "small": (DataTerminalTheme.FONT_FAMILY, DataTerminalTheme.FONT_SIZE_SMALL),
            "small_bold": (
                DataTerminalTheme.FONT_FAMILY,
                DataTerminalTheme.FONT_SIZE_SMALL,
                "bold",
            ),
            "tiny": (DataTerminalTheme.FONT_FAMILY, DataTerminalTheme.FONT_SIZE_TINY),
        }

        self.spacing = {
            "large": DataTerminalTheme.PADDING_LARGE,
            "medium": DataTerminalTheme.PADDING_MEDIUM,
            "small": DataTerminalTheme.PADDING_SMALL,
            "tiny": DataTerminalTheme.PADDING_TINY,
        }

        self.radius = {
            "large": DataTerminalTheme.RADIUS_LARGE,
            "medium": DataTerminalTheme.RADIUS_MEDIUM,
            "small": DataTerminalTheme.RADIUS_SMALL,
        }

    def get_glassmorphic_style(self, opacity: float = 0.8) -> Dict[str, str]:
        """Get glassmorphic styling configuration.

        Args:
            opacity: Background opacity (0.0 to 1.0)

        Returns:
            Style dictionary for glassmorphic effect
        """
        return {
            "bg": self.colors["glass_bg"],
            "relief": "flat",
            "bd": 1,
            "highlightbackground": self.colors["border"],
            "highlightthickness": 1,
        }

    def get_button_style(self, variant: str = "primary") -> Dict[str, str]:
        """Get button styling for different variants.

        Args:
            variant: Button variant ('primary', 'secondary', 'success', 'error')

        Returns:
            Button style dictionary
        """
        styles = {
            "primary": {
                "bg": self.colors["accent"],
                "fg": self.colors["background"],
                "activebackground": self.colors["accent_light"],
                "activeforeground": self.colors["background"],
            },
            "secondary": {
                "bg": self.colors["button_bg"],
                "fg": self.colors["text_primary"],
                "activebackground": self.colors["button_hover"],
                "activeforeground": self.colors["text_primary"],
            },
            "success": {
                "bg": self.colors["success"],
                "fg": self.colors["background"],
                "activebackground": self.colors["accent_light"],
                "activeforeground": self.colors["background"],
            },
            "error": {
                "bg": self.colors["error"],
                "fg": self.colors["text_primary"],
                "activebackground": "#CC3333",
                "activeforeground": self.colors["text_primary"],
            },
        }

        base_style = {
            "relief": "flat",
            "bd": 0,
            "cursor": "hand2",
            "font": self.fonts["small"],
        }

        variant_style = styles.get(variant, styles["primary"])
        return {**base_style, **variant_style}


# Initialize theme on import
DataTerminalTheme.configure_customtkinter()
