"""Style Constants - Centralized Styling System

Provides centralized color constants, spacing, animations, and font definitions
to eliminate duplicate styling throughout the codebase.
"""

from typing import Dict, Tuple, Union
from enum import Enum


class ColorPalette:
    """Centralized color palette for consistent theming."""
    
    # Primary brand colors
    PRIMARY_GREEN = "#00FF41"
    PRIMARY_BLUE = "#0099FF"
    PRIMARY_CYAN = "#00D4FF"
    
    # Background colors
    BG_DARK_PRIMARY = "#0A0A0A"
    BG_DARK_SECONDARY = "#1A1A1A"
    BG_DARK_TERTIARY = "#2A2A2A"
    BG_DARK_CARD = "#2B2B2B"
    
    BG_LIGHT_PRIMARY = "#F0F0F0"
    BG_LIGHT_SECONDARY = "#FFFFFF"
    BG_LIGHT_TERTIARY = "#E8E8E8"
    BG_LIGHT_CARD = "#F8F9FA"
    
    # Glass effect colors (converted from alpha to solid colors)
    GLASS_DARK_BG = "#333333"  # Dark gray instead of transparent white
    GLASS_DARK_BORDER = "#4D4D4D"  # Lighter gray for border
    GLASS_LIGHT_BG = "#E6E6E6"  # Light gray instead of transparent white
    GLASS_LIGHT_BORDER = "#CCCCCC"  # Medium gray for border
    
    # Text colors
    TEXT_DARK_PRIMARY = "#FFFFFF"
    TEXT_DARK_SECONDARY = "#CCCCCC"
    TEXT_DARK_TERTIARY = "#999999"
    
    TEXT_LIGHT_PRIMARY = "#1A1A1A"
    TEXT_LIGHT_SECONDARY = "#666666"
    TEXT_LIGHT_TERTIARY = "#999999"
    
    # Status colors
    SUCCESS = "#34C759"
    WARNING = "#FF9500"
    ERROR = "#FF453A"
    INFO = "#007AFF"
    
    # Interactive states (converted from alpha to solid colors)
    HOVER_DARK = "#3A3A3A"  # Light gray for dark theme hover
    HOVER_LIGHT = "#F0F0F0"  # Very light gray for light theme hover
    ACTIVE_DARK = "#4A4A4A"  # Slightly lighter gray for dark theme active
    ACTIVE_LIGHT = "#E0E0E0"  # Light gray for light theme active
    DISABLED = "#808080"  # Medium gray for disabled state
    
    # Weather-specific colors
    WEATHER_SUNNY = "#FFD700"
    WEATHER_CLOUDY = "#87CEEB"
    WEATHER_RAINY = "#4682B4"
    WEATHER_SNOWY = "#F0F8FF"
    WEATHER_STORMY = "#696969"
    WEATHER_CLEAR = "#00BFFF"
    
    # Chart and data visualization
    CHART_GRID = "#333333"
    CHART_PRIMARY = "#00FF88"
    CHART_SECONDARY = "#0099FF"
    CHART_ACCENT = "#FF6B6B"
    
    # Special UI elements
    BORDER_DEFAULT = "#333333"
    BORDER_FOCUS = "#00FF41"
    BORDER_ERROR = "#FF453A"
    
    # Map and location colors
    MAP_CONTROL_BG = "#4A90E2"
    MAP_CONTROL_HOVER = "#357ABD"
    MAP_OVERLAY = "#001122"
    
    # Search and input colors
    SEARCH_BG = "#1E1E1E"
    SEARCH_BORDER = "#00FFAB"
    SEARCH_HIGHLIGHT = "#00FFAB"
    AUTOCOMPLETE_BG = "#1E1E1E"
    AUTOCOMPLETE_HOVER = "#404040"


