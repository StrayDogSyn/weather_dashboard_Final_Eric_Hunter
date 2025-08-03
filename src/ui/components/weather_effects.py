"""Weather-Based Visual Effects

Provides dynamic visual effects based on weather conditions, temperature, and time of day.
Includes particle effects, dynamic gradients, and atmospheric enhancements.
"""

import random
import threading
import time
import tkinter as tk
from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple

import customtkinter as ctk


@dataclass
class WeatherCondition:
    """Weather condition data for visual effects."""

    condition: str
    temperature: float
    humidity: float
    wind_speed: float
    time_of_day: str  # 'day', 'night', 'dawn', 'dusk'
    precipitation: float = 0.0


class TemperatureGradient:
    """Creates dynamic gradients based on temperature."""

    def __init__(self):
        # Temperature color mappings (in Celsius)
        self.temp_colors = {
            -30: (0x1E, 0x3A, 0x8A),  # Deep blue (very cold)
            -10: (0x2E, 0x5A, 0xAA),  # Blue (cold)
            0: (0x4E, 0x7A, 0xCA),  # Light blue (freezing)
            10: (0x6E, 0x9A, 0xEA),  # Sky blue (cool)
            20: (0x8E, 0xBA, 0x8A),  # Green (mild)
            25: (0xAE, 0xDA, 0x6A),  # Light green (warm)
            30: (0xEE, 0xEA, 0x4A),  # Yellow (hot)
            35: (0xEE, 0xCA, 0x2A),  # Orange (very hot)
            40: (0xEE, 0x8A, 0x1A),  # Red-orange (extreme)
            50: (0xEE, 0x4A, 0x0A),  # Red (scorching)
        }

    def get_temperature_color(self, temperature: float) -> str:
        """Get color based on temperature."""
        # Find the two closest temperature points
        temps = sorted(self.temp_colors.keys())

        if temperature <= temps[0]:
            r, g, b = self.temp_colors[temps[0]]
        elif temperature >= temps[-1]:
            r, g, b = self.temp_colors[temps[-1]]
        else:
            # Interpolate between two closest temperatures
            lower_temp = max(t for t in temps if t <= temperature)
            upper_temp = min(t for t in temps if t >= temperature)

            if lower_temp == upper_temp:
                r, g, b = self.temp_colors[lower_temp]
            else:
                # Linear interpolation
                factor = (temperature - lower_temp) / (upper_temp - lower_temp)

                r1, g1, b1 = self.temp_colors[lower_temp]
                r2, g2, b2 = self.temp_colors[upper_temp]

                r = int(r1 + (r2 - r1) * factor)
                g = int(g1 + (g2 - g1) * factor)
                b = int(b1 + (b2 - b1) * factor)

        return f"#{r:02x}{g:02x}{b:02x}"

    def get_gradient_colors(
        self, temperature: float, time_of_day: str
    ) -> Tuple[str, str]:
        """Get gradient colors for background based on temperature and time."""
        base_color = self.get_temperature_color(temperature)

        # Adjust for time of day
        r = int(base_color[1:3], 16)
        g = int(base_color[3:5], 16)
        b = int(base_color[5:7], 16)

        if time_of_day == "night":
            # Darker, more blue
            r = max(0, r - 60)
            g = max(0, g - 40)
            b = min(255, b + 20)
        elif time_of_day == "dawn":
            # Warmer, more orange
            r = min(255, r + 30)
            g = min(255, g + 20)
            b = max(0, b - 20)
        elif time_of_day == "dusk":
            # Purple-orange tint
            r = min(255, r + 40)
            g = max(0, g - 10)
            b = min(255, b + 30)

        primary = f"#{r:02x}{g:02x}{b:02x}"

        # Create secondary color (lighter/darker variant)
        r2 = min(255, max(0, r + 40))
        g2 = min(255, max(0, g + 40))
        b2 = min(255, max(0, b + 40))
        secondary = f"#{r2:02x}{g2:02x}{b2:02x}"

        return primary, secondary


