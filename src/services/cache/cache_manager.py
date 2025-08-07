"""Cache manager for coordinating multiple cache layers.

Provides unified interface for memory and file caching with intelligent routing.
"""

import time
import threading
import logging
from typing import Any, Optional, Dict, List, Union, Callable
from dataclasses import dataclass
from enum import Enum

from .cache_service import CacheService, CacheStats
from .memory_cache import MemoryCache, get_memory_cache
from .file_cache import FileCache, get_file_cache


class CacheLevel(Enum):
    """Cache level enumeration."""
    MEMORY_ONLY = "memory_only"
    FILE_ONLY = "file_only"
    BOTH = "both"
    AUTO = "auto"


@dataclass
class CachePolicy:
    """Cache policy configuration."""
    level: CacheLevel = CacheLevel.AUTO
    memory_ttl: float = 300  # 5 minutes
    file_ttl: float = 3600   # 1 hour
    memory_threshold: int = 1024  # Use file cache for objects > 1KB
    compress_file: bool = True
    

class CacheManager:
    """Unified cache manager with multiple cache layers."""
    
    def __init__(self,
                 memory_cache: Optional[MemoryCache] = None,
                 file_cache: Optional[FileCache] = None,
                 default_policy: Optional[CachePolicy] = None):
        """
        Initialize cache manager.
        
        Args:
            memory_cache: Memory cache instance
            file_cache: File cache instance
            default_policy: Default cache policy
        """
        self.memory_cache = memory_cache or get_memory_cache()
        self.file_cache = file_cache or get_file_cache()
        self.default_policy = default_policy or CachePolicy()
        
        self._lock = threading.RLock()
        self._logger = logging.getLogger(__name__)
        
        # Cache hit/miss statistics
        self._stats = {
            'memory_hits': 0,
            'memory_misses': 0,
            'file_hits': 0,
            'file_misses': 0,
            'total_requests': 0
        }
    
    def get(self, key: str, policy: Optional[CachePolicy] = None) -> Optional[Any]:
        """Get value from cache.
        
        Args:
            key: Cache key
            policy: Cache policy (uses default if None)
            
        Returns:
            Cached value or None if not found
        """
        policy = policy or self.default_policy
        
        with self._lock:
            self._stats['total_requests'] += 1
            
            # Try memory cache first (if enabled)
            if policy.level in (CacheLevel.MEMORY_ONLY, CacheLevel.BOTH, CacheLevel.AUTO):
                value = self.memory_cache.get(key)
                if value is not None:
                    self._stats['memory_hits'] += 1
                    self._logger.debug(f"Memory cache hit for key: {key}")
                    return value
                else:
                    self._stats['memory_misses'] += 1
            
            # Try file cache (if enabled and not memory-only)
            if policy.level in (CacheLevel.FILE_ONLY, CacheLevel.BOTH, CacheLevel.AUTO):
                value = self.file_cache.get(key)
                if value is not None:
                    self._stats['file_hits'] += 1
                    self._logger.debug(f"File cache hit for key: {key}")
                    
                    # Promote to memory cache if using both levels
                    if policy.level in (CacheLevel.BOTH, CacheLevel.AUTO):
                        self.memory_cache.set(key, value, policy.memory_ttl)
                    
                    return value
                else:
                    self._stats['file_misses'] += 1
            
            return None
    
    def set(self, key: str, value: Any, policy: Optional[CachePolicy] = None) -> bool:
        """Set value in cache.
        
        Args:
            key: Cache key
            value: Value to cache
            policy: Cache policy (uses default if None)
            
        Returns:
            True if successfully cached
        """
        policy = policy or self.default_policy
        
        try:
            # Determine cache level based on policy and value size
            cache_level = self._determine_cache_level(value, policy)
            
            success = True
            
            # Cache in memory
            if cache_level in (CacheLevel.MEMORY_ONLY, CacheLevel.BOTH):
                memory_success = self.memory_cache.set(key, value, policy.memory_ttl)
                if memory_success:
                    self._logger.debug(f"Cached in memory: {key}")
                else:
                    self._logger.warning(f"Failed to cache in memory: {key}")
                    success = False
            
            # Cache in file
            if cache_level in (CacheLevel.FILE_ONLY, CacheLevel.BOTH):
                file_success = self.file_cache.set(
                    key, value, policy.file_ttl, policy.compress_file
                )
                if file_success:
                    self._logger.debug(f"Cached in file: {key}")
                else:
                    self._logger.warning(f"Failed to cache in file: {key}")
                    success = False
            
            return success
            
        except Exception as e:
            self._logger.error(f"Error caching {key}: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """Delete value from all cache levels.
        
        Args:
            key: Cache key
            
        Returns:
            True if any cache level had the key
        """
        memory_deleted = self.memory_cache.delete(key)
        file_deleted = self.file_cache.delete(key)
        
        return memory_deleted or file_deleted
    
    def clear(self, level: Optional[CacheLevel] = None) -> None:
        """Clear cache.
        
        Args:
            level: Cache level to clear (all if None)
        """
        if level is None or level in (CacheLevel.MEMORY_ONLY, CacheLevel.BOTH):
            self.memory_cache.clear()
            self._logger.info("Memory cache cleared")
        
        if level is None or level in (CacheLevel.FILE_ONLY, CacheLevel.BOTH):
            self.file_cache.clear()
            self._logger.info("File cache cleared")
        
        # Reset statistics
        with self._lock:
            self._stats = {
                'memory_hits': 0,
                'memory_misses': 0,
                'file_hits': 0,
                'file_misses': 0,
                'total_requests': 0
            }
    
    def get_or_set(self, key: str, factory: Callable[[], Any],
                   policy: Optional[CachePolicy] = None) -> Any:
        """Get value from cache or set using factory function.
        
        Args:
            key: Cache key
            factory: Function to generate value if not cached
            policy: Cache policy
            
        Returns:
            Cached or generated value
        """
        value = self.get(key, policy)
        if value is not None:
            return value
        
        # Generate value
        value = factory()
        self.set(key, value, policy)
        return value
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics.
        
        Returns:
            Dictionary with cache statistics
        """
        with self._lock:
            stats = self._stats.copy()
            
            # Calculate hit rates
            total_memory = stats['memory_hits'] + stats['memory_misses']
            total_file = stats['file_hits'] + stats['file_misses']
            
            if total_memory > 0:
                stats['memory_hit_rate'] = stats['memory_hits'] / total_memory
            else:
                stats['memory_hit_rate'] = 0.0
            
            if total_file > 0:
                stats['file_hit_rate'] = stats['file_hits'] / total_file
            else:
                stats['file_hit_rate'] = 0.0
            
            # Overall hit rate
            total_hits = stats['memory_hits'] + stats['file_hits']
            if stats['total_requests'] > 0:
                stats['overall_hit_rate'] = total_hits / stats['total_requests']
            else:
                stats['overall_hit_rate'] = 0.0
            
            # Add cache info
            stats['memory_cache_info'] = self.memory_cache.get_cache_info()
            stats['file_cache_info'] = self.file_cache.get_cache_info()
            
            return stats
    
    def optimize(self) -> Dict[str, Any]:
        """Optimize all cache levels.
        
        Returns:
            Dictionary with optimization results
        """
        memory_result = self.memory_cache.optimize()
        file_result = self.file_cache.optimize()
        
        return {
            'memory_optimization': memory_result,
            'file_optimization': file_result
        }
    
    def _determine_cache_level(self, value: Any, policy: CachePolicy) -> CacheLevel:
        """Determine appropriate cache level for value.
        
        Args:
            value: Value to cache
            policy: Cache policy
            
        Returns:
            Appropriate cache level
        """
        if policy.level != CacheLevel.AUTO:
            return policy.level
        
        # Estimate value size
        try:
            import sys
            size = sys.getsizeof(value)
            
            # For complex objects, use rough estimation
            if hasattr(value, '__dict__'):
                size += sum(sys.getsizeof(v) for v in value.__dict__.values())
            elif isinstance(value, (list, tuple)):
                size += sum(sys.getsizeof(item) for item in value[:10])  # Sample first 10
            elif isinstance(value, dict):
                size += sum(sys.getsizeof(k) + sys.getsizeof(v) 
                           for k, v in list(value.items())[:10])  # Sample first 10
            
            # Use memory cache for small objects, file cache for large ones
            if size <= policy.memory_threshold:
                return CacheLevel.MEMORY_ONLY
            else:
                return CacheLevel.BOTH  # Large objects go to both for redundancy
                
        except Exception:
            # Default to both if size estimation fails
            return CacheLevel.BOTH


class CacheDecorator:
    """Decorator for caching function results."""
    
    def __init__(self, cache_manager: Optional[CacheManager] = None,
                 policy: Optional[CachePolicy] = None,
                 key_func: Optional[Callable] = None):
        """
        Initialize cache decorator.
        
        Args:
            cache_manager: Cache manager instance
            policy: Cache policy
            key_func: Function to generate cache key
        """
        self.cache_manager = cache_manager or get_cache_manager()
        self.policy = policy or CachePolicy()
        self.key_func = key_func or self._default_key_func
    
    def __call__(self, func: Callable) -> Callable:
        """Decorate function with caching."""
        def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = self.key_func(func, args, kwargs)
            
            # Try to get from cache
            result = self.cache_manager.get(cache_key, self.policy)
            if result is not None:
                return result
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            self.cache_manager.set(cache_key, result, self.policy)
            
            return result
        
        wrapper._cache_manager = self.cache_manager
        wrapper._cache_policy = self.policy
        return wrapper
    
    def _default_key_func(self, func: Callable, args: tuple, kwargs: dict) -> str:
        """Generate default cache key."""
        import hashlib
        import pickle
        
        # Create key from function name and arguments
        key_data = {
            'func': f"{func.__module__}.{func.__name__}",
            'args': args,
            'kwargs': sorted(kwargs.items())
        }
        
        # Hash the key data
        key_bytes = pickle.dumps(key_data)
        return hashlib.md5(key_bytes).hexdigest()


# Global cache manager instance
_global_cache_manager = None


def get_cache_manager() -> CacheManager:
    """Get global cache manager instance."""
    global _global_cache_manager
    if _global_cache_manager is None:
        _global_cache_manager = CacheManager()
    return _global_cache_manager


def cache(policy: Optional[CachePolicy] = None,
          key_func: Optional[Callable] = None) -> CacheDecorator:
    """Decorator for caching function results.
    
    Args:
        policy: Cache policy
        key_func: Function to generate cache key
        
    Returns:
        Cache decorator
    """
    return CacheDecorator(policy=policy, key_func=key_func)


# Convenience functions
def cached_api_call(policy: Optional[CachePolicy] = None):
    """Decorator for caching API calls."""
    api_policy = policy or CachePolicy(
        level=CacheLevel.BOTH,
        memory_ttl=300,  # 5 minutes
        file_ttl=3600    # 1 hour
    )
    return cache(api_policy)


def cached_computation(policy: Optional[CachePolicy] = None):
    """Decorator for caching expensive computations."""
    comp_policy = policy or CachePolicy(
        level=CacheLevel.MEMORY_ONLY,
        memory_ttl=1800  # 30 minutes
    )
    return cache(comp_policy)


def cached_image(policy: Optional[CachePolicy] = None):
    """Decorator for caching image processing results."""
    image_policy = policy or CachePolicy(
        level=CacheLevel.FILE_ONLY,
        file_ttl=7200,  # 2 hours
        compress_file=True
    )
    return cache(image_policy)