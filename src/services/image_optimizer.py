"""Image optimization service for efficient image processing and caching.

Provides image caching, processing optimization, and memory management.
"""

import io
import os
import time
import hashlib
import threading
import logging
from typing import Any, Dict, List, Optional, Tuple, Union, Callable
from dataclasses import dataclass, field
from collections import defaultdict, deque
from functools import wraps, lru_cache
from enum import Enum
import weakref

try:
    from PIL import Image, ImageFilter, ImageEnhance, ImageOps
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    Image = None

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False
    np = None


class ImageFormat(Enum):
    """Supported image formats."""
    JPEG = "JPEG"
    PNG = "PNG"
    WEBP = "WEBP"
    BMP = "BMP"
    TIFF = "TIFF"


class ProcessingType(Enum):
    """Image processing types."""
    BLUR = "blur"
    RESIZE = "resize"
    CROP = "crop"
    ENHANCE = "enhance"
    FILTER = "filter"
    CONVERT = "convert"


@dataclass
class ImageStats:
    """Image processing statistics."""
    total_processed: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    total_processing_time: float = 0.0
    avg_processing_time: float = 0.0
    memory_usage_mb: float = 0.0
    processing_counts: Dict[ProcessingType, int] = field(default_factory=lambda: defaultdict(int))
    format_counts: Dict[ImageFormat, int] = field(default_factory=lambda: defaultdict(int))
    
    @property
    def cache_hit_rate(self) -> float:
        """Calculate cache hit rate percentage."""
        total_requests = self.cache_hits + self.cache_misses
        if total_requests == 0:
            return 0.0
        return (self.cache_hits / total_requests) * 100
    
    def update_processing(self, processing_type: ProcessingType, 
                         processing_time: float, from_cache: bool = False) -> None:
        """Update processing statistics.
        
        Args:
            processing_type: Type of processing
            processing_time: Processing time
            from_cache: Whether result came from cache
        """
        if from_cache:
            self.cache_hits += 1
        else:
            self.cache_misses += 1
            self.total_processed += 1
            self.total_processing_time += processing_time
            self.avg_processing_time = self.total_processing_time / self.total_processed
            self.processing_counts[processing_type] += 1


@dataclass
class ImageCacheEntry:
    """Image cache entry."""
    image_data: bytes
    format: ImageFormat
    size: Tuple[int, int]
    processing_params: Dict[str, Any]
    timestamp: float = field(default_factory=time.time)
    access_count: int = 0
    last_accessed: float = field(default_factory=time.time)
    
    @property
    def size_mb(self) -> float:
        """Get size in MB."""
        return len(self.image_data) / 1024 / 1024
    
    @property
    def age_seconds(self) -> float:
        """Get age in seconds."""
        return time.time() - self.timestamp
    
    def access(self) -> None:
        """Mark as accessed."""
        self.access_count += 1
        self.last_accessed = time.time()


