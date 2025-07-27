#!/usr/bin/env python3
"""
Theme Manager - Professional Glassmorphic Design System

This module implements a comprehensive glassmorphic design system including:
- RGBA color management with transparency
- Blur effects and depth layering
- Weather-responsive background themes
- Animation and transition systems
- Accessibility-compliant color schemes
"""

import logging
from typing import Dict, Tuple, Optional, Any
from dataclasses import dataclass
from enum import Enum
import customtkinter as ctk


class WeatherTheme(Enum):
    """Weather-responsive theme variations."""
    SUNNY = "sunny"
    CLOUDY = "cloudy"
    RAINY = "rainy"
    STORMY = "stormy"
    SNOWY = "snowy"
    FOGGY = "foggy"
    NIGHT = "night"
    DEFAULT = "default"


@dataclass
class GlassEffect:
    """Glassmorphic effect configuration."""
    background_alpha: float = 0.15  # Background transparency
    border_alpha: float = 0.3      # Border transparency
    blur_radius: int = 20           # Blur effect radius
    corner_radius: int = 15         # Corner rounding
    border_width: int = 1           # Border thickness
    shadow_offset: Tuple[int, int] = (0, 4)  # Shadow positioning
    shadow_blur: int = 15           # Shadow blur radius
    shadow_alpha: float = 0.1       # Shadow transparency


@dataclass
class ColorScheme:
    """Complete color scheme for glassmorphic design."""
    # Primary colors with RGBA support
    primary: str = "#3B82F6"        # Blue
    primary_light: str = "#60A5FA"  # Light blue
    primary_dark: str = "#1E40AF"   # Dark blue

    # Secondary colors
    secondary: str = "#8B5CF6"      # Purple
    accent: str = "#10B981"         # Green
    warning: str = "#F59E0B"        # Amber
    error: str = "#EF4444"          # Red

    # Neutral colors
    background: str = "#0F172A"     # Dark slate
    surface: str = "#1E293B"        # Slate
    surface_light: str = "#334155"  # Light slate

    # Text colors
    text_primary: str = "#F8FAFC"   # Almost white
    text_secondary: str = "#CBD5E1" # Light gray
    text_muted: str = "#64748B"     # Gray

    # Glass effect colors (with transparency)
    glass_white: str = "#FFFFFF"    # Base white for glass
    glass_black: str = "#000000"    # Base black for glass

    # Weather-specific accent colors
    sunny_accent: str = "#FCD34D"    # Golden yellow
    cloudy_accent: str = "#9CA3AF"   # Gray
    rainy_accent: str = "#3B82F6"    # Blue
    stormy_accent: str = "#6366F1"   # Indigo
    snowy_accent: str = "#E5E7EB"    # Light gray
    foggy_accent: str = "#6B7280"    # Medium gray
    night_accent: str = "#4C1D95"    # Deep purple