class ParticleSystem:
    """Creates particle effects for weather conditions."""

    def __init__(self, canvas: tk.Canvas, width: int, height: int):
        self.canvas = canvas
        self.width = width
        self.height = height
        self.particles = []
        self.is_running = False
        self.animation_thread = None

    def start_rain_effect(self, intensity: float = 0.5):
        """Start rain particle effect."""
        self.stop_effects()
        self.is_running = True

        # Create rain particles
        particle_count = int(50 * intensity)
        for _ in range(particle_count):
            particle = {
                "x": random.randint(0, self.width),
                "y": random.randint(-100, 0),
                "speed": random.uniform(5, 15),
                "length": random.randint(10, 25),
                "opacity": random.uniform(0.3, 0.8),
            }
            self.particles.append(particle)

        self.animation_thread = threading.Thread(target=self._animate_rain, daemon=True)
        self.animation_thread.start()

    def start_snow_effect(self, intensity: float = 0.5):
        """Start snow particle effect."""
        self.stop_effects()
        self.is_running = True

        # Create snow particles
        particle_count = int(30 * intensity)
        for _ in range(particle_count):
            particle = {
                "x": random.randint(0, self.width),
                "y": random.randint(-50, 0),
                "speed": random.uniform(1, 4),
                "size": random.randint(2, 6),
                "drift": random.uniform(-1, 1),
                "opacity": random.uniform(0.5, 1.0),
            }
            self.particles.append(particle)

        self.animation_thread = threading.Thread(target=self._animate_snow, daemon=True)
        self.animation_thread.start()

    def start_fog_effect(self, intensity: float = 0.5):
        """Start fog/mist effect."""
        self.stop_effects()
        self.is_running = True

        # Create fog particles (larger, slower moving)
        particle_count = int(10 * intensity)
        for _ in range(particle_count):
            particle = {
                "x": random.randint(-50, self.width + 50),
                "y": random.randint(0, self.height),
                "speed": random.uniform(0.5, 2),
                "size": random.randint(30, 80),
                "drift": random.uniform(-0.5, 0.5),
                "opacity": random.uniform(0.1, 0.3),
            }
            self.particles.append(particle)

        self.animation_thread = threading.Thread(target=self._animate_fog, daemon=True)
        self.animation_thread.start()

    def stop_effects(self):
        """Stop all particle effects."""
        self.is_running = False
        self.particles.clear()

        # Clear canvas
        try:
            self.canvas.delete("particle")
        except tk.TclError:
            pass

    def _animate_rain(self):
        """Animate rain particles."""
        while self.is_running:
            try:
                # Clear previous particles
                self.canvas.delete("rain_particle")

                # Update and draw particles
                for particle in self.particles[:]:
                    particle["y"] += particle["speed"]

                    # Reset particle if it goes off screen
                    if particle["y"] > self.height:
                        particle["y"] = random.randint(-100, -10)
                        particle["x"] = random.randint(0, self.width)

                    # Draw rain drop
                    x1, y1 = particle["x"], particle["y"]
                    x2, y2 = x1 + 2, y1 + particle["length"]

                    # Calculate color with opacity
                    opacity = int(255 * particle["opacity"])
                    color = f"#{opacity//4:02x}{opacity//4:02x}{opacity:02x}"

                    self.canvas.create_line(
                        x1, y1, x2, y2, fill=color, width=1, tags="rain_particle"
                    )

                time.sleep(0.05)  # 20 FPS

            except tk.TclError:
                break

    def _animate_snow(self):
        """Animate snow particles."""
        while self.is_running:
            try:
                # Clear previous particles
                self.canvas.delete("snow_particle")

                # Update and draw particles
                for particle in self.particles[:]:
                    particle["y"] += particle["speed"]
                    particle["x"] += particle["drift"]

                    # Reset particle if it goes off screen
                    if particle["y"] > self.height:
                        particle["y"] = random.randint(-50, -10)
                        particle["x"] = random.randint(0, self.width)

                    if particle["x"] < 0 or particle["x"] > self.width:
                        particle["x"] = random.randint(0, self.width)

                    # Draw snowflake
                    x, y = particle["x"], particle["y"]
                    size = particle["size"]

                    # Calculate color with opacity
                    opacity = int(255 * particle["opacity"])
                    color = f"#{opacity:02x}{opacity:02x}{opacity:02x}"

                    self.canvas.create_oval(
                        x - size // 2,
                        y - size // 2,
                        x + size // 2,
                        y + size // 2,
                        fill=color,
                        outline="",
                        tags="snow_particle",
                    )

                time.sleep(0.05)  # 20 FPS

            except tk.TclError:
                break

    def _animate_fog(self):
        """Animate fog particles."""
        while self.is_running:
            try:
                # Clear previous particles
                self.canvas.delete("fog_particle")

                # Update and draw particles
                for particle in self.particles[:]:
                    particle["x"] += particle["speed"]
                    particle["y"] += particle["drift"]

                    # Reset particle if it goes off screen
                    if particle["x"] > self.width + 50:
                        particle["x"] = -50
                        particle["y"] = random.randint(0, self.height)

                    # Draw fog cloud
                    x, y = particle["x"], particle["y"]
                    size = particle["size"]

                    # Calculate color with opacity
                    opacity = int(255 * particle["opacity"])
                    color = f"#{opacity:02x}{opacity:02x}{opacity:02x}"

                    self.canvas.create_oval(
                        x - size // 2,
                        y - size // 2,
                        x + size // 2,
                        y + size // 2,
                        fill=color,
                        outline="",
                        tags="fog_particle",
                    )

                time.sleep(0.1)  # 10 FPS for fog

            except tk.TclError:
                break


