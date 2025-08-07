from typing import Any, Optional, Callable
import pickle
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
import logging
import os

logger = logging.getLogger(__name__)

class IntelligentCache:
    """Intelligent cache manager with memory and disk persistence"""
    
    def __init__(self, base_dir="cache"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(exist_ok=True)
        self.memory_cache = {}
        self.cache_stats = {
            'hits': 0,
            'misses': 0,
            'evictions': 0
        }
        
    def get_or_compute(self, key: str, compute_func: Callable, 
                      ttl_minutes: int = 5, force_refresh: bool = False) -> Any:
        """Get from cache or compute if missing/expired"""
        if not force_refresh:
            cached = self.get(key)
            if cached is not None:
                self.cache_stats['hits'] += 1
                return cached
        
        self.cache_stats['misses'] += 1
        
        # Compute value
        try:
            value = compute_func()
            self.set(key, value, ttl_minutes)
            return value
        except Exception as e:
            logger.error(f"Failed to compute value for key {key}: {e}")
            return None
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        # Check memory cache first
        if key in self.memory_cache:
            entry = self.memory_cache[key]
            if self._is_valid(entry):
                entry['access_count'] += 1
                return entry['value']
            else:
                del self.memory_cache[key]
        
        # Check disk cache
        cache_file = self.base_dir / f"{self._hash_key(key)}.cache"
        if cache_file.exists():
            try:
                with open(cache_file, 'rb') as f:
                    entry = pickle.load(f)
                    if self._is_valid(entry):
                        entry['access_count'] += 1
                        self.memory_cache[key] = entry
                        return entry['value']
                    else:
                        cache_file.unlink()
            except Exception as e:
                logger.error(f"Failed to load cache file {cache_file}: {e}")
                if cache_file.exists():
                    cache_file.unlink()
        
        return None
    
    def set(self, key: str, value: Any, ttl_minutes: int = 5):
        """Set with automatic serialization"""
        cache_entry = {
            'value': value,
            'timestamp': datetime.now(),
            'ttl': timedelta(minutes=ttl_minutes),
            'access_count': 0
        }
        
        # Memory cache
        self.memory_cache[key] = cache_entry
        
        # Disk cache for persistence
        try:
            cache_file = self.base_dir / f"{self._hash_key(key)}.cache"
            with open(cache_file, 'wb') as f:
                pickle.dump(cache_entry, f)
        except Exception as e:
            logger.error(f"Failed to save cache file for key {key}: {e}")
        
        # Evict old entries if needed
        self._evict_if_needed()
    
    def _is_valid(self, entry: dict) -> bool:
        """Check if cache entry is still valid"""
        if 'timestamp' not in entry or 'ttl' not in entry:
            return False
        
        expiry_time = entry['timestamp'] + entry['ttl']
        return datetime.now() < expiry_time
    
    def _hash_key(self, key: str) -> str:
        """Create safe filename from key"""
        return hashlib.md5(key.encode()).hexdigest()
    
    def _evict_if_needed(self):
        """Smart eviction based on LRU and size"""
        max_memory_entries = 100
        max_disk_size_mb = 50
        
        # Memory eviction
        if len(self.memory_cache) > max_memory_entries:
            # Sort by access count and timestamp
            sorted_keys = sorted(
                self.memory_cache.keys(),
                key=lambda k: (
                    self.memory_cache[k]['access_count'],
                    self.memory_cache[k]['timestamp']
                )
            )
            
            # Evict least recently used
            for key in sorted_keys[:len(sorted_keys)//4]:
                del self.memory_cache[key]
                self.cache_stats['evictions'] += 1
        
        # Disk eviction based on size
        self._evict_disk_cache_by_size(max_disk_size_mb)
    
    def _evict_disk_cache_by_size(self, max_size_mb: int):
        """Evict disk cache files if total size exceeds limit"""
        try:
            total_size = 0
            cache_files = []
            
            for cache_file in self.base_dir.glob("*.cache"):
                if cache_file.is_file():
                    size = cache_file.stat().st_size
                    mtime = cache_file.stat().st_mtime
                    cache_files.append((cache_file, size, mtime))
                    total_size += size
            
            max_size_bytes = max_size_mb * 1024 * 1024
            
            if total_size > max_size_bytes:
                # Sort by modification time (oldest first)
                cache_files.sort(key=lambda x: x[2])
                
                # Remove oldest files until under limit
                for cache_file, size, _ in cache_files:
                    if total_size <= max_size_bytes:
                        break
                    
                    try:
                        cache_file.unlink()
                        total_size -= size
                        self.cache_stats['evictions'] += 1
                    except Exception as e:
                        logger.error(f"Failed to delete cache file {cache_file}: {e}")
        
        except Exception as e:
            logger.error(f"Failed to evict disk cache: {e}")
    
    def clear(self):
        """Clear all cache"""
        self.memory_cache.clear()
        
        try:
            for cache_file in self.base_dir.glob("*.cache"):
                cache_file.unlink()
        except Exception as e:
            logger.error(f"Failed to clear disk cache: {e}")
    
    def get_stats(self) -> dict:
        """Get cache statistics"""
        total_requests = self.cache_stats['hits'] + self.cache_stats['misses']
        hit_rate = (self.cache_stats['hits'] / total_requests * 100) if total_requests > 0 else 0
        
        return {
            **self.cache_stats,
            'hit_rate_percent': round(hit_rate, 2),
            'memory_entries': len(self.memory_cache),
            'disk_files': len(list(self.base_dir.glob("*.cache")))
        }
    
    def get_cache_size_mb(self) -> float:
        """Get total cache size in MB"""
        try:
            total_size = 0
            # Calculate disk cache size
            for cache_file in self.base_dir.glob("*.cache"):
                total_size += cache_file.stat().st_size
            return total_size / (1024 * 1024)
        except Exception as e:
            logger.error(f"Error calculating cache size: {e}")
            return 0.0
    
    def clear_all(self):
        """Clear all cache data"""
        try:
            # Clear memory cache
            self.memory_cache.clear()
            
            # Clear disk cache
            for cache_file in self.base_dir.glob("*.cache"):
                try:
                    cache_file.unlink()
                except Exception as e:
                    logger.error(f"Error deleting cache file {cache_file}: {e}")
            
            # Reset stats
            self.cache_stats = {'hits': 0, 'misses': 0, 'evictions': 0}
            logger.info("All cache cleared")
        except Exception as e:
            logger.error(f"Error clearing all cache: {e}")
    
    def clear_pattern(self, pattern: str):
        """Clear cache entries matching pattern"""
        try:
            # Clear from memory cache
            keys_to_remove = []
            for key in self.memory_cache.keys():
                if self._matches_pattern(key, pattern):
                    keys_to_remove.append(key)
            
            for key in keys_to_remove:
                del self.memory_cache[key]
            
            # Clear from disk cache
            for cache_file in self.base_dir.glob("*.cache"):
                try:
                    # Load and check if matches pattern
                    with open(cache_file, 'rb') as f:
                        entry = pickle.load(f)
                        # We need to reverse-engineer the key from filename
                        # This is a simplified approach
                        if pattern.replace('*', '') in cache_file.stem:
                            cache_file.unlink()
                except Exception as e:
                    logger.error(f"Error processing cache file {cache_file}: {e}")
            
            logger.info(f"Cleared cache entries matching pattern: {pattern}")
        except Exception as e:
            logger.error(f"Error clearing cache pattern {pattern}: {e}")
    
    def _matches_pattern(self, key: str, pattern: str) -> bool:
        """Check if key matches pattern (simple wildcard support)"""
        if '*' not in pattern:
            return key == pattern
        
        # Simple wildcard matching
        if pattern.endswith('*'):
            return key.startswith(pattern[:-1])
        elif pattern.startswith('*'):
            return key.endswith(pattern[1:])
        else:
            # Pattern has * in middle - more complex matching needed
            parts = pattern.split('*')
            if len(parts) == 2:
                return key.startswith(parts[0]) and key.endswith(parts[1])
        
        return False
    
    def clear_expired(self):
        """Clear expired cache entries"""
        try:
            # Clear expired from memory cache
            expired_keys = []
            for key, entry in self.memory_cache.items():
                if not self._is_valid(entry):
                    expired_keys.append(key)
            
            for key in expired_keys:
                del self.memory_cache[key]
            
            # Clear expired from disk cache
            for cache_file in self.base_dir.glob("*.cache"):
                try:
                    with open(cache_file, 'rb') as f:
                        entry = pickle.load(f)
                        if not self._is_valid(entry):
                            cache_file.unlink()
                except Exception as e:
                    logger.error(f"Error checking cache file {cache_file}: {e}")
            
            logger.info(f"Cleared {len(expired_keys)} expired cache entries")
        except Exception as e:
            logger.error(f"Error clearing expired cache: {e}")