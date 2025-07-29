"""Weather Display Component

Displays current weather data with professional metrics grid.
"""

import customtkinter as ctk
from typing import Optional, Callable
from datetime import datetime

from ui.theme import DataTerminalTheme
from models.weather_models import WeatherData


class WeatherMetricCard(ctk.CTkFrame):
    """Individual weather metric display card."""
    
    def __init__(self, parent, title: str, value: str = "--", unit: str = "", **kwargs):
        """Initialize metric card."""
        super().__init__(parent, **DataTerminalTheme.get_frame_style("default"), **kwargs)
        
        self.title = title
        self.unit = unit
        
        # Configure grid
        self.grid_columnconfigure(0, weight=1)
        
        # Title label
        self.title_label = ctk.CTkLabel(
            self,
            text=title,
            **DataTerminalTheme.get_label_style("caption")
        )
        self.title_label.grid(row=0, column=0, pady=(10, 2), sticky="ew")
        
        # Value label
        self.value_label = ctk.CTkLabel(
            self,
            text=value,
            **DataTerminalTheme.get_label_style("value")
        )
        self.value_label.grid(row=1, column=0, pady=(0, 5), sticky="ew")
        
        # Unit label (if provided)
        if unit:
            self.unit_label = ctk.CTkLabel(
                self,
                text=unit,
                **DataTerminalTheme.get_label_style("caption")
            )
            self.unit_label.grid(row=2, column=0, pady=(0, 10), sticky="ew")
    
    def update_value(self, value: str, unit: str = None) -> None:
        """Update the metric value."""
        self.value_label.configure(text=value)
        if unit and hasattr(self, 'unit_label'):
            self.unit_label.configure(text=unit)


