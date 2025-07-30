"""Enhanced Search Bar Component

Advanced city search with autocomplete, favorites, recent searches, and geolocation.
"""

import customtkinter as ctk
import tkinter as tk
from typing import Callable, Optional, List, Dict, Any
import threading
import time
import json
from pathlib import Path
from datetime import datetime

from ui.theme import DataTerminalTheme
from utils.helpers import Debouncer


class FavoritesManager:
    """Manages favorite locations."""
    
    def __init__(self):
        """Initialize favorites manager."""
        self.favorites_file = Path.cwd() / 'cache' / 'favorites.json'
        self.favorites: List[Dict[str, str]] = []
        self._load_favorites()
    
    def _load_favorites(self) -> None:
        """Load favorites from file."""
        try:
            if self.favorites_file.exists():
                with open(self.favorites_file, 'r', encoding='utf-8') as f:
                    self.favorites = json.load(f)
        except (json.JSONDecodeError, OSError, FileNotFoundError):
            self.favorites = []
    
    def _save_favorites(self) -> None:
        """Save favorites to file."""
        try:
            self.favorites_file.parent.mkdir(exist_ok=True)
            with open(self.favorites_file, 'w', encoding='utf-8') as f:
                json.dump(self.favorites, f, indent=2)
        except (OSError, json.JSONEncodeError):
            pass
    
    def add_favorite(self, location: Dict[str, str]) -> None:
        """Add location to favorites."""
        # Remove if already exists
        self.favorites = [f for f in self.favorites if f.get('name') != location.get('name')]
        # Add to beginning
        self.favorites.insert(0, location)
        # Limit to 10 favorites
        self.favorites = self.favorites[:10]
        self._save_favorites()
    
    def remove_favorite(self, location_name: str) -> None:
        """Remove location from favorites."""
        self.favorites = [f for f in self.favorites if f.get('name') != location_name]
        self._save_favorites()
    
    def is_favorite(self, location_name: str) -> bool:
        """Check if location is in favorites."""
        return any(f.get('name') == location_name for f in self.favorites)
    
    def get_favorites(self) -> List[Dict[str, str]]:
        """Get all favorites."""
        return self.favorites.copy()


class RecentSearchesManager:
    """Manages recent search history."""
    
    def __init__(self):
        """Initialize recent searches manager."""
        self.recent_file = Path.cwd() / 'cache' / 'recent_searches.json'
        self.recent_searches: List[Dict[str, Any]] = []
        self._load_recent()
    
    def _load_recent(self) -> None:
        """Load recent searches from file."""
        try:
            if self.recent_file.exists():
                with open(self.recent_file, 'r', encoding='utf-8') as f:
                    self.recent_searches = json.load(f)
        except (json.JSONDecodeError, OSError, FileNotFoundError):
            self.recent_searches = []
    
    def _save_recent(self) -> None:
        """Save recent searches to file."""
        try:
            self.recent_file.parent.mkdir(exist_ok=True)
            with open(self.recent_file, 'w', encoding='utf-8') as f:
                json.dump(self.recent_searches, f, indent=2)
        except (OSError, json.JSONEncodeError):
            pass
    
    def add_search(self, location: Dict[str, str]) -> None:
        """Add location to recent searches."""
        # Remove if already exists
        self.recent_searches = [r for r in self.recent_searches 
                               if r.get('name') != location.get('name')]
        # Add to beginning with timestamp
        search_entry = location.copy()
        search_entry['timestamp'] = datetime.now().isoformat()
        self.recent_searches.insert(0, search_entry)
        # Limit to 20 recent searches
        self.recent_searches = self.recent_searches[:20]
        self._save_recent()
    
    def get_recent(self, limit: int = 10) -> List[Dict[str, str]]:
        """Get recent searches."""
        return self.recent_searches[:limit]


