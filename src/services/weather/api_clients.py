"""Weather API clients for external service integration.

This module contains API client classes for interacting with weather services,
geocoding services, and other external APIs.
"""

import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from .enhanced_weather_service import LocationSearchResult, AirQualityData
from src.services.logging_config import get_logger
from src.services.exceptions import (
    WeatherAppError, APIError, NetworkError, RateLimitError
)
from src.services.error_handler import (
    retry_on_exception, safe_execute, handle_api_error
)


# Use centralized exceptions from services.exceptions
# WeatherServiceError -> WeatherAppError
# RateLimitError, APIKeyError, NetworkError are imported from services.exceptions

class ServiceUnavailableError(WeatherAppError):
    """Raised when the weather service is temporarily unavailable."""
    pass


class BaseAPIClient:
    """Base class for API clients with common functionality."""
    
    def __init__(self, api_key: str, cache_manager=None, logger=None):
        self.api_key = api_key
        self.cache_manager = cache_manager
        self.logger = logger or get_logger(__name__)
        
        # Error tracking and backoff
        self._consecutive_failures = 0
        self._last_successful_request = time.time()
        self._current_backoff = 1
        self._max_backoff = 300  # 5 minutes
        self._offline_mode = False
        
        # Cache for API responses
        self._cache = {}
        
        # Setup session with connection pooling and retries
        self._session = requests.Session()
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self._session.mount("http://", adapter)
        self._session.mount("https://", adapter)
        
        # Set reasonable timeouts
        self._session.timeout = (10, 30)  # (connect, read)
    
    def _is_cache_valid(self, cache_entry: Dict, max_age_seconds: int) -> bool:
        """Check if cache entry is still valid."""
        if not cache_entry or "timestamp" not in cache_entry:
            return False
        
        try:
            timestamp = datetime.fromisoformat(cache_entry["timestamp"])
            age = (datetime.now() - timestamp).total_seconds()
            return age < max_age_seconds
        except (ValueError, TypeError):
            return False
    
    def _get_stale_cache_data(self, cache_key: str, max_stale_hours: int = 24):
        """Get stale cache data as fallback when API is unavailable."""
        if cache_key not in self._cache:
            return None
        
        cache_entry = self._cache[cache_key]
        if not cache_entry or "timestamp" not in cache_entry:
            return None
        
        try:
            timestamp = datetime.fromisoformat(cache_entry["timestamp"])
            age_hours = (datetime.now() - timestamp).total_seconds() / 3600
            
            if age_hours <= max_stale_hours:
                self.logger.info(f"📦 Using stale cache data (age: {age_hours:.1f}h)")
                return cache_entry["data"]
        except (ValueError, TypeError):
            pass
        
        return None
    
    def _reset_backoff(self):
        """Reset backoff timer after successful request."""
        self._current_backoff = 1
        self._consecutive_failures = 0
    
    def _increase_backoff(self):
        """Increase backoff timer after failed request."""
        self._current_backoff = min(self._current_backoff * 2, self._max_backoff)
    
    def _check_offline_mode(self):
        """Check if we should enter offline mode."""
        if self._consecutive_failures >= 3:
            self._offline_mode = True
            self.logger.warning("🔌 Entering offline mode due to consecutive failures")
    
    def _save_cache(self):
        """Save cache to persistent storage if cache manager is available."""
        if self.cache_manager:
            try:
                self.cache_manager.set("weather_api_cache", self._cache)
            except Exception as e:
                self.logger.warning(f"Failed to save cache: {e}")


