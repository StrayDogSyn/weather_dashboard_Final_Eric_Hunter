"""Weather Service - OpenWeather API Integration

Handles weather data fetching, caching, and error management.
"""

import requests
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
import json
from pathlib import Path

from .config_service import ConfigService


@dataclass
class WeatherData:
    """Weather data model."""
    city: str
    country: str
    temperature: float
    feels_like: float
    humidity: int
    pressure: int
    visibility: int
    wind_speed: float
    wind_direction: int
    description: str
    icon: str
    timestamp: datetime
    
    # Additional metrics
    temp_min: float
    temp_max: float
    clouds: int
    uv_index: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'WeatherData':
        """Create from dictionary."""
        data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        return cls(**data)


@dataclass
class ForecastData:
    """Forecast data model."""
    date: datetime
    temp_min: float
    temp_max: float
    description: str
    icon: str
    humidity: int
    wind_speed: float
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        data = asdict(self)
        data['date'] = self.date.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ForecastData':
        """Create from dictionary."""
        data['date'] = datetime.fromisoformat(data['date'])
        return cls(**data)


class WeatherService:
    """Service for fetching weather data from OpenWeather API."""
    
    def __init__(self, config_service: ConfigService):
        """Initialize weather service."""
        self.config = config_service
        self.logger = logging.getLogger('weather_dashboard.weather_service')
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._cache_file = Path.cwd() / 'cache' / 'weather_cache.json'
        self._load_cache()
    
    def _load_cache(self) -> None:
        """Load weather cache from file."""
        try:
            if self._cache_file.exists():
                with open(self._cache_file, 'r', encoding='utf-8') as f:
                    self._cache = json.load(f)
                self.logger.debug(f"📁 Loaded cache with {len(self._cache)} entries")
        except Exception as e:
            self.logger.warning(f"Failed to load cache: {e}")
            self._cache = {}
    
    def _save_cache(self) -> None:
        """Save weather cache to file."""
        try:
            self._cache_file.parent.mkdir(exist_ok=True)
            
            # Create a serializable copy of the cache
            serializable_cache = {}
            for key, value in self._cache.items():
                serializable_cache[key] = {
                    'data': value['data'],  # Already converted by to_dict()
                    'timestamp': value['timestamp'] if isinstance(value['timestamp'], str) else value['timestamp'].isoformat()
                }
            
            with open(self._cache_file, 'w', encoding='utf-8') as f:
                json.dump(serializable_cache, f, indent=2)
            self.logger.debug("💾 Cache saved successfully")
        except Exception as e:
            self.logger.warning(f"Failed to save cache: {e}")
    
    def _is_cache_valid(self, cache_entry: Dict[str, Any]) -> bool:
        """Check if cache entry is still valid."""
        try:
            cached_time = datetime.fromisoformat(cache_entry['timestamp'])
            cache_duration = timedelta(seconds=self.config.app.cache_duration)
            return datetime.now() - cached_time < cache_duration
        except (KeyError, ValueError):
            return False
    
    def _make_request(self, endpoint: str, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Make API request with error handling."""
        try:
            # Add API key and default parameters
            params.update({
                'appid': self.config.weather.api_key,
                'units': self.config.weather.units
            })
            
            url = f"{self.config.weather.base_url}/{endpoint}"
            
            self.logger.debug(f"🌐 Making API request: {endpoint}")
            
            response = requests.get(
                url,
                params=params,
                timeout=self.config.weather.timeout
            )
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.Timeout:
            self.logger.error("⏰ API request timed out")
            raise Exception("Weather service timeout - please try again")
        
        except requests.exceptions.HTTPError as e:
            if response.status_code == 401:
                self.logger.error("🔑 Invalid API key")
                raise Exception("Invalid API key - please check your configuration")
            elif response.status_code == 404:
                self.logger.error("🏙️ City not found")
                raise Exception("City not found - please check the spelling")
            else:
                self.logger.error(f"🌐 HTTP error: {e}")
                raise Exception(f"Weather service error: {response.status_code}")
        
        except requests.exceptions.ConnectionError:
            self.logger.error("🌐 Connection error")
            raise Exception("No internet connection - please check your network")
        
        except Exception as e:
            self.logger.error(f"❌ Unexpected error: {e}")
            raise Exception(f"Weather service error: {str(e)}")
    
    def get_current_weather(self, city: str) -> WeatherData:
        """Get current weather for a city."""
        cache_key = f"current_{city.lower()}"
        
        # Check cache first
        if cache_key in self._cache and self._is_cache_valid(self._cache[cache_key]):
            self.logger.debug(f"📋 Using cached weather data for {city}")
            return WeatherData.from_dict(self._cache[cache_key]['data'])
        
        # Fetch from API
        self.logger.info(f"🌤️ Fetching current weather for {city}")
        
        data = self._make_request('weather', {'q': city})
        
        if not data:
            raise Exception("No weather data received")
        
        # Parse weather data
        weather_data = WeatherData(
            city=data['name'],
            country=data['sys']['country'],
            temperature=round(data['main']['temp'], 1),
            feels_like=round(data['main']['feels_like'], 1),
            humidity=data['main']['humidity'],
            pressure=data['main']['pressure'],
            visibility=data.get('visibility', 0) // 1000,  # Convert to km
            wind_speed=round(data['wind']['speed'], 1),
            wind_direction=data['wind'].get('deg', 0),
            description=data['weather'][0]['description'].title(),
            icon=data['weather'][0]['icon'],
            temp_min=round(data['main']['temp_min'], 1),
            temp_max=round(data['main']['temp_max'], 1),
            clouds=data['clouds']['all'],
            timestamp=datetime.now()
        )
        
        # Cache the result
        self._cache[cache_key] = {
            'data': weather_data.to_dict(),
            'timestamp': datetime.now().isoformat()
        }
        self._save_cache()
        
        self.logger.info(f"✅ Weather data retrieved for {city}: {weather_data.temperature}°C")
        return weather_data
    
    def get_forecast(self, city: str, days: int = 5) -> List[ForecastData]:
        """Get weather forecast for a city."""
        cache_key = f"forecast_{city.lower()}_{days}"
        
        # Check cache first
        if cache_key in self._cache and self._is_cache_valid(self._cache[cache_key]):
            self.logger.debug(f"📋 Using cached forecast data for {city}")
            cached_data = self._cache[cache_key]['data']
            return [ForecastData.from_dict(item) for item in cached_data]
        
        # Fetch from API
        self.logger.info(f"📅 Fetching {days}-day forecast for {city}")
        
        data = self._make_request('forecast', {'q': city, 'cnt': days * 8})  # 8 forecasts per day
        
        if not data or 'list' not in data:
            raise Exception("No forecast data received")
        
        # Parse forecast data (take one forecast per day at noon)
        forecast_list = []
        processed_dates = set()
        
        for item in data['list']:
            forecast_date = datetime.fromtimestamp(item['dt']).date()
            
            # Skip if we already have data for this date
            if forecast_date in processed_dates:
                continue
            
            forecast_data = ForecastData(
                date=datetime.fromtimestamp(item['dt']),
                temp_min=round(item['main']['temp_min'], 1),
                temp_max=round(item['main']['temp_max'], 1),
                description=item['weather'][0]['description'].title(),
                icon=item['weather'][0]['icon'],
                humidity=item['main']['humidity'],
                wind_speed=round(item['wind']['speed'], 1)
            )
            
            forecast_list.append(forecast_data)
            processed_dates.add(forecast_date)
            
            if len(forecast_list) >= days:
                break
        
        # Cache the result
        self._cache[cache_key] = {
            'data': [item.to_dict() for item in forecast_list],
            'timestamp': datetime.now().isoformat()
        }
        self._save_cache()
        
        self.logger.info(f"✅ Forecast data retrieved for {city}: {len(forecast_list)} days")
        return forecast_list
    
    def search_cities(self, query: str, limit: int = 5) -> List[Dict[str, str]]:
        """Search for cities matching the query."""
        try:
            self.logger.debug(f"🔍 Searching cities: {query}")
            
            data = self._make_request('find', {
                'q': query,
                'type': 'like',
                'cnt': limit
            })
            
            if not data or 'list' not in data:
                return []
            
            cities = []
            for item in data['list']:
                cities.append({
                    'name': item['name'],
                    'country': item['sys']['country'],
                    'display': f"{item['name']}, {item['sys']['country']}"
                })
            
            self.logger.debug(f"🏙️ Found {len(cities)} cities")
            return cities
            
        except Exception as e:
            self.logger.warning(f"City search failed: {e}")
            return []
    
    def clear_cache(self) -> None:
        """Clear weather cache."""
        self._cache.clear()
        if self._cache_file.exists():
            self._cache_file.unlink()
        self.logger.info("🗑️ Weather cache cleared")