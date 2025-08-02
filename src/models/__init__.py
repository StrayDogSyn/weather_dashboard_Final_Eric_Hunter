"""Models Package

This package contains domain models organized by category:
- weather: Weather-related data models
- location: Location and geographic data models
- user: User preference and settings models
"""

# Import location models
from .location import Location, LocationResult, LocationSearchQuery

# Import user models
from .user import (
    DisplayPreferences,
    DistanceUnit,
    NotificationPreferences,
    PressureUnit,
    TemperatureUnit,
    Theme,
    TimeFormat,
    UnitPreferences,
    UserPreferences,
    WindSpeedUnit,
)

# Import weather models
from .weather import (
    AlertSeverity,
    AlertType,
    DailyForecast,
    ForecastData,
    ForecastEntry,
    WeatherAlert,
    WeatherCondition,
    WeatherData,
    safe_divide,
)

__version__ = "1.0.0"
__author__ = "Weather Dashboard Team"

__all__ = [
    # Weather Models
    "safe_divide",
    "WeatherCondition",
    "WeatherData",
    "ForecastEntry",
    "DailyForecast",
    "ForecastData",
    "AlertSeverity",
    "AlertType",
    "WeatherAlert",
    # Location Models
    "Location",
    "LocationResult",
    "LocationSearchQuery",
    # User Models
    "TemperatureUnit",
    "WindSpeedUnit",
    "PressureUnit",
    "DistanceUnit",
    "TimeFormat",
    "Theme",
    "UnitPreferences",
    "NotificationPreferences",
    "DisplayPreferences",
    "UserPreferences",
]
