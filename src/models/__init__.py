"""Data Models Package

Defines structured data classes for weather information and application state.
"""

from .weather_models import (
    WeatherData,
    ForecastData,
    WeatherCondition,
    Location,
    WeatherAlert
)

__version__ = "1.0.0"
__author__ = "Weather Dashboard Team"

__all__ = [
    "WeatherData",
    "ForecastData", 
    "WeatherCondition",
    "Location",
    "WeatherAlert"
]