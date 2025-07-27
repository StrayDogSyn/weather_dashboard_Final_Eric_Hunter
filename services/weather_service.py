"""Weather service for OpenWeatherMap API integration."""

import requests
import time
from dataclasses import dataclass
from typing import Optional, Dict, Any
from datetime import datetime, timedelta

from config.settings import settings


class WeatherServiceError(Exception):
    """Custom exception for weather service errors."""
    pass


class APIKeyError(WeatherServiceError):
    """Raised when API key is invalid or missing."""
    pass


class LocationNotFoundError(WeatherServiceError):
    """Raised when location cannot be found."""
    pass


@dataclass
class WeatherData:
    """Structured weather data object."""
    location: str
    temperature: float
    feels_like: float
    humidity: int
    pressure: int
    description: str
    icon: str
    wind_speed: float
    timestamp: datetime


class WeatherService:
    """OpenWeatherMap API service with caching."""
    
    BASE_URL = "https://api.openweathermap.org/data/2.5/weather"
    CACHE_DURATION = timedelta(minutes=10)
    
    def __init__(self):
        self.api_key = settings.openweather_api_key
        self._cache: Dict[str, tuple[WeatherData, datetime]] = {}
    
    def get_weather(self, location: str) -> WeatherData:
        """Get current weather data for a location."""
        
        # Check cache first
        cached_data = self._get_cached_data(location)
        if cached_data:
            return cached_data
        
        # Fetch from API
        weather_data = self._fetch_weather_data(location)
        
        # Cache the result
        self._cache[location.lower()] = (weather_data, datetime.now())
        
        return weather_data
    
    def _get_cached_data(self, location: str) -> Optional[WeatherData]:
        """Get cached weather data if still valid."""
        cache_key = location.lower()
        if cache_key in self._cache:
            data, timestamp = self._cache[cache_key]
            if datetime.now() - timestamp < self.CACHE_DURATION:
                return data
            else:
                # Remove expired cache entry
                del self._cache[cache_key]
        return None
    
    def _fetch_weather_data(self, location: str) -> WeatherData:
        """Fetch weather data from OpenWeatherMap API."""
        params = {
            'q': location,
            'appid': self.api_key,
            'units': 'metric'
        }
        
        try:
            response = requests.get(self.BASE_URL, params=params, timeout=10)
            response.raise_for_status()
            
        except requests.exceptions.Timeout:
            raise WeatherServiceError("Request timed out. Please try again.")
        except requests.exceptions.ConnectionError:
            raise WeatherServiceError("Unable to connect to weather service.")
        except requests.exceptions.HTTPError as e:
            if response.status_code == 401:
                raise APIKeyError("Invalid API key. Please check your configuration.")
            elif response.status_code == 404:
                raise LocationNotFoundError(f"Location '{location}' not found.")
            else:
                raise WeatherServiceError(f"API request failed: {e}")
        
        return self._parse_weather_response(response.json())
    
    def _parse_weather_response(self, data: Dict[str, Any]) -> WeatherData:
        """Parse API response into WeatherData object."""
        try:
            return WeatherData(
                location=f"{data['name']}, {data['sys']['country']}",
                temperature=round(data['main']['temp'], 1),
                feels_like=round(data['main']['feels_like'], 1),
                humidity=data['main']['humidity'],
                pressure=data['main']['pressure'],
                description=data['weather'][0]['description'].title(),
                icon=data['weather'][0]['icon'],
                wind_speed=round(data['wind'].get('speed', 0), 1),
                timestamp=datetime.now()
            )
        except KeyError as e:
            raise WeatherServiceError(f"Unexpected API response format: missing {e}")