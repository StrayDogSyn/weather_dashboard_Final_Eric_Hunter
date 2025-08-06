"""Cache services for performance optimization.

Provides memory and file-based caching with TTL and automatic cleanup.
"""

from .cache_service import CacheService, CacheStats, CacheEntry, CacheDecorator, get_cache
from .memory_cache import MemoryCache, WeakValueCache, get_memory_cache, cache_ui_component, get_ui_component
from .file_cache import FileCache, FileCacheEntry, get_file_cache
from .cache_manager import (
    CacheManager, CacheLevel, CachePolicy, 
    CacheDecorator as ManagerDecorator, 
    get_cache_manager, cache, 
    cached_api_call, cached_computation, cached_image
)

__all__ = [
    # Core cache services
    'CacheService',
    'CacheStats', 
    'CacheEntry',
    'CacheDecorator',
    'get_cache',
    
    # Memory cache
    'MemoryCache',
    'WeakValueCache', 
    'get_memory_cache',
    'cache_ui_component',
    'get_ui_component',
    
    # File cache
    'FileCache',
    'FileCacheEntry',
    'get_file_cache',
    
    # Cache manager
    'CacheManager',
    'CacheLevel',
    'CachePolicy', 
    'ManagerDecorator',
    'get_cache_manager',
    'cache',
    'cached_api_call',
    'cached_computation', 
    'cached_image'
]