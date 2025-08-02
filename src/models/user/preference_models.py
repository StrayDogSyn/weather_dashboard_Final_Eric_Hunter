"""User Preference Data Models

Defines structured data classes for user preferences and settings.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class TemperatureUnit(Enum):
    """Temperature unit preferences."""

    CELSIUS = "celsius"
    FAHRENHEIT = "fahrenheit"
    KELVIN = "kelvin"


class WindSpeedUnit(Enum):
    """Wind speed unit preferences."""

    KMH = "kmh"  # kilometers per hour
    MPH = "mph"  # miles per hour
    MS = "ms"  # meters per second
    KNOTS = "knots"


class PressureUnit(Enum):
    """Pressure unit preferences."""

    HPA = "hpa"  # hectopascals
    INHG = "inhg"  # inches of mercury
    MMHG = "mmhg"  # millimeters of mercury
    MBAR = "mbar"  # millibars


class DistanceUnit(Enum):
    """Distance unit preferences."""

    METRIC = "metric"  # kilometers
    IMPERIAL = "imperial"  # miles


class TimeFormat(Enum):
    """Time format preferences."""

    TWELVE_HOUR = "12h"
    TWENTY_FOUR_HOUR = "24h"


class Theme(Enum):
    """UI theme preferences."""

    LIGHT = "light"
    DARK = "dark"
    AUTO = "auto"  # Follow system theme


@dataclass
class UnitPreferences:
    """User unit preferences for weather data display."""

    temperature: TemperatureUnit = TemperatureUnit.CELSIUS
    wind_speed: WindSpeedUnit = WindSpeedUnit.KMH
    pressure: PressureUnit = PressureUnit.HPA
    distance: DistanceUnit = DistanceUnit.METRIC
    time_format: TimeFormat = TimeFormat.TWELVE_HOUR

    def to_dict(self) -> Dict[str, str]:
        """Convert to dictionary for storage."""
        return {
            "temperature": self.temperature.value,
            "wind_speed": self.wind_speed.value,
            "pressure": self.pressure.value,
            "distance": self.distance.value,
            "time_format": self.time_format.value,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, str]) -> "UnitPreferences":
        """Create from dictionary."""
        return cls(
            temperature=TemperatureUnit(data.get("temperature", "celsius")),
            wind_speed=WindSpeedUnit(data.get("wind_speed", "kmh")),
            pressure=PressureUnit(data.get("pressure", "hpa")),
            distance=DistanceUnit(data.get("distance", "metric")),
            time_format=TimeFormat(data.get("time_format", "12h")),
        )


@dataclass
class NotificationPreferences:
    """User notification preferences."""

    enabled: bool = True
    severe_weather_alerts: bool = True
    daily_forecast: bool = False
    temperature_threshold_alerts: bool = False
    precipitation_alerts: bool = False
    wind_alerts: bool = False

    # Threshold values
    high_temp_threshold: Optional[float] = None
    low_temp_threshold: Optional[float] = None
    wind_speed_threshold: Optional[float] = None
    precipitation_threshold: Optional[float] = None

    # Timing preferences
    daily_forecast_time: str = "08:00"  # HH:MM format
    quiet_hours_start: str = "22:00"
    quiet_hours_end: str = "07:00"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "enabled": self.enabled,
            "severe_weather_alerts": self.severe_weather_alerts,
            "daily_forecast": self.daily_forecast,
            "temperature_threshold_alerts": self.temperature_threshold_alerts,
            "precipitation_alerts": self.precipitation_alerts,
            "wind_alerts": self.wind_alerts,
            "high_temp_threshold": self.high_temp_threshold,
            "low_temp_threshold": self.low_temp_threshold,
            "wind_speed_threshold": self.wind_speed_threshold,
            "precipitation_threshold": self.precipitation_threshold,
            "daily_forecast_time": self.daily_forecast_time,
            "quiet_hours_start": self.quiet_hours_start,
            "quiet_hours_end": self.quiet_hours_end,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "NotificationPreferences":
        """Create from dictionary."""
        return cls(
            enabled=data.get("enabled", True),
            severe_weather_alerts=data.get("severe_weather_alerts", True),
            daily_forecast=data.get("daily_forecast", False),
            temperature_threshold_alerts=data.get("temperature_threshold_alerts", False),
            precipitation_alerts=data.get("precipitation_alerts", False),
            wind_alerts=data.get("wind_alerts", False),
            high_temp_threshold=data.get("high_temp_threshold"),
            low_temp_threshold=data.get("low_temp_threshold"),
            wind_speed_threshold=data.get("wind_speed_threshold"),
            precipitation_threshold=data.get("precipitation_threshold"),
            daily_forecast_time=data.get("daily_forecast_time", "08:00"),
            quiet_hours_start=data.get("quiet_hours_start", "22:00"),
            quiet_hours_end=data.get("quiet_hours_end", "07:00"),
        )


@dataclass
class DisplayPreferences:
    """User display and UI preferences."""

    theme: Theme = Theme.AUTO
    show_feels_like: bool = True
    show_humidity: bool = True
    show_wind: bool = True
    show_pressure: bool = False
    show_uv_index: bool = True
    show_visibility: bool = False
    show_sunrise_sunset: bool = True

    # Forecast preferences
    default_forecast_days: int = 5
    show_hourly_forecast: bool = True
    hourly_forecast_hours: int = 24

    # Chart preferences
    show_temperature_chart: bool = True
    show_precipitation_chart: bool = True
    show_wind_chart: bool = False

    # Map preferences
    show_weather_map: bool = False
    default_map_layer: str = "temperature"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "theme": self.theme.value,
            "show_feels_like": self.show_feels_like,
            "show_humidity": self.show_humidity,
            "show_wind": self.show_wind,
            "show_pressure": self.show_pressure,
            "show_uv_index": self.show_uv_index,
            "show_visibility": self.show_visibility,
            "show_sunrise_sunset": self.show_sunrise_sunset,
            "default_forecast_days": self.default_forecast_days,
            "show_hourly_forecast": self.show_hourly_forecast,
            "hourly_forecast_hours": self.hourly_forecast_hours,
            "show_temperature_chart": self.show_temperature_chart,
            "show_precipitation_chart": self.show_precipitation_chart,
            "show_wind_chart": self.show_wind_chart,
            "show_weather_map": self.show_weather_map,
            "default_map_layer": self.default_map_layer,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DisplayPreferences":
        """Create from dictionary."""
        return cls(
            theme=Theme(data.get("theme", "auto")),
            show_feels_like=data.get("show_feels_like", True),
            show_humidity=data.get("show_humidity", True),
            show_wind=data.get("show_wind", True),
            show_pressure=data.get("show_pressure", False),
            show_uv_index=data.get("show_uv_index", True),
            show_visibility=data.get("show_visibility", False),
            show_sunrise_sunset=data.get("show_sunrise_sunset", True),
            default_forecast_days=data.get("default_forecast_days", 5),
            show_hourly_forecast=data.get("show_hourly_forecast", True),
            hourly_forecast_hours=data.get("hourly_forecast_hours", 24),
            show_temperature_chart=data.get("show_temperature_chart", True),
            show_precipitation_chart=data.get("show_precipitation_chart", True),
            show_wind_chart=data.get("show_wind_chart", False),
            show_weather_map=data.get("show_weather_map", False),
            default_map_layer=data.get("default_map_layer", "temperature"),
        )


@dataclass
class UserPreferences:
    """Complete user preferences container."""

    user_id: Optional[str] = None
    units: UnitPreferences = field(default_factory=UnitPreferences)
    notifications: NotificationPreferences = field(default_factory=NotificationPreferences)
    display: DisplayPreferences = field(default_factory=DisplayPreferences)

    # Favorite locations
    favorite_locations: List[str] = field(default_factory=list)  # Location names or IDs
    default_location: Optional[str] = None

    # Data preferences
    auto_refresh_interval: int = 300  # seconds
    cache_duration: int = 600  # seconds

    # Privacy preferences
    allow_location_tracking: bool = False
    share_usage_data: bool = False

    # Metadata
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    version: str = "1.0"

    def __post_init__(self):
        """Initialize timestamps if not provided."""
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = datetime.now()

    def update_timestamp(self):
        """Update the last modified timestamp."""
        self.updated_at = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "user_id": self.user_id,
            "units": self.units.to_dict(),
            "notifications": self.notifications.to_dict(),
            "display": self.display.to_dict(),
            "favorite_locations": self.favorite_locations,
            "default_location": self.default_location,
            "auto_refresh_interval": self.auto_refresh_interval,
            "cache_duration": self.cache_duration,
            "allow_location_tracking": self.allow_location_tracking,
            "share_usage_data": self.share_usage_data,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "version": self.version,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "UserPreferences":
        """Create from dictionary."""
        created_at = None
        updated_at = None

        if data.get("created_at"):
            created_at = datetime.fromisoformat(data["created_at"])
        if data.get("updated_at"):
            updated_at = datetime.fromisoformat(data["updated_at"])

        return cls(
            user_id=data.get("user_id"),
            units=UnitPreferences.from_dict(data.get("units", {})),
            notifications=NotificationPreferences.from_dict(data.get("notifications", {})),
            display=DisplayPreferences.from_dict(data.get("display", {})),
            favorite_locations=data.get("favorite_locations", []),
            default_location=data.get("default_location"),
            auto_refresh_interval=data.get("auto_refresh_interval", 300),
            cache_duration=data.get("cache_duration", 600),
            allow_location_tracking=data.get("allow_location_tracking", False),
            share_usage_data=data.get("share_usage_data", False),
            created_at=created_at,
            updated_at=updated_at,
            version=data.get("version", "1.0"),
        )
