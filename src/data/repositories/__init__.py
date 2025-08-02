"""Data Repositories Package

This package contains repository implementations for data access:
- base_repository: Abstract repository base classes
- weather_repository: Weather data access
- preference_repository: User preferences data access
- activity_repository: Activity data access
"""

from .base_repository import (
    BaseRepository,
    ReadOnlyRepository,
    InMemoryRepository
)

from .weather_repository import (
    WeatherRepository,
    ForecastRepository
)

from .preference_repository import (
    PreferenceRepository
)

from .activity_repository import (
    ActivityType,
    WeatherSuitability,
    ActivityRecommendation,
    ActivityRepository
)

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
    "ActivityRepository"
]