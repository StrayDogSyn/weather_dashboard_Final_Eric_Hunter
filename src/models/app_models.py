"""Application Data Models

Defines data structures for application state, preferences, and caching.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Union
from enum import Enum
import json


class TemperatureUnit(Enum):
    """Temperature unit preferences."""
    CELSIUS = "celsius"
    FAHRENHEIT = "fahrenheit"
    
    def symbol(self) -> str:
        """Get unit symbol."""
        return "°C" if self == self.CELSIUS else "°F"


class WindSpeedUnit(Enum):
    """Wind speed unit preferences."""
    METERS_PER_SECOND = "m/s"
    KILOMETERS_PER_HOUR = "km/h"
    MILES_PER_HOUR = "mph"
    
    def symbol(self) -> str:
        """Get unit symbol."""
        symbols = {
            self.METERS_PER_SECOND: "m/s",
            self.KILOMETERS_PER_HOUR: "km/h",
            self.MILES_PER_HOUR: "mph"
        }
        return symbols[self]


class PressureUnit(Enum):
    """Pressure unit preferences."""
    HECTOPASCAL = "hPa"
    INCHES_MERCURY = "inHg"
    MILLIBARS = "mbar"
    
    def symbol(self) -> str:
        """Get unit symbol."""
        symbols = {
            self.HECTOPASCAL: "hPa",
            self.INCHES_MERCURY: "inHg",
            self.MILLIBARS: "mbar"
        }
        return symbols[self]


class ChartType(Enum):
    """Chart type options."""
    TEMPERATURE = "temperature"
    HUMIDITY = "humidity"
    WIND_SPEED = "wind_speed"
    PRESSURE = "pressure"
    PRECIPITATION = "precipitation"


class AppTheme(Enum):
    """Application theme options."""
    DATA_TERMINAL = "data_terminal"
    DARK = "dark"
    LIGHT = "light"
    AUTO = "auto"


@dataclass
class UserPreferences:
    """User preferences and settings."""
    temperature_unit: TemperatureUnit = TemperatureUnit.CELSIUS
    wind_speed_unit: WindSpeedUnit = WindSpeedUnit.METERS_PER_SECOND
    pressure_unit: PressureUnit = PressureUnit.HECTOPASCAL
    default_chart_type: ChartType = ChartType.TEMPERATURE
    theme: AppTheme = AppTheme.DATA_TERMINAL
    auto_refresh_enabled: bool = True
    auto_refresh_interval: int = 300  # seconds
    show_alerts: bool = True
    show_detailed_metrics: bool = True
    default_location: Optional[str] = None
    recent_locations: List[str] = field(default_factory=list)
    max_recent_locations: int = 10
    enable_animations: bool = True
    enable_sound_alerts: bool = False
    
    def add_recent_location(self, location: str) -> None:
        """Add location to recent searches."""
        # Remove if already exists
        if location in self.recent_locations:
            self.recent_locations.remove(location)
        
        # Add to beginning
        self.recent_locations.insert(0, location)
        
        # Trim to max size
        if len(self.recent_locations) > self.max_recent_locations:
            self.recent_locations = self.recent_locations[:self.max_recent_locations]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "temperature_unit": self.temperature_unit.value,
            "wind_speed_unit": self.wind_speed_unit.value,
            "pressure_unit": self.pressure_unit.value,
            "default_chart_type": self.default_chart_type.value,
            "theme": self.theme.value,
            "auto_refresh_enabled": self.auto_refresh_enabled,
            "auto_refresh_interval": self.auto_refresh_interval,
            "show_alerts": self.show_alerts,
            "show_detailed_metrics": self.show_detailed_metrics,
            "default_location": self.default_location,
            "recent_locations": self.recent_locations,
            "max_recent_locations": self.max_recent_locations,
            "enable_animations": self.enable_animations,
            "enable_sound_alerts": self.enable_sound_alerts
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UserPreferences':
        """Create from dictionary."""
        return cls(
            temperature_unit=TemperatureUnit(data.get("temperature_unit", "celsius")),
            wind_speed_unit=WindSpeedUnit(data.get("wind_speed_unit", "m/s")),
            pressure_unit=PressureUnit(data.get("pressure_unit", "hPa")),
            default_chart_type=ChartType(data.get("default_chart_type", "temperature")),
            theme=AppTheme(data.get("theme", "data_terminal")),
            auto_refresh_enabled=data.get("auto_refresh_enabled", True),
            auto_refresh_interval=data.get("auto_refresh_interval", 300),
            show_alerts=data.get("show_alerts", True),
            show_detailed_metrics=data.get("show_detailed_metrics", True),
            default_location=data.get("default_location"),
            recent_locations=data.get("recent_locations", []),
            max_recent_locations=data.get("max_recent_locations", 10),
            enable_animations=data.get("enable_animations", True),
            enable_sound_alerts=data.get("enable_sound_alerts", False)
        )


@dataclass
class CacheEntry:
    """Cache entry for API responses."""
    key: str
    data: Any
    timestamp: datetime
    ttl: timedelta  # Time to live
    access_count: int = 0
    last_accessed: Optional[datetime] = None
    
    def __post_init__(self):
        """Set initial access time."""
        if self.last_accessed is None:
            self.last_accessed = self.timestamp
    
    @property
    def is_expired(self) -> bool:
        """Check if cache entry has expired."""
        return datetime.now() > (self.timestamp + self.ttl)
    
    @property
    def age(self) -> timedelta:
        """Get age of cache entry."""
        return datetime.now() - self.timestamp
    
    @property
    def time_until_expiry(self) -> timedelta:
        """Get time until expiry."""
        expiry_time = self.timestamp + self.ttl
        return max(timedelta(0), expiry_time - datetime.now())
    
    def access(self) -> Any:
        """Access cached data and update statistics."""
        self.access_count += 1
        self.last_accessed = datetime.now()
        return self.data
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "key": self.key,
            "data": self.data,
            "timestamp": self.timestamp.isoformat(),
            "ttl_seconds": self.ttl.total_seconds(),
            "access_count": self.access_count,
            "last_accessed": self.last_accessed.isoformat() if self.last_accessed else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CacheEntry':
        """Create from dictionary."""
        return cls(
            key=data["key"],
            data=data["data"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            ttl=timedelta(seconds=data["ttl_seconds"]),
            access_count=data.get("access_count", 0),
            last_accessed=datetime.fromisoformat(data["last_accessed"]) if data.get("last_accessed") else None
        )


@dataclass
class APIResponse:
    """Standardized API response wrapper."""
    success: bool
    data: Optional[Any] = None
    error_message: Optional[str] = None
    error_code: Optional[str] = None
    status_code: Optional[int] = None
    timestamp: datetime = field(default_factory=datetime.now)
    response_time: Optional[float] = None  # seconds
    cached: bool = False
    
    @property
    def is_error(self) -> bool:
        """Check if response indicates an error."""
        return not self.success
    
    @property
    def has_data(self) -> bool:
        """Check if response has data."""
        return self.data is not None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "success": self.success,
            "data": self.data,
            "error_message": self.error_message,
            "error_code": self.error_code,
            "status_code": self.status_code,
            "timestamp": self.timestamp.isoformat(),
            "response_time": self.response_time,
            "cached": self.cached
        }
    
    @classmethod
    def success_response(cls, data: Any, response_time: Optional[float] = None, cached: bool = False) -> 'APIResponse':
        """Create successful response."""
        return cls(
            success=True,
            data=data,
            response_time=response_time,
            cached=cached
        )
    
    @classmethod
    def error_response(cls, error_message: str, error_code: Optional[str] = None, status_code: Optional[int] = None) -> 'APIResponse':
        """Create error response."""
        return cls(
            success=False,
            error_message=error_message,
            error_code=error_code,
            status_code=status_code
        )


@dataclass
class AppState:
    """Application state management."""
    current_location: Optional[str] = None
    current_weather_data: Optional[Any] = None  # WeatherData
    current_forecast_data: Optional[Any] = None  # ForecastData
    preferences: UserPreferences = field(default_factory=UserPreferences)
    is_loading: bool = False
    last_update: Optional[datetime] = None
    last_error: Optional[str] = None
    api_request_count: int = 0
    cache_hit_count: int = 0
    session_start_time: datetime = field(default_factory=datetime.now)
    
    @property
    def session_duration(self) -> timedelta:
        """Get current session duration."""
        return datetime.now() - self.session_start_time
    
    @property
    def cache_hit_rate(self) -> float:
        """Calculate cache hit rate."""
        total_requests = self.api_request_count + self.cache_hit_count
        if total_requests == 0:
            return 0.0
        return self.cache_hit_count / total_requests
    
    @property
    def has_weather_data(self) -> bool:
        """Check if current weather data is available."""
        return self.current_weather_data is not None
    
    @property
    def has_forecast_data(self) -> bool:
        """Check if forecast data is available."""
        return self.current_forecast_data is not None
    
    @property
    def time_since_last_update(self) -> Optional[timedelta]:
        """Get time since last update."""
        if self.last_update is None:
            return None
        return datetime.now() - self.last_update
    
    def increment_api_request(self) -> None:
        """Increment API request counter."""
        self.api_request_count += 1
    
    def increment_cache_hit(self) -> None:
        """Increment cache hit counter."""
        self.cache_hit_count += 1
    
    def set_loading(self, loading: bool) -> None:
        """Set loading state."""
        self.is_loading = loading
        if not loading:
            self.last_update = datetime.now()
    
    def set_error(self, error: Optional[str]) -> None:
        """Set error state."""
        self.last_error = error
        self.is_loading = False
    
    def clear_error(self) -> None:
        """Clear error state."""
        self.last_error = None
    
    def update_weather_data(self, weather_data: Any, forecast_data: Any = None) -> None:
        """Update weather and forecast data."""
        self.current_weather_data = weather_data
        if forecast_data is not None:
            self.current_forecast_data = forecast_data
        self.last_update = datetime.now()
        self.clear_error()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "current_location": self.current_location,
            "preferences": self.preferences.to_dict(),
            "is_loading": self.is_loading,
            "last_update": self.last_update.isoformat() if self.last_update else None,
            "last_error": self.last_error,
            "api_request_count": self.api_request_count,
            "cache_hit_count": self.cache_hit_count,
            "session_start_time": self.session_start_time.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AppState':
        """Create from dictionary."""
        preferences = UserPreferences.from_dict(data.get("preferences", {}))
        
        return cls(
            current_location=data.get("current_location"),
            preferences=preferences,
            is_loading=data.get("is_loading", False),
            last_update=datetime.fromisoformat(data["last_update"]) if data.get("last_update") else None,
            last_error=data.get("last_error"),
            api_request_count=data.get("api_request_count", 0),
            cache_hit_count=data.get("cache_hit_count", 0),
            session_start_time=datetime.fromisoformat(data.get("session_start_time", datetime.now().isoformat()))
        )


@dataclass
class ErrorInfo:
    """Detailed error information."""
    message: str
    error_type: str
    timestamp: datetime = field(default_factory=datetime.now)
    context: Dict[str, Any] = field(default_factory=dict)
    stack_trace: Optional[str] = None
    user_message: Optional[str] = None
    
    @property
    def age(self) -> timedelta:
        """Get error age."""
        return datetime.now() - self.timestamp
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "message": self.message,
            "error_type": self.error_type,
            "timestamp": self.timestamp.isoformat(),
            "context": self.context,
            "stack_trace": self.stack_trace,
            "user_message": self.user_message
        }
    
    @classmethod
    def from_exception(cls, exception: Exception, context: Optional[Dict[str, Any]] = None, user_message: Optional[str] = None) -> 'ErrorInfo':
        """Create from exception."""
        import traceback
        
        return cls(
            message=str(exception),
            error_type=type(exception).__name__,
            context=context or {},
            stack_trace=traceback.format_exc(),
            user_message=user_message
        )