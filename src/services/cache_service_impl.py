#!/usr/bin/env python3
"""
Cache Service Implementation for Dependency Injection

This module provides the concrete implementation of ICacheService interface,
creating a comprehensive caching system that works with the dependency injection system.
It demonstrates professional caching patterns and best practices.

Author: Eric Hunter (Cortana Builder Agent)
Version: 1.0.0 (Dependency Injection Implementation)
"""

import json
import pickle
import time
from typing import Any, Dict, List, Optional, Union
from pathlib import Path
from datetime import datetime, timedelta
import threading
from dataclasses import dataclass, asdict

from core.interfaces import ICacheService, ILoggingService


@dataclass
class CacheEntry:
    """Represents a cache entry with metadata.
    
    This class encapsulates cached data along with its metadata,
    including expiration time, access count, and creation timestamp.
    """
    key: str
    value: Any
    created_at: float
    expires_at: Optional[float]
    access_count: int = 0
    last_accessed: Optional[float] = None
    
    def is_expired(self) -> bool:
        """Check if the cache entry has expired.
        
        Returns:
            True if expired, False otherwise
        """
        if self.expires_at is None:
            return False
        return time.time() > self.expires_at
    
    def touch(self) -> None:
        """Update access metadata."""
        self.access_count += 1
        self.last_accessed = time.time()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert cache entry to dictionary.
        
        Returns:
            Dictionary representation of cache entry
        """
        return asdict(self)


class CacheServiceImpl(ICacheService):
    """Implementation of ICacheService with comprehensive caching capabilities.
    
    This implementation provides both in-memory and file-based caching
    with TTL support, LRU eviction, and thread-safe operations.
    It demonstrates how to create a production-ready cache service.
    """
    
    def __init__(self, 
                 logger: Optional[ILoggingService] = None,
                 max_memory_entries: int = 1000,
                 default_ttl_seconds: int = 3600,
                 file_cache_dir: Optional[str] = None,
                 enable_file_cache: bool = True):
        """Initialize the cache service implementation.
        
        Args:
            logger: Optional logging service
            max_memory_entries: Maximum number of entries in memory cache
            default_ttl_seconds: Default time-to-live in seconds
            file_cache_dir: Directory for file-based cache
            enable_file_cache: Whether to enable file-based caching
        """
        self._logger = logger
        self._max_memory_entries = max_memory_entries
        self._default_ttl = default_ttl_seconds
        self._enable_file_cache = enable_file_cache
        
        # In-memory cache storage
        self._memory_cache: Dict[str, CacheEntry] = {}
        self._access_order: List[str] = []  # For LRU eviction
        self._lock = threading.RLock()  # Thread-safe operations
        
        # File cache setup
        if enable_file_cache:
            self._file_cache_dir = Path(file_cache_dir or "cache")
            self._file_cache_dir.mkdir(parents=True, exist_ok=True)
        else:
            self._file_cache_dir = None
        
        # Statistics
        self._stats = {
            'hits': 0,
            'misses': 0,
            'sets': 0,
            'deletes': 0,
            'evictions': 0,
            'expired_cleanups': 0
        }
        
        self._log_info("CacheServiceImpl initialized", 
                      max_entries=max_memory_entries,
                      default_ttl=default_ttl_seconds,
                      file_cache_enabled=enable_file_cache)
    
    def _log_debug(self, message: str, **kwargs) -> None:
        """Log debug message if logger available."""
        if self._logger:
            self._logger.debug(message, **kwargs)
    
    def _log_info(self, message: str, **kwargs) -> None:
        """Log info message if logger available."""
        if self._logger:
            self._logger.info(message, **kwargs)
    
    def _log_warning(self, message: str, **kwargs) -> None:
        """Log warning message if logger available."""
        if self._logger:
            self._logger.warning(message, **kwargs)
    
    def _log_error(self, message: str, **kwargs) -> None:
        """Log error message if logger available."""
        if self._logger:
            self._logger.error(message, **kwargs)
    
    def _clean_expired_entries(self) -> int:
        """Clean expired entries from memory cache.
        
        Returns:
            Number of expired entries removed
        """
        expired_keys = []
        current_time = time.time()
        
        for key, entry in self._memory_cache.items():
            if entry.is_expired():
                expired_keys.append(key)
        
        for key in expired_keys:
            del self._memory_cache[key]
            if key in self._access_order:
                self._access_order.remove(key)
        
        if expired_keys:
            self._stats['expired_cleanups'] += len(expired_keys)
            self._log_debug(f"Cleaned {len(expired_keys)} expired cache entries")
        
        return len(expired_keys)
    
    def _evict_lru_entries(self, count: int = 1) -> int:
        """Evict least recently used entries.
        
        Args:
            count: Number of entries to evict
            
        Returns:
            Number of entries actually evicted
        """
        evicted = 0
        
        while evicted < count and self._access_order:
            # Get least recently used key
            lru_key = self._access_order[0]
            
            # Remove from cache and access order
            if lru_key in self._memory_cache:
                del self._memory_cache[lru_key]
                evicted += 1
            
            self._access_order.remove(lru_key)
        
        if evicted > 0:
            self._stats['evictions'] += evicted
            self._log_debug(f"Evicted {evicted} LRU cache entries")
        
        return evicted
    
    def _update_access_order(self, key: str) -> None:
        """Update access order for LRU tracking.
        
        Args:
            key: Cache key that was accessed
        """
        if key in self._access_order:
            self._access_order.remove(key)
        self._access_order.append(key)
    
    def _get_file_cache_path(self, key: str) -> Optional[Path]:
        """Get file path for cache key.
        
        Args:
            key: Cache key
            
        Returns:
            Path to cache file or None if file cache disabled
        """
        if not self._file_cache_dir:
            return None
        
        # Create safe filename from key
        safe_key = key.replace('/', '_').replace('\\', '_').replace(':', '_')
        return self._file_cache_dir / f"{safe_key}.cache"
    
    def _save_to_file_cache(self, key: str, entry: CacheEntry) -> bool:
        """Save cache entry to file.
        
        Args:
            key: Cache key
            entry: Cache entry to save
            
        Returns:
            True if saved successfully, False otherwise
        """
        if not self._enable_file_cache:
            return False
        
        try:
            file_path = self._get_file_cache_path(key)
            if file_path:
                with open(file_path, 'wb') as f:
                    pickle.dump(entry, f)
                return True
        except Exception as e:
            self._log_error(f"Error saving to file cache: {e}", key=key)
        
        return False
    
    def _load_from_file_cache(self, key: str) -> Optional[CacheEntry]:
        """Load cache entry from file.
        
        Args:
            key: Cache key
            
        Returns:
            Cache entry if found and valid, None otherwise
        """
        if not self._enable_file_cache:
            return None
        
        try:
            file_path = self._get_file_cache_path(key)
            if file_path and file_path.exists():
                with open(file_path, 'rb') as f:
                    entry = pickle.load(f)
                
                # Check if entry is expired
                if entry.is_expired():
                    file_path.unlink()  # Delete expired file
                    return None
                
                return entry
        except Exception as e:
            self._log_error(f"Error loading from file cache: {e}", key=key)
        
        return None
    
    def _delete_from_file_cache(self, key: str) -> bool:
        """Delete cache entry file.
        
        Args:
            key: Cache key
            
        Returns:
            True if deleted successfully, False otherwise
        """
        if not self._enable_file_cache:
            return False
        
        try:
            file_path = self._get_file_cache_path(key)
            if file_path and file_path.exists():
                file_path.unlink()
                return True
        except Exception as e:
            self._log_error(f"Error deleting from file cache: {e}", key=key)
        
        return False
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found/expired
        """
        with self._lock:
            # Clean expired entries periodically
            if len(self._memory_cache) % 100 == 0:
                self._clean_expired_entries()
            
            # Check memory cache first
            if key in self._memory_cache:
                entry = self._memory_cache[key]
                
                if entry.is_expired():
                    del self._memory_cache[key]
                    if key in self._access_order:
                        self._access_order.remove(key)
                    self._stats['misses'] += 1
                    return None
                
                # Update access metadata
                entry.touch()
                self._update_access_order(key)
                self._stats['hits'] += 1
                
                self._log_debug(f"Cache hit (memory): {key}")
                return entry.value
            
            # Check file cache if enabled
            if self._enable_file_cache:
                entry = self._load_from_file_cache(key)
                if entry:
                    # Move to memory cache
                    entry.touch()
                    self._memory_cache[key] = entry
                    self._update_access_order(key)
                    self._stats['hits'] += 1
                    
                    self._log_debug(f"Cache hit (file): {key}")
                    return entry.value
            
            self._stats['misses'] += 1
            self._log_debug(f"Cache miss: {key}")
            return None
    
    def set(self, key: str, value: Any, ttl_seconds: Optional[int] = None) -> bool:
        """Set value in cache.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl_seconds: Time-to-live in seconds (None for default)
            
        Returns:
            True if set successfully, False otherwise
        """
        try:
            with self._lock:
                # Calculate expiration time
                ttl = ttl_seconds if ttl_seconds is not None else self._default_ttl
                expires_at = time.time() + ttl if ttl > 0 else None
                
                # Create cache entry
                entry = CacheEntry(
                    key=key,
                    value=value,
                    created_at=time.time(),
                    expires_at=expires_at
                )
                
                # Check if we need to evict entries
                if len(self._memory_cache) >= self._max_memory_entries:
                    # Clean expired entries first
                    cleaned = self._clean_expired_entries()
                    
                    # If still at capacity, evict LRU entries
                    if len(self._memory_cache) >= self._max_memory_entries:
                        self._evict_lru_entries(1)
                
                # Add to memory cache
                self._memory_cache[key] = entry
                self._update_access_order(key)
                
                # Save to file cache if enabled
                if self._enable_file_cache:
                    self._save_to_file_cache(key, entry)
                
                self._stats['sets'] += 1
                self._log_debug(f"Cache set: {key}", ttl=ttl)
                
                return True
                
        except Exception as e:
            self._log_error(f"Error setting cache value: {e}", key=key)
            return False
    
    def delete(self, key: str) -> bool:
        """Delete value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            True if deleted successfully, False if not found
        """
        with self._lock:
            deleted = False
            
            # Delete from memory cache
            if key in self._memory_cache:
                del self._memory_cache[key]
                deleted = True
            
            # Remove from access order
            if key in self._access_order:
                self._access_order.remove(key)
            
            # Delete from file cache
            if self._enable_file_cache:
                file_deleted = self._delete_from_file_cache(key)
                deleted = deleted or file_deleted
            
            if deleted:
                self._stats['deletes'] += 1
                self._log_debug(f"Cache delete: {key}")
            
            return deleted
    
    def exists(self, key: str) -> bool:
        """Check if key exists in cache.
        
        Args:
            key: Cache key
            
        Returns:
            True if key exists and not expired, False otherwise
        """
        return self.get(key) is not None
    
    def clear(self) -> bool:
        """Clear all cache entries.
        
        Returns:
            True if cleared successfully, False otherwise
        """
        try:
            with self._lock:
                # Clear memory cache
                memory_count = len(self._memory_cache)
                self._memory_cache.clear()
                self._access_order.clear()
                
                # Clear file cache
                file_count = 0
                if self._enable_file_cache and self._file_cache_dir:
                    for cache_file in self._file_cache_dir.glob("*.cache"):
                        try:
                            cache_file.unlink()
                            file_count += 1
                        except Exception as e:
                            self._log_error(f"Error deleting cache file: {e}", file=str(cache_file))
                
                self._log_info(f"Cache cleared", 
                              memory_entries=memory_count,
                              file_entries=file_count)
                
                return True
                
        except Exception as e:
            self._log_error(f"Error clearing cache: {e}")
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics.
        
        Returns:
            Dictionary containing cache statistics
        """
        with self._lock:
            total_requests = self._stats['hits'] + self._stats['misses']
            hit_rate = (self._stats['hits'] / total_requests * 100) if total_requests > 0 else 0
            
            stats = {
                'memory_entries': len(self._memory_cache),
                'max_memory_entries': self._max_memory_entries,
                'memory_usage_percent': (len(self._memory_cache) / self._max_memory_entries * 100),
                'hits': self._stats['hits'],
                'misses': self._stats['misses'],
                'hit_rate_percent': round(hit_rate, 2),
                'sets': self._stats['sets'],
                'deletes': self._stats['deletes'],
                'evictions': self._stats['evictions'],
                'expired_cleanups': self._stats['expired_cleanups'],
                'file_cache_enabled': self._enable_file_cache,
                'default_ttl_seconds': self._default_ttl
            }
            
            # Add file cache stats if enabled
            if self._enable_file_cache and self._file_cache_dir:
                file_count = len(list(self._file_cache_dir.glob("*.cache")))
                stats['file_entries'] = file_count
            
            return stats
    
    def get_keys(self) -> List[str]:
        """Get all cache keys.
        
        Returns:
            List of cache keys
        """
        with self._lock:
            # Clean expired entries first
            self._clean_expired_entries()
            return list(self._memory_cache.keys())
    
    def get_size(self) -> int:
        """Get number of cache entries.
        
        Returns:
            Number of cache entries
        """
        with self._lock:
            # Clean expired entries first
            self._clean_expired_entries()
            return len(self._memory_cache)
    
    def set_ttl(self, key: str, ttl_seconds: int) -> bool:
        """Update TTL for existing cache entry.
        
        Args:
            key: Cache key
            ttl_seconds: New time-to-live in seconds
            
        Returns:
            True if TTL updated successfully, False if key not found
        """
        with self._lock:
            if key in self._memory_cache:
                entry = self._memory_cache[key]
                entry.expires_at = time.time() + ttl_seconds if ttl_seconds > 0 else None
                
                # Update file cache if enabled
                if self._enable_file_cache:
                    self._save_to_file_cache(key, entry)
                
                self._log_debug(f"Cache TTL updated: {key}", ttl=ttl_seconds)
                return True
            
            return False
    
    def get_ttl(self, key: str) -> Optional[int]:
        """Get remaining TTL for cache entry.
        
        Args:
            key: Cache key
            
        Returns:
            Remaining TTL in seconds or None if key not found/no expiration
        """
        with self._lock:
            if key in self._memory_cache:
                entry = self._memory_cache[key]
                if entry.expires_at is None:
                    return None
                
                remaining = entry.expires_at - time.time()
                return max(0, int(remaining))
            
            return None


class MockCacheService(ICacheService):
    """Mock cache service implementation for testing.
    
    This class provides a mock implementation of ICacheService
    that can be used for unit testing and development scenarios.
    """
    
    def __init__(self, should_fail: bool = False):
        """Initialize the mock cache service.
        
        Args:
            should_fail: Whether to simulate failures
        """
        self._cache: Dict[str, Any] = {}
        self._should_fail = should_fail
        self._stats = {'hits': 0, 'misses': 0, 'sets': 0, 'deletes': 0}
        
        print("MockCacheService initialized")
    
    def set_should_fail(self, should_fail: bool) -> None:
        """Set whether the service should simulate failures.
        
        Args:
            should_fail: Whether to simulate failures
        """
        self._should_fail = should_fail
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from mock cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None
        """
        if self._should_fail:
            return None
        
        if key in self._cache:
            self._stats['hits'] += 1
            return self._cache[key]
        
        self._stats['misses'] += 1
        return None
    
    def set(self, key: str, value: Any, ttl_seconds: Optional[int] = None) -> bool:
        """Set value in mock cache.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl_seconds: Time-to-live (ignored in mock)
            
        Returns:
            True unless simulating failure
        """
        if self._should_fail:
            return False
        
        self._cache[key] = value
        self._stats['sets'] += 1
        return True
    
    def delete(self, key: str) -> bool:
        """Delete value from mock cache.
        
        Args:
            key: Cache key
            
        Returns:
            True if deleted, False if not found or simulating failure
        """
        if self._should_fail:
            return False
        
        if key in self._cache:
            del self._cache[key]
            self._stats['deletes'] += 1
            return True
        
        return False
    
    def exists(self, key: str) -> bool:
        """Check if key exists in mock cache.
        
        Args:
            key: Cache key
            
        Returns:
            True if exists, False otherwise
        """
        if self._should_fail:
            return False
        
        return key in self._cache
    
    def clear(self) -> bool:
        """Clear mock cache.
        
        Returns:
            True unless simulating failure
        """
        if self._should_fail:
            return False
        
        self._cache.clear()
        return True
    
    def get_stats(self) -> Dict[str, Any]:
        """Get mock cache statistics.
        
        Returns:
            Dictionary containing mock statistics
        """
        if self._should_fail:
            return {}
        
        total_requests = self._stats['hits'] + self._stats['misses']
        hit_rate = (self._stats['hits'] / total_requests * 100) if total_requests > 0 else 0
        
        return {
            'entries': len(self._cache),
            'hits': self._stats['hits'],
            'misses': self._stats['misses'],
            'hit_rate_percent': round(hit_rate, 2),
            'sets': self._stats['sets'],
            'deletes': self._stats['deletes'],
            'mock_service': True,
            'should_fail': self._should_fail
        }
    
    def get_keys(self) -> List[str]:
        """Get all mock cache keys.
        
        Returns:
            List of cache keys
        """
        if self._should_fail:
            return []
        
        return list(self._cache.keys())
    
    def get_size(self) -> int:
        """Get number of mock cache entries.
        
        Returns:
            Number of cache entries
        """
        if self._should_fail:
            return 0
        
        return len(self._cache)
    
    def set_ttl(self, key: str, ttl_seconds: int) -> bool:
        """Update TTL for mock cache entry.
        
        Args:
            key: Cache key
            ttl_seconds: New time-to-live
            
        Returns:
            True if key exists, False otherwise
        """
        if self._should_fail:
            return False
        
        return key in self._cache
    
    def get_ttl(self, key: str) -> Optional[int]:
        """Get remaining TTL for mock cache entry.
        
        Args:
            key: Cache key
            
        Returns:
            Mock TTL value or None
        """
        if self._should_fail or key not in self._cache:
            return None
        
        return 3600  # Mock TTL value