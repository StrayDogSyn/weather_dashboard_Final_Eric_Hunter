"""Optimized Team Data Service for high-performance loading and processing of team weather data.

This service provides intelligent caching, async support, robust error handling,
and data validation for team collaboration features.
"""

import asyncio
import csv
import json
import logging
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from io import StringIO
from typing import Dict, List, Optional, Any, Callable, Union
from urllib.parse import urljoin
from urllib.request import urlopen
from urllib.error import URLError, HTTPError

from ..utils.logger import LoggerMixin


@dataclass
class TeamDataConfig:
    """Configuration for team data service."""
    base_url: str = "https://raw.githubusercontent.com/StrayDogSyn/New_Team_Dashboard/main/exports"
    cache_ttl: int = 300  # 5 minutes
    max_retries: int = 3
    retry_delay: float = 1.0
    timeout: int = 30
    enable_metrics: bool = True
    max_concurrent_downloads: int = 5
    chunk_size: int = 8192


@dataclass
class CacheEntry:
    """Cache entry with TTL support."""
    data: Any
    timestamp: datetime
    ttl: int
    
    def is_expired(self) -> bool:
        """Check if cache entry is expired."""
        return datetime.now() - self.timestamp > timedelta(seconds=self.ttl)


@dataclass
class DataValidator:
    """Data validation and cleaning utilities."""
    
    @staticmethod
    def clean_csv_data(data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Clean and validate CSV data."""
        cleaned = []
        for row in data:
            if DataValidator._is_valid_weather_record(row):
                cleaned_row = DataValidator._clean_weather_record(row)
                if cleaned_row:
                    cleaned.append(cleaned_row)
        return cleaned
    
    @staticmethod
    def _is_valid_weather_record(record: Dict[str, Any]) -> bool:
        """Validate weather record has required fields."""
        required_fields = ['city', 'temperature', 'timestamp']
        return all(field in record and record[field] is not None for field in required_fields)
    
    @staticmethod
    def _clean_weather_record(record: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Clean and normalize weather record."""
        try:
            cleaned = {
                'city': str(record.get('city', '')).strip(),
                'country': str(record.get('country', '')).strip(),
                'temperature': float(record.get('temperature', 0)),
                'humidity': float(record.get('humidity', 0)) if record.get('humidity') else None,
                'wind_speed': float(record.get('wind_speed', 0)) if record.get('wind_speed') else None,
                'pressure': float(record.get('pressure', 0)) if record.get('pressure') else None,
                'weather_condition': str(record.get('weather_condition', '')).strip(),
                'timestamp': record.get('timestamp', ''),
                'shared_by': str(record.get('shared_by', '')).strip()
            }
            
            # Validate temperature range
            if not -100 <= cleaned['temperature'] <= 60:
                return None
                
            # Validate humidity range
            if cleaned['humidity'] is not None and not 0 <= cleaned['humidity'] <= 100:
                cleaned['humidity'] = None
                
            return cleaned
        except (ValueError, TypeError):
            return None


class OptimizedTeamDataService(LoggerMixin):
    """High-performance team data service with caching and async support."""
    
    def __init__(self, config: Optional[TeamDataConfig] = None):
        """Initialize the optimized team data service.
        
        Args:
            config: Service configuration
        """
        super().__init__()
        self.config = config or TeamDataConfig()
        self.cache: Dict[str, CacheEntry] = {}
        self.metrics: Dict[str, Any] = {
            'cache_hits': 0,
            'cache_misses': 0,
            'download_count': 0,
            'error_count': 0,
            'total_requests': 0,
            'avg_response_time': 0.0
        }
        self.executor = ThreadPoolExecutor(max_workers=self.config.max_concurrent_downloads)
        self._callbacks: List[Callable[[str, Any], None]] = []
        
    def add_callback(self, callback: Callable[[str, Any], None]):
        """Add callback for data updates.
        
        Args:
            callback: Function to call when data is updated
        """
        self._callbacks.append(callback)
        
    def remove_callback(self, callback: Callable[[str, Any], None]):
        """Remove callback.
        
        Args:
            callback: Function to remove
        """
        if callback in self._callbacks:
            self._callbacks.remove(callback)
    
    def _notify_callbacks(self, event: str, data: Any):
        """Notify all registered callbacks.
        
        Args:
            event: Event type
            data: Event data
        """
        for callback in self._callbacks:
            try:
                callback(event, data)
            except Exception as e:
                self.logger.warning(f"Callback error: {e}")
    
    def _get_from_cache(self, key: str) -> Optional[Any]:
        """Get data from cache if not expired.
        
        Args:
            key: Cache key
            
        Returns:
            Cached data or None if expired/missing
        """
        if key in self.cache:
            entry = self.cache[key]
            if not entry.is_expired():
                if self.config.enable_metrics:
                    self.metrics['cache_hits'] += 1
                return entry.data
            else:
                # Remove expired entry
                del self.cache[key]
        
        if self.config.enable_metrics:
            self.metrics['cache_misses'] += 1
        return None
    
    def _set_cache(self, key: str, data: Any, ttl: Optional[int] = None):
        """Set data in cache.
        
        Args:
            key: Cache key
            data: Data to cache
            ttl: Time to live in seconds
        """
        ttl = ttl or self.config.cache_ttl
        self.cache[key] = CacheEntry(
            data=data,
            timestamp=datetime.now(),
            ttl=ttl
        )
    
    def _download_with_retry(self, url: str) -> Optional[str]:
        """Download data with retry logic.
        
        Args:
            url: URL to download
            
        Returns:
            Downloaded content or None if failed
        """
        start_time = time.time()
        
        for attempt in range(self.config.max_retries):
            try:
                if self.config.enable_metrics:
                    self.metrics['download_count'] += 1
                    
                with urlopen(url, timeout=self.config.timeout) as response:
                    content = response.read().decode('utf-8')
                    
                if self.config.enable_metrics:
                    response_time = time.time() - start_time
                    self.metrics['avg_response_time'] = (
                        (self.metrics['avg_response_time'] * (self.metrics['total_requests'] - 1) + response_time) /
                        self.metrics['total_requests']
                    )
                    
                return content
                
            except (URLError, HTTPError, TimeoutError) as e:
                self.logger.warning(f"Download attempt {attempt + 1} failed for {url}: {e}")
                if attempt < self.config.max_retries - 1:
                    time.sleep(self.config.retry_delay * (2 ** attempt))  # Exponential backoff
                else:
                    if self.config.enable_metrics:
                        self.metrics['error_count'] += 1
                    self.logger.error(f"Failed to download {url} after {self.config.max_retries} attempts")
                    
        return None
    
    def load_csv_data(self, filename: str, use_cache: bool = True) -> Optional[List[Dict[str, Any]]]:
        """Load and parse CSV data from team repository.
        
        Args:
            filename: CSV filename to load
            use_cache: Whether to use cached data
            
        Returns:
            Parsed CSV data or None if failed
        """
        if self.config.enable_metrics:
            self.metrics['total_requests'] += 1
            
        cache_key = f"csv_{filename}"
        
        # Check cache first
        if use_cache:
            cached_data = self._get_from_cache(cache_key)
            if cached_data is not None:
                return cached_data
        
        # Download and parse CSV
        url = urljoin(self.config.base_url + "/", filename)
        content = self._download_with_retry(url)
        
        if content is None:
            return None
            
        try:
            # Parse CSV
            csv_reader = csv.DictReader(StringIO(content))
            raw_data = list(csv_reader)
            
            # Clean and validate data
            cleaned_data = DataValidator.clean_csv_data(raw_data)
            
            # Cache the result
            if use_cache:
                self._set_cache(cache_key, cleaned_data)
                
            self.logger.info(f"Loaded {len(cleaned_data)} records from {filename}")
            self._notify_callbacks('csv_loaded', {'filename': filename, 'records': len(cleaned_data)})
            
            return cleaned_data
            
        except Exception as e:
            self.logger.error(f"Error parsing CSV {filename}: {e}")
            if self.config.enable_metrics:
                self.metrics['error_count'] += 1
            return None
    
    def load_json_data(self, filename: str, use_cache: bool = True) -> Optional[Dict[str, Any]]:
        """Load and parse JSON data from team repository.
        
        Args:
            filename: JSON filename to load
            use_cache: Whether to use cached data
            
        Returns:
            Parsed JSON data or None if failed
        """
        if self.config.enable_metrics:
            self.metrics['total_requests'] += 1
            
        cache_key = f"json_{filename}"
        
        # Check cache first
        if use_cache:
            cached_data = self._get_from_cache(cache_key)
            if cached_data is not None:
                return cached_data
        
        # Download and parse JSON
        url = urljoin(self.config.base_url + "/", filename)
        content = self._download_with_retry(url)
        
        if content is None:
            return None
            
        try:
            data = json.loads(content)
            
            # Cache the result
            if use_cache:
                self._set_cache(cache_key, data)
                
            self.logger.info(f"Loaded JSON data from {filename}")
            self._notify_callbacks('json_loaded', {'filename': filename, 'data': data})
            
            return data
            
        except json.JSONDecodeError as e:
            self.logger.error(f"Error parsing JSON {filename}: {e}")
            if self.config.enable_metrics:
                self.metrics['error_count'] += 1
            return None
    
    async def load_csv_data_async(self, filename: str, use_cache: bool = True) -> Optional[List[Dict[str, Any]]]:
        """Asynchronously load CSV data.
        
        Args:
            filename: CSV filename to load
            use_cache: Whether to use cached data
            
        Returns:
            Parsed CSV data or None if failed
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self.executor, 
            self.load_csv_data, 
            filename, 
            use_cache
        )
    
    async def load_json_data_async(self, filename: str, use_cache: bool = True) -> Optional[Dict[str, Any]]:
        """Asynchronously load JSON data.
        
        Args:
            filename: JSON filename to load
            use_cache: Whether to use cached data
            
        Returns:
            Parsed JSON data or None if failed
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self.executor, 
            self.load_json_data, 
            filename, 
            use_cache
        )
    
    def get_city_weather(self, city_name: str, use_cache: bool = True) -> Optional[List[Dict[str, Any]]]:
        """Get weather data for a specific city.
        
        Args:
            city_name: Name of the city
            use_cache: Whether to use cached data
            
        Returns:
            Weather data for the city or None if not found
        """
        # Load team weather data
        weather_data = self.load_csv_data("team_weather_data.csv", use_cache)
        
        if weather_data is None:
            return None
            
        # Filter by city
        city_data = [
            record for record in weather_data 
            if record.get('city', '').lower() == city_name.lower()
        ]
        
        return city_data if city_data else None
    
    def get_team_summary(self, use_cache: bool = True) -> Optional[Dict[str, Any]]:
        """Get team summary statistics.
        
        Args:
            use_cache: Whether to use cached data
            
        Returns:
            Team summary data or None if failed
        """
        return self.load_json_data("team_summary.json", use_cache)
    
    def get_cities_analysis(self, use_cache: bool = True) -> Optional[Dict[str, Any]]:
        """Get cities analysis data.
        
        Args:
            use_cache: Whether to use cached data
            
        Returns:
            Cities analysis data or None if failed
        """
        return self.load_json_data("cities_analysis.json", use_cache)
    
    def refresh_all_data(self) -> Dict[str, bool]:
        """Refresh all cached data.
        
        Returns:
            Dictionary with refresh status for each data type
        """
        results = {}
        
        # Clear cache
        self.cache.clear()
        
        # Reload all data types
        data_files = [
            ("team_weather_data.csv", "csv"),
            ("team_summary.json", "json"),
            ("cities_analysis.json", "json")
        ]
        
        for filename, file_type in data_files:
            try:
                if file_type == "csv":
                    data = self.load_csv_data(filename, use_cache=False)
                else:
                    data = self.load_json_data(filename, use_cache=False)
                    
                results[filename] = data is not None
            except Exception as e:
                self.logger.error(f"Error refreshing {filename}: {e}")
                results[filename] = False
        
        self._notify_callbacks('data_refreshed', results)
        return results
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get service metrics.
        
        Returns:
            Service metrics dictionary
        """
        if not self.config.enable_metrics:
            return {}
            
        cache_hit_rate = 0.0
        total_cache_requests = self.metrics['cache_hits'] + self.metrics['cache_misses']
        if total_cache_requests > 0:
            cache_hit_rate = self.metrics['cache_hits'] / total_cache_requests
            
        return {
            **self.metrics,
            'cache_hit_rate': cache_hit_rate,
            'cache_size': len(self.cache),
            'active_downloads': self.executor._threads
        }
    
    def clear_cache(self):
        """Clear all cached data."""
        self.cache.clear()
        self.logger.info("Cache cleared")
        self._notify_callbacks('cache_cleared', {})
    
    def shutdown(self):
        """Shutdown the service and cleanup resources."""
        self.executor.shutdown(wait=True)
        self.cache.clear()
        self._callbacks.clear()
        self.logger.info("Team data service shutdown complete")