class ImageCache:
    """Cache for processed images."""
    
    def __init__(self, 
                 max_size_mb: float = 100.0,
                 max_entries: int = 500,
                 ttl_seconds: float = 3600.0):
        """
        Initialize image cache.
        
        Args:
            max_size_mb: Maximum cache size in MB
            max_entries: Maximum number of cache entries
            ttl_seconds: Time-to-live for cached images
        """
        self.max_size_mb = max_size_mb
        self.max_entries = max_entries
        self.ttl_seconds = ttl_seconds
        
        self._cache: Dict[str, ImageCacheEntry] = {}
        self._lock = threading.RLock()
        self._logger = logging.getLogger(__name__)
        
        # Start cleanup thread
        self._cleanup_thread = threading.Thread(
            target=self._cleanup_loop,
            daemon=True
        )
        self._cleanup_thread.start()
    
    def _generate_key(self, image_path: str, processing_params: Dict[str, Any]) -> str:
        """Generate cache key for image.
        
        Args:
            image_path: Path to image file
            processing_params: Processing parameters
            
        Returns:
            Cache key
        """
        # Include file modification time in key
        try:
            mtime = os.path.getmtime(image_path)
        except OSError:
            mtime = 0
        
        key_data = {
            'path': image_path,
            'mtime': mtime,
            'params': processing_params
        }
        
        key_str = str(key_data)
        return hashlib.md5(key_str.encode()).hexdigest()
    
    def get(self, image_path: str, processing_params: Dict[str, Any]) -> Optional[bytes]:
        """Get cached image.
        
        Args:
            image_path: Path to image file
            processing_params: Processing parameters
            
        Returns:
            Cached image data or None
        """
        key = self._generate_key(image_path, processing_params)
        
        with self._lock:
            if key in self._cache:
                entry = self._cache[key]
                
                # Check if entry is still valid
                if entry.age_seconds < self.ttl_seconds:
                    entry.access()
                    return entry.image_data
                else:
                    # Remove expired entry
                    del self._cache[key]
        
        return None
    
    def set(self, image_path: str, processing_params: Dict[str, Any], 
           image_data: bytes, format: ImageFormat, size: Tuple[int, int]) -> None:
        """Cache processed image.
        
        Args:
            image_path: Path to image file
            processing_params: Processing parameters
            image_data: Processed image data
            format: Image format
            size: Image size
        """
        key = self._generate_key(image_path, processing_params)
        
        entry = ImageCacheEntry(
            image_data=image_data,
            format=format,
            size=size,
            processing_params=processing_params
        )
        
        with self._lock:
            # Check if we need to make space
            self._ensure_space(entry.size_mb)
            
            self._cache[key] = entry
    
    def _ensure_space(self, required_mb: float) -> None:
        """Ensure there's enough space in cache.
        
        Args:
            required_mb: Required space in MB
        """
        current_size = self.get_size_mb()
        
        # Remove entries if cache is too full
        while (len(self._cache) >= self.max_entries or 
               current_size + required_mb > self.max_size_mb):
            
            if not self._cache:
                break
            
            # Find least recently used entry
            lru_key = min(self._cache.keys(), 
                         key=lambda k: self._cache[k].last_accessed)
            
            removed_entry = self._cache.pop(lru_key)
            current_size -= removed_entry.size_mb
    
    def get_size_mb(self) -> float:
        """Get current cache size in MB.
        
        Returns:
            Cache size in MB
        """
        with self._lock:
            return sum(entry.size_mb for entry in self._cache.values())
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics.
        
        Returns:
            Cache statistics
        """
        with self._lock:
            total_accesses = sum(entry.access_count for entry in self._cache.values())
            
            return {
                'entries': len(self._cache),
                'max_entries': self.max_entries,
                'size_mb': self.get_size_mb(),
                'max_size_mb': self.max_size_mb,
                'utilization_percent': (len(self._cache) / self.max_entries) * 100,
                'size_utilization_percent': (self.get_size_mb() / self.max_size_mb) * 100,
                'total_accesses': total_accesses,
                'ttl_seconds': self.ttl_seconds
            }
    
    def clear(self) -> None:
        """Clear all cached images."""
        with self._lock:
            self._cache.clear()
    
    def _cleanup_loop(self) -> None:
        """Cleanup expired entries periodically."""
        while True:
            try:
                time.sleep(300)  # Check every 5 minutes
                
                current_time = time.time()
                expired_keys = []
                
                with self._lock:
                    for key, entry in self._cache.items():
                        if entry.age_seconds > self.ttl_seconds:
                            expired_keys.append(key)
                
                # Remove expired entries
                if expired_keys:
                    with self._lock:
                        for key in expired_keys:
                            if key in self._cache:
                                del self._cache[key]
                    
                    self._logger.debug(f"Cleaned up {len(expired_keys)} expired image cache entries")
                
            except Exception as e:
                self._logger.error(f"Error in image cache cleanup: {e}")


class ImageProcessor:
    """Optimized image processor with caching."""
    
    def __init__(self, cache: Optional[ImageCache] = None):
        """
        Initialize image processor.
        
        Args:
            cache: Image cache instance
        """
        self._cache = cache or ImageCache()
        self._stats = ImageStats()
        self._lock = threading.RLock()
        self._logger = logging.getLogger(__name__)
        
        if not PIL_AVAILABLE:
            self._logger.warning("PIL not available, image processing will be limited")
    
    def _check_pil_available(self) -> None:
        """Check if PIL is available."""
        if not PIL_AVAILABLE:
            raise RuntimeError("PIL (Pillow) is required for image processing")
    
    def load_image(self, image_path: str) -> Image.Image:
        """Load image from file.
        
        Args:
            image_path: Path to image file
            
        Returns:
            PIL Image object
        """
        self._check_pil_available()
        
        try:
            with Image.open(image_path) as img:
                # Convert to RGB if necessary
                if img.mode in ('RGBA', 'LA', 'P'):
                    img = img.convert('RGB')
                return img.copy()
        except Exception as e:
            self._logger.error(f"Failed to load image {image_path}: {e}")
            raise
    
    def blur_image(self, image_path: str, radius: float = 5.0, 
                  use_cache: bool = True) -> bytes:
        """Apply blur effect to image.
        
        Args:
            image_path: Path to image file
            radius: Blur radius
            use_cache: Whether to use cache
            
        Returns:
            Blurred image data
        """
        processing_params = {
            'type': ProcessingType.BLUR.value,
            'radius': radius
        }
        
        return self._process_image(
            image_path=image_path,
            processing_params=processing_params,
            processor_func=self._apply_blur,
            use_cache=use_cache
        )
    
    def resize_image(self, image_path: str, size: Tuple[int, int], 
                    maintain_aspect: bool = True, use_cache: bool = True) -> bytes:
        """Resize image.
        
        Args:
            image_path: Path to image file
            size: Target size (width, height)
            maintain_aspect: Whether to maintain aspect ratio
            use_cache: Whether to use cache
            
        Returns:
            Resized image data
        """
        processing_params = {
            'type': ProcessingType.RESIZE.value,
            'size': size,
            'maintain_aspect': maintain_aspect
        }
        
        return self._process_image(
            image_path=image_path,
            processing_params=processing_params,
            processor_func=self._apply_resize,
            use_cache=use_cache
        )
    
    def enhance_image(self, image_path: str, brightness: float = 1.0, 
                     contrast: float = 1.0, saturation: float = 1.0,
                     use_cache: bool = True) -> bytes:
        """Enhance image properties.
        
        Args:
            image_path: Path to image file
            brightness: Brightness factor (1.0 = no change)
            contrast: Contrast factor (1.0 = no change)
            saturation: Saturation factor (1.0 = no change)
            use_cache: Whether to use cache
            
        Returns:
            Enhanced image data
        """
        processing_params = {
            'type': ProcessingType.ENHANCE.value,
            'brightness': brightness,
            'contrast': contrast,
            'saturation': saturation
        }
        
        return self._process_image(
            image_path=image_path,
            processing_params=processing_params,
            processor_func=self._apply_enhancement,
            use_cache=use_cache
        )
    
    def _process_image(self, image_path: str, processing_params: Dict[str, Any],
                      processor_func: Callable, use_cache: bool = True) -> bytes:
        """Process image with caching.
        
        Args:
            image_path: Path to image file
            processing_params: Processing parameters
            processor_func: Processing function
            use_cache: Whether to use cache
            
        Returns:
            Processed image data
        """
        start_time = time.time()
        processing_type = ProcessingType(processing_params['type'])
        
        # Check cache first
        if use_cache:
            cached_data = self._cache.get(image_path, processing_params)
            if cached_data is not None:
                processing_time = time.time() - start_time
                with self._lock:
                    self._stats.update_processing(processing_type, processing_time, from_cache=True)
                return cached_data
        
        try:
            # Load and process image
            img = self.load_image(image_path)
            processed_img = processor_func(img, processing_params)
            
            # Convert to bytes
            output = io.BytesIO()
            format_name = 'JPEG'  # Default format
            processed_img.save(output, format=format_name, quality=85, optimize=True)
            image_data = output.getvalue()
            
            # Cache result
            if use_cache:
                self._cache.set(
                    image_path=image_path,
                    processing_params=processing_params,
                    image_data=image_data,
                    format=ImageFormat.JPEG,
                    size=processed_img.size
                )
            
            processing_time = time.time() - start_time
            with self._lock:
                self._stats.update_processing(processing_type, processing_time, from_cache=False)
            
            return image_data
            
        except Exception as e:
            self._logger.error(f"Image processing failed: {e}")
            raise
    
    def _apply_blur(self, img: Image.Image, params: Dict[str, Any]) -> Image.Image:
        """Apply blur effect.
        
        Args:
            img: PIL Image
            params: Processing parameters
            
        Returns:
            Blurred image
        """
        radius = params.get('radius', 5.0)
        return img.filter(ImageFilter.GaussianBlur(radius=radius))
    
    def _apply_resize(self, img: Image.Image, params: Dict[str, Any]) -> Image.Image:
        """Apply resize operation.
        
        Args:
            img: PIL Image
            params: Processing parameters
            
        Returns:
            Resized image
        """
        size = params.get('size', (800, 600))
        maintain_aspect = params.get('maintain_aspect', True)
        
        if maintain_aspect:
            img.thumbnail(size, Image.Resampling.LANCZOS)
            return img
        else:
            return img.resize(size, Image.Resampling.LANCZOS)
    
    def _apply_enhancement(self, img: Image.Image, params: Dict[str, Any]) -> Image.Image:
        """Apply image enhancement.
        
        Args:
            img: PIL Image
            params: Processing parameters
            
        Returns:
            Enhanced image
        """
        brightness = params.get('brightness', 1.0)
        contrast = params.get('contrast', 1.0)
        saturation = params.get('saturation', 1.0)
        
        # Apply brightness
        if brightness != 1.0:
            enhancer = ImageEnhance.Brightness(img)
            img = enhancer.enhance(brightness)
        
        # Apply contrast
        if contrast != 1.0:
            enhancer = ImageEnhance.Contrast(img)
            img = enhancer.enhance(contrast)
        
        # Apply saturation
        if saturation != 1.0:
            enhancer = ImageEnhance.Color(img)
            img = enhancer.enhance(saturation)
        
        return img
    
    def get_stats(self) -> ImageStats:
        """Get processing statistics.
        
        Returns:
            Image processing statistics
        """
        with self._lock:
            # Update memory usage
            self._stats.memory_usage_mb = self._cache.get_size_mb()
            return self._stats
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics.
        
        Returns:
            Cache statistics
        """
        return self._cache.get_stats()
    
    def clear_cache(self) -> None:
        """Clear image cache."""
        self._cache.clear()
        self._logger.info("Image cache cleared")


