#!/usr/bin/env python3
"""
Weather Journal Photo Manager - Photo attachment system

This module handles photo attachments for journal entries including:
- File upload and storage
- Thumbnail generation
- Photo gallery interface
- Image metadata extraction
"""

import os
import shutil
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from PIL import Image, ImageTk, ExifTags
import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox

from ...utils.logger import LoggerMixin
from ...ui.components.glass import (
    GlassFrame, GlassButton, GlassLabel, 
    ComponentSize, create_glass_card
)
from .database import JournalDatabase


class PhotoManager(LoggerMixin):
    """
    Manages photo attachments for journal entries.
    
    Handles file operations, thumbnail generation, and metadata extraction.
    """
    
    def __init__(self, database: JournalDatabase, storage_path: str = None):
        self.database = database
        self.storage_path = Path(storage_path or "data/journal_photos")
        self.thumbnail_path = self.storage_path / "thumbnails"
        
        # Create storage directories
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.thumbnail_path.mkdir(parents=True, exist_ok=True)
        
        # Supported image formats
        self.supported_formats = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp'}
        
        # Thumbnail settings
        self.thumbnail_size = (200, 200)
        self.preview_size = (400, 400)
        
        self.logger.info("Photo Manager initialized")
    
    def add_photo(self, entry_id: int, file_path: str, description: str = None) -> Optional[Dict]:
        """
        Add a photo to a journal entry.
        
        Args:
            entry_id: Journal entry ID
            file_path: Path to the source image file
            description: Optional photo description
            
        Returns:
            Dict with photo information or None if failed
        """
        try:
            source_path = Path(file_path)
            
            # Validate file
            if not source_path.exists():
                raise FileNotFoundError(f"Source file not found: {file_path}")
            
            if source_path.suffix.lower() not in self.supported_formats:
                raise ValueError(f"Unsupported image format: {source_path.suffix}")
            
            # Generate unique filename
            file_hash = self._generate_file_hash(source_path)
            filename = f"{file_hash}{source_path.suffix.lower()}"
            destination_path = self.storage_path / filename
            
            # Copy file to storage
            shutil.copy2(source_path, destination_path)
            
            # Generate thumbnail
            thumbnail_filename = f"thumb_{filename}"
            thumbnail_path = self.thumbnail_path / thumbnail_filename
            self._generate_thumbnail(destination_path, thumbnail_path)
            
            # Extract image metadata
            metadata = self._extract_image_metadata(destination_path)
            
            # Save to database
            photo_id = self.database.save_photo(
                entry_id=entry_id,
                filename=filename,
                original_filename=source_path.name,
                file_path=str(destination_path),
                thumbnail_path=str(thumbnail_path),
                file_size=destination_path.stat().st_size,
                width=metadata.get('width'),
                height=metadata.get('height'),
                description=description
            )
            
            photo_info = {
                'id': photo_id,
                'filename': filename,
                'original_filename': source_path.name,
                'file_path': str(destination_path),
                'thumbnail_path': str(thumbnail_path),
                'file_size': destination_path.stat().st_size,
                'width': metadata.get('width'),
                'height': metadata.get('height'),
                'description': description,
                'created_at': datetime.now().isoformat()
            }
            
            self.logger.info(f"Photo added successfully: {filename}")
            return photo_info
            
        except Exception as e:
            self.logger.error(f"Error adding photo: {e}")
            return None
    
    def remove_photo(self, photo_id: int) -> bool:
        """
        Remove a photo from storage and database.
        
        Args:
            photo_id: Photo ID to remove
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Get photo info from database
            photos = self.database.get_entry_photos(0)  # This needs to be fixed
            photo_info = None
            for photo in photos:
                if photo['id'] == photo_id:
                    photo_info = photo
                    break
            
            if not photo_info:
                self.logger.warning(f"Photo not found: {photo_id}")
                return False
            
            # Remove files
            file_path = Path(photo_info['file_path'])
            thumbnail_path = Path(photo_info['thumbnail_path'])
            
            if file_path.exists():
                file_path.unlink()
            
            if thumbnail_path.exists():
                thumbnail_path.unlink()
            
            # Remove from database
            success = self.database.delete_photo(photo_id)
            
            if success:
                self.logger.info(f"Photo removed successfully: {photo_id}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error removing photo: {e}")
            return False
    
    def get_entry_photos(self, entry_id: int) -> List[Dict]:
        """
        Get all photos for a journal entry.
        
        Args:
            entry_id: Journal entry ID
            
        Returns:
            List of photo dictionaries
        """
        return self.database.get_entry_photos(entry_id)
    
    def _generate_file_hash(self, file_path: Path) -> str:
        """
        Generate a unique hash for the file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            SHA256 hash string
        """
        hash_sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)
        return hash_sha256.hexdigest()[:16]  # Use first 16 characters
    
    def _generate_thumbnail(self, source_path: Path, thumbnail_path: Path) -> None:
        """
        Generate a thumbnail for the image.
        
        Args:
            source_path: Path to the source image
            thumbnail_path: Path where thumbnail will be saved
        """
        try:
            with Image.open(source_path) as img:
                # Convert to RGB if necessary
                if img.mode in ('RGBA', 'LA', 'P'):
                    img = img.convert('RGB')
                
                # Create thumbnail
                img.thumbnail(self.thumbnail_size, Image.Resampling.LANCZOS)
                img.save(thumbnail_path, 'JPEG', quality=85)
                
        except Exception as e:
            self.logger.error(f"Error generating thumbnail: {e}")
            # Create a placeholder thumbnail
            placeholder = Image.new('RGB', self.thumbnail_size, color='#2b2b2b')
            placeholder.save(thumbnail_path, 'JPEG')
    
    def _extract_image_metadata(self, image_path: Path) -> Dict:
        """
        Extract metadata from image file.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Dictionary with image metadata
        """
        metadata = {}
        
        try:
            with Image.open(image_path) as img:
                metadata['width'] = img.width
                metadata['height'] = img.height
                metadata['format'] = img.format
                metadata['mode'] = img.mode
                
                # Extract EXIF data if available
                if hasattr(img, '_getexif') and img._getexif():
                    exif = img._getexif()
                    if exif:
                        for tag_id, value in exif.items():
                            tag = ExifTags.TAGS.get(tag_id, tag_id)
                            metadata[f'exif_{tag}'] = value
                            
        except Exception as e:
            self.logger.error(f"Error extracting image metadata: {e}")
        
        return metadata


class PhotoGalleryWidget(GlassFrame):
    """
    Glassmorphic photo gallery widget for displaying journal photos.
    """
    
    def __init__(self, parent, photo_manager: PhotoManager, entry_id: int = None, **kwargs):
        super().__init__(parent, **kwargs)
        
        self.photo_manager = photo_manager
        self.entry_id = entry_id
        self.photos = []
        self.photo_widgets = []
        
        self._setup_ui()
        if entry_id:
            self.load_photos(entry_id)
    
    def _setup_ui(self):
        """Setup the gallery UI."""
        # Header
        header_frame = GlassFrame(self)
        header_frame.pack(fill="x", padx=10, pady=(10, 5))
        
        title_label = GlassLabel(
            header_frame,
            text="📸 Photo Gallery",
            font=("Segoe UI", 14, "bold")
        )
        title_label.pack(side="left", padx=10, pady=5)
        
        # Add photo button
        add_button = GlassButton(
            header_frame,
            text="+ Add Photo",
            command=self._add_photo_dialog,
            size=ComponentSize.SMALL
        )
        add_button.pack(side="right", padx=10, pady=5)
        
        # Gallery container with scrolling
        self.gallery_frame = ctk.CTkScrollableFrame(
            self,
            fg_color="transparent",
            scrollbar_button_color="#3d3d3d",
            scrollbar_button_hover_color="#4d4d4d"
        )
        self.gallery_frame.pack(fill="both", expand=True, padx=10, pady=5)
    
    def load_photos(self, entry_id: int):
        """Load photos for the specified entry."""
        self.entry_id = entry_id
        self.photos = self.photo_manager.get_entry_photos(entry_id)
        self._refresh_gallery()
    
    def _refresh_gallery(self):
        """Refresh the photo gallery display."""
        # Clear existing widgets
        for widget in self.photo_widgets:
            widget.destroy()
        self.photo_widgets.clear()
        
        if not self.photos:
            # Show empty state
            empty_label = GlassLabel(
                self.gallery_frame,
                text="No photos yet. Click 'Add Photo' to get started!",
                font=("Segoe UI", 12)
            )
            empty_label.pack(pady=50)
            self.photo_widgets.append(empty_label)
            return
        
        # Create photo grid
        columns = 3
        for i, photo in enumerate(self.photos):
            row = i // columns
            col = i % columns
            
            photo_card = self._create_photo_card(photo)
            photo_card.grid(row=row, column=col, padx=5, pady=5, sticky="nsew")
            self.photo_widgets.append(photo_card)
        
        # Configure grid weights
        for col in range(columns):
            self.gallery_frame.grid_columnconfigure(col, weight=1)
    
    def _create_photo_card(self, photo: Dict) -> GlassFrame:
        """Create a photo card widget."""
        card = create_glass_card(self.gallery_frame)
        
        try:
            # Load thumbnail
            if os.path.exists(photo['thumbnail_path']):
                img = Image.open(photo['thumbnail_path'])
                photo_image = ImageTk.PhotoImage(img)
                
                # Photo display
                photo_label = tk.Label(
                    card,
                    image=photo_image,
                    bg="#2b2b2b",
                    cursor="hand2"
                )
                photo_label.image = photo_image  # Keep reference
                photo_label.pack(pady=5)
                
                # Bind click event for full view
                photo_label.bind("<Button-1>", lambda e: self._show_photo_fullscreen(photo))
            
            # Photo info
            info_frame = GlassFrame(card)
            info_frame.pack(fill="x", padx=5, pady=5)
            
            filename_label = GlassLabel(
                info_frame,
                text=photo['original_filename'][:20] + "..." if len(photo['original_filename']) > 20 else photo['original_filename'],
                font=("Segoe UI", 10, "bold")
            )
            filename_label.pack()
            
            if photo['description']:
                desc_label = GlassLabel(
                    info_frame,
                    text=photo['description'][:30] + "..." if len(photo['description']) > 30 else photo['description'],
                    font=("Segoe UI", 9)
                )
                desc_label.pack()
            
            # Delete button
            delete_button = GlassButton(
                card,
                text="🗑️",
                command=lambda p=photo: self._delete_photo(p),
                size=ComponentSize.SMALL,
                width=30,
                height=30
            )
            delete_button.pack(pady=5)
            
        except Exception as e:
            # Error placeholder
            error_label = GlassLabel(
                card,
                text="❌ Error loading photo",
                font=("Segoe UI", 10)
            )
            error_label.pack(pady=20)
        
        return card
    
    def _add_photo_dialog(self):
        """Show dialog to add a new photo."""
        if not self.entry_id:
            messagebox.showwarning("No Entry", "Please save the journal entry first.")
            return
        
        file_path = filedialog.askopenfilename(
            title="Select Photo",
            filetypes=[
                ("Image files", "*.jpg *.jpeg *.png *.gif *.bmp *.tiff *.webp"),
                ("All files", "*.*")
            ]
        )
        
        if file_path:
            # Simple description dialog
            description = tk.simpledialog.askstring(
                "Photo Description",
                "Enter a description for this photo (optional):"
            )
            
            # Add photo
            photo_info = self.photo_manager.add_photo(self.entry_id, file_path, description)
            
            if photo_info:
                self.photos.append(photo_info)
                self._refresh_gallery()
                messagebox.showinfo("Success", "Photo added successfully!")
            else:
                messagebox.showerror("Error", "Failed to add photo.")
    
    def _delete_photo(self, photo: Dict):
        """Delete a photo after confirmation."""
        if messagebox.askyesno("Delete Photo", f"Are you sure you want to delete '{photo['original_filename']}'?"):
            if self.photo_manager.remove_photo(photo['id']):
                self.photos = [p for p in self.photos if p['id'] != photo['id']]
                self._refresh_gallery()
                messagebox.showinfo("Success", "Photo deleted successfully!")
            else:
                messagebox.showerror("Error", "Failed to delete photo.")
    
    def _show_photo_fullscreen(self, photo: Dict):
        """Show photo in fullscreen view."""
        # Create fullscreen window
        fullscreen_window = ctk.CTkToplevel(self)
        fullscreen_window.title(photo['original_filename'])
        fullscreen_window.geometry("800x600")
        fullscreen_window.transient(self)
        fullscreen_window.grab_set()
        
        try:
            # Load full-size image
            img = Image.open(photo['file_path'])
            
            # Resize to fit window while maintaining aspect ratio
            img.thumbnail((750, 550), Image.Resampling.LANCZOS)
            photo_image = ImageTk.PhotoImage(img)
            
            # Display image
            photo_label = tk.Label(
                fullscreen_window,
                image=photo_image,
                bg="#1a1a1a"
            )
            photo_label.image = photo_image  # Keep reference
            photo_label.pack(expand=True)
            
            # Info panel
            info_frame = ctk.CTkFrame(fullscreen_window)
            info_frame.pack(fill="x", padx=10, pady=10)
            
            info_text = f"File: {photo['original_filename']}\n"
            info_text += f"Size: {photo['width']}x{photo['height']}\n"
            info_text += f"File Size: {photo['file_size'] // 1024} KB\n"
            if photo['description']:
                info_text += f"Description: {photo['description']}"
            
            info_label = ctk.CTkLabel(
                info_frame,
                text=info_text,
                justify="left"
            )
            info_label.pack(pady=10)
            
        except Exception as e:
            error_label = ctk.CTkLabel(
                fullscreen_window,
                text=f"Error loading image: {e}",
                font=("Segoe UI", 14)
            )
            error_label.pack(expand=True)