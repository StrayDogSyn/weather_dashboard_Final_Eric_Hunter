"""Weather services module.

Provides weather data retrieval, forecasting, and location services.
"""

from .weather_service import WeatherService
from .api_clients import (
    BaseAPIClient,
    OpenWeatherAPIClient,
    WeatherAPIClient,
)
from ..exceptions import (
    WeatherAppError as WeatherServiceError,
    APIError,
    RateLimitError,
    NetworkError,
    AuthenticationError as APIKeyError,
    WeatherAppError as ServiceUnavailableError,
)
from .models import (
    Location,
    LocationResult,
    WeatherAlert,
    WeatherData,
    ForecastEntry,
    DailyForecast,
    ForecastData,
    WeatherCondition,
)
from .enhanced_weather_service import EnhancedWeatherService
from .ml_weather_service import MLWeatherService
from .geocoding_service import GeocodingService

__all__ = [
    "WeatherService",
    "EnhancedWeatherService",
    "MLWeatherService",
    "GeocodingService",
    "BaseAPIClient",
    "OpenWeatherAPIClient",
    "WeatherAPIClient",
    "WeatherServiceError",
    "APIError",
    "RateLimitError",
    "NetworkError",
    "APIKeyError",
    "ServiceUnavailableError",
    "Location",
    "LocationResult",
    "WeatherAlert",
    "WeatherData",
    "ForecastEntry",
    "DailyForecast",
    "ForecastData",
    "WeatherCondition",
]