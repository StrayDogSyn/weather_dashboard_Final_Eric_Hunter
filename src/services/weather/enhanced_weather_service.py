"""Enhanced Weather Service - Extended API Integration

Handles weather data, air quality, astronomical data, and advanced search.
Implements robust error recovery and fallback mechanisms.
"""

import json
import logging
import random
import threading
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Callable

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from .models import (
    WeatherCondition,
    WeatherData,
    ForecastData,
    Location,
)
from ..config.config_service import ConfigService


# Custom Exception Types for Different Failure Modes
class WeatherServiceError(Exception):
    """Base exception for weather service errors."""


class RateLimitError(WeatherServiceError):
    """Raised when API rate limit is exceeded."""

    def __init__(self, retry_after: int = None):
        self.retry_after = retry_after
        super().__init__(f"Rate limit exceeded. Retry after {retry_after} seconds.")


class APIKeyError(WeatherServiceError):
    """Raised when API key is invalid or missing."""


class NetworkError(WeatherServiceError):
    """Raised when network connectivity issues occur."""


class ServiceUnavailableError(WeatherServiceError):
    """Raised when weather service is temporarily unavailable."""


@dataclass
class AirQualityData:
    """Air quality data model."""

    aqi: int  # Air Quality Index (1-5)
    co: float  # Carbon monoxide
    no: float  # Nitric oxide
    no2: float  # Nitrogen dioxide
    o3: float  # Ozone
    so2: float  # Sulphur dioxide
    pm2_5: float  # PM2.5
    pm10: float  # PM10
    nh3: float  # Ammonia
    timestamp: datetime

    def get_aqi_description(self) -> str:
        """Get AQI description."""
        descriptions = {1: "Good", 2: "Fair", 3: "Moderate", 4: "Poor", 5: "Very Poor"}
        return descriptions.get(self.aqi, "Unknown")

    def get_health_recommendation(self) -> str:
        """Get health recommendation based on AQI."""
        recommendations = {
            1: "Air quality is satisfactory for most people.",
            2: "Unusually sensitive people should consider reducing outdoor activities.",
            3: "Sensitive groups should reduce outdoor activities.",
            4: "Everyone should reduce outdoor activities.",
            5: "Everyone should avoid outdoor activities.",
        }
        return recommendations.get(self.aqi, "No recommendation available.")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        data = asdict(self)
        data["timestamp"] = self.timestamp.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AirQualityData":
        """Create from dictionary."""
        if isinstance(data["timestamp"], str):
            data["timestamp"] = datetime.fromisoformat(data["timestamp"])
        return cls(**data)


@dataclass
class AstronomicalData:
    """Astronomical data model."""

    sunrise: datetime
    sunset: datetime
    moonrise: Optional[datetime]
    moonset: Optional[datetime]
    moon_phase: float  # 0-1 (0 = new moon, 0.5 = full moon)
    day_length: timedelta

    def get_moon_phase_name(self) -> str:
        """Get moon phase name."""
        if self.moon_phase < 0.125:
            return "New Moon"
        elif self.moon_phase < 0.375:
            return "Waxing Crescent"
        elif self.moon_phase < 0.625:
            return "Full Moon"
        elif self.moon_phase < 0.875:
            return "Waning Crescent"
        else:
            return "New Moon"

    def get_moon_phase_emoji(self) -> str:
        """Get moon phase emoji."""
        if self.moon_phase < 0.125:
            return "🌑"
        elif self.moon_phase < 0.375:
            return "🌒"
        elif self.moon_phase < 0.625:
            return "🌕"
        elif self.moon_phase < 0.875:
            return "🌘"
        else:
            return "🌑"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        data = asdict(self)
        data["sunrise"] = self.sunrise.isoformat()
        data["sunset"] = self.sunset.isoformat()
        data["moonrise"] = self.moonrise.isoformat() if self.moonrise else None
        data["moonset"] = self.moonset.isoformat() if self.moonset else None
        data["day_length"] = self.day_length.total_seconds()
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AstronomicalData":
        """Create from dictionary."""
        if isinstance(data["sunrise"], str):
            data["sunrise"] = datetime.fromisoformat(data["sunrise"])
        if isinstance(data["sunset"], str):
            data["sunset"] = datetime.fromisoformat(data["sunset"])
        if data["moonrise"] and isinstance(data["moonrise"], str):
            data["moonrise"] = datetime.fromisoformat(data["moonrise"])
        if data["moonset"] and isinstance(data["moonset"], str):
            data["moonset"] = datetime.fromisoformat(data["moonset"])
        if isinstance(data["day_length"], (int, float)):
            data["day_length"] = timedelta(seconds=data["day_length"])
        elif isinstance(data["day_length"], str):
            try:
                data["day_length"] = timedelta(seconds=float(data["day_length"]))
            except (ValueError, TypeError):
                # Fallback to a default day length if conversion fails
                data["day_length"] = timedelta(hours=12)
        return cls(**data)


@dataclass
class WeatherAlert:
    """Weather alert data model."""

    event: str
    description: str
    severity: str  # minor, moderate, severe, extreme
    start_time: datetime
    end_time: datetime
    areas: List[str]

    def get_severity_color(self) -> str:
        """Get color for severity level."""
        colors = {
            "minor": "#FFEB3B",
            "moderate": "#FF9800",
            "severe": "#F44336",
            "extreme": "#9C27B0",
        }
        return colors.get(self.severity.lower(), "#757575")

    def get_severity_emoji(self) -> str:
        """Get emoji for severity level."""
        emojis = {"minor": "⚠️", "moderate": "🟡", "severe": "🔴", "extreme": "🟣"}
        return emojis.get(self.severity.lower(), "⚠️")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        data = asdict(self)
        data["start_time"] = self.start_time.isoformat()
        data["end_time"] = self.end_time.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WeatherAlert":
        """Create from dictionary."""
        if isinstance(data["start_time"], str):
            data["start_time"] = datetime.fromisoformat(data["start_time"])
        if isinstance(data["end_time"], str):
            data["end_time"] = datetime.fromisoformat(data["end_time"])
        return cls(**data)


@dataclass
class EnhancedWeatherData(WeatherData):
    """Enhanced weather data with additional information."""

    air_quality: Optional[AirQualityData] = None
    astronomical: Optional[AstronomicalData] = None
    alerts: List[WeatherAlert] = None
    forecast_data: Optional['ForecastData'] = None

    def __post_init__(self):
        if self.alerts is None:
            self.alerts = []


class LocationSearchResult:
    """Location search result with enhanced information."""

    def __init__(
        self,
        name: str,
        country: str,
        state: str = None,
        lat: float = None,
        lon: float = None,
        **kwargs,
    ):
        self.name = name
        self.country = country
        self.state = state
        self.lat = lat
        self.lon = lon
        self.display = self._create_display_name()

    def _create_display_name(self) -> str:
        """Create display name for location."""
        parts = [self.name]
        if self.state:
            parts.append(self.state)
        parts.append(self.country)
        return ", ".join(parts)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "country": self.country,
            "state": self.state,
            "lat": self.lat,
            "lon": self.lon,
            "display": self.display,
        }


