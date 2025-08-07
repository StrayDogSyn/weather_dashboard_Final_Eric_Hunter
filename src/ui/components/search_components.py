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
from datetime import datetime
from typing import Callable, Dict, List, Optional
import customtkinter as ctk


from src.services.weather import LocationResult

from ...services.weather.geocoding_service import GeocodingService


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
        self.last_search_query = ""
        self.validation_errors = []

        # Load search history and favorites
        self.search_history = self.load_search_history()
        self.favorites = self.load_favorites()

        # Geolocation state
        self.current_detected_location = None
        self.geolocation_permission_denied = False
        self.ip_location_fallback = None

        # Track scheduled calls for cleanup
        self.scheduled_calls = set()

        # Initialize UI components
        self.setup_ui()
        self.bind_events()

    def safe_after(self, delay_ms: int, callback, *args):
        """Safely schedule an after() call with error handling and tracking."""
        try:
            if not self.winfo_exists():
                return None
            
            if args:
                call_id = self.after(delay_ms, callback, *args)
            else:
                call_id = self.after(delay_ms, callback)
            self.scheduled_calls.add(call_id)
            return call_id
        except Exception as e:
            print(f"Error scheduling after() call: {e}")
            return None
            
    def safe_after_idle(self, callback, *args):
        """Safely schedule an after_idle() call with error handling and tracking."""
        try:
            if not self.winfo_exists():
                return None
            
            if args:
                call_id = self.after_idle(callback, *args)
            else:
                call_id = self.after_idle(callback)
            self.scheduled_calls.add(call_id)
            return call_id
        except Exception as e:
            print(f"Error scheduling after_idle() call: {e}")
            return None

    def _cleanup_scheduled_calls(self):
        """Cancel all scheduled calls to prevent TclError."""
        for call_id in self.scheduled_calls.copy():
            try:
                self.after_cancel(call_id)
            except Exception:
                pass
        self.scheduled_calls.clear()

    def destroy(self):
        """Override destroy to cleanup scheduled calls."""
        self._cleanup_scheduled_calls()
        super().destroy()

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
            placeholder_text="City, airport code (LAX), zip, or coordinates...",
            font=("Arial", 12),
            border_width=0,
            fg_color="transparent",
        )
        self.search_entry.pack(side="left", fill="x", expand=True, padx=(0, 5))

        # Favorites button
        self.favorites_button = ctk.CTkButton(
            self.search_frame,
            text="⭐",
            width=25,
            height=25,
            corner_radius=12,
            font=("Arial", 12),
            command=self.toggle_favorites,
            hover_color="#FFD700",
        )
        self.favorites_button.pack(side="right", padx=(0, 5))

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
        # Use safe_after_idle to allow click events to process first
        self.safe_after_idle(self.hide_dropdown)

    def is_child_of_dropdown(self, widget) -> bool:
        """Check if widget is part of the dropdown."""
        parent = widget
        while parent:
            if parent == self.autocomplete_frame or parent == self.search_entry:
                return True
            parent = parent.master
        return False

    def perform_search(self, query: str):
        """Perform autocomplete search with enhanced validation and error handling."""
        if self.is_searching:
            return

        # Validate search query
        validation_result = self.validate_search_query(query)
        if not validation_result["valid"]:
            self.show_validation_error(validation_result["error"])
            return

        # Store last search query
        self.last_search_query = query
        self.is_searching = True
        self.show_loading()

        def search_task():
            try:
                # Import custom exceptions for proper error handling
                from src.services.weather import (
                    APIKeyError,
                    NetworkError,
                    RateLimitError,
                    ServiceUnavailableError,
                    WeatherServiceError,
                )

                # Enhanced search with multiple format support
                results = self.enhanced_location_search(query)
                self.safe_after(0, self.handle_search_results, results)

            except RateLimitError as e:
                print(f"Rate limit exceeded: {e}")
                self.safe_after(
                    0, self.handle_search_error, "Search rate limit exceeded. Please wait a moment."
                )
            except APIKeyError as e:
                print(f"API key error: {e}")
                self.safe_after(
                    0, self.handle_search_error, "API configuration error. Please check settings."
                )
            except NetworkError as e:
                print(f"Network error: {e}")
                self.safe_after(
                    0,
                    self.handle_search_error,
                    "Network connection error. Please check your internet.",
                )
            except ServiceUnavailableError as e:
                print(f"Service unavailable: {e}")
                self.safe_after(0, self.handle_search_error, "Search service temporarily unavailable.")
            except WeatherServiceError as e:
                print(f"Weather service error: {e}")
                self.safe_after(0, self.handle_search_error, "Search service error. Please try again.")
            except Exception as e:
                print(f"Unexpected search error: {e}")
                self.safe_after(
                    0, self.handle_search_error, "An unexpected error occurred during search."
                )
            finally:
                self.is_searching = False
                self.safe_after(0, self.hide_loading)

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
        """Create a single autocomplete result item with enhanced display."""
        item_frame = ctk.CTkFrame(self.autocomplete_scroll, fg_color="transparent", height=45)
        item_frame.pack(fill="x", pady=1)
        item_frame.pack_propagate(False)

        # Main content frame
        content_frame = ctk.CTkFrame(item_frame, fg_color="transparent")
        content_frame.pack(side="left", fill="x", expand=True, padx=5, pady=2)

        # Country flag and location text with enhanced formatting
        flag = self.get_country_flag(result.country_code)

        # Primary location name
        primary_text = f"{flag} {result.name}"
        if hasattr(result, "state") and result.state:
            primary_text += f", {result.state}"
        if hasattr(result, "country") and result.country:
            primary_text += f", {result.country}"

        primary_label = ctk.CTkLabel(
            content_frame, text=primary_text, font=("Arial", 11, "bold"), anchor="w"
        )
        primary_label.pack(anchor="w", padx=5)

        # Secondary info (coordinates, type)
        secondary_info = []
        if hasattr(result, "latitude") and hasattr(result, "longitude"):
            secondary_info.append(f"📍 {result.latitude:.2f}, {result.longitude:.2f}")
        if hasattr(result, "type") and result.type:
            secondary_info.append(f"🏷️ {result.type}")

        if secondary_info:
            secondary_text = " • ".join(secondary_info)
            secondary_label = ctk.CTkLabel(
                content_frame,
                text=secondary_text,
                font=("Arial", 9),
                anchor="w",
                text_color="#888888",
            )
            secondary_label.pack(anchor="w", padx=5)

        # Favorite star button
        is_favorite = self.is_location_favorite(result)
        star_button = ctk.CTkButton(
            item_frame,
            text="⭐" if is_favorite else "☆",
            width=25,
            height=25,
            corner_radius=12,
            font=("Arial", 12),
            command=lambda: self.toggle_location_favorite(result),
            hover_color="#FFD700" if not is_favorite else "#FFA500",
        )
        star_button.pack(side="right", padx=5)

        # Bind click events
        for widget in [item_frame, content_frame, primary_label]:
            widget.bind("<Button-1>", lambda e, idx=index: self.select_item(idx))
            if hasattr(widget, "winfo_children"):
                for child in widget.winfo_children():
                    child.bind("<Button-1>", lambda e, idx=index: self.select_item(idx))

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
        """Select an autocomplete item with enhanced callback chain."""
        if 0 <= index < len(self.autocomplete_results):
            result = self.autocomplete_results[index]
            self.search_entry.delete(0, tk.END)
            self.search_entry.insert(0, result.display_name)

            # Add to search history with success flag
            self.add_to_search_history(result.display_name, success=True)

            # Clear any validation errors
            self.clear_validation_errors()

            # Notify parent with enhanced location data
            if self.on_location_selected:
                # Ensure we have all required location data
                enhanced_result = self.enhance_location_result(result)
                self.on_location_selected(enhanced_result)

            self.hide_dropdown()

            # Show success feedback
            self.show_selection_feedback(result.display_name)

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
            self.safe_after(500, self.animate_loading)

    def use_current_location(self):
        """Use geolocation with browser API fallback and IP-based location."""
        self.geo_button.configure(text="⏳")

        # Try browser geolocation first
        if not self.geolocation_permission_denied:
            self.try_browser_geolocation()
        else:
            # Fallback to IP-based location
            self.try_ip_based_location()

    def try_browser_geolocation(self):
        """Attempt to use browser geolocation API."""

        def get_browser_location():
            try:
                # Simulate browser geolocation request
                # In a real web app, this would use navigator.geolocation
                # For desktop app, we'll use IP-based location as fallback
                self.safe_after(0, self.try_ip_based_location)

            except Exception as e:
                print(f"Browser geolocation failed: {e}")
                self.geolocation_permission_denied = True
                self.safe_after(0, self.try_ip_based_location)

        threading.Thread(target=get_browser_location, daemon=True).start()

    def try_ip_based_location(self):
        """Fallback to IP-based location detection."""

        def get_ip_location():
            try:
                # Import custom exceptions for proper error handling
                from src.services.weather import (
                    APIKeyError,
                    NetworkError,
                    RateLimitError,
                    ServiceUnavailableError,
                )

                # Try geocoding service first
                location = self.geocoding_service.get_current_location()
                if location:
                    # Convert to LocationResult format if needed
                    if hasattr(location, "display_name"):
                        self.safe_after(0, self.handle_geolocation_result, location)
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
                        self.safe_after(0, self.handle_geolocation_result, location_result)
                else:
                    # Try IP-based location as final fallback
                    ip_location = self.get_ip_based_location()
                    if ip_location:
                        self.safe_after(0, self.handle_geolocation_result, ip_location)
                    else:
                        self.safe_after(0, self.handle_geolocation_error, "Location detection failed")

            except RateLimitError as e:
                print(f"Geolocation rate limit: {e}")
                self.safe_after(0, self.handle_geolocation_error, "Rate limit exceeded")
            except APIKeyError as e:
                print(f"Geolocation API key error: {e}")
                self.safe_after(0, self.handle_geolocation_error, "API configuration error")
            except NetworkError as e:
                print(f"Geolocation network error: {e}")
                self.safe_after(0, self.handle_geolocation_error, "Network connection error")
            except ServiceUnavailableError as e:
                print(f"Geolocation service unavailable: {e}")
                self.safe_after(0, self.handle_geolocation_error, "Service temporarily unavailable")
            except Exception as e:
                print(f"Unexpected geolocation error: {e}")
                self.safe_after(0, self.handle_geolocation_error, "Geolocation failed")

        threading.Thread(target=get_ip_location, daemon=True).start()

    def handle_geolocation_result(self, location: LocationResult):
        """Handle successful geolocation with enhanced feedback."""
        self.geo_button.configure(text="📍")
        self.search_entry.delete(0, tk.END)
        self.search_entry.insert(0, location.display_name)

        # Store detected location
        self.current_detected_location = location

        # Show detected location indicator
        self.show_detected_location_indicator(location.display_name)

        # Add to search history with geolocation flag
        self.add_to_search_history(location.display_name, success=True, is_geolocation=True)

        # Notify parent with enhanced location data
        if self.on_location_selected:
            enhanced_result = self.enhance_location_result(location)
            self.on_location_selected(enhanced_result)

    def handle_geolocation_error(self, error_message: str = "Location error"):
        """Handle geolocation error with user feedback."""
        self.geo_button.configure(text="❌")

        # Show error tooltip or status
        print(f"Geolocation error: {error_message}")

        # Reset button after 3 seconds
        self.safe_after(3000, lambda: self.geo_button.configure(text="📍"))

    def get_country_flag(self, country_code: str) -> str:
        """Get country flag emoji from country code."""
        if not country_code:
            return "🌍"

        # Common country flags
        flags = {
            "US": "🇺🇸",
            "CA": "🇨🇦",
            "GB": "🇬🇧",
            "DE": "🇩🇪",
            "FR": "🇫🇷",
            "IT": "🇮🇹",
            "ES": "🇪🇸",
            "AU": "🇦🇺",
            "JP": "🇯🇵",
            "CN": "🇨🇳",
            "IN": "🇮🇳",
            "BR": "🇧🇷",
            "MX": "🇲🇽",
            "RU": "🇷🇺",
            "KR": "🇰🇷",
            "NL": "🇳🇱",
            "SE": "🇸🇪",
            "NO": "🇳🇴",
            "DK": "🇩🇰",
            "FI": "🇫🇮",
            "CH": "🇨🇭",
            "AT": "🇦🇹",
            "BE": "🇧🇪",
            "PL": "🇵🇱",
            "CZ": "🇨🇿",
            "HU": "🇭🇺",
            "GR": "🇬🇷",
            "PT": "🇵🇹",
            "IE": "🇮🇪",
            "NZ": "🇳🇿",
            "ZA": "🇿🇦",
            "AR": "🇦🇷",
            "CL": "🇨🇱",
            "CO": "🇨🇴",
            "PE": "🇵🇪",
            "VE": "🇻🇪",
            "EG": "🇪🇬",
            "NG": "🇳🇬",
            "KE": "🇰🇪",
            "MA": "🇲🇦",
            "TH": "🇹🇭",
            "VN": "🇻🇳",
            "PH": "🇵🇭",
            "ID": "🇮🇩",
            "MY": "🇲🇾",
            "SG": "🇸🇬",
            "TR": "🇹🇷",
            "IL": "🇮🇱",
            "SA": "🇸🇦",
            "AE": "🇦🇪",
            "QA": "🇶🇦",
            "KW": "🇰🇼",
            "BH": "🇧🇭",
            "OM": "🇴🇲",
            "JO": "🇯🇴",
            "LB": "🇱🇧",
            "SY": "🇸🇾",
            "IQ": "🇮🇶",
            "IR": "🇮🇷",
            "AF": "🇦🇫",
            "PK": "🇵🇰",
            "BD": "🇧🇩",
            "LK": "🇱🇰",
            "NP": "🇳🇵",
            "BT": "🇧🇹",
            "MM": "🇲🇲",
            "KH": "🇰🇭",
            "LA": "🇱🇦",
            "MN": "🇲🇳",
            "KZ": "🇰🇿",
            "UZ": "🇺🇿",
            "TM": "🇹🇲",
            "KG": "🇰🇬",
            "TJ": "🇹🇯",
            "AM": "🇦🇲",
            "AZ": "🇦🇿",
            "GE": "🇬🇪",
            "UA": "🇺🇦",
            "BY": "🇧🇾",
            "MD": "🇲🇩",
            "RO": "🇷🇴",
            "BG": "🇧🇬",
            "RS": "🇷🇸",
            "HR": "🇭🇷",
            "BA": "🇧🇦",
            "ME": "🇲🇪",
            "MK": "🇲🇰",
            "AL": "🇦🇱",
            "SI": "🇸🇮",
            "SK": "🇸🇰",
            "LT": "🇱🇹",
            "LV": "🇱🇻",
            "EE": "🇪🇪",
            "IS": "🇮🇸",
            "MT": "🇲🇹",
            "CY": "🇨🇾",
            "LU": "🇱🇺",
            "LI": "🇱🇮",
            "AD": "🇦🇩",
            "MC": "🇲🇨",
            "SM": "🇸🇲",
            "VA": "🇻🇦",
        }

        return flags.get(country_code.upper(), "🌍")

    # Enhanced search validation and utility methods
    def validate_search_query(self, query: str) -> dict:
        """Validate search query and return validation result."""
        query = query.strip()

        if not query:
            return {"valid": False, "error": "Please enter a location to search"}

        if len(query) < 2:
            return {"valid": False, "error": "Search query must be at least 2 characters"}

        if len(query) > 100:
            return {"valid": False, "error": "Search query is too long"}

        # Check for invalid characters
        invalid_chars = ["<", ">", '"', "'", "&", ";", "|"]
        if any(char in query for char in invalid_chars):
            return {"valid": False, "error": "Search contains invalid characters"}

        return {"valid": True, "error": None}

    def detect_search_type(self, query: str) -> str:
        """Detect the type of search query."""
        query = query.strip().upper()

        # Airport codes (3 letters)
        if len(query) == 3 and query.isalpha():
            return "airport_code"

        # Coordinates (decimal format)
        if "," in query:
            parts = query.split(",")
            if len(parts) == 2:
                try:
                    lat = float(parts[0].strip())
                    lon = float(parts[1].strip())
                    if -90 <= lat <= 90 and -180 <= lon <= 180:
                        return "coordinates"
                except ValueError:
                    pass

        # ZIP codes (US format)
        if query.isdigit() and len(query) == 5:
            return "zip_code"

        # Postal codes (international format)
        if len(query) <= 10 and any(c.isdigit() for c in query):
            return "postal_code"

        # Default to city name
        return "city_name"

    def enhanced_location_search(self, query: str):
        """Enhanced location search with multiple format support."""
        search_type = self.detect_search_type(query)

        if search_type == "airport_code":
            return self.search_airport_code(query)
        elif search_type == "coordinates":
            return self.search_coordinates(query)
        else:
            return self.weather_service.search_locations_advanced(query)

    def search_airport_code(self, code: str):
        """Search for airport by IATA code."""
        # Common airport codes mapping
        airports = {
            "LAX": {
                "name": "Los Angeles",
                "state": "CA",
                "country": "United States",
                "lat": 33.9425,
                "lon": -118.4081,
            },
            "JFK": {
                "name": "New York",
                "state": "NY",
                "country": "United States",
                "lat": 40.6413,
                "lon": -73.7781,
            },
            "LHR": {
                "name": "London",
                "state": "England",
                "country": "United Kingdom",
                "lat": 51.4700,
                "lon": -0.4543,
            },
            "CDG": {
                "name": "Paris",
                "state": "Île-de-France",
                "country": "France",
                "lat": 49.0097,
                "lon": 2.5479,
            },
            "NRT": {
                "name": "Tokyo",
                "state": "Tokyo",
                "country": "Japan",
                "lat": 35.7720,
                "lon": 140.3929,
            },
            "SYD": {
                "name": "Sydney",
                "state": "NSW",
                "country": "Australia",
                "lat": -33.9399,
                "lon": 151.1753,
            },
            "DXB": {
                "name": "Dubai",
                "state": "Dubai",
                "country": "UAE",
                "lat": 25.2532,
                "lon": 55.3657,
            },
            "SIN": {
                "name": "Singapore",
                "state": "Singapore",
                "country": "Singapore",
                "lat": 1.3644,
                "lon": 103.9915,
            },
        }

        airport = airports.get(code.upper())
        if airport:
            from src.services.weather import LocationResult

            return [
                LocationResult(
                    name=airport["name"],
                    display_name=f"{airport['name']}, {airport['state']}, {airport['country']} (Airport: {code.upper()})",
                    latitude=airport["lat"],
                    longitude=airport["lon"],
                    country=airport["country"],
                    country_code=self.get_country_code_from_name(airport["country"]),
                    state=airport["state"],
                    raw_address=f"{airport['name']}, {airport['state']}, {airport['country']}",
                    type="airport",
                )
            ]

        # Fallback to regular search
        return self.weather_service.search_locations_advanced(code)

    def search_coordinates(self, query: str):
        """Search for location by coordinates."""
        try:
            parts = query.split(",")
            lat = float(parts[0].strip())
            lon = float(parts[1].strip())

            # Use reverse geocoding to get location name
            location_name = f"Location at {lat:.2f}, {lon:.2f}"

            from ...models.location import LocationResult

            return [
                LocationResult(
                    name=location_name,
                    display_name=location_name,
                    latitude=lat,
                    longitude=lon,
                    country="Unknown",
                    country_code="",
                    state="",
                    raw_address=f"{lat}, {lon}",
                    type="coordinates",
                )
            ]
        except (ValueError, IndexError):
            return []

    def get_country_code_from_name(self, country_name: str) -> str:
        """Get country code from country name."""
        country_codes = {
            "United States": "US",
            "United Kingdom": "GB",
            "France": "FR",
            "Japan": "JP",
            "Australia": "AU",
            "UAE": "AE",
            "Singapore": "SG",
        }
        return country_codes.get(country_name, "")

    def enhance_location_result(self, result):
        """Enhance location result with additional data."""
        # Ensure all required fields are present
        if not hasattr(result, "type"):
            result.type = self.detect_search_type(getattr(result, "name", ""))

        return result

    def show_validation_error(self, error_message: str):
        """Show validation error to user."""
        self.validation_errors.append(error_message)
        # You could show this in a tooltip or status bar
        print(f"Validation error: {error_message}")

    def clear_validation_errors(self):
        """Clear validation errors."""
        self.validation_errors.clear()

    def show_selection_feedback(self, location_name: str):
        """Show feedback when location is selected."""
        # Could show a brief success message
        print(f"Selected location: {location_name}")

    def show_detected_location_indicator(self, location_name: str):
        """Show indicator for detected location."""
        # Could show an icon or text indicating this is the detected location
        print(f"Detected location: {location_name}")

    def get_ip_based_location(self):
        """Get location based on IP address as fallback."""
        try:
            # This would typically use an IP geolocation service
            # For now, return None to indicate no fallback available
            return None
        except Exception as e:
            print(f"IP-based location failed: {e}")
            return None

    # Favorites management methods
    def load_favorites(self) -> dict:
        """Load favorite locations from file."""
        try:
            favorites_file = os.path.join(
                os.path.expanduser("~"), ".weather_dashboard_favorites.json"
            )
            if os.path.exists(favorites_file):
                with open(favorites_file, "r", encoding="utf-8") as f:
                    return json.load(f)
        except Exception as e:
            print(f"Error loading favorites: {e}")

        return {"favorite_locations": []}

    def save_favorites(self):
        """Save favorite locations to file."""
        try:
            favorites_file = os.path.join(
                os.path.expanduser("~"), ".weather_dashboard_favorites.json"
            )
            with open(favorites_file, "w", encoding="utf-8") as f:
                json.dump(self.favorites, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving favorites: {e}")

    def is_location_favorite(self, location) -> bool:
        """Check if location is in favorites."""
        location_key = f"{getattr(location, 'name', '')},{getattr(location, 'latitude', 0)},{getattr(location, 'longitude', 0)}"
        return any(
            fav.get("key") == location_key for fav in self.favorites.get("favorite_locations", [])
        )

    def toggle_location_favorite(self, location):
        """Toggle location favorite status."""
        location_key = f"{getattr(location, 'name', '')},{getattr(location, 'latitude', 0)},{getattr(location, 'longitude', 0)}"
        favorites_list = self.favorites.get("favorite_locations", [])

        # Remove if exists
        favorites_list = [fav for fav in favorites_list if fav.get("key") != location_key]

        # Add if not already favorite
        if not self.is_location_favorite(location):
            favorite_entry = {
                "key": location_key,
                "name": getattr(location, "name", ""),
                "display_name": getattr(location, "display_name", ""),
                "latitude": getattr(location, "latitude", 0),
                "longitude": getattr(location, "longitude", 0),
                "country": getattr(location, "country", ""),
                "state": getattr(location, "state", ""),
                "timestamp": datetime.now().isoformat(),
            }
            favorites_list.append(favorite_entry)

        self.favorites["favorite_locations"] = favorites_list[:20]  # Keep max 20 favorites
        self.save_favorites()

    def toggle_favorites(self):
        """Toggle favorites dropdown display."""
        if self.dropdown_visible:
            self.hide_dropdown()
        else:
            self.show_favorites_dropdown()

    def show_favorites_dropdown(self):
        """Show favorites in dropdown."""
        self.autocomplete_results = []

        # Convert favorites to LocationResult objects
        for fav in self.favorites.get("favorite_locations", []):
            from src.services.weather import LocationResult

            location_result = LocationResult(
                name=fav.get("name", ""),
                display_name=fav.get("display_name", ""),
                latitude=fav.get("latitude", 0),
                longitude=fav.get("longitude", 0),
                country=fav.get("country", ""),
                country_code=self.get_country_code_from_name(fav.get("country", "")),
                state=fav.get("state", ""),
                raw_address=fav.get("display_name", ""),
                type="favorite",
            )
            self.autocomplete_results.append(location_result)

        if self.autocomplete_results:
            self.update_autocomplete_results(self.autocomplete_results)
        else:
            # Show message about no favorites
            self.show_no_favorites_message()

    def show_no_favorites_message(self):
        """Show message when no favorites are available."""
        # Create a simple message frame
        if hasattr(self, "autocomplete_frame") and self.autocomplete_frame:
            # Clear existing content
            for widget in self.autocomplete_scroll.winfo_children():
                widget.destroy()

            # Show no favorites message
            message_frame = ctk.CTkFrame(
                self.autocomplete_scroll, fg_color="transparent", height=40
            )
            message_frame.pack(fill="x", pady=5)
            message_frame.pack_propagate(False)

            message_label = ctk.CTkLabel(
                message_frame,
                text="⭐ No favorite locations saved",
                font=("Arial", 11),
                text_color="#888888",
                anchor="center",
            )
            message_label.pack(expand=True, fill="both", padx=10, pady=10)

            self.show_dropdown()

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

    def add_to_search_history(self, query: str, success: bool = True, is_geolocation: bool = False):
        """Add search query to history with enhanced metadata."""
        # Remove if already exists
        self.search_history["recent_searches"] = [
            item for item in self.search_history["recent_searches"] if item["query"] != query
        ]

        # Add to beginning with enhanced metadata
        search_entry = {
            "query": query,
            "timestamp": datetime.now().isoformat(),
            "success": success,
            "is_geolocation": is_geolocation,
            "search_type": self.detect_search_type(query),
        }

        self.search_history["recent_searches"].insert(0, search_entry)

        # Keep only last 10 successful searches
        successful_searches = [
            item for item in self.search_history["recent_searches"] if item.get("success", True)
        ]
        self.search_history["recent_searches"] = successful_searches[:10]

        # Save to file
        self.save_search_history()

    def clear_search_history(self):
        """Clear all search history."""
        self.search_history = {"recent_searches": [], "favorites": []}
        self.save_search_history()