class ThemeManager:
    """
    Professional glassmorphic theme management system.

    This class provides comprehensive theme management including:
    - Weather-responsive color schemes
    - Glassmorphic effect calculations
    - RGBA color utilities
    - Animation and transition support
    - Accessibility compliance
    """

    def __init__(self):
        """Initialize the theme manager."""
        self.logger = logging.getLogger(__name__)

        # Current theme state
        self.current_weather_theme = WeatherTheme.DEFAULT
        self.current_color_scheme = ColorScheme()
        self.glass_effect = GlassEffect()

        # Theme configurations for different weather conditions
        self.weather_themes = self._initialize_weather_themes()

        # CustomTkinter theme integration
        self._setup_customtkinter_theme()

        self.logger.info("Theme manager initialized with glassmorphic design system")

    def _initialize_weather_themes(self) -> Dict[WeatherTheme, Dict[str, Any]]:
        """
        Initialize weather-responsive theme configurations.

        Each weather condition has its own color palette and visual effects
        to create an immersive, context-aware user experience.
        """
        return {
            WeatherTheme.SUNNY: {
                "primary_accent": "#FCD34D",  # Golden yellow
                "background_tint": "#FEF3C7",  # Light yellow tint
                "glass_tint": "#FBBF24",      # Warm yellow
                "shadow_color": "#F59E0B",    # Amber shadow
                "animation_speed": 1.2,        # Slightly faster animations
                "blur_intensity": 0.8,         # Less blur for clarity
            },
            WeatherTheme.CLOUDY: {
                "primary_accent": "#9CA3AF",  # Gray
                "background_tint": "#F3F4F6",  # Light gray tint
                "glass_tint": "#6B7280",      # Medium gray
                "shadow_color": "#4B5563",    # Dark gray shadow
                "animation_speed": 1.0,        # Normal speed
                "blur_intensity": 1.0,         # Standard blur
            },
            WeatherTheme.RAINY: {
                "primary_accent": "#3B82F6",  # Blue
                "background_tint": "#DBEAFE",  # Light blue tint
                "glass_tint": "#2563EB",      # Bright blue
                "shadow_color": "#1D4ED8",    # Deep blue shadow
                "animation_speed": 0.8,        # Slower, flowing animations
                "blur_intensity": 1.3,         # More blur for rain effect
            },
            WeatherTheme.STORMY: {
                "primary_accent": "#6366F1",  # Indigo
                "background_tint": "#E0E7FF",  # Light indigo tint
                "glass_tint": "#4F46E5",      # Vibrant indigo
                "shadow_color": "#3730A3",    # Dark indigo shadow
                "animation_speed": 1.5,        # Fast, dramatic animations
                "blur_intensity": 1.1,         # Slightly more blur
            },
            WeatherTheme.SNOWY: {
                "primary_accent": "#E5E7EB",  # Light gray
                "background_tint": "#F9FAFB",  # Almost white tint
                "glass_tint": "#D1D5DB",      # Cool gray
                "shadow_color": "#9CA3AF",    # Soft gray shadow
                "animation_speed": 0.6,        # Slow, gentle animations
                "blur_intensity": 1.4,         # High blur for snow effect
            },
            WeatherTheme.FOGGY: {
                "primary_accent": "#6B7280",  # Medium gray
                "background_tint": "#F3F4F6",  # Misty gray tint
                "glass_tint": "#9CA3AF",      # Foggy gray
                "shadow_color": "#4B5563",    # Muted shadow
                "animation_speed": 0.7,        # Slow, mysterious animations
                "blur_intensity": 1.6,         # Maximum blur for fog
            },
            WeatherTheme.NIGHT: {
                "primary_accent": "#4C1D95",  # Deep purple
                "background_tint": "#1E1B4B",  # Dark purple tint
                "glass_tint": "#5B21B6",      # Rich purple
                "shadow_color": "#312E81",    # Purple shadow
                "animation_speed": 0.9,        # Slightly slower
                "blur_intensity": 1.2,         # Enhanced blur for night
            },
            WeatherTheme.DEFAULT: {
                "primary_accent": "#3B82F6",  # Standard blue
                "background_tint": "#1E293B",  # Default dark
                "glass_tint": "#475569",      # Neutral gray
                "shadow_color": "#0F172A",    # Dark shadow
                "animation_speed": 1.0,        # Normal speed
                "blur_intensity": 1.0,         # Standard blur
            }
        }

    def _setup_customtkinter_theme(self) -> None:
        """
        Configure CustomTkinter with glassmorphic theme settings.

        This method sets up the base CustomTkinter theme that will be
        enhanced with our glassmorphic effects.
        """
        # Set dark mode for glassmorphic base
        ctk.set_appearance_mode("dark")

        # Create custom color theme
        custom_theme = {
            "CTk": {
                "fg_color": [self.current_color_scheme.background, self.current_color_scheme.background]
            },
            "CTkToplevel": {
                "fg_color": [self.current_color_scheme.background, self.current_color_scheme.background]
            },
            "CTkFrame": {
                "fg_color": [self.current_color_scheme.surface, self.current_color_scheme.surface],
                "border_color": [self.current_color_scheme.surface_light, self.current_color_scheme.surface_light]
            },
            "CTkButton": {
                "fg_color": [self.current_color_scheme.primary, self.current_color_scheme.primary],
                "hover_color": [self.current_color_scheme.primary_light, self.current_color_scheme.primary_light],
                "text_color": [self.current_color_scheme.text_primary, self.current_color_scheme.text_primary]
            },
            "CTkLabel": {
                "text_color": [self.current_color_scheme.text_primary, self.current_color_scheme.text_primary]
            },
            "CTkEntry": {
                "fg_color": [self.current_color_scheme.surface, self.current_color_scheme.surface],
                "border_color": [self.current_color_scheme.surface_light, self.current_color_scheme.surface_light],
                "text_color": [self.current_color_scheme.text_primary, self.current_color_scheme.text_primary]
            }
        }

        # Apply a predefined theme instead of custom dictionary
        # CustomTkinter doesn't support direct dictionary themes
        ctk.set_default_color_theme("dark-blue")

    def set_weather_theme(self, weather_condition: str) -> None:
        """
        Set the theme based on current weather conditions.

        Args:
            weather_condition: Weather condition string (e.g., 'sunny', 'rainy')
        """
        try:
            # Map weather condition to theme
            condition_lower = weather_condition.lower()

            if 'sun' in condition_lower or 'clear' in condition_lower:
                new_theme = WeatherTheme.SUNNY
            elif 'cloud' in condition_lower or 'overcast' in condition_lower:
                new_theme = WeatherTheme.CLOUDY
            elif 'rain' in condition_lower or 'drizzle' in condition_lower:
                new_theme = WeatherTheme.RAINY
            elif 'storm' in condition_lower or 'thunder' in condition_lower:
                new_theme = WeatherTheme.STORMY
            elif 'snow' in condition_lower or 'blizzard' in condition_lower:
                new_theme = WeatherTheme.SNOWY
            elif 'fog' in condition_lower or 'mist' in condition_lower:
                new_theme = WeatherTheme.FOGGY
            else:
                new_theme = WeatherTheme.DEFAULT

            if new_theme != self.current_weather_theme:
                self.current_weather_theme = new_theme
                self._apply_weather_theme(new_theme)

                self.logger.info(f"Theme changed to {new_theme.value} for weather: {weather_condition}")

        except Exception as e:
            self.logger.error(f"Failed to set weather theme: {e}")

    def _apply_weather_theme(self, theme: WeatherTheme) -> None:
        """
        Apply the specified weather theme configuration.

        Args:
            theme: WeatherTheme to apply
        """
        theme_config = self.weather_themes[theme]

        # Update glass effect based on weather
        self.glass_effect.blur_radius = int(20 * theme_config["blur_intensity"])

        # Update color scheme with weather-specific accents
        self.current_color_scheme.accent = theme_config["primary_accent"]

    def get_glass_color(self, base_color: str, alpha: float = None) -> str:
        """
        Generate glassmorphic color with transparency.

        Args:
            base_color: Base color in hex format
            alpha: Transparency level (0.0 to 1.0)

        Returns:
            RGBA color string for glassmorphic effects
        """
        if alpha is None:
            alpha = self.glass_effect.background_alpha

        try:
            # Convert hex to RGB
            hex_color = base_color.lstrip('#')
            rgb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

            # Return RGBA format
            return f"rgba({rgb[0]}, {rgb[1]}, {rgb[2]}, {alpha})"

        except Exception as e:
            self.logger.error(f"Failed to convert color {base_color}: {e}")
            return f"rgba(255, 255, 255, {alpha})"  # Fallback to white

    def get_glass_frame_config(self, variant: str = "default") -> Dict[str, Any]:
        """
        Get CustomTkinter frame configuration for glassmorphic effects.

        Args:
            variant: Frame variant ('default', 'primary', 'secondary')

        Returns:
            Dictionary of CustomTkinter frame parameters
        """
        base_config = {
            "corner_radius": self.glass_effect.corner_radius,
            "border_width": self.glass_effect.border_width,
        }

        if variant == "primary":
            base_config.update({
                "fg_color": "#1a1a2e",
                "border_color": "#3b3b5c",
            })
        elif variant == "secondary":
            base_config.update({
                "fg_color": "#2a1a2a",
                "border_color": "#5c3b5c",
            })
        elif variant == "accent":
            base_config.update({
                "fg_color": "#1a2a2a",
                "border_color": "#3b5c5c",
            })
        else:  # default
            base_config.update({
                "fg_color": "#1a1a1a",
                "border_color": "#333333",
            })

        return base_config

    def get_glass_button_config(self, variant: str = "primary") -> Dict[str, Any]:
        """
        Get CustomTkinter button configuration for glassmorphic effects.

        Args:
            variant: Button variant ('primary', 'secondary', 'accent', 'ghost')

        Returns:
            Dictionary of CustomTkinter button parameters
        """
        base_config = {
            "corner_radius": self.glass_effect.corner_radius,
            "border_width": self.glass_effect.border_width,
            "text_color": self.current_color_scheme.text_primary,
            "font": ("Segoe UI", 12, "normal"),
        }

        if variant == "primary":
            base_config.update({
                "fg_color": "#3B82F6",
                "hover_color": "#60A5FA",
                "border_color": "#2563EB",
            })
        elif variant == "secondary":
            base_config.update({
                "fg_color": "#6B7280",
                "hover_color": "#9CA3AF",
                "border_color": "#4B5563",
            })
        elif variant == "accent":
            base_config.update({
                "fg_color": "#10B981",
                "hover_color": "#34D399",
                "border_color": "#059669",
            })
        elif variant == "ghost":
            base_config.update({
                "fg_color": "transparent",
                "hover_color": "#333333",
                "border_color": "#555555",
            })

        return base_config

    def get_glass_entry_config(self) -> Dict[str, Any]:
        """
        Get CustomTkinter entry configuration for glassmorphic effects.

        Returns:
            Dictionary of CustomTkinter entry parameters
        """
        return {
            "corner_radius": self.glass_effect.corner_radius,
            "border_width": self.glass_effect.border_width,
            "fg_color": self.get_glass_color(self.current_color_scheme.glass_white, 0.05),
            "border_color": self.get_glass_color(self.current_color_scheme.glass_white, 0.2),
            "text_color": self.current_color_scheme.text_primary,
            "placeholder_text_color": self.current_color_scheme.text_muted,
            "font": ("Segoe UI", 11, "normal"),
        }

    def get_text_color(self, variant: str = "primary") -> str:
        """
        Get text color for the specified variant.

        Args:
            variant: Text variant ('primary', 'secondary', 'muted', 'accent')

        Returns:
            Color string
        """
        color_map = {
            "primary": self.current_color_scheme.text_primary,
            "secondary": self.current_color_scheme.text_secondary,
            "muted": self.current_color_scheme.text_muted,
            "accent": self.current_color_scheme.accent,
        }

        return color_map.get(variant, self.current_color_scheme.text_primary)

    def get_font_config(self, size: int = 12, weight: str = "normal") -> Tuple[str, int, str]:
        """
        Get font configuration for consistent typography.

        Args:
            size: Font size
            weight: Font weight ('normal', 'bold')

        Returns:
            Font tuple for CustomTkinter
        """
        return ("Segoe UI", size, weight)

    def get_animation_duration(self) -> int:
        """
        Get animation duration based on current weather theme.

        Returns:
            Animation duration in milliseconds
        """
        theme_config = self.weather_themes[self.current_weather_theme]
        base_duration = 300  # Base animation duration
        speed_multiplier = theme_config["animation_speed"]

        return int(base_duration / speed_multiplier)

    def get_weather_accent_color(self) -> str:
        """
        Get the current weather-specific accent color.

        Returns:
            Hex color string
        """
        theme_config = self.weather_themes[self.current_weather_theme]
        return theme_config["primary_accent"]

    def create_gradient_background(self, width: int, height: int) -> str:
        """
        Create CSS-style gradient background for glassmorphic effects.

        Args:
            width: Background width
            height: Background height

        Returns:
            CSS gradient string
        """
        theme_config = self.weather_themes[self.current_weather_theme]
        primary_color = theme_config["primary_accent"]
        background_tint = theme_config["background_tint"]

        # Create a subtle gradient that enhances the glassmorphic effect
        gradient = f"linear-gradient(135deg, {self.get_glass_color(primary_color, 0.1)} 0%, {self.get_glass_color(background_tint, 0.05)} 100%)"

        return gradient

    def get_current_theme_info(self) -> Dict[str, Any]:
        """
        Get information about the current theme state.

        Returns:
            Dictionary containing current theme information
        """
        return {
            "weather_theme": self.current_weather_theme.value,
            "primary_accent": self.get_weather_accent_color(),
            "glass_opacity": self.glass_effect.background_alpha,
            "blur_radius": self.glass_effect.blur_radius,
            "corner_radius": self.glass_effect.corner_radius,
            "animation_duration": self.get_animation_duration(),
        }
