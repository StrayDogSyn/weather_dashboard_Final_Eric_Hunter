"""Weather Service Facade.

This module provides a unified interface for weather operations,
using the API clients and models to deliver weather data.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from pathlib import Path
import json

from .api_clients import (
    OpenWeatherAPIClient,
    WeatherAPIClient
)
from ..exceptions import (
    WeatherAppError,
    APIError,
    RateLimitError,
    NetworkError,
    AuthenticationError
)
from .models import (
    WeatherData,
    ForecastData,
    ForecastEntry,
    DailyForecast,
    WeatherAlert,
    Location,
    LocationResult,
    WeatherCondition
)
from .enhanced_weather_service import AirQualityData


class WeatherService:
    """Unified weather service facade.
    
    Provides a clean interface for weather operations using multiple API clients
    with fallback mechanisms and robust error handling.
    """
    
    def __init__(self, config_service, cache_manager=None):
        """Initialize weather service with configuration and optional cache manager."""
        self.config = config_service
        self.cache_manager = cache_manager
        self.logger = logging.getLogger("weather_dashboard.weather_service")
        
        # Initialize API clients
        self.openweather_client = OpenWeatherAPIClient(
            api_key=self.config.weather.api_key,
            cache_manager=cache_manager,
            logger=self.logger
        )
        
        # Initialize fallback client if available
        self.fallback_client = None
        if hasattr(self.config, 'weatherapi_key') and self.config.weatherapi_key:
            self.fallback_client = WeatherAPIClient(
                api_key=self.config.weatherapi_key,
                cache_manager=cache_manager,
                logger=self.logger
            )
        
        # Service state
        self._primary_client = self.openweather_client
        self._current_client = self._primary_client
        self._consecutive_failures = 0
        self._fallback_threshold = 3
        
        # Cache configuration
        self._cache = {}
        self._cache_file = Path.cwd() / "cache" / "weather_service_cache.json"
        self._load_cache()
        
        # Observer pattern for weather updates
        self._observers: List[Callable] = []
        
        self.logger.info("🌤️ Weather Service initialized")
    
    def _load_cache(self) -> None:
        """Load weather service cache from file."""
        try:
            if self._cache_file.exists():
                with open(self._cache_file, "r", encoding="utf-8") as f:
                    self._cache = json.load(f)
                self.logger.debug(f"📁 Loaded cache with {len(self._cache)} entries")
        except Exception as e:
            self.logger.warning(f"Failed to load cache: {e}")
            self._cache = {}
    
    def _save_cache(self) -> None:
        """Save weather service cache to file."""
        try:
            self._cache_file.parent.mkdir(exist_ok=True)
            with open(self._cache_file, "w", encoding="utf-8") as f:
                json.dump(self._cache, f, indent=2, default=str)
        except Exception as e:
            self.logger.warning(f"Failed to save cache: {e}")
    
    def add_observer(self, observer: Callable) -> None:
        """Add an observer for weather updates."""
        if observer not in self._observers:
            self._observers.append(observer)
            self.logger.debug(f"Added weather observer")
    
    def remove_observer(self, observer: Callable) -> None:
        """Remove an observer for weather updates."""
        if observer in self._observers:
            self._observers.remove(observer)
            self.logger.debug(f"Removed weather observer")
    
    def notify_observers(self, weather_data: Any) -> None:
        """Notify all observers of weather data updates."""
        for observer in self._observers:
            try:
                observer(weather_data)
            except Exception as e:
                self.logger.error(f"Error notifying observer: {e}")
    
    def _handle_api_failure(self, error: Exception) -> None:
        """Handle API failure and potentially switch to fallback client."""
        self._consecutive_failures += 1
        
        if (self._consecutive_failures >= self._fallback_threshold and 
            self.fallback_client and 
            self._current_client != self.fallback_client):
            
            self.logger.warning(f"🔄 Switching to fallback API after {self._consecutive_failures} failures")
            self._current_client = self.fallback_client
            self._consecutive_failures = 0
    
    def _handle_api_success(self) -> None:
        """Handle successful API response."""
        if self._consecutive_failures > 0:
            self.logger.info("✅ API recovered, resetting failure count")
        
        self._consecutive_failures = 0
        
        # Switch back to primary client if we were using fallback
        if self._current_client != self._primary_client:
            self.logger.info("🔄 Switching back to primary API")
            self._current_client = self._primary_client
    
    def get_current_weather(self, location: Location) -> Optional[WeatherData]:
        """Get current weather data for a location."""
        try:
            # Get raw weather data from API client
            raw_data = self._current_client.get_current_weather(location.latitude, location.longitude)
            
            if not raw_data:
                return None
            
            # Convert raw data to WeatherData model
            weather_data = self._convert_current_weather(raw_data, location)
            
            # Get air quality data if available
            try:
                air_quality_data = self._current_client.get_air_quality(location.latitude, location.longitude)
                if air_quality_data:
                    weather_data.air_quality = self._convert_air_quality(air_quality_data)
            except Exception as e:
                self.logger.warning(f"Failed to get air quality data: {e}")
            
            self._handle_api_success()
            self.notify_observers(weather_data)
            
            return weather_data
        
        except Exception as e:
            self.logger.error(f"Failed to get current weather: {e}")
            self._handle_api_failure(e)
            
            # Try fallback client if available
            if (self._current_client != self.fallback_client and 
                self.fallback_client):
                try:
                    return self.get_current_weather(location)
                except Exception as fallback_error:
                    self.logger.error(f"Fallback also failed: {fallback_error}")
            
            return None
    
    def get_forecast(self, location: Location, days: int = 5) -> Optional[ForecastData]:
        """Get weather forecast for a location."""
        try:
            # Get raw forecast data from API client
            raw_data = self._current_client.get_forecast(location.latitude, location.longitude)
            
            if not raw_data:
                return None
            
            # Convert raw data to ForecastData model
            forecast_data = self._convert_forecast(raw_data, location, days)
            
            self._handle_api_success()
            self.notify_observers(forecast_data)
            
            return forecast_data
        
        except Exception as e:
            self.logger.error(f"Failed to get forecast: {e}")
            self._handle_api_failure(e)
            
            # Try fallback client if available
            if (self._current_client != self.fallback_client and 
                self.fallback_client):
                try:
                    return self.get_forecast(location, days)
                except Exception as fallback_error:
                    self.logger.error(f"Fallback also failed: {fallback_error}")
            
            return None
    
    def search_locations(self, query: str, limit: int = 5) -> List[LocationResult]:
        """Search for locations by name."""
        try:
            # Use current API client to search locations
            search_results = self._current_client.search_locations(query, limit)
            
            # Convert to LocationResult objects
            locations = []
            for result in search_results:
                location = LocationResult(
                    name=result.name,
                    display_name=result.display,
                    latitude=result.lat or 0.0,
                    longitude=result.lon or 0.0,
                    country=result.country,
                    country_code=result.country[:2].upper() if result.country else "",
                    state=result.state or "",
                    raw_address=result.display
                )
                locations.append(location)
            
            self._handle_api_success()
            return locations
        
        except Exception as e:
            self.logger.error(f"Failed to search locations: {e}")
            self._handle_api_failure(e)
            
            # Try fallback client if available
            if (self._current_client != self.fallback_client and 
                self.fallback_client):
                try:
                    return self.search_locations(query, limit)
                except Exception as fallback_error:
                    self.logger.error(f"Fallback also failed: {fallback_error}")
            
            return []
    
    def search_by_zipcode(self, zipcode: str) -> Optional[LocationResult]:
        """Search for location by zipcode."""
        try:
            # Use current API client to search by zipcode
            result = self._current_client.search_by_zipcode(zipcode)
            
            if not result:
                return None
            
            # Convert to LocationResult
            location = LocationResult(
                name=result.name,
                display_name=result.display,
                latitude=result.lat or 0.0,
                longitude=result.lon or 0.0,
                country=result.country,
                country_code=result.country[:2].upper() if result.country else "",
                state=result.state or "",
                raw_address=result.display
            )
            
            self._handle_api_success()
            return location
        
        except Exception as e:
            self.logger.error(f"Failed to search by zipcode: {e}")
            self._handle_api_failure(e)
            
            # Try fallback client if available
            if (self._current_client != self.fallback_client and 
                self.fallback_client):
                try:
                    return self.search_by_zipcode(zipcode)
                except Exception as fallback_error:
                    self.logger.error(f"Fallback also failed: {fallback_error}")
            
            return None
    
    def reverse_geocode(self, latitude: float, longitude: float) -> Optional[LocationResult]:
        """Reverse geocode coordinates to location."""
        try:
            # Use current API client for reverse geocoding
            result = self._current_client.reverse_geocode(latitude, longitude)
            
            if not result:
                return None
            
            # Convert to LocationResult
            location = LocationResult(
                name=result.name,
                display_name=result.display,
                latitude=result.lat or latitude,
                longitude=result.lon or longitude,
                country=result.country,
                country_code=result.country[:2].upper() if result.country else "",
                state=result.state or "",
                raw_address=result.display
            )
            
            self._handle_api_success()
            return location
        
        except Exception as e:
            self.logger.error(f"Failed to reverse geocode: {e}")
            self._handle_api_failure(e)
            
            # Try fallback client if available
            if (self._current_client != self.fallback_client and 
                self.fallback_client):
                try:
                    return self.reverse_geocode(latitude, longitude)
                except Exception as fallback_error:
                    self.logger.error(f"Fallback also failed: {fallback_error}")
            
            return None
    
    def _convert_current_weather(self, raw_data: Dict, location: Location) -> WeatherData:
        """Convert raw API data to WeatherData model."""
        main = raw_data.get("main", {})
        weather = raw_data.get("weather", [{}])[0]
        wind = raw_data.get("wind", {})
        clouds = raw_data.get("clouds", {})
        sys = raw_data.get("sys", {})
        
        # Convert weather condition
        condition_id = weather.get("id", 800)
        condition = self._map_weather_condition(condition_id)
        
        # Create WeatherData object
        weather_data = WeatherData(
            location=location,
            temperature=main.get("temp", 0.0),
            feels_like=main.get("feels_like", 0.0),
            humidity=main.get("humidity", 0),
            pressure=main.get("pressure", 0.0),
            wind_speed=wind.get("speed", 0.0),
            wind_direction=wind.get("deg", 0),
            cloud_cover=clouds.get("all", 0),
            visibility=raw_data.get("visibility", 10000) / 1000,  # Convert to km
            uv_index=0.0,  # Not available in current weather endpoint
            condition=condition,
            description=weather.get("description", ""),
            icon=weather.get("icon", ""),
            timestamp=datetime.now(),
            sunrise=datetime.fromtimestamp(sys.get("sunrise", 0)) if sys.get("sunrise") else None,
            sunset=datetime.fromtimestamp(sys.get("sunset", 0)) if sys.get("sunset") else None
        )
        
        return weather_data
    
    def _convert_forecast(self, raw_data: Dict, location: Location, days: int) -> ForecastData:
        """Convert raw API forecast data to ForecastData model."""
        forecast_list = raw_data.get("list", [])
        
        # Group forecast entries by day
        daily_forecasts = {}
        hourly_entries = []
        
        for item in forecast_list[:days * 8]:  # 8 entries per day (3-hour intervals)
            dt = datetime.fromtimestamp(item.get("dt", 0))
            date_key = dt.date()
            
            # Create forecast entry
            main = item.get("main", {})
            weather = item.get("weather", [{}])[0]
            wind = item.get("wind", {})
            clouds = item.get("clouds", {})
            
            condition_id = weather.get("id", 800)
            condition = self._map_weather_condition(condition_id)
            
            entry = ForecastEntry(
                datetime=dt,
                temperature=main.get("temp", 0.0),
                feels_like=main.get("feels_like", 0.0),
                humidity=main.get("humidity", 0),
                pressure=main.get("pressure", 0.0),
                wind_speed=wind.get("speed", 0.0),
                wind_direction=wind.get("deg", 0),
                cloud_cover=clouds.get("all", 0),
                precipitation_probability=item.get("pop", 0.0) * 100,
                precipitation_amount=item.get("rain", {}).get("3h", 0.0),
                condition=condition,
                description=weather.get("description", ""),
                icon=weather.get("icon", "")
            )
            
            hourly_entries.append(entry)
            
            # Group by day for daily forecasts
            if date_key not in daily_forecasts:
                daily_forecasts[date_key] = []
            daily_forecasts[date_key].append(entry)
        
        # Create daily forecast summaries
        daily_forecast_list = []
        for date, entries in daily_forecasts.items():
            if entries:
                # Calculate daily aggregates
                temps = [e.temperature for e in entries]
                daily_forecast = DailyForecast(
                    date=date,
                    min_temperature=min(temps),
                    max_temperature=max(temps),
                    condition=entries[len(entries)//2].condition,  # Use midday condition
                    description=entries[len(entries)//2].description,
                    icon=entries[len(entries)//2].icon,
                    precipitation_probability=max(e.precipitation_probability for e in entries),
                    precipitation_amount=sum(e.precipitation_amount for e in entries),
                    wind_speed=sum(e.wind_speed for e in entries) / len(entries),
                    humidity=sum(e.humidity for e in entries) // len(entries)
                )
                daily_forecast_list.append(daily_forecast)
        
        return ForecastData(
            location=location,
            daily_forecasts=daily_forecast_list,
            hourly_forecasts=hourly_entries,
            timestamp=datetime.now()
        )
    
    def _convert_air_quality(self, raw_data: Dict) -> Optional[AirQualityData]:
        """Convert raw air quality data to AirQualityData model."""
        try:
            air_quality_list = raw_data.get("list", [])
            if not air_quality_list:
                return None
            
            aqi_data = air_quality_list[0]
            main = aqi_data.get("main", {})
            components = aqi_data.get("components", {})
            
            return AirQualityData(
                aqi=main.get("aqi", 1),
                co=components.get("co", 0.0),
                no=components.get("no", 0.0),
                no2=components.get("no2", 0.0),
                o3=components.get("o3", 0.0),
                so2=components.get("so2", 0.0),
                pm2_5=components.get("pm2_5", 0.0),
                pm10=components.get("pm10", 0.0),
                nh3=components.get("nh3", 0.0),
                timestamp=datetime.fromtimestamp(aqi_data.get("dt", 0))
            )
        
        except Exception as e:
            self.logger.error(f"Failed to convert air quality data: {e}")
            return None
    
    def _map_weather_condition(self, condition_id: int) -> WeatherCondition:
        """Map OpenWeather condition ID to WeatherCondition enum."""
        # Thunderstorm
        if 200 <= condition_id <= 232:
            return WeatherCondition.THUNDERSTORM
        # Drizzle
        elif 300 <= condition_id <= 321:
            return WeatherCondition.DRIZZLE
        # Rain
        elif 500 <= condition_id <= 531:
            return WeatherCondition.RAIN
        # Snow
        elif 600 <= condition_id <= 622:
            return WeatherCondition.SNOW
        # Atmosphere (mist, fog, etc.)
        elif 701 <= condition_id <= 781:
            return WeatherCondition.MIST
        # Clear
        elif condition_id == 800:
            return WeatherCondition.CLEAR
        # Clouds
        elif 801 <= condition_id <= 804:
            return WeatherCondition.CLOUDS
        else:
            return WeatherCondition.CLEAR
    
    def get_service_status(self) -> Dict[str, Any]:
        """Get current service status and health information."""
        return {
            "primary_client": "OpenWeatherMap",
            "current_client": "OpenWeatherMap" if self._current_client == self._primary_client else "WeatherAPI",
            "fallback_available": self.fallback_client is not None,
            "consecutive_failures": self._consecutive_failures,
            "cache_entries": len(self._cache),
            "observers": len(self._observers)
        }