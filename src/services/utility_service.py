"""Utility Service

Provides shared utility functions and common operations used across the application.
Includes data validation, formatting, caching, and helper functions.
"""

import logging
import hashlib
import json
import os
import re
from typing import Any, Dict, List, Optional, Union, Callable
from datetime import datetime, timezone, timedelta
from pathlib import Path
import pickle
from functools import wraps
import time


class ValidationService:
    """Service for data validation operations."""
    
    def __init__(self):
        """Initialize the validation service."""
        self.logger = logging.getLogger(__name__)
    
    def validate_coordinates(self, lat: float, lon: float) -> bool:
        """Validate latitude and longitude coordinates.
        
        Args:
            lat: Latitude value
            lon: Longitude value
            
        Returns:
            True if coordinates are valid
        """
        try:
            return -90 <= lat <= 90 and -180 <= lon <= 180
        except (TypeError, ValueError):
            return False
    
    def validate_city_name(self, city: str) -> bool:
        """Validate city name format.
        
        Args:
            city: City name to validate
            
        Returns:
            True if city name is valid
        """
        if not city or not isinstance(city, str):
            return False
        
        # Remove extra whitespace and check length
        city = city.strip()
        if len(city) < 2 or len(city) > 100:
            return False
        
        # Check for valid characters (letters, spaces, hyphens, apostrophes)
        pattern = r"^[a-zA-Z\s\-']+$"
        return bool(re.match(pattern, city))
    
    def validate_api_key(self, api_key: str) -> bool:
        """Validate API key format.
        
        Args:
            api_key: API key to validate
            
        Returns:
            True if API key format is valid
        """
        if not api_key or not isinstance(api_key, str):
            return False
        
        # Basic validation - should be alphanumeric and reasonable length
        api_key = api_key.strip()
        return len(api_key) >= 16 and api_key.isalnum()
    
    def validate_temperature_range(self, temp: float, unit: str = 'celsius') -> bool:
        """Validate temperature is within reasonable range.
        
        Args:
            temp: Temperature value
            unit: Temperature unit ('celsius', 'fahrenheit', 'kelvin')
            
        Returns:
            True if temperature is within valid range
        """
        try:
            if unit.lower() == 'celsius':
                return -100 <= temp <= 60  # Extreme but possible range
            elif unit.lower() == 'fahrenheit':
                return -148 <= temp <= 140
            elif unit.lower() == 'kelvin':
                return 173 <= temp <= 333
            else:
                return False
        except (TypeError, ValueError):
            return False
    
    def validate_humidity(self, humidity: Union[int, float]) -> bool:
        """Validate humidity percentage.
        
        Args:
            humidity: Humidity percentage
            
        Returns:
            True if humidity is valid
        """
        try:
            return 0 <= humidity <= 100
        except (TypeError, ValueError):
            return False
    
    def validate_pressure(self, pressure: float) -> bool:
        """Validate atmospheric pressure.
        
        Args:
            pressure: Pressure in hPa
            
        Returns:
            True if pressure is valid
        """
        try:
            return 800 <= pressure <= 1200  # Reasonable atmospheric pressure range
        except (TypeError, ValueError):
            return False
    
    def validate_wind_speed(self, speed: float) -> bool:
        """Validate wind speed.
        
        Args:
            speed: Wind speed in m/s
            
        Returns:
            True if wind speed is valid
        """
        try:
            return 0 <= speed <= 150  # Up to extreme hurricane speeds
        except (TypeError, ValueError):
            return False
    
    def validate_uv_index(self, uv: float) -> bool:
        """Validate UV index.
        
        Args:
            uv: UV index value
            
        Returns:
            True if UV index is valid
        """
        try:
            return 0 <= uv <= 20  # Theoretical maximum is around 15-16
        except (TypeError, ValueError):
            return False


