"""Core types and effects for glassmorphic UI components.

This module provides the foundational types, enums, and effect classes
that are used across all glassmorphic components in the weather dashboard.

Classes:
    ComponentSize: Enumeration for consistent component sizing
    AnimationState: Enumeration for animation state management
    GlassEffect: Core glassmorphic visual effects configuration
"""

from enum import Enum
from typing import Dict, Any
from dataclasses import dataclass


class ComponentSize(Enum):
    """Enumeration for component sizes.
    
    Provides consistent sizing across all glassmorphic components
    with predefined dimensions and styling parameters.
    """
    SMALL = "small"
    MEDIUM = "medium"
    LARGE = "large"
    EXTRA_LARGE = "extra_large"


class AnimationState(Enum):
    """Enumeration for animation states.
    
    Manages the current state of component animations
    for smooth transitions and visual feedback.
    """
    IDLE = "idle"
    HOVER = "hover"
    ACTIVE = "active"
    DISABLED = "disabled"
    LOADING = "loading"


@dataclass
class GlassEffect:
    """Configuration for glassmorphic visual effects.
    
    This class encapsulates all the visual parameters needed
    to create consistent glassmorphic styling across components.
    
    Attributes:
        opacity: Background opacity (0.0 to 1.0)
        blur_radius: Background blur effect radius
        border_width: Border thickness in pixels
        corner_radius: Corner rounding radius in pixels
        shadow_offset: Shadow offset (x, y) in pixels
        shadow_blur: Shadow blur radius in pixels
        shadow_color: Shadow color in hex format
        gradient_start: Gradient start color in hex format
        gradient_end: Gradient end color in hex format
    """
    opacity: float = 0.15
    blur_radius: int = 10
    border_width: int = 1
    corner_radius: int = 12
    shadow_offset: tuple[int, int] = (0, 4)
    shadow_blur: int = 8
    shadow_color: str = "#000000"
    gradient_start: str = "#FFFFFF"
    gradient_end: str = "#F0F0F0"
    
    def get_style_config(self) -> Dict[str, Any]:
        """Get style configuration dictionary.
        
        Returns:
            Dictionary containing style parameters for UI framework
        """
        return {
            'opacity': self.opacity,
            'blur_radius': self.blur_radius,
            'border_width': self.border_width,
            'corner_radius': self.corner_radius,
            'shadow_offset': self.shadow_offset,
            'shadow_blur': self.shadow_blur,
            'shadow_color': self.shadow_color,
            'gradient_start': self.gradient_start,
            'gradient_end': self.gradient_end
        }
    
    def with_opacity(self, opacity: float) -> 'GlassEffect':
        """Create a new GlassEffect with modified opacity.
        
        Args:
            opacity: New opacity value (0.0 to 1.0)
            
        Returns:
            New GlassEffect instance with updated opacity
        """
        return GlassEffect(
            opacity=opacity,
            blur_radius=self.blur_radius,
            border_width=self.border_width,
            corner_radius=self.corner_radius,
            shadow_offset=self.shadow_offset,
            shadow_blur=self.shadow_blur,
            shadow_color=self.shadow_color,
            gradient_start=self.gradient_start,
            gradient_end=self.gradient_end
        )
    
    def with_corner_radius(self, radius: int) -> 'GlassEffect':
        """Create a new GlassEffect with modified corner radius.
        
        Args:
            radius: New corner radius in pixels
            
        Returns:
            New GlassEffect instance with updated corner radius
        """
        return GlassEffect(
            opacity=self.opacity,
            blur_radius=self.blur_radius,
            border_width=self.border_width,
            corner_radius=radius,
            shadow_offset=self.shadow_offset,
            shadow_blur=self.shadow_blur,
            shadow_color=self.shadow_color,
            gradient_start=self.gradient_start,
            gradient_end=self.gradient_end
        )