"""Loading Spinner Component

Reusable loading spinner with glassmorphic styling.
"""

import math
import tkinter as tk
from typing import Optional
import customtkinter as ctk
from ..glassmorphic.base_frame import GlassmorphicFrame


class LoadingSpinner(GlassmorphicFrame):
    """Animated loading spinner with glassmorphic styling."""

    def __init__(self, parent, size: int = 50, message: str = "Loading...", **kwargs):
        """Initialize loading spinner.
        
        Args:
            parent: Parent widget
            size: Spinner size in pixels
            message: Loading message to display
            **kwargs: Additional frame arguments
        """
        super().__init__(parent, width=size + 40, height=size + 60, **kwargs)
        
        self.size = size
        self.message = message
        self.is_spinning = False
        self.angle = 0
        self.animation_id: Optional[str] = None
        
        # Spinner styling
        self.spinner_color = "#00FF41"
        self.bg_color = "#0D0D0D"
        self.text_color = "#E0E0E0"
        self.trail_alpha = 0.3
        
        # Animation settings
        self.rotation_speed = 10  # degrees per frame
        self.frame_delay = 50  # milliseconds
        
        # Create canvas for spinner
        self.canvas = tk.Canvas(
            self,
            width=size,
            height=size,
            bg=self.bg_color,
            highlightthickness=0
        )
        self.canvas.pack(pady=(10, 5))
        
        # Create message label
        self.message_label = ctk.CTkLabel(
            self,
            text=message,
            font=("Consolas", 10),
            text_color=self.text_color
        )
        self.message_label.pack(pady=(0, 10))
        
        # Track scheduled calls
        self.scheduled_calls = set()
    
    def start_spinning(self):
        """Start the spinning animation."""
        if not self.is_spinning:
            self.is_spinning = True
            self._animate()
    
    def stop_spinning(self):
        """Stop the spinning animation."""
        self.is_spinning = False
        if self.animation_id:
            try:
                self.after_cancel(self.animation_id)
            except Exception:
                pass
            self.animation_id = None
    
    def set_message(self, message: str):
        """Update the loading message.
        
        Args:
            message: New loading message
        """
        self.message = message
        try:
            self.message_label.configure(text=message)
        except Exception:
            pass
    
    def _animate(self):
        """Animate the spinner rotation."""
        if not self.is_spinning:
            return
        
        try:
            if not self.winfo_exists():
                return
            
            # Clear canvas
            self.canvas.delete("all")
            
            # Draw spinner
            self._draw_spinner()
            
            # Update angle
            self.angle = (self.angle + self.rotation_speed) % 360
            
            # Schedule next frame
            self.animation_id = self.after(self.frame_delay, self._animate)
            
        except Exception as e:
            print(f"Error in spinner animation: {e}")
            self.is_spinning = False
    
    def _draw_spinner(self):
        """Draw the spinner on canvas."""
        try:
            center_x = self.size // 2
            center_y = self.size // 2
            radius = self.size // 3
            
            # Number of dots in the spinner
            num_dots = 12
            dot_size = max(2, self.size // 20)
            
            for i in range(num_dots):
                # Calculate dot position
                dot_angle = math.radians(self.angle + (i * 360 / num_dots))
                dot_x = center_x + radius * math.cos(dot_angle)
                dot_y = center_y + radius * math.sin(dot_angle)
                
                # Calculate alpha based on position (trailing effect)
                alpha = 1.0 - (i / num_dots) * (1.0 - self.trail_alpha)
                
                # Convert alpha to color intensity
                color_intensity = int(255 * alpha)
                dot_color = f"#{color_intensity:02x}{color_intensity:02x}{color_intensity:02x}"
                
                # Draw dot
                self.canvas.create_oval(
                    dot_x - dot_size, dot_y - dot_size,
                    dot_x + dot_size, dot_y + dot_size,
                    fill=dot_color,
                    outline=""
                )
                
        except Exception as e:
            print(f"Error drawing spinner: {e}")
    
    def destroy(self):
        """Clean up when destroying widget."""
        self.stop_spinning()
        
        # Cancel any scheduled calls
        for call_id in self.scheduled_calls.copy():
            try:
                self.after_cancel(call_id)
            except Exception:
                pass
        self.scheduled_calls.clear()
        
        super().destroy()


class ShimmerLoader(GlassmorphicFrame):
    """Shimmer loading effect for content placeholders."""

    def __init__(self, parent, width: int = 200, height: int = 20, **kwargs):
        """Initialize shimmer loader.
        
        Args:
            parent: Parent widget
            width: Loader width
            height: Loader height
            **kwargs: Additional frame arguments
        """
        super().__init__(parent, width=width, height=height, **kwargs)
        
        self.loader_width = width
        self.loader_height = height
        self.is_active = False
        self.shimmer_position = 0
        self.animation_id: Optional[str] = None
        
        # Shimmer styling
        self.base_color = "#2A2A2A"
        self.shimmer_color = "#4A4A4A"
        self.shimmer_width = 50
        self.animation_speed = 5  # pixels per frame
        self.frame_delay = 30  # milliseconds
        
        # Create canvas for shimmer effect
        self.canvas = tk.Canvas(
            self,
            width=width,
            height=height,
            bg=self.base_color,
            highlightthickness=0
        )
        self.canvas.pack(fill="both", expand=True)
    
    def start_shimmer(self):
        """Start the shimmer animation."""
        if not self.is_active:
            self.is_active = True
            self.shimmer_position = -self.shimmer_width
            self._animate_shimmer()
    
    def stop_shimmer(self):
        """Stop the shimmer animation."""
        self.is_active = False
        if self.animation_id:
            try:
                self.after_cancel(self.animation_id)
            except Exception:
                pass
            self.animation_id = None
        
        # Clear canvas
        try:
            self.canvas.delete("all")
        except Exception:
            pass
    
    def _animate_shimmer(self):
        """Animate the shimmer effect."""
        if not self.is_active:
            return
        
        try:
            if not self.winfo_exists():
                return
            
            # Clear canvas
            self.canvas.delete("all")
            
            # Draw base rectangle
            self.canvas.create_rectangle(
                0, 0, self.loader_width, self.loader_height,
                fill=self.base_color,
                outline=""
            )
            
            # Draw shimmer effect
            if 0 <= self.shimmer_position <= self.loader_width:
                # Create gradient effect
                for i in range(self.shimmer_width):
                    x = self.shimmer_position + i
                    if 0 <= x < self.loader_width:
                        # Calculate alpha for gradient
                        alpha = 1.0 - abs(i - self.shimmer_width // 2) / (self.shimmer_width // 2)
                        
                        # Interpolate color
                        base_rgb = self._hex_to_rgb(self.base_color)
                        shimmer_rgb = self._hex_to_rgb(self.shimmer_color)
                        
                        blended_rgb = [
                            int(base_rgb[j] + (shimmer_rgb[j] - base_rgb[j]) * alpha)
                            for j in range(3)
                        ]
                        
                        blended_color = f"#{blended_rgb[0]:02x}{blended_rgb[1]:02x}{blended_rgb[2]:02x}"
                        
                        self.canvas.create_line(
                            x, 0, x, self.loader_height,
                            fill=blended_color,
                            width=1
                        )
            
            # Update position
            self.shimmer_position += self.animation_speed
            if self.shimmer_position > self.loader_width + self.shimmer_width:
                self.shimmer_position = -self.shimmer_width
            
            # Schedule next frame
            self.animation_id = self.after(self.frame_delay, self._animate_shimmer)
            
        except Exception as e:
            print(f"Error in shimmer animation: {e}")
            self.is_active = False
    
    def _hex_to_rgb(self, hex_color: str) -> tuple:
        """Convert hex color to RGB tuple.
        
        Args:
            hex_color: Hex color string
            
        Returns:
            RGB tuple
        """
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    
    def destroy(self):
        """Clean up when destroying widget."""
        self.stop_shimmer()
        super().destroy()


class ProgressSpinner(GlassmorphicFrame):
    """Progress spinner with percentage display."""

    def __init__(self, parent, size: int = 60, **kwargs):
        """Initialize progress spinner.
        
        Args:
            parent: Parent widget
            size: Spinner size in pixels
            **kwargs: Additional frame arguments
        """
        super().__init__(parent, width=size + 20, height=size + 40, **kwargs)
        
        self.size = size
        self.progress = 0.0  # 0.0 to 1.0
        
        # Styling
        self.bg_color = "#0D0D0D"
        self.progress_color = "#00FF41"
        self.track_color = "#333333"
        self.text_color = "#E0E0E0"
        
        # Create canvas
        self.canvas = tk.Canvas(
            self,
            width=size,
            height=size,
            bg=self.bg_color,
            highlightthickness=0
        )
        self.canvas.pack(pady=(10, 5))
        
        # Create percentage label
        self.percentage_label = ctk.CTkLabel(
            self,
            text="0%",
            font=("Consolas", 10, "bold"),
            text_color=self.text_color
        )
        self.percentage_label.pack(pady=(0, 10))
        
        # Initial draw
        self._draw_progress()
    
    def set_progress(self, progress: float):
        """Set progress value.
        
        Args:
            progress: Progress value (0.0 to 1.0)
        """
        self.progress = max(0.0, min(1.0, progress))
        self._draw_progress()
        
        # Update percentage label
        percentage = int(self.progress * 100)
        try:
            self.percentage_label.configure(text=f"{percentage}%")
        except Exception:
            pass
    
    def _draw_progress(self):
        """Draw the progress circle."""
        try:
            if not self.canvas.winfo_exists():
                return
            
            self.canvas.delete("all")
            
            center_x = self.size // 2
            center_y = self.size // 2
            radius = self.size // 2 - 5
            
            # Draw track circle
            self.canvas.create_oval(
                center_x - radius, center_y - radius,
                center_x + radius, center_y + radius,
                outline=self.track_color,
                width=3,
                fill=""
            )
            
            # Draw progress arc
            if self.progress > 0:
                extent = 360 * self.progress
                self.canvas.create_arc(
                    center_x - radius, center_y - radius,
                    center_x + radius, center_y + radius,
                    start=90,  # Start from top
                    extent=-extent,  # Clockwise
                    outline=self.progress_color,
                    width=3,
                    style="arc"
                )
                
        except Exception as e:
            print(f"Error drawing progress: {e}")