from typing import Callable, Optional, Tuple
import threading
import requests
from PIL import Image, ImageTk
from io import BytesIO
import logging
import tkinter as tk
from pathlib import Path
import hashlib
import os

logger = logging.getLogger(__name__)

class LazyImageLoader:
    """Lazy image loader with caching and async loading"""
    
    def __init__(self, cache_size_mb=20):
        self.image_cache = {}
        self.loading_images = set()
        self.placeholder = self.create_placeholder()
        self.max_cache_size = cache_size_mb * 1024 * 1024
        self.current_cache_size = 0
        self.cache_dir = Path("cache/images")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        
    def create_placeholder(self, size: Tuple[int, int] = (100, 100)) -> ImageTk.PhotoImage:
        """Create a placeholder image"""
        try:
            # Create a simple gray placeholder
            placeholder = Image.new('RGB', size, color='#f0f0f0')
            return ImageTk.PhotoImage(placeholder)
        except Exception as e:
            logger.error(f"Failed to create placeholder: {e}")
            return None
    
    def load_image_async(self, url: str, callback: Callable, 
                        size: Optional[Tuple[int, int]] = None,
                        widget: Optional[tk.Widget] = None):
        """Load image asynchronously with caching"""
        cache_key = self._get_cache_key(url, size)
        
        # Check memory cache
        with self._lock:
            if cache_key in self.image_cache:
                self._safe_callback(callback, self.image_cache[cache_key], widget)
                return
        
        # Check if already loading
        if cache_key in self.loading_images:
            return
        
        # Return placeholder immediately
        if self.placeholder:
            self._safe_callback(callback, self.placeholder, widget)
        
        # Load in background
        self.loading_images.add(cache_key)
        thread = threading.Thread(
            target=self._load_image,
            args=(url, callback, size, cache_key, widget)
        )
        thread.daemon = True
        thread.start()
    
    def _load_image(self, url: str, callback: Callable, 
                   size: Optional[Tuple[int, int]], cache_key: str,
                   widget: Optional[tk.Widget]):
        """Background image loading"""
        try:
            # Check disk cache first
            disk_image = self._load_from_disk(cache_key)
            if disk_image:
                with self._lock:
                    self.image_cache[cache_key] = disk_image
                self._safe_callback(callback, disk_image, widget)
                return
            
            # Download image
            response = requests.get(url, timeout=10, stream=True)
            response.raise_for_status()
            
            # Load and process image
            image = Image.open(BytesIO(response.content))
            
            if size:
                image = image.resize(size, Image.Resampling.LANCZOS)
            
            # Convert to PhotoImage
            photo_image = ImageTk.PhotoImage(image)
            
            # Cache management
            self._add_to_cache(cache_key, photo_image, image)
            
            # Callback on main thread
            self._safe_callback(callback, photo_image, widget)
                
        except Exception as e:
            logger.error(f"Failed to load image from {url}: {e}")
            # Use placeholder on error
            if self.placeholder:
                self._safe_callback(callback, self.placeholder, widget)
        finally:
            self.loading_images.discard(cache_key)
    
    def _safe_callback(self, callback: Callable, image: ImageTk.PhotoImage, 
                      widget: Optional[tk.Widget]):
        """Safely execute callback on main thread"""
        try:
            if widget and hasattr(widget, 'winfo_exists'):
                # Check if widget still exists
                if widget.winfo_exists():
                    widget.after(0, lambda: callback(image))
            else:
                callback(image)
        except Exception as e:
            logger.error(f"Failed to execute image callback: {e}")
    
    def _get_cache_key(self, url: str, size: Optional[Tuple[int, int]]) -> str:
        """Generate cache key for URL and size"""
        key_string = f"{url}_{size}" if size else url
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def _add_to_cache(self, cache_key: str, photo_image: ImageTk.PhotoImage, 
                     pil_image: Image.Image):
        """Add image to memory and disk cache"""
        with self._lock:
            # Add to memory cache
            self.image_cache[cache_key] = photo_image
            
            # Estimate size and manage cache
            estimated_size = self._estimate_image_size(pil_image)
            self.current_cache_size += estimated_size
            
            # Save to disk cache
            self._save_to_disk(cache_key, pil_image)
            
            # Evict if needed
            self._evict_if_needed()
    
    def _estimate_image_size(self, image: Image.Image) -> int:
        """Estimate memory size of image"""
        width, height = image.size
        channels = len(image.getbands())
        return width * height * channels
    
    def _save_to_disk(self, cache_key: str, image: Image.Image):
        """Save image to disk cache"""
        try:
            cache_file = self.cache_dir / f"{cache_key}.png"
            image.save(cache_file, "PNG")
        except Exception as e:
            logger.error(f"Failed to save image to disk: {e}")
    
    def _load_from_disk(self, cache_key: str) -> Optional[ImageTk.PhotoImage]:
        """Load image from disk cache"""
        try:
            cache_file = self.cache_dir / f"{cache_key}.png"
            if cache_file.exists():
                image = Image.open(cache_file)
                return ImageTk.PhotoImage(image)
        except Exception as e:
            logger.error(f"Failed to load image from disk: {e}")
        return None
    
    def _evict_if_needed(self):
        """Evict images if cache size exceeds limit"""
        if self.current_cache_size > self.max_cache_size:
            # Simple LRU eviction - remove half the cache
            items_to_remove = len(self.image_cache) // 2
            keys_to_remove = list(self.image_cache.keys())[:items_to_remove]
            
            for key in keys_to_remove:
                del self.image_cache[key]
                # Also remove from disk
                try:
                    cache_file = self.cache_dir / f"{key}.png"
                    if cache_file.exists():
                        cache_file.unlink()
                except Exception as e:
                    logger.error(f"Failed to remove disk cache file: {e}")
            
            # Recalculate cache size
            self.current_cache_size = self.current_cache_size // 2
    
    def preload_image(self, url: str, size: Optional[Tuple[int, int]] = None):
        """Preload image without callback"""
        self.load_image_async(url, lambda img: None, size)
    
    def clear_cache(self):
        """Clear all cached images"""
        with self._lock:
            self.image_cache.clear()
            self.current_cache_size = 0
            
            # Clear disk cache
            try:
                for cache_file in self.cache_dir.glob("*.png"):
                    cache_file.unlink()
            except Exception as e:
                logger.error(f"Failed to clear disk cache: {e}")
    
    def get_cache_stats(self) -> dict:
        """Get cache statistics"""
        with self._lock:
            disk_files = len(list(self.cache_dir.glob("*.png")))
            return {
                'memory_images': len(self.image_cache),
                'disk_images': disk_files,
                'cache_size_mb': round(self.current_cache_size / (1024 * 1024), 2),
                'loading_images': len(self.loading_images)
            }

# Global instance for easy access
_global_loader = None

def get_image_loader() -> LazyImageLoader:
    """Get global image loader instance"""
    global _global_loader
    if _global_loader is None:
        _global_loader = LazyImageLoader()
    return _global_loader