class FormattingService:
    """Service for data formatting operations."""
    
    def __init__(self):
        """Initialize the formatting service."""
        self.logger = logging.getLogger(__name__)
    
    def format_temperature(self, temp: float, unit: str = 'celsius', 
                          decimal_places: int = 1) -> str:
        """Format temperature with unit.
        
        Args:
            temp: Temperature value
            unit: Temperature unit
            decimal_places: Number of decimal places
            
        Returns:
            Formatted temperature string
        """
        try:
            unit_symbols = {
                'celsius': '°C',
                'fahrenheit': '°F',
                'kelvin': 'K'
            }
            symbol = unit_symbols.get(unit.lower(), '°C')
            return f"{temp:.{decimal_places}f}{symbol}"
        except (TypeError, ValueError) as e:
            self.logger.error(f"Error formatting temperature: {e}")
            return "N/A"
    
    def format_pressure(self, pressure: float, unit: str = 'hpa') -> str:
        """Format pressure with unit.
        
        Args:
            pressure: Pressure value
            unit: Pressure unit
            
        Returns:
            Formatted pressure string
        """
        try:
            unit_symbols = {
                'hpa': ' hPa',
                'mbar': ' mbar',
                'inhg': ' inHg',
                'mmhg': ' mmHg'
            }
            symbol = unit_symbols.get(unit.lower(), ' hPa')
            
            if unit.lower() == 'inhg':
                # Convert hPa to inHg
                pressure = pressure * 0.02953
                return f"{pressure:.2f}{symbol}"
            elif unit.lower() == 'mmhg':
                # Convert hPa to mmHg
                pressure = pressure * 0.75006
                return f"{pressure:.0f}{symbol}"
            else:
                return f"{pressure:.0f}{symbol}"
        except (TypeError, ValueError) as e:
            self.logger.error(f"Error formatting pressure: {e}")
            return "N/A"
    
    def format_wind_speed(self, speed: float, unit: str = 'ms') -> str:
        """Format wind speed with unit.
        
        Args:
            speed: Wind speed value
            unit: Wind speed unit
            
        Returns:
            Formatted wind speed string
        """
        try:
            if unit.lower() == 'kmh':
                # Convert m/s to km/h
                speed = speed * 3.6
                return f"{speed:.1f} km/h"
            elif unit.lower() == 'mph':
                # Convert m/s to mph
                speed = speed * 2.237
                return f"{speed:.1f} mph"
            elif unit.lower() == 'knots':
                # Convert m/s to knots
                speed = speed * 1.944
                return f"{speed:.1f} knots"
            else:
                return f"{speed:.1f} m/s"
        except (TypeError, ValueError) as e:
            self.logger.error(f"Error formatting wind speed: {e}")
            return "N/A"
    
    def format_distance(self, distance: float, unit: str = 'km') -> str:
        """Format distance with unit.
        
        Args:
            distance: Distance value
            unit: Distance unit
            
        Returns:
            Formatted distance string
        """
        try:
            if unit.lower() == 'miles':
                # Convert km to miles
                distance = distance * 0.621371
                return f"{distance:.1f} miles"
            elif unit.lower() == 'm':
                # Convert km to meters
                distance = distance * 1000
                return f"{distance:.0f} m"
            else:
                return f"{distance:.1f} km"
        except (TypeError, ValueError) as e:
            self.logger.error(f"Error formatting distance: {e}")
            return "N/A"
    
    def format_datetime(self, dt: datetime, format_type: str = 'default') -> str:
        """Format datetime for display.
        
        Args:
            dt: Datetime object
            format_type: Format type ('default', 'short', 'time_only', 'date_only')
            
        Returns:
            Formatted datetime string
        """
        try:
            if format_type == 'short':
                return dt.strftime("%m/%d %H:%M")
            elif format_type == 'time_only':
                return dt.strftime("%H:%M")
            elif format_type == 'date_only':
                return dt.strftime("%Y-%m-%d")
            else:
                return dt.strftime("%Y-%m-%d %H:%M:%S")
        except (TypeError, ValueError) as e:
            self.logger.error(f"Error formatting datetime: {e}")
            return "N/A"
    
    def format_percentage(self, value: Union[int, float], decimal_places: int = 0) -> str:
        """Format percentage value.
        
        Args:
            value: Percentage value
            decimal_places: Number of decimal places
            
        Returns:
            Formatted percentage string
        """
        try:
            return f"{value:.{decimal_places}f}%"
        except (TypeError, ValueError) as e:
            self.logger.error(f"Error formatting percentage: {e}")
            return "N/A"


