"""Weather Models Package

This package contains weather-related data models:
- current_weather: Current weather data models
- forecast_models: Weather forecast data structures
- alert_models: Weather alert models
"""

from .current_weather import (
    safe_divide,
    WeatherCondition,
    WeatherData
)

from .forecast_models import (
    ForecastEntry,
    DailyForecast,
    ForecastData
)

from .alert_models import (
    AlertSeverity,
    AlertType,
    WeatherAlert
)

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
    "WeatherAlert"
]