class WeatherBackgroundManager:
    """Manages dynamic weather-based backgrounds."""

    def __init__(
        self, parent: ctk.CTkBaseClass, theme_colors: Optional[Dict[str, str]] = None
    ):
        self.parent = parent
        self.theme_colors = theme_colors or {}
        self.gradient_generator = TemperatureGradient()
        self.current_weather = None
        self.background_frame = None
        self.particle_canvas = None
        self.particle_system = None

    def setup_background(self, width: int, height: int):
        """Setup background canvas and frame."""
        # Create background frame
        self.background_frame = ctk.CTkFrame(
            self.parent, width=width, height=height, fg_color="transparent"
        )
        self.background_frame.place(x=0, y=0)

        # Create particle canvas
        self.particle_canvas = tk.Canvas(
            self.background_frame,
            width=width,
            height=height,
            highlightthickness=0,
            bg="#1a1a1a"
        )
        self.particle_canvas.place(x=0, y=0)

        # Initialize particle system
        self.particle_system = ParticleSystem(self.particle_canvas, width, height)

    def update_weather_background(self, weather_condition: WeatherCondition):
        """Update background based on weather condition."""
        if not self.background_frame or not self.particle_canvas:
            return

        self.current_weather = weather_condition

        # Update background gradient
        primary, secondary = self.gradient_generator.get_gradient_colors(
            weather_condition.temperature, weather_condition.time_of_day
        )

        # Apply gradient background (simplified for tkinter)
        self._apply_gradient_background(primary, secondary)

        # Update particle effects based on weather
        self._update_particle_effects(weather_condition)

    def _apply_gradient_background(self, primary: str, secondary: str):
        """Apply gradient background to canvas."""
        if not self.particle_canvas:
            return

        try:
            # Clear existing background
            self.particle_canvas.delete("background")

            # Create gradient effect using rectangles
            height = self.particle_canvas.winfo_height()
            width = self.particle_canvas.winfo_width()

            if height <= 1 or width <= 1:
                return

            # Parse colors
            r1 = int(primary[1:3], 16)
            g1 = int(primary[3:5], 16)
            b1 = int(primary[5:7], 16)

            r2 = int(secondary[1:3], 16)
            g2 = int(secondary[3:5], 16)
            b2 = int(secondary[5:7], 16)

            # Create gradient strips
            strips = 50
            for i in range(strips):
                ratio = i / (strips - 1)

                r = int(r1 + (r2 - r1) * ratio)
                g = int(g1 + (g2 - g1) * ratio)
                b = int(b1 + (b2 - b1) * ratio)

                color = f"#{r:02x}{g:02x}{b:02x}"

                y1 = int(height * i / strips)
                y2 = int(height * (i + 1) / strips)

                self.particle_canvas.create_rectangle(
                    0, y1, width, y2, fill=color, outline="", tags="background"
                )

        except (tk.TclError, ValueError):
            pass

    def _update_particle_effects(self, weather_condition: WeatherCondition):
        """Update particle effects based on weather condition."""
        if not self.particle_system:
            return

        condition = weather_condition.condition.lower()

        # Stop existing effects
        self.particle_system.stop_effects()

        # Start appropriate effect
        if "rain" in condition or "drizzle" in condition:
            intensity = min(1.0, weather_condition.precipitation / 10.0)
            self.particle_system.start_rain_effect(intensity)
        elif "snow" in condition:
            intensity = min(1.0, weather_condition.precipitation / 5.0)
            self.particle_system.start_snow_effect(intensity)
        elif "fog" in condition or "mist" in condition:
            intensity = weather_condition.humidity / 100.0
            self.particle_system.start_fog_effect(intensity)

    def update_theme(self, theme_data: Dict[str, Any] = None):
        """Update theme colors for weather background."""
        if theme_data:
            self.theme_colors = theme_data

        # Refresh background if weather condition exists
        if self.current_weather:
            self.update_weather_background(self.current_weather)

    def cleanup(self):
        """Clean up background resources."""
        if self.particle_system:
            self.particle_system.stop_effects()

        if self.background_frame:
            try:
                self.background_frame.destroy()
            except tk.TclError:
                pass
            self.background_frame = None
            self.particle_canvas = None
            self.particle_system = None


# StatusMessageManager has been moved to status_manager.py to avoid conflicts
