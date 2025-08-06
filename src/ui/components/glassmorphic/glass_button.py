"""Glass Button Component

Provides glassmorphic styled buttons with hover effects and animations.
"""

from typing import Callable, Dict, Optional
import customtkinter as ctk
from .base_frame import GlassmorphicFrame


class GlassButton(ctk.CTkButton):
    """Button with glassmorphic styling and hover effects."""

    def __init__(
        self,
        parent,
        text: str = "",
        command: Optional[Callable] = None,
        theme_colors: Optional[Dict[str, str]] = None,
        glass_opacity: float = 0.15,
        hover_opacity: float = 0.25,
        **kwargs
    ):
        """Initialize glass button.
        
        Args:
            parent: Parent widget
            text: Button text
            command: Button command callback
            theme_colors: Custom theme colors
            glass_opacity: Default glass opacity
            hover_opacity: Hover state opacity
            **kwargs: Additional button arguments
        """
        self.theme_colors = theme_colors or {
            "glass_bg": "#FFFFFF",
            "glass_border": "#E0E0E0",
            "glass_hover": "#F0F0F0",
            "text_color": "#333333",
        }
        
        self.glass_opacity = glass_opacity
        self.hover_opacity = hover_opacity
        self._is_hovered = False
        
        # Apply glass styling
        glass_kwargs = {
            "fg_color": self._apply_opacity(self.theme_colors["glass_bg"], glass_opacity),
            "hover_color": self._apply_opacity(self.theme_colors["glass_hover"], hover_opacity),
            "border_color": self._apply_opacity(self.theme_colors["glass_border"], 0.3),
            "border_width": 1,
            "corner_radius": 8,
            "text_color": self.theme_colors["text_color"],
            "font": ("Segoe UI", 12),
        }
        glass_kwargs.update(kwargs)
        
        super().__init__(parent, text=text, command=command, **glass_kwargs)
        
        # Bind hover events for enhanced interactions
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self.bind("<Button-1>", self._on_click)
    
    def _apply_opacity(self, color: str, opacity: float) -> str:
        """Apply opacity to hex color.
        
        Args:
            color: Hex color string
            opacity: Opacity value (0.0 to 1.0)
            
        Returns:
            Color with applied opacity
        """
        try:
            color = color.lstrip("#")
            r = int(color[0:2], 16)
            g = int(color[2:4], 16)
            b = int(color[4:6], 16)
            
            # Apply opacity (blend with white for glass effect)
            r = int(r + (255 - r) * (1 - opacity))
            g = int(g + (255 - g) * (1 - opacity))
            b = int(b + (255 - b) * (1 - opacity))
            
            return f"#{r:02x}{g:02x}{b:02x}"
        except (ValueError, IndexError):
            return color
    
    def _on_enter(self, event=None):
        """Handle mouse enter event."""
        self._is_hovered = True
        # Add subtle glow effect
        self.configure(border_width=2)
    
    def _on_leave(self, event=None):
        """Handle mouse leave event."""
        self._is_hovered = False
        # Remove glow effect
        self.configure(border_width=1)
    
    def _on_click(self, event):
        """Handle click event with visual feedback."""
        # Brief visual feedback
        original_opacity = self.hover_opacity if self._is_hovered else self.glass_opacity
        click_color = self._apply_opacity(self.theme_colors["glass_bg"], original_opacity + 0.1)
        
        self.configure(fg_color=click_color)
        
        # Reset color after brief delay
        self.after(100, self._reset_color)
    
    def _reset_color(self):
        """Reset button color to normal state."""
        if self._is_hovered:
            color = self._apply_opacity(self.theme_colors["glass_hover"], self.hover_opacity)
        else:
            color = self._apply_opacity(self.theme_colors["glass_bg"], self.glass_opacity)
        
        self.configure(fg_color=color)
    
    def set_glass_opacity(self, opacity: float):
        """Update glass opacity.
        
        Args:
            opacity: New opacity value (0.0 to 1.0)
        """
        self.glass_opacity = opacity
        if not self._is_hovered:
            color = self._apply_opacity(self.theme_colors["glass_bg"], opacity)
            self.configure(fg_color=color)
    
    def set_theme_colors(self, theme_colors: Dict[str, str]):
        """Update theme colors.
        
        Args:
            theme_colors: New theme color dictionary
        """
        self.theme_colors.update(theme_colors)
        self._reset_color()