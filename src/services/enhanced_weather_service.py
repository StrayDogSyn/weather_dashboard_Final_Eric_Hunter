"""Enhanced Weather Service - Extended API Integration

Handles weather data, air quality, astronomical data, and advanced search.
"""

import requests
import logging
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
import json
from pathlib import Path
import asyncio
import aiohttp

from .config_service import ConfigService
from models.weather_models import WeatherData, ForecastData, Location, WeatherCondition


@dataclass
class AirQualityData:
    """Air quality data model."""
    aqi: int  # Air Quality Index (1-5)
    co: float  # Carbon monoxide
    no: float  # Nitric oxide
    no2: float  # Nitrogen dioxide
    o3: float  # Ozone
    so2: float  # Sulphur dioxide
    pm2_5: float  # PM2.5
    pm10: float  # PM10
    nh3: float  # Ammonia
    timestamp: datetime
    
    def get_aqi_description(self) -> str:
        """Get AQI description."""
        descriptions = {
            1: "Good",
            2: "Fair", 
            3: "Moderate",
            4: "Poor",
            5: "Very Poor"
        }
        return descriptions.get(self.aqi, "Unknown")
    
    def get_health_recommendation(self) -> str:
        """Get health recommendation based on AQI."""
        recommendations = {
            1: "Air quality is satisfactory for most people.",
            2: "Unusually sensitive people should consider reducing outdoor activities.",
            3: "Sensitive groups should reduce outdoor activities.",
            4: "Everyone should reduce outdoor activities.",
            5: "Everyone should avoid outdoor activities."
        }
        return recommendations.get(self.aqi, "No recommendation available.")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AirQualityData':
        """Create from dictionary."""
        data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        return cls(**data)


@dataclass
class AstronomicalData:
    """Astronomical data model."""
    sunrise: datetime
    sunset: datetime
    moonrise: Optional[datetime]
    moonset: Optional[datetime]
    moon_phase: float  # 0-1 (0 = new moon, 0.5 = full moon)
    day_length: timedelta
    
    def get_moon_phase_name(self) -> str:
        """Get moon phase name."""
        if self.moon_phase < 0.125:
            return "New Moon"
        elif self.moon_phase < 0.375:
            return "Waxing Crescent"
        elif self.moon_phase < 0.625:
            return "Full Moon"
        elif self.moon_phase < 0.875:
            return "Waning Crescent"
        else:
            return "New Moon"
    
    def get_moon_phase_emoji(self) -> str:
        """Get moon phase emoji."""
        if self.moon_phase < 0.125:
            return "🌑"
        elif self.moon_phase < 0.375:
            return "🌒"
        elif self.moon_phase < 0.625:
            return "🌕"
        elif self.moon_phase < 0.875:
            return "🌘"
        else:
            return "🌑"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        data = asdict(self)
        data['sunrise'] = self.sunrise.isoformat()
        data['sunset'] = self.sunset.isoformat()
        data['moonrise'] = self.moonrise.isoformat() if self.moonrise else None
        data['moonset'] = self.moonset.isoformat() if self.moonset else None
        data['day_length'] = self.day_length.total_seconds()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AstronomicalData':
        """Create from dictionary."""
        data['sunrise'] = datetime.fromisoformat(data['sunrise'])
        data['sunset'] = datetime.fromisoformat(data['sunset'])
        data['moonrise'] = datetime.fromisoformat(data['moonrise']) if data['moonrise'] else None
        data['moonset'] = datetime.fromisoformat(data['moonset']) if data['moonset'] else None
        data['day_length'] = timedelta(seconds=data['day_length'])
        return cls(**data)


@dataclass
class WeatherAlert:
    """Weather alert data model."""
    event: str
    description: str
    severity: str  # minor, moderate, severe, extreme
    start_time: datetime
    end_time: datetime
    areas: List[str]
    
    def get_severity_color(self) -> str:
        """Get color for severity level."""
        colors = {
            'minor': '#FFEB3B',
            'moderate': '#FF9800', 
            'severe': '#F44336',
            'extreme': '#9C27B0'
        }
        return colors.get(self.severity.lower(), '#757575')
    
    def get_severity_emoji(self) -> str:
        """Get emoji for severity level."""
        emojis = {
            'minor': '⚠️',
            'moderate': '🟡',
            'severe': '🔴', 
            'extreme': '🟣'
        }
        return emojis.get(self.severity.lower(), '⚠️')
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        data = asdict(self)
        data['start_time'] = self.start_time.isoformat()
        data['end_time'] = self.end_time.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'WeatherAlert':
        """Create from dictionary."""
        data['start_time'] = datetime.fromisoformat(data['start_time'])
        data['end_time'] = datetime.fromisoformat(data['end_time'])
        return cls(**data)


