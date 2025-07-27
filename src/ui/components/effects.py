"""3D Effects System for Hunter Theme

Provides advanced visual effects including multi-layer shadows,
gradient rendering, smooth animations, and frosted glass processing.
"""

import tkinter as tk
from tkinter import Canvas
from typing import List, Tuple, Optional, Dict, Any
from PIL import Image, ImageDraw, ImageFilter, ImageTk
import math
from ..themes.hunter_glass import HunterColors, HunterStyling, HunterAnimations

class ShadowRenderer:
    """Multi-layer shadow rendering system"""
    
    @staticmethod
    def create_multi_layer_shadow(canvas: Canvas, x: int, y: int, width: int, height: int, 
                                elevation: int = 2) -> List[int]:
        """Create multi-layer drop shadow with depth"""
        shadow_items = []
        
        # Calculate shadow offsets based on elevation
        base_offset = elevation
        blur_radius = elevation * 2
        
        # Layer 1: Dark depth shadow
        shadow_items.append(
            canvas.create_rectangle(
                x + base_offset + 2, y + base_offset + 2,
                x + width + base_offset + 2, y + height + base_offset + 2,
                fill=HunterColors.DROP_SHADOW_DARK,
                outline="",
                tags="shadow_dark"
            )
        )
        
        # Layer 2: Inner glow
        shadow_items.append(
            canvas.create_rectangle(
                x + base_offset, y + base_offset,
                x + width + base_offset, y + height + base_offset,
                fill=HunterColors.DROP_SHADOW_INNER,
                outline="",
                tags="shadow_inner"
            )
        )
        
        # Layer 3: Silver highlight (top-left)
        shadow_items.append(
            canvas.create_rectangle(
                x - 1, y - 1,
                x + width + 1, y + height + 1,
                fill="",
                outline=HunterColors.DROP_SHADOW_LIGHT,
                width=2,
                tags="shadow_light"
            )
        )
        
        return shadow_items
    
    @staticmethod
    def update_shadow_elevation(canvas: Canvas, shadow_items: List[int], 
                              new_elevation: int):
        """Update shadow elevation for animation"""
        if len(shadow_items) >= 2:
            # Update dark shadow position
            coords = canvas.coords(shadow_items[0])
            if len(coords) == 4:
                offset = new_elevation + 2
                canvas.coords(shadow_items[0], 
                            coords[0] - 2 + offset, coords[1] - 2 + offset,
                            coords[2] - 2 + offset, coords[3] - 2 + offset)

class GradientRenderer:
    """Gradient button state management"""
    
    def __init__(self, canvas: Canvas):
        self.canvas = canvas
        self.gradient_cache: Dict[str, ImageTk.PhotoImage] = {}
    
    def create_gradient_button(self, x: int, y: int, width: int, height: int,
                             colors: List[str], state: str = 'normal') -> int:
        """Create gradient-filled button"""
        cache_key = f"{width}x{height}_{state}_{'_'.join(colors)}"
        
        if cache_key not in self.gradient_cache:
            self.gradient_cache[cache_key] = self._generate_gradient_image(
                width, height, colors
            )
        
        return self.canvas.create_image(
            x, y, anchor='nw',
            image=self.gradient_cache[cache_key],
            tags=f"gradient_button_{state}"
        )
    
    def _generate_gradient_image(self, width: int, height: int, 
                               colors: List[str]) -> ImageTk.PhotoImage:
        """Generate gradient image with PIL"""
        image = Image.new('RGBA', (width, height))
        draw = ImageDraw.Draw(image)
        
        # Create vertical gradient
        for y in range(height):
            # Calculate color interpolation
            progress = y / height
            color_index = progress * (len(colors) - 1)
            
            if color_index >= len(colors) - 1:
                color = colors[-1]
            else:
                # Interpolate between two colors
                idx = int(color_index)
                t = color_index - idx
                color = self._interpolate_colors(colors[idx], colors[idx + 1], t)
            
            draw.line([(0, y), (width, y)], fill=color)
        
        return ImageTk.PhotoImage(image)
    
    def _interpolate_colors(self, color1: str, color2: str, t: float) -> str:
        """Interpolate between two hex colors"""
        # Convert hex to RGB
        rgb1 = tuple(int(color1.lstrip('#')[i:i+2], 16) for i in (0, 2, 4))
        rgb2 = tuple(int(color2.lstrip('#')[i:i+2], 16) for i in (0, 2, 4))
        
        # Interpolate
        rgb = tuple(int(rgb1[i] + (rgb2[i] - rgb1[i]) * t) for i in range(3))
        
        # Convert back to hex
        return f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}"