class SearchSuggestionDropdown(ctk.CTkFrame):
    """Enhanced dropdown with autocomplete, favorites, and recent searches."""
    
    def __init__(self, parent, on_select: Callable[[Dict[str, str]], None], 
                 favorites_manager: FavoritesManager, 
                 recent_manager: RecentSearchesManager, **kwargs):
        """Initialize suggestion dropdown."""
        super().__init__(parent, **DataTerminalTheme.get_frame_style("default"), **kwargs)
        
        self.on_select = on_select
        self.favorites_manager = favorites_manager
        self.recent_manager = recent_manager
        self.suggestion_buttons: List[ctk.CTkButton] = []
        
        # Configure grid
        self.grid_columnconfigure(0, weight=1)
        
        # Initially hidden
        self.grid_remove()
    
    def show_suggestions(self, suggestions: List[Dict[str, str]], 
                        show_favorites: bool = False, 
                        show_recent: bool = False) -> None:
        """Show suggestion dropdown with various content types."""
        # Clear existing buttons
        self.clear_suggestions()
        
        all_items = []
        
        # Add favorites section
        if show_favorites:
            favorites = self.favorites_manager.get_favorites()
            if favorites:
                all_items.append({'type': 'header', 'text': '⭐ FAVORITES'})
                for fav in favorites[:3]:  # Show top 3 favorites
                    fav_item = fav.copy()
                    fav_item['type'] = 'favorite'
                    all_items.append(fav_item)
        
        # Add recent searches section
        if show_recent and not suggestions:
            recent = self.recent_manager.get_recent(5)
            if recent:
                all_items.append({'type': 'header', 'text': '🕒 RECENT SEARCHES'})
                for rec in recent:
                    rec_item = rec.copy()
                    rec_item['type'] = 'recent'
                    all_items.append(rec_item)
        
        # Add autocomplete suggestions
        if suggestions:
            if all_items:  # Add separator if we have other content
                all_items.append({'type': 'header', 'text': '🔍 SUGGESTIONS'})
            for suggestion in suggestions[:5]:
                suggestion_item = suggestion.copy()
                suggestion_item['type'] = 'suggestion'
                all_items.append(suggestion_item)
        
        if not all_items:
            self.grid_remove()
            return
        
        # Create buttons for all items
        row = 0
        for item in all_items:
            if item['type'] == 'header':
                # Header label
                header = ctk.CTkLabel(
                    self,
                    text=item['text'],
                    **DataTerminalTheme.get_label_style("caption")
                )
                header.grid(row=row, column=0, sticky="ew", padx=10, pady=(5, 2))
                row += 1
            else:
                # Create button based on type
                display_text = item.get('display', item.get('name', ''))
                
                # Add icons based on type
                if item['type'] == 'favorite':
                    display_text = f"⭐ {display_text}"
                elif item['type'] == 'recent':
                    display_text = f"🕒 {display_text}"
                
                button = ctk.CTkButton(
                    self,
                    text=display_text,
                    command=lambda i=item: self._on_suggestion_click(i),
                    **DataTerminalTheme.get_button_style("secondary")
                )
                button.grid(row=row, column=0, sticky="ew", padx=5, pady=1)
                self.suggestion_buttons.append(button)
                row += 1
        
        # Show the frame
        self.grid()
    
    def clear_suggestions(self) -> None:
        """Clear all suggestion buttons."""
        for widget in self.winfo_children():
            widget.destroy()
        self.suggestion_buttons.clear()
        self.grid_remove()
    
    def _on_suggestion_click(self, item: Dict[str, str]) -> None:
        """Handle suggestion button click."""
        self.on_select(item)
        self.clear_suggestions()


