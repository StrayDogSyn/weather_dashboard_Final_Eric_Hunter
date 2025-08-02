"""Current Weather Data Models

Defines structured data classes for current weather information.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from ..location.location_models import Location
from .alert_models import WeatherAlert


def safe_divide(a, b, default=0):
    """Safely divide two numbers, returning default if division by zero."""
    try:
        return a / b if b != 0 else default
    except (TypeError, ZeroDivisionError):
        return default


class WeatherCondition(Enum):
    """Weather condition categories."""

    CLEAR = "clear"
    CLOUDS = "clouds"
    RAIN = "rain"
    DRIZZLE = "drizzle"
    THUNDERSTORM = "thunderstorm"
    SNOW = "snow"
    MIST = "mist"
    SMOKE = "smoke"
    HAZE = "haze"
    DUST = "dust"
    FOG = "fog"
    SAND = "sand"
    ASH = "ash"
    SQUALL = "squall"
    TORNADO = "tornado"
    UNKNOWN = "unknown"

    @classmethod
    def from_openweather(cls, main: str, description: str = "") -> "WeatherCondition":
        """Convert OpenWeather API main condition to enum."""
        condition_map = {
            "Clear": cls.CLEAR,
            "Clouds": cls.CLOUDS,
            "Rain": cls.RAIN,
            "Drizzle": cls.DRIZZLE,
            "Thunderstorm": cls.THUNDERSTORM,
            "Snow": cls.SNOW,
            "Mist": cls.MIST,
            "Smoke": cls.SMOKE,
            "Haze": cls.HAZE,
            "Dust": cls.DUST,
            "Fog": cls.FOG,
            "Sand": cls.SAND,
            "Ash": cls.ASH,
            "Squall": cls.SQUALL,
            "Tornado": cls.TORNADO,
        }
        return condition_map.get(main, cls.UNKNOWN)

    def get_icon(self) -> str:
        """Get weather icon character."""
        icon_map = {
            self.CLEAR: "☀",
            self.CLOUDS: "☁",
            self.RAIN: "🌧",
            self.DRIZZLE: "🌦",
            self.THUNDERSTORM: "⛈",
            self.SNOW: "❄",
            self.MIST: "🌫",
            self.SMOKE: "💨",
            self.HAZE: "🌫",
            self.DUST: "💨",
            self.FOG: "🌫",
            self.SAND: "💨",
            self.ASH: "💨",
            self.SQUALL: "💨",
            self.TORNADO: "🌪",
            self.UNKNOWN: "❓",
        }
        return icon_map.get(self, "❓")


@dataclass
class WeatherData:
    """Current weather data."""

    location: Location
    timestamp: datetime
    condition: WeatherCondition
    description: str
    temperature: float  # Celsius
    feels_like: float  # Celsius
    humidity: int  # Percentage
    pressure: float  # hPa
    visibility: Optional[float] = None  # km
    uv_index: Optional[float] = None
    wind_speed: Optional[float] = None  # m/s
    wind_direction: Optional[int] = None  # degrees
    wind_gust: Optional[float] = None  # m/s
    cloudiness: Optional[int] = None  # percentage
    sunrise: Optional[datetime] = None
    sunset: Optional[datetime] = None
    alerts: List[WeatherAlert] = field(default_factory=list)
    raw_data: Dict[str, Any] = field(default_factory=dict)

    @property
    def temperature_f(self) -> float:
        """Temperature in Fahrenheit."""
        return (self.temperature * 9 / 5) + 32

    @property
    def feels_like_f(self) -> float:
        """Feels like temperature in Fahrenheit."""
        return (self.feels_like * 9 / 5) + 32

    @property
    def wind_speed_kmh(self) -> Optional[float]:
        """Wind speed in km/h."""
        return self.wind_speed * 3.6 if self.wind_speed else None

    @property
    def wind_speed_mph(self) -> Optional[float]:
        """Wind speed in mph."""
        return self.wind_speed * 2.237 if self.wind_speed else None

    @property
    def wind_direction_text(self) -> str:
        """Wind direction as text (N, NE, E, etc.)."""
        if self.wind_direction is None:
            return "N/A"

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
        try:
            index = round(safe_divide(self.wind_direction, 22.5, 0)) % 16
            return directions[index]
        except (TypeError, ZeroDivisionError):
            return "N/A"

    @property
    def pressure_inhg(self) -> float:
        """Pressure in inches of mercury."""
        return self.pressure * 0.02953

    @property
    def visibility_miles(self) -> Optional[float]:
        """Visibility in miles."""
        return self.visibility * 0.621371 if self.visibility else None

    @property
    def is_day(self) -> bool:
        """Check if it's currently daytime."""
        if not self.sunrise or not self.sunset:
            return True  # Default to day if no sun data

        now = datetime.now()
        return self.sunrise <= now <= self.sunset

    @property
    def has_alerts(self) -> bool:
        """Check if there are active weather alerts."""
        return any(alert.is_active for alert in self.alerts)

    @property
    def active_alerts(self) -> List[WeatherAlert]:
        """Get list of active alerts."""
        return [alert for alert in self.alerts if alert.is_active]

    @classmethod
    def from_openweather(cls, data: Dict[str, Any]) -> "WeatherData":
        """Create WeatherData from OpenWeather API response."""
        weather = data.get("weather", [{}])[0]
        main = data.get("main", {})
        wind = data.get("wind", {})
        sys_data = data.get("sys", {})

        # Parse timestamps
        timestamp = datetime.fromtimestamp(data.get("dt", 0))
        sunrise = None
        sunset = None

        if sys_data.get("sunrise"):
            sunrise = datetime.fromtimestamp(sys_data["sunrise"])
        if sys_data.get("sunset"):
            sunset = datetime.fromtimestamp(sys_data["sunset"])

        return cls(
            location=Location.from_openweather(data),
            timestamp=timestamp,
            condition=WeatherCondition.from_openweather(
                weather.get("main", "Unknown"), weather.get("description", "")
            ),
            description=weather.get("description", "Unknown").title(),
            temperature=main.get("temp", 0.0),
            feels_like=main.get("feels_like", 0.0),
            humidity=main.get("humidity", 0),
            pressure=main.get("pressure", 0.0),
            visibility=(
                safe_divide(data.get("visibility"), 1000) if data.get("visibility") else None
            ),  # Convert m to km
            wind_speed=wind.get("speed"),
            wind_direction=wind.get("deg"),
            wind_gust=wind.get("gust"),
            cloudiness=data.get("clouds", {}).get("all"),
            sunrise=sunrise,
            sunset=sunset,
            raw_data=data,
        )
