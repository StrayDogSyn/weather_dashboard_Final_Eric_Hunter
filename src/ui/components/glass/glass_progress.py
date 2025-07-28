"""Glassmorphic progress bar component.

This module provides the GlassProgressBar class, a progress indicator
with glassmorphic styling and smooth animations.

Classes:
    GlassProgressBar: Glassmorphic progress bar with animation support
"""

import customtkinter as ctk
from typing import Optional, Dict, Any

from .core_types import ComponentSize, AnimationState, GlassEffect
from src.utils.logger import LoggerMixin
from src.ui.theme_manager import ThemeManager, WeatherTheme


class GlassProgressBar(ctk.CTkProgressBar, LoggerMixin):
    """Glassmorphic progress bar component.
    
    This class provides professional progress indication with glassmorphic
    styling and smooth animations for the weather dashboard.
    
    Features:
        - Glassmorphic visual effects with transparent backgrounds
        - Smooth progress animations with customizable duration
        - Theme-aware styling that adapts to weather conditions
        - Customizable sizes with predefined configurations
        - Value animation support for smooth transitions
        - Accessibility support with proper contrast ratios
    
    Attributes:
        glass_effect: GlassEffect configuration for visual styling
        size: ComponentSize for consistent dimensions
        theme_manager: ThemeManager for dynamic theming
        animation_state: Current animation state
        target_value: Target progress value for animations
        animation_id: ID for current animation timer
    """
    
    def __init__(
        self,
        parent,
        glass_effect: Optional[GlassEffect] = None,
        size: ComponentSize = ComponentSize.MEDIUM,
        **kwargs
    ):
        """Initialize the glassmorphic progress bar.
        
        Args:
            parent: Parent widget
            glass_effect: Optional GlassEffect for custom styling
            size: ComponentSize for dimensions
            **kwargs: Additional CustomTkinter progress bar arguments
        """
        self.glass_effect = glass_effect or GlassEffect()
        self.size = size
        self.theme_manager = ThemeManager()
        self.animation_state = AnimationState.IDLE
        self.target_value = 0.0
        self.animation_id = None
        
        # Apply glass styling
        glass_config = self._get_glass_progress_config()
        kwargs.update(glass_config)
        
        super().__init__(parent, **kwargs)
        
        self.logger.debug(f"GlassProgressBar initialized with size: {size.value}")
    
    def _get_glass_progress_config(self) -> Dict[str, Any]:
        """Generate CustomTkinter configuration for glassmorphic progress bar.
        
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
        
        # Get current theme colors
        current_theme = self.theme_manager.get_current_theme()
        
        # Glassmorphic colors based on theme
        if current_theme == WeatherTheme.SUNNY:
            fg_color = "#FFE4B5"  # Moccasin
            progress_color = "#FF8C00"  # Dark orange
        elif current_theme == WeatherTheme.RAINY:
            fg_color = "#2F4F4F"  # Dark slate gray
            progress_color = "#00CED1"  # Dark turquoise
        elif current_theme == WeatherTheme.CLOUDY:
            fg_color = "#696969"  # Dim gray
            progress_color = "#87CEEB"  # Sky blue
        elif current_theme == WeatherTheme.SNOWY:
            fg_color = "#F0F8FF"  # Alice blue
            progress_color = "#4169E1"  # Royal blue
        else:  # Default/Dark theme
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
        """Animate progress bar to target value.
        
        Args:
            target_value: Target progress value (0.0 to 1.0)
            duration: Animation duration in milliseconds
        """
        # Clamp target value to valid range
        target_value = max(0.0, min(1.0, target_value))
        
        self.target_value = target_value
        self.animation_state = AnimationState.ACTIVE
        
        # Cancel any existing animation
        if self.animation_id:
            self.after_cancel(self.animation_id)
        
        # Start animation
        current_value = self.get()
        steps = 50
        step_duration = duration // steps
        step_increment = (target_value - current_value) / steps
        
        self._animate_step(current_value, step_increment, step_duration, 0, steps)
        
        self.logger.debug(f"Progress animation started: {current_value:.2f} -> {target_value:.2f}")
    
    def _animate_step(self, start_value: float, increment: float, step_duration: int, step: int, total_steps: int) -> None:
        """Execute one step of progress animation.
        
        Args:
            start_value: Starting progress value
            increment: Value increment per step
            step_duration: Duration of each step in milliseconds
            step: Current step number
            total_steps: Total number of animation steps
        """
        if step <= total_steps and self.animation_state == AnimationState.ACTIVE:
            # Calculate current value with easing
            progress = step / total_steps
            eased_progress = self._ease_in_out_cubic(progress)
            new_value = start_value + (self.target_value - start_value) * eased_progress
            
            # Update progress bar
            self.set(new_value)
            
            if step < total_steps:
                # Schedule next step
                self.animation_id = self.after(
                    step_duration,
                    lambda: self._animate_step(start_value, increment, step_duration, step + 1, total_steps)
                )
            else:
                # Animation complete
                self.animation_state = AnimationState.IDLE
                self.animation_id = None
                self.logger.debug("Progress animation completed")
    
    def _ease_in_out_cubic(self, t: float) -> float:
        """Cubic easing function for smooth animations.
        
        Args:
            t: Time parameter (0.0 to 1.0)
            
        Returns:
            Eased value (0.0 to 1.0)
        """
        if t < 0.5:
            return 4 * t * t * t
        else:
            return 1 - pow(-2 * t + 2, 3) / 2
    
    def set_value_instantly(self, value: float) -> None:
        """Set progress value instantly without animation.
        
        Args:
            value: Progress value (0.0 to 1.0)
        """
        # Cancel any existing animation
        if self.animation_id:
            self.after_cancel(self.animation_id)
            self.animation_id = None
        
        self.animation_state = AnimationState.IDLE
        
        # Clamp value to valid range
        value = max(0.0, min(1.0, value))
        self.set(value)
        
        self.logger.debug(f"Progress value set instantly: {value:.2f}")
    
    def pulse_animation(self, duration: int = 2000) -> None:
        """Start a pulsing animation for indeterminate progress.
        
        Args:
            duration: Duration of one pulse cycle in milliseconds
        """
        self.animation_state = AnimationState.LOADING
        
        # Cancel any existing animation
        if self.animation_id:
            self.after_cancel(self.animation_id)
        
        self._pulse_step(0, duration)
        
        self.logger.debug("Progress pulse animation started")
    
    def _pulse_step(self, step: int, duration: int) -> None:
        """Execute one step of pulse animation.
        
        Args:
            step: Current animation step
            duration: Total duration of one pulse cycle
        """
        if self.animation_state != AnimationState.LOADING:
            return
        
        # Calculate pulse value using sine wave
        import math
        progress = (step % 100) / 100.0  # 0 to 1 over 100 steps
        pulse_value = 0.5 + 0.4 * math.sin(progress * 2 * math.pi)
        
        # Update progress bar
        self.set(pulse_value)
        
        # Schedule next step
        step_duration = duration // 100
        self.animation_id = self.after(
            step_duration,
            lambda: self._pulse_step(step + 1, duration)
        )
    
    def stop_animation(self) -> None:
        """Stop any current animation."""
        if self.animation_id:
            self.after_cancel(self.animation_id)
            self.animation_id = None
        
        self.animation_state = AnimationState.IDLE
        
        self.logger.debug("Progress animation stopped")
    
    def update_theme(self, theme: WeatherTheme) -> None:
        """Update progress bar styling based on weather theme.
        
        Args:
            theme: New weather theme to apply
        """
        self.theme_manager.set_theme(theme)
        
        # Reapply styling with new theme
        current_config = self._get_glass_progress_config()
        self.configure(**current_config)
        
        self.logger.debug(f"GlassProgressBar theme updated to: {theme.value}")
    
    def set_glass_effect(self, effect: GlassEffect) -> None:
        """Update glass effect configuration.
        
        Args:
            effect: New GlassEffect configuration
        """
        self.glass_effect = effect
        
        # Reapply styling with new effect
        current_config = self._get_glass_progress_config()
        self.configure(**current_config)
        
        self.logger.debug("GlassProgressBar effect updated")
    
    def get_animation_state(self) -> AnimationState:
        """Get current animation state.
        
        Returns:
            Current AnimationState
        """
        return self.animation_state
    
    def is_animating(self) -> bool:
        """Check if progress bar is currently animating.
        
        Returns:
            True if animation is in progress
        """
        return self.animation_state in [AnimationState.ACTIVE, AnimationState.LOADING]