class SpacingSystem:
    """Consistent spacing and padding system."""
    
    # Base spacing unit (8px)
    BASE_UNIT = 8
    
    # Padding sizes
    PADDING_NONE = 0
    PADDING_TINY = BASE_UNIT // 2  # 4px
    PADDING_SMALL = BASE_UNIT  # 8px
    PADDING_MEDIUM = BASE_UNIT * 2  # 16px
    PADDING_LARGE = BASE_UNIT * 3  # 24px
    PADDING_XLARGE = BASE_UNIT * 4  # 32px
    
    # Margin sizes (same as padding)
    MARGIN_NONE = PADDING_NONE
    MARGIN_TINY = PADDING_TINY
    MARGIN_SMALL = PADDING_SMALL
    MARGIN_MEDIUM = PADDING_MEDIUM
    MARGIN_LARGE = PADDING_LARGE
    MARGIN_XLARGE = PADDING_XLARGE
    
    # Gap sizes for layouts
    GAP_TINY = 4
    GAP_SMALL = 8
    GAP_MEDIUM = 12
    GAP_LARGE = 16
    GAP_XLARGE = 24
    
    # Border radius
    RADIUS_NONE = 0
    RADIUS_SMALL = 4
    RADIUS_MEDIUM = 8
    RADIUS_LARGE = 12
    RADIUS_XLARGE = 16
    RADIUS_ROUND = 50  # For circular elements


class FontSystem:
    """Centralized font definitions."""
    
    # Font families
    FONT_PRIMARY = "Arial"
    FONT_MONOSPACE = "Consolas"
    FONT_SYSTEM = "System"
    
    # Font sizes
    SIZE_TINY = 10
    SIZE_SMALL = 12
    SIZE_MEDIUM = 14
    SIZE_LARGE = 16
    SIZE_XLARGE = 18
    SIZE_TITLE = 20
    SIZE_HEADING = 24
    
    # Font weights
    WEIGHT_NORMAL = "normal"
    WEIGHT_BOLD = "bold"
    
    # Common font configurations
    @classmethod
    def get_font(cls, size: int = None, weight: str = None, family: str = None) -> Tuple[str, int, str]:
        """Get font configuration tuple.
        
        Args:
            size: Font size (defaults to SIZE_MEDIUM)
            weight: Font weight (defaults to WEIGHT_NORMAL)
            family: Font family (defaults to FONT_PRIMARY)
            
        Returns:
            Font configuration tuple (family, size, weight)
        """
        return (
            family or cls.FONT_PRIMARY,
            size or cls.SIZE_MEDIUM,
            weight or cls.WEIGHT_NORMAL
        )


class AnimationConstants:
    """Standardized animation durations and easing."""
    
    # Duration constants (in milliseconds)
    DURATION_INSTANT = 0
    DURATION_FAST = 150
    DURATION_NORMAL = 250
    DURATION_SLOW = 400
    DURATION_VERY_SLOW = 600
    
    # Shimmer animation
    SHIMMER_DURATION = 1500
    SHIMMER_STEPS = 30
    
    # Loading animation
    LOADING_SPIN_DURATION = 1000
    LOADING_PULSE_DURATION = 800
    
    # Transition types
    EASE_LINEAR = "linear"
    EASE_IN = "ease-in"
    EASE_OUT = "ease-out"
    EASE_IN_OUT = "ease-in-out"


class ComponentSizes:
    """Standard component dimensions."""
    
    # Button sizes
    BUTTON_HEIGHT_SMALL = 28
    BUTTON_HEIGHT_MEDIUM = 32
    BUTTON_HEIGHT_LARGE = 40
    
    # Input field sizes
    INPUT_HEIGHT_SMALL = 28
    INPUT_HEIGHT_MEDIUM = 32
    INPUT_HEIGHT_LARGE = 40
    
    # Icon sizes
    ICON_TINY = 12
    ICON_SMALL = 16
    ICON_MEDIUM = 20
    ICON_LARGE = 24
    ICON_XLARGE = 32
    
    # Panel and card sizes
    CARD_MIN_WIDTH = 200
    CARD_MIN_HEIGHT = 150
    PANEL_MIN_WIDTH = 300
    PANEL_MIN_HEIGHT = 200
    
    # Loading spinner sizes
    SPINNER_SMALL = 16
    SPINNER_MEDIUM = 24
    SPINNER_LARGE = 32


