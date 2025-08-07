"""Glassmorphic Theme Management

Provides centralized theme management for glassmorphic UI components.
"""

from typing import Dict, Tuple, Optional, Any, Callable
import customtkinter as ctk
from enum import Enum


class ThemeMode(Enum):
    """Theme mode enumeration."""
    LIGHT = "light"
    DARK = "dark"
    AUTO = "auto"


class GlassmorphicTheme:
    """Glassmorphic theme configuration and styling."""
    
    def __init__(self, mode: ThemeMode = ThemeMode.DARK):
        """Initialize glassmorphic theme.
        
        Args:
            mode: Theme mode (light, dark, auto)
        """
        self.mode = mode
        self._observers: list[Callable] = []
        
        # Base color palettes
        self._light_palette = {
            # Background colors
            "bg_primary": "#F0F0F0",
            "bg_secondary": "#FFFFFF",
            "bg_tertiary": "#E8E8E8",
            "bg_glass": "#FFFFFF",
            
            # Glass effect colors
            "glass_bg": ("#FFFFFF", 0.15),
            "glass_border": ("#FFFFFF", 0.3),
            "glass_shadow": ("#000000", 0.1),
            "glass_highlight": ("#FFFFFF", 0.5),
            
            # Text colors
            "text_primary": "#1A1A1A",
            "text_secondary": "#666666",
            "text_tertiary": "#999999",
            "text_inverse": "#FFFFFF",
            
            # Accent colors
            "accent_primary": "#00FF41",
            "accent_secondary": "#0099FF",
            "accent_warning": "#FF9500",
            "accent_error": "#FF3B30",
            "accent_success": "#34C759",
            
            # Interactive states
            "hover_overlay": ("#000000", 0.05),
            "active_overlay": ("#000000", 0.1),
            "disabled_overlay": ("#FFFFFF", 0.5),
            
            # Weather-specific colors
            "weather_sunny": "#FFD700",
            "weather_cloudy": "#87CEEB",
            "weather_rainy": "#4682B4",
            "weather_snowy": "#F0F8FF",
            "weather_stormy": "#696969"
        }
        
        self._dark_palette = {
            # Background colors
            "bg_primary": "#1A1A1A",
            "bg_secondary": "#2D2D2D",
            "bg_tertiary": "#3A3A3A",
            "bg_glass": "#2D2D2D",
            
            # Glass effect colors
            "glass_bg": ("#FFFFFF", 0.1),
            "glass_border": ("#FFFFFF", 0.2),
            "glass_shadow": ("#000000", 0.3),
            "glass_highlight": ("#FFFFFF", 0.3),
            
            # Text colors
            "text_primary": "#FFFFFF",
            "text_secondary": "#CCCCCC",
            "text_tertiary": "#999999",
            "text_inverse": "#1A1A1A",
            
            # Accent colors
            "accent_primary": "#00FF41",
            "accent_secondary": "#0099FF",
            "accent_warning": "#FF9500",
            "accent_error": "#FF453A",
            "accent_success": "#30D158",
            
            # Interactive states
            "hover_overlay": ("#FFFFFF", 0.1),
            "active_overlay": ("#FFFFFF", 0.15),
            "disabled_overlay": ("#000000", 0.3),
            
            # Weather-specific colors
            "weather_sunny": "#FFD700",
            "weather_cloudy": "#87CEEB",
            "weather_rainy": "#4682B4",
            "weather_snowy": "#F0F8FF",
            "weather_stormy": "#696969"
        }
        
        # Glass effect settings
        self.glass_settings = {
            "blur_radius": 10,
            "border_width": 1,
            "corner_radius": 12,
            "shadow_offset": (0, 2),
            "shadow_blur": 8,
            "highlight_width": 1,
            "backdrop_opacity": 0.8
        }
        
        # Animation settings
        self.animation_settings = {
            "duration_fast": 150,
            "duration_normal": 250,
            "duration_slow": 400,
            "easing": "ease_out",
            "hover_scale": 1.02,
            "press_scale": 0.98
        }
        
        # Typography settings
        self.typography = {
            "font_family": "Consolas",
            "font_sizes": {
                "xs": 10,
                "sm": 11,
                "md": 12,
                "lg": 14,
                "xl": 16,
                "xxl": 20,
                "title": 24
            },
            "font_weights": {
                "normal": "normal",
                "bold": "bold"
            },
            "line_heights": {
                "tight": 1.2,
                "normal": 1.4,
                "loose": 1.6
            }
        }
        
        # Spacing system (8px grid)
        self.spacing = {
            "xs": 4,
            "sm": 8,
            "md": 16,
            "lg": 24,
            "xl": 32,
            "xxl": 48
        }
        
        # Component-specific styles
        self.component_styles = {
            "button": {
                "height": 36,
                "padding_x": 16,
                "padding_y": 8,
                "border_radius": 8
            },
            "card": {
                "padding": 16,
                "border_radius": 12,
                "shadow_elevation": 2
            },
            "panel": {
                "padding": 20,
                "border_radius": 16,
                "shadow_elevation": 4
            },
            "input": {
                "height": 40,
                "padding_x": 12,
                "border_radius": 6
            }
        }
    
    def get_color(self, color_key: str) -> str:
        """Get color value for current theme mode.
        
        Args:
            color_key: Color key from palette
            
        Returns:
            Color value as hex string
        """
        palette = self._get_current_palette()
        color_value = palette.get(color_key, "#FF00FF")  # Magenta fallback for missing colors
        
        # Handle tuple colors (color, opacity)
        if isinstance(color_value, tuple):
            return color_value[0]
        
        return color_value
    
    def get_color_with_opacity(self, color_key: str) -> Tuple[str, float]:
        """Get color with opacity for current theme mode.
        
        Args:
            color_key: Color key from palette
            
        Returns:
            Tuple of (color, opacity)
        """
        palette = self._get_current_palette()
        color_value = palette.get(color_key, ("#FF00FF", 1.0))
        
        if isinstance(color_value, tuple):
            return color_value
        
        return (color_value, 1.0)
    
    def _get_current_palette(self) -> Dict[str, Any]:
        """Get current color palette based on theme mode.
        
        Returns:
            Current color palette dictionary
        """
        if self.mode == ThemeMode.LIGHT:
            return self._light_palette
        elif self.mode == ThemeMode.DARK:
            return self._dark_palette
        else:  # AUTO mode
            # Use system theme detection or default to dark
            try:
                system_mode = ctk.get_appearance_mode()
                if system_mode.lower() == "light":
                    return self._light_palette
                else:
                    return self._dark_palette
            except:
                return self._dark_palette
    
    def set_mode(self, mode: ThemeMode):
        """Set theme mode and notify observers.
        
        Args:
            mode: New theme mode
        """
        if self.mode != mode:
            self.mode = mode
            self._notify_observers()
    
    def toggle_mode(self):
        """Toggle between light and dark modes."""
        if self.mode == ThemeMode.LIGHT:
            self.set_mode(ThemeMode.DARK)
        elif self.mode == ThemeMode.DARK:
            self.set_mode(ThemeMode.LIGHT)
        # AUTO mode stays as AUTO
    
    def add_observer(self, callback: Callable):
        """Add theme change observer.
        
        Args:
            callback: Function to call when theme changes
        """
        if callback not in self._observers:
            self._observers.append(callback)
    
    def remove_observer(self, callback: Callable):
        """Remove theme change observer.
        
        Args:
            callback: Function to remove from observers
        """
        if callback in self._observers:
            self._observers.remove(callback)
    
    def _notify_observers(self):
        """Notify all observers of theme change."""
        for callback in self._observers:
            try:
                callback(self)
            except Exception as e:
                print(f"Error notifying theme observer: {e}")
    
    def get_glass_style(self, variant: str = "default") -> Dict[str, Any]:
        """Get glass effect styling configuration.
        
        Args:
            variant: Glass style variant ("default", "subtle", "prominent")
            
        Returns:
            Glass styling configuration
        """
        base_style = {
            "fg_color": self.get_color_with_opacity("glass_bg"),
            "border_color": self.get_color_with_opacity("glass_border"),
            "corner_radius": self.glass_settings["corner_radius"],
            "border_width": self.glass_settings["border_width"]
        }
        
        # Variant modifications
        if variant == "subtle":
            bg_color, bg_opacity = base_style["fg_color"]
            border_color, border_opacity = base_style["border_color"]
            base_style["fg_color"] = (bg_color, bg_opacity * 0.5)
            base_style["border_color"] = (border_color, border_opacity * 0.5)
        elif variant == "prominent":
            bg_color, bg_opacity = base_style["fg_color"]
            border_color, border_opacity = base_style["border_color"]
            base_style["fg_color"] = (bg_color, bg_opacity * 1.5)
            base_style["border_color"] = (border_color, border_opacity * 1.5)
        
        return base_style
    
    def get_component_style(self, component: str) -> Dict[str, Any]:
        """Get styling for specific component type.
        
        Args:
            component: Component type ("button", "card", "panel", "input")
            
        Returns:
            Component styling configuration
        """
        return self.component_styles.get(component, {})
    
    def get_font_config(self, size: str = "md", weight: str = "normal") -> Tuple[str, int, str]:
        """Get font configuration tuple.
        
        Args:
            size: Font size key ("xs", "sm", "md", "lg", "xl", "xxl", "title")
            weight: Font weight ("normal", "bold")
            
        Returns:
            Font configuration tuple (family, size, weight)
        """
        family = self.typography["font_family"]
        font_size = self.typography["font_sizes"].get(size, 12)
        font_weight = self.typography["font_weights"].get(weight, "normal")
        
        return (family, font_size, font_weight)
    
    def get_spacing(self, size: str) -> int:
        """Get spacing value.
        
        Args:
            size: Spacing size key ("xs", "sm", "md", "lg", "xl", "xxl")
            
        Returns:
            Spacing value in pixels
        """
        return self.spacing.get(size, 8)