@dataclass
class EnhancedWeatherData(WeatherData):
    """Enhanced weather data with additional information."""
    air_quality: Optional[AirQualityData] = None
    astronomical: Optional[AstronomicalData] = None
    alerts: List[WeatherAlert] = None
    
    def __post_init__(self):
        if self.alerts is None:
            self.alerts = []


class LocationSearchResult:
    """Location search result with enhanced information."""
    
    def __init__(self, name: str, country: str, state: str = None, 
                 lat: float = None, lon: float = None, **kwargs):
        self.name = name
        self.country = country
        self.state = state
        self.lat = lat
        self.lon = lon
        self.display = self._create_display_name()
    
    def _create_display_name(self) -> str:
        """Create display name for location."""
        parts = [self.name]
        if self.state:
            parts.append(self.state)
        parts.append(self.country)
        return ", ".join(parts)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'name': self.name,
            'country': self.country,
            'state': self.state,
            'lat': self.lat,
            'lon': self.lon,
            'display': self.display
        }


class EnhancedWeatherService:
    """Enhanced weather service with extended capabilities."""
    
    def __init__(self, config_service: ConfigService):
        """Initialize enhanced weather service."""
        self.config = config_service
        self.logger = logging.getLogger('weather_dashboard.enhanced_weather_service')
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._cache_file = Path.cwd() / 'cache' / 'enhanced_weather_cache.json'
        self._load_cache()
        
        # Rate limiting
        self._last_request_time = 0
        self._min_request_interval = 1.0  # Minimum seconds between requests
        
        # API endpoints
        self.base_url = self.config.weather.base_url
        self.api_key = self.config.weather.api_key
    
    def _load_cache(self) -> None:
        """Load enhanced weather cache from file."""
        try:
            if self._cache_file.exists():
                with open(self._cache_file, 'r', encoding='utf-8') as f:
                    self._cache = json.load(f)
                self.logger.debug(f"📁 Loaded enhanced cache with {len(self._cache)} entries")
        except Exception as e:
            self.logger.warning(f"Failed to load enhanced cache: {e}")
            self._cache = {}
    
    def _save_cache(self) -> None:
        """Save enhanced weather cache to file."""
        try:
            self._cache_file.parent.mkdir(exist_ok=True)
            with open(self._cache_file, 'w', encoding='utf-8') as f:
                json.dump(self._cache, f, indent=2, default=str)
            self.logger.debug("💾 Enhanced cache saved successfully")
        except Exception as e:
            self.logger.warning(f"Failed to save enhanced cache: {e}")
    
    def _is_cache_valid(self, cache_entry: Dict[str, Any], cache_duration: int = None) -> bool:
        """Check if cache entry is still valid."""
        try:
            cached_time = datetime.fromisoformat(cache_entry['timestamp'])
            duration = cache_duration or self.config.app.cache_duration
            cache_duration_delta = timedelta(seconds=duration)
            return datetime.now() - cached_time < cache_duration_delta
        except (KeyError, ValueError):
            return False
    
    def _rate_limit(self) -> None:
        """Implement rate limiting."""
        current_time = datetime.now().timestamp()
        time_since_last = current_time - self._last_request_time
        
        if time_since_last < self._min_request_interval:
            sleep_time = self._min_request_interval - time_since_last
            import time
            time.sleep(sleep_time)
        
        self._last_request_time = datetime.now().timestamp()
    
    def _make_request(self, endpoint: str, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Make API request with enhanced error handling and rate limiting."""
        try:
            # Rate limiting
            self._rate_limit()
            
            # Add API key and default parameters
            params.update({
                'appid': self.api_key,
                'units': self.config.weather.units
            })
            
            url = f"{self.base_url}/{endpoint}"
            
            self.logger.debug(f"🌐 Making enhanced API request: {endpoint}")
            
            response = requests.get(
                url,
                params=params,
                timeout=self.config.weather.timeout
            )
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.Timeout:
            self.logger.error("⏰ Enhanced API request timed out")
            raise Exception("Weather service timeout - please try again")
        
        except requests.exceptions.HTTPError as e:
            if response.status_code == 401:
                self.logger.error("🔑 Invalid API key")
                raise Exception("Invalid API key - please check your configuration")
            elif response.status_code == 404:
                self.logger.error("🏙️ Location not found")
                raise Exception("Location not found - please check the spelling")
            elif response.status_code == 429:
                self.logger.error("🚫 API rate limit exceeded")
                raise Exception("Too many requests - please wait a moment")
            else:
                self.logger.error(f"🌐 HTTP error: {e}")
                raise Exception(f"Weather service error: {response.status_code}")
        
        except requests.exceptions.ConnectionError:
            self.logger.error("🌐 Connection error")
            raise Exception("No internet connection - please check your network")
        
        except Exception as e:
            self.logger.error(f"❌ Unexpected error: {e}")
            raise Exception(f"Weather service error: {str(e)}")
    
    def search_locations(self, query: str, limit: int = 5) -> List[LocationSearchResult]:
        """Enhanced location search with geocoding."""
        cache_key = f"search_{query.lower()}_{limit}"
        
        # Check cache first (longer cache for search results)
        if cache_key in self._cache and self._is_cache_valid(self._cache[cache_key], 3600):  # 1 hour cache
            self.logger.debug(f"📋 Using cached search results for {query}")
            cached_data = self._cache[cache_key]['data']
            return [LocationSearchResult(**item) for item in cached_data]
        
        try:
            self.logger.info(f"🔍 Enhanced search for locations: {query}")
            
            # Use geocoding API for better results
            data = self._make_request('geo/1.0/direct', {
                'q': query,
                'limit': limit
            })
            
            if not data:
                return []
            
            locations = []
            for item in data:
                location = LocationSearchResult(
                    name=item.get('name', ''),
                    country=item.get('country', ''),
                    state=item.get('state', ''),
                    lat=item.get('lat'),
                    lon=item.get('lon')
                )
                locations.append(location)
            
            # Cache the results
            self._cache[cache_key] = {
                'data': [loc.to_dict() for loc in locations],
                'timestamp': datetime.now().isoformat()
            }
            self._save_cache()
            
            self.logger.info(f"✅ Found {len(locations)} locations for {query}")
            return locations
            
        except Exception as e:
            self.logger.warning(f"Enhanced location search failed: {e}")
            return []
    
    def get_air_quality(self, lat: float, lon: float) -> Optional[AirQualityData]:
        """Get air quality data for coordinates."""
        cache_key = f"air_quality_{lat}_{lon}"
        
        # Check cache first
        if cache_key in self._cache and self._is_cache_valid(self._cache[cache_key]):
            self.logger.debug(f"📋 Using cached air quality data")
            return AirQualityData.from_dict(self._cache[cache_key]['data'])
        
        try:
            self.logger.info(f"🌬️ Fetching air quality for {lat}, {lon}")
            
            data = self._make_request('data/2.5/air_pollution', {
                'lat': lat,
                'lon': lon
            })
            
            if not data or 'list' not in data or not data['list']:
                return None
            
            pollution_data = data['list'][0]
            components = pollution_data['components']
            
            air_quality = AirQualityData(
                aqi=pollution_data['main']['aqi'],
                co=components.get('co', 0),
                no=components.get('no', 0),
                no2=components.get('no2', 0),
                o3=components.get('o3', 0),
                so2=components.get('so2', 0),
                pm2_5=components.get('pm2_5', 0),
                pm10=components.get('pm10', 0),
                nh3=components.get('nh3', 0),
                timestamp=datetime.now()
            )
            
            # Cache the result
            self._cache[cache_key] = {
                'data': air_quality.to_dict(),
                'timestamp': datetime.now().isoformat()
            }
            self._save_cache()
            
            self.logger.info(f"✅ Air quality data retrieved: AQI {air_quality.aqi}")
            return air_quality
            
        except Exception as e:
            self.logger.warning(f"Air quality fetch failed: {e}")
            return None
    
    def get_astronomical_data(self, lat: float, lon: float) -> Optional[AstronomicalData]:
        """Get astronomical data for coordinates."""
        # This would typically use a separate astronomy API
        # For now, we'll simulate with basic sunrise/sunset from weather data
        try:
            data = self._make_request('weather', {
                'lat': lat,
                'lon': lon
            })
            
            if not data or 'sys' not in data:
                return None
            
            sunrise = datetime.fromtimestamp(data['sys']['sunrise'])
            sunset = datetime.fromtimestamp(data['sys']['sunset'])
            day_length = sunset - sunrise
            
            # Simulate moon phase (in real app, use astronomy API)
            import random
            moon_phase = random.random()
            
            astronomical = AstronomicalData(
                sunrise=sunrise,
                sunset=sunset,
                moonrise=None,  # Would need astronomy API
                moonset=None,   # Would need astronomy API
                moon_phase=moon_phase,
                day_length=day_length
            )
            
            return astronomical
            
        except Exception as e:
            self.logger.warning(f"Astronomical data fetch failed: {e}")
            return None
    
    def get_weather_alerts(self, lat: float, lon: float) -> List[WeatherAlert]:
        """Get weather alerts for coordinates."""
        try:
            # This would use the One Call API alerts endpoint
            # For now, return empty list as alerts require special API access
            return []
            
        except Exception as e:
            self.logger.warning(f"Weather alerts fetch failed: {e}")
            return []
    
    def get_enhanced_weather(self, location: str) -> EnhancedWeatherData:
        """Get enhanced weather data with all additional information."""
        cache_key = f"enhanced_{location.lower()}"
        
        # Check cache first
        if cache_key in self._cache and self._is_cache_valid(self._cache[cache_key]):
            self.logger.debug(f"📋 Using cached enhanced weather data for {location}")
            cached_data = self._cache[cache_key]['data']
            
            # Reconstruct enhanced weather data
            weather_data = EnhancedWeatherData(**cached_data['weather'])
            if cached_data.get('air_quality'):
                weather_data.air_quality = AirQualityData.from_dict(cached_data['air_quality'])
            if cached_data.get('astronomical'):
                weather_data.astronomical = AstronomicalData.from_dict(cached_data['astronomical'])
            if cached_data.get('alerts'):
                weather_data.alerts = [WeatherAlert.from_dict(alert) for alert in cached_data['alerts']]
            
            return weather_data
        
        # Fetch basic weather data first
        self.logger.info(f"🌤️ Fetching enhanced weather for {location}")
        
        data = self._make_request('weather', {'q': location})
        
        if not data:
            raise Exception("No weather data received")
        
        # Parse basic weather data
        location = Location(
            name=data['name'],
            country=data['sys']['country'],
            latitude=data['coord']['lat'],
            longitude=data['coord']['lon']
        )
        
        condition = WeatherCondition.from_openweather(
            data['weather'][0]['main'],
            data['weather'][0]['description']
        )
        
        weather_data = EnhancedWeatherData(
            location=location,
            timestamp=datetime.now(),
            condition=condition,
            description=data['weather'][0]['description'].title(),
            temperature=round(data['main']['temp'], 1),
            feels_like=round(data['main']['feels_like'], 1),
            humidity=data['main']['humidity'],
            pressure=data['main']['pressure'],
            visibility=data.get('visibility', 0) // 1000 if data.get('visibility') else None,
            wind_speed=round(data['wind']['speed'], 1) if 'wind' in data else None,
            wind_direction=data['wind'].get('deg', 0) if 'wind' in data else None,
            cloudiness=data['clouds']['all'] if 'clouds' in data else None,
            raw_data=data
        )
        
        # Get coordinates for additional data
        lat = data['coord']['lat']
        lon = data['coord']['lon']
        
        # Fetch additional data
        weather_data.air_quality = self.get_air_quality(lat, lon)
        weather_data.astronomical = self.get_astronomical_data(lat, lon)
        weather_data.alerts = self.get_weather_alerts(lat, lon)
        
        # Cache the complete result
        cache_data = {
            'weather': asdict(weather_data),
            'air_quality': weather_data.air_quality.to_dict() if weather_data.air_quality else None,
            'astronomical': weather_data.astronomical.to_dict() if weather_data.astronomical else None,
            'alerts': [alert.to_dict() for alert in weather_data.alerts] if weather_data.alerts else []
        }
        
        self._cache[cache_key] = {
            'data': cache_data,
            'timestamp': datetime.now().isoformat()
        }
        self._save_cache()
        
        self.logger.info(f"✅ Enhanced weather data retrieved for {location}")
        return weather_data
    
    def get_weather(self, location: str) -> EnhancedWeatherData:
        """Get weather data - compatibility method that delegates to get_enhanced_weather."""
        return self.get_enhanced_weather(location)
    
    def clear_cache(self) -> None:
        """Clear enhanced weather cache."""
        self._cache.clear()
        if self._cache_file.exists():
            self._cache_file.unlink()
        self.logger.info("🗑️ Enhanced weather cache cleared")