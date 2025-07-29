"""Data Models Package

Defines structured data classes for weather information and application state.
"""

from models.weather_models import (
    WeatherData,
    ForecastData,
    WeatherCondition,
    Location,
    WeatherAlert
)

from models.app_models import (
    AppState,
    UserPreferences,
    CacheEntry,
    APIResponse
)

__version__ = "1.0.0"
__author__ = "Weather Dashboard Team"

__all__ = [
    "WeatherData",
    "ForecastData", 
    "WeatherCondition",
    "Location",
    "WeatherAlert",
    "AppState",
    "UserPreferences",
    "CacheEntry",
    "APIResponse"
]