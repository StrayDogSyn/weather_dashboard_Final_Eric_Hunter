"""Weather Data Models

Defines structured data classes for weather information and forecasts.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


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
class Location:
    """Geographic location information."""

    name: str
    country: str
    state: Optional[str] = None
    latitude: float = 0.0
    longitude: float = 0.0
    timezone: Optional[str] = None

    def __str__(self) -> str:
        """String representation of location."""
        if self.state:
            return f"{self.name}, {self.state}, {self.country}"
        return f"{self.name}, {self.country}"

    @property
    def coordinates(self) -> tuple[float, float]:
        """Get coordinates as (lat, lon) tuple."""
        return (self.latitude, self.longitude)

    @classmethod
    def from_openweather(cls, data: Dict[str, Any]) -> "Location":
        """Create Location from OpenWeather API response."""
        coord = data.get("coord", {})
        sys_data = data.get("sys", {})

        return cls(
            name=data.get("name", "Unknown"),
            country=sys_data.get("country", "Unknown"),
            latitude=coord.get("lat", 0.0),
            longitude=coord.get("lon", 0.0),
        )


@dataclass
class LocationResult:
    """Enhanced location result for search and geocoding."""

    name: str
    display_name: str
    latitude: float
    longitude: float
    country: str = ""
    country_code: str = ""
    state: Optional[str] = None
    raw_address: str = ""

    def __str__(self) -> str:
        """String representation of location result."""
        return self.display_name

    @property
    def coordinates(self) -> tuple[float, float]:
        """Get coordinates as (lat, lon) tuple."""
        return (self.latitude, self.longitude)


@dataclass
class WeatherAlert:
    """Weather alert/warning information."""

    title: str
    description: str
    severity: str  # "minor", "moderate", "severe", "extreme"
    start_time: datetime
    end_time: datetime
    source: str = "Unknown"

    @property
    def is_active(self) -> bool:
        """Check if alert is currently active."""
        now = datetime.now()
        return self.start_time <= now <= self.end_time

    @property
    def severity_level(self) -> int:
        """Get numeric severity level (1-4)."""
        severity_map = {"minor": 1, "moderate": 2, "severe": 3, "extreme": 4}
        return severity_map.get(self.severity.lower(), 1)


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


@dataclass
class ForecastEntry:
    """Single forecast entry."""

    timestamp: datetime
    condition: WeatherCondition
    description: str
    temperature: float  # Celsius
    feels_like: float  # Celsius
    humidity: int  # Percentage
    pressure: float  # hPa
    wind_speed: Optional[float] = None  # m/s
    wind_direction: Optional[int] = None  # degrees
    cloudiness: Optional[int] = None  # percentage
    precipitation_probability: Optional[float] = None  # 0-1
    precipitation_amount: Optional[float] = None  # mm

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
    def precipitation_probability_percent(self) -> Optional[int]:
        """Precipitation probability as percentage."""
        return int(self.precipitation_probability * 100) if self.precipitation_probability else None


@dataclass
class DailyForecast:
    """Daily forecast summary."""

    date: datetime
    condition: WeatherCondition
    description: str
    temp_min: float  # Celsius
    temp_max: float  # Celsius
    humidity: int  # Percentage
    wind_speed: Optional[float] = None  # m/s
    precipitation_probability: Optional[float] = None  # 0-1
    precipitation_amount: Optional[float] = None  # mm

    @property
    def temp_min_f(self) -> float:
        """Minimum temperature in Fahrenheit."""
        return (self.temp_min * 9 / 5) + 32

    @property
    def temp_max_f(self) -> float:
        """Maximum temperature in Fahrenheit."""
        return (self.temp_max * 9 / 5) + 32

    @property
    def temp_range_c(self) -> str:
        """Temperature range in Celsius."""
        return f"{self.temp_min:.0f}°C - {self.temp_max:.0f}°C"

    @property
    def temp_range_f(self) -> str:
        """Temperature range in Fahrenheit."""
        return f"{self.temp_min_f:.0f}°F - {self.temp_max_f:.0f}°F"


@dataclass
class ForecastData:
    """Weather forecast data."""

    location: Location
    timestamp: datetime
    hourly_forecasts: List[ForecastEntry] = field(default_factory=list)
    daily_forecasts: List[DailyForecast] = field(default_factory=list)
    raw_data: Dict[str, Any] = field(default_factory=dict)

    @property
    def forecast_hours(self) -> int:
        """Number of hours in forecast."""
        return len(self.hourly_forecasts)

    @property
    def forecast_days(self) -> int:
        """Number of days in forecast."""
        return len(self.daily_forecasts)

    def get_hourly_forecast(self, hours: int = 24) -> List[ForecastEntry]:
        """Get forecast for next N hours."""
        return self.hourly_forecasts[:hours]

    def get_daily_forecast(self, days: int = 5) -> List[DailyForecast]:
        """Get forecast for next N days."""
        return self.daily_forecasts[:days]

    def get_temperature_range(self, hours: int = 24) -> tuple[float, float]:
        """Get temperature range for next N hours."""
        if not self.hourly_forecasts:
            return (0.0, 0.0)

        forecasts = self.get_hourly_forecast(hours)
        temps = [f.temperature for f in forecasts]
        return (min(temps), max(temps))

    @classmethod
    def from_openweather_forecast(cls, data: Dict[str, Any]) -> "ForecastData":
        """Create ForecastData from OpenWeather forecast API response."""
        city = data.get("city", {})
        forecast_list = data.get("list", [])

        # Create location from city data
        location = Location(
            name=city.get("name", "Unknown"),
            country=city.get("country", "Unknown"),
            latitude=city.get("coord", {}).get("lat", 0.0),
            longitude=city.get("coord", {}).get("lon", 0.0),
        )

        # Parse hourly forecasts
        hourly_forecasts = []
        for item in forecast_list:
            weather = item.get("weather", [{}])[0]
            main = item.get("main", {})
            wind = item.get("wind", {})

            forecast_entry = ForecastEntry(
                timestamp=datetime.fromtimestamp(item.get("dt", 0)),
                condition=WeatherCondition.from_openweather(weather.get("main", "Unknown")),
                description=weather.get("description", "Unknown").title(),
                temperature=main.get("temp", 0.0),
                feels_like=main.get("feels_like", 0.0),
                humidity=main.get("humidity", 0),
                pressure=main.get("pressure", 0.0),
                wind_speed=wind.get("speed"),
                wind_direction=wind.get("deg"),
                cloudiness=item.get("clouds", {}).get("all"),
                precipitation_probability=item.get("pop"),
            )
            hourly_forecasts.append(forecast_entry)

        return cls(
            location=location,
            timestamp=datetime.now(),
            hourly_forecasts=hourly_forecasts,
            raw_data=data,
        )