class WeatherDisplayFrame(ctk.CTkFrame):
    """Main weather display component."""
    
    def __init__(self, parent, on_refresh: Optional[Callable] = None, **kwargs):
        """Initialize weather display."""
        super().__init__(parent, **DataTerminalTheme.get_frame_style("default"), **kwargs)
        
        self.on_refresh = on_refresh
        self.current_weather: Optional[WeatherData] = None
        
        # Configure grid
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)
        
        self._create_widgets()
        self._setup_layout()
    
    def _create_widgets(self) -> None:
        """Create all widgets."""
        # Header
        self.header_frame = ctk.CTkFrame(
            self,
            **DataTerminalTheme.get_frame_style("main")
        )
        
        self.title_label = ctk.CTkLabel(
            self.header_frame,
            text="📍 CURRENT WEATHER",
            **DataTerminalTheme.get_label_style("subtitle")
        )
        
        self.refresh_button = ctk.CTkButton(
            self.header_frame,
            text="🔄",
            width=40,
            command=self._on_refresh_click,
            **DataTerminalTheme.get_button_style("secondary")
        )
        
        # Location and main info
        self.location_frame = ctk.CTkFrame(
            self,
            **DataTerminalTheme.get_frame_style("highlight")
        )
        
        self.location_label = ctk.CTkLabel(
            self.location_frame,
            text="Select a city",
            **DataTerminalTheme.get_label_style("title")
        )
        
        self.temperature_label = ctk.CTkLabel(
            self.location_frame,
            text="--°",
            font=DataTerminalTheme.get_font(48, "bold"),
            text_color=DataTerminalTheme.PRIMARY
        )
        
        self.description_label = ctk.CTkLabel(
            self.location_frame,
            text="",
            **DataTerminalTheme.get_label_style("default")
        )
        
        self.feels_like_label = ctk.CTkLabel(
            self.location_frame,
            text="",
            **DataTerminalTheme.get_label_style("caption")
        )
        
        # Metrics grid
        self.metrics_frame = ctk.CTkFrame(
            self,
            **DataTerminalTheme.get_frame_style("main")
        )
        
        # Configure metrics grid
        for i in range(3):
            self.metrics_frame.grid_columnconfigure(i, weight=1)
        for i in range(3):
            self.metrics_frame.grid_rowconfigure(i, weight=1)
        
        # Create metric cards
        self.metrics = {
            'humidity': WeatherMetricCard(
                self.metrics_frame,
                "HUMIDITY",
                "--",
                "%"
            ),
            'pressure': WeatherMetricCard(
                self.metrics_frame,
                "PRESSURE",
                "--",
                "hPa"
            ),
            'visibility': WeatherMetricCard(
                self.metrics_frame,
                "VISIBILITY",
                "--",
                "km"
            ),
            'wind_speed': WeatherMetricCard(
                self.metrics_frame,
                "WIND SPEED",
                "--",
                "m/s"
            ),
            'wind_direction': WeatherMetricCard(
                self.metrics_frame,
                "WIND DIR",
                "--",
                "°"
            ),
            'clouds': WeatherMetricCard(
                self.metrics_frame,
                "CLOUDINESS",
                "--",
                "%"
            ),
            'temp_min': WeatherMetricCard(
                self.metrics_frame,
                "MIN TEMP",
                "--",
                "°C"
            ),
            'temp_max': WeatherMetricCard(
                self.metrics_frame,
                "MAX TEMP",
                "--",
                "°C"
            ),
            'uv_index': WeatherMetricCard(
                self.metrics_frame,
                "UV INDEX",
                "--",
                ""
            )
        }
    
    def _setup_layout(self) -> None:
        """Arrange widgets."""
        # Header
        self.header_frame.grid(row=0, column=0, sticky="ew", padx=15, pady=(15, 10))
        self.header_frame.grid_columnconfigure(0, weight=1)
        
        self.title_label.grid(row=0, column=0, sticky="w")
        self.refresh_button.grid(row=0, column=1, sticky="e")
        
        # Location and main info
        self.location_frame.grid(row=1, column=0, sticky="ew", padx=15, pady=(0, 15))
        self.location_frame.grid_columnconfigure(0, weight=1)
        
        self.location_label.grid(row=0, column=0, pady=(15, 5), sticky="ew")
        self.temperature_label.grid(row=1, column=0, pady=5, sticky="ew")
        self.description_label.grid(row=2, column=0, pady=5, sticky="ew")
        self.feels_like_label.grid(row=3, column=0, pady=(5, 15), sticky="ew")
        
        # Metrics grid
        self.metrics_frame.grid(row=2, column=0, sticky="nsew", padx=15, pady=(0, 15))
        
        # Position metric cards in grid
        positions = [
            ('humidity', 0, 0), ('pressure', 0, 1), ('visibility', 0, 2),
            ('wind_speed', 1, 0), ('wind_direction', 1, 1), ('clouds', 1, 2),
            ('temp_min', 2, 0), ('temp_max', 2, 1), ('uv_index', 2, 2)
        ]
        
        for metric_name, row, col in positions:
            self.metrics[metric_name].grid(
                row=row, column=col,
                padx=5, pady=5,
                sticky="nsew"
            )
    
    def _on_refresh_click(self) -> None:
        """Handle refresh button click."""
        if self.on_refresh:
            self.on_refresh()
    
    def update_weather(self, weather_data: WeatherData) -> None:
        """Update display with new weather data."""
        self.current_weather = weather_data
        
        # Update location and main info
        self.location_label.configure(
            text=f"{weather_data.city}, {weather_data.country}"
        )
        
        self.temperature_label.configure(
            text=f"{weather_data.temperature}°"
        )
        
        self.description_label.configure(
            text=weather_data.description
        )
        
        self.feels_like_label.configure(
            text=f"Feels like {weather_data.feels_like}°C"
        )
        
        # Update metrics
        self.metrics['humidity'].update_value(str(weather_data.humidity))
        self.metrics['pressure'].update_value(str(weather_data.pressure))
        self.metrics['visibility'].update_value(str(weather_data.visibility))
        self.metrics['wind_speed'].update_value(str(weather_data.wind_speed))
        self.metrics['wind_direction'].update_value(str(weather_data.wind_direction))
        self.metrics['clouds'].update_value(str(weather_data.clouds))
        self.metrics['temp_min'].update_value(str(weather_data.temp_min))
        self.metrics['temp_max'].update_value(str(weather_data.temp_max))
        
        # UV Index (if available)
        if weather_data.uv_index is not None:
            self.metrics['uv_index'].update_value(str(weather_data.uv_index))
        else:
            self.metrics['uv_index'].update_value("N/A")
    
    def clear_display(self) -> None:
        """Clear the weather display."""
        self.current_weather = None
        
        # Reset location and main info
        self.location_label.configure(text="Select a city")
        self.temperature_label.configure(text="--°")
        self.description_label.configure(text="")
        self.feels_like_label.configure(text="")
        
        # Reset all metrics
        for metric in self.metrics.values():
            metric.update_value("--")