class OpenWeatherAPIClient(BaseAPIClient):
    """API client for OpenWeatherMap services."""
    
    BASE_URL = "https://api.openweathermap.org"
    
    def _make_request(self, endpoint: str, params: Dict[str, Any], 
                     use_fallback: bool = False) -> Optional[Dict]:
        """Make API request with error handling and caching."""
        
        # Check if we're in offline mode
        if self._offline_mode:
            time_since_last_success = time.time() - self._last_successful_request
            if time_since_last_success < self._current_backoff:
                self.logger.debug("⏸️ In offline mode, skipping API request")
                return None
            else:
                # Try to exit offline mode
                self._offline_mode = False
                self.logger.info("🔄 Attempting to exit offline mode")
        
        # Create cache key
        cache_key = f"{endpoint}_{hash(str(sorted(params.items())))}"
        
        # Check cache first
        if cache_key in self._cache and self._is_cache_valid(self._cache[cache_key], 600):  # 10 min cache
            return self._cache[cache_key]["data"]
        
        try:
            # Add API key to params
            params = params.copy()
            params["appid"] = self.api_key
            
            # Construct URL
            url = f"{self.BASE_URL}/{endpoint}"
            
            # Make request
            response = self._session.get(url, params=params)
            
            if response.status_code == 200:
                # Success - reset error tracking
                self._last_successful_request = time.time()
                self._offline_mode = False
                self._reset_backoff()
                
                data = response.json()
                
                # Cache the response
                self._cache[cache_key] = {
                    "data": data,
                    "timestamp": datetime.now().isoformat()
                }
                self._save_cache()
                
                return data
            
            elif response.status_code == 429:
                # Rate limit exceeded
                self._consecutive_failures += 1
                retry_after = int(response.headers.get("Retry-After", self._current_backoff))
                raise RateLimitError(retry_after)
            
            elif response.status_code == 401:
                # Invalid API key
                raise APIError("Invalid API key", status_code=401)
            
            elif response.status_code == 404:
                # Not found - not necessarily an error
                return None
            
            else:
                # Other HTTP errors
                self._consecutive_failures += 1
                raise ServiceUnavailableError(f"API returned status {response.status_code}")
        
        except (requests.exceptions.Timeout, requests.exceptions.ReadTimeout):
            self.logger.error("⏰ Request timed out")
            self._consecutive_failures += 1
            self._check_offline_mode()
            
            # Try stale cache data
            stale_data = self._get_stale_cache_data(cache_key)
            if stale_data:
                return stale_data
            raise NetworkError("Request timeout - please try again")
        
        except requests.exceptions.ConnectionError:
            self.logger.error("🌐 Connection error")
            self._consecutive_failures += 1
            self._check_offline_mode()
            
            # Try stale cache data
            stale_data = self._get_stale_cache_data(cache_key)
            if stale_data:
                return stale_data
            raise NetworkError("No internet connection - please check your network")
        
        except (RateLimitError, APIKeyError):
            # Re-raise these specific errors
            raise
        
        except Exception as e:
            self.logger.error(f"❌ Unexpected error: {e}")
            self._consecutive_failures += 1
            self._check_offline_mode()
            
            # Try stale cache data as last resort
            stale_data = self._get_stale_cache_data(cache_key)
            if stale_data:
                return stale_data
            
            raise WeatherAppError(f"Weather service error: {str(e)}")
    
    def _make_geocoding_request(self, endpoint: str, params: Dict[str, Any]) -> Optional[Dict]:
        """Make geocoding API request with error handling."""
        
        # Create cache key for geocoding
        cache_key = f"geo_{endpoint}_{hash(str(sorted(params.items())))}"
        
        # Check cache first (longer cache for geocoding)
        if cache_key in self._cache and self._is_cache_valid(self._cache[cache_key], 3600):  # 1 hour
            return self._cache[cache_key]["data"]
        
        try:
            # Add API key and construct URL
            params = params.copy()
            params["appid"] = self.api_key
            url = f"{self.BASE_URL}/{endpoint}"
            
            # Use session with connection pooling and retries
            response = self._session.get(url, params=params)
            
            if response.status_code == 200:
                # Success - reset error tracking
                self._last_successful_request = time.time()
                self._offline_mode = False
                self._reset_backoff()
                return response.json()
            elif response.status_code == 429:
                # Rate limit exceeded
                self._consecutive_failures += 1
                retry_after = int(response.headers.get("Retry-After", self._current_backoff))
                raise RateLimitError(retry_after)
            elif response.status_code == 401:
                # Invalid API key
                raise APIError("Invalid API key for geocoding", status_code=401)
            elif response.status_code == 404:
                # Location not found - not a service error
                return None
            else:
                # Other HTTP errors
                self._consecutive_failures += 1
                raise ServiceUnavailableError(f"Geocoding API returned status {response.status_code}")
        
        except (requests.exceptions.Timeout, requests.exceptions.ReadTimeout):
            self.logger.error("⏰ Geocoding request timed out")
            self._consecutive_failures += 1
            self._check_offline_mode()
            
            # Try stale cache data
            stale_data = self._get_stale_cache_data(cache_key)
            if stale_data:
                return stale_data
            raise NetworkError("Geocoding timeout - please try again")
        
        except requests.exceptions.ConnectionError:
            self.logger.error("🌐 Geocoding connection error")
            self._consecutive_failures += 1
            self._check_offline_mode()
            
            # Try stale cache data
            stale_data = self._get_stale_cache_data(cache_key)
            if stale_data:
                return stale_data
            raise NetworkError("No internet connection - please check your network")
        
        except RateLimitError:
            # Re-raise rate limit errors
            raise
        except APIKeyError:
            # Re-raise API key errors
            raise
        except Exception as e:
            self.logger.error(f"❌ Unexpected geocoding error: {e}")
            self._consecutive_failures += 1
            self._check_offline_mode()
            
            # Try stale cache data as last resort
            stale_data = self._get_stale_cache_data(cache_key)
            if stale_data:
                return stale_data
            
            raise WeatherAppError(f"Geocoding service error: {str(e)}")
    
    def get_current_weather(self, lat: float, lon: float) -> Optional[Dict]:
        """Get current weather data for coordinates."""
        return self._make_request("data/2.5/weather", {
            "lat": lat,
            "lon": lon,
            "units": "metric"
        })
    
    def get_forecast(self, lat: float, lon: float) -> Optional[Dict]:
        """Get 5-day forecast data for coordinates."""
        return self._make_request("data/2.5/forecast", {
            "lat": lat,
            "lon": lon,
            "units": "metric"
        })
    
    def get_air_quality(self, lat: float, lon: float) -> Optional[Dict]:
        """Get air quality data for coordinates."""
        return self._make_request("data/2.5/air_pollution", {
            "lat": lat,
            "lon": lon
        })
    
    def search_locations(self, query: str, limit: int = 5) -> List[LocationSearchResult]:
        """Search for locations using geocoding API."""
        try:
            data = self._make_geocoding_request("geo/1.0/direct", {
                "q": query,
                "limit": limit
            })
            
            if not data:
                return []
            
            results = []
            for item in data:
                result = LocationSearchResult(
                    name=item.get("name", ""),
                    country=item.get("country", ""),
                    state=item.get("state", ""),
                    lat=item.get("lat"),
                    lon=item.get("lon")
                )
                results.append(result)
            
            return results
        
        except Exception as e:
            self.logger.error(f"Location search failed: {e}")
            return []
    
    def search_by_zipcode(self, zipcode: str) -> Optional[LocationSearchResult]:
        """Search location by zipcode."""
        try:
            # Format zipcode for API
            formatted_zip = zipcode.replace(" ", "")
            
            # For US zipcodes, use simple format
            if formatted_zip.isdigit() and len(formatted_zip) == 5:
                query_param = f"{formatted_zip},US"
            elif "-" in formatted_zip and len(formatted_zip.split("-")[0]) == 5:
                # US ZIP+4 format
                query_param = f"{formatted_zip.split('-')[0]},US"
            else:
                # International postal code
                query_param = formatted_zip
            
            data = self._make_geocoding_request("geo/1.0/zip", {"zip": query_param})
            
            if data and "lat" in data and "lon" in data:
                return LocationSearchResult(
                    name=data.get("name", zipcode),
                    country=data.get("country", ""),
                    state="",  # Zip endpoint doesn't provide state
                    lat=data.get("lat"),
                    lon=data.get("lon")
                )
            
            return None
        
        except Exception as e:
            self.logger.error(f"Zipcode search failed for {zipcode}: {e}")
            return None
    
    def reverse_geocode(self, lat: float, lon: float) -> Optional[LocationSearchResult]:
        """Reverse geocode coordinates to location."""
        try:
            data = self._make_geocoding_request("geo/1.0/reverse", {
                "lat": lat,
                "lon": lon,
                "limit": 1
            })
            
            if data and len(data) > 0:
                item = data[0]
                return LocationSearchResult(
                    name=item.get("name", ""),
                    country=item.get("country", ""),
                    state=item.get("state", ""),
                    lat=item.get("lat"),
                    lon=item.get("lon")
                )
            
            return None
        
        except Exception as e:
            self.logger.error(f"Reverse geocoding failed for {lat}, {lon}: {e}")
            return None


