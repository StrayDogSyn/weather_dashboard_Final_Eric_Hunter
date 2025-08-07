#!/usr/bin/env python3
"""
Advanced Cache Manager for Weather Dashboard
Provides intelligent caching with compression, LRU eviction, and performance tracking.
"""

import gzip
import json
import logging
import pickle
import threading
import time
from collections import OrderedDict
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set


class CompressionType(Enum):
    """Types of compression available."""

    NONE = "none"
    GZIP = "gzip"
    PICKLE = "pickle"


@dataclass
class CacheEntry:
    """Represents a cached item with metadata."""

    value: Any
    created_at: float
    expires_at: Optional[float]
    access_count: int = 0
    last_accessed: float = field(default_factory=time.time)
    size_bytes: int = 0
    compression: CompressionType = CompressionType.NONE
    tags: Set[str] = field(default_factory=set)
    priority: int = 1

    def is_expired(self) -> bool:
        """Check if the entry has expired."""
        return self.expires_at is not None and time.time() > self.expires_at

    def touch(self):
        """Update access time and count."""
        self.last_accessed = time.time()
        self.access_count += 1


@dataclass
class CacheStats:
    """Cache performance statistics."""

    hits: int = 0
    misses: int = 0
    evictions: int = 0
    compressions: int = 0
    decompressions: int = 0
    total_size_bytes: int = 0

    @property
    def hit_rate(self) -> float:
        """Calculate hit rate percentage."""
        total = self.hits + self.misses
        return (self.hits / total * 100) if total > 0 else 0.0

    @property
    def total_size_mb(self) -> float:
        """Get total size in MB."""
        return self.total_size_bytes / (1024 * 1024)


