"""Enhanced Search Component

Advanced search interface with autocomplete, favorites, and recent searches.
"""

import json
import threading
import tkinter as tk
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List

import customtkinter as ctk

from ..theme import DataTerminalTheme


class EnhancedSearchComponent(ctk.CTkFrame):
    """Enhanced search component with autocomplete and favorites."""

    def __init__(
        self, parent, weather_service, on_location_selected: Callable[[Dict[str, Any]], None]
    ):
        super().__init__(parent, fg_color=DataTerminalTheme.CARD_BG, corner_radius=8)

        self.weather_service = weather_service
        self.on_location_selected = on_location_selected

        # Search data
        self.search_suggestions: List[Dict[str, Any]] = []
        self.recent_searches: List[Dict[str, Any]] = []
        self.favorite_locations: List[Dict[str, Any]] = []

        # UI state with enhanced navigation
        self.suggestions_visible = False
        self.current_search_thread = None
        self.selected_suggestion_index = -1
        self.suggestion_buttons = []

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
            self, text="🔍", font=ctk.CTkFont(size=16), text_color=DataTerminalTheme.PRIMARY
        )
        search_icon.grid(row=0, column=0, padx=(10, 5), pady=10, sticky="w")

        # Search entry with enhanced styling and loading indicator
        self.search_container = ctk.CTkFrame(self, fg_color="transparent")
        self.search_container.grid(row=0, column=1, padx=5, pady=10, sticky="ew")
        self.search_container.grid_columnconfigure(0, weight=1)

        self.search_entry = ctk.CTkEntry(
            self.search_container,
            placeholder_text="🌍 Search cities, coordinates, or airport codes...",
            font=ctk.CTkFont(size=14),
            fg_color=DataTerminalTheme.BACKGROUND,
            border_color=DataTerminalTheme.PRIMARY,
            text_color=DataTerminalTheme.TEXT,
            placeholder_text_color=DataTerminalTheme.TEXT_SECONDARY,
            height=40,
            corner_radius=6,
        )
        self.search_entry.grid(row=0, column=0, sticky="ew")

        # Loading indicator
        self.loading_indicator = ctk.CTkLabel(
            self.search_container,
            text="⟳",
            font=ctk.CTkFont(size=16),
            text_color=DataTerminalTheme.PRIMARY,
        )
        # Initially hidden
        self.is_loading = False

        # Bind events with enhanced keyboard navigation
        self.search_entry.bind("<KeyRelease>", self._on_search_input)
        self.search_entry.bind("<Return>", self._on_search_submit)
        self.search_entry.bind("<FocusIn>", self._on_search_focus)
        self.search_entry.bind("<FocusOut>", self._on_search_blur)
        self.search_entry.bind("<Up>", self._on_arrow_up)
        self.search_entry.bind("<Down>", self._on_arrow_down)
        self.search_entry.bind("<Escape>", self._on_escape)
        self.search_entry.bind("<Tab>", self._on_tab)

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
            command=self._detect_location,
        )
        self.gps_button.grid(row=0, column=2, padx=(5, 10), pady=10)

        # Suggestions dropdown (initially hidden)
        self.suggestions_frame = ctk.CTkScrollableFrame(
            self,
            fg_color=DataTerminalTheme.BACKGROUND,
            border_color=DataTerminalTheme.PRIMARY,
            border_width=1,
            corner_radius=6,
            height=200,
        )

        # Quick access buttons frame
        self.quick_access_frame = ctk.CTkFrame(self, fg_color="transparent", height=40)
        self.quick_access_frame.grid(
            row=2, column=0, columnspan=3, padx=10, pady=(0, 10), sticky="ew"
        )
        self.quick_access_frame.grid_columnconfigure((0, 1, 2, 3), weight=1)

        # Recent searches button
        self.recent_button = ctk.CTkButton(
            self.quick_access_frame,
            text="🕒 Recent",
            height=30,
            font=ctk.CTkFont(size=12),
            fg_color="transparent",
            text_color=DataTerminalTheme.TEXT_SECONDARY,
            hover_color=DataTerminalTheme.CARD_BG,
            command=self._show_recent_searches,
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
            command=self._show_favorites,
        )
        self.favorites_button.grid(row=0, column=1, padx=2, sticky="ew")

        # Random city button
        self.random_button = ctk.CTkButton(
            self.quick_access_frame,
            text="🎲 Random",
            height=30,
            font=ctk.CTkFont(size=12),
            fg_color="transparent",
            text_color=DataTerminalTheme.TEXT_SECONDARY,
            hover_color=DataTerminalTheme.CARD_BG,
            command=self._select_random_city,
        )
        self.random_button.grid(row=0, column=2, padx=2, sticky="ew")

        # Clear button
        self.clear_button = ctk.CTkButton(
            self.quick_access_frame,
            text="🗑️ Clear",
            height=30,
            font=ctk.CTkFont(size=12),
            fg_color="transparent",
            text_color=DataTerminalTheme.TEXT_SECONDARY,
            hover_color=DataTerminalTheme.CARD_BG,
            command=self._clear_search,
        )
        self.clear_button.grid(row=0, column=3, padx=2, sticky="ew")

    def _on_search_input(self, event):
        """Handle search input with autocomplete and loading indicator."""
        query = self.search_entry.get().strip()

        if len(query) >= 2:  # Start searching after 2 characters
            # Cancel previous search thread
            if self.current_search_thread and self.current_search_thread.is_alive():
                return  # Let the current search complete

            # Show loading indicator
            self._show_loading()

            # Start new search thread
            self.current_search_thread = threading.Thread(
                target=self._search_suggestions, args=(query,), daemon=True
            )
            self.current_search_thread.start()
        else:
            self._hide_suggestions()
            self._hide_loading()

    def _search_suggestions(self, query: str):
        """Search for location suggestions in background thread."""
        try:
            # Get suggestions from weather service
            suggestions = self.weather_service.search_locations(query, limit=8)

            # Convert LocationSearchResult objects to dictionaries
            suggestion_dicts = []
            for suggestion in suggestions:
                if hasattr(suggestion, "to_dict"):
                    suggestion_dicts.append(suggestion.to_dict())
                elif isinstance(suggestion, dict):
                    suggestion_dicts.append(suggestion)
                else:
                    # Fallback for unexpected data types
                    suggestion_dicts.append({"name": str(suggestion), "display": str(suggestion)})

            # Update UI in main thread
            self.after(0, lambda: self._update_suggestions(suggestion_dicts))

        except Exception as e:
            print(f"Search error: {e}")
            self.after(0, self._hide_suggestions)
        finally:
            # Always hide loading indicator
            self.after(0, self._hide_loading)

    def _update_suggestions(self, suggestions: List[Dict[str, Any]]):
        """Update suggestions dropdown."""
        # Validate suggestions data
        validated_suggestions = []
        for suggestion in suggestions:
            if isinstance(suggestion, dict) and suggestion.get("name"):
                validated_suggestions.append(suggestion)

        self.search_suggestions = validated_suggestions

        if validated_suggestions:
            self._show_suggestions()
        else:
            self._hide_suggestions()

    def _show_suggestions(self):
        """Show suggestions dropdown with enhanced navigation support."""
        if self.suggestions_visible:
            # Clear existing suggestions
            for widget in self.suggestions_frame.winfo_children():
                widget.destroy()
        else:
            # Show suggestions frame
            self.suggestions_frame.grid(
                row=1, column=0, columnspan=3, padx=10, pady=(0, 5), sticky="ew"
            )
            self.suggestions_visible = True

        # Reset navigation state
        self.selected_suggestion_index = -1
        self.suggestion_buttons = []

        # Add suggestion items with enhanced styling
        for i, suggestion in enumerate(self.search_suggestions[:5]):  # Limit to 5 suggestions
            self._create_suggestion_item(suggestion, i)

        # Store current suggestions for keyboard navigation
        self.current_suggestions = self.search_suggestions[:5]

    def _create_suggestion_item(self, location: Dict[str, Any], index: int):
        """Create a suggestion item button with enhanced details."""
        # Enhanced display text with location details
        display_text = location.get("display", location.get("name", "Unknown Location"))
        if "country" in location and location["country"]:
            display_text += f" • {location['country']}"
        if "region" in location and location["region"]:
            display_text += f", {location['region']}"

        suggestion_btn = ctk.CTkButton(
            self.suggestions_frame,
            text=f"📍 {display_text}",
            command=lambda: self._select_suggestion_by_index(index),
            fg_color="transparent",
            hover_color=DataTerminalTheme.PRIMARY,
            text_color=DataTerminalTheme.TEXT,
            anchor="w",
            height=35,
            font=ctk.CTkFont(size=13),
        )
        suggestion_btn.grid(row=index, column=0, sticky="ew", padx=5, pady=2)
        self.suggestion_buttons.append(suggestion_btn)

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

    def _on_arrow_up(self, event=None):
        """Handle up arrow key navigation."""
        if self.suggestions_visible and self.suggestion_buttons:
            if self.selected_suggestion_index > 0:
                self.selected_suggestion_index -= 1
            else:
                self.selected_suggestion_index = len(self.suggestion_buttons) - 1
            self._update_suggestion_selection()
        return "break"

    def _on_arrow_down(self, event=None):
        """Handle down arrow key navigation."""
        if self.suggestions_visible and self.suggestion_buttons:
            if self.selected_suggestion_index < len(self.suggestion_buttons) - 1:
                self.selected_suggestion_index += 1
            else:
                self.selected_suggestion_index = 0
            self._update_suggestion_selection()
        return "break"

    def _on_escape(self, event=None):
        """Handle escape key to hide suggestions."""
        self._hide_suggestions()
        return "break"

    def _on_tab(self, event=None):
        """Handle tab key to accept current suggestion."""
        if self.suggestions_visible and self.selected_suggestion_index >= 0:
            self._select_suggestion(self.selected_suggestion_index)
            return "break"

    def _update_suggestion_selection(self):
        """Update visual selection of suggestions."""
        for i, button in enumerate(self.suggestion_buttons):
            if i == self.selected_suggestion_index:
                button.configure(fg_color=DataTerminalTheme.SELECTED)
            else:
                button.configure(fg_color="transparent")

    def _show_loading(self):
        """Show loading indicator."""
        if not self.is_loading:
            self.is_loading = True
            self.loading_indicator.grid(row=0, column=1, padx=(5, 0))
            self._animate_loading()

    def _hide_loading(self):
        """Hide loading indicator."""
        self.is_loading = False
        self.loading_indicator.grid_remove()

    def _animate_loading(self):
        """Animate the loading indicator."""
        if self.is_loading:
            current_text = self.loading_indicator.cget("text")
            if current_text == "⟳":
                self.loading_indicator.configure(text="⟲")
            else:
                self.loading_indicator.configure(text="⟳")
            self.after(500, self._animate_loading)

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
            # Validate and clean the query
            query = query.strip()
            if len(query) < 2:
                self._show_error("Please enter at least 2 characters")
                return

            results = self.weather_service.search_locations(query, limit=1)
            if results:
                # Convert LocationSearchResult to dictionary format
                location_data = (
                    results[0].to_dict() if hasattr(results[0], "to_dict") else results[0]
                )
                self._select_location(location_data)
            else:
                self._show_error(f"No results found for '{query}'")
        except Exception as e:
            self._show_error(f"Search error: {str(e)}")

    def _select_suggestion_by_index(self, index: int):
        """Select suggestion by index for keyboard navigation."""
        if 0 <= index < len(self.current_suggestions):
            self._select_location(self.current_suggestions[index])

    def _select_location(self, location: Dict[str, Any]):
        """Select a location and update weather with enhanced feedback."""
        # Hide suggestions
        self._hide_suggestions()

        # Ensure location data is in proper dictionary format
        if hasattr(location, "to_dict"):
            location = location.to_dict()

        # Validate required fields
        if not location.get("name"):
            self._show_error("Invalid location data")
            return

        # Update search entry with proper display name
        display_name = location.get("display", location.get("name", ""))
        self.search_entry.delete(0, tk.END)
        self.search_entry.insert(0, display_name)

        # Brief visual confirmation
        original_color = self.search_entry.cget("border_color")
        self.search_entry.configure(border_color=DataTerminalTheme.SUCCESS)
        self.after(1000, lambda: self.search_entry.configure(border_color=original_color))

        # Update parent status if available
        if hasattr(self.parent, "update_status"):
            location_name = location.get("name", "Unknown location")
            self.parent.update_status(f"Selected location: {location_name}", "success")

        # Add to recent searches
        self._add_to_recent(location)

        # Notify parent with validated location data
        self.on_location_selected(location)

    def _detect_location(self):
        """Detect user's current location using IP geolocation."""
        self.gps_button.configure(text="⏳")

        def detect_thread():
            try:
                import requests

                # Try multiple IP geolocation services for better reliability
                services = [
                    ("http://ip-api.com/json/", self._parse_ip_api),
                    ("https://ipapi.co/json/", self._parse_ipapi_co),
                    ("https://ipinfo.io/json", self._parse_ipinfo),
                ]

                for service_url, parser in services:
                    try:
                        response = requests.get(service_url, timeout=5)
                        if response.status_code == 200:
                            location = parser(response.json())
                            if location:
                                # Update UI in main thread
                                self.after(0, lambda loc=location: self._select_location(loc))
                                return
                    except Exception as e:
                        print(f"Service {service_url} failed: {e}")
                        continue

                # If all services fail, use a default location
                default_location = {
                    "name": "New York",
                    "display": "New York, NY, USA (Default)",
                    "lat": 40.7128,
                    "lon": -74.0060,
                    "country": "US",
                    "region": "New York",
                }
                self.after(0, lambda: self._select_location(default_location))
                self.after(
                    0,
                    lambda: self._show_error(
                        "Using default location - location detection unavailable"
                    ),
                )

            except Exception:
                # Fallback to default location
                default_location = {
                    "name": "New York",
                    "display": "New York, NY, USA (Default)",
                    "lat": 40.7128,
                    "lon": -74.0060,
                    "country": "US",
                    "region": "New York",
                }
                self.after(0, lambda: self._select_location(default_location))
                self.after(
                    0,
                    lambda: self._show_error(f"Location detection failed, using default: {str(e)}"),
                )
            finally:
                self.after(0, lambda: self.gps_button.configure(text="📍"))

        threading.Thread(target=detect_thread, daemon=True).start()

    def _parse_ip_api(self, data):
        """Parse response from ip-api.com"""
        if data.get("status") == "success":
            return {
                "name": data.get("city", "Unknown"),
                "display": f"{data.get('city', 'Unknown')}, {data.get('regionName', '')}, {data.get('country', '')}",
                "lat": data.get("lat"),
                "lon": data.get("lon"),
                "country": data.get("country", ""),
                "region": data.get("regionName", ""),
            }
        return None

    def _parse_ipapi_co(self, data):
        """Parse response from ipapi.co"""
        if data.get("city") and data.get("latitude"):
            return {
                "name": data.get("city", "Unknown"),
                "display": f"{data.get('city', 'Unknown')}, {data.get('region', '')}, {data.get('country_name', '')}",
                "lat": data.get("latitude"),
                "lon": data.get("longitude"),
                "country": data.get("country_name", ""),
                "region": data.get("region", ""),
            }
        return None

    def _parse_ipinfo(self, data):
        """Parse response from ipinfo.io"""
        if data.get("city") and data.get("loc"):
            lat, lon = data.get("loc", "0,0").split(",")
            return {
                "name": data.get("city", "Unknown"),
                "display": f"{data.get('city', 'Unknown')}, {data.get('region', '')}, {data.get('country', '')}",
                "lat": float(lat),
                "lon": float(lon),
                "country": data.get("country", ""),
                "region": data.get("region", ""),
            }
        return None

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

    def _select_random_city(self):
        """Select a random city from popular destinations."""
        popular_cities = [
            {"name": "New York", "display": "New York, NY, USA", "lat": 40.7128, "lon": -74.0060},
            {"name": "London", "display": "London, England, UK", "lat": 51.5074, "lon": -0.1278},
            {"name": "Tokyo", "display": "Tokyo, Japan", "lat": 35.6762, "lon": 139.6503},
            {"name": "Paris", "display": "Paris, France", "lat": 48.8566, "lon": 2.3522},
            {
                "name": "Sydney",
                "display": "Sydney, NSW, Australia",
                "lat": -33.8688,
                "lon": 151.2093,
            },
            {"name": "Dubai", "display": "Dubai, UAE", "lat": 25.2048, "lon": 55.2708},
            {"name": "Singapore", "display": "Singapore", "lat": 1.3521, "lon": 103.8198},
            {
                "name": "Los Angeles",
                "display": "Los Angeles, CA, USA",
                "lat": 34.0522,
                "lon": -118.2437,
            },
            {"name": "Berlin", "display": "Berlin, Germany", "lat": 52.5200, "lon": 13.4050},
            {"name": "Mumbai", "display": "Mumbai, India", "lat": 19.0760, "lon": 72.8777},
            {"name": "São Paulo", "display": "São Paulo, Brazil", "lat": -23.5505, "lon": -46.6333},
            {"name": "Cairo", "display": "Cairo, Egypt", "lat": 30.0444, "lon": 31.2357},
            {"name": "Bangkok", "display": "Bangkok, Thailand", "lat": 13.7563, "lon": 100.5018},
            {"name": "Moscow", "display": "Moscow, Russia", "lat": 55.7558, "lon": 37.6176},
            {
                "name": "Cape Town",
                "display": "Cape Town, South Africa",
                "lat": -33.9249,
                "lon": 18.4241,
            },
        ]

        import random

        random_city = random.choice(popular_cities)

        # Update search entry
        self.search_entry.delete(0, tk.END)
        self.search_entry.insert(0, random_city["display"])

        # Select the location
        self._select_location(random_city)

    def _add_to_recent(self, location: Dict[str, Any]):
        """Add location to recent searches."""
        # Remove if already exists
        self.recent_searches = [
            loc for loc in self.recent_searches if loc.get("display") != location.get("display")
        ]

        # Add to beginning
        location["timestamp"] = datetime.now().isoformat()
        self.recent_searches.insert(0, location)

        # Keep only last 10
        self.recent_searches = self.recent_searches[:10]

        # Save to file
        self._save_search_data()

    def add_to_favorites(self, location: Dict[str, Any]):
        """Add location to favorites."""
        # Check if already in favorites
        if not any(
            fav.get("display") == location.get("display") for fav in self.favorite_locations
        ):
            self.favorite_locations.append(location)
            self._save_search_data()
            return True
        return False

    def remove_from_favorites(self, location: Dict[str, Any]):
        """Remove location from favorites."""
        self.favorite_locations = [
            fav for fav in self.favorite_locations if fav.get("display") != location.get("display")
        ]
        self._save_search_data()

    def is_favorite(self, location: Dict[str, Any]) -> bool:
        """Check if location is in favorites."""
        return any(fav.get("display") == location.get("display") for fav in self.favorite_locations)

    def _load_search_data(self):
        """Load search data from file."""
        try:
            data_file = Path.cwd() / "data" / "search_data.json"
            if data_file.exists():
                with open(data_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.recent_searches = data.get("recent", [])
                    self.favorite_locations = data.get("favorites", [])
        except Exception as e:
            print(f"Failed to load search data: {e}")

    def _save_search_data(self):
        """Save search data to file."""
        try:
            data_file = Path.cwd() / "data" / "search_data.json"
            data_file.parent.mkdir(exist_ok=True)

            data = {"recent": self.recent_searches, "favorites": self.favorite_locations}

            with open(data_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Failed to save search data: {e}")

    def _show_error(self, message: str):
        """Show error message."""
        # Create temporary error label
        error_label = ctk.CTkLabel(
            self, text=f"❌ {message}", font=ctk.CTkFont(size=12), text_color="#FF6B6B"
        )
        error_label.grid(row=3, column=0, columnspan=3, padx=10, pady=5)

        # Remove after 3 seconds
        self.after(3000, error_label.destroy)