class EnhancedWeatherService:
    """Enhanced weather service with extended capabilities."""

    def __init__(self, config_service: ConfigService):
        """Initialize enhanced weather service with robust error recovery."""
        self.config = config_service
        self.logger = logging.getLogger("weather_dashboard.enhanced_weather_service")
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._cache_file = Path.cwd() / "cache" / "enhanced_weather_cache.json"
        self._load_cache()

        # Offline mode detection
        self._offline_mode = False
        self._last_successful_request = time.time()
        self._failed_requests_start = None
        self._offline_threshold = 30  # seconds
        self._consecutive_failures = 0

        # Rate limiting with exponential backoff
        self._last_request_time = 0
        self._min_request_interval = 1.0  # 1 second between requests
        self._backoff_base = 1  # Start at 1 second
        self._backoff_max = 32  # Max 32 seconds
        self._backoff_multiplier = 2
        self._current_backoff = self._backoff_base

        # API fallback configuration
        self._primary_api = "openweather"
        self._backup_api = "openweather_backup"
        self._fallback_api = "weatherapi"
        self._api_switch_threshold = 3  # Switch after 3 consecutive failures
        self._current_api = self._primary_api

        # Connection pooling and retry strategy with proper timeouts
        self._session = self._create_session_with_retries()

        # Enhanced caching with TTL and stale data support
        self._cache_ttl = {
            "current_weather": 600,  # 10 minutes
            "forecast": 3600,  # 1 hour
            "air_quality": 1800,  # 30 minutes
            "geocoding": 86400 * 7,  # 7 days
            "stale_acceptable": 7200,  # 2 hours for stale data
        }

        self.logger.info("🌐 Enhanced Weather Service initialized with robust error recovery")

        # API endpoints
        self.base_url = self.config.weather.base_url
        self.api_key = self.config.weather.api_key
        
        # WeatherAPI base URL
        self.weatherapi_base_url = self.config.get_setting("api.weatherapi_base_url", "https://api.weatherapi.com/v1")
        
        # Observer pattern for weather updates
        self._observers: List[Callable] = []
        self._observer_lock = threading.Lock()

    def _load_cache(self) -> None:
        """Load enhanced weather cache from file."""
        try:
            if self._cache_file.exists():
                with open(self._cache_file, "r", encoding="utf-8") as f:
                    self._cache = json.load(f)
                self.logger.debug(f"📁 Loaded enhanced cache with {len(self._cache)} entries")
        except Exception as e:
            self.logger.warning(f"Failed to load enhanced cache: {e}")
            self._cache = {}

    def _save_cache(self) -> None:
        """Save enhanced weather cache to file."""
        try:
            self._cache_file.parent.mkdir(exist_ok=True)
            with open(self._cache_file, "w", encoding="utf-8") as f:
                json.dump(self._cache, f, indent=2, default=str)
        except Exception as e:
            self.logger.warning(f"Failed to save enhanced cache: {e}")

    def add_observer(self, observer: Callable) -> None:
        """Add an observer for weather updates in a thread-safe manner."""
        with self._observer_lock:
            if observer not in self._observers:
                self._observers.append(observer)
                self.logger.debug(f"Added weather observer: {observer.__name__ if hasattr(observer, '__name__') else str(observer)}")

    def remove_observer(self, observer: Callable) -> None:
        """Remove an observer for weather updates in a thread-safe manner."""
        with self._observer_lock:
            if observer in self._observers:
                self._observers.remove(observer)
                self.logger.debug(f"Removed weather observer: {observer.__name__ if hasattr(observer, '__name__') else str(observer)}")

    def notify_observers(self, weather_data: Any) -> None:
        """Thread-safe observer notification with dead observer cleanup."""
        with self._observer_lock:
            dead_observers = []
            
            for observer in self._observers[:]:
                try:
                    # Check if observer is still valid (widget-based observers)
                    if hasattr(observer, '__self__'):
                        widget = observer.__self__
                        if hasattr(widget, 'winfo_exists'):
                            try:
                                if not widget.winfo_exists():
                                    dead_observers.append(observer)
                                    continue
                            except Exception:
                                # Widget is likely destroyed
                                dead_observers.append(observer)
                                continue
                    
                    # Notify observer
                    observer(weather_data)
                    
                except Exception as e:
                    self.logger.error(f"Observer error: {e}")
                    dead_observers.append(observer)
            
            # Clean up dead observers
            for observer in dead_observers:
                try:
                    self._observers.remove(observer)
                    self.logger.debug(f"Removed dead observer: {observer.__name__ if hasattr(observer, '__name__') else str(observer)}")
                except ValueError:
                    pass  # Observer already removed
                    
            if dead_observers:
                self.logger.info(f"Cleaned up {len(dead_observers)} dead observers")
    
    def get_observer_count(self) -> int:
        """Get the current number of active observers."""
        with self._observer_lock:
            return len(self._observers)
    
    def cleanup_observers(self) -> None:
        """Manually cleanup all observers."""
        with self._observer_lock:
            observer_count = len(self._observers)
            self._observers.clear()
            self.logger.info(f"Cleaned up all {observer_count} observers")

    def _is_cache_valid(self, cache_entry: Dict[str, Any], cache_duration: int = None) -> bool:
        """Check if cache entry is still valid."""
        try:
            cached_time = datetime.fromisoformat(cache_entry["timestamp"])
            duration = cache_duration or self.config.app.cache_duration
            cache_duration_delta = timedelta(seconds=duration)
            return datetime.now() - cached_time < cache_duration_delta
        except (KeyError, ValueError):
            return False

    def _rate_limit(self) -> None:
        """Implement rate limiting."""
        current_time = datetime.now().timestamp()
        time_since_last = current_time - self._last_request_time

        if time_since_last < self._min_request_interval:
            sleep_time = self._min_request_interval - time_since_last
            import time

            time.sleep(sleep_time)

        self._last_request_time = datetime.now().timestamp()

    def _create_session_with_retries(self) -> requests.Session:
        """Create HTTP session with enhanced connection pooling and proper timeouts."""
        session = requests.Session()

        # Enhanced retry strategy with exponential backoff
        retry_strategy = Retry(
            total=3,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS"],
            backoff_factor=1,  # Will be handled by our custom exponential backoff
            raise_on_status=False,
            respect_retry_after_header=True,
        )

        # Enhanced HTTP adapter with proper connection pooling
        adapter = HTTPAdapter(
            max_retries=retry_strategy,
            pool_connections=20,
            pool_maxsize=50,
            pool_block=False,
        )

        session.mount("http://", adapter)
        session.mount("https://", adapter)

        # Set proper timeouts: 3 second connect, 5 second read
        session.timeout = (3.0, 5.0)

        # Add headers for better performance
        session.headers.update(
            {
                "Accept-Encoding": "gzip, deflate",
                "Connection": "keep-alive",
                "User-Agent": "WeatherDashboard/1.0",
            }
        )

        return session

    def _apply_exponential_backoff(self) -> None:
        """Apply exponential backoff for rate limiting."""
        if self._current_backoff > 0:
            jitter = random.uniform(0, 0.1 * self._current_backoff)  # Add jitter
            sleep_time = self._current_backoff + jitter
            self.logger.info(f"⏳ Applying exponential backoff: {sleep_time:.2f}s")
            time.sleep(sleep_time)

            # Increase backoff for next time, up to max
            self._current_backoff = min(
                self._current_backoff * self._backoff_multiplier, self._backoff_max
            )

    def _reset_backoff(self) -> None:
        """Reset exponential backoff after successful request."""
        self._current_backoff = self._backoff_base
        self._consecutive_failures = 0
        if self._failed_requests_start:
            self._failed_requests_start = None

    def _check_offline_mode(self) -> None:
        """Check if service should enter offline mode after consecutive failures."""
        current_time = time.time()

        if self._failed_requests_start is None:
            self._failed_requests_start = current_time

        time_since_first_failure = current_time - self._failed_requests_start

        if time_since_first_failure >= self._offline_threshold:
            if not self._offline_mode:
                self.logger.warning(
                    f"🔌 Entering offline mode after {self._offline_threshold}s of failures"
                )
                self._offline_mode = True

    def _should_use_fallback_api(self) -> bool:
        """Determine if we should switch to fallback API."""
        return self._consecutive_failures >= self._api_switch_threshold

    def _switch_to_fallback_api(self) -> None:
        """Switch to fallback API configuration."""
        if self._current_api == self._primary_api:
            # First try backup OpenWeather key
            if self.config.get_setting("api.openweather_backup_api_key"):
                self._current_api = self._backup_api
                self.logger.info(f"🔄 Switching to backup OpenWeather API key")
            else:
                # Skip to WeatherAPI if no backup key
                self._current_api = self._fallback_api
                self.logger.info(f"🔄 Switching to WeatherAPI fallback")
        elif self._current_api == self._backup_api:
            # Switch from backup to WeatherAPI
            self._current_api = self._fallback_api
            self.logger.info(f"🔄 Switching to WeatherAPI fallback")
        # Reset failure count when switching
        self._consecutive_failures = 0
        self._reset_backoff()

    def _get_stale_cache_data(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Get stale cache data when API is unavailable but cache exists."""
        if cache_key not in self._cache:
            return None

        cached_data = self._cache[cache_key]
        if "timestamp" not in cached_data:
            return None

        try:
            # Handle both string and datetime objects
            timestamp_value = cached_data["timestamp"]
            if isinstance(timestamp_value, str):
                cache_time = datetime.fromisoformat(timestamp_value)
            elif isinstance(timestamp_value, datetime):
                cache_time = timestamp_value
            else:
                self.logger.warning(f"Invalid timestamp type in stale cache: {type(timestamp_value)}")
                return None
                
            cache_age = time.time() - time.mktime(cache_time.timetuple())

            # Allow stale data up to the stale_acceptable limit
            if cache_age < self._cache_ttl["stale_acceptable"]:
                self.logger.info(f"📋 Using stale cache data (age: {cache_age:.0f}s)")
                stale_data = cached_data["data"].copy()
                stale_data["stale"] = True
                stale_data["cache_age"] = cache_age
                return stale_data
                
        except Exception as e:
            self.logger.error(f"Error processing stale cache timestamp: {e}")
            return None

        return None

    def _convert_to_weatherapi(self, endpoint: str, params: Dict[str, Any], api_key: str) -> tuple[Optional[str], Dict[str, Any]]:
        """Convert OpenWeather API endpoint to WeatherAPI format.
        
        Args:
            endpoint: OpenWeather endpoint (e.g., 'weather', 'forecast')
            params: OpenWeather parameters
            api_key: WeatherAPI key
            
        Returns:
            Tuple of (weatherapi_url, weatherapi_params) or (None, {}) if conversion fails
        """
        try:
            location = params.get('q', '')
            if not location:
                return None, {}
            
            weatherapi_params = {
                'key': api_key,
                'q': location,
                'aqi': 'yes'  # Include air quality data
            }
            
            # Convert endpoints
            if endpoint == 'weather':
                # Current weather
                url = f"{self.weatherapi_base_url}/current.json"
            elif endpoint == 'forecast':
                # Weather forecast
                url = f"{self.weatherapi_base_url}/forecast.json"
                weatherapi_params['days'] = 7  # 7-day forecast
                weatherapi_params['alerts'] = 'yes'
            elif endpoint.startswith('air_pollution'):
                # Air quality - use current endpoint with aqi=yes
                url = f"{self.weatherapi_base_url}/current.json"
            else:
                # Unsupported endpoint
                self.logger.warning(f"🔄 WeatherAPI does not support endpoint: {endpoint}")
                return None, {}
                
            return url, weatherapi_params
            
        except Exception as e:
            self.logger.error(f"🔄 Error converting to WeatherAPI format: {e}")
            return None, {}

    def _is_cache_valid_with_ttl(self, cache_key: str, cache_type: str) -> bool:
        """Check if cached data is still valid based on TTL."""
        if cache_key not in self._cache:
            return False

        cached_data = self._cache[cache_key]
        if "timestamp" not in cached_data:
            return False

        try:
            # Debug logging to identify timestamp format issues
            timestamp_value = cached_data["timestamp"]
            self.logger.debug(f"DEBUG: Cache timestamp type: {type(timestamp_value)}, value: {timestamp_value}")
            
            # Handle both string and datetime objects
            if isinstance(timestamp_value, str):
                cache_time = datetime.fromisoformat(timestamp_value)
            elif isinstance(timestamp_value, datetime):
                cache_time = timestamp_value
            else:
                self.logger.warning(f"Invalid timestamp type in cache: {type(timestamp_value)}")
                return False
                
            cache_age = time.time() - time.mktime(cache_time.timetuple())
            ttl = self._cache_ttl.get(cache_type, 600)  # Default 10 minutes
            
            return cache_age < ttl
            
        except Exception as e:
            self.logger.error(f"Error validating cache timestamp: {e}")
            return False

    def _get_offline_fallback(self, data_type: str, location: str = "Unknown") -> Dict[str, Any]:
        """Get enhanced offline fallback data when API is unavailable."""
        self.logger.warning(f"🔌 Using offline fallback for {data_type}")

        # Try to get last known good data from cache first
        cache_key = f"{data_type}_{location.lower()}"
        if cache_key in self._cache:
            cached_data = self._cache[cache_key]
            if "data" in cached_data:
                self.logger.info(f"Using cached {data_type} data for offline mode")
                cached_data["data"]["offline"] = True
                cached_data["data"]["cache_used"] = True
                return cached_data["data"]

        # Fallback to default offline data
        fallbacks = {
            "weather": {
                "location": location,
                "temperature": 20.0,
                "condition": "Offline Mode",
                "description": "Weather data unavailable - check connection",
                "humidity": 50,
                "pressure": 1013.25,
                "wind_speed": 0.0,
                "timestamp": time.time(),
                "offline": True,
                "cache_used": False,
            },
            "forecast": {
                "location": location,
                "days": [],
                "message": "Forecast unavailable in offline mode",
                "offline": True,
                "cache_used": False,
            },
            "air_quality": {
                "location": location,
                "aqi": 50,
                "quality": "Offline Mode",
                "offline": True,
                "cache_used": False,
            },
        }

        return fallbacks.get(data_type, {"error": "No offline data available"})

    def _make_request(self, endpoint: str, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Make API request with robust error handling, fallback, and intelligent caching."""
        cache_key = f"{endpoint}_{str(sorted(params.items()))}"

        # Check if we're in offline mode
        if self._offline_mode:
            self.logger.warning("🔌 Service in offline mode, trying stale cache")
            stale_data = self._get_stale_cache_data(cache_key)
            if stale_data:
                return stale_data
            return self._get_offline_fallback("weather", params.get("q", "Unknown"))

        # Apply exponential backoff if needed
        if self._consecutive_failures > 0:
            self._apply_exponential_backoff()

        # Check if we should switch to fallback API
        if self._should_use_fallback_api():
            self._switch_to_fallback_api()

        try:
            # Rate limiting
            self._rate_limit()

            # Configure API parameters based on current API
            if self._current_api == "openweather":
                params.update({"appid": self.api_key, "units": self.config.weather.units})
                url = f"{self.base_url}/{endpoint}"
            elif self._current_api == "openweather_backup":
                # Use backup OpenWeather API key
                backup_key = self.config.get_setting("api.openweather_backup_api_key")
                params.update({"appid": backup_key, "units": self.config.weather.units})
                url = f"{self.base_url}/{endpoint}"
            elif self._current_api == "weatherapi":
                # WeatherAPI configuration
                weatherapi_key = self.config.get_setting("api.weatherapi_api_key")
                if weatherapi_key:
                    # Convert OpenWeather endpoint to WeatherAPI format
                    weatherapi_url, weatherapi_params = self._convert_to_weatherapi(endpoint, params, weatherapi_key)
                    if weatherapi_url:
                        url = weatherapi_url
                        params = weatherapi_params
                    else:
                        self.logger.warning("🔄 WeatherAPI endpoint conversion failed, using OpenWeather format")
                        params.update({"appid": self.api_key, "units": self.config.weather.units})
                        url = f"{self.base_url}/{endpoint}"
                else:
                    self.logger.warning("🔄 WeatherAPI key not available, using primary OpenWeather")
                    params.update({"appid": self.api_key, "units": self.config.weather.units})
                    url = f"{self.base_url}/{endpoint}"


            # Use session with connection pooling and retries
            response = self._session.get(url, params=params)

            if response.status_code == 200:
                # Success - reset error tracking
                self._last_successful_request = time.time()
                self._offline_mode = False
                self._reset_backoff()
                return response.json()
            elif response.status_code == 429:
                # Rate limit exceeded
                self._consecutive_failures += 1
                retry_after = int(response.headers.get("Retry-After", self._current_backoff))
                raise RateLimitError(retry_after)
            elif response.status_code == 401:
                # Invalid API key
                raise APIKeyError("Invalid API key - please check your configuration")
            elif response.status_code == 404:
                # Location not found - handle differently for air quality vs weather
                if "air_pollution" in endpoint:
                    # Air quality data not available for this location - return None gracefully
                    return None
                else:
                    # Weather/geocoding location not found - this is an error
                    raise ValueError("Location not found - please check the spelling")
            else:
                # Other HTTP errors
                self._consecutive_failures += 1
                raise ServiceUnavailableError(f"API returned status {response.status_code}")

        except (requests.exceptions.Timeout, requests.exceptions.ReadTimeout):
            self.logger.error("⏰ API request timed out")
            self._consecutive_failures += 1
            self._check_offline_mode()

            # Try stale cache data
            stale_data = self._get_stale_cache_data(cache_key)
            if stale_data:
                return stale_data
            raise NetworkError("Request timeout - please try again")

        except requests.exceptions.ConnectionError:
            self.logger.error("🌐 Connection error")
            self._consecutive_failures += 1
            self._check_offline_mode()

            # Try stale cache data
            stale_data = self._get_stale_cache_data(cache_key)
            if stale_data:
                return stale_data

            if self._offline_mode:
                return self._get_offline_fallback("weather", params.get("q", "Unknown"))
            raise NetworkError("No internet connection - please check your network")

        except RateLimitError:
            # Re-raise rate limit errors
            raise
        except APIKeyError:
            # Re-raise API key errors
            raise
        except Exception as e:
            self.logger.error(f"❌ Unexpected API error: {e}")
            self._consecutive_failures += 1
            self._check_offline_mode()

            # Try stale cache data as last resort
            stale_data = self._get_stale_cache_data(cache_key)
            if stale_data:
                return stale_data

            raise WeatherServiceError(f"Weather service error: {str(e)}")

    def _make_geocoding_request(
        self, endpoint: str, params: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Make geocoding API request with robust error handling and caching."""
        cache_key = f"geocoding_{endpoint}_{str(sorted(params.items()))}"

        # Check if we're in offline mode
        if self._offline_mode:
            self.logger.warning("🔌 Service in offline mode, trying cached geocoding")
            stale_data = self._get_stale_cache_data(cache_key)
            return stale_data

        # Apply exponential backoff if needed
        if self._consecutive_failures > 0:
            self._apply_exponential_backoff()

        # Check if we should switch to fallback API
        if self._should_use_fallback_api():
            self._switch_to_fallback_api()

        try:
            # Rate limiting
            self._rate_limit()

            # Configure API parameters based on current API
            if self._current_api == "openweather":
                params.update({"appid": self.api_key})
                url = f"https://api.openweathermap.org/{endpoint}"
            else:
                # WeatherAPI fallback configuration
                self.logger.warning("🔄 WeatherAPI geocoding fallback not fully implemented")
                params.update({"appid": self.api_key})
                url = f"https://api.openweathermap.org/{endpoint}"


            # Use session with connection pooling and retries
            response = self._session.get(url, params=params)

            if response.status_code == 200:
                # Success - reset error tracking
                self._last_successful_request = time.time()
                self._offline_mode = False
                self._reset_backoff()
                return response.json()
            elif response.status_code == 429:
                # Rate limit exceeded
                self._consecutive_failures += 1
                retry_after = int(response.headers.get("Retry-After", self._current_backoff))
                raise RateLimitError(retry_after)
            elif response.status_code == 401:
                # Invalid API key
                raise APIKeyError("Invalid API key for geocoding")
            elif response.status_code == 404:
                # Location not found - not a service error
                return None
            else:
                # Other HTTP errors
                self._consecutive_failures += 1
                raise ServiceUnavailableError(
                    f"Geocoding API returned status {response.status_code}"
                )

        except (requests.exceptions.Timeout, requests.exceptions.ReadTimeout):
            self.logger.error("⏰ Geocoding request timed out")
            self._consecutive_failures += 1
            self._check_offline_mode()

            # Try stale cache data
            stale_data = self._get_stale_cache_data(cache_key)
            if stale_data:
                return stale_data
            raise NetworkError("Geocoding timeout - please try again")

        except requests.exceptions.ConnectionError:
            self.logger.error("🌐 Geocoding connection error")
            self._consecutive_failures += 1
            self._check_offline_mode()

            # Try stale cache data
            stale_data = self._get_stale_cache_data(cache_key)
            if stale_data:
                return stale_data
            raise NetworkError("No internet connection - please check your network")

        except RateLimitError:
            # Re-raise rate limit errors
            raise
        except APIKeyError:
            # Re-raise API key errors
            raise
        except Exception as e:
            self.logger.error(f"❌ Unexpected geocoding error: {e}")
            self._consecutive_failures += 1
            self._check_offline_mode()

            # Try stale cache data as last resort
            stale_data = self._get_stale_cache_data(cache_key)
            if stale_data:
                return stale_data

            raise WeatherServiceError(f"Geocoding service error: {str(e)}")

    def search_locations(self, query: str, limit: int = 5) -> List[LocationSearchResult]:
        """Enhanced location search with support for multiple formats including zipcodes."""
        # Validate and clean query input
        if not query or not isinstance(query, str):
            self.logger.warning("Invalid search query: must be a non-empty string")
            return []

        query = query.strip()
        if len(query) < 2:
            self.logger.warning("Search query too short: must be at least 2 characters")
            return []

        # Validate limit parameter
        if not isinstance(limit, int) or limit < 1:
            limit = 5
        elif limit > 20:  # Reasonable upper bound
            limit = 20

        cache_key = f"search_{query.lower()}_{limit}"

        # Check cache first (longer cache for search results)
        if cache_key in self._cache and self._is_cache_valid(
            self._cache[cache_key], 3600
        ):  # 1 hour cache
            cached_data = self._cache[cache_key]["data"]
            return [LocationSearchResult(**item) for item in cached_data]

        try:
            self.logger.info(f"🔍 Enhanced search for locations: {query}")

            # Detect query type and use appropriate search method
            search_type = self._detect_query_type(query)

            locations = []

            if search_type == "zipcode":
                locations = self._search_by_zipcode(query, limit)
            elif search_type == "coordinates":
                locations = self._search_by_coordinates(query)
            elif search_type == "airport":
                locations = self._search_by_airport(query, limit)
            else:
                # Default to geocoding search for city names and general
                # queries
                locations = self._search_by_geocoding(query, limit)

            # If primary search fails, try fallback methods
            if not locations and search_type != "geocoding":
                locations = self._search_by_geocoding(query, limit)

            # Cache the results
            self._cache[cache_key] = {
                "data": [loc.to_dict() for loc in locations],
                "timestamp": datetime.now().isoformat(),
            }
            self._save_cache()

            self.logger.info(f"✅ Found {len(locations)} locations for {query}")
            return locations

        except Exception as e:
            self.logger.warning(f"Enhanced location search failed: {e}")
            return []

    def search_locations_advanced(self, query: str) -> List["LocationResult"]:
        """Advanced location search with support for multiple formats."""

        query = query.strip()
        if not query:
            return []

        # Check if zip code
        if self.is_zip_code(query):
            return self.geocode_zip(query)

        # Check if coordinates
        if self.is_coordinates(query):
            return self.reverse_geocode(query)

        # Standard city search with fuzzy matching
        return self.search_cities_fuzzy(query)

    def is_zip_code(self, query: str) -> bool:
        """Check if query is a zip/postal code."""
        import re

        zip_patterns = {
            "US": re.compile(r"^\d{5}(-\d{4})?$"),  # 12345 or 12345-6789
            # SW1A 1AA
            "UK": re.compile(r"^[A-Z]{1,2}\d[A-Z\d]?\s?\d[A-Z]{2}$", re.IGNORECASE),
            # K1A 0A6
            "CA": re.compile(r"^[A-Z]\d[A-Z]\s?\d[A-Z]\d$", re.IGNORECASE),
        }

        for pattern in zip_patterns.values():
            if pattern.match(query):
                return True
        return False

    def is_coordinates(self, query: str) -> bool:
        """Check if query is coordinates (lat,lon)."""
        import re

        coordinate_pattern = re.compile(r"^(-?\d+\.?\d*),\s*(-?\d+\.?\d*)$")
        return bool(coordinate_pattern.match(query))

    def geocode_zip(self, zip_code: str) -> List["LocationResult"]:
        """Geocode a zip/postal code."""
        from ..models.location import LocationResult

        try:
            # Convert existing LocationSearchResult to LocationResult
            search_results = self._search_by_zipcode(zip_code, 3)
            location_results = []

            for result in search_results:
                location_result = LocationResult(
                    name=result.name,
                    display_name=f"{result.name}, {result.state or ''}, "
                    f"{result.country}".strip(", "),
                    latitude=result.lat or 0.0,
                    longitude=result.lon or 0.0,
                    country=result.country,
                    country_code=result.country[:2].upper() if result.country else "",
                    state=result.state,
                    raw_address=f"{result.name}, {result.state or ''}, {result.country}".strip(
                        ", "
                    ),
                )
                location_results.append(location_result)

            return location_results

        except Exception as e:
            self.logger.error(f"Geocoding error for zip '{zip_code}': {e}")
            return []

    def reverse_geocode(self, coordinates: str) -> List["LocationResult"]:
        """Reverse geocode coordinates."""
        import re

        from ..models.location import LocationResult

        try:
            coordinate_pattern = re.compile(r"^(-?\d+\.?\d*),\s*(-?\d+\.?\d*)$")
            match = coordinate_pattern.match(coordinates)
            if not match:
                return []

            # Convert existing coordinate search to LocationResult
            search_results = self._search_by_coordinates(coordinates)
            location_results = []

            for result in search_results:
                location_result = LocationResult(
                    name=result.name,
                    display_name=f"{result.name}, {result.state or ''}, "
                    f"{result.country}".strip(", "),
                    latitude=result.lat or 0.0,
                    longitude=result.lon or 0.0,
                    country=result.country,
                    country_code=result.country[:2].upper() if result.country else "",
                    state=result.state,
                    raw_address=f"{result.name}, {result.state or ''}, {result.country}".strip(
                        ", "
                    ),
                )
                location_results.append(location_result)

            return location_results

        except Exception as e:
            self.logger.error(f"Reverse geocoding error for '{coordinates}': {e}")
            return []

    def search_cities_fuzzy(self, query: str) -> List["LocationResult"]:
        """Search cities with fuzzy matching."""
        from ..models.location import LocationResult

        try:
            # Convert existing geocoding search to LocationResult
            search_results = self._search_by_geocoding(query, 8)
            location_results = []

            for result in search_results:
                location_result = LocationResult(
                    name=result.name,
                    display_name=f"{result.name}, {result.state or ''}, "
                    f"{result.country}".strip(", "),
                    latitude=result.lat or 0.0,
                    longitude=result.lon or 0.0,
                    country=result.country,
                    country_code=result.country[:2].upper() if result.country else "",
                    state=result.state,
                    raw_address=f"{result.name}, {result.state or ''}, {result.country}".strip(
                        ", "
                    ),
                )
                location_results.append(location_result)

            return location_results

        except Exception as e:
            self.logger.error(f"City search error for '{query}': {e}")
            return []

    def _detect_query_type(self, query: str) -> str:
        """Detect the type of location query (zipcode, coordinates, airport code, or general)."""
        import re

        query = query.strip()

        # Check for coordinates (lat,lon format)
        coord_pattern = r"^-?\d+\.?\d*\s*,\s*-?\d+\.?\d*$"
        if re.match(coord_pattern, query):
            return "coordinates"

        # Check for airport codes (3-letter IATA or 4-letter ICAO)
        airport_pattern = r"^[A-Z]{3,4}$"
        if re.match(airport_pattern, query.upper()) and len(query) in [3, 4]:
            return "airport"

        # Check for US zipcode (5 digits or 5+4 format)
        us_zip_pattern = r"^\d{5}(-\d{4})?$"
        if re.match(us_zip_pattern, query):
            return "zipcode"

        # Check for international postal codes (various formats)
        # UK: SW1A 1AA, Canada: K1A 0A6, etc.
        intl_postal_patterns = [
            r"^[A-Z]{1,2}\d[A-Z\d]?\s?\d[A-Z]{2}$",  # UK
            r"^[A-Z]\d[A-Z]\s?\d[A-Z]\d$",  # Canada
            r"^\d{4,5}$",  # Germany, France, etc.
            r"^\d{3}-\d{4}$",  # Japan
        ]

        for pattern in intl_postal_patterns:
            if re.match(pattern, query.upper()):
                return "zipcode"

        # Default to geocoding for city names and general queries
        return "geocoding"

    def _search_by_zipcode(self, zipcode: str, limit: int = 5) -> List[LocationSearchResult]:
        """Search location by zipcode using OpenWeather's zip endpoint with geocoding fallback."""
        try:
            # Format zipcode for API (remove spaces, handle international
            # formats)
            formatted_zip = zipcode.replace(" ", "")

            # For US zipcodes, use simple format
            if formatted_zip.isdigit() and len(formatted_zip) == 5:
                query_param = f"{formatted_zip},US"
            elif "-" in formatted_zip and len(formatted_zip.split("-")[0]) == 5:
                # US ZIP+4 format
                query_param = f"{formatted_zip.split('-')[0]},US"
            else:
                # International postal code - try without country code first
                query_param = formatted_zip


            # Use zip endpoint for direct zipcode lookup
            data = self._make_geocoding_request("geo/1.0/zip", {"zip": query_param})

            if data and "lat" in data and "lon" in data:
                # Get proper location name, fallback to reverse geocoding if needed
                location_name = data.get("name")
                if not location_name or location_name == zipcode:
                    # Try to get a better name using reverse geocoding
                    try:
                        reverse_data = self._make_geocoding_request(
                            "geo/1.0/reverse", 
                            {"lat": data.get("lat"), "lon": data.get("lon"), "limit": 1}
                        )
                        if reverse_data and len(reverse_data) > 0:
                            location_name = reverse_data[0].get("name", zipcode)
                    except Exception:
                        location_name = zipcode
                
                location = LocationSearchResult(
                    name=location_name,
                    country=data.get("country", ""),
                    state="",  # Zip endpoint doesn't provide state
                    lat=data.get("lat"),
                    lon=data.get("lon"),
                )
                return [location]

            # If zip endpoint fails, try geocoding as fallback for
            # international postal codes
            return self._search_by_geocoding(zipcode, limit)

        except Exception as e:
            self.logger.warning(f"Zipcode search failed for {zipcode}: {e}")
            # Try geocoding as final fallback
            try:
                return self._search_by_geocoding(zipcode, limit)
            except Exception as fallback_e:
                self.logger.warning(f"Geocoding fallback also failed for {zipcode}: {fallback_e}")
                return []

    def _search_by_coordinates(self, coords: str) -> List[LocationSearchResult]:
        """Search location by coordinates using reverse geocoding."""
        try:
            # Parse coordinates
            parts = coords.replace(" ", "").split(",")
            if len(parts) != 2:
                return []

            lat = float(parts[0])
            lon = float(parts[1])

            # Validate coordinate ranges
            if not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
                self.logger.warning(f"Invalid coordinates: {lat}, {lon}")
                return []

            # Warn about extreme coordinates that might not have meaningful
            # results
            if abs(lat) >= 89 or abs(lon) >= 179:
                self.logger.debug(
                    f"⚠️ Using extreme coordinates: {lat}, {lon} - results may be limited"
                )


            # Use reverse geocoding
            data = self._make_geocoding_request(
                "geo/1.0/reverse", {"lat": lat, "lon": lon, "limit": 1}
            )

            if data and len(data) > 0:
                item = data[0]
                location = LocationSearchResult(
                    name=item.get("name", f"{lat}, {lon}"),
                    country=item.get("country", ""),
                    state=item.get("state", ""),
                    lat=lat,
                    lon=lon,
                )
                return [location]

            # If reverse geocoding fails, still return the coordinates as a
            # valid location
            location = LocationSearchResult(
                name=f"Location at {lat}, {lon}", country="", state="", lat=lat, lon=lon
            )
            return [location]

        except (ValueError, IndexError) as e:
            self.logger.warning(f"Coordinate parsing failed for {coords}: {e}")
            return []
        except Exception as e:
            self.logger.warning(f"Coordinate search failed for {coords}: {e}")
            return []

    def _search_by_geocoding(self, query: str, limit: int = 5) -> List[LocationSearchResult]:
        """Search location using standard geocoding API with multiple query
        strategies and enhanced fallback."""
        # Try multiple query formats for better results
        query_variations = self._generate_query_variations(query)

        # If query looks like a postal code, add international variations
        if self._detect_query_type(query) == "zipcode":
            postal_variations = [
                f"{query}, UK",
                f"{query}, Canada",
                f"{query}, Germany",
                f"{query}, France",
                f"{query}, Japan",
                f"{query}, Australia",
            ]
            query_variations.extend(postal_variations)

        for i, query_variant in enumerate(query_variations):
            try:
                self.logger.debug(
                    f"🏙️ Geocoding search attempt {i + 1}/{len(query_variations)}: {query_variant}"
                )

                data = self._make_geocoding_request(
                    "geo/1.0/direct", {"q": query_variant, "limit": limit}
                )

                if data and len(data) > 0:
                    locations = []
                    for item in data:
                        location = LocationSearchResult(
                            name=item.get("name", ""),
                            country=item.get("country", ""),
                            state=item.get("state", ""),
                            lat=item.get("lat"),
                            lon=item.get("lon"),
                        )
                        locations.append(location)

                    self.logger.debug(
                        f"✅ Found {
                            len(locations)} locations with query: {query_variant}"
                    )
                    return locations

            except Exception as e:
                continue

        self.logger.warning(f"All geocoding attempts failed for: {query}")
        return []

    def _search_by_airport(self, airport_code: str, limit: int = 5) -> List[LocationSearchResult]:
        """Search location by airport code (IATA/ICAO) with comprehensive airport database."""
        try:
            airport_code = airport_code.upper().strip()
            
            # Comprehensive airport database with major airports
            airport_database = {
                # Major US airports
                "JFK": {"name": "John F. Kennedy International Airport", "city": "New York", "state": "NY", "country": "US", "lat": 40.6413, "lon": -73.7781},
                "LAX": {"name": "Los Angeles International Airport", "city": "Los Angeles", "state": "CA", "country": "US", "lat": 33.9425, "lon": -118.4081},
                "ORD": {"name": "O'Hare International Airport", "city": "Chicago", "state": "IL", "country": "US", "lat": 41.9742, "lon": -87.9073},
                "ATL": {"name": "Hartsfield-Jackson Atlanta International Airport", "city": "Atlanta", "state": "GA", "country": "US", "lat": 33.6407, "lon": -84.4277},
                "DFW": {"name": "Dallas/Fort Worth International Airport", "city": "Dallas", "state": "TX", "country": "US", "lat": 32.8998, "lon": -97.0403},
                "DEN": {"name": "Denver International Airport", "city": "Denver", "state": "CO", "country": "US", "lat": 39.8561, "lon": -104.6737},
                "SFO": {"name": "San Francisco International Airport", "city": "San Francisco", "state": "CA", "country": "US", "lat": 37.6213, "lon": -122.3790},
                "SEA": {"name": "Seattle-Tacoma International Airport", "city": "Seattle", "state": "WA", "country": "US", "lat": 47.4502, "lon": -122.3088},
                "LAS": {"name": "McCarran International Airport", "city": "Las Vegas", "state": "NV", "country": "US", "lat": 36.0840, "lon": -115.1537},
                "PHX": {"name": "Phoenix Sky Harbor International Airport", "city": "Phoenix", "state": "AZ", "country": "US", "lat": 33.4484, "lon": -112.0740},
                "IAH": {"name": "George Bush Intercontinental Airport", "city": "Houston", "state": "TX", "country": "US", "lat": 29.9902, "lon": -95.3368},
                "MIA": {"name": "Miami International Airport", "city": "Miami", "state": "FL", "country": "US", "lat": 25.7959, "lon": -80.2870},
                "BOS": {"name": "Logan International Airport", "city": "Boston", "state": "MA", "country": "US", "lat": 42.3656, "lon": -71.0096},
                "MSP": {"name": "Minneapolis-Saint Paul International Airport", "city": "Minneapolis", "state": "MN", "country": "US", "lat": 42.2124, "lon": -121.7269},
                "DTW": {"name": "Detroit Metropolitan Wayne County Airport", "city": "Detroit", "state": "MI", "country": "US", "lat": 42.2162, "lon": -83.3554},
                "PHL": {"name": "Philadelphia International Airport", "city": "Philadelphia", "state": "PA", "country": "US", "lat": 39.8744, "lon": -75.2424},
                "LGA": {"name": "LaGuardia Airport", "city": "New York", "state": "NY", "country": "US", "lat": 40.7769, "lon": -73.8740},
                "BWI": {"name": "Baltimore/Washington International Airport", "city": "Baltimore", "state": "MD", "country": "US", "lat": 39.1774, "lon": -76.6684},
                "DCA": {"name": "Ronald Reagan Washington National Airport", "city": "Washington", "state": "DC", "country": "US", "lat": 38.8512, "lon": -77.0402},
                "IAD": {"name": "Washington Dulles International Airport", "city": "Washington", "state": "VA", "country": "US", "lat": 38.9531, "lon": -77.4565},
                
                # Major international airports
                "LHR": {"name": "Heathrow Airport", "city": "London", "state": "", "country": "GB", "lat": 51.4700, "lon": -0.4543},
                "CDG": {"name": "Charles de Gaulle Airport", "city": "Paris", "state": "", "country": "FR", "lat": 49.0097, "lon": 2.5479},
                "FRA": {"name": "Frankfurt Airport", "city": "Frankfurt", "state": "", "country": "DE", "lat": 50.0379, "lon": 8.5622},
                "AMS": {"name": "Amsterdam Airport Schiphol", "city": "Amsterdam", "state": "", "country": "NL", "lat": 52.3105, "lon": 4.7683},
                "MAD": {"name": "Madrid-Barajas Airport", "city": "Madrid", "state": "", "country": "ES", "lat": 40.4839, "lon": -3.5680},
                "FCO": {"name": "Leonardo da Vinci International Airport", "city": "Rome", "state": "", "country": "IT", "lat": 41.8003, "lon": 12.2389},
                "ZUR": {"name": "Zurich Airport", "city": "Zurich", "state": "", "country": "CH", "lat": 47.4647, "lon": 8.5492},
                "VIE": {"name": "Vienna International Airport", "city": "Vienna", "state": "", "country": "AT", "lat": 48.1103, "lon": 16.5697},
                "ARN": {"name": "Stockholm Arlanda Airport", "city": "Stockholm", "state": "", "country": "SE", "lat": 59.6519, "lon": 17.9186},
                "CPH": {"name": "Copenhagen Airport", "city": "Copenhagen", "state": "", "country": "DK", "lat": 55.6181, "lon": 12.6561},
                
                # Major Asia-Pacific airports
                "NRT": {"name": "Narita International Airport", "city": "Tokyo", "state": "", "country": "JP", "lat": 35.7720, "lon": 140.3929},
                "HND": {"name": "Haneda Airport", "city": "Tokyo", "state": "", "country": "JP", "lat": 35.5494, "lon": 139.7798},
                "ICN": {"name": "Incheon International Airport", "city": "Seoul", "state": "", "country": "KR", "lat": 37.4602, "lon": 126.4407},
                "PEK": {"name": "Beijing Capital International Airport", "city": "Beijing", "state": "", "country": "CN", "lat": 40.0799, "lon": 116.6031},
                "PVG": {"name": "Shanghai Pudong International Airport", "city": "Shanghai", "state": "", "country": "CN", "lat": 31.1443, "lon": 121.8083},
                "HKG": {"name": "Hong Kong International Airport", "city": "Hong Kong", "state": "", "country": "HK", "lat": 22.3080, "lon": 113.9185},
                "SIN": {"name": "Singapore Changi Airport", "city": "Singapore", "state": "", "country": "SG", "lat": 1.3644, "lon": 103.9915},
                "BKK": {"name": "Suvarnabhumi Airport", "city": "Bangkok", "state": "", "country": "TH", "lat": 13.6900, "lon": 100.7501},
                "KUL": {"name": "Kuala Lumpur International Airport", "city": "Kuala Lumpur", "state": "", "country": "MY", "lat": 2.7456, "lon": 101.7072},
                "SYD": {"name": "Sydney Kingsford Smith Airport", "city": "Sydney", "state": "NSW", "country": "AU", "lat": -33.9399, "lon": 151.1753},
                "MEL": {"name": "Melbourne Airport", "city": "Melbourne", "state": "VIC", "country": "AU", "lat": -37.6690, "lon": 144.8410},
                
                # Major Canadian airports
                "YYZ": {"name": "Toronto Pearson International Airport", "city": "Toronto", "state": "ON", "country": "CA", "lat": 43.6777, "lon": -79.6248},
                "YVR": {"name": "Vancouver International Airport", "city": "Vancouver", "state": "BC", "country": "CA", "lat": 49.1967, "lon": -123.1815},
                "YUL": {"name": "Montreal-Pierre Elliott Trudeau International Airport", "city": "Montreal", "state": "QC", "country": "CA", "lat": 45.4706, "lon": -73.7408},
                "YYC": {"name": "Calgary International Airport", "city": "Calgary", "state": "AB", "country": "CA", "lat": 51.1315, "lon": -114.0106},
            }
            
            if airport_code in airport_database:
                airport_info = airport_database[airport_code]
                
                # Create display name with city and airport name
                if airport_info["state"]:
                    display_name = f"{airport_info['city']}, {airport_info['state']}, {airport_info['country']} ({airport_code})"
                else:
                    display_name = f"{airport_info['city']}, {airport_info['country']} ({airport_code})"
                
                location = LocationSearchResult(
                    name=display_name,
                    country=airport_info["country"],
                    state=airport_info["state"],
                    lat=airport_info["lat"],
                    lon=airport_info["lon"],
                )
                
                self.logger.info(f"✅ Found airport: {display_name}")
                return [location]
            
            # If not found in database, try geocoding as fallback
            fallback_queries = [
                f"{airport_code} airport",
                f"{airport_code} international airport",
                airport_code
            ]
            
            for query in fallback_queries:
                try:
                    results = self._search_by_geocoding(query, limit)
                    if results:
                        # Enhance the result to indicate it's an airport
                        for result in results:
                            if "airport" not in result.name.lower():
                                result.name = f"{result.name} ({airport_code})"
                        return results
                except Exception as e:
                    continue
            
            self.logger.warning(f"Airport code {airport_code} not found")
            return []
            
        except Exception as e:
            self.logger.warning(f"Airport search failed for {airport_code}: {e}")
            return []

    def _generate_query_variations(self, query: str) -> List[str]:
        """Generate multiple query variations to improve search success."""
        variations = [query.strip()]

        # Remove common suffixes that might confuse the API
        suffixes_to_try = [", United States", ", USA", ", US"]
        base_query = query.strip()

        for suffix in suffixes_to_try:
            if base_query.endswith(suffix):
                # Try without the suffix
                without_suffix = base_query[: -len(suffix)].strip()
                if without_suffix not in variations:
                    variations.append(without_suffix)
                break

        # For US locations, try different formats
        if "United States" in query or ", US" in query or ", USA" in query:
            parts = (
                base_query.replace(", United States", "")
                .replace(", USA", "")
                .replace(", US", "")
                .split(",")
            )
            if len(parts) >= 2:
                city = parts[0].strip()
                state = parts[1].strip()

                # Try "City, State" format
                city_state = f"{city}, {state}"
                if city_state not in variations:
                    variations.append(city_state)

                # Try "City, State, US" format
                city_state_us = f"{city}, {state}, US"
                if city_state_us not in variations:
                    variations.append(city_state_us)

                # Try just the city name
                if city not in variations:
                    variations.append(city)

        return variations

    def _geocode_query(self, query: str, limit: int = 5) -> Optional[List[Dict[str, Any]]]:
        """Make geocoding request with proper error handling."""
        try:
            # Use the new geocoding request method
            data = self._make_geocoding_request(
                "geo/1.0/direct", {"q": query, "limit": limit}
            )

            return data if data else []

        except Exception as e:
            if "Invalid API key" in str(e) or "Rate limit" in str(e):
                raise e
            raise Exception(f"Request failed: {str(e)}")

    def get_air_quality(self, lat: float, lon: float) -> Optional[AirQualityData]:
        """Get air quality data for coordinates."""
        cache_key = f"air_quality_{lat}_{lon}"

        # Check cache first with TTL validation
        if self._is_cache_valid_with_ttl(cache_key, "air_quality"):
            return AirQualityData.from_dict(self._cache[cache_key]["data"])

        try:
            self.logger.info(f"🌬️ Fetching air quality for {lat}, {lon}")

            data = self._make_request("data/2.5/air_pollution", {"lat": lat, "lon": lon})

            if not data or "list" not in data or not data["list"]:
                return None

            pollution_data = data["list"][0]
            components = pollution_data["components"]

            air_quality = AirQualityData(
                aqi=pollution_data["main"]["aqi"],
                co=components.get("co", 0),
                no=components.get("no", 0),
                no2=components.get("no2", 0),
                o3=components.get("o3", 0),
                so2=components.get("so2", 0),
                pm2_5=components.get("pm2_5", 0),
                pm10=components.get("pm10", 0),
                nh3=components.get("nh3", 0),
                timestamp=datetime.now(),
            )

            # Cache the result with TTL (30 minutes)
            self._cache[cache_key] = {
                "data": air_quality.to_dict(),
                "timestamp": datetime.now().isoformat(),
                "ttl": self._cache_ttl["air_quality"],
            }
            self._save_cache()

            self.logger.info(
                f"✅ Air quality data retrieved: AQI {
                    air_quality.aqi}"
            )
            return air_quality

        except Exception as e:
            # Handle specific air quality API errors more gracefully
            if "Location not found" in str(e) or "404" in str(e):
                self.logger.info(f"Air quality data not available for location: {lat}, {lon}")
            else:
                self.logger.warning(f"Air quality fetch failed: {e}")
            return None

    def get_astronomical_data(self, lat: float, lon: float) -> Optional[AstronomicalData]:
        """Get astronomical data for coordinates."""
        # This would typically use a separate astronomy API
        # For now, we'll simulate with basic sunrise/sunset from weather data
        try:
            data = self._make_request("weather", {"lat": lat, "lon": lon})

            if not data or "sys" not in data:
                return None

            sunrise = datetime.fromtimestamp(data["sys"]["sunrise"])
            sunset = datetime.fromtimestamp(data["sys"]["sunset"])
            day_length = sunset - sunrise

            # Simulate moon phase (in real app, use astronomy API)
            import random

            moon_phase = random.random()

            astronomical = AstronomicalData(
                sunrise=sunrise,
                sunset=sunset,
                moonrise=None,  # Would need astronomy API
                moonset=None,  # Would need astronomy API
                moon_phase=moon_phase,
                day_length=day_length,
            )

            return astronomical

        except Exception as e:
            self.logger.warning(f"Astronomical data fetch failed: {e}")
            return None

    def get_weather_alerts(self, lat: float, lon: float) -> List[WeatherAlert]:
        """Get weather alerts for coordinates."""
        try:
            # This would use the One Call API alerts endpoint
            # For now, return empty list as alerts require special API access
            return []

        except Exception as e:
            self.logger.warning(f"Weather alerts fetch failed: {e}")
            return []

    def get_enhanced_weather(self, location: str) -> EnhancedWeatherData:
        """Get enhanced weather data with all additional information."""
        # Validate and clean location input
        if not location or not isinstance(location, str):
            raise ValueError("Location must be a non-empty string")

        location = location.strip()
        if len(location) < 2:
            raise ValueError("Location must be at least 2 characters long")

        cache_key = f"enhanced_{location.lower()}"

        # Check cache first with TTL validation
        if self._is_cache_valid_with_ttl(cache_key, "current_weather"):
            cached_data = self._cache[cache_key]["data"]

            # Reconstruct enhanced weather data
            weather_dict = cached_data["weather"].copy()
            # Convert location dict back to Location object
            if isinstance(weather_dict["location"], dict):
                weather_dict["location"] = Location(**weather_dict["location"])
            # Convert condition string back to WeatherCondition enum
            if isinstance(weather_dict["condition"], str):
                # Handle both enum string representation and direct value
                condition_str = weather_dict["condition"]
                if condition_str.startswith("WeatherCondition."):
                    # Extract the enum name (e.g., 'CLEAR' from
                    # 'WeatherCondition.CLEAR')
                    enum_name = condition_str.split(".")[-1]
                    weather_dict["condition"] = getattr(WeatherCondition, enum_name)
                else:
                    # Direct enum value (e.g., 'clear')
                    weather_dict["condition"] = WeatherCondition(condition_str)
            # Convert timestamp string back to datetime
            if isinstance(weather_dict["timestamp"], str):
                weather_dict["timestamp"] = datetime.fromisoformat(weather_dict["timestamp"])

            weather_data = EnhancedWeatherData(**weather_dict)
            if cached_data.get("air_quality"):
                weather_data.air_quality = AirQualityData.from_dict(cached_data["air_quality"])
            if cached_data.get("astronomical"):
                weather_data.astronomical = AstronomicalData.from_dict(cached_data["astronomical"])
            if cached_data.get("alerts"):
                weather_data.alerts = [
                    WeatherAlert.from_dict(alert) for alert in cached_data["alerts"]
                ]

            return weather_data

        # Fetch basic weather data first
        self.logger.info(f"🌤️ Fetching enhanced weather for {location}")

        try:
            data = self._make_request("weather", {"q": location})
            if not data:
                raise WeatherServiceError("No weather data received")
        except RateLimitError as e:
            self.logger.warning(f"⏱️ Rate limited, waiting {e.retry_after} seconds")
            time.sleep(e.retry_after)
            # Try again after rate limit
            data = self._make_request("weather", {"q": location})
            if not data:
                raise WeatherServiceError("No weather data received after rate limit retry")
        except (NetworkError, ServiceUnavailableError) as e:
            # Try to get stale cache data
            stale_data = self._get_stale_cache_data(cache_key)
            if stale_data:
                self.logger.warning(f"🔄 Using stale cached data due to: {e}")
                # Reconstruct from stale cache
                weather_dict = stale_data["weather"].copy()
                if isinstance(weather_dict["location"], dict):
                    weather_dict["location"] = Location(**weather_dict["location"])
                if isinstance(weather_dict["condition"], str):
                    condition_str = weather_dict["condition"]
                    if condition_str.startswith("WeatherCondition."):
                        enum_name = condition_str.split(".")[-1]
                        weather_dict["condition"] = getattr(WeatherCondition, enum_name)
                    else:
                        weather_dict["condition"] = WeatherCondition(condition_str)
                if isinstance(weather_dict["timestamp"], str):
                    weather_dict["timestamp"] = datetime.fromisoformat(weather_dict["timestamp"])

                weather_data = EnhancedWeatherData(**weather_dict)
                if stale_data.get("air_quality"):
                    weather_data.air_quality = AirQualityData.from_dict(stale_data["air_quality"])
                if stale_data.get("astronomical"):
                    weather_data.astronomical = AstronomicalData.from_dict(
                        stale_data["astronomical"]
                    )
                if stale_data.get("alerts"):
                    weather_data.alerts = [
                        WeatherAlert.from_dict(alert) for alert in stale_data["alerts"]
                    ]
                return weather_data

            # If no stale data, use offline fallback
            fallback_data = self._get_offline_fallback("weather", location)
            if fallback_data:
                self.logger.warning(f"🔌 Using offline fallback data due to: {e}")
                # Create basic weather data from fallback
                location_obj = Location(
                    name=fallback_data.get("name", location),
                    country=fallback_data.get("sys", {}).get("country", "Unknown"),
                    latitude=fallback_data.get("coord", {}).get("lat", 0.0),
                    longitude=fallback_data.get("coord", {}).get("lon", 0.0),
                )
                return EnhancedWeatherData(
                    location=location_obj,
                    timestamp=datetime.now(),
                    condition=WeatherCondition.UNKNOWN,
                    description="Offline Mode - No Current Data",
                    temperature=fallback_data.get("main", {}).get("temp", 20.0),
                    feels_like=fallback_data.get("main", {}).get("feels_like", 20.0),
                    humidity=fallback_data.get("main", {}).get("humidity", 50),
                    pressure=fallback_data.get("main", {}).get("pressure", 1013),
                    raw_data=fallback_data,
                )
            raise  # Re-raise if no fallback available
        except APIKeyError:
            # API key errors should not be retried
            raise
        except Exception as e:
            # Wrap unexpected errors
            raise WeatherServiceError(f"Failed to fetch weather data: {str(e)}") from e

        # Parse basic weather data
        location_obj = Location(
            name=data["name"],
            country=data["sys"]["country"],
            latitude=data["coord"]["lat"],
            longitude=data["coord"]["lon"],
        )

        condition = WeatherCondition.from_openweather(
            data["weather"][0]["main"], data["weather"][0]["description"]
        )

        weather_data = EnhancedWeatherData(
            location=location_obj,
            timestamp=datetime.now(),
            condition=condition,
            description=data["weather"][0]["description"].title(),
            temperature=round(data["main"]["temp"], 1),
            feels_like=round(data["main"]["feels_like"], 1),
            humidity=data["main"]["humidity"],
            pressure=data["main"]["pressure"],
            visibility=data.get("visibility", 0) // 1000 if data.get("visibility") else None,
            wind_speed=round(data["wind"]["speed"], 1) if "wind" in data else None,
            wind_direction=data["wind"].get("deg", 0) if "wind" in data else None,
            cloudiness=data["clouds"]["all"] if "clouds" in data else None,
            raw_data=data,
        )

        # Get coordinates for additional data
        lat = data["coord"]["lat"]
        lon = data["coord"]["lon"]

        # Fetch additional data
        weather_data.air_quality = self.get_air_quality(lat, lon)
        weather_data.astronomical = self.get_astronomical_data(lat, lon)
        weather_data.alerts = self.get_weather_alerts(lat, lon)

        # Cache the complete result
        cache_data = {
            "weather": asdict(weather_data),
            "air_quality": weather_data.air_quality.to_dict() if weather_data.air_quality else None,
            "astronomical": (
                weather_data.astronomical.to_dict() if weather_data.astronomical else None
            ),
            "alerts": (
                [alert.to_dict() for alert in weather_data.alerts] if weather_data.alerts else []
            ),
        }

        # Cache with TTL for current weather (10 minutes)
        self._cache[cache_key] = {
            "data": cache_data,
            "timestamp": datetime.now().isoformat(),
            "ttl": self._cache_ttl["current_weather"],
        }
        self._save_cache()

        self.logger.info(f"✅ Enhanced weather data retrieved for {location}")
        
        # Debug logging as requested by user
        self.logger.info(f"DEBUG: get_weather({location}) returned: {weather_data.temperature}°C, {weather_data.description}")
        
        # Notify observers of new weather data
        self.notify_observers(weather_data)
        
        return weather_data

    def _get_wind_direction(self, degrees: float) -> str:
        """Convert wind direction degrees to compass direction."""
        if degrees is None:
            return "N"

        directions = [
            "N",
            "NNE",
            "NE",
            "ENE",
            "E",
            "ESE",
            "SE",
            "SSE",
            "S",
            "SSW",
            "SW",
            "WSW",
            "W",
            "WNW",
            "NW",
            "NNW",
        ]

        # Normalize degrees to 0-360 range
        degrees = degrees % 360

        # Calculate index (16 directions, so 360/16 = 22.5 degrees per
        # direction)
        index = round(degrees / 22.5) % 16

        return directions[index]

    def get_weather(self, location: str, use_cache: bool = True) -> EnhancedWeatherData:
        """Fetch weather data for specified location.
        
        Args:
            location: Location name to fetch weather for
            use_cache: Whether to use cached data if available
            
        Returns:
            EnhancedWeatherData object containing current conditions
            
        Raises:
            APIError: If weather API is unavailable
            ValueError: If location name is invalid
            NetworkError: If network connectivity issues occur
        """
        if not use_cache:
            # Clear cache for this location to force fresh data
            cache_key = f"enhanced_{location.lower()}"
            if cache_key in self._cache:
                del self._cache[cache_key]
        return self.get_enhanced_weather(location)

    def get_current_weather(self, location: str = None) -> Dict[str, Any]:
        """Get current weather data in dictionary format for compatibility.

        Args:
            location: Location to get weather for. If None, uses default location.

        Returns:
            Dictionary containing current weather data
        """
        if location is None:
            location = "London"  # Default location

        try:
            enhanced_data = self.get_enhanced_weather(location)
            self.logger.debug(
                f"Enhanced data type: {
                    type(enhanced_data)}, location type: {
                    type(
                        enhanced_data.location)}"
            )

            # Get forecast data
            forecast_data = self.get_forecast_data(location)

            # Convert to enhanced weather display format
            weather_dict = {
                "location": {
                    "name": enhanced_data.location.name,
                    "country": enhanced_data.location.country,
                },
                "current": {
                    "temp_c": enhanced_data.temperature,
                    "feelslike_c": enhanced_data.feels_like,
                    "humidity": enhanced_data.humidity,
                    "pressure_mb": enhanced_data.pressure,
                    "condition": {
                        "text": enhanced_data.description,
                        "code": enhanced_data.condition.value,
                    },
                    "wind_kph": (
                        enhanced_data.wind_speed * 3.6 if enhanced_data.wind_speed else 0
                    ),  # Convert m/s to km/h
                    "wind_dir": (
                        self._get_wind_direction(enhanced_data.wind_direction)
                        if enhanced_data.wind_direction
                        else "N"
                    ),
                    "vis_km": enhanced_data.visibility if enhanced_data.visibility else 0,
                    "cloud": enhanced_data.cloudiness if enhanced_data.cloudiness else 0,
                    "uv": 0,  # OpenWeatherMap doesn't provide UV in current weather
                },
                "timestamp": enhanced_data.timestamp.isoformat(),
                "air_quality": (
                    enhanced_data.air_quality.to_dict() if enhanced_data.air_quality else None
                ),
                "astronomical": (
                    enhanced_data.astronomical.to_dict() if enhanced_data.astronomical else None
                ),
            }

            # Add forecast data if available
            if forecast_data:
                weather_dict["forecast"] = forecast_data

            return weather_dict

        except Exception as e:
            self.logger.error(f"Failed to get current weather: {e}")
            # Return minimal fallback data
            return {
                "location": {"name": location, "country": ""},
                "current": {
                    "temp_c": 20.0,
                    "condition": {"text": "Weather data unavailable", "code": "unknown"},
                    "humidity": 0,
                    "pressure_mb": 0,
                    "wind_kph": 0,
                    "vis_km": 0,
                    "cloud": 0,
                },
                "timestamp": datetime.now().isoformat(),
            }

    def get_forecast_data(self, location: str) -> Optional[Dict[str, Any]]:
        """
        Get forecast data from OpenWeatherMap API.

        Args:
            location: Location to get forecast for

        Returns:
            Dictionary containing forecast data in OpenWeatherMap format
        """
        try:
            # Check cache first with TTL validation
            cache_key = f"forecast_{location.lower()}"
            if self._is_cache_valid_with_ttl(cache_key, "forecast"):
                return self._cache[cache_key]["data"]

            # Fetch forecast data from API
            self.logger.info(f"🌤️ Fetching forecast data for {location}")

            forecast_data = self._make_request("forecast", {"q": location})

            if forecast_data:
                # Cache the forecast data with TTL (1 hour)
                self._cache[cache_key] = {
                    "data": forecast_data,
                    "timestamp": datetime.now().isoformat(),
                    "ttl": self._cache_ttl["forecast"],
                }
                self._save_cache()

                return forecast_data
            else:
                self.logger.warning(f"No forecast data received for {location}")
                return None

        except Exception as e:
            self.logger.error(f"Failed to get forecast data for {location}: {e}")
            return None

    def get_forecast(self, location: str) -> ForecastData:
        """Get 5-day forecast data."""
        cache_key = f"forecast_{location.lower()}"

        # Check cache with TTL validation
        if self._is_cache_valid_with_ttl(cache_key, "forecast"):
            return ForecastData.from_openweather_forecast(self._cache[cache_key]["data"])

        try:
            # Fetch forecast data
            data = self._make_request("forecast", {"q": location})

            if not data:
                raise Exception("No forecast data received")

            # Cache the result with TTL (1 hour)
            self._cache[cache_key] = {
                "data": data,
                "timestamp": datetime.now().isoformat(),
                "ttl": self._cache_ttl["forecast"],
            }
            self._save_cache()

            return ForecastData.from_openweather_forecast(data)

        except Exception as e:
            self.logger.error(f"Forecast fetch failed: {e}")
            raise

    def clear_cache(self) -> None:
        """Clear enhanced weather cache."""
        self._cache.clear()
        if self._cache_file.exists():
            self._cache_file.unlink()
        self.logger.info("🗑️ Enhanced weather cache cleared")
