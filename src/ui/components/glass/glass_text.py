"""Glassmorphic text components.

This module provides text-related glassmorphic components including
labels for display and entry fields for user input.

Classes:
    GlassLabel: Glassmorphic text label with typography options
    GlassEntry: Glassmorphic text entry with validation support
"""

import customtkinter as ctk
from typing import Optional, Callable, Dict, Any

from .core_types import ComponentSize, AnimationState, GlassEffect
from src.utils.logger import LoggerMixin
from src.ui.theme_manager import ThemeManager, WeatherTheme


class GlassLabel(ctk.CTkLabel, LoggerMixin):
    """Glassmorphic label component.
    
    This class provides a glassmorphic text label with consistent styling,
    typography options, and theme-aware coloring for the weather dashboard.
    
    Features:
        - Glassmorphic visual effects with transparent backgrounds
        - Typography styles (heading, body, caption, etc.)
        - Theme-aware text coloring that adapts to weather conditions
        - Customizable sizes with predefined configurations
        - Animation support for text transitions
        - Accessibility support with proper contrast ratios
    
    Attributes:
        glass_effect: GlassEffect configuration for visual styling
        size: ComponentSize for consistent dimensions
        theme_manager: ThemeManager for dynamic theming
        text_style: Typography style identifier
        animation_state: Current animation state
    """
    
    def __init__(
        self,
        parent,
        text: str = "Label",
        glass_effect: Optional[GlassEffect] = None,
        size: ComponentSize = ComponentSize.MEDIUM,
        text_style: str = "body",
        **kwargs
    ):
        """Initialize the glassmorphic label.
        
        Args:
            parent: Parent widget
            text: Label text content
            glass_effect: Optional GlassEffect for custom styling
            size: ComponentSize for dimensions
            text_style: Typography style (heading, body, caption, etc.)
            **kwargs: Additional CustomTkinter label arguments
        """
        self.glass_effect = glass_effect or GlassEffect()
        self.size = size
        self.theme_manager = ThemeManager()
        self.text_style = text_style
        self.animation_state = AnimationState.IDLE
        
        # Apply glass styling
        glass_config = self._get_glass_label_config()
        kwargs.update(glass_config)
        
        super().__init__(parent, text=text, **kwargs)
        
        self.logger.debug(f"GlassLabel '{text}' initialized with style: {text_style}")
    
    def _get_glass_label_config(self) -> Dict[str, Any]:
        """Generate CustomTkinter configuration for glassmorphic label.
        
        Returns:
            Configuration dictionary for CTkLabel
        """
        # Typography configurations
        typography_configs = {
            'heading': {'font_size': 24, 'weight': 'bold'},
            'subheading': {'font_size': 18, 'weight': 'bold'},
            'body': {'font_size': 14, 'weight': 'normal'},
            'caption': {'font_size': 12, 'weight': 'normal'},
            'small': {'font_size': 10, 'weight': 'normal'}
        }
        
        typography_config = typography_configs.get(self.text_style, typography_configs['body'])
        
        # Size adjustments
        size_multipliers = {
            ComponentSize.SMALL: 0.8,
            ComponentSize.MEDIUM: 1.0,
            ComponentSize.LARGE: 1.2,
            ComponentSize.EXTRA_LARGE: 1.4
        }
        
        size_multiplier = size_multipliers.get(self.size, 1.0)
        font_size = int(typography_config['font_size'] * size_multiplier)
        
        # Get current theme colors
        current_theme = self.theme_manager.get_current_theme()
        
        # Text colors based on theme
        if current_theme == WeatherTheme.SUNNY:
            text_color = "#8B4513"  # Saddle brown
        elif current_theme == WeatherTheme.RAINY:
            text_color = "#E0E0E0"  # Light gray
        elif current_theme == WeatherTheme.CLOUDY:
            text_color = "#F5F5F5"  # White smoke
        elif current_theme == WeatherTheme.SNOWY:
            text_color = "#2F4F4F"  # Dark slate gray
        else:  # Default/Dark theme
            text_color = "#FFFFFF"
        
        return {
            'text_color': text_color,
            'fg_color': "transparent",  # Transparent background for glassmorphic effect
            'font': ctk.CTkFont(
                size=font_size,
                weight=typography_config['weight']
            )
        }
    
    def set_text_style(self, style: str) -> None:
        """Update label typography style.
        
        Args:
            style: New typography style identifier
        """
        self.text_style = style
        
        # Reapply styling with new typography
        current_config = self._get_glass_label_config()
        self.configure(**current_config)
        
        self.logger.debug(f"GlassLabel text style updated to: {style}")
    
    def animate_text_change(self, new_text: str, duration: int = 500) -> None:
        """Animate text change with fade effect.
        
        Args:
            new_text: New text to display
            duration: Animation duration in milliseconds
        """
        self.animation_state = AnimationState.ACTIVE
        
        # Simple fade out and in animation
        steps = 20
        step_duration = duration // (steps * 2)
        
        def fade_out(step: int):
            if step <= steps:
                alpha = 1.0 - (step / steps)
                # Note: CustomTkinter doesn't support alpha directly,
                # so we'll use a simple text replacement for now
                if step == steps:
                    self.configure(text=new_text)
                    fade_in(0)
                else:
                    self.after(step_duration, lambda: fade_out(step + 1))
        
        def fade_in(step: int):
            if step <= steps:
                alpha = step / steps
                # Restore full opacity
                if step == steps:
                    self.animation_state = AnimationState.IDLE
                else:
                    self.after(step_duration, lambda: fade_in(step + 1))
        
        fade_out(0)
    
    def update_theme(self, theme: WeatherTheme) -> None:
        """Update label styling based on weather theme.
        
        Args:
            theme: New weather theme to apply
        """
        self.theme_manager.set_theme(theme)
        
        # Reapply styling with new theme
        current_config = self._get_glass_label_config()
        self.configure(**current_config)
        
        self.logger.debug(f"GlassLabel theme updated to: {theme.value}")


