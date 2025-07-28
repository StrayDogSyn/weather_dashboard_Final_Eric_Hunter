"""Glassmorphic frame component.

This module provides the GlassFrame class, which serves as the base
glassmorphic container component for the weather dashboard application.

Classes:
    GlassFrame: Base glassmorphic frame with theming and animation support
"""

import customtkinter as ctk
from typing import Optional, Callable, Dict, Any, List
from datetime import datetime

from .core_types import ComponentSize, AnimationState, GlassEffect
from src.utils.logger import LoggerMixin
from src.core.theme_manager import ThemeManager, WeatherTheme


class GlassFrame(ctk.CTkFrame, LoggerMixin):
    """Glassmorphic frame component.
    
    This class provides a base glassmorphic frame with consistent styling,
    theming support, and smooth animations for the weather dashboard.
    
    Features:
        - Glassmorphic visual effects with customizable opacity and blur
        - Responsive sizing with predefined size configurations
        - Theme-aware styling that adapts to weather conditions
        - Smooth hover and focus animations
        - Event handling for user interactions
        - Accessibility support with keyboard navigation
    
    Attributes:
        glass_effect: GlassEffect configuration for visual styling
        size: ComponentSize for consistent dimensions
        theme_manager: ThemeManager for dynamic theming
        animation_state: Current animation state
        hover_callbacks: List of callbacks for hover events
        is_enabled: Whether the frame accepts user interactions
    """
    
    def __init__(
        self,
        parent,
        glass_effect: Optional[GlassEffect] = None,
        size: ComponentSize = ComponentSize.MEDIUM,
        **kwargs
    ):
        """Initialize the glassmorphic frame.
        
        Args:
            parent: Parent widget
            glass_effect: Optional GlassEffect for custom styling
            size: ComponentSize for dimensions
            **kwargs: Additional CustomTkinter frame arguments
        """
        self.glass_effect = glass_effect or GlassEffect()
        self.size = size
        self.theme_manager = ThemeManager()
        self.animation_state = AnimationState.IDLE
        self.hover_callbacks: List[Callable] = []
        self.is_enabled = True
        
        # Apply glass styling
        glass_config = self._get_glass_frame_config()
        kwargs.update(glass_config)
        
        super().__init__(parent, **kwargs)
        
        # Bind events for interactivity
        self._bind_events()
        
        self.logger.debug(f"GlassFrame initialized with size: {size.value}")
    
    def _get_glass_frame_config(self) -> Dict[str, Any]:
        """Generate CustomTkinter configuration for glassmorphic frame.
        
        Returns:
            Configuration dictionary for CTkFrame
        """
        # Size configurations
        size_configs = {
            ComponentSize.SMALL: {'width': 200, 'height': 150},
            ComponentSize.MEDIUM: {'width': 300, 'height': 200},
            ComponentSize.LARGE: {'width': 400, 'height': 300},
            ComponentSize.EXTRA_LARGE: {'width': 500, 'height': 400}
        }
        
        size_config = size_configs.get(self.size, size_configs[ComponentSize.MEDIUM])
        
        # Get current theme colors
        current_theme = self.theme_manager.get_current_theme()
        
        # Glassmorphic colors based on theme
        if current_theme == WeatherTheme.SUNNY:
            fg_color = "#FFE4B5"  # Light golden
            border_color = "#FFD700"  # Gold
        elif current_theme == WeatherTheme.RAINY:
            fg_color = "#4682B4"  # Steel blue
            border_color = "#1E90FF"  # Dodger blue
        elif current_theme == WeatherTheme.CLOUDY:
            fg_color = "#708090"  # Slate gray
            border_color = "#A9A9A9"  # Dark gray
        elif current_theme == WeatherTheme.SNOWY:
            fg_color = "#F0F8FF"  # Alice blue
            border_color = "#E6E6FA"  # Lavender
        else:  # Default/Dark theme
            fg_color = "#2a2a2a"
            border_color = "#444444"
        
        return {
            'fg_color': fg_color,
            'border_color': border_color,
            'border_width': self.glass_effect.border_width,
            'corner_radius': self.glass_effect.corner_radius,
            'width': size_config['width'],
            'height': size_config['height']
        }
    
    def _bind_events(self) -> None:
        """Bind events for frame interactivity."""
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self.bind("<Button-1>", self._on_click)
        self.bind("<FocusIn>", self._on_focus_in)
        self.bind("<FocusOut>", self._on_focus_out)
    
    def _on_enter(self, event) -> None:
        """Handle mouse enter event.
        
        Args:
            event: Tkinter event object
        """
        if self.is_enabled and self.animation_state == AnimationState.IDLE:
            self.animation_state = AnimationState.HOVER
            self._apply_hover_effect()
            
            # Trigger hover callbacks
            for callback in self.hover_callbacks:
                try:
                    callback(True)  # True for hover start
                except Exception as e:
                    self.logger.error(f"Error in hover callback: {e}")
    
    def _on_leave(self, event) -> None:
        """Handle mouse leave event.
        
        Args:
            event: Tkinter event object
        """
        if self.is_enabled and self.animation_state == AnimationState.HOVER:
            self.animation_state = AnimationState.IDLE
            self._remove_hover_effect()
            
            # Trigger hover callbacks
            for callback in self.hover_callbacks:
                try:
                    callback(False)  # False for hover end
                except Exception as e:
                    self.logger.error(f"Error in hover callback: {e}")
    
    def _on_click(self, event) -> None:
        """Handle click event.
        
        Args:
            event: Tkinter event object
        """
        if self.is_enabled:
            self.animation_state = AnimationState.ACTIVE
            self.focus_set()
            self.logger.debug("GlassFrame clicked")
    
    def _on_focus_in(self, event) -> None:
        """Handle focus in event.
        
        Args:
            event: Tkinter event object
        """
        if self.is_enabled:
            # Add focus styling
            current_config = self._get_glass_frame_config()
            focus_border = "#00FF00"  # Green focus indicator
            self.configure(border_color=focus_border)
    
    def _on_focus_out(self, event) -> None:
        """Handle focus out event.
        
        Args:
            event: Tkinter event object
        """
        if self.is_enabled:
            # Remove focus styling
            current_config = self._get_glass_frame_config()
            self.configure(border_color=current_config['border_color'])
    
    def _apply_hover_effect(self) -> None:
        """Apply hover visual effect."""
        # Slightly increase opacity for hover effect
        hover_effect = self.glass_effect.with_opacity(self.glass_effect.opacity + 0.05)
        
        # Update styling for hover
        current_config = self._get_glass_frame_config()
        hover_border = "#FFFFFF"  # White hover border
        self.configure(border_color=hover_border)
    
    def _remove_hover_effect(self) -> None:
        """Remove hover visual effect."""
        # Reset to original styling
        current_config = self._get_glass_frame_config()
        self.configure(border_color=current_config['border_color'])
    
    def add_hover_callback(self, callback: Callable[[bool], None]) -> None:
        """Add callback for hover events.
        
        Args:
            callback: Function to call on hover (receives bool for hover state)
        """
        self.hover_callbacks.append(callback)
    
    def set_enabled(self, enabled: bool) -> None:
        """Set frame enabled state.
        
        Args:
            enabled: Whether frame should accept interactions
        """
        self.is_enabled = enabled
        self.animation_state = AnimationState.IDLE if enabled else AnimationState.DISABLED
        
        # Update visual state
        if enabled:
            current_config = self._get_glass_frame_config()
            self.configure(**current_config)
        else:
            # Disabled styling
            self.configure(
                fg_color="#1a1a1a",
                border_color="#333333"
            )
    
    def update_theme(self, theme: WeatherTheme) -> None:
        """Update frame styling based on weather theme.
        
        Args:
            theme: New weather theme to apply
        """
        self.theme_manager.set_theme(theme)
        
        # Reapply styling with new theme
        current_config = self._get_glass_frame_config()
        self.configure(**current_config)
        
        self.logger.debug(f"GlassFrame theme updated to: {theme.value}")
    
    def get_animation_state(self) -> AnimationState:
        """Get current animation state.
        
        Returns:
            Current AnimationState
        """
        return self.animation_state
    
    def set_glass_effect(self, effect: GlassEffect) -> None:
        """Update glass effect configuration.
        
        Args:
            effect: New GlassEffect configuration
        """
        self.glass_effect = effect
        
        # Reapply styling with new effect
        current_config = self._get_glass_frame_config()
        self.configure(**current_config)
        
        self.logger.debug("GlassFrame effect updated")