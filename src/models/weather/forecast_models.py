"""Weather Forecast Data Models

Defines structured data classes for weather forecast information.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

from ..location.location_models import Location
from .current_weather import WeatherCondition


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