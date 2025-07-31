"""Location Manager Component

Handles favorite locations, recent searches, and GPS detection.
"""

import customtkinter as ctk
from typing import Dict, List, Optional, Callable, Any
import json
import os
from datetime import datetime
import threading
import geocoder

from ..theme import DataTerminalTheme


class LocationData:
    """Data class for location information."""
    
    def __init__(self, name: str, lat: float, lon: float, country: str = "", 
                 region: str = "", timezone: str = ""):
        self.name = name
        self.lat = lat
        self.lon = lon
        self.country = country
        self.region = region
        self.timezone = timezone
        self.last_accessed = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'name': self.name,
            'lat': self.lat,
            'lon': self.lon,
            'country': self.country,
            'region': self.region,
            'timezone': self.timezone,
            'last_accessed': self.last_accessed.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'LocationData':
        """Create from dictionary."""
        location = cls(
            name=data['name'],
            lat=data['lat'],
            lon=data['lon'],
            country=data.get('country', ''),
            region=data.get('region', ''),
            timezone=data.get('timezone', '')
        )
        
        if 'last_accessed' in data:
            try:
                location.last_accessed = datetime.fromisoformat(data['last_accessed'])
            except:
                location.last_accessed = datetime.now()
        
        return location
    
    def get_display_name(self) -> str:
        """Get formatted display name."""
        if self.country and self.country != self.name:
            return f"{self.name}, {self.country}"
        return self.name
    
    def get_coordinates(self) -> tuple[float, float]:
        """Get coordinates as tuple."""
        return (self.lat, self.lon)


