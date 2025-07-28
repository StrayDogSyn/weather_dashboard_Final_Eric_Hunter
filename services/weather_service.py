"""Clean weather service with OpenWeatherMap integration."""

import requests
import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime

from config.settings import get_settings


class WeatherServiceError(Exception):
    """Custom exception for weather service errors."""
    pass


@dataclass
class WeatherData:
    """Weather data model."""
    location: str
    temperature: float
    feels_like: float
    humidity: int
    pressure: int
    description: str
    icon: str
    wind_speed: float
    wind_direction: int
    visibility: Optional[float] = None
    uv_index: Optional[float] = None
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


class WeatherService:
    """Simple, focused weather service using OpenWeatherMap API."""
    
    BASE_URL = "https://api.openweathermap.org/data/2.5"
    
    def __init__(self):
        self.settings = get_settings()
        self.session = requests.Session()
        self.session.timeout = 10  # 10 second timeout
        
        if not self.settings.openweather_api_key:
            raise WeatherServiceError("OpenWeatherMap API key not configured")
    
    def get_current_weather(self, city: str) -> Optional[WeatherData]:
        """Get current weather for a city.
        
        Args:
            city: City name (e.g., "London", "New York, US")
            
        Returns:
            WeatherData object or None if failed
        """
        try:
            url = f"{self.BASE_URL}/weather"
            params = {
                'q': city,
                'appid': self.settings.openweather_api_key,
                'units': 'metric'  # Celsius
            }
            
            response = self.session.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            return self._parse_weather_data(data)
            
        except requests.exceptions.RequestException as e:
            logging.error(f"Weather API request failed: {e}")
            raise WeatherServiceError(f"Failed to fetch weather data: {e}")
        except (KeyError, ValueError) as e:
            logging.error(f"Weather data parsing failed: {e}")
            raise WeatherServiceError(f"Invalid weather data received: {e}")
    
    def get_forecast(self, city: str, days: int = 5) -> Optional[list[WeatherData]]:
        """Get weather forecast for a city.
        
        Args:
            city: City name
            days: Number of days (1-5)
            
        Returns:
            List of WeatherData objects or None if failed
        """
        try:
            url = f"{self.BASE_URL}/forecast"
            params = {
                'q': city,
                'appid': self.settings.openweather_api_key,
                'units': 'metric',
                'cnt': min(days * 8, 40)  # 8 forecasts per day, max 40
            }
            
            response = self.session.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            return [self._parse_forecast_item(item, data['city']['name']) 
                   for item in data['list']]
            
        except requests.exceptions.RequestException as e:
            logging.error(f"Forecast API request failed: {e}")
            raise WeatherServiceError(f"Failed to fetch forecast data: {e}")
        except (KeyError, ValueError) as e:
            logging.error(f"Forecast data parsing failed: {e}")
            raise WeatherServiceError(f"Invalid forecast data received: {e}")
    
    def _parse_weather_data(self, data: Dict[str, Any]) -> WeatherData:
        """Parse OpenWeatherMap current weather response."""
        main = data['main']
        weather = data['weather'][0]
        wind = data.get('wind', {})
        
        return WeatherData(
            location=f"{data['name']}, {data['sys']['country']}",
            temperature=round(main['temp'], 1),
            feels_like=round(main['feels_like'], 1),
            humidity=main['humidity'],
            pressure=main['pressure'],
            description=weather['description'].title(),
            icon=weather['icon'],
            wind_speed=wind.get('speed', 0),
            wind_direction=wind.get('deg', 0),
            visibility=data.get('visibility', 0) / 1000 if 'visibility' in data else None,  # Convert to km
            timestamp=datetime.fromtimestamp(data['dt'])
        )
    
    def _parse_forecast_item(self, item: Dict[str, Any], city_name: str) -> WeatherData:
        """Parse OpenWeatherMap forecast item."""
        main = item['main']
        weather = item['weather'][0]
        wind = item.get('wind', {})
        
        return WeatherData(
            location=city_name,
            temperature=round(main['temp'], 1),
            feels_like=round(main['feels_like'], 1),
            humidity=main['humidity'],
            pressure=main['pressure'],
            description=weather['description'].title(),
            icon=weather['icon'],
            wind_speed=wind.get('speed', 0),
            wind_direction=wind.get('deg', 0),
            timestamp=datetime.fromtimestamp(item['dt'])
        )
    
    def get_weather(self, city: str) -> Optional[WeatherData]:
        """Get weather data for a city (alias for get_current_weather).
        
        Args:
            city: City name
            
        Returns:
            WeatherData object or None if failed
        """
        return self.get_current_weather(city)
    
    def test_connection(self) -> bool:
        """Test API connection with a simple request."""
        try:
            self.get_current_weather("London")
            return True
        except WeatherServiceError:
            return False
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.session.close()