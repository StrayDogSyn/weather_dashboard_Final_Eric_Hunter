"""Enhanced Search Component

Advanced search interface with autocomplete, favorites, and recent searches.
"""

import customtkinter as ctk
import tkinter as tk
from typing import List, Dict, Any, Optional, Callable
import json
from pathlib import Path
import threading
from datetime import datetime

from ..theme import DataTerminalTheme


class EnhancedSearchComponent(ctk.CTkFrame):
    """Enhanced search component with autocomplete and favorites."""
    
    def __init__(self, parent, weather_service, on_location_selected: Callable[[Dict[str, Any]], None]):
        super().__init__(parent, fg_color=DataTerminalTheme.CARD_BG, corner_radius=8)
        
        self.weather_service = weather_service
        self.on_location_selected = on_location_selected
        
        # Search data
        self.search_suggestions: List[Dict[str, Any]] = []
        self.recent_searches: List[Dict[str, Any]] = []
        self.favorite_locations: List[Dict[str, Any]] = []
        
        # UI state
        self.suggestions_visible = False
        self.current_search_thread = None
        
        # Load saved data
        self._load_search_data()
        
        # Create UI
        self._create_search_ui()
        
    def _create_search_ui(self):
        """Create the enhanced search interface."""
        # Configure grid
        self.grid_columnconfigure(1, weight=1)
        
        # Search icon
        search_icon = ctk.CTkLabel(
            self,
            text="🔍",
            font=ctk.CTkFont(size=16),
            text_color=DataTerminalTheme.PRIMARY
        )
        search_icon.grid(row=0, column=0, padx=(10, 5), pady=10, sticky="w")
        
        # Search entry with enhanced styling
        self.search_entry = ctk.CTkEntry(
            self,
            placeholder_text="Search cities, coordinates, or airport codes...",
            font=ctk.CTkFont(size=14),
            fg_color=DataTerminalTheme.BACKGROUND,
            border_color=DataTerminalTheme.PRIMARY,
            text_color=DataTerminalTheme.TEXT,
            placeholder_text_color=DataTerminalTheme.TEXT_SECONDARY,
            height=40,
            corner_radius=6
        )
        self.search_entry.grid(row=0, column=1, padx=5, pady=10, sticky="ew")
        
        # Bind events
        self.search_entry.bind("<KeyRelease>", self._on_search_input)
        self.search_entry.bind("<Return>", self._on_search_submit)
        self.search_entry.bind("<FocusIn>", self._on_search_focus)
        self.search_entry.bind("<FocusOut>", self._on_search_blur)
        
        # GPS location button
        self.gps_button = ctk.CTkButton(
            self,
            text="📍",
            width=40,
            height=40,
            font=ctk.CTkFont(size=16),
            fg_color=DataTerminalTheme.CARD_BG,
            hover_color=DataTerminalTheme.PRIMARY,
            border_color=DataTerminalTheme.PRIMARY,
            border_width=1,
            corner_radius=6,
            command=self._detect_location
        )
        self.gps_button.grid(row=0, column=2, padx=(5, 10), pady=10)
        
        # Suggestions dropdown (initially hidden)
        self.suggestions_frame = ctk.CTkScrollableFrame(
            self,
            fg_color=DataTerminalTheme.BACKGROUND,
            border_color=DataTerminalTheme.PRIMARY,
            border_width=1,
            corner_radius=6,
            height=200
        )
        
        # Quick access buttons frame
        self.quick_access_frame = ctk.CTkFrame(
            self,
            fg_color="transparent",
            height=40
        )
        self.quick_access_frame.grid(row=2, column=0, columnspan=3, padx=10, pady=(0, 10), sticky="ew")
        self.quick_access_frame.grid_columnconfigure((0, 1, 2), weight=1)
        
        # Recent searches button
        self.recent_button = ctk.CTkButton(
            self.quick_access_frame,
            text="🕒 Recent",
            height=30,
            font=ctk.CTkFont(size=12),
            fg_color="transparent",
            text_color=DataTerminalTheme.TEXT_SECONDARY,
            hover_color=DataTerminalTheme.CARD_BG,
            command=self._show_recent_searches
        )
        self.recent_button.grid(row=0, column=0, padx=2, sticky="ew")
        
        # Favorites button
        self.favorites_button = ctk.CTkButton(
            self.quick_access_frame,
            text="⭐ Favorites",
            height=30,
            font=ctk.CTkFont(size=12),
            fg_color="transparent",
            text_color=DataTerminalTheme.TEXT_SECONDARY,
            hover_color=DataTerminalTheme.CARD_BG,
            command=self._show_favorites
        )
        self.favorites_button.grid(row=0, column=1, padx=2, sticky="ew")
        
        # Clear button
        self.clear_button = ctk.CTkButton(
            self.quick_access_frame,
            text="🗑️ Clear",
            height=30,
            font=ctk.CTkFont(size=12),
            fg_color="transparent",
            text_color=DataTerminalTheme.TEXT_SECONDARY,
            hover_color=DataTerminalTheme.CARD_BG,
            command=self._clear_search
        )
        self.clear_button.grid(row=0, column=2, padx=2, sticky="ew")
        
    def _on_search_input(self, event):
        """Handle search input with autocomplete."""
        query = self.search_entry.get().strip()
        
        if len(query) >= 2:  # Start searching after 2 characters
            # Cancel previous search thread
            if self.current_search_thread and self.current_search_thread.is_alive():
                return  # Let the current search complete
            
            # Start new search thread
            self.current_search_thread = threading.Thread(
                target=self._search_suggestions,
                args=(query,),
                daemon=True
            )
            self.current_search_thread.start()
        else:
            self._hide_suggestions()
    
    def _search_suggestions(self, query: str):
        """Search for location suggestions in background thread."""
        try:
            # Get suggestions from weather service
            suggestions = self.weather_service.search_locations(query, limit=8)
            
            # Update UI in main thread
            self.after(0, lambda: self._update_suggestions(suggestions))
            
        except Exception as e:
            print(f"Search error: {e}")
            self.after(0, self._hide_suggestions)
    
    def _update_suggestions(self, suggestions: List[Dict[str, Any]]):
        """Update suggestions dropdown."""
        self.search_suggestions = suggestions
        
        if suggestions:
            self._show_suggestions()
        else:
            self._hide_suggestions()
    
    def _show_suggestions(self):
        """Show suggestions dropdown."""
        if self.suggestions_visible:
            # Clear existing suggestions
            for widget in self.suggestions_frame.winfo_children():
                widget.destroy()
        else:
            # Show suggestions frame
            self.suggestions_frame.grid(row=1, column=0, columnspan=3, padx=10, pady=(0, 5), sticky="ew")
            self.suggestions_visible = True
        
        # Add suggestion items
        for i, suggestion in enumerate(self.search_suggestions):
            self._create_suggestion_item(suggestion, i)
    
    def _create_suggestion_item(self, location: Dict[str, Any], index: int):
        """Create a suggestion item."""
        # Suggestion button
        suggestion_btn = ctk.CTkButton(
            self.suggestions_frame,
            text=f"📍 {location.get('display', location.get('name', 'Unknown'))}",
            font=ctk.CTkFont(size=12),
            fg_color="transparent",
            text_color=DataTerminalTheme.TEXT,
            hover_color=DataTerminalTheme.PRIMARY,
            anchor="w",
            command=lambda loc=location: self._select_location(loc)
        )
        suggestion_btn.grid(row=index, column=0, padx=5, pady=2, sticky="ew")
        
        # Configure grid
        self.suggestions_frame.grid_columnconfigure(0, weight=1)
    
    def _hide_suggestions(self):
        """Hide suggestions dropdown."""
        if self.suggestions_visible:
            self.suggestions_frame.grid_remove()
            self.suggestions_visible = False
    
    def _on_search_focus(self, event):
        """Handle search entry focus."""
        # Show recent searches if no current input
        if not self.search_entry.get().strip() and self.recent_searches:
            self._show_recent_in_suggestions()
    
    def _on_search_blur(self, event):
        """Handle search entry blur."""
        # Hide suggestions after a short delay to allow clicking
        self.after(200, self._hide_suggestions)
    
    def _on_search_submit(self, event):
        """Handle search submission."""
        query = self.search_entry.get().strip()
        if query:
            # If there are suggestions, select the first one
            if self.search_suggestions:
                self._select_location(self.search_suggestions[0])
            else:
                # Try direct search
                self._search_direct(query)
    
    def _search_direct(self, query: str):
        """Perform direct search for location."""
        try:
            results = self.weather_service.search_locations(query, limit=1)
            if results:
                self._select_location(results[0])
            else:
                self._show_error(f"No results found for '{query}'")
        except Exception as e:
            self._show_error(f"Search error: {str(e)}")
    
    def _select_location(self, location: Dict[str, Any]):
        """Select a location and update weather."""
        # Hide suggestions
        self._hide_suggestions()
        
        # Update search entry
        self.search_entry.delete(0, tk.END)
        self.search_entry.insert(0, location.get('display', location.get('name', '')))
        
        # Add to recent searches
        self._add_to_recent(location)
        
        # Notify parent
        self.on_location_selected(location)
    
    def _detect_location(self):
        """Detect current location using GPS/IP."""
        self.gps_button.configure(text="⏳")
        
        def detect_thread():
            try:
                # Use IP-based geolocation as fallback
                import requests
                response = requests.get('http://ip-api.com/json/', timeout=5)
                data = response.json()
                
                if data['status'] == 'success':
                    location = {
                        'name': data['city'],
                        'country': data['country'],
                        'state': data.get('regionName', ''),
                        'lat': data['lat'],
                        'lon': data['lon'],
                        'display': f"{data['city']}, {data['country']}"
                    }
                    
                    self.after(0, lambda: self._select_location(location))
                else:
                    self.after(0, lambda: self._show_error("Could not detect location"))
                    
            except Exception as e:
                self.after(0, lambda: self._show_error(f"Location detection failed: {str(e)}"))
            finally:
                self.after(0, lambda: self.gps_button.configure(text="📍"))
        
        threading.Thread(target=detect_thread, daemon=True).start()
    
    def _show_recent_searches(self):
        """Show recent searches in suggestions."""
        if self.recent_searches:
            self.search_suggestions = self.recent_searches[:8]
            self._show_suggestions()
    
    def _show_favorites(self):
        """Show favorite locations in suggestions."""
        if self.favorite_locations:
            self.search_suggestions = self.favorite_locations
            self._show_suggestions()
    
    def _show_recent_in_suggestions(self):
        """Show recent searches when focused."""
        if self.recent_searches:
            self.search_suggestions = self.recent_searches[:5]
            self._show_suggestions()
    
    def _clear_search(self):
        """Clear search entry and hide suggestions."""
        self.search_entry.delete(0, tk.END)
        self._hide_suggestions()
    
    def _add_to_recent(self, location: Dict[str, Any]):
        """Add location to recent searches."""
        # Remove if already exists
        self.recent_searches = [loc for loc in self.recent_searches 
                               if loc.get('display') != location.get('display')]
        
        # Add to beginning
        location['timestamp'] = datetime.now().isoformat()
        self.recent_searches.insert(0, location)
        
        # Keep only last 10
        self.recent_searches = self.recent_searches[:10]
        
        # Save to file
        self._save_search_data()
    
    def add_to_favorites(self, location: Dict[str, Any]):
        """Add location to favorites."""
        # Check if already in favorites
        if not any(fav.get('display') == location.get('display') for fav in self.favorite_locations):
            self.favorite_locations.append(location)
            self._save_search_data()
            return True
        return False
    
    def remove_from_favorites(self, location: Dict[str, Any]):
        """Remove location from favorites."""
        self.favorite_locations = [fav for fav in self.favorite_locations 
                                  if fav.get('display') != location.get('display')]
        self._save_search_data()
    
    def is_favorite(self, location: Dict[str, Any]) -> bool:
        """Check if location is in favorites."""
        return any(fav.get('display') == location.get('display') for fav in self.favorite_locations)
    
    def _load_search_data(self):
        """Load search data from file."""
        try:
            data_file = Path.cwd() / 'data' / 'search_data.json'
            if data_file.exists():
                with open(data_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.recent_searches = data.get('recent', [])
                    self.favorite_locations = data.get('favorites', [])
        except Exception as e:
            print(f"Failed to load search data: {e}")
    
    def _save_search_data(self):
        """Save search data to file."""
        try:
            data_file = Path.cwd() / 'data' / 'search_data.json'
            data_file.parent.mkdir(exist_ok=True)
            
            data = {
                'recent': self.recent_searches,
                'favorites': self.favorite_locations
            }
            
            with open(data_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Failed to save search data: {e}")
    
    def _show_error(self, message: str):
        """Show error message."""
        # Create temporary error label
        error_label = ctk.CTkLabel(
            self,
            text=f"❌ {message}",
            font=ctk.CTkFont(size=12),
            text_color="#FF6B6B"
        )
        error_label.grid(row=3, column=0, columnspan=3, padx=10, pady=5)
        
        # Remove after 3 seconds
        self.after(3000, error_label.destroy)