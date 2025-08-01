"""Weather Display Enhancer Module

Contains the WeatherDisplayEnhancer class for enhancing weather display formatting.
"""

import logging


class WeatherDisplayEnhancer:
    """Enhances existing weather display with better formatting and icons."""

    def __init__(self, weather_dashboard):
        self.dashboard = weather_dashboard
        self.weather_icons = {
            "clear": "☀️",
            "sunny": "☀️",
            "partly cloudy": "⛅",
            "cloudy": "☁️",
            "overcast": "☁️",
            "rain": "🌧️",
            "drizzle": "🌦️",
            "snow": "❄️",
            "thunderstorm": "⛈️",
            "fog": "🌫️",
            "mist": "🌫️",
            "default": "🌤️",
        }

    def enhance_display(self):
        """Enhance existing weather display with better formatting - NO DUPLICATION."""
        try:
            # Check if dashboard and widgets still exist before enhancing
            if not hasattr(self, "dashboard") or not self.dashboard.winfo_exists():
                return

            self.add_weather_icons()
            self.improve_temperature_display()
            self.update_existing_weather_details()

        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.warning(f"Enhancement error (non-critical): {e}")

    def enhance_weather_display(self, condition):
        """Enhance weather condition display with icons."""
        try:
            # Find matching icon
            icon = self.weather_icons.get("default", "🌤️")
            condition_lower = condition.lower()

            for weather_type, emoji in self.weather_icons.items():
                if weather_type in condition_lower:
                    icon = emoji
                    break

            return f"{icon} {condition}"
        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.warning(f"Weather display enhancement error: {e}")
            return condition

    def add_weather_icons(self):
        """Add weather icons to existing display."""
        try:
            # Check if condition label exists and is valid
            if (
                not hasattr(self.dashboard, "condition_label")
                or not self.dashboard.condition_label.winfo_exists()
            ):
                return

            # Get current condition text
            current_condition = self.dashboard.condition_label.cget("text").lower()

            # Find matching icon
            icon = self.weather_icons.get("default")
            for condition, emoji in self.weather_icons.items():
                if condition in current_condition:
                    icon = emoji
                    break

            # Update condition label with icon ONLY if not already present
            current_text = self.dashboard.condition_label.cget("text")
            if not any(emoji in current_text for emoji in self.weather_icons.values()):
                enhanced_text = f"{icon} {current_text}"
                self.dashboard.condition_label.configure(text=enhanced_text)

        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.warning(f"Icon enhancement error: {e}")

    def improve_temperature_display(self):
        """Improve temperature display formatting."""
        try:
            # Check if temp label exists and is valid
            if (
                not hasattr(self.dashboard, "temp_label")
                or not self.dashboard.temp_label.winfo_exists()
            ):
                return

            # Add degree symbol styling if not present
            temp_text = self.dashboard.temp_label.cget("text")
            if "°" not in temp_text and any(char.isdigit() for char in temp_text):
                # Extract number and add proper formatting
                import re

                numbers = re.findall(r"-?\d+", temp_text)
                if numbers:
                    enhanced_temp = f"{numbers[0]}°C"
                    self.dashboard.temp_label.configure(text=enhanced_temp)

        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.warning(f"Temperature enhancement error: {e}")

    def update_existing_weather_details(self):
        """Update existing weather detail labels - NO NEW WIDGETS CREATED."""
        try:
            # Only update existing labels, never create new ones
            if (
                hasattr(self.dashboard, "feels_like_label")
                and self.dashboard.feels_like_label.winfo_exists()
            ):
                current_text = self.dashboard.feels_like_label.cget("text")
                if "🌡️" not in current_text:
                    self.dashboard.feels_like_label.configure(text=f"🌡️ {current_text}")

            if (
                hasattr(self.dashboard, "humidity_label")
                and self.dashboard.humidity_label.winfo_exists()
            ):
                current_text = self.dashboard.humidity_label.cget("text")
                if "💧" not in current_text:
                    self.dashboard.humidity_label.configure(text=f"💧 {current_text}")

        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.warning(f"Details update error: {e}")
