"""Weather Models Package

This package contains weather-related data models:
- current_weather: Current weather data models
- forecast_models: Weather forecast data structures
- alert_models: Weather alert models
"""

from .alert_models import AlertSeverity, AlertType, WeatherAlert
from .current_weather import WeatherCondition, WeatherData, safe_divide
from .forecast_models import DailyForecast, ForecastData, ForecastEntry

__all__ = [
    # Utilities
    "safe_divide",
    # Current Weather
    "WeatherCondition",
    "WeatherData",
    # Forecast
    "ForecastEntry",
    "DailyForecast",
    "ForecastData",
    # Alerts
    "AlertSeverity",
    "AlertType",
    "WeatherAlert",
]
