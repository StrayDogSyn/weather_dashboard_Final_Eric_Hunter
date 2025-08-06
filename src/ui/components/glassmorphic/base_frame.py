"""Base Glassmorphic Frame Component

Provides the foundational glassmorphic styling for all glass UI components.
"""

from typing import Dict, Optional
import customtkinter as ctk


class GlassmorphicFrame(ctk.CTkFrame):
    """Base frame with glassmorphic styling capabilities."""

    def __init__(self, parent, theme_colors: Optional[Dict[str, str]] = None, **kwargs):
        """Initialize glassmorphic frame.
        
        Args:
            parent: Parent widget
            theme_colors: Custom theme colors for glass effect
            **kwargs: Additional frame arguments
        """
        self.theme_colors = theme_colors or {
            "glass_bg": "#FFFFFF",
            "glass_border": "#E0E0E0", 
            "glass_shadow": "#000000",
            "glass_highlight": "#FFFFFF",
        }
        
        # Apply default glass styling
        glass_kwargs = {
            "fg_color": self._apply_opacity(self.theme_colors["glass_bg"], 0.1),
            "border_color": self._apply_opacity(self.theme_colors["glass_border"], 0.2),
            "border_width": 1,
            "corner_radius": 12,
        }
        glass_kwargs.update(kwargs)
        
        super().__init__(parent, **glass_kwargs)
        
        # Add highlight effect by default
        self.after(1, self._add_glass_highlight)
    
    def apply_glass_effect(
        self,
        opacity: float = 0.1,
        blur_radius: int = 10,
        border_opacity: float = 0.2,
        add_highlight: bool = True,
    ) -> "GlassmorphicFrame":
        """Apply glass morphism effect to this frame.
        
        Args:
            opacity: Background opacity (0.0 to 1.0)
            blur_radius: Blur effect radius (not implemented in CTk)
            border_opacity: Border opacity (0.0 to 1.0)
            add_highlight: Whether to add highlight effect
            
        Returns:
            Self for method chaining
        """
        # Calculate glass colors with opacity
        glass_bg = self._apply_opacity(self.theme_colors["glass_bg"], opacity)
        glass_border = self._apply_opacity(self.theme_colors["glass_border"], border_opacity)
        
        # Configure widget with glass properties
        self.configure(
            fg_color=glass_bg,
            border_color=glass_border,
            border_width=1,
            corner_radius=12
        )
        
        # Add highlight effect
        if add_highlight:
            self._add_glass_highlight()
            
        return self
    
    def _apply_opacity(self, color: str, opacity: float) -> str:
        """Apply opacity to hex color.
        
        Args:
            color: Hex color string
            opacity: Opacity value (0.0 to 1.0)
            
        Returns:
            Color with applied opacity
        """
        try:
            # Remove # if present
            color = color.lstrip("#")
            
            # Convert to RGB
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
    
    def _add_glass_highlight(self):
        """Add subtle highlight to glass element."""
        try:
            # Create highlight frame
            highlight = ctk.CTkFrame(
                self,
                height=2,
                fg_color=self._apply_opacity(self.theme_colors["glass_highlight"], 0.3),
                corner_radius=0,
            )
            highlight.place(relx=0, rely=0, relwidth=1.0)
        except Exception:
            # Silently fail if highlight cannot be added
            pass