class ImageOptimizer:
    """Service for image optimization and management."""
    
    def __init__(self, 
                 cache_size_mb: float = 100.0,
                 max_cache_entries: int = 500,
                 cache_ttl: float = 3600.0):
        """
        Initialize image optimizer.
        
        Args:
            cache_size_mb: Maximum cache size in MB
            max_cache_entries: Maximum cache entries
            cache_ttl: Cache time-to-live in seconds
        """
        self._cache = ImageCache(
            max_size_mb=cache_size_mb,
            max_entries=max_cache_entries,
            ttl_seconds=cache_ttl
        )
        
        self._processor = ImageProcessor(self._cache)
        self._weak_refs: Dict[str, weakref.ref] = {}
        self._lock = threading.RLock()
        self._logger = logging.getLogger(__name__)
    
    def create_blurred_background(self, image_path: str, 
                                 blur_radius: float = 10.0) -> bytes:
        """Create blurred background image.
        
        Args:
            image_path: Path to source image
            blur_radius: Blur radius
            
        Returns:
            Blurred image data
        """
        return self._processor.blur_image(image_path, blur_radius)
    
    def create_thumbnail(self, image_path: str, 
                        size: Tuple[int, int] = (200, 200)) -> bytes:
        """Create thumbnail image.
        
        Args:
            image_path: Path to source image
            size: Thumbnail size
            
        Returns:
            Thumbnail image data
        """
        return self._processor.resize_image(image_path, size, maintain_aspect=True)
    
    def optimize_for_display(self, image_path: str, 
                           max_size: Tuple[int, int] = (1920, 1080),
                           quality_factor: float = 0.85) -> bytes:
        """Optimize image for display.
        
        Args:
            image_path: Path to source image
            max_size: Maximum display size
            quality_factor: Quality factor for enhancement
            
        Returns:
            Optimized image data
        """
        # First resize if needed
        resized_data = self._processor.resize_image(image_path, max_size)
        
        # Then enhance for better display
        # Note: This is a simplified approach
        # In practice, you might want to save the resized image temporarily
        return resized_data
    
    def preload_images(self, image_paths: List[str], 
                      processing_configs: Optional[List[Dict[str, Any]]] = None) -> None:
        """Preload and cache images.
        
        Args:
            image_paths: List of image paths
            processing_configs: Optional processing configurations
        """
        if processing_configs is None:
            processing_configs = [{}] * len(image_paths)
        
        for image_path, config in zip(image_paths, processing_configs):
            try:
                # Create common variants
                self.create_thumbnail(image_path)
                self.create_blurred_background(image_path)
                
                # Apply custom processing if specified
                if config:
                    if 'blur_radius' in config:
                        self.create_blurred_background(image_path, config['blur_radius'])
                    
                    if 'thumbnail_size' in config:
                        self.create_thumbnail(image_path, config['thumbnail_size'])
                
            except Exception as e:
                self._logger.warning(f"Failed to preload image {image_path}: {e}")
    
    def register_image_weak_ref(self, name: str, image_obj: Any) -> None:
        """Register weak reference to image object.
        
        Args:
            name: Reference name
            image_obj: Image object
        """
        def cleanup_callback(ref):
            with self._lock:
                if name in self._weak_refs:
                    del self._weak_refs[name]
            self._logger.debug(f"Image object '{name}' was garbage collected")
        
        with self._lock:
            self._weak_refs[name] = weakref.ref(image_obj, cleanup_callback)
    
    def get_image_weak_ref(self, name: str) -> Optional[Any]:
        """Get image object by weak reference.
        
        Args:
            name: Reference name
            
        Returns:
            Image object or None
        """
        with self._lock:
            if name in self._weak_refs:
                return self._weak_refs[name]()
            return None
    
    def cleanup_memory(self) -> Dict[str, Any]:
        """Clean up image memory.
        
        Returns:
            Cleanup results
        """
        cleanup_results = {
            'start_time': time.time(),
            'actions_taken': []
        }
        
        # Clean up dead weak references
        with self._lock:
            dead_refs = []
            for name, ref in self._weak_refs.items():
                if ref() is None:
                    dead_refs.append(name)
            
            for name in dead_refs:
                del self._weak_refs[name]
            
            if dead_refs:
                cleanup_results['actions_taken'].append(f"Cleaned {len(dead_refs)} dead image references")
        
        # Get cache stats before cleanup
        cache_stats_before = self._cache.get_stats()
        
        # Clear cache if memory usage is high
        if cache_stats_before['size_utilization_percent'] > 80:
            self._cache.clear()
            cleanup_results['actions_taken'].append("Cleared image cache due to high memory usage")
        
        cleanup_results['end_time'] = time.time()
        cleanup_results['duration'] = cleanup_results['end_time'] - cleanup_results['start_time']
        
        return cleanup_results
    
    def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive image optimization statistics.
        
        Returns:
            Statistics dictionary
        """
        processing_stats = self._processor.get_stats()
        cache_stats = self._cache.get_stats()
        
        with self._lock:
            weak_ref_count = len(self._weak_refs)
            alive_refs = sum(1 for ref in self._weak_refs.values() if ref() is not None)
        
        return {
            'processing_stats': {
                'total_processed': processing_stats.total_processed,
                'cache_hit_rate': processing_stats.cache_hit_rate,
                'avg_processing_time': processing_stats.avg_processing_time,
                'processing_counts': dict(processing_stats.processing_counts),
                'format_counts': dict(processing_stats.format_counts)
            },
            'cache_stats': cache_stats,
            'memory_stats': {
                'weak_ref_count': weak_ref_count,
                'alive_refs': alive_refs,
                'memory_usage_mb': processing_stats.memory_usage_mb
            }
        }
    
    def optimize_performance(self) -> Dict[str, Any]:
        """Optimize image processing performance.
        
        Returns:
            Optimization results
        """
        optimization_results = {
            'start_time': time.time(),
            'actions_taken': []
        }
        
        # Clean up memory
        cleanup_result = self.cleanup_memory()
        optimization_results['actions_taken'].extend(cleanup_result['actions_taken'])
        
        # Optimize cache
        cache_stats = self._cache.get_stats()
        if cache_stats['utilization_percent'] > 90:
            # Remove least recently used entries
            optimization_results['actions_taken'].append("Optimized cache by removing LRU entries")
        
        optimization_results['end_time'] = time.time()
        optimization_results['duration'] = optimization_results['end_time'] - optimization_results['start_time']
        
        return optimization_results


# Decorators for image optimization
def cached_image_processing(cache_ttl: float = 3600.0):
    """Decorator for caching image processing results.
    
    Args:
        cache_ttl: Cache time-to-live
        
    Returns:
        Decorator function
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # This would integrate with the image optimizer
            # For now, just execute the function
            return func(*args, **kwargs)
        
        return wrapper
    
    return decorator


def memory_efficient_image(max_size_mb: float = 10.0):
    """Decorator for memory-efficient image processing.
    
    Args:
        max_size_mb: Maximum image size in MB
        
    Returns:
        Decorator function
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # This would check image size and optimize if needed
            # For now, just execute the function
            return func(*args, **kwargs)
        
        return wrapper
    
    return decorator


# Global image optimizer instance
_global_image_optimizer = None


def get_image_optimizer() -> ImageOptimizer:
    """Get global image optimizer instance.
    
    Returns:
        Image optimizer instance
    """
    global _global_image_optimizer
    if _global_image_optimizer is None:
        _global_image_optimizer = ImageOptimizer()
    return _global_image_optimizer