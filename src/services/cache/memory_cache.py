"""Memory cache implementation with weak references and memory optimization.

Provides specialized caching for UI components and large objects.
"""

import gc
import weakref
import threading
import time
from typing import Any, Optional, Dict, Set, Callable
from dataclasses import dataclass
import logging
import psutil
import os


@dataclass
class MemoryStats:
    """Memory usage statistics."""
    process_memory_mb: float
    cache_entries: int
    weak_references: int
    gc_collections: int
    last_cleanup: float


class WeakValueCache:
    """Cache using weak references to prevent memory leaks."""
    
    def __init__(self):
        self._cache: Dict[str, weakref.ref] = {}
        self._lock = threading.RLock()
        self._callbacks: Dict[str, Callable] = {}
    
    def set(self, key: str, value: Any, callback: Optional[Callable] = None) -> None:
        """Set value with weak reference.
        
        Args:
            key: Cache key
            value: Value to cache (must be weakly referenceable)
            callback: Optional callback when object is garbage collected
        """
        def cleanup_callback(ref):
            with self._lock:
                if key in self._cache and self._cache[key] is ref:
                    del self._cache[key]
                if callback:
                    callback(key)
        
        with self._lock:
            try:
                self._cache[key] = weakref.ref(value, cleanup_callback)
                if callback:
                    self._callbacks[key] = callback
            except TypeError:
                # Object is not weakly referenceable
                raise ValueError(f"Object of type {type(value)} is not weakly referenceable")
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from weak reference cache."""
        with self._lock:
            if key not in self._cache:
                return None
            
            ref = self._cache[key]
            value = ref()
            
            if value is None:
                # Object was garbage collected
                del self._cache[key]
                if key in self._callbacks:
                    del self._callbacks[key]
                return None
            
            return value
    
    def delete(self, key: str) -> bool:
        """Delete entry from cache."""
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                if key in self._callbacks:
                    del self._callbacks[key]
                return True
            return False
    
    def clear(self) -> None:
        """Clear all entries."""
        with self._lock:
            self._cache.clear()
            self._callbacks.clear()
    
    def keys(self) -> Set[str]:
        """Get all valid keys."""
        with self._lock:
            valid_keys = set()
            for key in list(self._cache.keys()):
                if self.get(key) is not None:
                    valid_keys.add(key)
            return valid_keys


class MemoryCache:
    """Advanced memory cache with monitoring and optimization."""
    
    def __init__(self, 
                 memory_limit_mb: int = 200,
                 gc_threshold: float = 0.8,
                 monitor_interval: float = 30):
        """
        Initialize memory cache.
        
        Args:
            memory_limit_mb: Memory limit in MB
            gc_threshold: GC trigger threshold (0.0-1.0)
            monitor_interval: Memory monitoring interval in seconds
        """
        self.memory_limit_bytes = memory_limit_mb * 1024 * 1024
        self.gc_threshold = gc_threshold
        self.monitor_interval = monitor_interval
        
        self._weak_cache = WeakValueCache()
        self._strong_cache: Dict[str, Any] = {}
        self._cache_sizes: Dict[str, int] = {}
        self._access_times: Dict[str, float] = {}
        
        self._lock = threading.RLock()
        self._logger = logging.getLogger(__name__)
        self._gc_count = 0
        self._last_cleanup = time.time()
        
        # Start memory monitor
        self._monitor_thread = threading.Thread(
            target=self._memory_monitor,
            daemon=True
        )
        self._monitor_thread.start()
    
    def set_weak(self, key: str, value: Any, 
                 cleanup_callback: Optional[Callable] = None) -> None:
        """Set value using weak reference.
        
        Args:
            key: Cache key
            value: Value to cache
            cleanup_callback: Optional cleanup callback
        """
        try:
            self._weak_cache.set(key, value, cleanup_callback)
            self._access_times[key] = time.time()
        except ValueError as e:
            self._logger.warning(f"Cannot cache {key} with weak reference: {e}")
    
    def set_strong(self, key: str, value: Any, size_hint: Optional[int] = None) -> None:
        """Set value using strong reference.
        
        Args:
            key: Cache key
            value: Value to cache
            size_hint: Optional size hint in bytes
        """
        with self._lock:
            # Estimate size if not provided
            if size_hint is None:
                size_hint = self._estimate_size(value)
            
            # Check if we need to free memory
            if self._would_exceed_limit(size_hint):
                self._free_memory(size_hint)
            
            self._strong_cache[key] = value
            self._cache_sizes[key] = size_hint
            self._access_times[key] = time.time()
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache (tries weak then strong)."""
        # Try weak cache first
        value = self._weak_cache.get(key)
        if value is not None:
            self._access_times[key] = time.time()
            return value
        
        # Try strong cache
        with self._lock:
            if key in self._strong_cache:
                self._access_times[key] = time.time()
                return self._strong_cache[key]
        
        return None
    
    def delete(self, key: str) -> bool:
        """Delete entry from cache."""
        deleted = False
        
        # Delete from weak cache
        if self._weak_cache.delete(key):
            deleted = True
        
        # Delete from strong cache
        with self._lock:
            if key in self._strong_cache:
                del self._strong_cache[key]
                if key in self._cache_sizes:
                    del self._cache_sizes[key]
                deleted = True
            
            if key in self._access_times:
                del self._access_times[key]
        
        return deleted
    
    def clear(self) -> None:
        """Clear all caches."""
        self._weak_cache.clear()
        with self._lock:
            self._strong_cache.clear()
            self._cache_sizes.clear()
            self._access_times.clear()
    
    def force_gc(self) -> int:
        """Force garbage collection.
        
        Returns:
            Number of objects collected
        """
        collected = gc.collect()
        self._gc_count += 1
        self._last_cleanup = time.time()
        self._logger.debug(f"Forced GC collected {collected} objects")
        return collected
    
    def get_memory_stats(self) -> MemoryStats:
        """Get memory usage statistics."""
        process = psutil.Process(os.getpid())
        memory_mb = process.memory_info().rss / 1024 / 1024
        
        with self._lock:
            return MemoryStats(
                process_memory_mb=memory_mb,
                cache_entries=len(self._strong_cache),
                weak_references=len(self._weak_cache.keys()),
                gc_collections=self._gc_count,
                last_cleanup=self._last_cleanup
            )
    
    def optimize_memory(self) -> Dict[str, int]:
        """Optimize memory usage.
        
        Returns:
            Dictionary with optimization results
        """
        stats_before = self.get_memory_stats()
        
        # Clean up weak references
        weak_keys = list(self._weak_cache.keys())
        for key in weak_keys:
            self._weak_cache.get(key)  # This will clean up dead references
        
        # Remove old entries from strong cache
        with self._lock:
            current_time = time.time()
            old_keys = [
                key for key, access_time in self._access_times.items()
                if current_time - access_time > 3600  # 1 hour
            ]
            
            for key in old_keys:
                if key in self._strong_cache:
                    del self._strong_cache[key]
                if key in self._cache_sizes:
                    del self._cache_sizes[key]
                del self._access_times[key]
        
        # Force garbage collection
        collected = self.force_gc()
        
        stats_after = self.get_memory_stats()
        
        return {
            'weak_references_cleaned': len(weak_keys) - stats_after.weak_references,
            'strong_entries_removed': len(old_keys),
            'objects_collected': collected,
            'memory_freed_mb': stats_before.process_memory_mb - stats_after.process_memory_mb
        }
    
    def _estimate_size(self, value: Any) -> int:
        """Estimate memory size of value."""
        import sys
        
        try:
            return sys.getsizeof(value)
        except Exception:
            return 1024  # Default estimate
    
    def _would_exceed_limit(self, additional_size: int) -> bool:
        """Check if adding size would exceed memory limit."""
        current_size = sum(self._cache_sizes.values())
        return current_size + additional_size > self.memory_limit_bytes
    
    def _free_memory(self, needed_size: int) -> None:
        """Free memory by removing LRU entries."""
        with self._lock:
            # Sort by access time (oldest first)
            sorted_keys = sorted(
                self._strong_cache.keys(),
                key=lambda k: self._access_times.get(k, 0)
            )
            
            freed_size = 0
            for key in sorted_keys:
                if freed_size >= needed_size:
                    break
                
                if key in self._cache_sizes:
                    freed_size += self._cache_sizes[key]
                    del self._cache_sizes[key]
                
                del self._strong_cache[key]
                if key in self._access_times:
                    del self._access_times[key]
                
                self._logger.debug(f"Freed memory by removing cache entry: {key}")
    
    def _memory_monitor(self) -> None:
        """Monitor memory usage and trigger cleanup."""
        while True:
            try:
                time.sleep(self.monitor_interval)
                
                process = psutil.Process(os.getpid())
                memory_percent = process.memory_percent()
                
                if memory_percent > self.gc_threshold * 100:
                    self._logger.info(f"Memory usage {memory_percent:.1f}%, triggering optimization")
                    self.optimize_memory()
                
            except Exception as e:
                self._logger.error(f"Error in memory monitor: {e}")


# Global memory cache instance
_global_memory_cache = None


def get_memory_cache() -> MemoryCache:
    """Get global memory cache instance."""
    global _global_memory_cache
    if _global_memory_cache is None:
        _global_memory_cache = MemoryCache()
    return _global_memory_cache


def cache_ui_component(key: str, component: Any) -> None:
    """Cache UI component with weak reference.
    
    Args:
        key: Cache key
        component: UI component to cache
    """
    cache = get_memory_cache()
    
    def cleanup_callback(cache_key):
        logging.getLogger(__name__).debug(f"UI component {cache_key} was garbage collected")
    
    cache.set_weak(key, component, cleanup_callback)


def get_ui_component(key: str) -> Optional[Any]:
    """Get cached UI component.
    
    Args:
        key: Cache key
        
    Returns:
        Cached component or None
    """
    return get_memory_cache().get(key)