class AnimationManager:
    """Smooth hover animations and elevation changes"""
    
    def __init__(self, widget: tk.Widget):
        self.widget = widget
        self.active_animations: Dict[str, Any] = {}
    
    def animate_elevation(self, target_elevation: int, duration: int = 150,
                        callback: Optional[callable] = None):
        """Animate elevation change with easing"""
        animation_id = "elevation"
        
        # Cancel existing animation
        if animation_id in self.active_animations:
            self.widget.after_cancel(self.active_animations[animation_id])
        
        start_time = self.widget.tk.call('clock', 'milliseconds')
        start_elevation = getattr(self.widget, 'elevation', 2)
        
        def animate_step():
            current_time = self.widget.tk.call('clock', 'milliseconds')
            elapsed = current_time - start_time
            progress = min(elapsed / duration, 1.0)
            
            # Apply easing
            eased_progress = HunterAnimations.ease_out_cubic(progress)
            current_elevation = start_elevation + (target_elevation - start_elevation) * eased_progress
            
            # Update elevation
            if hasattr(self.widget, 'elevation'):
                self.widget.elevation = current_elevation
            
            if progress < 1.0:
                self.active_animations[animation_id] = self.widget.after(16, animate_step)
            else:
                if callback:
                    callback()
                if animation_id in self.active_animations:
                    del self.active_animations[animation_id]
        
        animate_step()
    
    def animate_color_transition(self, target_color: str, duration: int = 200,
                               property_name: str = 'bg'):
        """Animate color transition"""
        animation_id = f"color_{property_name}"
        
        if animation_id in self.active_animations:
            self.widget.after_cancel(self.active_animations[animation_id])
        
        start_color = self.widget.cget(property_name)
        start_time = self.widget.tk.call('clock', 'milliseconds')
        
        def animate_step():
            current_time = self.widget.tk.call('clock', 'milliseconds')
            elapsed = current_time - start_time
            progress = min(elapsed / duration, 1.0)
            
            eased_progress = HunterAnimations.ease_in_out_quad(progress)
            
            # Interpolate color
            current_color = self._interpolate_colors(start_color, target_color, eased_progress)
            self.widget.configure(**{property_name: current_color})
            
            if progress < 1.0:
                self.active_animations[animation_id] = self.widget.after(16, animate_step)
            else:
                if animation_id in self.active_animations:
                    del self.active_animations[animation_id]
        
        animate_step()
    
    def _interpolate_colors(self, color1: str, color2: str, t: float) -> str:
        """Interpolate between two colors"""
        try:
            # Handle hex colors
            if color1.startswith('#') and color2.startswith('#'):
                rgb1 = tuple(int(color1.lstrip('#')[i:i+2], 16) for i in (0, 2, 4))
                rgb2 = tuple(int(color2.lstrip('#')[i:i+2], 16) for i in (0, 2, 4))
                
                rgb = tuple(int(rgb1[i] + (rgb2[i] - rgb1[i]) * t) for i in range(3))
                return f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}"
        except:
            pass
        
        # Fallback to target color
        return color2

class FrostedGlassProcessor:
    """Frosted glass blur processing"""
    
    @staticmethod
    def create_frosted_background(image: Image.Image, blur_radius: int = 15,
                                opacity: float = 0.35) -> ImageTk.PhotoImage:
        """Create frosted glass effect from background image"""
        # Apply Gaussian blur
        blurred = image.filter(ImageFilter.GaussianBlur(radius=blur_radius))
        
        # Create overlay for opacity
        overlay = Image.new('RGBA', blurred.size, (47, 79, 79, int(255 * opacity)))
        
        # Composite the images
        result = Image.alpha_composite(blurred.convert('RGBA'), overlay)
        
        return ImageTk.PhotoImage(result)
    
    @staticmethod
    def apply_glass_distortion(image: Image.Image, strength: float = 0.1) -> Image.Image:
        """Apply subtle distortion for glass effect"""
        width, height = image.size
        distorted = Image.new('RGBA', (width, height))
        
        for y in range(height):
            for x in range(width):
                # Calculate distortion offset
                offset_x = int(math.sin(y * 0.1) * strength * 2)
                offset_y = int(math.cos(x * 0.1) * strength * 2)
                
                # Sample from original image with offset
                src_x = max(0, min(width - 1, x + offset_x))
                src_y = max(0, min(height - 1, y + offset_y))
                
                try:
                    pixel = image.getpixel((src_x, src_y))
                    distorted.putpixel((x, y), pixel)
                except:
                    continue
        
        return distorted