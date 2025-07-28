"""Glassmorphic button component.

This module provides the GlassButton class, an interactive glassmorphic
button component with icon support, loading states, and smooth animations.

Classes:
    GlassButton: Interactive glassmorphic button with advanced features
"""

import customtkinter as ctk
from typing import Optional, Callable, Dict, Any
from PIL import Image, ImageTk
import math

from .core_types import ComponentSize, AnimationState, GlassEffect
from src.utils.logger import LoggerMixin
from src.ui.theme_manager import ThemeManager, WeatherTheme


class GlassButton(ctk.CTkButton, LoggerMixin):
    """Glassmorphic button component.
    
    This class provides an interactive glassmorphic button with consistent styling,
    icon support, loading states, and smooth animations for the weather dashboard.
    
    Features:
        - Glassmorphic visual effects with hover animations
        - Icon support with automatic scaling and positioning
        - Loading state with pulse animation
        - Theme-aware styling that adapts to weather conditions
        - Customizable sizes with predefined configurations
        - Accessibility support with keyboard navigation
        - Command callback support for user interactions
    
    Attributes:
        glass_effect: GlassEffect configuration for visual styling
        size: ComponentSize for consistent dimensions
        theme_manager: ThemeManager for dynamic theming
        icon_path: Path to button icon image
        is_loading: Whether button is in loading state
        pulse_animation_id: ID for pulse animation timer
    """
    
    def __init__(
        self,
        parent,
        text: str = "Button",
        command: Optional[Callable] = None,
        glass_effect: Optional[GlassEffect] = None,
        size: ComponentSize = ComponentSize.MEDIUM,
        icon: Optional[str] = None,
        **kwargs
    ):
        """Initialize the glassmorphic button.
        
        Args:
            parent: Parent widget
            text: Button text
            command: Callback function for button clicks
            glass_effect: Optional GlassEffect for custom styling
            size: ComponentSize for dimensions
            icon: Optional path to icon image
            **kwargs: Additional CustomTkinter button arguments
        """
        self.glass_effect = glass_effect or GlassEffect()
        self.size = size
        self.theme_manager = ThemeManager()
        self.icon_path = icon
        self.is_loading = False
        self.pulse_animation_id = None
        
        # Apply glass styling
        glass_config = self._get_glass_button_config()
        kwargs.update(glass_config)
        
        # Set command
        if command:
            kwargs['command'] = command
        
        super().__init__(parent, text=text, **kwargs)
        
        # Load and set icon if provided
        if self.icon_path:
            self._load_icon()
        
        self.logger.debug(f"GlassButton '{text}' initialized with size: {size.value}")
    
    def _get_glass_button_config(self) -> Dict[str, Any]:
        """Generate CustomTkinter configuration for glassmorphic button.
        
        Returns:
            Configuration dictionary for CTkButton
        """
        # Size configurations
        size_configs = {
            ComponentSize.SMALL: {'width': 100, 'height': 32, 'font_size': 12},
            ComponentSize.MEDIUM: {'width': 140, 'height': 36, 'font_size': 14},
            ComponentSize.LARGE: {'width': 180, 'height': 40, 'font_size': 16},
            ComponentSize.EXTRA_LARGE: {'width': 220, 'height': 44, 'font_size': 18}
        }
        
        size_config = size_configs.get(self.size, size_configs[ComponentSize.MEDIUM])
        
        # Get current theme colors
        current_theme = self.theme_manager.get_current_theme()
        
        # Glassmorphic colors based on theme
        if current_theme == WeatherTheme.SUNNY:
            fg_color = "#FFD700"  # Gold
            hover_color = "#FFA500"  # Orange
            text_color = "#000000"  # Black
        elif current_theme == WeatherTheme.RAINY:
            fg_color = "#4682B4"  # Steel blue
            hover_color = "#1E90FF"  # Dodger blue
            text_color = "#FFFFFF"  # White
        elif current_theme == WeatherTheme.CLOUDY:
            fg_color = "#708090"  # Slate gray
            hover_color = "#A9A9A9"  # Dark gray
            text_color = "#FFFFFF"  # White
        elif current_theme == WeatherTheme.SNOWY:
            fg_color = "#E6E6FA"  # Lavender
            hover_color = "#DDA0DD"  # Plum
            text_color = "#000000"  # Black
        else:  # Default/Dark theme
            fg_color = "#3a3a3a"
            hover_color = "#4a4a4a"
            text_color = "#FFFFFF"
        
        return {
            'fg_color': fg_color,
            'hover_color': hover_color,
            'text_color': text_color,
            'border_width': self.glass_effect.border_width,
            'corner_radius': self.glass_effect.corner_radius,
            'width': size_config['width'],
            'height': size_config['height'],
            'font': ctk.CTkFont(size=size_config['font_size'], weight="bold")
        }
    
    def _load_icon(self) -> None:
        """Load and configure button icon."""
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
            ctk_image = ctk.CTkImage(light_image=icon_image, dark_image=icon_image, size=(icon_size, icon_size))
            
            # Set icon
            self.configure(image=ctk_image)
            
            self.logger.debug(f"Icon loaded: {self.icon_path}")
            
        except Exception as e:
            self.logger.error(f"Failed to load icon {self.icon_path}: {e}")
    
    def set_loading_state(self, loading: bool) -> None:
        """Set button loading state with pulse animation.
        
        Args:
            loading: Whether button should show loading state
        """
        self.is_loading = loading
        
        if loading:
            # Disable button and start pulse animation
            self.configure(state="disabled")
            self._start_pulse_animation()
            self.logger.debug("Button loading state enabled")
        else:
            # Enable button and stop pulse animation
            self.configure(state="normal")
            self._stop_pulse_animation()
            self.logger.debug("Button loading state disabled")
    
    def _start_pulse_animation(self) -> None:
        """Start pulse animation for loading state."""
        self._pulse_step(0)
    
    def _pulse_step(self, step: int) -> None:
        """Execute one step of pulse animation.
        
        Args:
            step: Current animation step
        """
        if not self.is_loading:
            return
        
        # Calculate pulse opacity (sine wave)
        opacity = 0.5 + 0.3 * math.sin(step * 0.2)
        
        # Apply pulse effect by modifying colors
        current_config = self._get_glass_button_config()
        pulse_color = self._blend_colors(current_config['fg_color'], "#FFFFFF", opacity)
        
        self.configure(fg_color=pulse_color)
        
        # Schedule next step
        self.pulse_animation_id = self.after(50, lambda: self._pulse_step(step + 1))
    
    def _stop_pulse_animation(self) -> None:
        """Stop pulse animation and restore normal styling."""
        if self.pulse_animation_id:
            self.after_cancel(self.pulse_animation_id)
            self.pulse_animation_id = None
        
        # Restore normal styling
        current_config = self._get_glass_button_config()
        self.configure(fg_color=current_config['fg_color'])
    
    def _blend_colors(self, color1: str, color2: str, factor: float) -> str:
        """Blend two hex colors.
        
        Args:
            color1: First color in hex format
            color2: Second color in hex format
            factor: Blend factor (0.0 to 1.0)
            
        Returns:
            Blended color in hex format
        """
        try:
            # Convert hex to RGB
            r1, g1, b1 = int(color1[1:3], 16), int(color1[3:5], 16), int(color1[5:7], 16)
            r2, g2, b2 = int(color2[1:3], 16), int(color2[3:5], 16), int(color2[5:7], 16)
            
            # Blend colors
            r = int(r1 + (r2 - r1) * factor)
            g = int(g1 + (g2 - g1) * factor)
            b = int(b1 + (b2 - b1) * factor)
            
            # Convert back to hex
            return f"#{r:02x}{g:02x}{b:02x}"
        except:
            return color1  # Return original color on error
    
    def set_icon(self, icon_path: Optional[str]) -> None:
        """Update button icon.
        
        Args:
            icon_path: Path to new icon image, or None to remove icon
        """
        self.icon_path = icon_path
        
        if icon_path:
            self._load_icon()
        else:
            self.configure(image=None)
        
        self.logger.debug(f"Button icon updated: {icon_path}")
    
    def update_theme(self, theme: WeatherTheme) -> None:
        """Update button styling based on weather theme.
        
        Args:
            theme: New weather theme to apply
        """
        self.theme_manager.set_theme(theme)
        
        # Reapply styling with new theme
        current_config = self._get_glass_button_config()
        self.configure(**current_config)
        
        self.logger.debug(f"GlassButton theme updated to: {theme.value}")
    
    def set_glass_effect(self, effect: GlassEffect) -> None:
        """Update glass effect configuration.
        
        Args:
            effect: New GlassEffect configuration
        """
        self.glass_effect = effect
        
        # Reapply styling with new effect
        current_config = self._get_glass_button_config()
        self.configure(**current_config)
        
        self.logger.debug("GlassButton effect updated")
    
    def get_loading_state(self) -> bool:
        """Get current loading state.
        
        Returns:
            True if button is in loading state
        """
        return self.is_loading