class ThemeManager:
    """Global theme manager singleton."""
    
    _instance: Optional['ThemeManager'] = None
    _theme: Optional[GlassmorphicTheme] = None
    
    def __new__(cls) -> 'ThemeManager':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._theme is None:
            self._theme = GlassmorphicTheme()
    
    @classmethod
    def get_theme(cls) -> GlassmorphicTheme:
        """Get the global theme instance.
        
        Returns:
            Global glassmorphic theme
        """
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance._theme
    
    @classmethod
    def set_theme(cls, theme: GlassmorphicTheme):
        """Set the global theme instance.
        
        Args:
            theme: New glassmorphic theme
        """
        if cls._instance is None:
            cls._instance = cls()
        cls._instance._theme = theme
    
    @classmethod
    def apply_to_widget(cls, widget, component_type: str = "default", variant: str = "default"):
        """Apply theme styling to a widget.
        
        Args:
            widget: Widget to style
            component_type: Component type for styling
            variant: Style variant
        """
        theme = cls.get_theme()
        
        try:
            # Apply glass styling if supported
            if hasattr(widget, 'configure'):
                glass_style = theme.get_glass_style(variant)
                
                # Convert color tuples to hex for widgets that don't support opacity
                config = {}
                for key, value in glass_style.items():
                    if isinstance(value, tuple):
                        config[key] = value[0]  # Use color without opacity
                    else:
                        config[key] = value
                
                widget.configure(**config)
            
            # Apply component-specific styling
            if component_type != "default":
                component_style = theme.get_component_style(component_type)
                if hasattr(widget, 'configure') and component_style:
                    widget.configure(**component_style)
                    
        except Exception as e:
            print(f"Error applying theme to widget: {e}")
    
    @classmethod
    def get_color(cls, color_key: str) -> str:
        """Get color from global theme.
        
        Args:
            color_key: Color key
            
        Returns:
            Color value
        """
        return cls.get_theme().get_color(color_key)
    
    @classmethod
    def get_font(cls, size: str = "md", weight: str = "normal") -> Tuple[str, int, str]:
        """Get font configuration from global theme.
        
        Args:
            size: Font size key
            weight: Font weight
            
        Returns:
            Font configuration tuple
        """
        return cls.get_theme().get_font_config(size, weight)
    
    @classmethod
    def get_spacing(cls, size: str) -> int:
        """Get spacing from global theme.
        
        Args:
            size: Spacing size key
            
        Returns:
            Spacing value
        """
        return cls.get_theme().get_spacing(size)