class EnhancedSearchBarFrame(ctk.CTkFrame):
    """Enhanced search bar with advanced features."""
    
    def __init__(self, parent, 
                 on_search: Callable[[str], None],
                 on_suggestion_select: Callable[[Dict[str, str]], None],
                 weather_service=None, **kwargs):
        """Initialize enhanced search bar."""
        super().__init__(parent, **DataTerminalTheme.get_frame_style("main"), **kwargs)
        
        self.on_search = on_search
        self.on_suggestion_select = on_suggestion_select
        self.weather_service = weather_service
        
        # Managers
        self.favorites_manager = FavoritesManager()
        self.recent_manager = RecentSearchesManager()
        
        # Search state
        self.search_thread: Optional[threading.Thread] = None
        self.last_search_time = 0
        self.search_delay = 0.3  # Faster response for better UX
        
        # Configure grid
        self.grid_columnconfigure(0, weight=1)
        
        self._create_widgets()
        self._setup_layout()
        self._setup_bindings()
    
    def _create_widgets(self) -> None:
        """Create search widgets."""
        # Search container
        self.search_container = ctk.CTkFrame(
            self,
            **DataTerminalTheme.get_frame_style("main")
        )
        
        # Search entry with enhanced placeholder and improved styling
        entry_style = DataTerminalTheme.get_entry_style()
        # Remove font from theme to avoid conflicts
        if 'font' in entry_style:
            del entry_style['font']
        
        self.search_entry = ctk.CTkEntry(
            self.search_container,
            placeholder_text="🔍 Search cities, coordinates, or zip codes...",
            width=300,
            height=42,
            state="normal",  # Ensure entry is enabled
            font=("Segoe UI", 12),
            **entry_style
        )
        
        # Button container
        self.button_container = ctk.CTkFrame(
            self.search_container,
            **DataTerminalTheme.get_frame_style("main")
        )
        
        # Search button with improved styling
        primary_style = DataTerminalTheme.get_button_style("primary")
        if 'font' in primary_style:
            del primary_style['font']
        
        self.search_button = ctk.CTkButton(
            self.button_container,
            text="SEARCH",
            width=85,
            height=42,
            font=("Segoe UI", 12, "bold"),
            command=self._on_search_click,
            **primary_style
        )
        
        # Favorites toggle button with improved styling
        secondary_style = DataTerminalTheme.get_button_style("secondary")
        if 'font' in secondary_style:
            del secondary_style['font']
        
        self.favorites_button = ctk.CTkButton(
            self.button_container,
            text="⭐",
            width=42,
            height=42,
            font=("Segoe UI", 14),
            command=self._toggle_favorites,
            **secondary_style
        )
        
        # GPS location button with improved styling
        secondary_style2 = DataTerminalTheme.get_button_style("secondary")
        if 'font' in secondary_style2:
            del secondary_style2['font']
        
        self.gps_button = ctk.CTkButton(
            self.button_container,
            text="📍",
            width=42,
            height=42,
            font=("Segoe UI", 14),
            command=self._get_current_location,
            **secondary_style2
        )
        
        # Current city display with favorite toggle
        self.current_city_container = ctk.CTkFrame(
            self.search_container,
            **DataTerminalTheme.get_frame_style("main")
        )
        
        self.current_city_label = ctk.CTkLabel(
            self.current_city_container,
            text="",
            **DataTerminalTheme.get_label_style("caption")
        )
        
        self.favorite_toggle_button = ctk.CTkButton(
            self.current_city_container,
            text="☆",
            width=30,
            height=25,
            command=self._toggle_current_favorite,
            **DataTerminalTheme.get_button_style("secondary")
        )
        
        # Enhanced suggestion dropdown
        self.suggestion_frame = SearchSuggestionDropdown(
            self,
            on_select=self._on_suggestion_select,
            favorites_manager=self.favorites_manager,
            recent_manager=self.recent_manager
        )
    
    def _setup_layout(self) -> None:
        """Arrange widgets with enhanced spacing and alignment."""
        # Main search container with refined padding
        self.search_container.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        self.search_container.grid_columnconfigure(0, weight=1)
        
        # Search entry and buttons with optimized spacing
        self.search_entry.grid(row=0, column=0, sticky="ew", padx=(0, 10))
        self.button_container.grid(row=0, column=1, sticky="e")
        
        # Button container with tighter, more professional spacing
        self.search_button.grid(row=0, column=0, padx=(0, 4))
        self.favorites_button.grid(row=0, column=1, padx=(0, 4))
        self.gps_button.grid(row=0, column=2)
        
        # Current city container with refined layout
        self.current_city_container.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(6, 0))
        self.current_city_container.grid_columnconfigure(0, weight=1)
        
        self.current_city_label.grid(row=0, column=0, sticky="w", padx=(3, 0))
        self.favorite_toggle_button.grid(row=0, column=1, sticky="e", padx=(0, 3))
        
        # Suggestion dropdown with precise positioning
        self.suggestion_frame.grid(row=1, column=0, sticky="ew", padx=5, pady=(0, 5))
    
    def _setup_bindings(self) -> None:
        """Setup event bindings."""
        # Entry events
        self.search_entry.bind("<Return>", self._on_enter_key)
        self.search_entry.bind("<KeyRelease>", self._on_key_release)
        self.search_entry.bind("<FocusIn>", self._on_focus_in)
        self.search_entry.bind("<FocusOut>", self._on_focus_out)
        self.search_entry.bind("<Button-1>", self._on_entry_click)
        
        # Click outside to hide suggestions
        self.bind("<Button-1>", self._on_click_outside)
        
        # Set initial focus to search entry with longer delay
        self.after(500, self._set_initial_focus)  # Increased from 100ms
    
    def _on_search_click(self) -> None:
        """Handle search button click."""
        query = self.search_entry.get().strip()
        if query:
            self.suggestion_frame.clear_suggestions()
            self.on_search(query)
    
    def _on_enter_key(self, event) -> None:
        """Handle Enter key press."""
        self._on_search_click()
    
    def _on_focus_in(self, event) -> None:
        """Handle focus in event - show recent searches if empty."""
        query = self.search_entry.get().strip()
        if not query:
            self.suggestion_frame.show_suggestions(
                [], show_favorites=True, show_recent=True
            )
    
    def _on_key_release(self, event) -> None:
        """Handle key release for autocomplete."""
        # Ignore special keys
        if event.keysym in ['Up', 'Down', 'Left', 'Right', 'Tab', 'Return', 'Escape']:
            return
        
        query = self.search_entry.get().strip()
        
        if len(query) < 2:
            if len(query) == 0:
                # Show favorites and recent when empty
                self.suggestion_frame.show_suggestions(
                    [], show_favorites=True, show_recent=True
                )
            else:
                self.suggestion_frame.clear_suggestions()
            return
        
        # Debounce search requests
        self.last_search_time = time.time()
        
        if self.search_thread and self.search_thread.is_alive():
            return  # Previous search still running
        
        self.search_thread = threading.Thread(
            target=self._delayed_search,
            args=(query, self.last_search_time),
            daemon=True
        )
        self.search_thread.start()
    
    def _delayed_search(self, query: str, search_time: float) -> None:
        """Perform delayed search for autocomplete."""
        time.sleep(self.search_delay)
        
        # Check if this search is still relevant
        if search_time != self.last_search_time:
            return
        
        # Get city suggestions
        suggestions = self._get_city_suggestions(query)
        
        # Update UI on main thread
        self.after(0, self._show_suggestions, suggestions)
    
    def _get_city_suggestions(self, query: str) -> List[Dict[str, str]]:
        """Get city suggestions for autocomplete."""
        if self.weather_service and hasattr(self.weather_service, 'search_cities'):
            try:
                return self.weather_service.search_cities(query, limit=5)
            except (ValueError, KeyError, TypeError):
                pass
        
        # Fallback to sample cities
        sample_cities = [
            {'name': 'New York', 'country': 'US', 'display': 'New York, US'},
            {'name': 'London', 'country': 'GB', 'display': 'London, GB'},
            {'name': 'Paris', 'country': 'FR', 'display': 'Paris, FR'},
            {'name': 'Tokyo', 'country': 'JP', 'display': 'Tokyo, JP'},
            {'name': 'Sydney', 'country': 'AU', 'display': 'Sydney, AU'},
            {'name': 'Berlin', 'country': 'DE', 'display': 'Berlin, DE'},
            {'name': 'Moscow', 'country': 'RU', 'display': 'Moscow, RU'},
            {'name': 'Toronto', 'country': 'CA', 'display': 'Toronto, CA'},
            {'name': 'Mumbai', 'country': 'IN', 'display': 'Mumbai, IN'},
            {'name': 'Beijing', 'country': 'CN', 'display': 'Beijing, CN'},
        ]
        
        query_lower = query.lower()
        matching_cities = [
            city for city in sample_cities
            if query_lower in city['name'].lower()
        ]
        
        return matching_cities[:5]
    
    def _show_suggestions(self, suggestions: List[Dict[str, str]]) -> None:
        """Show autocomplete suggestions."""
        self.suggestion_frame.show_suggestions(suggestions)
    
    def _on_suggestion_select(self, suggestion: Dict[str, str]) -> None:
        """Handle suggestion selection."""
        # Update search entry
        self.search_entry.delete(0, tk.END)
        self.search_entry.insert(0, suggestion.get('name', ''))
        
        # Add to recent searches
        self.recent_manager.add_search(suggestion)
        
        # Clear suggestions
        self.suggestion_frame.clear_suggestions()
        
        # Trigger search
        self.on_suggestion_select(suggestion)
    
    def _toggle_favorites(self) -> None:
        """Toggle favorites dropdown."""
        self.suggestion_frame.show_suggestions(
            [], show_favorites=True, show_recent=False
        )
    
    def _get_current_location(self) -> None:
        """Get current location using GPS/IP geolocation."""
        # Placeholder for geolocation functionality
        # In a real implementation, this would use browser geolocation API
        # or IP-based location services
        self.search_entry.delete(0, tk.END)
        self.search_entry.insert(0, "Current Location")
        self._on_search_click()
    
    def _toggle_current_favorite(self) -> None:
        """Toggle current city as favorite."""
        current_text = self.current_city_label.cget("text")
        if current_text and "Current:" in current_text:
            city_name = current_text.replace("Current: ", "")
            
            if self.favorites_manager.is_favorite(city_name):
                self.favorites_manager.remove_favorite(city_name)
                self.favorite_toggle_button.configure(text="☆")
            else:
                location = {'name': city_name, 'display': city_name}
                self.favorites_manager.add_favorite(location)
                self.favorite_toggle_button.configure(text="⭐")
    
    def _on_focus_out(self, event) -> None:
        """Handle focus out event."""
        # Delay hiding suggestions to allow clicking on them
        self.after(200, self._check_and_hide_suggestions)
    
    def _on_entry_click(self, event) -> None:
        """Handle entry click event."""
        self.search_entry.focus_set()
        return "break"
    
    def _set_initial_focus(self) -> None:
        """Set initial focus to search entry."""
        try:
            self.search_entry.focus_set()
        except (AttributeError, RuntimeError):
            pass  # Ignore focus errors during initialization
    
    def _on_click_outside(self, event) -> None:
        """Handle click outside search area."""
        widget = event.widget
        if not self._is_child_of(widget, self.suggestion_frame):
            self.suggestion_frame.clear_suggestions()
    
    def _check_and_hide_suggestions(self) -> None:
        """Check if suggestions should be hidden."""
        if self.focus_get() != self.search_entry:
            self.suggestion_frame.clear_suggestions()
    
    def _is_child_of(self, widget, parent) -> bool:
        """Check if widget is a child of parent."""
        while widget:
            if widget == parent:
                return True
            widget = widget.master
        return False
    
    def set_current_city(self, city: str) -> None:
        """Set the current city display."""
        self.current_city_label.configure(text=f"Current: {city}")
        
        # Update favorite button state
        if self.favorites_manager.is_favorite(city):
            self.favorite_toggle_button.configure(text="⭐")
        else:
            self.favorite_toggle_button.configure(text="☆")
    
    def clear_current_city(self) -> None:
        """Clear the current city display."""
        self.current_city_label.configure(text="")
        self.favorite_toggle_button.configure(text="☆")
    
    def get_search_text(self) -> str:
        """Get current search text."""
        return self.search_entry.get().strip()
    
    def set_search_text(self, text: str) -> None:
        """Set search text."""
        self.search_entry.delete(0, tk.END)
        self.search_entry.insert(0, text)
    
    def clear_search(self) -> None:
        """Clear search entry and suggestions."""
        self.search_entry.delete(0, tk.END)
        self.suggestion_frame.clear_suggestions()