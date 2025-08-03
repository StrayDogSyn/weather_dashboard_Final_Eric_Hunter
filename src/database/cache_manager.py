"""Enhanced Cache Manager with LRU Eviction and Compression.

Provides high-performance thread-safe caching with automatic expiration,
LRU eviction, compression, and advanced memory management.
"""

import asyncio
import gzip
import json
import logging
import pickle
import sys
import threading
import time
import weakref
import zlib
from collections import OrderedDict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Protocol


class CompressionType:
    """Compression types for cache entries."""

    NONE = "none"
    GZIP = "gzip"
    ZLIB = "zlib"
    PICKLE = "pickle"


class CacheStats:
    """Cache statistics tracking."""

    def __init__(self):
        self.hits = 0
        self.misses = 0
        self.evictions = 0
        self.compressions = 0
        self.decompressions = 0
        self.memory_saved = 0
        self.total_size = 0
        self.start_time = time.time()

    @property
    def hit_rate(self) -> float:
        """Calculate cache hit rate."""
        total = self.hits + self.misses
        return self.hits / total if total > 0 else 0.0

    @property
    def compression_ratio(self) -> float:
        """Calculate compression ratio."""
        return self.memory_saved / self.total_size if self.total_size > 0 else 0.0

    def reset(self):
        """Reset all statistics."""
        self.__init__()


class Serializable(Protocol):
    """Protocol for serializable objects."""

    def to_dict(self) -> Dict[str, Any]: ...
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Serializable": ...


class CacheEntry:
    """Enhanced cache entry with compression and memory tracking."""

    def __init__(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
        tags: Optional[List[str]] = None,
        compression: str = CompressionType.NONE,
        priority: int = 0,
    ):
        """Initialize cache entry.

        Args:
            key: Cache key
            value: Cached value
            ttl: Time to live in seconds
            tags: Optional tags for categorization
            compression: Compression type to use
            priority: Priority for eviction (higher = keep longer)
        """
        self.key = key
        self._raw_value = value
        self._compressed_value = None
        self.ttl = ttl
        self.tags = tags or []
        self.compression = compression
        self.priority = priority
        self.created_at = time.time()
        self.accessed_at = self.created_at
        self.access_count = 0
        self.expires_at = self.created_at + ttl if ttl else None
        self.original_size = self._calculate_size(value)
        self.compressed_size = 0

        # Compress if needed
        if compression != CompressionType.NONE:
            self._compress_value()

    def _calculate_size(self, obj: Any) -> int:
        """Calculate approximate memory size of object."""
        try:
            if isinstance(obj, (str, bytes)):
                return len(obj)
            elif isinstance(obj, (list, tuple)):
                return sum(self._calculate_size(item) for item in obj)
            elif isinstance(obj, dict):
                return sum(
                    self._calculate_size(k) + self._calculate_size(v) for k, v in obj.items()
                )
            else:
                return sys.getsizeof(obj)
        except Exception:
            return sys.getsizeof(obj)

    def _compress_value(self) -> None:
        """Compress the stored value."""
        try:
            if self.compression == CompressionType.GZIP:
                serialized = pickle.dumps(self._raw_value)
                self._compressed_value = gzip.compress(serialized)
            elif self.compression == CompressionType.ZLIB:
                serialized = pickle.dumps(self._raw_value)
                self._compressed_value = zlib.compress(serialized)
            elif self.compression == CompressionType.PICKLE:
                self._compressed_value = pickle.dumps(self._raw_value)

            if self._compressed_value:
                self.compressed_size = len(self._compressed_value)
                # Clear raw value to save memory if compression is effective
                if self.compressed_size < self.original_size * 0.8:
                    self._raw_value = None
        except Exception:
            # Fallback to no compression
            self.compression = CompressionType.NONE
            self._compressed_value = None

    def _decompress_value(self) -> Any:
        """Decompress and return the stored value."""
        if self._raw_value is not None:
            return self._raw_value

        if self._compressed_value is None:
            return None

        try:
            if self.compression == CompressionType.GZIP:
                decompressed = gzip.decompress(self._compressed_value)
                return pickle.loads(decompressed)
            elif self.compression == CompressionType.ZLIB:
                decompressed = zlib.decompress(self._compressed_value)
                return pickle.loads(decompressed)
            elif self.compression == CompressionType.PICKLE:
                return pickle.loads(self._compressed_value)
        except Exception:
            return None

        return self._raw_value

    @property
    def value(self) -> Any:
        """Get the cached value (decompressing if needed)."""
        if self._raw_value is not None:
            return self._raw_value
        return self._decompress_value()

    @property
    def memory_size(self) -> int:
        """Get current memory usage of this entry."""
        size = 0
        if self._raw_value is not None:
            size += self.original_size
        if self._compressed_value is not None:
            size += self.compressed_size
        return size + sys.getsizeof(self.key) + 200  # Approximate overhead

    @property
    def compression_ratio(self) -> float:
        """Get compression ratio (0.0 = no compression, 1.0 = perfect compression)."""
        if self.compressed_size == 0 or self.original_size == 0:
            return 0.0
        return 1.0 - (self.compressed_size / self.original_size)

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
                return len(self.value.encode("utf-8"))
            elif isinstance(self.value, (dict, list)):
                return len(json.dumps(self.value, default=str).encode("utf-8"))
            else:
                return len(str(self.value).encode("utf-8"))
        except Exception:
            return 1024  # Default estimate

    def to_dict(self) -> Dict:
        """Convert entry to dictionary.

        Returns:
            Dict: Entry data
        """
        return {
            "key": self.key,
            "value": self.value,
            "created_at": self.created_at,
            "accessed_at": self.accessed_at,
            "access_count": self.access_count,
            "ttl": self.ttl,
            "expires_at": self.expires_at,
            "expired": self.is_expired(),
            "size": self.size_estimate(),
        }


