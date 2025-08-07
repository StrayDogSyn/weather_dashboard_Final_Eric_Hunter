"""Data Repositories Package

This package contains repository implementations for data access:
- base_repository: Abstract repository base classes
- weather_repository: Weather data access
- preference_repository: User preferences data access
- activity_repository: Activity data access
"""

from .activity_repository import (
    ActivityRecommendation,
    ActivityRepository,
    ActivityType,
    WeatherSuitability,
)
from .base_repository import BaseRepository, InMemoryRepository, ReadOnlyRepository

__all__ = [
    # Base Repository
    "BaseRepository",
    "ReadOnlyRepository",
    "InMemoryRepository",
    # Weather Repositories
    "WeatherRepository",
    "ForecastRepository",
    # Preference Repository
    "PreferenceRepository",
    # Activity Repository
    "ActivityType",
    "WeatherSuitability",
    "ActivityRecommendation",
    "ActivityRepository",
]
