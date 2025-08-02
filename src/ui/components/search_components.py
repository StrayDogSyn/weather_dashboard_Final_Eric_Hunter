"""Enhanced Search Components with Autocomplete and Geolocation

Provides advanced search functionality including:
- Real-time autocomplete
- Geolocation detection
- Zip code support
- Search history persistence
"""

import json
import os
import threading
import tkinter as tk
from datetime import datetime
from typing import Callable, Dict, List, Optional

import customtkinter as ctk

from ...models.weather_models import LocationResult
from ...services.geocoding_service import GeocodingService


class EnhancedSearchBar(ctk.CTkFrame):
    """Enhanced search bar with autocomplete, geolocation, and search history."""

    def __init__(
        self, parent, weather_service, on_location_selected: Optional[Callable] = None, **kwargs
    ):
        """Initialize enhanced search bar."""
        super().__init__(parent, **kwargs)

        self.weather_service = weather_service
        self.geocoding_service = GeocodingService()
        self.on_location_selected = on_location_selected

        # Search state
        self.is_searching = False
        self.search_delay_id = None
        self.autocomplete_results: List[LocationResult] = []
        self.selected_index = -1
        self.dropdown_visible = False
        self.loading_spinner_active = False
        self.search_timer = None

        # Load search history
        self.search_history = self.load_search_history()

        # Initialize UI components
        self.setup_ui()
        self.bind_events()

    def setup_ui(self):
        """Setup the search bar UI components."""
        self.configure(fg_color="transparent")

        # Main search container
        self.search_container = ctk.CTkFrame(self, fg_color="transparent")
        self.search_container.pack(fill="x", padx=10, pady=5)

        # Search frame with icon and entry
        self.search_frame = ctk.CTkFrame(
            self.search_container,
            height=40,
            corner_radius=20,
            border_width=2,
            border_color="#00FFAB",
        )
        self.search_frame.pack(side="left", fill="x", expand=True, padx=(0, 5))
        self.search_frame.pack_propagate(False)

        # Search icon
        self.search_icon = ctk.CTkLabel(self.search_frame, text="🔍", font=("Arial", 16), width=30)
        self.search_icon.pack(side="left", padx=(10, 5))

        # Search entry
        self.search_entry = ctk.CTkEntry(
            self.search_frame,
            placeholder_text="City, zip code, or coordinates...",
            font=("Arial", 12),
            border_width=0,
            fg_color="transparent",
        )
        self.search_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))

        # Loading spinner (initially hidden)
        self.loading_label = ctk.CTkLabel(
            self.search_frame, text="⏳", font=("Arial", 14), width=20
        )

        # Geolocation button
        self.geo_button = ctk.CTkButton(
            self.search_container,
            text="📍",
            width=40,
            height=40,
            corner_radius=20,
            font=("Arial", 16),
            command=self.use_current_location,
            hover_color="#00CC88",
        )
        self.geo_button.pack(side="right")

        # Autocomplete dropdown (initially hidden)
        self.autocomplete_frame = ctk.CTkFrame(
            self, fg_color="#1E1E1E", border_color="#00FFAB", border_width=1, corner_radius=10
        )

        # Scrollable frame for autocomplete items
        self.autocomplete_scroll = ctk.CTkScrollableFrame(
            self.autocomplete_frame, height=200, fg_color="transparent"
        )
        self.autocomplete_scroll.pack(fill="both", expand=True, padx=5, pady=5)

    def bind_events(self):
        """Bind keyboard and mouse events."""
        self.search_entry.bind("<KeyRelease>", self.on_key_release)
        self.search_entry.bind("<KeyPress>", self.on_key_press)
        self.search_entry.bind("<FocusIn>", self.on_focus_in)
        self.search_entry.bind("<Button-1>", self.on_click)
        self.search_entry.bind("<FocusOut>", self.on_focus_out)

    def on_key_release(self, event):
        """Handle key release events for search input."""
        if event.keysym in ["Up", "Down", "Return", "Escape"]:
            return

        query = self.search_entry.get().strip()

        # Cancel previous search timer
        if self.search_timer:
            self.search_timer.cancel()

        if len(query) >= 3:
            # Debounce search with 300ms delay
            self.search_timer = threading.Timer(0.3, self.perform_search, [query])
            self.search_timer.start()
        else:
            self.hide_dropdown()

    def on_key_press(self, event):
        """Handle key press events for navigation."""
        if not self.dropdown_visible:
            return

        if event.keysym == "Down":
            self.navigate_dropdown(1)
            return "break"
        elif event.keysym == "Up":
            self.navigate_dropdown(-1)
            return "break"
        elif event.keysym == "Return":
            self.select_current_item()
            return "break"
        elif event.keysym == "Escape":
            self.hide_dropdown()
            return "break"

    def on_focus_in(self, event):
        """Handle focus in event - show recent searches if empty."""
        query = self.search_entry.get().strip()
        if not query and self.search_history["recent_searches"]:
            self.show_recent_searches()

    def on_click(self, event):
        """Handle click on search entry."""
        self.on_focus_in(event)

    def on_click_outside(self, event):
        """Handle click outside to close dropdown."""
        widget = event.widget
        if not self.is_child_of_dropdown(widget):
            self.hide_dropdown()

    def on_focus_out(self, event):
        """Handle focus out to close dropdown."""
        # Use after_idle to allow click events to process first
        self.after_idle(self.hide_dropdown)

    def is_child_of_dropdown(self, widget) -> bool:
        """Check if widget is part of the dropdown."""
        parent = widget
        while parent:
            if parent == self.autocomplete_frame or parent == self.search_entry:
                return True
            parent = parent.master
        return False

    def perform_search(self, query: str):
        """Perform autocomplete search with enhanced error handling."""
        if self.is_searching:
            return

        self.is_searching = True
        self.show_loading()

        def search_task():
            try:
                # Import custom exceptions for proper error handling
                from src.services.enhanced_weather_service import (
                    WeatherServiceError, RateLimitError, APIKeyError, 
                    NetworkError, ServiceUnavailableError
                )
                
                results = self.weather_service.search_locations_advanced(query)
                self.after(0, self.handle_search_results, results)
                
            except RateLimitError as e:
                print(f"Rate limit exceeded: {e}")
                self.after(0, self.handle_search_error, "Search rate limit exceeded. Please wait a moment.")
            except APIKeyError as e:
                print(f"API key error: {e}")
                self.after(0, self.handle_search_error, "API configuration error. Please check settings.")
            except NetworkError as e:
                print(f"Network error: {e}")
                self.after(0, self.handle_search_error, "Network connection error. Please check your internet.")
            except ServiceUnavailableError as e:
                print(f"Service unavailable: {e}")
                self.after(0, self.handle_search_error, "Search service temporarily unavailable.")
            except WeatherServiceError as e:
                print(f"Weather service error: {e}")
                self.after(0, self.handle_search_error, "Search service error. Please try again.")
            except Exception as e:
                print(f"Unexpected search error: {e}")
                self.after(0, self.handle_search_error, "An unexpected error occurred during search.")
            finally:
                self.is_searching = False
                self.after(0, self.hide_loading)

        threading.Thread(target=search_task, daemon=True).start()

    def update_autocomplete_results(self, results: List[LocationResult]):
        """Update autocomplete dropdown with results."""
        self.autocomplete_results = results[:8]  # Limit to 8 results
        self.selected_index = -1

        # Clear previous results
        for widget in self.autocomplete_scroll.winfo_children():
            widget.destroy()

        if not results:
            self.show_no_results()
            return

        # Add result items
        for i, result in enumerate(self.autocomplete_results):
            self.create_result_item(result, i)

        self.show_dropdown()

    def create_result_item(self, result: LocationResult, index: int):
        """Create a single autocomplete result item."""
        item_frame = ctk.CTkFrame(self.autocomplete_scroll, fg_color="transparent", height=40)
        item_frame.pack(fill="x", pady=1)
        item_frame.pack_propagate(False)

        # Country flag and location text
        flag = self.get_country_flag(result.country_code)
        location_text = f"{flag} {result.display_name}"

        item_label = ctk.CTkLabel(item_frame, text=location_text, font=("Arial", 11), anchor="w")
        item_label.pack(side="left", fill="x", expand=True, padx=10, pady=5)

        # Bind click event
        item_frame.bind("<Button-1>", lambda e, idx=index: self.select_item(idx))
        item_label.bind("<Button-1>", lambda e, idx=index: self.select_item(idx))

        # Store reference for highlighting
        item_frame.result_index = index

    def show_recent_searches(self):
        """Show recent searches in dropdown."""
        # Clear previous results
        for widget in self.autocomplete_scroll.winfo_children():
            widget.destroy()

        recent = self.search_history["recent_searches"][:8]
        if not recent:
            return

        # Add header
        header = ctk.CTkLabel(
            self.autocomplete_scroll,
            text="Recent Searches",
            font=("Arial", 10, "bold"),
            text_color="#888888",
        )
        header.pack(anchor="w", padx=10, pady=(5, 2))

        # Add recent search items
        for search in recent:
            self.create_recent_search_item(search["query"])

        self.show_dropdown()

    def create_recent_search_item(self, query: str):
        """Create a recent search item."""
        item_frame = ctk.CTkFrame(self.autocomplete_scroll, fg_color="transparent", height=35)
        item_frame.pack(fill="x", pady=1)
        item_frame.pack_propagate(False)

        item_label = ctk.CTkLabel(
            item_frame, text=f"🕒 {query}", font=("Arial", 10), anchor="w", text_color="#CCCCCC"
        )
        item_label.pack(side="left", fill="x", expand=True, padx=10, pady=5)

        # Bind click event
        item_frame.bind("<Button-1>", lambda e: self.select_recent_search(query))
        item_label.bind("<Button-1>", lambda e: self.select_recent_search(query))

    def select_recent_search(self, query: str):
        """Select a recent search."""
        self.search_entry.delete(0, tk.END)
        self.search_entry.insert(0, query)
        self.hide_dropdown()
        self.perform_search(query)

    def show_no_results(self, message: str = "No results found"):
        """Show no results message with optional custom message."""
        # Clear previous results
        for widget in self.autocomplete_scroll.winfo_children():
            widget.destroy()

        no_results = ctk.CTkLabel(
            self.autocomplete_scroll,
            text=message,
            font=("Arial", 11),
            text_color="#888888",
        )
        no_results.pack(pady=20)

        self.show_dropdown()

    def handle_search_error(self, error_message: str = "Search failed"):
        """Handle search errors with user-friendly messages."""
        self.hide_loading()
        self.show_no_results(error_message)
        print(f"Search error: {error_message}")

    def handle_search_results(self, results):
        """Handle successful search results."""
        self.hide_loading()
        self.update_autocomplete_results(results)

    def navigate_dropdown(self, direction: int):
        """Navigate dropdown with arrow keys."""
        if not self.autocomplete_results:
            return

        # Update selected index
        self.selected_index += direction
        self.selected_index = max(-1, min(len(self.autocomplete_results) - 1, self.selected_index))

        # Update highlighting
        self.update_selection_highlight()

    def update_selection_highlight(self):
        """Update visual highlighting of selected item."""
        for i, widget in enumerate(self.autocomplete_scroll.winfo_children()):
            if hasattr(widget, "result_index"):
                if widget.result_index == self.selected_index:
                    widget.configure(fg_color="#00FFAB", text_color="#000000")
                else:
                    widget.configure(fg_color="transparent", text_color="#FFFFFF")

    def select_current_item(self):
        """Select the currently highlighted item."""
        if 0 <= self.selected_index < len(self.autocomplete_results):
            self.select_item(self.selected_index)

    def select_item(self, index: int):
        """Select an autocomplete item."""
        if 0 <= index < len(self.autocomplete_results):
            result = self.autocomplete_results[index]
            self.search_entry.delete(0, tk.END)
            self.search_entry.insert(0, result.display_name)

            # Add to search history
            self.add_to_search_history(result.display_name)

            # Notify parent
            if self.on_location_selected:
                self.on_location_selected(result)

            self.hide_dropdown()

    def show_dropdown(self):
        """Show the autocomplete dropdown with animation."""
        if self.dropdown_visible:
            return

        self.dropdown_visible = True

        # Position dropdown below search bar
        self.autocomplete_frame.place(in_=self.search_container, x=0, y=45, relwidth=1.0)

        # Animate dropdown appearance
        self.animate_dropdown_show()

    def hide_dropdown(self):
        """Hide the autocomplete dropdown."""
        if not self.dropdown_visible:
            return

        self.dropdown_visible = False
        self.autocomplete_frame.place_forget()

    def animate_dropdown_show(self):
        """Animate dropdown slide-down effect."""
        # Simple fade-in effect
        self.autocomplete_frame.configure(fg_color="#1E1E1E")

    def show_loading(self):
        """Show loading spinner."""
        if not self.loading_spinner_active:
            self.loading_spinner_active = True
            self.loading_label.pack(side="right", padx=(0, 10))
            self.animate_loading()

    def hide_loading(self):
        """Hide loading spinner."""
        self.loading_spinner_active = False
        self.loading_label.pack_forget()

    def animate_loading(self):
        """Animate loading spinner."""
        if self.loading_spinner_active:
            current_text = self.loading_label.cget("text")
            spinners = ["⏳", "⌛"]
            next_spinner = spinners[(spinners.index(current_text) + 1) % len(spinners)]
            self.loading_label.configure(text=next_spinner)
            self.after(500, self.animate_loading)

    def use_current_location(self):
        """Use geolocation to get current location with enhanced error handling."""
        self.geo_button.configure(text="⏳")

        def get_location():
            try:
                # Import custom exceptions for proper error handling
                from src.services.enhanced_weather_service import (
                    WeatherServiceError, RateLimitError, APIKeyError, 
                    NetworkError, ServiceUnavailableError
                )
                
                location = self.geocoding_service.get_current_location()
                if location:
                    # Convert to LocationResult format if needed
                    if hasattr(location, "display_name"):
                        self.after(0, self.handle_geolocation_result, location)
                    else:
                        # Create LocationResult from geocoding result
                        location_result = LocationResult(
                            name=location.name,
                            display_name=location.display_name,
                            latitude=location.latitude,
                            longitude=location.longitude,
                            country=location.country,
                            country_code=location.country_code,
                            state=location.state,
                            raw_address=location.raw_address,
                        )
                        self.after(0, self.handle_geolocation_result, location_result)
                else:
                    self.after(0, self.handle_geolocation_error, "Location not found")
                    
            except RateLimitError as e:
                print(f"Geolocation rate limit: {e}")
                self.after(0, self.handle_geolocation_error, "Rate limit exceeded")
            except APIKeyError as e:
                print(f"Geolocation API key error: {e}")
                self.after(0, self.handle_geolocation_error, "API configuration error")
            except NetworkError as e:
                print(f"Geolocation network error: {e}")
                self.after(0, self.handle_geolocation_error, "Network connection error")
            except ServiceUnavailableError as e:
                print(f"Geolocation service unavailable: {e}")
                self.after(0, self.handle_geolocation_error, "Service temporarily unavailable")
            except Exception as e:
                print(f"Unexpected geolocation error: {e}")
                self.after(0, self.handle_geolocation_error, "Geolocation failed")

        threading.Thread(target=get_location, daemon=True).start()

    def handle_geolocation_result(self, location: LocationResult):
        """Handle successful geolocation."""
        self.geo_button.configure(text="📍")
        self.search_entry.delete(0, tk.END)
        self.search_entry.insert(0, location.display_name)

        # Add to search history
        self.add_to_search_history(location.display_name)

        # Notify parent
        if self.on_location_selected:
            self.on_location_selected(location)

    def handle_geolocation_error(self, error_message: str = "Location error"):
        """Handle geolocation error with user feedback."""
        self.geo_button.configure(text="❌")
        
        # Show error tooltip or status
        print(f"Geolocation error: {error_message}")
        
        # Reset button after 3 seconds
        self.after(3000, lambda: self.geo_button.configure(text="📍"))

    def get_country_flag(self, country_code: str) -> str:
        """Get country flag emoji from country code."""
        flag_map = {
            "US": "🇺🇸",
            "GB": "🇬🇧",
            "CA": "🇨🇦",
            "AU": "🇦🇺",
            "DE": "🇩🇪",
            "FR": "🇫🇷",
            "IT": "🇮🇹",
            "ES": "🇪🇸",
            "JP": "🇯🇵",
            "CN": "🇨🇳",
            "IN": "🇮🇳",
            "BR": "🇧🇷",
            "RU": "🇷🇺",
            "MX": "🇲🇽",
            "NL": "🇳🇱",
        }
        return flag_map.get(country_code.upper(), "🌍")

    def load_search_history(self) -> Dict:
        """Load search history from file."""
        history_file = os.path.join("data", "search_history.json")

        default_history = {"recent_searches": [], "favorites": []}

        try:
            if os.path.exists(history_file):
                with open(history_file, "r", encoding="utf-8") as f:
                    return json.load(f)
        except Exception as e:
            print(f"Error loading search history: {e}")

        return default_history

    def save_search_history(self):
        """Save search history to file."""
        history_file = os.path.join("data", "search_history.json")

        try:
            os.makedirs("data", exist_ok=True)
            with open(history_file, "w", encoding="utf-8") as f:
                json.dump(self.search_history, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving search history: {e}")

    def add_to_search_history(self, query: str):
        """Add search query to history."""
        # Remove if already exists
        self.search_history["recent_searches"] = [
            item for item in self.search_history["recent_searches"] if item["query"] != query
        ]

        # Add to beginning
        self.search_history["recent_searches"].insert(
            0, {"query": query, "timestamp": datetime.now().isoformat()}
        )

        # Keep only last 10
        self.search_history["recent_searches"] = self.search_history["recent_searches"][:10]

        # Save to file
        self.save_search_history()

    def clear_search_history(self):
        """Clear all search history."""
        self.search_history = {"recent_searches": [], "favorites": []}
        self.save_search_history()