class CacheManager:
    """Advanced cache manager with compression and LRU eviction."""

    def __init__(
        self,
        max_size_mb: int = 100,
        enable_compression: bool = True,
        compression_threshold: int = 1024,
        lru_factor: float = 0.8,
    ):
        """
        Initialize the cache manager.

        Args:
            max_size_mb: Maximum cache size in megabytes
            enable_compression: Whether to enable automatic compression
            compression_threshold: Size threshold for compression (bytes)
            lru_factor: Factor for LRU eviction (0.0-1.0)
        """
        self.max_size_bytes = max_size_mb * 1024 * 1024
        self.enable_compression = enable_compression
        self.compression_threshold = compression_threshold
        self.lru_factor = lru_factor

        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._stats = CacheStats()
        self._lock = threading.RLock()
        self._tag_index: Dict[str, Set[str]] = {}

        self.logger = logging.getLogger(__name__)

    def get(self, key: str) -> Optional[Any]:
        """Get a value from cache with LRU update."""
        with self._lock:
            if key not in self._cache:
                self._stats.misses += 1
                return None

            entry = self._cache[key]

            # Check expiration
            if entry.is_expired():
                self._remove_entry(key)
                self._stats.misses += 1
                return None

            # Update LRU order and access stats
            entry.touch()
            self._cache.move_to_end(key)
            self._stats.hits += 1

            # Handle decompression
            if entry.compression != CompressionType.NONE:
                self._stats.decompressions += 1

            return self._decompress_value(entry.value, entry.compression)

    def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
        tags: Optional[List[str]] = None,
        priority: int = 1,
    ) -> bool:
        """Set a value in cache with compression and LRU management."""
        with self._lock:
            # Remove existing entry if present
            if key in self._cache:
                self._remove_entry(key)

            # Determine compression
            compression_type = self._determine_compression(value)
            compressed_value = self._compress_value(value, compression_type)

            # Calculate size
            size_bytes = self._calculate_size(compressed_value)

            # Create entry
            expires_at = time.time() + ttl if ttl else None
            entry = CacheEntry(
                value=compressed_value,
                created_at=time.time(),
                expires_at=expires_at,
                size_bytes=size_bytes,
                compression=compression_type,
                tags=set(tags or []),
                priority=priority,
            )

            # Ensure capacity
            self._ensure_capacity(size_bytes)

            # Add to cache
            self._cache[key] = entry
            self._stats.total_size_bytes += size_bytes

            # Update tag index
            for tag in entry.tags:
                if tag not in self._tag_index:
                    self._tag_index[tag] = set()
                self._tag_index[tag].add(key)

            # Update compression stats
            if compression_type != CompressionType.NONE:
                self._stats.compressions += 1

            return True

    def _determine_compression(self, value: Any) -> CompressionType:
        """Determine the best compression type for a value."""
        if not self.enable_compression:
            return CompressionType.NONE

        # Estimate size
        estimated_size = (
            len(str(value))
            if isinstance(value, (str, int, float))
            else len(json.dumps(value, default=str))
        )

        if estimated_size < self.compression_threshold:
            return CompressionType.NONE

        # Use pickle for complex objects, gzip for strings/simple data
        if isinstance(value, (dict, list, tuple)):
            return CompressionType.PICKLE
        else:
            return CompressionType.GZIP

    def _compress_value(self, value: Any, compression_type: CompressionType) -> Any:
        """Compress a value based on compression type."""
        if compression_type == CompressionType.NONE:
            return value
        elif compression_type == CompressionType.GZIP:
            json_str = json.dumps(value, default=str)
            return gzip.compress(json_str.encode("utf-8"))
        elif compression_type == CompressionType.PICKLE:
            return gzip.compress(pickle.dumps(value))
        else:
            return value

    def _decompress_value(self, value: Any, compression_type: CompressionType) -> Any:
        """Decompress a value based on compression type."""
        if compression_type == CompressionType.NONE:
            return value
        elif compression_type == CompressionType.GZIP:
            decompressed = gzip.decompress(value).decode("utf-8")
            return json.loads(decompressed)
        elif compression_type == CompressionType.PICKLE:
            return pickle.loads(gzip.decompress(value))
        else:
            return value

    def _calculate_size(self, value: Any) -> int:
        """Calculate the size of a value in bytes."""
        if isinstance(value, bytes):
            return len(value)
        elif isinstance(value, str):
            return len(value.encode("utf-8"))
        else:
            return len(pickle.dumps(value))

    def _ensure_capacity(self, new_size: int):
        """Ensure cache has capacity for new entry."""
        target_size = self.max_size_bytes - new_size

        while self._stats.total_size_bytes > target_size and self._cache:
            self._evict_lru_entries()

    def _evict_lru_entries(self):
        """Evict least recently used entries."""
        # Calculate how many entries to evict (based on LRU factor)
        evict_count = max(1, int(len(self._cache) * (1 - self.lru_factor)))

        # Get LRU entries (first items in OrderedDict)
        lru_keys = list(self._cache.keys())[:evict_count]

        for key in lru_keys:
            self._remove_entry(key)
            self._stats.evictions += 1

    def _remove_entry(self, key: str):
        """Remove an entry and update indexes."""
        if key in self._cache:
            entry = self._cache[key]

            # Update size
            self._stats.total_size_bytes -= entry.size_bytes

            # Update tag index
            for tag in entry.tags:
                if tag in self._tag_index:
                    self._tag_index[tag].discard(key)
                    if not self._tag_index[tag]:
                        del self._tag_index[tag]

            # Remove from cache
            del self._cache[key]

    def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive cache statistics."""
        with self._lock:
            return {
                "hit_rate": self._stats.hit_rate,
                "hits": self._stats.hits,
                "misses": self._stats.misses,
                "evictions": self._stats.evictions,
                "compressions": self._stats.compressions,
                "decompressions": self._stats.decompressions,
                "total_size_mb": self._stats.total_size_mb,
                "total_entries": len(self._cache),
                "max_size_mb": self.max_size_bytes / (1024 * 1024),
                "utilization": (
                    self._stats.total_size_bytes / self.max_size_bytes
                ) * 100,
            }

    def get_by_tags(self, tags: List[str]) -> Dict[str, Any]:
        """Get all cached items with specified tags."""
        with self._lock:
            result = {}

            # Find keys with matching tags
            matching_keys = set()
            for tag in tags:
                if tag in self._tag_index:
                    if not matching_keys:
                        matching_keys = self._tag_index[tag].copy()
                    else:
                        matching_keys &= self._tag_index[tag]

            # Get values for matching keys
            for key in matching_keys:
                value = self.get(key)
                if value is not None:
                    result[key] = value

            return result

    def clear_by_tags(self, tags: List[str]) -> int:
        """Clear all cached items with specified tags."""
        with self._lock:
            # Find keys with matching tags
            matching_keys = set()
            for tag in tags:
                if tag in self._tag_index:
                    matching_keys.update(self._tag_index[tag])

            # Remove matching entries
            removed_count = 0
            for key in list(matching_keys):
                if key in self._cache:
                    self._remove_entry(key)
                    removed_count += 1

            return removed_count

    def bulk_set(
        self,
        items: Dict[str, Any],
        ttl: Optional[int] = None,
        tags: Optional[List[str]] = None,
    ) -> int:
        """Set multiple items efficiently."""
        success_count = 0
        for key, value in items.items():
            if self.set(key, value, ttl=ttl, tags=tags):
                success_count += 1
        return success_count

    def bulk_get(self, keys: List[str]) -> Dict[str, Any]:
        """Get multiple items efficiently."""
        result = {}
        for key in keys:
            value = self.get(key)
            if value is not None:
                result[key] = value
        return result

    def optimize_memory(self) -> Dict[str, int]:
        """Optimize memory usage by recompressing and cleaning up."""
        with self._lock:
            stats = {"recompressed": 0, "cleaned": 0}

            # Clean expired entries
            expired_keys = []
            for key, entry in self._cache.items():
                if entry.is_expired():
                    expired_keys.append(key)

            for key in expired_keys:
                self._remove_entry(key)
                stats["cleaned"] += 1

            # Recompress entries that might benefit
            for key, entry in list(self._cache.items()):
                if entry.compression == CompressionType.NONE:
                    new_compression = self._determine_compression(entry.value)
                    if new_compression != CompressionType.NONE:
                        # Re-set with compression
                        value = entry.value
                        tags = list(entry.tags)
                        ttl = int(entry.expires_at - time.time()) if entry.expires_at else None

                        self._remove_entry(key)
                        self.set(key, value, ttl=ttl, tags=tags, priority=entry.priority)
                        stats["recompressed"] += 1

            return stats

    def clear(self):
        """Clear all cached items."""
        with self._lock:
            self._cache.clear()
            self._tag_index.clear()
            self._stats = CacheStats()

    def __len__(self) -> int:
        """Get number of cached items."""
        return len(self._cache)

    def __contains__(self, key: str) -> bool:
        """Check if key exists in cache."""
        with self._lock:
            return key in self._cache and not self._cache[key].is_expired()