class CacheService:
    """Service for caching operations."""
    
    def __init__(self, cache_dir: Optional[str] = None, default_ttl: int = 3600):
        """Initialize the cache service.
        
        Args:
            cache_dir: Directory for cache files
            default_ttl: Default time-to-live in seconds
        """
        self.logger = logging.getLogger(__name__)
        self.cache_dir = Path(cache_dir) if cache_dir else Path.cwd() / 'cache'
        self.default_ttl = default_ttl
        self.memory_cache = {}
        
        # Create cache directory if it doesn't exist
        self.cache_dir.mkdir(exist_ok=True)
    
    def get(self, key: str, use_memory: bool = True) -> Optional[Any]:
        """Get value from cache.
        
        Args:
            key: Cache key
            use_memory: Whether to use memory cache first
            
        Returns:
            Cached value or None if not found/expired
        """
        try:
            # Check memory cache first
            if use_memory and key in self.memory_cache:
                entry = self.memory_cache[key]
                if entry['expires'] > datetime.now():
                    return entry['data']
                else:
                    del self.memory_cache[key]
            
            # Check file cache
            cache_file = self.cache_dir / f"{self._hash_key(key)}.cache"
            if cache_file.exists():
                with open(cache_file, 'rb') as f:
                    entry = pickle.load(f)
                
                if entry['expires'] > datetime.now():
                    # Update memory cache
                    if use_memory:
                        self.memory_cache[key] = entry
                    return entry['data']
                else:
                    # Remove expired file
                    cache_file.unlink()
            
            return None
        except Exception as e:
            self.logger.error(f"Error getting cache value: {e}")
            return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None, 
            use_memory: bool = True) -> bool:
        """Set value in cache.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time-to-live in seconds
            use_memory: Whether to also store in memory cache
            
        Returns:
            True if successful
        """
        try:
            ttl = ttl or self.default_ttl
            expires = datetime.now() + timedelta(seconds=ttl)
            
            entry = {
                'data': value,
                'expires': expires,
                'created': datetime.now()
            }
            
            # Store in memory cache
            if use_memory:
                self.memory_cache[key] = entry
            
            # Store in file cache
            cache_file = self.cache_dir / f"{self._hash_key(key)}.cache"
            with open(cache_file, 'wb') as f:
                pickle.dump(entry, f)
            
            return True
        except Exception as e:
            self.logger.error(f"Error setting cache value: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """Delete value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            True if successful
        """
        try:
            # Remove from memory cache
            if key in self.memory_cache:
                del self.memory_cache[key]
            
            # Remove from file cache
            cache_file = self.cache_dir / f"{self._hash_key(key)}.cache"
            if cache_file.exists():
                cache_file.unlink()
            
            return True
        except Exception as e:
            self.logger.error(f"Error deleting cache value: {e}")
            return False
    
    def clear(self) -> bool:
        """Clear all cache entries.
        
        Returns:
            True if successful
        """
        try:
            # Clear memory cache
            self.memory_cache.clear()
            
            # Clear file cache
            for cache_file in self.cache_dir.glob("*.cache"):
                cache_file.unlink()
            
            return True
        except Exception as e:
            self.logger.error(f"Error clearing cache: {e}")
            return False
    
    def cleanup_expired(self) -> int:
        """Remove expired cache entries.
        
        Returns:
            Number of entries removed
        """
        removed_count = 0
        try:
            current_time = datetime.now()
            
            # Clean memory cache
            expired_keys = [
                key for key, entry in self.memory_cache.items()
                if entry['expires'] <= current_time
            ]
            for key in expired_keys:
                del self.memory_cache[key]
                removed_count += 1
            
            # Clean file cache
            for cache_file in self.cache_dir.glob("*.cache"):
                try:
                    with open(cache_file, 'rb') as f:
                        entry = pickle.load(f)
                    
                    if entry['expires'] <= current_time:
                        cache_file.unlink()
                        removed_count += 1
                except (pickle.PickleError, OSError, KeyError) as e:
                    # Remove corrupted cache files
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.debug(f"Removing corrupted cache file {cache_file}: {e}")
                    cache_file.unlink()
                    removed_count += 1
            
            return removed_count
        except Exception as e:
            self.logger.error(f"Error cleaning up cache: {e}")
            return removed_count
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics.
        
        Returns:
            Dictionary with cache statistics
        """
        try:
            memory_count = len(self.memory_cache)
            file_count = len(list(self.cache_dir.glob("*.cache")))
            
            # Calculate total size
            total_size = 0
            for cache_file in self.cache_dir.glob("*.cache"):
                total_size += cache_file.stat().st_size
            
            return {
                'memory_entries': memory_count,
                'file_entries': file_count,
                'total_size_bytes': total_size,
                'cache_directory': str(self.cache_dir),
                'default_ttl': self.default_ttl
            }
        except Exception as e:
            self.logger.error(f"Error getting cache stats: {e}")
            return {}
    
    def _hash_key(self, key: str) -> str:
        """Generate hash for cache key.
        
        Args:
            key: Original key
            
        Returns:
            Hashed key
        """
        return hashlib.md5(key.encode()).hexdigest()


class RateLimitService:
    """Service for rate limiting operations."""
    
    def __init__(self):
        """Initialize the rate limit service."""
        self.logger = logging.getLogger(__name__)
        self.requests = {}
    
    def is_allowed(self, key: str, max_requests: int, window_seconds: int) -> bool:
        """Check if request is allowed under rate limit.
        
        Args:
            key: Unique identifier for the rate limit
            max_requests: Maximum requests allowed
            window_seconds: Time window in seconds
            
        Returns:
            True if request is allowed
        """
        try:
            current_time = time.time()
            window_start = current_time - window_seconds
            
            # Initialize or clean up old requests
            if key not in self.requests:
                self.requests[key] = []
            
            # Remove old requests outside the window
            self.requests[key] = [
                req_time for req_time in self.requests[key]
                if req_time > window_start
            ]
            
            # Check if under limit
            if len(self.requests[key]) < max_requests:
                self.requests[key].append(current_time)
                return True
            
            return False
        except Exception as e:
            self.logger.error(f"Error checking rate limit: {e}")
            return True  # Allow on error to avoid blocking
    
    def get_remaining(self, key: str, max_requests: int, window_seconds: int) -> int:
        """Get remaining requests in current window.
        
        Args:
            key: Unique identifier for the rate limit
            max_requests: Maximum requests allowed
            window_seconds: Time window in seconds
            
        Returns:
            Number of remaining requests
        """
        try:
            current_time = time.time()
            window_start = current_time - window_seconds
            
            if key not in self.requests:
                return max_requests
            
            # Count requests in current window
            current_requests = [
                req_time for req_time in self.requests[key]
                if req_time > window_start
            ]
            
            return max(0, max_requests - len(current_requests))
        except Exception as e:
            self.logger.error(f"Error getting remaining requests: {e}")
            return max_requests


def retry_on_failure(max_retries: int = 3, delay: float = 1.0, 
                    backoff_factor: float = 2.0):
    """Decorator for retrying failed operations.
    
    Args:
        max_retries: Maximum number of retry attempts
        delay: Initial delay between retries
        backoff_factor: Multiplier for delay on each retry
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            current_delay = delay
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries:
                        time.sleep(current_delay)
                        current_delay *= backoff_factor
                    else:
                        raise last_exception
            
            return None
        return wrapper
    return decorator


def measure_execution_time(func: Callable) -> Callable:
    """Decorator to measure function execution time."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        
        logger = logging.getLogger(func.__module__)
        logger.debug(f"{func.__name__} executed in {end_time - start_time:.3f} seconds")
        
        return result
    return wrapper


class UtilityService:
    """Main utility service that combines all utility functions."""
    
    def __init__(self, cache_dir: Optional[str] = None):
        """Initialize the utility service.
        
        Args:
            cache_dir: Directory for cache files
        """
        self.validation = ValidationService()
        self.formatting = FormattingService()
        self.cache = CacheService(cache_dir)
        self.rate_limit = RateLimitService()
        self.logger = logging.getLogger(__name__)
    
    def generate_location_id(self, location: str, country: str = '') -> str:
        """Generate unique ID for a location.
        
        Args:
            location: Location name
            country: Country name
            
        Returns:
            Unique location identifier
        """
        location_string = f"{location.lower().strip()}_{country.lower().strip()}"
        return hashlib.md5(location_string.encode()).hexdigest()[:12]
    
    def sanitize_filename(self, filename: str) -> str:
        """Sanitize filename for safe file operations.
        
        Args:
            filename: Original filename
            
        Returns:
            Sanitized filename
        """
        # Remove or replace invalid characters
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, '_')
        
        # Remove leading/trailing spaces and dots
        filename = filename.strip(' .')
        
        # Limit length
        if len(filename) > 255:
            filename = filename[:255]
        
        return filename or 'unnamed'
    
    def parse_location_input(self, location_input: str) -> Dict[str, Optional[str]]:
        """Parse location input to extract city and country.
        
        Args:
            location_input: User input for location
            
        Returns:
            Dictionary with parsed city and country
        """
        try:
            # Clean input
            location_input = location_input.strip()
            
            # Check for coordinates pattern (lat,lon)
            coord_pattern = r'^(-?\d+\.?\d*),\s*(-?\d+\.?\d*)$'
            coord_match = re.match(coord_pattern, location_input)
            
            if coord_match:
                lat, lon = float(coord_match.group(1)), float(coord_match.group(2))
                if self.validation.validate_coordinates(lat, lon):
                    return {
                        'type': 'coordinates',
                        'lat': lat,
                        'lon': lon,
                        'city': None,
                        'country': None
                    }
            
            # Check for city, country pattern
            if ',' in location_input:
                parts = [part.strip() for part in location_input.split(',')]
                if len(parts) == 2:
                    city, country = parts
                    if self.validation.validate_city_name(city):
                        return {
                            'type': 'city_country',
                            'city': city,
                            'country': country,
                            'lat': None,
                            'lon': None
                        }
            
            # Assume it's just a city name
            if self.validation.validate_city_name(location_input):
                return {
                    'type': 'city',
                    'city': location_input,
                    'country': None,
                    'lat': None,
                    'lon': None
                }
            
            return {
                'type': 'invalid',
                'city': None,
                'country': None,
                'lat': None,
                'lon': None
            }
        except Exception as e:
            self.logger.error(f"Error parsing location input: {e}")
            return {
                'type': 'error',
                'city': None,
                'country': None,
                'lat': None,
                'lon': None
            }
    
    def calculate_distance(self, lat1: float, lon1: float, 
                          lat2: float, lon2: float) -> float:
        """Calculate distance between two coordinates using Haversine formula.
        
        Args:
            lat1, lon1: First coordinate
            lat2, lon2: Second coordinate
            
        Returns:
            Distance in kilometers
        """
        try:
            from math import radians, sin, cos, sqrt, atan2
            
            # Convert to radians
            lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
            
            # Haversine formula
            dlat = lat2 - lat1
            dlon = lon2 - lon1
            a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
            c = 2 * atan2(sqrt(a), sqrt(1-a))
            
            # Earth's radius in kilometers
            r = 6371
            
            return r * c
        except Exception as e:
            self.logger.error(f"Error calculating distance: {e}")
            return 0.0
    
    def get_system_info(self) -> Dict[str, Any]:
        """Get system information for debugging.
        
        Returns:
            Dictionary with system information
        """
        try:
            import platform
            import psutil
            
            return {
                'platform': platform.platform(),
                'python_version': platform.python_version(),
                'cpu_count': psutil.cpu_count(),
                'memory_total': psutil.virtual_memory().total,
                'memory_available': psutil.virtual_memory().available,
                'disk_usage': psutil.disk_usage('/').percent if os.name != 'nt' else psutil.disk_usage('C:').percent
            }
        except ImportError:
            # psutil not available
            import platform
            return {
                'platform': platform.platform(),
                'python_version': platform.python_version(),
                'cpu_count': os.cpu_count(),
                'memory_total': 'Unknown',
                'memory_available': 'Unknown',
                'disk_usage': 'Unknown'
            }
        except Exception as e:
            self.logger.error(f"Error getting system info: {e}")
            return {}