class WeatherAPIClient(BaseAPIClient):
    """API client for WeatherAPI.com services (fallback)."""
    
    BASE_URL = "https://api.weatherapi.com/v1"
    
    def _make_request(self, endpoint: str, params: Dict[str, Any]) -> Optional[Dict]:
        """Make API request to WeatherAPI.com."""
        
        # Create cache key
        cache_key = f"weatherapi_{endpoint}_{hash(str(sorted(params.items())))}"
        
        # Check cache first
        if cache_key in self._cache and self._is_cache_valid(self._cache[cache_key], 600):  # 10 min cache
            return self._cache[cache_key]["data"]
        
        try:
            # Add API key to params
            params = params.copy()
            params["key"] = self.api_key
            
            # Construct URL
            url = f"{self.BASE_URL}/{endpoint}"
            
            # Make request
            response = self._session.get(url, params=params)
            
            if response.status_code == 200:
                data = response.json()
                
                # Cache the response
                self._cache[cache_key] = {
                    "data": data,
                    "timestamp": datetime.now().isoformat()
                }
                self._save_cache()
                
                return data
            
            elif response.status_code == 401:
                raise APIError("Invalid WeatherAPI key", status_code=401)
            
            elif response.status_code == 429:
                raise RateLimitError(60)  # Default retry after 1 minute
            
            else:
                raise ServiceUnavailableError(f"WeatherAPI returned status {response.status_code}")
        
        except Exception as e:
            self.logger.error(f"WeatherAPI request failed: {e}")
            raise
    
    def get_current_weather(self, lat: float, lon: float) -> Optional[Dict]:
        """Get current weather from WeatherAPI.com."""
        return self._make_request("current.json", {
            "q": f"{lat},{lon}",
            "aqi": "yes"
        })
    
    def get_forecast(self, lat: float, lon: float, days: int = 5) -> Optional[Dict]:
        """Get forecast from WeatherAPI.com."""
        return self._make_request("forecast.json", {
            "q": f"{lat},{lon}",
            "days": min(days, 10),  # WeatherAPI supports up to 10 days
            "aqi": "yes"
        })
    
    def search_locations(self, query: str) -> List[LocationSearchResult]:
        """Search locations using WeatherAPI.com."""
        try:
            data = self._make_request("search.json", {"q": query})
            
            if not data:
                return []
            
            results = []
            for item in data:
                result = LocationSearchResult(
                    name=item.get("name", ""),
                    country=item.get("country", ""),
                    state=item.get("region", ""),
                    lat=item.get("lat"),
                    lon=item.get("lon")
                )
                results.append(result)
            
            return results
        
        except Exception as e:
            self.logger.error(f"WeatherAPI location search failed: {e}")
            return []