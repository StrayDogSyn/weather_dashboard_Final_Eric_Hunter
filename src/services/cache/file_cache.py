"""File-based cache implementation for persistent caching.

Provides disk-based caching for API responses, images, and computed data.
"""

import os
import json
import pickle
import hashlib
import time
import threading
import shutil
from pathlib import Path
from typing import Any, Optional, Dict, List, Union
from dataclasses import dataclass, asdict
import logging
import tempfile
import gzip


@dataclass
class FileCacheEntry:
    """File cache entry metadata."""
    key: str
    filename: str
    size: int
    created: float
    expires: float
    access_count: int
    last_access: float
    compressed: bool = False
    
    def is_expired(self) -> bool:
        """Check if entry has expired."""
        return time.time() > self.expires
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'FileCacheEntry':
        """Create from dictionary."""
        return cls(**data)


class FileCache:
    """File-based cache with compression and cleanup."""
    
    def __init__(self,
                 cache_dir: Optional[str] = None,
                 default_ttl: float = 3600,  # 1 hour
                 max_size_mb: int = 500,
                 compress_threshold: int = 1024,  # Compress files > 1KB
                 cleanup_interval: float = 300):  # 5 minutes
        """
        Initialize file cache.
        
        Args:
            cache_dir: Cache directory path
            default_ttl: Default time-to-live in seconds
            max_size_mb: Maximum cache size in MB
            compress_threshold: Compress files larger than this size
            cleanup_interval: Cleanup interval in seconds
        """
        self.default_ttl = default_ttl
        self.max_size_bytes = max_size_mb * 1024 * 1024
        self.compress_threshold = compress_threshold
        self.cleanup_interval = cleanup_interval
        
        # Setup cache directory
        if cache_dir is None:
            cache_dir = os.path.join(tempfile.gettempdir(), 'weather_dashboard_cache')
        
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        self.metadata_file = self.cache_dir / 'metadata.json'
        self._metadata: Dict[str, FileCacheEntry] = {}
        self._lock = threading.RLock()
        self._logger = logging.getLogger(__name__)
        
        # Load existing metadata
        self._load_metadata()
        
        # Start cleanup thread
        self._cleanup_thread = threading.Thread(
            target=self._periodic_cleanup,
            daemon=True
        )
        self._cleanup_thread.start()
    
    def set(self, key: str, value: Any, ttl: Optional[float] = None,
           compress: Optional[bool] = None) -> bool:
        """Set value in file cache.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time-to-live in seconds
            compress: Whether to compress (auto-detect if None)
            
        Returns:
            True if successfully cached
        """
        if ttl is None:
            ttl = self.default_ttl
        
        try:
            with self._lock:
                # Generate filename
                filename = self._generate_filename(key)
                filepath = self.cache_dir / filename
                
                # Serialize data
                if isinstance(value, (str, bytes)):
                    data = value.encode() if isinstance(value, str) else value
                    use_pickle = False
                else:
                    data = pickle.dumps(value)
                    use_pickle = True
                
                # Determine compression
                if compress is None:
                    compress = len(data) > self.compress_threshold
                
                # Compress if needed
                if compress:
                    data = gzip.compress(data)
                    filename += '.gz'
                    filepath = self.cache_dir / filename
                
                # Check size limits
                if not self._check_size_limit(len(data)):
                    self._cleanup_old_files(len(data))
                
                # Write file
                with open(filepath, 'wb') as f:
                    f.write(data)
                
                # Update metadata
                entry = FileCacheEntry(
                    key=key,
                    filename=filename,
                    size=len(data),
                    created=time.time(),
                    expires=time.time() + ttl,
                    access_count=0,
                    last_access=time.time(),
                    compressed=compress
                )
                
                # Store additional metadata for non-pickle data
                if not use_pickle:
                    entry.filename += '.txt'
                
                self._metadata[key] = entry
                self._save_metadata()
                
                return True
                
        except Exception as e:
            self._logger.error(f"Error caching {key}: {e}")
            return False
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from file cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found/expired
        """
        with self._lock:
            if key not in self._metadata:
                return None
            
            entry = self._metadata[key]
            
            # Check expiration
            if entry.is_expired():
                self._remove_entry(key)
                return None
            
            try:
                filepath = self.cache_dir / entry.filename
                
                if not filepath.exists():
                    self._remove_entry(key)
                    return None
                
                # Read file
                with open(filepath, 'rb') as f:
                    data = f.read()
                
                # Decompress if needed
                if entry.compressed:
                    data = gzip.decompress(data)
                
                # Deserialize
                if entry.filename.endswith('.txt'):
                    value = data.decode()
                else:
                    value = pickle.loads(data)
                
                # Update access metadata
                entry.access_count += 1
                entry.last_access = time.time()
                self._save_metadata()
                
                return value
                
            except Exception as e:
                self._logger.error(f"Error reading cache {key}: {e}")
                self._remove_entry(key)
                return None
    
    def delete(self, key: str) -> bool:
        """Delete entry from cache.
        
        Args:
            key: Cache key
            
        Returns:
            True if entry was deleted
        """
        with self._lock:
            if key in self._metadata:
                self._remove_entry(key)
                return True
            return False
    
    def clear(self) -> None:
        """Clear all cache entries."""
        with self._lock:
            # Remove all files
            for entry in self._metadata.values():
                filepath = self.cache_dir / entry.filename
                if filepath.exists():
                    filepath.unlink()
            
            # Clear metadata
            self._metadata.clear()
            self._save_metadata()
    
    def get_cache_info(self) -> Dict[str, Any]:
        """Get cache information.
        
        Returns:
            Dictionary with cache statistics
        """
        with self._lock:
            total_size = sum(entry.size for entry in self._metadata.values())
            total_files = len(self._metadata)
            
            # Count by type
            compressed_count = sum(1 for entry in self._metadata.values() if entry.compressed)
            
            # Find oldest and newest
            if self._metadata:
                oldest = min(entry.created for entry in self._metadata.values())
                newest = max(entry.created for entry in self._metadata.values())
            else:
                oldest = newest = 0
            
            return {
                'total_entries': total_files,
                'total_size_mb': total_size / (1024 * 1024),
                'compressed_entries': compressed_count,
                'oldest_entry': oldest,
                'newest_entry': newest,
                'cache_dir': str(self.cache_dir),
                'max_size_mb': self.max_size_bytes / (1024 * 1024)
            }
    
    def cleanup_expired(self) -> int:
        """Remove expired entries.
        
        Returns:
            Number of entries removed
        """
        with self._lock:
            expired_keys = [
                key for key, entry in self._metadata.items()
                if entry.is_expired()
            ]
            
            for key in expired_keys:
                self._remove_entry(key)
            
            if expired_keys:
                self._save_metadata()
                self._logger.debug(f"Removed {len(expired_keys)} expired entries")
            
            return len(expired_keys)
    
    def optimize(self) -> Dict[str, int]:
        """Optimize cache by removing old/unused entries.
        
        Returns:
            Dictionary with optimization results
        """
        with self._lock:
            initial_count = len(self._metadata)
            initial_size = sum(entry.size for entry in self._metadata.values())
            
            # Remove expired entries
            expired_removed = self.cleanup_expired()
            
            # Remove least recently used entries if over size limit
            lru_removed = 0
            if not self._check_size_limit(0):
                lru_removed = self._cleanup_old_files(0)
            
            final_count = len(self._metadata)
            final_size = sum(entry.size for entry in self._metadata.values())
            
            return {
                'expired_removed': expired_removed,
                'lru_removed': lru_removed,
                'total_removed': initial_count - final_count,
                'size_freed_mb': (initial_size - final_size) / (1024 * 1024)
            }
    
    def _generate_filename(self, key: str) -> str:
        """Generate filename for cache key."""
        # Use hash to avoid filesystem issues
        hash_obj = hashlib.md5(key.encode())
        return hash_obj.hexdigest()
    
    def _check_size_limit(self, additional_size: int) -> bool:
        """Check if adding size would exceed limit."""
        current_size = sum(entry.size for entry in self._metadata.values())
        return current_size + additional_size <= self.max_size_bytes
    
    def _cleanup_old_files(self, needed_size: int) -> int:
        """Remove old files to free space.
        
        Returns:
            Number of entries removed
        """
        if not self._metadata:
            return 0
        
        # Sort by last access time (oldest first)
        sorted_entries = sorted(
            self._metadata.items(),
            key=lambda x: x[1].last_access
        )
        
        freed_size = 0
        removed_count = 0
        
        for key, entry in sorted_entries:
            if freed_size >= needed_size and self._check_size_limit(0):
                break
            
            self._remove_entry(key)
            freed_size += entry.size
            removed_count += 1
        
        if removed_count > 0:
            self._save_metadata()
            self._logger.debug(f"Removed {removed_count} old entries to free space")
        
        return removed_count
    
    def _remove_entry(self, key: str) -> None:
        """Remove cache entry and file."""
        if key not in self._metadata:
            return
        
        entry = self._metadata[key]
        filepath = self.cache_dir / entry.filename
        
        # Remove file
        if filepath.exists():
            try:
                filepath.unlink()
            except Exception as e:
                self._logger.error(f"Error removing cache file {filepath}: {e}")
        
        # Remove metadata
        del self._metadata[key]
    
    def _load_metadata(self) -> None:
        """Load metadata from file."""
        try:
            if self.metadata_file.exists():
                with open(self.metadata_file, 'r') as f:
                    data = json.load(f)
                
                self._metadata = {
                    key: FileCacheEntry.from_dict(entry_data)
                    for key, entry_data in data.items()
                }
                
                # Verify files exist
                missing_keys = []
                for key, entry in self._metadata.items():
                    filepath = self.cache_dir / entry.filename
                    if not filepath.exists():
                        missing_keys.append(key)
                
                # Remove entries for missing files
                for key in missing_keys:
                    del self._metadata[key]
                
                if missing_keys:
                    self._save_metadata()
                    self._logger.debug(f"Removed {len(missing_keys)} entries for missing files")
                    
        except Exception as e:
            self._logger.error(f"Error loading cache metadata: {e}")
            self._metadata = {}
    
    def _save_metadata(self) -> None:
        """Save metadata to file."""
        try:
            data = {
                key: entry.to_dict()
                for key, entry in self._metadata.items()
            }
            
            # Write to temporary file first
            temp_file = self.metadata_file.with_suffix('.tmp')
            with open(temp_file, 'w') as f:
                json.dump(data, f, indent=2)
            
            # Atomic rename
            temp_file.replace(self.metadata_file)
            
        except Exception as e:
            self._logger.error(f"Error saving cache metadata: {e}")
    
    def _periodic_cleanup(self) -> None:
        """Periodic cleanup of expired entries."""
        while True:
            try:
                time.sleep(self.cleanup_interval)
                self.cleanup_expired()
            except Exception as e:
                self._logger.error(f"Error in periodic cleanup: {e}")


# Global file cache instance
_global_file_cache = None


def get_file_cache() -> FileCache:
    """Get global file cache instance."""
    global _global_file_cache
    if _global_file_cache is None:
        _global_file_cache = FileCache()
    return _global_file_cache