class ThemeVariants:
    """Theme variant definitions for different component states."""
    
    # Frame variants
    FRAME_DEFAULT = "default"
    FRAME_MAIN = "main"
    FRAME_HIGHLIGHT = "highlight"
    FRAME_GLASS = "glass"
    FRAME_CARD = "card"
    
    # Button variants
    BUTTON_PRIMARY = "primary"
    BUTTON_SECONDARY = "secondary"
    BUTTON_DANGER = "danger"
    BUTTON_SUCCESS = "success"
    BUTTON_WARNING = "warning"
    BUTTON_GLASS = "glass"
    
    # Text variants
    TEXT_DEFAULT = "default"
    TEXT_TITLE = "title"
    TEXT_SUBTITLE = "subtitle"
    TEXT_CAPTION = "caption"
    TEXT_VALUE = "value"
    TEXT_ERROR = "error"
    TEXT_SUCCESS = "success"


class LayoutConstants:
    """Layout and positioning constants."""
    
    # Grid system
    GRID_COLUMNS = 12
    GRID_GUTTER = 16
    
    # Container max widths
    CONTAINER_SMALL = 576
    CONTAINER_MEDIUM = 768
    CONTAINER_LARGE = 992
    CONTAINER_XLARGE = 1200
    
    # Z-index layers
    Z_BASE = 0
    Z_CONTENT = 10
    Z_OVERLAY = 100
    Z_MODAL = 1000
    Z_TOOLTIP = 2000
    Z_NOTIFICATION = 3000


# Utility functions for color manipulation
def hex_to_rgba(hex_color: str, alpha: float = 1.0) -> str:
    """Convert hex color to RGBA string.
    
    Args:
        hex_color: Hex color string (e.g., '#FF0000')
        alpha: Alpha value (0.0 to 1.0)
        
    Returns:
        RGBA color string
    """
    hex_color = hex_color.lstrip('#')
    if len(hex_color) == 3:
        hex_color = ''.join([c*2 for c in hex_color])
    
    r = int(hex_color[0:2], 16)
    g = int(hex_color[2:4], 16)
    b = int(hex_color[4:6], 16)
    
    return f"rgba({r}, {g}, {b}, {alpha})"


def get_theme_colors(is_dark: bool = True) -> Dict[str, str]:
    """Get theme-appropriate color set.
    
    Args:
        is_dark: Whether to use dark theme colors
        
    Returns:
        Dictionary of theme colors
    """
    if is_dark:
        return {
            'bg_primary': ColorPalette.BG_DARK_PRIMARY,
            'bg_secondary': ColorPalette.BG_DARK_SECONDARY,
            'bg_tertiary': ColorPalette.BG_DARK_TERTIARY,
            'bg_card': ColorPalette.BG_DARK_CARD,
            'text_primary': ColorPalette.TEXT_DARK_PRIMARY,
            'text_secondary': ColorPalette.TEXT_DARK_SECONDARY,
            'text_tertiary': ColorPalette.TEXT_DARK_TERTIARY,
            'glass_bg': ColorPalette.GLASS_DARK_BG,
            'glass_border': ColorPalette.GLASS_DARK_BORDER,
            'hover': ColorPalette.HOVER_DARK,
            'active': ColorPalette.ACTIVE_DARK,
        }
    else:
        return {
            'bg_primary': ColorPalette.BG_LIGHT_PRIMARY,
            'bg_secondary': ColorPalette.BG_LIGHT_SECONDARY,
            'bg_tertiary': ColorPalette.BG_LIGHT_TERTIARY,
            'bg_card': ColorPalette.BG_LIGHT_CARD,
            'text_primary': ColorPalette.TEXT_LIGHT_PRIMARY,
            'text_secondary': ColorPalette.TEXT_LIGHT_SECONDARY,
            'text_tertiary': ColorPalette.TEXT_LIGHT_TERTIARY,
            'glass_bg': ColorPalette.GLASS_LIGHT_BG,
            'glass_border': ColorPalette.GLASS_LIGHT_BORDER,
            'hover': ColorPalette.HOVER_LIGHT,
            'active': ColorPalette.ACTIVE_LIGHT,
        }


# Export commonly used constants
__all__ = [
    'ColorPalette',
    'SpacingSystem', 
    'FontSystem',
    'AnimationConstants',
    'ComponentSizes',
    'ThemeVariants',
    'LayoutConstants',
    'hex_to_rgba',
    'get_theme_colors',
]