class GlassEntry(ctk.CTkEntry, LoggerMixin):
    """Glassmorphic entry component.
    
    This class provides a glassmorphic text entry field with consistent styling,
    validation support, and theme-aware coloring for the weather dashboard.
    
    Features:
        - Glassmorphic visual effects with transparent backgrounds
        - Input validation with visual feedback
        - Theme-aware styling that adapts to weather conditions
        - Customizable sizes with predefined configurations
        - Placeholder text support
        - Error state indication with color changes
        - Accessibility support with proper focus handling
    
    Attributes:
        glass_effect: GlassEffect configuration for visual styling
        size: ComponentSize for consistent dimensions
        theme_manager: ThemeManager for dynamic theming
        validation_callback: Optional validation function
        is_valid: Current validation state
    """
    
    def __init__(
        self,
        parent,
        placeholder_text: str = "",
        glass_effect: Optional[GlassEffect] = None,
        size: ComponentSize = ComponentSize.MEDIUM,
        validation_callback: Optional[Callable[[str], bool]] = None,
        **kwargs
    ):
        """Initialize the glassmorphic entry.
        
        Args:
            parent: Parent widget
            placeholder_text: Placeholder text to display
            glass_effect: Optional GlassEffect for custom styling
            size: ComponentSize for dimensions
            validation_callback: Optional function for input validation
            **kwargs: Additional CustomTkinter entry arguments
        """
        self.glass_effect = glass_effect or GlassEffect()
        self.size = size
        self.theme_manager = ThemeManager()
        self.validation_callback = validation_callback
        self.is_valid = True
        
        # Apply glass styling
        glass_config = self._get_glass_entry_config()
        kwargs.update(glass_config)
        
        # Set placeholder text
        if placeholder_text:
            kwargs['placeholder_text'] = placeholder_text
        
        super().__init__(parent, **kwargs)
        
        # Bind validation events
        if self.validation_callback:
            self.bind('<KeyRelease>', self._on_text_change)
            self.bind('<FocusOut>', self._on_focus_out)
        
        self.logger.debug(f"GlassEntry initialized with placeholder: '{placeholder_text}'")
    
    def _get_glass_entry_config(self) -> Dict[str, Any]:
        """Generate CustomTkinter configuration for glassmorphic entry.
        
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
        
        # Get current theme colors
        current_theme = self.theme_manager.get_current_theme()
        
        # Glassmorphic colors based on theme
        if current_theme == WeatherTheme.SUNNY:
            fg_color = "#FFF8DC"  # Cornsilk
            border_color = "#DAA520"  # Goldenrod
            text_color = "#8B4513"  # Saddle brown
            placeholder_color = "#CD853F"  # Peru
        elif current_theme == WeatherTheme.RAINY:
            fg_color = "#2F4F4F"  # Dark slate gray
            border_color = "#4682B4"  # Steel blue
            text_color = "#E0E0E0"  # Light gray
            placeholder_color = "#A9A9A9"  # Dark gray
        elif current_theme == WeatherTheme.CLOUDY:
            fg_color = "#696969"  # Dim gray
            border_color = "#A9A9A9"  # Dark gray
            text_color = "#F5F5F5"  # White smoke
            placeholder_color = "#D3D3D3"  # Light gray
        elif current_theme == WeatherTheme.SNOWY:
            fg_color = "#F8F8FF"  # Ghost white
            border_color = "#E6E6FA"  # Lavender
            text_color = "#2F4F4F"  # Dark slate gray
            placeholder_color = "#9370DB"  # Medium purple
        else:  # Default/Dark theme
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
        """Handle text change for validation.
        
        Args:
            event: Tkinter event object
        """
        if self.validation_callback:
            text = self.get()
            self.is_valid = self.validation_callback(text)
            self._update_validation_styling()
    
    def _on_focus_out(self, event) -> None:
        """Handle focus out event for validation.
        
        Args:
            event: Tkinter event object
        """
        if self.validation_callback:
            text = self.get()
            self.is_valid = self.validation_callback(text)
            self._update_validation_styling()
    
    def _update_validation_styling(self) -> None:
        """Update styling based on validation state.
        
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
        """Set entry error state with optional message.
        
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
        """Get text only if validation passes.
        
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
    
    def update_theme(self, theme: WeatherTheme) -> None:
        """Update entry styling based on weather theme.
        
        Args:
            theme: New weather theme to apply
        """
        self.theme_manager.set_theme(theme)
        
        # Reapply styling with new theme
        current_config = self._get_glass_entry_config()
        self.configure(**current_config)
        
        self.logger.debug(f"GlassEntry theme updated to: {theme.value}")
    
    def set_glass_effect(self, effect: GlassEffect) -> None:
        """Update glass effect configuration.
        
        Args:
            effect: New GlassEffect configuration
        """
        self.glass_effect = effect
        
        # Reapply styling with new effect
        current_config = self._get_glass_entry_config()
        self.configure(**current_config)
        
        self.logger.debug("GlassEntry effect updated")
    
    def get_validation_state(self) -> bool:
        """Get current validation state.
        
        Returns:
            True if entry content is valid
        """
        return self.is_valid