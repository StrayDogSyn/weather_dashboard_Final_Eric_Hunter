"""Beautiful weather visualization using only Canvas - no WebView needed"""

from tkinter import Canvas
import random
import threading
from typing import Optional, Dict, List, Tuple
import logging
import time
import customtkinter as ctk

from ..theme import DataTerminalTheme
from ..safe_widgets import SafeWidget
from ...utils.error_wrapper import ensure_main_thread


class WeatherVisualizationPanel(SafeWidget, ctk.CTkFrame):
    """Beautiful weather visualization using only Canvas - no WebView needed"""
    
    def __init__(self, parent, weather_service=None, config=None, **kwargs):
        SafeWidget.__init__(self)
        ctk.CTkFrame.__init__(self, parent, **kwargs)
        self.weather_service = weather_service
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Widget is alive by default
        
        # Animation state
        self.animation_running = True
        self.particles = []
        self.wind_lines = []
        self.temp_grid = []
        self.current_weather = None
        
        # Configure frame
        self.configure(fg_color=DataTerminalTheme.BACKGROUND)
        
        # Create header
        self._create_header()
        
        # Create main canvas
        self.canvas = Canvas(
            self,
            bg='#1a1a1a',
            highlightthickness=0
        )
        self.canvas.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
        # Bind resize event
        self.canvas.bind('<Configure>', self._on_canvas_resize)
        
        # Initialize visualization
        self.safe_after(100, self._initialize_visualization)
        
        # Start weather updates
        self._start_weather_updates()
        
    def _create_header(self):
        """Create the header section."""
        header_frame = ctk.CTkFrame(
            self,
            fg_color=DataTerminalTheme.ACCENT,
            corner_radius=10,
            height=80
        )
        header_frame.pack(fill="x", padx=20, pady=20)
        header_frame.pack_propagate(False)
        
        # Title
        title_label = ctk.CTkLabel(
            header_frame,
            text="🌤️ Live Weather Visualization",
            font=(DataTerminalTheme.FONT_FAMILY, 24, "bold"),
            text_color="white"
        )
        title_label.pack(side="left", padx=20, pady=20)
        
        # Status
        self.status_label = ctk.CTkLabel(
            header_frame,
            text="Initializing weather visualization...",
            font=(DataTerminalTheme.FONT_FAMILY, 12),
            text_color="white"
        )
        self.status_label.pack(side="right", padx=20, pady=20)
        
    def _initialize_visualization(self):
        """Initialize the weather visualization"""
        self._create_background_gradient()
        self._create_temperature_grid()
        self._create_wind_flow()
        self._create_weather_info_overlay()
        self._start_animations()
        
        # Update with real weather data if available
        if self.weather_service:
            try:
                weather_data = self.weather_service.get_current_weather("London")
                if weather_data:
                    self.update_weather_data(weather_data)
            except Exception as e:
                self.logger.error(f"Failed to get initial weather data: {e}")
    
    def _create_background_gradient(self):
        """Create atmospheric gradient background"""
        width = self.canvas.winfo_width()
        height = self.canvas.winfo_height()
        
        if width <= 1 or height <= 1:
            return
        
        # Create smooth gradient effect with fewer lines for better performance
        gradient_steps = min(height // 4, 100)  # Limit gradient steps
        step_height = height / gradient_steps
        
        for i in range(gradient_steps):
            y_pos = int(i * step_height)
            next_y = int((i + 1) * step_height)
            
            # Create a more sophisticated gradient
            progress = i / gradient_steps
            
            # Sky-like gradient: darker at top, lighter at bottom
            r = int(20 + progress * 40)  # 20 to 60
            g = int(25 + progress * 45)  # 25 to 70
            b = int(35 + progress * 55)  # 35 to 90
            
            color = f'#{r:02x}{g:02x}{b:02x}'
            
            # Create rectangle instead of lines for smoother appearance
            self.canvas.create_rectangle(
                0, y_pos, width, next_y,
                fill=color, outline=color, tags="background"
            )
    
    def _create_temperature_grid(self):
        """Create temperature heatmap with smooth circles"""
        width = self.canvas.winfo_width()
        height = self.canvas.winfo_height()
        
        if width <= 1 or height <= 1:
            return
        
        grid_size = 80  # Larger grid for better visual appeal
        cols = width // grid_size + 1
        rows = height // grid_size + 1
        
        for row in range(rows):
            for col in range(cols):
                x = col * grid_size + random.randint(-20, 20)  # Add some randomness
                y = row * grid_size + random.randint(-20, 20)
                
                # Generate temperature-based color
                temp = 15 + random.uniform(-10, 15)  # Mock temperature
                color = self._temp_to_color(temp)
                
                # Create smooth circles instead of rectangles
                radius = random.randint(15, 35)
                circle = self.canvas.create_oval(
                    x - radius, y - radius, x + radius, y + radius,
                    fill=color,
                    outline="",
                    tags=("temp_grid", f"grid_{row}_{col}")
                )
                
                # Add transparency effect with multiple overlapping circles
                for i in range(3):
                    smaller_radius = radius - (i * 8)
                    if smaller_radius > 0:
                        alpha_color = self._adjust_color_alpha(color, 0.3 - i * 0.1)
                        self.canvas.create_oval(
                            x - smaller_radius, y - smaller_radius, 
                            x + smaller_radius, y + smaller_radius,
                            fill=alpha_color,
                            outline="",
                            tags=("temp_grid", f"grid_{row}_{col}_layer_{i}")
                        )
                
                self.temp_grid.append((circle, temp))
    
    def _temp_to_color(self, temp: float) -> str:
        """Convert temperature to color with smooth gradients"""
        # Normalize temperature to 0-1 range
        normalized = max(0, min(1, (temp + 20) / 60))  # -20°C to 40°C range
        
        if normalized < 0.2:  # Very cold
            r, g, b = 0, int(100 + normalized * 400), int(200 + normalized * 255)
        elif normalized < 0.4:  # Cold
            r, g, b = 0, int(150 + (normalized - 0.2) * 255), 255
        elif normalized < 0.6:  # Mild
            r, g, b = int((normalized - 0.4) * 255), 255, int(255 - (normalized - 0.4) * 255)
        elif normalized < 0.8:  # Warm
            r, g, b = 255, int(255 - (normalized - 0.6) * 255), 0
        else:  # Hot
            r, g, b = 255, int(100 - (normalized - 0.8) * 100), 0
        
        return f'#{r:02x}{g:02x}{b:02x}'
    
    def _adjust_color_alpha(self, color: str, alpha: float) -> str:
        """Simulate alpha transparency by blending with background"""
        # Extract RGB values
        r = int(color[1:3], 16)
        g = int(color[3:5], 16)
        b = int(color[5:7], 16)
        
        # Blend with dark background (40, 50, 60)
        bg_r, bg_g, bg_b = 40, 50, 60
        
        new_r = int(r * alpha + bg_r * (1 - alpha))
        new_g = int(g * alpha + bg_g * (1 - alpha))
        new_b = int(b * alpha + bg_b * (1 - alpha))
        
        return f'#{new_r:02x}{new_g:02x}{new_b:02x}'
    
    def _create_weather_info_overlay(self):
        """Create professional weather information overlay"""
        width = self.canvas.winfo_width()
        height = self.canvas.winfo_height()
        
        if width <= 1 or height <= 1:
            return
        
        # Create semi-transparent info panel
        panel_width = 280
        panel_height = 120
        panel_x = width - panel_width - 20
        panel_y = 20
        
        # Background panel
        self.canvas.create_rectangle(
            panel_x, panel_y, panel_x + panel_width, panel_y + panel_height,
            fill="#2a2a2a", outline="#4a4a4a", width=1,
            tags="info_panel"
        )
        
        # Title
        self.canvas.create_text(
            panel_x + 15, panel_y + 15,
            text="Live Weather Visualization",
            fill="#ffffff", font=("Arial", 12, "bold"),
            anchor="nw", tags="info_panel"
        )
        
        # Weather details
        details = [
            "🌡️ Temperature Grid: Real-time thermal mapping",
            "💨 Wind Flow: Dynamic air current visualization",
            "🌧️ Precipitation: Multi-type particle simulation",
            "🎨 Atmospheric Gradient: Sky condition rendering"
        ]
        
        for i, detail in enumerate(details):
            self.canvas.create_text(
                panel_x + 15, panel_y + 35 + (i * 18),
                text=detail,
                fill="#cccccc", font=("Arial", 9),
                anchor="nw", tags="info_panel"
            )
        
        # Add legend for temperature colors
        legend_x = 20
        legend_y = height - 80
        
        self.canvas.create_text(
            legend_x, legend_y,
            text="Temperature Scale:",
            fill="#ffffff", font=("Arial", 10, "bold"),
            anchor="nw", tags="legend"
        )
        
        # Temperature color scale
        temps = [-10, 0, 10, 20, 30]
        labels = ["Cold", "Cool", "Mild", "Warm", "Hot"]
        
        for i, (temp, label) in enumerate(zip(temps, labels)):
            color = self._temp_to_color(temp)
            x = legend_x + (i * 40)
            y = legend_y + 20
            
            # Color swatch
            self.canvas.create_rectangle(
                x, y, x + 30, y + 15,
                fill=color, outline="#666666",
                tags="legend"
            )
            
            # Label
            self.canvas.create_text(
                x + 15, y + 25,
                text=label,
                fill="#cccccc", font=("Arial", 8),
                anchor="n", tags="legend"
            )
    
    def _create_wind_flow(self):
        """Create animated wind flow lines with smooth appearance"""
        width = self.canvas.winfo_width()
        height = self.canvas.winfo_height()
        
        if width <= 1 or height <= 1:
            return
        
        # Create elegant wind flow lines
        for _ in range(15):  # Fewer lines for cleaner look
            start_x = random.randint(-50, width + 50)
            start_y = random.randint(0, height)
            
            # Create smooth curved wind line
            points = []
            x, y = start_x, start_y
            
            # Generate smoother curves
            for i in range(8):
                x += random.randint(20, 40)
                y += random.randint(-15, 15)
                points.extend([x, y])
            
            if len(points) > 4:
                # Create main wind line with gradient effect
                line = self.canvas.create_line(
                    points,
                    fill="#ffffff",
                    width=3,
                    smooth=True,
                    tags="wind"
                )
                
                # Add subtle glow effect with thinner lines
                glow_line = self.canvas.create_line(
                    points,
                    fill="#cccccc",
                    width=1,
                    smooth=True,
                    tags="wind_glow"
                )
                
                self.wind_lines.extend([line, glow_line])
    
    def _start_animations(self):
        """Start all animations"""
        self._animate_particles()
        self._animate_wind()
        self._animate_temperature()
    
    def _animate_particles(self):
        """Animate smooth precipitation particles"""
        if not self.animation_running or not self._widget_exists():
            return
            
        try:
            width = self.canvas.winfo_width()
            height = self.canvas.winfo_height()
            
            if width <= 1 or height <= 1:
                self.safe_after(100, self._animate_particles)
                return
            
            # Add new particles with variety
            if len(self.particles) < 60:  # Fewer particles for cleaner look
                x = random.randint(-20, width + 20)
                size = random.uniform(1.5, 4.0)  # Variable sizes
                
                # Create different types of particles
                particle_type = random.choice(['rain', 'mist', 'snow'])
                
                if particle_type == 'rain':
                    # Rain drops - elongated ovals
                    particle = self.canvas.create_oval(
                        x, -10, x + size, -10 + size * 2,
                        fill="#66aaff",
                        outline="",
                        tags="particle"
                    )
                elif particle_type == 'mist':
                    # Mist - soft circles
                    particle = self.canvas.create_oval(
                        x, -10, x + size * 1.5, -10 + size * 1.5,
                        fill="#aaccff",
                        outline="",
                        tags="particle"
                    )
                else:  # snow
                    # Snow - white circles
                    particle = self.canvas.create_oval(
                        x, -10, x + size, -10 + size,
                        fill="#ffffff",
                        outline="",
                        tags="particle"
                    )
                
                self.particles.append((particle, particle_type, size))
            
            # Move existing particles with realistic physics
            for particle_data in self.particles[:]:
                try:
                    particle, p_type, size = particle_data
                    coords = self.canvas.coords(particle)
                    
                    if coords and len(coords) >= 4 and coords[1] < height + 20:
                        # Different movement patterns for different particle types
                        if p_type == 'rain':
                            dx = random.uniform(-0.5, 0.5)
                            dy = 4 + size * 0.5
                        elif p_type == 'mist':
                            dx = random.uniform(-2, 2)
                            dy = 1 + size * 0.2
                        else:  # snow
                            dx = random.uniform(-1.5, 1.5)
                            dy = 2 + size * 0.3
                        
                        self.canvas.move(particle, dx, dy)
                    else:
                        self.canvas.delete(particle)
                        self.particles.remove(particle_data)
                except Exception:
                    # Particle might have been deleted
                    if particle_data in self.particles:
                        self.particles.remove(particle_data)
            
            # Schedule next frame
            self.safe_after(60, self._animate_particles)  # Slightly slower for smoother appearance
            
        except Exception as e:
            self.logger.error(f"Particle animation error: {e}")
            self.safe_after(100, self._animate_particles)
    
    def _animate_wind(self):
        """Animate wind flow lines"""
        if not self.animation_running or not self._widget_exists():
            return
            
        try:
            # Move wind lines
            for line in self.wind_lines[:]:
                try:
                    self.canvas.move(line, 1, 0)
                    coords = self.canvas.coords(line)
                    if coords and coords[0] > self.canvas.winfo_width() + 100:
                        self.canvas.delete(line)
                        self.wind_lines.remove(line)
                except Exception:
                    if line in self.wind_lines:
                        self.wind_lines.remove(line)
            
            # Add new wind lines occasionally
            if len(self.wind_lines) < 20 and random.random() < 0.1:
                self._add_wind_line()
            
            # Schedule next frame
            self.safe_after(100, self._animate_wind)
            
        except Exception as e:
            self.logger.error(f"Wind animation error: {e}")
            self.safe_after(200, self._animate_wind)
    
    def _add_wind_line(self):
        """Add a new wind line"""
        try:
            height = self.canvas.winfo_height()
            if height <= 1:
                return
                
            start_y = random.randint(0, height)
            
            # Create curved wind line
            points = []
            x, y = -50, start_y
            for i in range(10):
                x += random.randint(10, 30)
                y += random.randint(-20, 20)
                points.extend([x, y])
            
            if len(points) > 4:
                line = self.canvas.create_line(
                    points,
                    fill="#ffffff",
                    width=2,
                    smooth=True,
                    stipple="gray50",
                    tags="wind"
                )
                self.wind_lines.append(line)
        except Exception as e:
            self.logger.error(f"Failed to add wind line: {e}")
    
    def _animate_temperature(self):
        """Animate temperature grid"""
        if not self.animation_running or not self._widget_exists():
            return
            
        try:
            # Update temperature grid colors
            for i, (rect, temp) in enumerate(self.temp_grid[:]):
                try:
                    # Slightly vary temperature
                    new_temp = temp + random.uniform(-0.5, 0.5)
                    new_color = self._temp_to_color(new_temp)
                    self.canvas.itemconfig(rect, fill=new_color)
                    self.temp_grid[i] = (rect, new_temp)
                except Exception:
                    # Rectangle might have been deleted
                    pass
            
            # Schedule next update
            self.safe_after(2000, self._animate_temperature)
            
        except Exception as e:
            self.logger.error(f"Temperature animation error: {e}")
            self.safe_after(3000, self._animate_temperature)
    
    def _on_canvas_resize(self, event):
        """Handle canvas resize"""
        try:
            # Clear and recreate visualization
            self.canvas.delete("all")
            self.particles.clear()
            self.wind_lines.clear()
            self.temp_grid.clear()
            
            # Recreate after a short delay
            self.safe_after(100, self._initialize_visualization)
        except Exception as e:
            self.logger.error(f"Canvas resize error: {e}")
    
    @ensure_main_thread
    def _start_weather_updates(self):
        """Start periodic weather updates."""
        def update_loop():
             while self._widget_exists() and self.animation_running:
                try:
                    if self.weather_service:
                        weather_data = self.weather_service.get_current_weather("London")
                        if weather_data:
                            self.current_weather = weather_data
                            self.safe_after_idle(lambda: self._update_status("Weather data updated"))
                    time.sleep(30)  # Update every 30 seconds
                except Exception as e:
                    self.logger.error(f"Weather update error: {e}")
                    time.sleep(60)  # Wait longer on error
                    
        thread = threading.Thread(target=update_loop, daemon=True)
        thread.start()
    
    def update_weather_data(self, weather_data: Dict):
        """Update visualization with real weather data"""
        try:
            self.current_weather = weather_data
            
            # Update particle type based on weather condition
            condition = weather_data.get('condition', '').lower()
            
            if 'rain' in condition:
                self._set_particle_type('rain')
            elif 'snow' in condition:
                self._set_particle_type('snow')
            elif 'cloud' in condition:
                self._set_particle_type('cloud')
            else:
                self._set_particle_type('clear')
                
            # Update status
            temp = weather_data.get('temperature', 0)
            desc = weather_data.get('description', 'Unknown')
            self._update_status(f"Current: {temp:.1f}°C, {desc}")
            
        except Exception as e:
            self.logger.error(f"Failed to update weather data: {e}")
    
    def _set_particle_type(self, weather_type: str):
        """Set particle appearance based on weather type"""
        try:
            if weather_type == 'rain':
                # Blue rain drops
                for particle in self.particles:
                    self.canvas.itemconfig(particle, fill="#4499ff")
            elif weather_type == 'snow':
                # White snowflakes
                for particle in self.particles:
                    self.canvas.itemconfig(particle, fill="#ffffff")
            elif weather_type == 'cloud':
                # Gray particles
                for particle in self.particles:
                    self.canvas.itemconfig(particle, fill="#888888")
            else:
                # Clear - golden particles
                for particle in self.particles:
                    self.canvas.itemconfig(particle, fill="#ffdd44")
        except Exception as e:
            self.logger.error(f"Failed to set particle type: {e}")
    
    def _update_status(self, message: str):
        """Update status message."""
        try:
            if hasattr(self, 'status_label') and self.status_label.winfo_exists():
                self.status_label.configure(text=message)
        except Exception:
            pass
    
    def cleanup(self):
        """Clean up resources."""
        self.animation_running = False
        try:
            self.canvas.delete("all")
        except Exception:
            pass
        super().cleanup()
    
    def _widget_exists(self):
        """Check if widget still exists."""
        try:
            return hasattr(self, 'winfo_exists') and self.winfo_exists()
        except Exception:
            return False