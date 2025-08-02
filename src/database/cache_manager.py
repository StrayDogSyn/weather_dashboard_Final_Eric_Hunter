"""Cache manager with TTL and size limits.

Provides thread-safe caching with automatic expiration and size management.
"""

import asyncio
import json
import logging
import threading
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union


class CacheEntry:
    """Represents a cache entry with metadata."""
    
    def __init__(self, key: str, value: Any, ttl: Optional[int] = None):
        """Initialize cache entry.
        
        Args:
            key: Cache key
            value: Cached value
            ttl: Time to live in seconds
        """
        self.key = key
        self.value = value
        self.created_at = time.time()
        self.accessed_at = self.created_at
        self.access_count = 0
        self.ttl = ttl
        self.expires_at = self.created_at + ttl if ttl else None
    
    def is_expired(self) -> bool:
        """Check if entry is expired.
        
        Returns:
            bool: True if expired
        """
        if self.expires_at is None:
            return False
        return time.time() > self.expires_at
    
    def touch(self) -> None:
        """Update access time and count."""
        self.accessed_at = time.time()
        self.access_count += 1
    
    def size_estimate(self) -> int:
        """Estimate memory size of entry.
        
        Returns:
            int: Estimated size in bytes
        """
        try:
            # Simple size estimation
            if isinstance(self.value, str):
                return len(self.value.encode('utf-8'))
            elif isinstance(self.value, (dict, list)):
                return len(json.dumps(self.value, default=str).encode('utf-8'))
            else:
                return len(str(self.value).encode('utf-8'))
        except Exception:
            return 1024  # Default estimate
    
    def to_dict(self) -> Dict:
        """Convert entry to dictionary.
        
        Returns:
            Dict: Entry data
        """
        return {
            'key': self.key,
            'value': self.value,
            'created_at': self.created_at,
            'accessed_at': self.accessed_at,
            'access_count': self.access_count,
            'ttl': self.ttl,
            'expires_at': self.expires_at,
            'expired': self.is_expired(),
            'size': self.size_estimate()
        }


