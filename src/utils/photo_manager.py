"""Photo Manager Utility

This module provides comprehensive photo management functionality for the weather journal,
including image processing, thumbnail generation, and photo organization.
"""

import os
import shutil
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple, Dict, Any
from PIL import Image, ImageOps, ExifTags
import hashlib
import json


class PhotoManager:
    """Manages photo operations for the weather journal."""
    
    SUPPORTED_FORMATS = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.webp'}
    THUMBNAIL_SIZE = (150, 150)
    MAX_IMAGE_SIZE = (1920, 1080)  # Max size for stored images
    PHOTOS_DIR = "assets/photos"
    THUMBNAILS_DIR = "assets/photos/thumbnails"
    
    def __init__(self, base_path: str = "."):
        """Initialize the photo manager.
        
        Args:
            base_path: Base directory path for the application
        """
        self.base_path = Path(base_path)
        self.photos_dir = self.base_path / self.PHOTOS_DIR
        self.thumbnails_dir = self.base_path / self.THUMBNAILS_DIR
        self.logger = logging.getLogger(__name__)
        
        # Create directories if they don't exist
        self._ensure_directories()
        
        # Load photo metadata
        self.metadata_file = self.photos_dir / "photo_metadata.json"
        self.metadata = self._load_metadata()
    
    def _ensure_directories(self) -> None:
        """Ensure photo and thumbnail directories exist."""
        try:
            self.photos_dir.mkdir(parents=True, exist_ok=True)
            self.thumbnails_dir.mkdir(parents=True, exist_ok=True)
            self.logger.info(f"Photo directories ensured: {self.photos_dir}")
        except Exception as e:
            self.logger.error(f"Failed to create photo directories: {e}")
            raise
    
    def _load_metadata(self) -> Dict[str, Any]:
        """Load photo metadata from JSON file.
        
        Returns:
            Dictionary containing photo metadata
        """
        if self.metadata_file.exists():
            try:
                with open(self.metadata_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                self.logger.warning(f"Failed to load photo metadata: {e}")
        
        return {"photos": {}, "version": "1.0"}
    
    def _save_metadata(self) -> None:
        """Save photo metadata to JSON file."""
        try:
            with open(self.metadata_file, 'w', encoding='utf-8') as f:
                json.dump(self.metadata, f, indent=2, ensure_ascii=False)
        except Exception as e:
            self.logger.error(f"Failed to save photo metadata: {e}")
    
    def _get_image_hash(self, image_path: Path) -> str:
        """Generate hash for image file.
        
        Args:
            image_path: Path to image file
            
        Returns:
            SHA256 hash of the image
        """
        hash_sha256 = hashlib.sha256()
        with open(image_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)
        return hash_sha256.hexdigest()[:16]  # Use first 16 characters
    
    def _fix_image_orientation(self, image: Image.Image) -> Image.Image:
        """Fix image orientation based on EXIF data.
        
        Args:
            image: PIL Image object
            
        Returns:
            Image with corrected orientation
        """
        try:
            # Get EXIF data
            exif = image._getexif()
            if exif is not None:
                for tag, value in exif.items():
                    if tag in ExifTags.TAGS and ExifTags.TAGS[tag] == 'Orientation':
                        if value == 3:
                            image = image.rotate(180, expand=True)
                        elif value == 6:
                            image = image.rotate(270, expand=True)
                        elif value == 8:
                            image = image.rotate(90, expand=True)
                        break
        except (AttributeError, KeyError, TypeError):
            # No EXIF data or orientation info
            pass
        
        return image
    
    def _resize_image(self, image: Image.Image, max_size: Tuple[int, int]) -> Image.Image:
        """Resize image while maintaining aspect ratio.
        
        Args:
            image: PIL Image object
            max_size: Maximum size (width, height)
            
        Returns:
            Resized image
        """
        # Calculate new size maintaining aspect ratio
        image.thumbnail(max_size, Image.Resampling.LANCZOS)
        return image
    
    def _generate_filename(self, original_name: str, entry_id: Optional[int] = None) -> str:
        """Generate unique filename for photo.
        
        Args:
            original_name: Original filename
            entry_id: Journal entry ID (optional)
            
        Returns:
            Generated filename
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        name_part = Path(original_name).stem[:20]  # Limit length
        extension = Path(original_name).suffix.lower()
        
        if entry_id:
            return f"entry_{entry_id}_{timestamp}_{name_part}{extension}"
        else:
            return f"{timestamp}_{name_part}{extension}"
    
    def add_photo(self, source_path: str, entry_id: Optional[int] = None, 
                  description: str = "") -> Optional[str]:
        """Add a photo to the journal.
        
        Args:
            source_path: Path to source image file
            entry_id: Journal entry ID to associate with
            description: Optional description for the photo
            
        Returns:
            Relative path to stored photo or None if failed
        """
        try:
            source_path = Path(source_path)
            
            # Validate file exists and format
            if not source_path.exists():
                self.logger.error(f"Source image not found: {source_path}")
                return None
            
            if source_path.suffix.lower() not in self.SUPPORTED_FORMATS:
                self.logger.error(f"Unsupported image format: {source_path.suffix}")
                return None
            
            # Generate unique filename
            new_filename = self._generate_filename(source_path.name, entry_id)
            photo_path = self.photos_dir / new_filename
            thumbnail_path = self.thumbnails_dir / new_filename
            
            # Open and process image
            with Image.open(source_path) as image:
                # Convert to RGB if necessary
                if image.mode in ('RGBA', 'LA', 'P'):
                    background = Image.new('RGB', image.size, (255, 255, 255))
                    if image.mode == 'P':
                        image = image.convert('RGBA')
                    background.paste(image, mask=image.split()[-1] if image.mode in ('RGBA', 'LA') else None)
                    image = background
                
                # Fix orientation
                image = self._fix_image_orientation(image)
                
                # Resize main image if too large
                if image.size[0] > self.MAX_IMAGE_SIZE[0] or image.size[1] > self.MAX_IMAGE_SIZE[1]:
                    image = self._resize_image(image, self.MAX_IMAGE_SIZE)
                
                # Save main image
                image.save(photo_path, 'JPEG', quality=85, optimize=True)
                
                # Create and save thumbnail
                thumbnail = image.copy()
                thumbnail = ImageOps.fit(thumbnail, self.THUMBNAIL_SIZE, Image.Resampling.LANCZOS)
                thumbnail.save(thumbnail_path, 'JPEG', quality=80, optimize=True)
            
            # Generate image hash for duplicate detection
            image_hash = self._get_image_hash(photo_path)
            
            # Store metadata
            relative_path = str(Path(self.PHOTOS_DIR) / new_filename)
            self.metadata["photos"][relative_path] = {
                "original_name": source_path.name,
                "entry_id": entry_id,
                "description": description,
                "added_at": datetime.now().isoformat(),
                "file_size": photo_path.stat().st_size,
                "dimensions": list(Image.open(photo_path).size),
                "hash": image_hash
            }
            
            self._save_metadata()
            
            self.logger.info(f"Photo added successfully: {relative_path}")
            return relative_path
            
        except Exception as e:
            self.logger.error(f"Failed to add photo: {e}")
            return None
    
    def remove_photo(self, photo_path: str) -> bool:
        """Remove a photo and its thumbnail.
        
        Args:
            photo_path: Relative path to photo
            
        Returns:
            True if removed successfully, False otherwise
        """
        try:
            full_photo_path = self.base_path / photo_path
            thumbnail_path = self.thumbnails_dir / Path(photo_path).name
            
            # Remove files
            if full_photo_path.exists():
                full_photo_path.unlink()
            
            if thumbnail_path.exists():
                thumbnail_path.unlink()
            
            # Remove from metadata
            if photo_path in self.metadata["photos"]:
                del self.metadata["photos"][photo_path]
                self._save_metadata()
            
            self.logger.info(f"Photo removed successfully: {photo_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to remove photo: {e}")
            return False
    
    def get_photo_info(self, photo_path: str) -> Optional[Dict[str, Any]]:
        """Get information about a photo.
        
        Args:
            photo_path: Relative path to photo
            
        Returns:
            Photo information dictionary or None
        """
        return self.metadata["photos"].get(photo_path)
    
    def get_thumbnail_path(self, photo_path: str) -> str:
        """Get thumbnail path for a photo.
        
        Args:
            photo_path: Relative path to photo
            
        Returns:
            Relative path to thumbnail
        """
        filename = Path(photo_path).name
        return str(Path(self.THUMBNAILS_DIR) / filename)
    
    def get_photos_for_entry(self, entry_id: int) -> List[Dict[str, Any]]:
        """Get all photos associated with a journal entry.
        
        Args:
            entry_id: Journal entry ID
            
        Returns:
            List of photo information dictionaries
        """
        photos = []
        for path, info in self.metadata["photos"].items():
            if info.get("entry_id") == entry_id:
                photo_info = info.copy()
                photo_info["path"] = path
                photo_info["thumbnail_path"] = self.get_thumbnail_path(path)
                photos.append(photo_info)
        
        return sorted(photos, key=lambda x: x.get("added_at", ""))
    
    def find_duplicate_photos(self) -> List[List[str]]:
        """Find duplicate photos based on hash.
        
        Returns:
            List of lists containing paths of duplicate photos
        """
        hash_groups = {}
        
        for path, info in self.metadata["photos"].items():
            photo_hash = info.get("hash")
            if photo_hash:
                if photo_hash not in hash_groups:
                    hash_groups[photo_hash] = []
                hash_groups[photo_hash].append(path)
        
        # Return only groups with duplicates
        return [paths for paths in hash_groups.values() if len(paths) > 1]
    
    def cleanup_orphaned_photos(self) -> int:
        """Remove photos that are not referenced in metadata.
        
        Returns:
            Number of orphaned photos removed
        """
        removed_count = 0
        
        try:
            # Check main photos directory
            for photo_file in self.photos_dir.glob("*"):
                if photo_file.is_file() and photo_file.name != "photo_metadata.json":
                    relative_path = str(Path(self.PHOTOS_DIR) / photo_file.name)
                    if relative_path not in self.metadata["photos"]:
                        photo_file.unlink()
                        removed_count += 1
                        self.logger.info(f"Removed orphaned photo: {photo_file.name}")
            
            # Check thumbnails directory
            for thumb_file in self.thumbnails_dir.glob("*"):
                if thumb_file.is_file():
                    main_photo_path = str(Path(self.PHOTOS_DIR) / thumb_file.name)
                    if main_photo_path not in self.metadata["photos"]:
                        thumb_file.unlink()
                        self.logger.info(f"Removed orphaned thumbnail: {thumb_file.name}")
            
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")
        
        return removed_count
    
    def get_storage_stats(self) -> Dict[str, Any]:
        """Get storage statistics for photos.
        
        Returns:
            Dictionary with storage statistics
        """
        stats = {
            "total_photos": len(self.metadata["photos"]),
            "total_size_bytes": 0,
            "total_size_mb": 0,
            "average_size_bytes": 0,
            "formats": {},
            "entries_with_photos": set()
        }
        
        for path, info in self.metadata["photos"].items():
            file_size = info.get("file_size", 0)
            stats["total_size_bytes"] += file_size
            
            # Track format
            ext = Path(path).suffix.lower()
            stats["formats"][ext] = stats["formats"].get(ext, 0) + 1
            
            # Track entries with photos
            if info.get("entry_id"):
                stats["entries_with_photos"].add(info["entry_id"])
        
        stats["total_size_mb"] = round(stats["total_size_bytes"] / (1024 * 1024), 2)
        stats["entries_with_photos"] = len(stats["entries_with_photos"])
        
        if stats["total_photos"] > 0:
            stats["average_size_bytes"] = stats["total_size_bytes"] // stats["total_photos"]
        
        return stats
    
    def export_photos(self, entry_ids: List[int], export_dir: str) -> bool:
        """Export photos for specific entries to a directory.
        
        Args:
            entry_ids: List of entry IDs to export photos for
            export_dir: Directory to export photos to
            
        Returns:
            True if export successful, False otherwise
        """
        try:
            export_path = Path(export_dir)
            export_path.mkdir(parents=True, exist_ok=True)
            
            exported_count = 0
            
            for path, info in self.metadata["photos"].items():
                if info.get("entry_id") in entry_ids:
                    source_path = self.base_path / path
                    if source_path.exists():
                        dest_path = export_path / Path(path).name
                        shutil.copy2(source_path, dest_path)
                        exported_count += 1
            
            self.logger.info(f"Exported {exported_count} photos to {export_dir}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to export photos: {e}")
            return False