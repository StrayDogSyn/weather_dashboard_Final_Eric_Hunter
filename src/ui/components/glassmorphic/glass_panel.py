"""Glass Panel Component

Provides large glassmorphic panels for content areas with optional shadows and highlights.
"""

from typing import Dict, Optional
import customtkinter as ctk
from .base_frame import GlassmorphicFrame


class GlassPanel(GlassmorphicFrame):
    """Large glassmorphic panel for content areas."""

    def __init__(
        self,
        parent,
        width: int = 400,
        height: int = 300,
        theme_colors: Optional[Dict[str, str]] = None,
        glass_opacity: float = 0.08,
        add_shadow: bool = True,
        shadow_elevation: int = 2,
        **kwargs
    ):
        """Initialize glass panel.
        
        Args:
            parent: Parent widget
            width: Panel width
            height: Panel height
            theme_colors: Custom theme colors
            glass_opacity: Glass background opacity
            add_shadow: Whether to add shadow effect
            shadow_elevation: Shadow elevation level (1-5)
            **kwargs: Additional frame arguments
        """
        self.add_shadow = add_shadow
        self.shadow_elevation = shadow_elevation
        self.shadow_frame = None
        
        # Set panel dimensions
        panel_kwargs = {
            "width": width,
            "height": height,
        }
        panel_kwargs.update(kwargs)
        
        super().__init__(parent, theme_colors=theme_colors, **panel_kwargs)
        
        # Apply glass effect with custom opacity
        self.apply_glass_effect(opacity=glass_opacity)
        
        # Add shadow if requested
        if add_shadow:
            self.after(10, self._add_shadow)
    
    def _add_shadow(self):
        """Add elevation shadow behind the panel."""
        try:
            # Shadow properties based on elevation
            shadow_configs = {
                1: {"offset": 1, "blur": 3, "opacity": 0.12},
                2: {"offset": 2, "blur": 6, "opacity": 0.16},
                3: {"offset": 3, "blur": 10, "opacity": 0.19},
                4: {"offset": 4, "blur": 14, "opacity": 0.25},
                5: {"offset": 5, "blur": 18, "opacity": 0.30},
            }
            
            config = shadow_configs.get(self.shadow_elevation, shadow_configs[2])
            
            # Create shadow frame
            shadow_color = self.theme_colors.get("glass_shadow", "#000000")
            shadow_with_opacity = self._apply_shadow_opacity(shadow_color, config["opacity"])
            
            self.shadow_frame = ctk.CTkFrame(
                self.master,
                width=self.winfo_reqwidth() + config["blur"],
                height=self.winfo_reqheight() + config["blur"],
                fg_color=shadow_with_opacity,
                corner_radius=self.cget("corner_radius") + 2,
                border_width=0,
            )
            
            # Position shadow behind panel
            self.shadow_frame.place(
                x=self.winfo_x() + config["offset"],
                y=self.winfo_y() + config["offset"]
            )
            
            # Lower shadow behind panel
            self.shadow_frame.lower(self)
            
        except Exception:
            # Silently fail if shadow cannot be added
            pass
    
    def _apply_shadow_opacity(self, color: str, opacity: float) -> str:
        """Apply opacity to shadow color.
        
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
            
            # For shadows, blend with black instead of white
            r = int(r * opacity)
            g = int(g * opacity)
            b = int(b * opacity)
            
            return f"#{r:02x}{g:02x}{b:02x}"
        except (ValueError, IndexError):
            return color
    
    def add_glow_effect(self, color: str = "#4A9EFF", intensity: float = 0.3, radius: int = 8):
        """Add glow effect around the panel.
        
        Args:
            color: Glow color
            intensity: Glow intensity (0.0 to 1.0)
            radius: Glow radius in pixels
        """
        try:
            glow_color = self._apply_shadow_opacity(color, intensity)
            
            glow_frame = ctk.CTkFrame(
                self.master,
                width=self.winfo_reqwidth() + radius * 2,
                height=self.winfo_reqheight() + radius * 2,
                fg_color=glow_color,
                corner_radius=self.cget("corner_radius") + radius,
                border_width=0,
            )
            
            # Position glow behind panel
            glow_frame.place(
                x=self.winfo_x() - radius,
                y=self.winfo_y() - radius
            )
            
            glow_frame.lower(self)
            
            return glow_frame
            
        except Exception:
            return None
    
    def update_shadow_elevation(self, elevation: int):
        """Update shadow elevation level.
        
        Args:
            elevation: New elevation level (1-5)
        """
        self.shadow_elevation = max(1, min(5, elevation))
        
        # Remove existing shadow
        if self.shadow_frame:
            try:
                self.shadow_frame.destroy()
            except Exception:
                pass
            self.shadow_frame = None
        
        # Add new shadow
        if self.add_shadow:
            self.after(10, self._add_shadow)
    
    def destroy(self):
        """Clean up shadow frame when destroying panel."""
        if self.shadow_frame:
            try:
                self.shadow_frame.destroy()
            except Exception:
                pass
        super().destroy()