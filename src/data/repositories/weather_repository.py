"""Weather Data Repository

Handles data access operations for weather information.
"""

import json
import sqlite3
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from ...models.location.location_models import Location
from ...models.weather.alert_models import WeatherAlert
from ...models.weather.current_weather import WeatherData
from ...models.weather.forecast_models import ForecastData
from .base_repository import BaseRepository


class WeatherRepository(BaseRepository[WeatherData, str]):
    """Repository for weather data with caching and persistence."""

    def __init__(self, db_path: str = "weather_cache.db"):
        super().__init__()
        self.db_path = db_path
        self._init_database()

    def _init_database(self):
        """Initialize SQLite database for weather caching."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS weather_cache (
                    location_key TEXT PRIMARY KEY,
                    weather_data TEXT NOT NULL,
                    cached_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP NOT NULL
                )
            """
            )

            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS forecast_cache (
                    location_key TEXT PRIMARY KEY,
                    forecast_data TEXT NOT NULL,
                    cached_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP NOT NULL
                )
            """
            )

            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS alert_cache (
                    location_key TEXT,
                    alert_id TEXT,
                    alert_data TEXT NOT NULL,
                    cached_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP NOT NULL,
                    PRIMARY KEY (location_key, alert_id)
                )
            """
            )

            conn.commit()

    def _get_location_key(self, location: Location) -> str:
        """Generate unique key for location."""
        return f"{location.latitude:.4f},{location.longitude:.4f}"

    async def get_by_id(self, location_key: str) -> Optional[WeatherData]:
        """Get cached weather data by location key."""
        # Check memory cache first
        cached = self._get_from_cache(location_key)
        if cached:
            return cached

        # Check database cache
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT weather_data FROM weather_cache WHERE location_key = ? AND expires_at > ?",
                (location_key, datetime.now().isoformat()),
            )
            row = cursor.fetchone()

            if row:
                weather_dict = json.loads(row[0])
                weather_data = self._dict_to_weather_data(weather_dict)
                self._set_cache(location_key, weather_data)
                return weather_data

        return None

    async def get_all(self, limit: Optional[int] = None, offset: int = 0) -> List[WeatherData]:
        """Get all cached weather data."""
        with sqlite3.connect(self.db_path) as conn:
            query = "SELECT weather_data FROM weather_cache WHERE expires_at > ? ORDER BY cached_at DESC"
            params = [datetime.now().isoformat()]

            if limit:
                query += " LIMIT ? OFFSET ?"
                params.extend([limit, offset])

            cursor = conn.execute(query, params)
            rows = cursor.fetchall()

            return [
                self._dict_to_weather_data(json.loads(row[0])) for row in rows
            ]

    async def create(self, entity: WeatherData) -> WeatherData:
        """Cache weather data."""
        location_key = self._get_location_key(entity.location)
        return await self.update(location_key, entity)

    async def update(self, location_key: str, entity: WeatherData) -> Optional[WeatherData]:
        """Update cached weather data."""
        expires_at = datetime.now() + timedelta(minutes=10)  # 10-minute cache
        weather_dict = self._weather_data_to_dict(entity)

        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT OR REPLACE INTO weather_cache (location_key, weather_data, "
                "expires_at) VALUES (?, ?, ?)",
                (location_key, json.dumps(weather_dict), expires_at.isoformat()),
            )
            conn.commit()

        # Update memory cache
        self._set_cache(location_key, entity, 600)  # 10 minutes
        return entity

    async def delete(self, location_key: str) -> bool:
        """Delete cached weather data."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "DELETE FROM weather_cache WHERE location_key = ?", (location_key,)
            )
            conn.commit()

            self._invalidate_cache(location_key)
            return cursor.rowcount > 0

    async def exists(self, location_key: str) -> bool:
        """Check if weather data exists in cache."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT 1 FROM weather_cache WHERE location_key = ? AND expires_at > ?",
                (location_key, datetime.now().isoformat()),
            )
            return cursor.fetchone() is not None

    async def get_weather_by_location(self, location: Location) -> Optional[WeatherData]:
        """Get weather data for specific location."""
        location_key = self._get_location_key(location)
        return await self.get_by_id(location_key)

    async def cache_weather(self, location: Location, weather_data: WeatherData) -> WeatherData:
        """Cache weather data for location."""
        location_key = self._get_location_key(location)
        return await self.update(location_key, weather_data)

    def _weather_data_to_dict(self, weather_data: WeatherData) -> Dict[str, Any]:
        """Convert WeatherData to dictionary for storage."""
        return {
            "temperature": weather_data.temperature,
            "feels_like": weather_data.feels_like,
            "humidity": weather_data.humidity,
            "pressure": weather_data.pressure,
            "wind_speed": weather_data.wind_speed,
            "wind_direction": weather_data.wind_direction,
            "visibility": weather_data.visibility,
            "uv_index": weather_data.uv_index,
            "condition": weather_data.condition.value if weather_data.condition else None,
            "description": weather_data.description,
            "icon": weather_data.icon,
            "sunrise": weather_data.sunrise.isoformat() if weather_data.sunrise else None,
            "sunset": weather_data.sunset.isoformat() if weather_data.sunset else None,
            "timestamp": weather_data.timestamp.isoformat(),
            "location": {
                "name": weather_data.location.name,
                "country": weather_data.location.country,
                "state": weather_data.location.state,
                "latitude": weather_data.location.latitude,
                "longitude": weather_data.location.longitude,
            },
            "alerts": [self._alert_to_dict(alert) for alert in weather_data.alerts],
        }

    def _dict_to_weather_data(self, data: Dict[str, Any]) -> WeatherData:
        """Convert dictionary to WeatherData object."""
        from ...models.weather.current_weather import WeatherCondition

        location_data = data["location"]
        location = Location(
            name=location_data["name"],
            country=location_data["country"],
            state=location_data.get("state"),
            latitude=location_data["latitude"],
            longitude=location_data["longitude"],
        )

        condition = None
        if data.get("condition"):
            try:
                condition = WeatherCondition(data["condition"])
            except ValueError:
                condition = WeatherCondition.UNKNOWN

        alerts = [self._dict_to_alert(alert_data) for alert_data in data.get("alerts", [])]

        return WeatherData(
            temperature=data["temperature"],
            feels_like=data["feels_like"],
            humidity=data["humidity"],
            pressure=data["pressure"],
            wind_speed=data["wind_speed"],
            wind_direction=data["wind_direction"],
            visibility=data["visibility"],
            uv_index=data["uv_index"],
            condition=condition,
            description=data["description"],
            icon=data["icon"],
            sunrise=datetime.fromisoformat(data["sunrise"]) if data.get("sunrise") else None,
            sunset=datetime.fromisoformat(data["sunset"]) if data.get("sunset") else None,
            timestamp=datetime.fromisoformat(data["timestamp"]),
            location=location,
            alerts=alerts,
        )

    def _alert_to_dict(self, alert: WeatherAlert) -> Dict[str, Any]:
        """Convert WeatherAlert to dictionary."""
        return {
            "title": alert.title,
            "description": alert.description,
            "severity": alert.severity,
            "start_time": alert.start_time.isoformat(),
            "end_time": alert.end_time.isoformat(),
            "source": alert.source,
            "areas": alert.areas,
        }

    def _dict_to_alert(self, data: Dict[str, Any]) -> WeatherAlert:
        """Convert dictionary to WeatherAlert."""
        return WeatherAlert(
            title=data["title"],
            description=data["description"],
            severity=data["severity"],
            start_time=datetime.fromisoformat(data["start_time"]),
            end_time=datetime.fromisoformat(data["end_time"]),
            source=data["source"],
            areas=data.get("areas", []),
        )

    async def cleanup_expired(self) -> int:
        """Remove expired cache entries."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "DELETE FROM weather_cache WHERE expires_at <= ?", (datetime.now().isoformat(),)
            )
            conn.commit()

            self._cleanup_expired_cache()
            return cursor.rowcount


class ForecastRepository(BaseRepository[ForecastData, str]):
    """Repository for weather forecast data."""

    def __init__(self, db_path: str = "weather_cache.db"):
        super().__init__()
        self.db_path = db_path

    def _get_location_key(self, location: Location) -> str:
        """Generate unique key for location."""
        return f"{location.latitude:.4f},{location.longitude:.4f}"

    async def get_by_id(self, location_key: str) -> Optional[ForecastData]:
        """Get cached forecast data by location key."""
        cached = self._get_from_cache(location_key)
        if cached:
            return cached

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT forecast_data FROM forecast_cache WHERE location_key = ? "
                "AND expires_at > ?",
                (location_key, datetime.now().isoformat()),
            )
            row = cursor.fetchone()

            if row:
                forecast_dict = json.loads(row[0])
                forecast_data = self._dict_to_forecast_data(forecast_dict)
                self._set_cache(location_key, forecast_data)
                return forecast_data

        return None

    async def get_all(self, limit: Optional[int] = None, offset: int = 0) -> List[ForecastData]:
        """Get all cached forecast data."""
        with sqlite3.connect(self.db_path) as conn:
            query = (
                "SELECT forecast_data FROM forecast_cache WHERE expires_at > ? "
                "ORDER BY cached_at DESC"
            )
            params = [datetime.now().isoformat()]

            if limit:
                query += " LIMIT ? OFFSET ?"
                params.extend([limit, offset])

            cursor = conn.execute(query, params)
            rows = cursor.fetchall()

            return [
                self._dict_to_forecast_data(json.loads(row[0])) for row in rows
            ]

    async def create(self, entity: ForecastData) -> ForecastData:
        """Cache forecast data."""
        location_key = self._get_location_key(entity.location)
        return await self.update(location_key, entity)

    async def update(self, location_key: str, entity: ForecastData) -> Optional[ForecastData]:
        """Update cached forecast data."""
        expires_at = datetime.now() + timedelta(hours=1)  # 1-hour cache
        forecast_dict = self._forecast_data_to_dict(entity)

        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT OR REPLACE INTO forecast_cache (location_key, forecast_data, "
                "expires_at) VALUES (?, ?, ?)",
                (location_key, json.dumps(forecast_dict), expires_at.isoformat()),
            )
            conn.commit()

        self._set_cache(location_key, entity, 3600)  # 1 hour
        return entity

    async def delete(self, location_key: str) -> bool:
        """Delete cached forecast data."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "DELETE FROM forecast_cache WHERE location_key = ?", (location_key,)
            )
            conn.commit()

            self._invalidate_cache(location_key)
            return cursor.rowcount > 0

    async def exists(self, location_key: str) -> bool:
        """Check if forecast data exists in cache."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT 1 FROM forecast_cache WHERE location_key = ? AND expires_at > ?",
                (location_key, datetime.now().isoformat()),
            )
            return cursor.fetchone() is not None

    async def get_forecast_by_location(self, location: Location) -> Optional[ForecastData]:
        """Get forecast data for specific location."""
        location_key = self._get_location_key(location)
        return await self.get_by_id(location_key)

    def _forecast_data_to_dict(self, forecast_data: ForecastData) -> Dict[str, Any]:
        """Convert ForecastData to dictionary for storage."""
        return {
            "location": {
                "name": forecast_data.location.name,
                "country": forecast_data.location.country,
                "state": forecast_data.location.state,
                "latitude": forecast_data.location.latitude,
                "longitude": forecast_data.location.longitude,
            },
            "hourly_forecasts": [
                {
                    "datetime": entry.datetime.isoformat(),
                    "temperature": entry.temperature,
                    "feels_like": entry.feels_like,
                    "humidity": entry.humidity,
                    "wind_speed": entry.wind_speed,
                    "wind_direction": entry.wind_direction,
                    "precipitation_probability": entry.precipitation_probability,
                    "condition": entry.condition.value if entry.condition else None,
                    "description": entry.description,
                    "icon": entry.icon,
                }
                for entry in forecast_data.hourly_forecasts
            ],
            "daily_forecasts": [
                {
                    "date": daily.date.isoformat(),
                    "high_temp": daily.high_temp,
                    "low_temp": daily.low_temp,
                    "condition": daily.condition.value if daily.condition else None,
                    "description": daily.description,
                    "icon": daily.icon,
                    "precipitation_probability": daily.precipitation_probability,
                    "wind_speed": daily.wind_speed,
                    "humidity": daily.humidity,
                }
                for daily in forecast_data.daily_forecasts
            ],
            "timestamp": forecast_data.timestamp.isoformat(),
        }

    def _dict_to_forecast_data(self, data: Dict[str, Any]) -> ForecastData:
        """Convert dictionary to ForecastData object."""
        from ...models.weather.current_weather import WeatherCondition
        from ...models.weather.forecast_models import DailyForecast, ForecastEntry

        location_data = data["location"]
        location = Location(
            name=location_data["name"],
            country=location_data["country"],
            state=location_data.get("state"),
            latitude=location_data["latitude"],
            longitude=location_data["longitude"],
        )

        hourly_forecasts = []
        for entry_data in data.get("hourly_forecasts", []):
            condition = None
            if entry_data.get("condition"):
                try:
                    condition = WeatherCondition(entry_data["condition"])
                except ValueError:
                    condition = WeatherCondition.UNKNOWN

            hourly_forecasts.append(
                ForecastEntry(
                    datetime=datetime.fromisoformat(entry_data["datetime"]),
                    temperature=entry_data["temperature"],
                    feels_like=entry_data["feels_like"],
                    humidity=entry_data["humidity"],
                    wind_speed=entry_data["wind_speed"],
                    wind_direction=entry_data["wind_direction"],
                    precipitation_probability=entry_data["precipitation_probability"],
                    condition=condition,
                    description=entry_data["description"],
                    icon=entry_data["icon"],
                )
            )

        daily_forecasts = []
        for daily_data in data.get("daily_forecasts", []):
            condition = None
            if daily_data.get("condition"):
                try:
                    condition = WeatherCondition(daily_data["condition"])
                except ValueError:
                    condition = WeatherCondition.UNKNOWN

            daily_forecasts.append(
                DailyForecast(
                    date=datetime.fromisoformat(daily_data["date"]).date(),
                    high_temp=daily_data["high_temp"],
                    low_temp=daily_data["low_temp"],
                    condition=condition,
                    description=daily_data["description"],
                    icon=daily_data["icon"],
                    precipitation_probability=daily_data["precipitation_probability"],
                    wind_speed=daily_data["wind_speed"],
                    humidity=daily_data["humidity"],
                )
            )

        return ForecastData(
            location=location,
            hourly_forecasts=hourly_forecasts,
            daily_forecasts=daily_forecasts,
            timestamp=datetime.fromisoformat(data["timestamp"]),
        )