class CacheManager:
    """Enhanced thread-safe cache manager with LRU eviction and compression."""

    def __init__(
        self,
        max_size: int = 100 * 1024 * 1024,  # 100MB
        max_entries: int = 10000,
        default_ttl: int = 3600,  # 1 hour
        cleanup_interval: int = 300,  # 5 minutes
        persistence_file: Optional[Path] = None,
        enable_compression: bool = True,
        compression_threshold: int = 1024,  # Compress items > 1KB
        lru_factor: float = 0.1,
    ):  # Evict 10% when full
        """Initialize enhanced cache manager.

        Args:
            max_size: Maximum cache size in bytes
            max_entries: Maximum number of entries
            default_ttl: Default TTL in seconds
            cleanup_interval: Cleanup interval in seconds
            persistence_file: Optional file for cache persistence
            enable_compression: Enable automatic compression
            compression_threshold: Minimum size for compression
            lru_factor: Fraction of cache to evict when full
        """
        # Use OrderedDict for LRU functionality
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._lock = threading.RLock()
        self._logger = logging.getLogger(__name__)

        # Configuration
        self._max_size = max_size
        self._max_entries = max_entries
        self._default_ttl = default_ttl
        self._cleanup_interval = cleanup_interval
        self._persistence_file = persistence_file
        self._enable_compression = enable_compression
        self._compression_threshold = compression_threshold
        self._lru_factor = lru_factor

        # Enhanced statistics
        self._stats = CacheStats()

        # Memory tracking
        self._current_size = 0
        self._size_lock = threading.Lock()

        # Cleanup task
        self._cleanup_task = None
        self._running = False

        # Weak references for cleanup
        self._cleanup_refs: List[weakref.ref] = []

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

    def _determine_compression(self, value: Any) -> str:
        """Determine appropriate compression type for value."""
        if not self._enable_compression:
            return CompressionType.NONE

        try:
            size = sys.getsizeof(value)
            if size < self._compression_threshold:
                return CompressionType.NONE

            # Choose compression based on data type and size
            if isinstance(value, (dict, list)) and size > 10240:  # 10KB
                return CompressionType.ZLIB
            elif isinstance(value, str) and size > 5120:  # 5KB
                return CompressionType.GZIP
            elif size > self._compression_threshold:
                return CompressionType.PICKLE
        except Exception:
            pass

        return CompressionType.NONE

    def _evict_lru_entries(self) -> int:
        """Evict least recently used entries."""
        if not self._cache:
            return 0

        # Calculate how many entries to evict
        target_count = max(1, int(len(self._cache) * self._lru_factor))
        evicted = 0

        # Evict from the beginning (oldest)
        keys_to_remove = list(self._cache.keys())[:target_count]

        for key in keys_to_remove:
            if key in self._cache:
                entry = self._cache[key]
                self._current_size -= entry.memory_size
                del self._cache[key]
                evicted += 1
                self._stats.evictions += 1

        return evicted

    def _ensure_capacity(self, new_entry_size: int) -> None:
        """Ensure cache has capacity for new entry."""
        # Check entry count limit
        while len(self._cache) >= self._max_entries:
            self._evict_lru_entries()

        # Check size limit
        while (self._current_size + new_entry_size) > self._max_size and self._cache:
            self._evict_lru_entries()

    def get(self, key: str) -> Optional[Any]:
        """Get value from cache with LRU update.

        Args:
            key: Cache key

        Returns:
            Optional[Any]: Cached value or None
        """
        with self._lock:
            entry = self._cache.get(key)

            if entry is None:
                self._stats.misses += 1
                return None

            if entry.is_expired():
                self._current_size -= entry.memory_size
                del self._cache[key]
                self._stats.misses += 1
                return None

            # Move to end for LRU (most recently used)
            self._cache.move_to_end(key)
            entry.touch()
            self._stats.hits += 1

            # Handle decompression stats
            if entry.compression != CompressionType.NONE:
                self._stats.decompressions += 1

            return entry.value

    def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
        tags: Optional[List[str]] = None,
        priority: int = 0,
    ) -> bool:
        """Set value in cache with enhanced features.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds (uses default if None)
            tags: Optional tags for categorization
            priority: Priority for eviction (higher = keep longer)

        Returns:
            bool: True if value was cached
        """
        if ttl is None:
            ttl = self._default_ttl

        with self._lock:
            # Determine compression type
            compression = self._determine_compression(value)

            # Create new entry with compression
            entry = CacheEntry(key, value, ttl, tags, compression, priority)

            # Remove existing entry if present
            if key in self._cache:
                old_entry = self._cache[key]
                self._current_size -= old_entry.memory_size
                del self._cache[key]

            # Ensure we have capacity
            self._ensure_capacity(entry.memory_size)

            # Add to cache (at end for LRU)
            self._cache[key] = entry
            self._current_size += entry.memory_size

            # Update compression stats
            if compression != CompressionType.NONE:
                self._stats.compressions += 1
                self._stats.memory_saved += max(0, entry.original_size - entry.compressed_size)

            self._stats.total_size = self._current_size

            return True

    def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive cache statistics."""
        with self._lock:
            return {
                "hits": self._stats.hits,
                "misses": self._stats.misses,
                "hit_rate": self._stats.hit_rate,
                "evictions": self._stats.evictions,
                "compressions": self._stats.compressions,
                "decompressions": self._stats.decompressions,
                "compression_ratio": self._stats.compression_ratio,
                "memory_saved": self._stats.memory_saved,
                "current_size": self._current_size,
                "max_size": self._max_size,
                "entry_count": len(self._cache),
                "max_entries": self._max_entries,
                "uptime": time.time() - self._stats.start_time,
                "size_utilization": self._current_size / self._max_size,
                "entry_utilization": len(self._cache) / self._max_entries,
            }

    def get_by_tags(self, tags: List[str]) -> Dict[str, Any]:
        """Get all entries matching any of the given tags."""
        with self._lock:
            result = {}
            for key, entry in self._cache.items():
                if not entry.is_expired() and any(tag in entry.tags for tag in tags):
                    entry.touch()
                    self._cache.move_to_end(key)
                    result[key] = entry.value
            return result

    def clear_by_tags(self, tags: List[str]) -> int:
        """Clear all entries matching any of the given tags."""
        with self._lock:
            keys_to_remove = []
            for key, entry in self._cache.items():
                if any(tag in entry.tags for tag in tags):
                    keys_to_remove.append(key)

            for key in keys_to_remove:
                if key in self._cache:
                    entry = self._cache[key]
                    self._current_size -= entry.memory_size
                    del self._cache[key]

            return len(keys_to_remove)

    def bulk_set(
        self, items: Dict[str, Any], ttl: Optional[int] = None, tags: Optional[List[str]] = None
    ) -> int:
        """Set multiple items in cache efficiently."""
        success_count = 0
        for key, value in items.items():
            if self.set(key, value, ttl, tags):
                success_count += 1
        return success_count

    def bulk_get(self, keys: List[str]) -> Dict[str, Any]:
        """Get multiple items from cache efficiently."""
        result = {}
        for key in keys:
            value = self.get(key)
            if value is not None:
                result[key] = value
        return result

    def optimize_memory(self) -> Dict[str, int]:
        """Optimize memory usage by recompressing and cleaning up."""
        with self._lock:
            original_size = self._current_size
            recompressed = 0
            cleaned = 0

            # Clean expired entries
            expired_keys = []
            for key, entry in self._cache.items():
                if entry.is_expired():
                    expired_keys.append(key)

            for key in expired_keys:
                if key in self._cache:
                    entry = self._cache[key]
                    self._current_size -= entry.memory_size
                    del self._cache[key]
                    cleaned += 1

            # Recompress entries that might benefit
            for entry in self._cache.values():
                if (
                    entry.compression == CompressionType.NONE
                    and entry.original_size > self._compression_threshold
                ):
                    old_size = entry.memory_size
                    entry.compression = self._determine_compression(entry.value)
                    if entry.compression != CompressionType.NONE:
                        entry._compress_value()
                        self._current_size += entry.memory_size - old_size
                        recompressed += 1

            return {
                "original_size": original_size,
                "new_size": self._current_size,
                "saved_bytes": original_size - self._current_size,
                "recompressed_entries": recompressed,
                "cleaned_entries": cleaned,
            }

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
            expired_keys = [key for key, entry in self._cache.items() if entry.is_expired()]

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
        lru_key = min(self._cache.keys(), key=lambda k: self._cache[k].accessed_at)

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
            entries.sort(key=lambda x: x["accessed_at"], reverse=True)

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

    def set_config(
        self,
        max_size: Optional[int] = None,
        max_entries: Optional[int] = None,
        default_ttl: Optional[int] = None,
    ) -> None:
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

            self._logger.info(
                f"Cache config updated: size={self._max_size}, "
                f"entries={self._max_entries}, ttl={self._default_ttl}"
            )

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
                cache_data = {"version": "1.0", "saved_at": time.time(), "entries": {}}

                for key, entry in self._cache.items():
                    if not entry.is_expired():
                        cache_data["entries"][key] = {
                            "value": entry.value,
                            "created_at": entry.created_at,
                            "ttl": entry.ttl,
                            "access_count": entry.access_count,
                        }

                # Save to file
                self._persistence_file.parent.mkdir(parents=True, exist_ok=True)

                with open(self._persistence_file, "w", encoding="utf-8") as f:
                    json.dump(cache_data, f, indent=2, default=str)

                self._logger.debug(f"Cache saved to {self._persistence_file}")

        except Exception as e:
            self._logger.error(f"Failed to save cache: {e}")

    def _load_cache(self) -> None:
        """Load cache from persistence file."""
        if not self._persistence_file or not self._persistence_file.exists():
            return

        try:
            with open(self._persistence_file, "r", encoding="utf-8") as f:
                cache_data = json.load(f)

            if "entries" not in cache_data:
                return

            loaded_count = 0
            current_time = time.time()

            with self._lock:
                for key, entry_data in cache_data["entries"].items():
                    # Check if entry is still valid
                    created_at = entry_data.get("created_at", current_time)
                    ttl = entry_data.get("ttl")

                    if ttl and (current_time - created_at) > ttl:
                        continue  # Skip expired entries

                    # Recreate cache entry
                    entry = CacheEntry(key=key, value=entry_data["value"], ttl=ttl)

                    entry.created_at = created_at
                    entry.access_count = entry_data.get("access_count", 0)

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
                    "metadata": {
                        "exported_at": datetime.now().isoformat(),
                        "cache_stats": self.get_stats(),
                        "entry_count": len(self._cache),
                    },
                    "entries": [entry.to_dict() for entry in self._cache.values()],
                }

            export_file.parent.mkdir(parents=True, exist_ok=True)

            with open(export_file, "w", encoding="utf-8") as f:
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
                    "metadata": {
                        "saved_at": datetime.now().isoformat(),
                        "entry_count": len(self._cache),
                    },
                    "entries": {},
                }

                # Save non-expired entries
                for key, entry in self._cache.items():
                    if not entry.is_expired():
                        cache_data["entries"][key] = {
                            "value": entry.value,
                            "created_at": entry.created_at,
                            "ttl": entry.ttl,
                            "access_count": entry.access_count,
                        }

            # Ensure directory exists
            self._persistence_file.parent.mkdir(parents=True, exist_ok=True)

            # Write to file
            with open(self._persistence_file, "w", encoding="utf-8") as f:
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