class LocationManager:
    """Manages favorite locations and recent searches."""
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        self.favorites_file = os.path.join(data_dir, "favorite_locations.json")
        self.recent_file = os.path.join(data_dir, "recent_searches.json")
        
        # Ensure data directory exists
        os.makedirs(data_dir, exist_ok=True)
        
        # Load data
        self.favorites: List[LocationData] = self._load_favorites()
        self.recent_searches: List[LocationData] = self._load_recent_searches()
        
        # Limits
        self.max_recent = 10
        self.max_favorites = 20
    
    def _load_favorites(self) -> List[LocationData]:
        """Load favorite locations from file."""
        try:
            if os.path.exists(self.favorites_file):
                with open(self.favorites_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return [LocationData.from_dict(item) for item in data]
        except Exception as e:
            print(f"Error loading favorites: {e}")
        return []
    
    def _load_recent_searches(self) -> List[LocationData]:
        """Load recent searches from file."""
        try:
            if os.path.exists(self.recent_file):
                with open(self.recent_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return [LocationData.from_dict(item) for item in data]
        except Exception as e:
            print(f"Error loading recent searches: {e}")
        return []
    
    def _save_favorites(self):
        """Save favorite locations to file."""
        try:
            data = [location.to_dict() for location in self.favorites]
            with open(self.favorites_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving favorites: {e}")
    
    def _save_recent_searches(self):
        """Save recent searches to file."""
        try:
            data = [location.to_dict() for location in self.recent_searches]
            with open(self.recent_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving recent searches: {e}")
    
    def add_to_favorites(self, location: LocationData) -> bool:
        """Add location to favorites."""
        # Check if already in favorites
        for fav in self.favorites:
            if (abs(fav.lat - location.lat) < 0.01 and 
                abs(fav.lon - location.lon) < 0.01):
                return False  # Already exists
        
        # Add to favorites
        self.favorites.insert(0, location)
        
        # Limit favorites
        if len(self.favorites) > self.max_favorites:
            self.favorites = self.favorites[:self.max_favorites]
        
        self._save_favorites()
        return True
    
    def remove_from_favorites(self, location: LocationData) -> bool:
        """Remove location from favorites."""
        for i, fav in enumerate(self.favorites):
            if (abs(fav.lat - location.lat) < 0.01 and 
                abs(fav.lon - location.lon) < 0.01):
                del self.favorites[i]
                self._save_favorites()
                return True
        return False
    
    def is_favorite(self, location: LocationData) -> bool:
        """Check if location is in favorites."""
        for fav in self.favorites:
            if (abs(fav.lat - location.lat) < 0.01 and 
                abs(fav.lon - location.lon) < 0.01):
                return True
        return False
    
    def add_to_recent(self, location: LocationData):
        """Add location to recent searches."""
        # Remove if already exists
        self.recent_searches = [
            loc for loc in self.recent_searches 
            if not (abs(loc.lat - location.lat) < 0.01 and 
                   abs(loc.lon - location.lon) < 0.01)
        ]
        
        # Add to front
        location.last_accessed = datetime.now()
        self.recent_searches.insert(0, location)
        
        # Limit recent searches
        if len(self.recent_searches) > self.max_recent:
            self.recent_searches = self.recent_searches[:self.max_recent]
        
        self._save_recent_searches()
    
    def get_favorites(self) -> List[LocationData]:
        """Get list of favorite locations."""
        return self.favorites.copy()
    
    def get_recent_searches(self) -> List[LocationData]:
        """Get list of recent searches."""
        return self.recent_searches.copy()
    
    def clear_recent_searches(self):
        """Clear all recent searches."""
        self.recent_searches.clear()
        self._save_recent_searches()
    
    def clear_favorites(self):
        """Clear all favorites."""
        self.favorites.clear()
        self._save_favorites()


class LocationManagerUI(ctk.CTkFrame):
    """UI component for managing locations."""
    
    def __init__(self, parent, location_manager: LocationManager, 
                 location_selected_callback: Callable[[LocationData], None]):
        super().__init__(parent, fg_color="transparent")
        
        self.location_manager = location_manager
        self.location_selected_callback = location_selected_callback
        self.current_location: Optional[LocationData] = None
        
        # Create UI
        self._create_location_ui()
        
        # Refresh display
        self.refresh_display()
    
    def _create_location_ui(self):
        """Create location management UI."""
        # Configure grid
        self.grid_columnconfigure((0, 1), weight=1)
        
        # GPS Location section
        self._create_gps_section()
        
        # Favorites section
        self._create_favorites_section()
        
        # Recent searches section
        self._create_recent_section()
    
    def _create_gps_section(self):
        """Create GPS location detection section."""
        gps_frame = ctk.CTkFrame(
            self,
            fg_color=DataTerminalTheme.CARD_BG,
            corner_radius=8,
            border_color=DataTerminalTheme.BORDER,
            border_width=1
        )
        gps_frame.grid(row=0, column=0, columnspan=2, padx=10, pady=5, sticky="ew")
        gps_frame.grid_columnconfigure(1, weight=1)
        
        # GPS button
        self.gps_button = ctk.CTkButton(
            gps_frame,
            text="📍 Use Current Location",
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color=DataTerminalTheme.PRIMARY,
            hover_color=DataTerminalTheme.HOVER,
            text_color=DataTerminalTheme.BACKGROUND,
            width=180,
            height=32,
            command=self.detect_current_location
        )
        self.gps_button.grid(row=0, column=0, padx=15, pady=15, sticky="w")
        
        # GPS status
        self.gps_status = ctk.CTkLabel(
            gps_frame,
            text="Click to detect your current location",
            font=ctk.CTkFont(size=11),
            text_color=DataTerminalTheme.TEXT_SECONDARY
        )
        self.gps_status.grid(row=0, column=1, padx=15, pady=15, sticky="w")
    
    def _create_favorites_section(self):
        """Create favorites section."""
        favorites_frame = ctk.CTkFrame(
            self,
            fg_color=DataTerminalTheme.CARD_BG,
            corner_radius=8,
            border_color=DataTerminalTheme.BORDER,
            border_width=1
        )
        favorites_frame.grid(row=1, column=0, padx=(10, 5), pady=5, sticky="ew")
        
        # Header
        fav_header_frame = ctk.CTkFrame(favorites_frame, fg_color="transparent")
        fav_header_frame.grid(row=0, column=0, padx=15, pady=(15, 5), sticky="ew")
        fav_header_frame.grid_columnconfigure(0, weight=1)
        
        fav_title = ctk.CTkLabel(
            fav_header_frame,
            text="⭐ Favorite Locations",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=DataTerminalTheme.PRIMARY
        )
        fav_title.grid(row=0, column=0, sticky="w")
        
        # Clear favorites button
        self.clear_fav_button = ctk.CTkButton(
            fav_header_frame,
            text="Clear",
            font=ctk.CTkFont(size=10),
            fg_color="transparent",
            text_color=DataTerminalTheme.TEXT_SECONDARY,
            hover_color=DataTerminalTheme.BORDER,
            width=50,
            height=24,
            command=self.clear_favorites
        )
        self.clear_fav_button.grid(row=0, column=1, sticky="e")
        
        # Favorites list
        self.favorites_frame = ctk.CTkScrollableFrame(
            favorites_frame,
            fg_color="transparent",
            height=150
        )
        self.favorites_frame.grid(row=1, column=0, padx=15, pady=(0, 15), sticky="ew")
    
    def _create_recent_section(self):
        """Create recent searches section."""
        recent_frame = ctk.CTkFrame(
            self,
            fg_color=DataTerminalTheme.CARD_BG,
            corner_radius=8,
            border_color=DataTerminalTheme.BORDER,
            border_width=1
        )
        recent_frame.grid(row=1, column=1, padx=(5, 10), pady=5, sticky="ew")
        
        # Header
        recent_header_frame = ctk.CTkFrame(recent_frame, fg_color="transparent")
        recent_header_frame.grid(row=0, column=0, padx=15, pady=(15, 5), sticky="ew")
        recent_header_frame.grid_columnconfigure(0, weight=1)
        
        recent_title = ctk.CTkLabel(
            recent_header_frame,
            text="🕒 Recent Searches",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=DataTerminalTheme.PRIMARY
        )
        recent_title.grid(row=0, column=0, sticky="w")
        
        # Clear recent button
        self.clear_recent_button = ctk.CTkButton(
            recent_header_frame,
            text="Clear",
            font=ctk.CTkFont(size=10),
            fg_color="transparent",
            text_color=DataTerminalTheme.TEXT_SECONDARY,
            hover_color=DataTerminalTheme.BORDER,
            width=50,
            height=24,
            command=self.clear_recent
        )
        self.clear_recent_button.grid(row=0, column=1, sticky="e")
        
        # Recent searches list
        self.recent_frame = ctk.CTkScrollableFrame(
            recent_frame,
            fg_color="transparent",
            height=150
        )
        self.recent_frame.grid(row=1, column=0, padx=15, pady=(0, 15), sticky="ew")
    
    def detect_current_location(self):
        """Detect current location using GPS/IP."""
        self.gps_button.configure(text="📍 Detecting...", state="disabled")
        self.gps_status.configure(text="Detecting your location...")
        
        def detect_location():
            try:
                # Try IP-based location first (faster)
                g = geocoder.ip('me')
                
                if g.ok:
                    location = LocationData(
                        name=g.city or "Current Location",
                        lat=g.latlng[0],
                        lon=g.latlng[1],
                        country=g.country or "",
                        region=g.state or ""
                    )
                    
                    self.current_location = location
                    
                    # Update UI on main thread
                    self.after(0, self._location_detected_success, location)
                else:
                    self.after(0, self._location_detected_error, "Unable to detect location")
                    
            except Exception as e:
                self.after(0, self._location_detected_error, str(e))
        
        # Run detection in background thread
        threading.Thread(target=detect_location, daemon=True).start()
    
    def _location_detected_success(self, location: LocationData):
        """Handle successful location detection."""
        self.gps_button.configure(text="📍 Use Current Location", state="normal")
        self.gps_status.configure(
            text=f"Current: {location.get_display_name()}",
            text_color=DataTerminalTheme.PRIMARY
        )
        
        # Add to recent searches
        self.location_manager.add_to_recent(location)
        self.refresh_display()
        
        # Notify callback
        self.location_selected_callback(location)
    
    def _location_detected_error(self, error_message: str):
        """Handle location detection error."""
        self.gps_button.configure(text="📍 Use Current Location", state="normal")
        self.gps_status.configure(
            text=f"Error: {error_message}",
            text_color="#FF6B6B"
        )
        
        # Reset status after 5 seconds
        self.after(5000, lambda: self.gps_status.configure(
            text="Click to detect your current location",
            text_color=DataTerminalTheme.TEXT_SECONDARY
        ))
    
    def refresh_display(self):
        """Refresh the favorites and recent searches display."""
        self._refresh_favorites()
        self._refresh_recent()
    
    def _refresh_favorites(self):
        """Refresh favorites list."""
        # Clear existing items
        for widget in self.favorites_frame.winfo_children():
            widget.destroy()
        
        favorites = self.location_manager.get_favorites()
        
        if not favorites:
            no_fav_label = ctk.CTkLabel(
                self.favorites_frame,
                text="No favorite locations yet",
                font=ctk.CTkFont(size=11),
                text_color=DataTerminalTheme.TEXT_SECONDARY
            )
            no_fav_label.grid(row=0, column=0, pady=10)
        else:
            for i, location in enumerate(favorites):
                self._create_location_item(self.favorites_frame, location, i, is_favorite=True)
    
    def _refresh_recent(self):
        """Refresh recent searches list."""
        # Clear existing items
        for widget in self.recent_frame.winfo_children():
            widget.destroy()
        
        recent = self.location_manager.get_recent_searches()
        
        if not recent:
            no_recent_label = ctk.CTkLabel(
                self.recent_frame,
                text="No recent searches",
                font=ctk.CTkFont(size=11),
                text_color=DataTerminalTheme.TEXT_SECONDARY
            )
            no_recent_label.grid(row=0, column=0, pady=10)
        else:
            for i, location in enumerate(recent):
                self._create_location_item(self.recent_frame, location, i, is_favorite=False)
    
    def _create_location_item(self, parent, location: LocationData, index: int, is_favorite: bool):
        """Create a location item widget."""
        item_frame = ctk.CTkFrame(
            parent,
            fg_color=DataTerminalTheme.BACKGROUND,
            corner_radius=6,
            border_color=DataTerminalTheme.BORDER,
            border_width=1
        )
        item_frame.grid(row=index, column=0, padx=5, pady=2, sticky="ew")
        item_frame.grid_columnconfigure(1, weight=1)
        
        # Location button
        location_button = ctk.CTkButton(
            item_frame,
            text=location.get_display_name(),
            font=ctk.CTkFont(size=11),
            fg_color="transparent",
            text_color=DataTerminalTheme.TEXT,
            hover_color=DataTerminalTheme.BORDER,
            anchor="w",
            command=lambda loc=location: self._select_location(loc)
        )
        location_button.grid(row=0, column=0, columnspan=2, padx=5, pady=5, sticky="ew")
        
        # Action buttons frame
        actions_frame = ctk.CTkFrame(item_frame, fg_color="transparent")
        actions_frame.grid(row=1, column=0, columnspan=2, padx=5, pady=(0, 5), sticky="ew")
        
        # Coordinates label
        coords_label = ctk.CTkLabel(
            actions_frame,
            text=f"{location.lat:.3f}, {location.lon:.3f}",
            font=ctk.CTkFont(size=9),
            text_color=DataTerminalTheme.TEXT_SECONDARY
        )
        coords_label.grid(row=0, column=0, sticky="w")
        
        # Favorite toggle button
        if is_favorite:
            fav_button = ctk.CTkButton(
                actions_frame,
                text="❌",
                font=ctk.CTkFont(size=10),
                fg_color="transparent",
                text_color="#FF6B6B",
                hover_color=DataTerminalTheme.BORDER,
                width=24,
                height=20,
                command=lambda loc=location: self._remove_favorite(loc)
            )
            fav_button.grid(row=0, column=1, sticky="e")
        else:
            # Check if already favorite
            if not self.location_manager.is_favorite(location):
                fav_button = ctk.CTkButton(
                    actions_frame,
                    text="⭐",
                    font=ctk.CTkFont(size=10),
                    fg_color="transparent",
                    text_color=DataTerminalTheme.PRIMARY,
                    hover_color=DataTerminalTheme.BORDER,
                    width=24,
                    height=20,
                    command=lambda loc=location: self._add_favorite(loc)
                )
                fav_button.grid(row=0, column=1, sticky="e")
    
    def _select_location(self, location: LocationData):
        """Select a location."""
        # Add to recent searches
        self.location_manager.add_to_recent(location)
        self.refresh_display()
        
        # Notify callback
        self.location_selected_callback(location)
    
    def _add_favorite(self, location: LocationData):
        """Add location to favorites."""
        if self.location_manager.add_to_favorites(location):
            self.refresh_display()
    
    def _remove_favorite(self, location: LocationData):
        """Remove location from favorites."""
        if self.location_manager.remove_from_favorites(location):
            self.refresh_display()
    
    def clear_favorites(self):
        """Clear all favorites."""
        self.location_manager.clear_favorites()
        self.refresh_display()
    
    def clear_recent(self):
        """Clear recent searches."""
        self.location_manager.clear_recent_searches()
        self.refresh_display()
    
    def add_location(self, location: LocationData):
        """Add a new location (from search results)."""
        self.location_manager.add_to_recent(location)
        self.refresh_display()