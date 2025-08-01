"""Weather Display Component

Handles the display of weather information with proper separation of concerns.
"""

import logging
from typing import Any, Dict, Optional

import customtkinter as ctk

from ...core.event_bus import EventTypes, publish_event
from ...core.interfaces import IWeatherDisplay
from ...models.weather_models import WeatherData
from .base_component import BaseComponent


class WeatherDisplay(BaseComponent, IWeatherDisplay):
    """Weather display component with clean architecture."""

    def __init__(self, parent: Optional[ctk.CTkFrame] = None, **kwargs):
        """Initialize the weather display component.

        Args:
            parent: Parent widget
            **kwargs: Additional arguments
        """
        self.current_weather: Optional[WeatherData] = None
        self.temp_unit = kwargs.get('temp_unit', 'C')
        self.weather_icons = {
            "clear": "☀️",
            "partly cloudy": "⛅",
            "cloudy": "☁️",
            "overcast": "☁️",
            "rain": "🌧️",
            "drizzle": "🌦️",
            "thunderstorm": "⛈️",
            "snow": "❄️",
            "mist": "🌫️",
            "fog": "🌫️",
        }

        super().__init__(parent, **kwargs)

    def _setup_component(self, **kwargs) -> None:
        """Setup component-specific initialization."""
        self.main_frame = None
        self.current_weather_frame = None
        self.forecast_frame = None
        self.metrics_frame = None
        self.loading_label = None
        self.error_label = None

    def _subscribe_to_events(self) -> None:
        """Subscribe to weather-related events."""
        super()._subscribe_to_events()
        self.event_bus.subscribe(EventTypes.WEATHER_UPDATED, self._on_weather_updated)
        self.event_bus.subscribe(EventTypes.WEATHER_ERROR, self._on_weather_error)
        self.event_bus.subscribe(EventTypes.WEATHER_LOADING, self._on_weather_loading)

    def _create_widget(self) -> ctk.CTkFrame:
        """Create the main weather display widget.

        Returns:
            The main frame containing weather display
        """
        self.main_frame = ctk.CTkFrame(self.parent)

        # Create sub-frames
        self._create_current_weather_section()
        self._create_forecast_section()
        self._create_metrics_section()

        return self.main_frame

    def _create_current_weather_section(self) -> None:
        """Create the current weather display section."""
        self.current_weather_frame = ctk.CTkFrame(self.main_frame)
        self.current_weather_frame.pack(fill="x", padx=10, pady=5)

        # Title
        title_label = ctk.CTkLabel(
            self.current_weather_frame,
            text="Current Weather",
            font=("Arial", 16, "bold")
        )
        title_label.pack(pady=5)

        # Weather info container
        self.weather_info_frame = ctk.CTkFrame(self.current_weather_frame)
        self.weather_info_frame.pack(fill="x", padx=10, pady=5)

        # Loading and error labels
        self.loading_label = ctk.CTkLabel(
            self.weather_info_frame,
            text="Loading weather data...",
            font=("Arial", 12)
        )

        self.error_label = ctk.CTkLabel(
            self.weather_info_frame,
            text="",
            font=("Arial", 12),
            text_color="red"
        )

    def _create_forecast_section(self) -> None:
        """Create the forecast display section."""
        self.forecast_frame = ctk.CTkFrame(self.main_frame)
        self.forecast_frame.pack(fill="x", padx=10, pady=5)

        # Title
        forecast_title = ctk.CTkLabel(
            self.forecast_frame,
            text="5-Day Forecast",
            font=("Arial", 16, "bold")
        )
        forecast_title.pack(pady=5)

        # Forecast container
        self.forecast_container = ctk.CTkFrame(self.forecast_frame)
        self.forecast_container.pack(fill="x", padx=10, pady=5)

    def _create_metrics_section(self) -> None:
        """Create the weather metrics section."""
        self.metrics_frame = ctk.CTkFrame(self.main_frame)
        self.metrics_frame.pack(fill="x", padx=10, pady=5)

        # Title
        metrics_title = ctk.CTkLabel(
            self.metrics_frame,
            text="Weather Metrics",
            font=("Arial", 16, "bold")
        )
        metrics_title.pack(pady=5)

        # Metrics container
        self.metrics_container = ctk.CTkFrame(self.metrics_frame)
        self.metrics_container.pack(fill="x", padx=10, pady=5)

    def _update_widget(self, data: WeatherData) -> None:
        """Update the widget with new weather data.

        Args:
            data: New weather data
        """
        self.current_weather = data
        self._update_current_weather_display()
        self._update_forecast_display()
        self._update_metrics_display()

    def _update_current_weather_display(self) -> None:
        """Update the current weather display."""
        if not self.current_weather or not self.weather_info_frame:
            return

        # Clear existing widgets
        for widget in self.weather_info_frame.winfo_children():
            widget.destroy()

        # Create new weather display
        location_label = ctk.CTkLabel(
            self.weather_info_frame,
            text=f"📍 {self.current_weather.location.name}, {self.current_weather.location.country}",
            font=("Arial", 14, "bold")
        )
        location_label.pack(pady=5)

        # Temperature and condition
        temp_condition_frame = ctk.CTkFrame(self.weather_info_frame)
        temp_condition_frame.pack(fill="x", pady=5)

        temp_text = f"{self.current_weather.temperature}°{self.temp_unit}"
        temp_label = ctk.CTkLabel(
            temp_condition_frame,
            text=temp_text,
            font=("Arial", 24, "bold")
        )
        temp_label.pack(side="left", padx=10)

        condition_icon = self._get_weather_icon(self.current_weather.condition.description)
        condition_label = ctk.CTkLabel(
            temp_condition_frame,
            text=f"{condition_icon} {self.current_weather.condition.description.title()}",
            font=("Arial", 16)
        )
        condition_label.pack(side="right", padx=10)

        # Additional details
        details_frame = ctk.CTkFrame(self.weather_info_frame)
        details_frame.pack(fill="x", pady=5)

        # Feels like
        feels_like_text = f"Feels like: {self.current_weather.feels_like}°{self.temp_unit}"
        feels_like_label = ctk.CTkLabel(
            details_frame,
            text=feels_like_text,
            font=("Arial", 12)
        )
        feels_like_label.pack(side="left", padx=10)

        # Humidity
        humidity_text = f"Humidity: {self.current_weather.humidity}%"
        humidity_label = ctk.CTkLabel(
            details_frame,
            text=humidity_text,
            font=("Arial", 12)
        )
        humidity_label.pack(side="right", padx=10)

    def _update_forecast_display(self) -> None:
        """Update the forecast display."""
        if not self.current_weather or not self.forecast_container:
            return

        # Clear existing widgets
        for widget in self.forecast_container.winfo_children():
            widget.destroy()

        # Create forecast cards
        if hasattr(self.current_weather, 'forecast') and self.current_weather.forecast:
            for i, day_forecast in enumerate(self.current_weather.forecast[:5]):
                self._create_forecast_card(day_forecast, i)

    def _create_forecast_card(self, forecast: Any, index: int) -> None:
        """Create a forecast card.

        Args:
            forecast: Forecast data
            index: Card index
        """
        card_frame = ctk.CTkFrame(self.forecast_container)
        card_frame.pack(side="left", padx=5, pady=5, fill="both", expand=True)

        # Day
        day_label = ctk.CTkLabel(
            card_frame,
            text=forecast.date.strftime("%a"),
            font=("Arial", 12, "bold")
        )
        day_label.pack(pady=2)

        # Icon
        icon_label = ctk.CTkLabel(
            card_frame,
            text=self._get_weather_icon(forecast.condition.description),
            font=("Arial", 20)
        )
        icon_label.pack(pady=2)

        # Temperature
        temp_text = f"{forecast.temperature}°{self.temp_unit}"
        temp_label = ctk.CTkLabel(
            card_frame,
            text=temp_text,
            font=("Arial", 14)
        )
        temp_label.pack(pady=2)

    def _update_metrics_display(self) -> None:
        """Update the metrics display."""
        if not self.current_weather or not self.metrics_container:
            return

        # Clear existing widgets
        for widget in self.metrics_container.winfo_children():
            widget.destroy()

        # Create metrics grid
        metrics_grid = ctk.CTkFrame(self.metrics_container)
        metrics_grid.pack(fill="x", pady=5)

        # Wind
        if hasattr(self.current_weather, 'wind'):
            wind_text = f"Wind: {self.current_weather.wind.speed} km/h"
            wind_label = ctk.CTkLabel(
                metrics_grid,
                text=wind_text,
                font=("Arial", 12)
            )
            wind_label.pack(side="left", padx=10)

        # Pressure
        if hasattr(self.current_weather, 'pressure'):
            pressure_text = f"Pressure: {self.current_weather.pressure} hPa"
            pressure_label = ctk.CTkLabel(
                metrics_grid,
                text=pressure_text,
                font=("Arial", 12)
            )
            pressure_label.pack(side="left", padx=10)

        # Visibility
        if hasattr(self.current_weather, 'visibility'):
            visibility_text = f"Visibility: {self.current_weather.visibility} km"
            visibility_label = ctk.CTkLabel(
                metrics_grid,
                text=visibility_text,
                font=("Arial", 12)
            )
            visibility_label.pack(side="left", padx=10)

    def _get_weather_icon(self, condition: str) -> str:
        """Get weather icon for condition.

        Args:
            condition: Weather condition

        Returns:
            Weather icon emoji
        """
        condition_lower = condition.lower()
        for key, icon in self.weather_icons.items():
            if key in condition_lower:
                return icon
        return "🌤️"  # Default icon

    def show_loading(self) -> None:
        """Show loading state."""
        if self.weather_info_frame:
            # Clear existing widgets
            for widget in self.weather_info_frame.winfo_children():
                widget.destroy()

            # Show loading label
            self.loading_label = ctk.CTkLabel(
                self.weather_info_frame,
                text="Loading weather data...",
                font=("Arial", 12)
            )
            self.loading_label.pack(pady=20)

    def show_error(self, error: str) -> None:
        """Show error state.

        Args:
            error: Error message
        """
        if self.weather_info_frame:
            # Clear existing widgets
            for widget in self.weather_info_frame.winfo_children():
                widget.destroy()

            # Show error label
            self.error_label = ctk.CTkLabel(
                self.weather_info_frame,
                text=f"Error: {error}",
                font=("Arial", 12),
                text_color="red"
            )
            self.error_label.pack(pady=20)

    def show_weather(self, weather_data: WeatherData) -> None:
        """Show weather data.

        Args:
            weather_data: Weather data to display
        """
        self.update(weather_data)

    def _get_main_widget(self) -> Optional[ctk.CTkFrame]:
        """Get the main widget.

        Returns:
            The main frame
        """
        return self.main_frame

    def _on_weather_updated(self, data: WeatherData) -> None:
        """Handle weather updated event.

        Args:
            data: Updated weather data
        """
        self.update(data)

    def _on_weather_error(self, data: Dict[str, Any]) -> None:
        """Handle weather error event.

        Args:
            data: Error data
        """
        error_message = data.get('error', 'Unknown error occurred')
        self.show_error(error_message)

    def _on_weather_loading(self, data: Any) -> None:
        """Handle weather loading event.

        Args:
            data: Loading data
        """
        self.show_loading()

    def toggle_temperature_unit(self) -> None:
        """Toggle between Celsius and Fahrenheit."""
        self.temp_unit = "F" if self.temp_unit == "C" else "C"
        if self.current_weather:
            self._update_current_weather_display()
            self._update_forecast_display()

    def get_current_weather(self) -> Optional[WeatherData]:
        """Get current weather data.

        Returns:
            Current weather data or None
        """
        return self.current_weather
