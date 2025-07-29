"""Theme Configuration - Data Terminal Aesthetic

Defines colors, fonts, and styling for the modern weather dashboard.
"""

from typing import Dict, Any
import customtkinter as ctk


class DataTerminalTheme:
    """Data Terminal color scheme and styling configuration."""
    
    # Core Colors
    BACKGROUND = "#121212"          # Dark background
    PRIMARY = "#00FFAB"             # Neon green
    ACCENT = "#2C2C2C"              # Dark gray
    TEXT = "#EAEAEA"                # Light gray
    TEXT_SECONDARY = "#B0B0B0"      # Medium gray
    
    # Status Colors
    SUCCESS = "#00FF88"             # Bright green
    WARNING = "#FFB800"             # Orange
    ERROR = "#FF4444"               # Red
    INFO = "#00AAFF"                # Blue
    
    # UI Element Colors
    CARD_BG = "#1E1E1E"             # Card background
    BORDER = "#333333"              # Border color
    HOVER = "#2A2A2A"               # Hover state
    SELECTED = "#003D2B"            # Selected state (darker green)
    
    # Chart Colors
    CHART_PRIMARY = PRIMARY
    CHART_SECONDARY = "#00CC88"
    CHART_GRID = "#333333"
    CHART_TEXT = TEXT
    
    # Typography
    FONT_FAMILY = "JetBrains Mono"  # Professional developer font
    FONT_SIZE_LARGE = 24
    FONT_SIZE_MEDIUM = 16
    FONT_SIZE_SMALL = 12
    FONT_SIZE_TINY = 10
    
    # Spacing
    PADDING_LARGE = 20
    PADDING_MEDIUM = 15
    PADDING_SMALL = 10
    PADDING_TINY = 5
    
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
        theme_config = {
            "CTk": {
                "fg_color": [cls.BACKGROUND, cls.BACKGROUND]
            },
            "CTkFrame": {
                "fg_color": [cls.CARD_BG, cls.CARD_BG],
                "border_color": [cls.BORDER, cls.BORDER]
            },
            "CTkButton": {
                "fg_color": [cls.PRIMARY, cls.PRIMARY],
                "hover_color": [cls.SUCCESS, cls.SUCCESS],
                "text_color": [cls.BACKGROUND, cls.BACKGROUND],
                "border_color": [cls.PRIMARY, cls.PRIMARY]
            },
            "CTkEntry": {
                "fg_color": [cls.CARD_BG, cls.CARD_BG],
                "border_color": [cls.BORDER, cls.BORDER],
                "text_color": [cls.TEXT, cls.TEXT],
                "placeholder_text_color": [cls.TEXT_SECONDARY, cls.TEXT_SECONDARY]
            },
            "CTkLabel": {
                "text_color": [cls.TEXT, cls.TEXT]
            },
            "CTkProgressBar": {
                "fg_color": [cls.ACCENT, cls.ACCENT],
                "progress_color": [cls.PRIMARY, cls.PRIMARY]
            },
            "CTkScrollbar": {
                "fg_color": [cls.ACCENT, cls.ACCENT],
                "button_color": [cls.PRIMARY, cls.PRIMARY],
                "button_hover_color": [cls.SUCCESS, cls.SUCCESS]
            }
        }
        
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
                "font": cls.get_font(cls.FONT_SIZE_MEDIUM, "bold")
            },
            "secondary": {
                "fg_color": cls.BACKGROUND,
                "hover_color": cls.HOVER,
                "text_color": cls.PRIMARY,
                "border_color": cls.PRIMARY,
                "border_width": 2,
                "corner_radius": cls.RADIUS_MEDIUM,
                "font": cls.get_font(cls.FONT_SIZE_MEDIUM)
            },
            "danger": {
                "fg_color": cls.ERROR,
                "hover_color": "#CC3333",
                "text_color": cls.TEXT,
                "border_color": cls.ERROR,
                "border_width": 1,
                "corner_radius": cls.RADIUS_MEDIUM,
                "font": cls.get_font(cls.FONT_SIZE_MEDIUM, "bold")
            }
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
                "corner_radius": cls.RADIUS_MEDIUM
            },
            "main": {
                "fg_color": cls.BACKGROUND,
                "border_color": cls.BACKGROUND,
                "border_width": 0,
                "corner_radius": 0
            },
            "highlight": {
                "fg_color": cls.CARD_BG,
                "border_color": cls.PRIMARY,
                "border_width": 2,
                "corner_radius": cls.RADIUS_MEDIUM
            }
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
            "font": cls.get_font(cls.FONT_SIZE_MEDIUM)
        }
    
    @classmethod
    def get_label_style(cls, variant: str = "default") -> Dict[str, Any]:
        """Get label styling configuration."""
        styles = {
            "default": {
                "text_color": cls.TEXT,
                "font": cls.get_font(cls.FONT_SIZE_MEDIUM)
            },
            "title": {
                "text_color": cls.PRIMARY,
                "font": cls.get_font(cls.FONT_SIZE_LARGE, "bold")
            },
            "subtitle": {
                "text_color": cls.TEXT,
                "font": cls.get_font(cls.FONT_SIZE_MEDIUM, "bold")
            },
            "caption": {
                "text_color": cls.TEXT_SECONDARY,
                "font": cls.get_font(cls.FONT_SIZE_SMALL)
            },
            "value": {
                "text_color": cls.PRIMARY,
                "font": cls.get_font(cls.FONT_SIZE_MEDIUM, "bold")
            }
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
            "font": cls.get_font(cls.FONT_SIZE_SMALL)
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
            "font": cls.get_font(cls.FONT_SIZE_SMALL)
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
            "font": cls.get_font(cls.FONT_SIZE_SMALL)
        }
    
    @classmethod
    def get_matplotlib_style(cls) -> Dict[str, Any]:
        """Get matplotlib styling configuration."""
        return {
            'figure.facecolor': cls.BACKGROUND,
            'axes.facecolor': cls.CARD_BG,
            'axes.edgecolor': cls.BORDER,
            'axes.labelcolor': cls.TEXT,
            'axes.spines.left': True,
            'axes.spines.bottom': True,
            'axes.spines.top': False,
            'axes.spines.right': False,
            'xtick.color': cls.TEXT,
            'ytick.color': cls.TEXT,
            'grid.color': cls.CHART_GRID,
            'grid.alpha': 0.3,
            'text.color': cls.TEXT,
            'font.family': 'monospace',
            'font.size': cls.FONT_SIZE_SMALL,
            'lines.color': cls.CHART_PRIMARY,
            'patch.edgecolor': cls.BORDER
        }


# Initialize theme on import
DataTerminalTheme.configure_customtkinter()