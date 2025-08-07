"""Weather Forecast Data Models

Defines structured data classes for weather forecast information.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
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
        """Create ForecastData from OpenWeather forecast API response.

        Parses 40 3-hour forecast entries from API and groups by day using local timezone.
        Calculates daily high/low temperatures and determines predominant weather condition.
        """
        from collections import Counter, defaultdict

        import pytz

        city = data.get("city", {})
        forecast_list = data.get("list", [])

        # Get timezone info
        timezone_offset = city.get("timezone", 0)  # seconds from UTC

        # Create location from city data
        location = Location(
            name=city.get("name", "Unknown"),
            country=city.get("country", "Unknown"),
            latitude=city.get("coord", {}).get("lat", 0.0),
            longitude=city.get("coord", {}).get("lon", 0.0),
        )

        # Parse hourly forecasts (limit to 40 entries as per API)
        hourly_forecasts = []
        daily_data = defaultdict(
            lambda: {
                "temps": [],
                "conditions": [],
                "descriptions": [],
                "humidity": [],
                "wind_speeds": [],
                "wind_directions": [],
                "precipitation_probs": [],
                "precipitation_amounts": [],
                "entries": [],
            }
        )

        for item in forecast_list[:40]:  # Limit to 40 3-hour entries
            weather = item.get("weather", [{}])[0]
            main = item.get("main", {})
            wind = item.get("wind", {})

            # Convert timestamp to local time using timezone offset
            utc_timestamp = datetime.fromtimestamp(item.get("dt", 0), tz=pytz.UTC)
            local_timestamp = utc_timestamp + timedelta(seconds=timezone_offset)

            forecast_entry = ForecastEntry(
                timestamp=local_timestamp,
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
                precipitation_amount=item.get("rain", {}).get("3h", 0)
                + item.get("snow", {}).get("3h", 0),
            )
            hourly_forecasts.append(forecast_entry)

            # Group by day for daily forecasts
            day_key = local_timestamp.date()
            daily_data[day_key]["temps"].append(main.get("temp", 0.0))
            daily_data[day_key]["conditions"].append(weather.get("main", "Unknown"))
            daily_data[day_key]["descriptions"].append(weather.get("description", "Unknown"))
            daily_data[day_key]["humidity"].append(main.get("humidity", 0))
            daily_data[day_key]["wind_speeds"].append(wind.get("speed", 0))
            daily_data[day_key]["wind_directions"].append(wind.get("deg", 0))
            daily_data[day_key]["precipitation_probs"].append(item.get("pop", 0))
            daily_data[day_key]["precipitation_amounts"].append(
                item.get("rain", {}).get("3h", 0) + item.get("snow", {}).get("3h", 0)
            )
            daily_data[day_key]["entries"].append(forecast_entry)

        # Create daily forecasts
        daily_forecasts = []
        for day_date in sorted(daily_data.keys())[:5]:  # Limit to 5 days
            day_info = daily_data[day_date]

            # Calculate daily statistics
            temps = day_info["temps"]
            temp_min = min(temps) if temps else 0.0
            temp_max = max(temps) if temps else 0.0

            # Determine predominant weather condition
            condition_counts = Counter(day_info["conditions"])
            predominant_condition = (
                condition_counts.most_common(1)[0][0] if condition_counts else "Unknown"
            )

            # Get most common description
            description_counts = Counter(day_info["descriptions"])
            predominant_description = (
                description_counts.most_common(1)[0][0] if description_counts else "Unknown"
            )

            # Calculate averages
            avg_humidity = (
                sum(day_info["humidity"]) / len(day_info["humidity"]) if day_info["humidity"] else 0
            )
            avg_wind_speed = (
                sum(day_info["wind_speeds"]) / len(day_info["wind_speeds"])
                if day_info["wind_speeds"]
                else 0
            )
            max_precipitation_prob = (
                max(day_info["precipitation_probs"]) if day_info["precipitation_probs"] else 0
            )
            total_precipitation = (
                sum(day_info["precipitation_amounts"]) if day_info["precipitation_amounts"] else 0
            )

            daily_forecast = DailyForecast(
                date=datetime.combine(day_date, datetime.min.time()),
                condition=WeatherCondition.from_openweather(predominant_condition),
                description=predominant_description.title(),
                temp_min=temp_min,
                temp_max=temp_max,
                humidity=int(avg_humidity),
                wind_speed=avg_wind_speed,
                precipitation_probability=max_precipitation_prob,
                precipitation_amount=total_precipitation,
            )
            daily_forecasts.append(daily_forecast)

        return cls(
            location=location,
            timestamp=datetime.now(),
            hourly_forecasts=hourly_forecasts,
            daily_forecasts=daily_forecasts,
            raw_data=data,
        )
