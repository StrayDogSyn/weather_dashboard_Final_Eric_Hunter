"""Cache service implementation with TTL and performance monitoring.

Provides caching functionality for API responses, database queries, and computed results.
"""

import time
import threading
import weakref
from typing import Any, Optional, Dict, Tuple, Callable
from dataclasses import dataclass
from collections import defaultdict
import logging
import json
import hashlib


@dataclass
class CacheStats:
    """Cache performance statistics."""
    hits: int = 0
    misses: int = 0
    evictions: int = 0
    memory_usage: int = 0
    
    @property
    def hit_rate(self) -> float:
        """Calculate cache hit rate."""
        total = self.hits + self.misses
        return self.hits / total if total > 0 else 0.0


class CacheEntry:
    """Cache entry with metadata."""
    
    def __init__(self, value: Any, ttl: float, size: int = 0):
        self.value = value
        self.timestamp = time.time()
        self.ttl = ttl
        self.size = size
        self.access_count = 0
        self.last_access = self.timestamp
    
    def is_expired(self) -> bool:
        """Check if cache entry has expired."""
        return time.time() - self.timestamp > self.ttl
    
    def access(self) -> Any:
        """Access the cached value and update metadata."""
        self.access_count += 1
        self.last_access = time.time()
        return self.value


class CacheService:
    """High-performance cache service with TTL and memory management."""
    
    def __init__(self, 
                 default_ttl: float = 300,  # 5 minutes
                 max_size: int = 1000,
                 max_memory_mb: int = 100,
                 cleanup_interval: float = 60):
        """
        Initialize cache service.
        
        Args:
            default_ttl: Default time-to-live in seconds
            max_size: Maximum number of cache entries
            max_memory_mb: Maximum memory usage in MB
            cleanup_interval: Cleanup interval in seconds
        """
        self.default_ttl = default_ttl
        self.max_size = max_size
        self.max_memory_bytes = max_memory_mb * 1024 * 1024
        self.cleanup_interval = cleanup_interval
        
        self._cache: Dict[str, CacheEntry] = {}
        self._stats = CacheStats()
        self._lock = threading.RLock()
        self._logger = logging.getLogger(__name__)
        
        # Start cleanup thread
        self._cleanup_thread = threading.Thread(
            target=self._periodic_cleanup,
            daemon=True
        )
        self._cleanup_thread.start()
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found/expired
        """
        with self._lock:
            if key not in self._cache:
                self._stats.misses += 1
                return None
            
            entry = self._cache[key]
            
            if entry.is_expired():
                del self._cache[key]
                self._stats.misses += 1
                self._stats.evictions += 1
                return None
            
            self._stats.hits += 1
            return entry.access()
    
    def set(self, key: str, value: Any, ttl: Optional[float] = None) -> None:
        """Set value in cache.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time-to-live in seconds (uses default if None)
        """
        if ttl is None:
            ttl = self.default_ttl
        
        # Calculate approximate size
        size = self._estimate_size(value)
        
        with self._lock:
            # Check memory limits
            if self._would_exceed_memory(size):
                self._evict_lru()
            
            # Check size limits
            if len(self._cache) >= self.max_size:
                self._evict_lru()
            
            entry = CacheEntry(value, ttl, size)
            self._cache[key] = entry
            self._stats.memory_usage += size
    
    def delete(self, key: str) -> bool:
        """Delete entry from cache.
        
        Args:
            key: Cache key
            
        Returns:
            True if entry was deleted, False if not found
        """
        with self._lock:
            if key in self._cache:
                entry = self._cache.pop(key)
                self._stats.memory_usage -= entry.size
                self._stats.evictions += 1
                return True
            return False
    
    def clear(self) -> None:
        """Clear all cache entries."""
        with self._lock:
            self._cache.clear()
            self._stats = CacheStats()
    
    def get_stats(self) -> CacheStats:
        """Get cache statistics."""
        with self._lock:
            return CacheStats(
                hits=self._stats.hits,
                misses=self._stats.misses,
                evictions=self._stats.evictions,
                memory_usage=self._stats.memory_usage
            )
    
    def get_or_set(self, key: str, factory: Callable[[], Any], 
                   ttl: Optional[float] = None) -> Any:
        """Get value from cache or compute and cache it.
        
        Args:
            key: Cache key
            factory: Function to compute value if not cached
            ttl: Time-to-live in seconds
            
        Returns:
            Cached or computed value
        """
        value = self.get(key)
        if value is not None:
            return value
        
        # Compute value
        value = factory()
        self.set(key, value, ttl)
        return value
    
    def mget(self, keys: list) -> Dict[str, Any]:
        """Get multiple values from cache.
        
        Args:
            keys: List of cache keys
            
        Returns:
            Dictionary of key-value pairs for found entries
        """
        result = {}
        for key in keys:
            value = self.get(key)
            if value is not None:
                result[key] = value
        return result
    
    def mset(self, items: Dict[str, Any], ttl: Optional[float] = None) -> None:
        """Set multiple values in cache.
        
        Args:
            items: Dictionary of key-value pairs
            ttl: Time-to-live in seconds
        """
        for key, value in items.items():
            self.set(key, value, ttl)
    
    def invalidate_pattern(self, pattern: str) -> int:
        """Invalidate cache entries matching pattern.
        
        Args:
            pattern: Pattern to match (supports * wildcard)
            
        Returns:
            Number of entries invalidated
        """
        import fnmatch
        
        with self._lock:
            keys_to_delete = [
                key for key in self._cache.keys()
                if fnmatch.fnmatch(key, pattern)
            ]
            
            for key in keys_to_delete:
                self.delete(key)
            
            return len(keys_to_delete)
    
    def _estimate_size(self, value: Any) -> int:
        """Estimate memory size of value."""
        try:
            if isinstance(value, (str, bytes)):
                return len(value)
            elif isinstance(value, (int, float, bool)):
                return 8
            elif isinstance(value, (list, tuple)):
                return sum(self._estimate_size(item) for item in value)
            elif isinstance(value, dict):
                return sum(
                    self._estimate_size(k) + self._estimate_size(v)
                    for k, v in value.items()
                )
            else:
                # Fallback to JSON serialization size
                return len(json.dumps(value, default=str))
        except Exception:
            return 1024  # Default estimate
    
    def _would_exceed_memory(self, additional_size: int) -> bool:
        """Check if adding size would exceed memory limit."""
        return self._stats.memory_usage + additional_size > self.max_memory_bytes
    
    def _evict_lru(self) -> None:
        """Evict least recently used entry."""
        if not self._cache:
            return
        
        # Find LRU entry
        lru_key = min(
            self._cache.keys(),
            key=lambda k: self._cache[k].last_access
        )
        
        entry = self._cache.pop(lru_key)
        self._stats.memory_usage -= entry.size
        self._stats.evictions += 1
        
        self._logger.debug(f"Evicted LRU entry: {lru_key}")
    
    def _periodic_cleanup(self) -> None:
        """Periodic cleanup of expired entries."""
        while True:
            try:
                time.sleep(self.cleanup_interval)
                self._cleanup_expired()
            except Exception as e:
                self._logger.error(f"Error in cache cleanup: {e}")
    
    def _cleanup_expired(self) -> None:
        """Remove expired entries."""
        with self._lock:
            expired_keys = [
                key for key, entry in self._cache.items()
                if entry.is_expired()
            ]
            
            for key in expired_keys:
                entry = self._cache.pop(key)
                self._stats.memory_usage -= entry.size
                self._stats.evictions += 1
            
            if expired_keys:
                self._logger.debug(f"Cleaned up {len(expired_keys)} expired entries")


class CacheDecorator:
    """Decorator for caching function results."""
    
    def __init__(self, cache: CacheService, ttl: Optional[float] = None,
                 key_func: Optional[Callable] = None):
        self.cache = cache
        self.ttl = ttl
        self.key_func = key_func or self._default_key_func
    
    def __call__(self, func: Callable) -> Callable:
        def wrapper(*args, **kwargs):
            # Generate cache key
            key = self.key_func(func.__name__, args, kwargs)
            
            # Try to get from cache
            result = self.cache.get(key)
            if result is not None:
                return result
            
            # Compute and cache result
            result = func(*args, **kwargs)
            self.cache.set(key, result, self.ttl)
            return result
        
        wrapper.__name__ = func.__name__
        wrapper.__doc__ = func.__doc__
        return wrapper
    
    def _default_key_func(self, func_name: str, args: tuple, kwargs: dict) -> str:
        """Generate default cache key."""
        key_data = {
            'func': func_name,
            'args': args,
            'kwargs': sorted(kwargs.items())
        }
        key_str = json.dumps(key_data, sort_keys=True, default=str)
        return hashlib.md5(key_str.encode()).hexdigest()


# Global cache instance
_global_cache = None


def get_cache() -> CacheService:
    """Get global cache instance."""
    global _global_cache
    if _global_cache is None:
        _global_cache = CacheService()
    return _global_cache


def cached(ttl: Optional[float] = None, key_func: Optional[Callable] = None):
    """Decorator for caching function results.
    
    Args:
        ttl: Time-to-live in seconds
        key_func: Custom key generation function
    """
    return CacheDecorator(get_cache(), ttl, key_func)