class CacheManager:
    """Thread-safe cache manager with TTL and size limits."""
    
    def __init__(self, 
                 max_size: int = 100 * 1024 * 1024,  # 100MB
                 max_entries: int = 10000,
                 default_ttl: int = 3600,  # 1 hour
                 cleanup_interval: int = 300,  # 5 minutes
                 persistence_file: Optional[Path] = None):
        """Initialize cache manager.
        
        Args:
            max_size: Maximum cache size in bytes
            max_entries: Maximum number of entries
            default_ttl: Default TTL in seconds
            cleanup_interval: Cleanup interval in seconds
            persistence_file: Optional file for cache persistence
        """
        self._cache: Dict[str, CacheEntry] = {}
        self._lock = threading.RLock()
        self._logger = logging.getLogger(__name__)
        
        # Configuration
        self._max_size = max_size
        self._max_entries = max_entries
        self._default_ttl = default_ttl
        self._cleanup_interval = cleanup_interval
        self._persistence_file = persistence_file
        
        # Statistics
        self._hits = 0
        self._misses = 0
        self._evictions = 0
        
        # Cleanup task
        self._cleanup_task = None
        self._running = False
        
        # Load persisted cache if available
        if self._persistence_file:
            self._load_cache()
    
    async def initialize(self) -> bool:
        """Initialize the cache manager.
        
        Returns:
            bool: True if initialization was successful
        """
        try:
            self.start()
            return True
        except Exception as e:
            self._logger.error(f"Failed to initialize cache manager: {e}")
            return False
    
    def start(self) -> None:
        """Start the cache manager and cleanup task."""
        if self._running:
            return
        
        self._running = True
        
        # Start cleanup task
        if self._cleanup_task is None:
            self._cleanup_task = asyncio.create_task(self._cleanup_loop())
        
        self._logger.info("Cache manager started")
    
    def stop(self) -> None:
        """Stop the cache manager and save cache."""
        if not self._running:
            return
        
        self._running = False
        
        # Cancel cleanup task
        if self._cleanup_task:
            self._cleanup_task.cancel()
            self._cleanup_task = None
        
        # Save cache if persistence is enabled
        if self._persistence_file:
            self._save_cache()
        
        self._logger.info("Cache manager stopped")
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            Optional[Any]: Cached value or None
        """
        with self._lock:
            entry = self._cache.get(key)
            
            if entry is None:
                self._misses += 1
                return None
            
            if entry.is_expired():
                del self._cache[key]
                self._misses += 1
                return None
            
            entry.touch()
            self._hits += 1
            return entry.value
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in cache.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds (uses default if None)
            
        Returns:
            bool: True if value was cached
        """
        if ttl is None:
            ttl = self._default_ttl
        
        with self._lock:
            # Create new entry
            entry = CacheEntry(key, value, ttl)
            
            # Check if we need to make space
            if not self._make_space_for_entry(entry):
                self._logger.warning(f"Failed to cache entry: {key} (size limit exceeded)")
                return False
            
            # Add to cache
            self._cache[key] = entry
            
            return True
    
    def delete(self, key: str) -> bool:
        """Delete entry from cache.
        
        Args:
            key: Cache key
            
        Returns:
            bool: True if entry was deleted
        """
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False
    
    def exists(self, key: str) -> bool:
        """Check if key exists and is not expired.
        
        Args:
            key: Cache key
            
        Returns:
            bool: True if key exists and is valid
        """
        with self._lock:
            entry = self._cache.get(key)
            
            if entry is None:
                return False
            
            if entry.is_expired():
                del self._cache[key]
                return False
            
            return True
    
    def clear(self) -> None:
        """Clear all cache entries."""
        with self._lock:
            self._cache.clear()
            self._logger.info("Cache cleared")
    
    def cleanup_expired(self) -> int:
        """Remove expired entries.
        
        Returns:
            int: Number of entries removed
        """
        with self._lock:
            expired_keys = [
                key for key, entry in self._cache.items()
                if entry.is_expired()
            ]
            
            for key in expired_keys:
                del self._cache[key]
            
            if expired_keys:
                self._logger.debug(f"Cleaned up {len(expired_keys)} expired entries")
            
            return len(expired_keys)
    
    def _make_space_for_entry(self, new_entry: CacheEntry) -> bool:
        """Make space for a new entry by evicting old ones.
        
        Args:
            new_entry: Entry to be added
            
        Returns:
            bool: True if space was made
        """
        # Check entry count limit
        while len(self._cache) >= self._max_entries:
            if not self._evict_lru_entry():
                return False
        
        # Check size limit
        current_size = self.get_size()
        new_entry_size = new_entry.size_estimate()
        
        while current_size + new_entry_size > self._max_size:
            if not self._evict_lru_entry():
                return False
            current_size = self.get_size()
        
        return True
    
    def _evict_lru_entry(self) -> bool:
        """Evict least recently used entry.
        
        Returns:
            bool: True if an entry was evicted
        """
        if not self._cache:
            return False
        
        # Find LRU entry
        lru_key = min(self._cache.keys(), 
                     key=lambda k: self._cache[k].accessed_at)
        
        del self._cache[lru_key]
        self._evictions += 1
        
        return True
    
    def get_size(self) -> int:
        """Get current cache size in bytes.
        
        Returns:
            int: Cache size in bytes
        """
        with self._lock:
            return sum(entry.size_estimate() for entry in self._cache.values())
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics.
        
        Returns:
            Dict[str, Any]: Cache statistics
        """
        with self._lock:
            total_requests = self._hits + self._misses
            hit_rate = (self._hits / total_requests * 100) if total_requests > 0 else 0
            
            size_bytes = self.get_size()
            return {
                'entries': len(self._cache),
                'size_bytes': size_bytes,
                'memory_usage': size_bytes,  # Alias for compatibility
                'size_mb': round(size_bytes / (1024 * 1024), 2),
                'max_entries': self._max_entries,
                'max_size_mb': round(self._max_size / (1024 * 1024), 2),
                'hits': self._hits,
                'misses': self._misses,
                'hit_rate': round(hit_rate, 2),
                'evictions': self._evictions,
                'running': self._running
            }
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get cache statistics (alias for get_stats).
        
        Returns:
            Dict[str, Any]: Cache statistics
        """
        return self.get_stats()
    
    def get_entries_info(self) -> List[Dict]:
        """Get information about all cache entries.
        
        Returns:
            List[Dict]: Entry information
        """
        with self._lock:
            entries = []
            
            for entry in self._cache.values():
                entries.append(entry.to_dict())
            
            # Sort by access time (most recent first)
            entries.sort(key=lambda x: x['accessed_at'], reverse=True)
            
            return entries
    
    def get_keys(self, pattern: Optional[str] = None) -> List[str]:
        """Get cache keys, optionally filtered by pattern.
        
        Args:
            pattern: Optional pattern to match keys
            
        Returns:
            List[str]: Matching keys
        """
        with self._lock:
            keys = list(self._cache.keys())
            
            if pattern:
                import fnmatch
                keys = [key for key in keys if fnmatch.fnmatch(key, pattern)]
            
            return sorted(keys)
    
    def set_config(self, 
                   max_size: Optional[int] = None,
                   max_entries: Optional[int] = None,
                   default_ttl: Optional[int] = None) -> None:
        """Update cache configuration.
        
        Args:
            max_size: Maximum cache size in bytes
            max_entries: Maximum number of entries
            default_ttl: Default TTL in seconds
        """
        with self._lock:
            if max_size is not None:
                self._max_size = max_size
            
            if max_entries is not None:
                self._max_entries = max_entries
            
            if default_ttl is not None:
                self._default_ttl = default_ttl
            
            # Trigger cleanup if needed
            self._enforce_limits()
            
            self._logger.info(f"Cache config updated: size={self._max_size}, entries={self._max_entries}, ttl={self._default_ttl}")
    
    def _enforce_limits(self) -> None:
        """Enforce cache size and entry limits."""
        # Remove expired entries first
        self.cleanup_expired()
        
        # Enforce entry limit
        while len(self._cache) > self._max_entries:
            if not self._evict_lru_entry():
                break
        
        # Enforce size limit
        while self.get_size() > self._max_size:
            if not self._evict_lru_entry():
                break
    
    async def _cleanup_loop(self) -> None:
        """Background cleanup task."""
        while self._running:
            try:
                await asyncio.sleep(self._cleanup_interval)
                
                if self._running:
                    expired_count = self.cleanup_expired()
                    
                    if expired_count > 0:
                        self._logger.debug(f"Cleanup removed {expired_count} expired entries")
                    
                    # Enforce limits
                    self._enforce_limits()
                    
                    # Save cache periodically if persistence is enabled
                    if self._persistence_file:
                        self._save_cache()
                        
            except asyncio.CancelledError:
                break
            except Exception as e:
                self._logger.error(f"Cache cleanup error: {e}")
    
    def _save_cache(self) -> None:
        """Save cache to persistence file."""
        if not self._persistence_file:
            return
        
        try:
            with self._lock:
                # Prepare cache data for serialization
                cache_data = {
                    'version': '1.0',
                    'saved_at': time.time(),
                    'entries': {}
                }
                
                for key, entry in self._cache.items():
                    if not entry.is_expired():
                        cache_data['entries'][key] = {
                            'value': entry.value,
                            'created_at': entry.created_at,
                            'ttl': entry.ttl,
                            'access_count': entry.access_count
                        }
                
                # Save to file
                self._persistence_file.parent.mkdir(parents=True, exist_ok=True)
                
                with open(self._persistence_file, 'w', encoding='utf-8') as f:
                    json.dump(cache_data, f, indent=2, default=str)
                
                self._logger.debug(f"Cache saved to {self._persistence_file}")
                
        except Exception as e:
            self._logger.error(f"Failed to save cache: {e}")
    
    def _load_cache(self) -> None:
        """Load cache from persistence file."""
        if not self._persistence_file or not self._persistence_file.exists():
            return
        
        try:
            with open(self._persistence_file, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
            
            if 'entries' not in cache_data:
                return
            
            loaded_count = 0
            current_time = time.time()
            
            with self._lock:
                for key, entry_data in cache_data['entries'].items():
                    # Check if entry is still valid
                    created_at = entry_data.get('created_at', current_time)
                    ttl = entry_data.get('ttl')
                    
                    if ttl and (current_time - created_at) > ttl:
                        continue  # Skip expired entries
                    
                    # Recreate cache entry
                    entry = CacheEntry(
                        key=key,
                        value=entry_data['value'],
                        ttl=ttl
                    )
                    
                    entry.created_at = created_at
                    entry.access_count = entry_data.get('access_count', 0)
                    
                    self._cache[key] = entry
                    loaded_count += 1
            
            self._logger.info(f"Loaded {loaded_count} cache entries from {self._persistence_file}")
            
        except Exception as e:
            self._logger.error(f"Failed to load cache: {e}")
    
    def export_cache(self, export_file: Path) -> bool:
        """Export cache to a file.
        
        Args:
            export_file: File to export to
            
        Returns:
            bool: True if export was successful
        """
        try:
            with self._lock:
                export_data = {
                    'metadata': {
                        'exported_at': datetime.now().isoformat(),
                        'cache_stats': self.get_stats(),
                        'entry_count': len(self._cache)
                    },
                    'entries': [entry.to_dict() for entry in self._cache.values()]
                }
            
            export_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(export_file, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, default=str)
            
            self._logger.info(f"Cache exported to {export_file}")
            return True
            
        except Exception as e:
            self._logger.error(f"Failed to export cache: {e}")
            return False
    
    def save_to_file(self) -> bool:
        """Save cache to persistence file.
        
        Returns:
            bool: True if save was successful
        """
        if not self._persistence_file:
            return True  # No persistence configured
        
        try:
            with self._lock:
                cache_data = {
                    'metadata': {
                        'saved_at': datetime.now().isoformat(),
                        'entry_count': len(self._cache)
                    },
                    'entries': {}
                }
                
                # Save non-expired entries
                for key, entry in self._cache.items():
                    if not entry.is_expired():
                        cache_data['entries'][key] = {
                            'value': entry.value,
                            'created_at': entry.created_at,
                            'ttl': entry.ttl,
                            'access_count': entry.access_count
                        }
            
            # Ensure directory exists
            self._persistence_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Write to file
            with open(self._persistence_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, indent=2, default=str)
            
            self._logger.debug(f"Cache saved to {self._persistence_file}")
            return True
            
        except Exception as e:
            self._logger.error(f"Failed to save cache: {e}")
            return False
    
    def __enter__(self):
        """Context manager entry."""
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop()