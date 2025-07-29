"""Helper Utilities

Common utility functions for data processing and operations.
"""

import json
import hashlib
import time
import threading
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Callable, TypeVar, Union
from functools import wraps
import os
import sys

T = TypeVar('T')


class Debouncer:
    """Debounce function calls to prevent excessive API requests."""
    
    def __init__(self, delay: float = 0.5):
        """Initialize debouncer.
        
        Args:
            delay: Delay in seconds before executing the function
        """
        self.delay = delay
        self._timer: Optional[threading.Timer] = None
        self._lock = threading.Lock()
    
    def __call__(self, func: Callable[..., Any]) -> Callable[..., None]:
        """Decorator to debounce function calls."""
        @wraps(func)
        def wrapper(*args, **kwargs):
            with self._lock:
                if self._timer is not None:
                    self._timer.cancel()
                
                self._timer = threading.Timer(
                    self.delay,
                    lambda: func(*args, **kwargs)
                )
                self._timer.start()
        
        return wrapper
    
    def cancel(self):
        """Cancel any pending debounced calls."""
        with self._lock:
            if self._timer is not None:
                self._timer.cancel()
                self._timer = None


class SimpleCache:
    """Simple in-memory cache with TTL support."""
    
    def __init__(self, default_ttl: int = 300):
        """Initialize cache.
        
        Args:
            default_ttl: Default time-to-live in seconds
        """
        self.default_ttl = default_ttl
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache.
        
        Args:
            key: Cache key
        
        Returns:
            Cached value or None if not found/expired
        """
        with self._lock:
            if key not in self._cache:
                return None
            
            entry = self._cache[key]
            
            # Check if expired
            if time.time() > entry['expires_at']:
                del self._cache[key]
                return None
            
            return entry['value']
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set value in cache.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time-to-live in seconds (uses default if None)
        """
        if ttl is None:
            ttl = self.default_ttl
        
        with self._lock:
            self._cache[key] = {
                'value': value,
                'expires_at': time.time() + ttl,
                'created_at': time.time()
            }
    
    def delete(self, key: str) -> bool:
        """Delete value from cache.
        
        Args:
            key: Cache key
        
        Returns:
            True if key was deleted, False if not found
        """
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False
    
    def clear(self) -> None:
        """Clear all cached values."""
        with self._lock:
            self._cache.clear()
    
    def cleanup_expired(self) -> int:
        """Remove expired entries from cache.
        
        Returns:
            Number of entries removed
        """
        current_time = time.time()
        removed_count = 0
        
        with self._lock:
            expired_keys = [
                key for key, entry in self._cache.items()
                if current_time > entry['expires_at']
            ]
            
            for key in expired_keys:
                del self._cache[key]
                removed_count += 1
        
        return removed_count
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics.
        
        Returns:
            Dictionary with cache statistics
        """
        with self._lock:
            current_time = time.time()
            total_entries = len(self._cache)
            expired_entries = sum(
                1 for entry in self._cache.values()
                if current_time > entry['expires_at']
            )
            
            return {
                'total_entries': total_entries,
                'active_entries': total_entries - expired_entries,
                'expired_entries': expired_entries,
                'default_ttl': self.default_ttl
            }


def generate_cache_key(*args, **kwargs) -> str:
    """Generate a cache key from function arguments.
    
    Args:
        *args: Positional arguments
        **kwargs: Keyword arguments
    
    Returns:
        MD5 hash of the arguments as cache key
    """
    # Create a string representation of all arguments
    key_data = {
        'args': args,
        'kwargs': sorted(kwargs.items())
    }
    
    # Convert to JSON string (sorted for consistency)
    key_string = json.dumps(key_data, sort_keys=True, default=str)
    
    # Generate MD5 hash
    return hashlib.md5(key_string.encode()).hexdigest()


def retry_on_failure(
    max_retries: int = 3,
    delay: float = 1.0,
    backoff_factor: float = 2.0,
    exceptions: tuple = (Exception,)
) -> Callable:
    """Decorator to retry function calls on failure.
    
    Args:
        max_retries: Maximum number of retry attempts
        delay: Initial delay between retries in seconds
        backoff_factor: Multiplier for delay after each retry
        exceptions: Tuple of exceptions to catch and retry on
    
    Returns:
        Decorated function
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            last_exception = None
            current_delay = delay
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    
                    if attempt < max_retries:
                        time.sleep(current_delay)
                        current_delay *= backoff_factor
                    else:
                        # Last attempt failed, re-raise the exception
                        raise last_exception
            
            # This should never be reached, but just in case
            raise last_exception
        
        return wrapper
    return decorator


def safe_divide(numerator: Union[int, float], denominator: Union[int, float], default: float = 0.0) -> float:
    """Safely divide two numbers, returning default on division by zero.
    
    Args:
        numerator: Number to divide
        denominator: Number to divide by
        default: Default value to return on division by zero
    
    Returns:
        Result of division or default value
    """
    try:
        if denominator == 0:
            return default
        return float(numerator) / float(denominator)
    except (TypeError, ValueError):
        return default


def safe_get(dictionary: Dict[str, Any], key: str, default: Any = None) -> Any:
    """Safely get value from dictionary with nested key support.
    
    Args:
        dictionary: Dictionary to search
        key: Key to search for (supports dot notation for nested keys)
        default: Default value if key not found
    
    Returns:
        Value from dictionary or default
    """
    if not isinstance(dictionary, dict):
        return default
    
    # Handle nested keys with dot notation
    keys = key.split('.')
    current = dictionary
    
    for k in keys:
        if isinstance(current, dict) and k in current:
            current = current[k]
        else:
            return default
    
    return current


def clamp(value: Union[int, float], min_val: Union[int, float], max_val: Union[int, float]) -> Union[int, float]:
    """Clamp a value between minimum and maximum bounds.
    
    Args:
        value: Value to clamp
        min_val: Minimum allowed value
        max_val: Maximum allowed value
    
    Returns:
        Clamped value
    """
    return max(min_val, min(value, max_val))


def interpolate(value: float, from_range: tuple, to_range: tuple) -> float:
    """Interpolate a value from one range to another.
    
    Args:
        value: Value to interpolate
        from_range: Tuple of (min, max) for input range
        to_range: Tuple of (min, max) for output range
    
    Returns:
        Interpolated value
    """
    from_min, from_max = from_range
    to_min, to_max = to_range
    
    # Avoid division by zero
    if from_max == from_min:
        return to_min
    
    # Calculate interpolation
    ratio = (value - from_min) / (from_max - from_min)
    return to_min + ratio * (to_max - to_min)


def get_resource_path(relative_path: str) -> str:
    """Get absolute path to resource, works for dev and PyInstaller.
    
    Args:
        relative_path: Relative path to resource
    
    Returns:
        Absolute path to resource
    """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except AttributeError:
        # Normal Python execution
        base_path = os.path.abspath(".")
    
    return os.path.join(base_path, relative_path)


def ensure_directory(directory_path: str) -> bool:
    """Ensure directory exists, create if it doesn't.
    
    Args:
        directory_path: Path to directory
    
    Returns:
        True if directory exists or was created successfully
    """
    try:
        os.makedirs(directory_path, exist_ok=True)
        return True
    except (OSError, PermissionError):
        return False


def get_file_size(file_path: str) -> Optional[int]:
    """Get file size in bytes.
    
    Args:
        file_path: Path to file
    
    Returns:
        File size in bytes or None if file doesn't exist
    """
    try:
        return os.path.getsize(file_path)
    except (OSError, FileNotFoundError):
        return None


def is_file_older_than(file_path: str, seconds: int) -> bool:
    """Check if file is older than specified number of seconds.
    
    Args:
        file_path: Path to file
        seconds: Number of seconds
    
    Returns:
        True if file is older than specified time
    """
    try:
        file_time = os.path.getmtime(file_path)
        return (time.time() - file_time) > seconds
    except (OSError, FileNotFoundError):
        return True  # Treat missing files as "old"


def truncate_string(text: str, max_length: int, suffix: str = "...") -> str:
    """Truncate string to maximum length with optional suffix.
    
    Args:
        text: Text to truncate
        max_length: Maximum allowed length
        suffix: Suffix to add when truncating
    
    Returns:
        Truncated string
    """
    if len(text) <= max_length:
        return text
    
    if len(suffix) >= max_length:
        return text[:max_length]
    
    return text[:max_length - len(suffix)] + suffix


def parse_duration(duration_str: str) -> Optional[int]:
    """Parse duration string to seconds.
    
    Args:
        duration_str: Duration string (e.g., '5m', '1h', '30s')
    
    Returns:
        Duration in seconds or None if invalid
    """
    if not duration_str:
        return None
    
    duration_str = duration_str.strip().lower()
    
    # Extract number and unit
    import re
    match = re.match(r'^(\d+)([smhd]?)$', duration_str)
    
    if not match:
        return None
    
    number, unit = match.groups()
    number = int(number)
    
    # Convert to seconds
    multipliers = {
        's': 1,
        'm': 60,
        'h': 3600,
        'd': 86400,
        '': 1  # Default to seconds
    }
    
    return number * multipliers.get(unit, 1)


def format_duration(seconds: int) -> str:
    """Format seconds into human-readable duration.
    
    Args:
        seconds: Duration in seconds
    
    Returns:
        Formatted duration string
    """
    if seconds < 60:
        return f"{seconds}s"
    elif seconds < 3600:
        minutes = seconds // 60
        remaining_seconds = seconds % 60
        if remaining_seconds == 0:
            return f"{minutes}m"
        return f"{minutes}m {remaining_seconds}s"
    elif seconds < 86400:
        hours = seconds // 3600
        remaining_minutes = (seconds % 3600) // 60
        if remaining_minutes == 0:
            return f"{hours}h"
        return f"{hours}h {remaining_minutes}m"
    else:
        days = seconds // 86400
        remaining_hours = (seconds % 86400) // 3600
        if remaining_hours == 0:
            return f"{days}d"
        return f"{days}d {remaining_hours}h"


def merge_dicts(*dicts: Dict[str, Any]) -> Dict[str, Any]:
    """Merge multiple dictionaries, with later ones taking precedence.
    
    Args:
        *dicts: Dictionaries to merge
    
    Returns:
        Merged dictionary
    """
    result = {}
    for d in dicts:
        if isinstance(d, dict):
            result.update(d)
    return result


def flatten_dict(d: Dict[str, Any], parent_key: str = '', sep: str = '.') -> Dict[str, Any]:
    """Flatten nested dictionary.
    
    Args:
        d: Dictionary to flatten
        parent_key: Parent key prefix
        sep: Separator for nested keys
    
    Returns:
        Flattened dictionary
    """
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)


def chunk_list(lst: List[T], chunk_size: int) -> List[List[T]]:
    """Split list into chunks of specified size.
    
    Args:
        lst: List to chunk
        chunk_size: Size of each chunk
    
    Returns:
        List of chunks
    """
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]


def get_system_info() -> Dict[str, Any]:
    """Get basic system information.
    
    Returns:
        Dictionary with system information
    """
    import platform
    
    return {
        'platform': platform.system(),
        'platform_version': platform.version(),
        'architecture': platform.architecture()[0],
        'python_version': platform.python_version(),
        'hostname': platform.node(),
        'processor': platform.processor() or 'Unknown'
    }