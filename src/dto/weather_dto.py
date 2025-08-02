"""Weather Data Transfer Objects

DTOs for API response mapping and data transformation.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union


class WeatherProvider(Enum):
    """Weather data providers."""

    OPENWEATHER = "openweather"
    WEATHERAPI = "weatherapi"
    ACCUWEATHER = "accuweather"
    NOAA = "noaa"


@dataclass
class CoordinatesDTO:
    """Geographic coordinates DTO."""

    latitude: float
    longitude: float

    def to_dict(self) -> Dict[str, float]:
        return {"lat": self.latitude, "lon": self.longitude}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CoordinatesDTO":
        return cls(
            latitude=data.get("lat", data.get("latitude", 0.0)),
            longitude=data.get("lon", data.get("longitude", 0.0)),
        )


@dataclass
class LocationDTO:
    """Location information DTO."""

    name: str
    country: str
    state: Optional[str] = None
    coordinates: Optional[CoordinatesDTO] = None
    timezone: Optional[str] = None

    @classmethod
    def from_openweather(cls, data: Dict[str, Any]) -> "LocationDTO":
        """Create from OpenWeather API response."""
        coord_data = data.get("coord", {})
        coordinates = CoordinatesDTO.from_dict(coord_data) if coord_data else None

        return cls(
            name=data.get("name", ""),
            country=data.get("sys", {}).get("country", ""),
            state=data.get("state"),
            coordinates=coordinates,
            timezone=data.get("timezone"),
        )

    @classmethod
    def from_geocoding(cls, data: Dict[str, Any]) -> "LocationDTO":
        """Create from geocoding API response."""
        return cls(
            name=data.get("name", ""),
            country=data.get("country", ""),
            state=data.get("state"),
            coordinates=CoordinatesDTO(
                latitude=data.get("lat", 0.0), longitude=data.get("lon", 0.0)
            ),
        )


@dataclass
class WeatherConditionDTO:
    """Weather condition DTO."""

    id: int
    main: str
    description: str
    icon: str

    @classmethod
    def from_openweather(cls, data: Dict[str, Any]) -> "WeatherConditionDTO":
        """Create from OpenWeather weather condition."""
        return cls(
            id=data.get("id", 0),
            main=data.get("main", ""),
            description=data.get("description", ""),
            icon=data.get("icon", ""),
        )


@dataclass
class TemperatureDTO:
    """Temperature data DTO."""

    current: float
    feels_like: float
    min_temp: Optional[float] = None
    max_temp: Optional[float] = None

    @classmethod
    def from_openweather_current(cls, main_data: Dict[str, Any]) -> "TemperatureDTO":
        """Create from OpenWeather current weather main data."""
        return cls(
            current=main_data.get("temp", 0.0),
            feels_like=main_data.get("feels_like", 0.0),
            min_temp=main_data.get("temp_min"),
            max_temp=main_data.get("temp_max"),
        )

    @classmethod
    def from_openweather_forecast(cls, temp_data: Dict[str, Any]) -> "TemperatureDTO":
        """Create from OpenWeather forecast temperature data."""
        return cls(
            current=temp_data.get("temp", temp_data.get("day", 0.0)),
            feels_like=temp_data.get("feels_like", temp_data.get("day", 0.0)),
            min_temp=temp_data.get("min"),
            max_temp=temp_data.get("max"),
        )


@dataclass
class WindDTO:
    """Wind data DTO."""

    speed: float
    direction: Optional[float] = None
    gust: Optional[float] = None

    @classmethod
    def from_openweather(cls, wind_data: Dict[str, Any]) -> "WindDTO":
        """Create from OpenWeather wind data."""
        return cls(
            speed=wind_data.get("speed", 0.0),
            direction=wind_data.get("deg"),
            gust=wind_data.get("gust"),
        )


@dataclass
class AtmosphericDTO:
    """Atmospheric conditions DTO."""

    pressure: float
    humidity: int
    visibility: Optional[float] = None
    uv_index: Optional[float] = None

    @classmethod
    def from_openweather(
        cls, main_data: Dict[str, Any], visibility: Optional[float] = None
    ) -> "AtmosphericDTO":
        """Create from OpenWeather atmospheric data."""
        return cls(
            pressure=main_data.get("pressure", 0.0),
            humidity=main_data.get("humidity", 0),
            visibility=visibility,
            uv_index=main_data.get("uvi"),
        )


@dataclass
class PrecipitationDTO:
    """Precipitation data DTO."""

    rain_1h: Optional[float] = None
    rain_3h: Optional[float] = None
    snow_1h: Optional[float] = None
    snow_3h: Optional[float] = None
    probability: Optional[float] = None

    @classmethod
    def from_openweather(
        cls,
        rain_data: Optional[Dict[str, Any]] = None,
        snow_data: Optional[Dict[str, Any]] = None,
        pop: Optional[float] = None,
    ) -> "PrecipitationDTO":
        """Create from OpenWeather precipitation data."""
        return cls(
            rain_1h=rain_data.get("1h") if rain_data else None,
            rain_3h=rain_data.get("3h") if rain_data else None,
            snow_1h=snow_data.get("1h") if snow_data else None,
            snow_3h=snow_data.get("3h") if snow_data else None,
            probability=pop,
        )


@dataclass
class SunTimesDTO:
    """Sunrise/sunset times DTO."""

    sunrise: Optional[datetime] = None
    sunset: Optional[datetime] = None

    @classmethod
    def from_openweather(cls, sys_data: Dict[str, Any]) -> "SunTimesDTO":
        """Create from OpenWeather sys data."""
        sunrise = None
        sunset = None

        if "sunrise" in sys_data:
            sunrise = datetime.fromtimestamp(sys_data["sunrise"])
        if "sunset" in sys_data:
            sunset = datetime.fromtimestamp(sys_data["sunset"])

        return cls(sunrise=sunrise, sunset=sunset)


@dataclass
class CurrentWeatherDTO:
    """Current weather data DTO."""

    location: LocationDTO
    temperature: TemperatureDTO
    weather_condition: WeatherConditionDTO
    wind: WindDTO
    atmospheric: AtmosphericDTO
    precipitation: PrecipitationDTO
    sun_times: Optional[SunTimesDTO] = None
    timestamp: Optional[datetime] = None
    provider: WeatherProvider = WeatherProvider.OPENWEATHER

    @classmethod
    def from_openweather(cls, data: Dict[str, Any]) -> "CurrentWeatherDTO":
        """Create from OpenWeather current weather API response."""
        # Extract nested data
        main_data = data.get("main", {})
        weather_data = data.get("weather", [{}])[0]
        wind_data = data.get("wind", {})
        rain_data = data.get("rain")
        snow_data = data.get("snow")
        sys_data = data.get("sys", {})

        # Create DTOs
        location = LocationDTO.from_openweather(data)
        temperature = TemperatureDTO.from_openweather_current(main_data)
        weather_condition = WeatherConditionDTO.from_openweather(weather_data)
        wind = WindDTO.from_openweather(wind_data)
        atmospheric = AtmosphericDTO.from_openweather(main_data, data.get("visibility"))
        precipitation = PrecipitationDTO.from_openweather(rain_data, snow_data)
        sun_times = SunTimesDTO.from_openweather(sys_data)

        # Timestamp
        timestamp = None
        if "dt" in data:
            timestamp = datetime.fromtimestamp(data["dt"])

        return cls(
            location=location,
            temperature=temperature,
            weather_condition=weather_condition,
            wind=wind,
            atmospheric=atmospheric,
            precipitation=precipitation,
            sun_times=sun_times,
            timestamp=timestamp,
            provider=WeatherProvider.OPENWEATHER,
        )


@dataclass
class HourlyForecastDTO:
    """Hourly forecast entry DTO."""

    timestamp: datetime
    temperature: TemperatureDTO
    weather_condition: WeatherConditionDTO
    wind: WindDTO
    atmospheric: AtmosphericDTO
    precipitation: PrecipitationDTO

    @classmethod
    def from_openweather(cls, data: Dict[str, Any]) -> "HourlyForecastDTO":
        """Create from OpenWeather hourly forecast entry."""
        main_data = data.get("main", {})
        weather_data = data.get("weather", [{}])[0]
        wind_data = data.get("wind", {})
        rain_data = data.get("rain")
        snow_data = data.get("snow")

        return cls(
            timestamp=datetime.fromtimestamp(data.get("dt", 0)),
            temperature=TemperatureDTO.from_openweather_current(main_data),
            weather_condition=WeatherConditionDTO.from_openweather(weather_data),
            wind=WindDTO.from_openweather(wind_data),
            atmospheric=AtmosphericDTO.from_openweather(main_data, data.get("visibility")),
            precipitation=PrecipitationDTO.from_openweather(rain_data, snow_data, data.get("pop")),
        )


@dataclass
class DailyForecastDTO:
    """Daily forecast entry DTO."""

    date: datetime
    temperature: TemperatureDTO
    weather_condition: WeatherConditionDTO
    wind: WindDTO
    atmospheric: AtmosphericDTO
    precipitation: PrecipitationDTO
    sun_times: Optional[SunTimesDTO] = None

    @classmethod
    def from_openweather(cls, data: Dict[str, Any]) -> "DailyForecastDTO":
        """Create from OpenWeather daily forecast entry."""
        temp_data = data.get("temp", {})
        weather_data = data.get("weather", [{}])[0]
        wind_data = data.get("wind", {})

        # Create temperature DTO with daily values
        temperature = TemperatureDTO(
            current=temp_data.get("day", 0.0),
            feels_like=data.get("feels_like", {}).get("day", temp_data.get("day", 0.0)),
            min_temp=temp_data.get("min"),
            max_temp=temp_data.get("max"),
        )

        # Atmospheric data
        atmospheric = AtmosphericDTO(
            pressure=data.get("pressure", 0.0),
            humidity=data.get("humidity", 0),
            uv_index=data.get("uvi"),
        )

        # Sun times
        sun_times = SunTimesDTO(
            sunrise=datetime.fromtimestamp(data["sunrise"]) if "sunrise" in data else None,
            sunset=datetime.fromtimestamp(data["sunset"]) if "sunset" in data else None,
        )

        return cls(
            date=datetime.fromtimestamp(data.get("dt", 0)),
            temperature=temperature,
            weather_condition=WeatherConditionDTO.from_openweather(weather_data),
            wind=WindDTO.from_openweather(wind_data),
            atmospheric=atmospheric,
            precipitation=PrecipitationDTO.from_openweather(
                data.get("rain"), data.get("snow"), data.get("pop")
            ),
            sun_times=sun_times,
        )


@dataclass
class ForecastDTO:
    """Complete forecast data DTO."""

    location: LocationDTO
    hourly_forecasts: List[HourlyForecastDTO] = field(default_factory=list)
    daily_forecasts: List[DailyForecastDTO] = field(default_factory=list)
    provider: WeatherProvider = WeatherProvider.OPENWEATHER
    generated_at: Optional[datetime] = None

    @classmethod
    def from_openweather_5day(cls, data: Dict[str, Any]) -> "ForecastDTO":
        """Create from OpenWeather 5-day forecast API response."""
        city_data = data.get("city", {})
        location = LocationDTO.from_openweather(city_data)

        hourly_forecasts = []
        for forecast_item in data.get("list", []):
            hourly_forecasts.append(HourlyForecastDTO.from_openweather(forecast_item))

        return cls(
            location=location,
            hourly_forecasts=hourly_forecasts,
            provider=WeatherProvider.OPENWEATHER,
            generated_at=datetime.now(),
        )

    @classmethod
    def from_openweather_onecall(cls, data: Dict[str, Any]) -> "ForecastDTO":
        """Create from OpenWeather One Call API response."""
        # Create location from coordinates (One Call doesn't include city info)
        location = LocationDTO(
            name="",  # One Call API doesn't provide city name
            country="",
            coordinates=CoordinatesDTO(
                latitude=data.get("lat", 0.0), longitude=data.get("lon", 0.0)
            ),
            timezone=data.get("timezone"),
        )

        # Parse hourly forecasts
        hourly_forecasts = []
        for hourly_item in data.get("hourly", []):
            hourly_forecasts.append(HourlyForecastDTO.from_openweather(hourly_item))

        # Parse daily forecasts
        daily_forecasts = []
        for daily_item in data.get("daily", []):
            daily_forecasts.append(DailyForecastDTO.from_openweather(daily_item))

        return cls(
            location=location,
            hourly_forecasts=hourly_forecasts,
            daily_forecasts=daily_forecasts,
            provider=WeatherProvider.OPENWEATHER,
            generated_at=datetime.now(),
        )


@dataclass
class WeatherAlertDTO:
    """Weather alert DTO."""

    sender_name: str
    event: str
    start: datetime
    end: datetime
    description: str
    tags: List[str] = field(default_factory=list)

    @classmethod
    def from_openweather(cls, data: Dict[str, Any]) -> "WeatherAlertDTO":
        """Create from OpenWeather alert data."""
        return cls(
            sender_name=data.get("sender_name", ""),
            event=data.get("event", ""),
            start=datetime.fromtimestamp(data.get("start", 0)),
            end=datetime.fromtimestamp(data.get("end", 0)),
            description=data.get("description", ""),
            tags=data.get("tags", []),
        )


@dataclass
class WeatherResponseDTO:
    """Complete weather API response DTO."""

    current_weather: Optional[CurrentWeatherDTO] = None
    forecast: Optional[ForecastDTO] = None
    alerts: List[WeatherAlertDTO] = field(default_factory=list)
    provider: WeatherProvider = WeatherProvider.OPENWEATHER
    request_timestamp: datetime = field(default_factory=datetime.now)
    response_time_ms: Optional[float] = None

    @classmethod
    def from_openweather_current(
        cls, data: Dict[str, Any], response_time_ms: Optional[float] = None
    ) -> "WeatherResponseDTO":
        """Create from OpenWeather current weather response."""
        return cls(
            current_weather=CurrentWeatherDTO.from_openweather(data),
            provider=WeatherProvider.OPENWEATHER,
            response_time_ms=response_time_ms,
        )

    @classmethod
    def from_openweather_forecast(
        cls, data: Dict[str, Any], response_time_ms: Optional[float] = None
    ) -> "WeatherResponseDTO":
        """Create from OpenWeather forecast response."""
        return cls(
            forecast=ForecastDTO.from_openweather_5day(data),
            provider=WeatherProvider.OPENWEATHER,
            response_time_ms=response_time_ms,
        )

    @classmethod
    def from_openweather_onecall(
        cls, data: Dict[str, Any], response_time_ms: Optional[float] = None
    ) -> "WeatherResponseDTO":
        """Create from OpenWeather One Call API response."""
        current_weather = None
        if "current" in data:
            # Create a mock structure for current weather
            current_data = data["current"].copy()
            current_data.update(
                {
                    "coord": {"lat": data.get("lat", 0.0), "lon": data.get("lon", 0.0)},
                    "name": "",
                    "sys": {"country": ""},
                    "timezone": data.get("timezone"),
                }
            )
            current_weather = CurrentWeatherDTO.from_openweather(current_data)

        alerts = []
        for alert_data in data.get("alerts", []):
            alerts.append(WeatherAlertDTO.from_openweather(alert_data))

        return cls(
            current_weather=current_weather,
            forecast=ForecastDTO.from_openweather_onecall(data),
            alerts=alerts,
            provider=WeatherProvider.OPENWEATHER,
            response_time_ms=response_time_ms,
        )


@dataclass
class WeatherRequestDTO:
    """Weather API request DTO."""

    location: Union[str, CoordinatesDTO]
    include_forecast: bool = False
    include_alerts: bool = False
    forecast_days: int = 5
    units: str = "metric"  # metric, imperial, kelvin
    language: str = "en"
    provider: WeatherProvider = WeatherProvider.OPENWEATHER

    def to_openweather_params(self) -> Dict[str, Any]:
        """Convert to OpenWeather API parameters."""
        params = {"units": self.units, "lang": self.language}

        if isinstance(self.location, str):
            params["q"] = self.location
        elif isinstance(self.location, CoordinatesDTO):
            params["lat"] = self.location.latitude
            params["lon"] = self.location.longitude

        return params

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        location_data = self.location
        if isinstance(self.location, CoordinatesDTO):
            location_data = self.location.to_dict()

        return {
            "location": location_data,
            "include_forecast": self.include_forecast,
            "include_alerts": self.include_alerts,
            "forecast_days": self.forecast_days,
            "units": self.units,
            "language": self.language,
            "provider": self.provider.value,
        }
