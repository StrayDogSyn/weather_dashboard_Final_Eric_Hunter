"""Hunter Theme Glassmorphic UI System

Defines the Hunter theme color palette, 3D styling constants, and utility functions
for creating glassmorphic effects with dark slate, hunter green, and silver accents.
"""

from typing import List, Tuple
import tkinter as tk
from PIL import Image, ImageFilter

# Hunter Theme Color Palette
class HunterColors:
    """Hunter theme color constants"""
    
    # Base colors
    HUNTER_DARK_SLATE = "#2F4F4F"
    HUNTER_BLACK = "#1C1C1C"
    HUNTER_GREEN = "#355E3B"
    HUNTER_SILVER = "#C0C0C0"
    
    # Glass overlays - using RGB with alpha values for transparency
    GLASS_HUNTER_PRIMARY = "#2F4F4F"      # Dark slate (use with alpha in code)
    GLASS_HUNTER_ACCENT = "#C0C0C0"       # Silver (use with alpha in code)
    GLASS_HUNTER_HOVER = "#355E3B"        # Hunter green (use with alpha in code)
    
    # Alpha values for transparency effects
    ALPHA_LIGHT = 0.2   # 20% opacity
    ALPHA_MEDIUM = 0.4  # 40% opacity
    ALPHA_HEAVY = 0.5   # 50% opacity
    
    # 3D Button gradients
    BUTTON_RAISED = ["#C0C0C0", "#355E3B", "#2F4F4F"]  # Silver→Green→Slate
    BUTTON_PRESSED = ["#2F4F4F", "#355E3B", "#1C1C1C"] # Inverted for depth
    
    # Drop shadows (multi-layer for 3D depth)
    DROP_SHADOW_LIGHT = "#E0E0E0"   # Silver highlight
    DROP_SHADOW_DARK = "#404040"    # Black depth shadow
    DROP_SHADOW_INNER = "#7A9A7A"   # Inner glow

class HunterStyling:
    """3D styling and animation constants"""
    
    # Corner radius
    CORNER_RADIUS = 12
    
    # Shadow depths
    SHADOW_NORMAL = 2
    SHADOW_HOVER = 6
    SHADOW_PRESSED = 1
    
    # Blur effects
    GLASS_BLUR_RADIUS = 15
    PANEL_OPACITY = 0.35
    
    # Animation timing
    HOVER_DURATION = 150  # milliseconds
    PRESS_DURATION = 100
    
    # Border widths
    SILVER_BORDER = 1
    GLASS_BORDER = 2

class BlurEffects:
    """Utility functions for blur and glass effects"""
    
    @staticmethod
    def create_gaussian_blur(image: Image.Image, radius: int = 15) -> Image.Image:
        """Apply Gaussian blur to create frosted glass effect"""
        return image.filter(ImageFilter.GaussianBlur(radius=radius))
    
    @staticmethod
    def create_glass_overlay(width: int, height: int, color: str, opacity: float = 0.35) -> str:
        """Generate CSS-like color string for glass overlay"""
        # Convert hex to RGBA
        hex_color = color.lstrip('#')
        rgb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        return f"rgba({rgb[0]}, {rgb[1]}, {rgb[2]}, {opacity})"
    
    @staticmethod
    def get_gradient_stops(colors: List[str], steps: int = 3) -> List[Tuple[float, str]]:
        """Generate gradient stops for smooth color transitions"""
        stops = []
        for i, color in enumerate(colors):
            position = i / (len(colors) - 1) if len(colors) > 1 else 0
            stops.append((position, color))
        return stops

def create_gradient_stops(colors: list, steps: int = 100) -> list:
    """
    Create gradient color stops for smooth transitions.
    
    Args:
        colors: List of hex color strings
        steps: Number of gradient steps
        
    Returns:
        List of interpolated color strings
    """
    if len(colors) < 2:
        return colors
    
    gradient_stops = []
    segment_steps = steps // (len(colors) - 1)
    
    for i in range(len(colors) - 1):
        start_color = colors[i]
        end_color = colors[i + 1]
        
        # Convert hex to RGB
        start_rgb = tuple(int(start_color[j:j+2], 16) for j in (1, 3, 5))
        end_rgb = tuple(int(end_color[j:j+2], 16) for j in (1, 3, 5))
        
        # Interpolate between colors
        for step in range(segment_steps):
            ratio = step / segment_steps
            r = int(start_rgb[0] + (end_rgb[0] - start_rgb[0]) * ratio)
            g = int(start_rgb[1] + (end_rgb[1] - start_rgb[1]) * ratio)
            b = int(start_rgb[2] + (end_rgb[2] - start_rgb[2]) * ratio)
            
            gradient_stops.append(f"#{r:02x}{g:02x}{b:02x}")
    
    return gradient_stops


class AnimationCurves:
    """
    Animation timing curves for smooth transitions.
    """
    
    @staticmethod
    def ease_in_out(t: float) -> float:
        """Ease in-out cubic curve."""
        return 3 * t * t - 2 * t * t * t
    
    @staticmethod
    def ease_out(t: float) -> float:
        """Ease out curve."""
        return 1 - (1 - t) ** 3
    
    @staticmethod
    def ease_in(t: float) -> float:
        """Ease in curve."""
        return t ** 3


class HunterGlassTheme:
    """
    Hunter theme class providing color constants and styling.
    """
    
    def __init__(self):
        # Base colors
        self.HUNTER_BLACK = HunterColors.HUNTER_BLACK
        self.HUNTER_DARK_SLATE = HunterColors.HUNTER_DARK_SLATE
        self.HUNTER_GREEN = HunterColors.HUNTER_GREEN
        self.HUNTER_SILVER = HunterColors.HUNTER_SILVER
        
        # Glass overlays
        self.GLASS_HUNTER_PRIMARY = HunterColors.GLASS_HUNTER_PRIMARY
        self.GLASS_HUNTER_ACCENT = HunterColors.GLASS_HUNTER_ACCENT
        self.GLASS_HUNTER_HOVER = HunterColors.GLASS_HUNTER_HOVER
        
        # Styling constants
        self.styling = HunterStyling()


class HunterAnimations:
    """Animation and transition utilities"""
    
    @staticmethod
    def ease_out_cubic(t: float) -> float:
        """Cubic ease-out animation curve"""
        return 1 - pow(1 - t, 3)
    
    @staticmethod
    def ease_in_out_quad(t: float) -> float:
        """Quadratic ease-in-out animation curve"""
        return 2 * t * t if t < 0.5 else 1 - pow(-2 * t + 2, 2) / 2