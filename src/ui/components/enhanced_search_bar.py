from typing import List, Optional, Callable
import json
import os
import customtkinter as ctk


class EnhancedSearchBar(ctk.CTkFrame):
    """Enhanced search bar component with glassmorphic styling and advanced features."""
    
    def __init__(self, parent, placeholder="Search for a city...", on_search: Optional[Callable] = None, weather_service=None):
        """Initialize the enhanced search bar.
        
        Args:
            parent: Parent widget
            placeholder: Placeholder text for search entry
            on_search: Callback function for search events
            weather_service: Weather service instance for geocoding
        """
        super().__init__(parent, fg_color="transparent")
        
        # Store parameters
        self.placeholder = placeholder
        self.on_search = on_search
        self.weather_service = weather_service
        
        # Initialize instance variables
        self.search_history = self._load_search_history()
        self.suggestions = []
        self.suggestion_widgets = []
        self.selected_suggestion_index = -1
        
        # Create suggestion dropdown frame
        self.suggestion_frame = ctk.CTkFrame(
            self,
            fg_color=("#FFFFFF", "#2B2B2B"),
            corner_radius=15,
            border_width=1,
            border_color=("#E0E0E0", "#404040")
        )
        # Initially hidden
        self.suggestion_frame.pack_forget()
        
        # Create the main search container with glassmorphic styling
        self.search_container = ctk.CTkFrame(
            self,
            fg_color=("#FFFFFF", "#1E1E1E"),
            corner_radius=15,
            border_width=2
        )
        self.search_container.pack(fill="x", padx=10, pady=5)
        
        # Create search icon
        self.search_icon = ctk.CTkLabel(
            self.search_container,
            text="🔍",
            font=("Arial", 16),
            fg_color="transparent"
        )
        self.search_icon.pack(side="left", padx=(10, 5))
        
        # Create search entry field
        self.search_entry = ctk.CTkEntry(
            self.search_container,
            placeholder_text=self.placeholder,
            fg_color="transparent",
            border_width=0,
            font=("Arial", 14)
        )
        self.search_entry.pack(side="left", fill="x", expand=True, padx=(0, 5))
        
        # Create button container for the four action buttons
        self.button_container = ctk.CTkFrame(
            self.search_container,
            fg_color="transparent"
        )
        self.button_container.pack(side="right", padx=(5, 10))
        
        # Create search button with icon
        self.search_button = ctk.CTkButton(
            self.button_container,
            text="🔍",
            width=35,
            height=30,
            corner_radius=8,
            font=("Arial", 16),
            command=self._perform_search,
            hover_color=("#0078D4", "#106EBE")
        )
        self.search_button.pack(side="left", padx=2)
        
        # Create current location button with icon
        self.current_location_button = ctk.CTkButton(
            self.button_container,
            text="📍",
            width=35,
            height=30,
            corner_radius=8,
            font=("Arial", 16),
            command=self._get_current_location,
            hover_color=("#0078D4", "#106EBE")
        )
        self.current_location_button.pack(side="left", padx=2)
        
        # Create random location button with icon
        self.random_location_button = ctk.CTkButton(
            self.button_container,
            text="🎲",
            width=35,
            height=30,
            corner_radius=8,
            font=("Arial", 16),
            command=self._get_random_location,
            hover_color=("#0078D4", "#106EBE")
        )
        self.random_location_button.pack(side="left", padx=2)
        
        # Create clear button with icon - always visible with proper sizing
        self.clear_button = ctk.CTkButton(
            self.button_container,
            text="✕",
            width=35,
            height=30,
            corner_radius=8,
            font=("Arial", 14, "bold"),
            command=self._clear_search,
            hover_color=("#D13438", "#A4262C"),
            fg_color=("#E74C3C", "#C0392B")
        )
        self.clear_button.pack(side="left", padx=2)
        
        # Create search variable for tracking changes
        self.search_var = ctk.StringVar()
        self.search_entry.configure(textvariable=self.search_var)
        
        # Bind events
        self._bind_events()
    
    def _bind_events(self):
        """Bind keyboard and mouse events."""
        self.search_var.trace("w", self._on_search_change)
        self.search_entry.bind("<Return>", self._on_enter_key)
        self.search_entry.bind("<Escape>", lambda e: self._hide_suggestions())
        self.search_entry.bind("<Up>", self._navigate_suggestions_up)
        self.search_entry.bind("<Down>", self._navigate_suggestions_down)
        self.search_entry.bind("<KeyRelease>", self._on_key_release)
        self.search_entry.bind("<FocusIn>", self._on_focus_in)
        self.search_entry.bind("<FocusOut>", self._on_focus_out)
    
    def _on_key_release(self, event):
        """Handle key release events for dynamic features."""
        # Clear button is now always visible, no need for show/hide logic
        pass
    
    def _on_focus_in(self, event):
        """Handle focus in events."""
        current_text = self.search_entry.get().strip()
        if current_text:
            self._update_suggestions(current_text)
    
    def _on_focus_out(self, event):
        """Handle focus out events."""
        # Delay hiding to allow clicking on suggestions
        self.after(100, self._hide_suggestions)
    
    def _clear_search(self):
        """Clear the search input and focus"""
        self.search_var.set("")
        self.search_entry.focus_set()
        self._hide_suggestions()
    
    def _perform_search(self):
        """Execute search and update history"""
        query = self.search_var.get().strip()
        if not query:
            return
            
        # Add to search history
        self._add_to_history(query)
        
        # Execute search callback if provided
        if self.on_search:
            self.on_search(query)
    
    def _on_enter_key(self, event):
        """Handle Enter key press - select suggestion or perform search"""
        if self.suggestions and self.selected_suggestion_index >= 0:
            # Select the highlighted suggestion
            suggestion_text = self.suggestions[self.selected_suggestion_index]["text"]
            self._select_suggestion(suggestion_text)
        else:
            # Perform regular search
            self._perform_search()
        return "break"
    
    def get_search_text(self) -> str:
        """Get current search text."""
        return self.search_entry.get().strip()
    
    def set_search_text(self, text: str):
        """Set search text programmatically."""
        self.search_entry.delete(0, "end")
        self.search_entry.insert(0, text)
        if text:
            self.clear_button.pack(side="right", padx=(0, 5), before=self.search_button)
    
    def _load_search_history(self) -> List[str]:
        """Load search history from file."""
        history_file = "data/search_history.json"
        if os.path.exists(history_file):
            try:
                with open(history_file, "r") as f:
                    data = json.load(f)
                    # Handle both old format (dict) and new format (list)
                    if isinstance(data, dict):
                        # Extract search queries from the dict format
                        if "recent_searches" in data:
                            return [item.get("query", "") for item in data["recent_searches"] if item.get("query")]
                        return []
                    elif isinstance(data, list):
                        return data
            except:
                pass
        return []
    
    def _save_search_history(self):
        """Save search history to file."""
        history_file = "data/search_history.json"
        os.makedirs(os.path.dirname(history_file), exist_ok=True)
        with open(history_file, "w") as f:
            json.dump(self.search_history, f)
    
    def _add_to_history(self, search_text: str):
        """Add search to history."""
        if search_text in self.search_history:
            self.search_history.remove(search_text)
        self.search_history.insert(0, search_text)
        self.search_history = self.search_history[:10]  # Keep last 10
        self._save_search_history()
    
    def _on_search_change(self, *args):
        """Handle search text changes."""
        current_text = self.search_var.get().strip()
        
        # Show/hide clear button based on text content
        if current_text and not self.clear_button.winfo_viewable():
            self.clear_button.pack(side="right", padx=(0, 5), before=self.search_button)
        elif not current_text and self.clear_button.winfo_viewable():
            self.clear_button.pack_forget()
        
        # Update suggestions
        self._update_suggestions(current_text)
    
    def _update_suggestions(self, search_text: str):
        """Update search suggestions based on current text."""
        if not search_text:
            self._hide_suggestions()
            return
        
        suggestions = []
        # Add from search history
        history_matches = [h for h in self.search_history
                          if h.lower().startswith(search_text.lower())][:3]
        for match in history_matches:
            suggestions.append({"text": match, "type": "history"})
        
        # Add city suggestions
        city_suggestions = self._get_city_suggestions(search_text)[:5]
        for city in city_suggestions:
            suggestions.append({"text": city, "type": "city"})
        
        self.suggestions = suggestions
        self._show_suggestions()
    
    def _get_city_suggestions(self, search_text: str) -> List[str]:
        """Get city suggestions based on search text using geocoding service."""
        suggestions = []
        
        # Try to get suggestions from weather service geocoding
        if self.weather_service and len(search_text) >= 2:
            try:
                geocoding_results = self.weather_service.search_locations(search_text, limit=5)
                for result in geocoding_results:
                    # Use the name directly if it's already well-formatted (e.g., from airport search)
                    if hasattr(result, 'name') and result.name:
                        # Check if the name already contains location info (like airport codes)
                        if '(' in result.name or 'Airport' in result.name:
                            suggestions.append(result.name)
                        else:
                            # Format city display name manually for regular locations
                            if hasattr(result, 'state') and result.state and hasattr(result, 'country') and result.country == 'US':
                                display_name = f"{result.name}, {result.state}, {result.country}"
                            elif hasattr(result, 'country') and result.country:
                                display_name = f"{result.name}, {result.country}"
                            else:
                                display_name = result.name
                            suggestions.append(display_name)
                    elif hasattr(result, 'display') and result.display:
                        suggestions.append(result.display)
                    else:
                        # Fallback to basic name
                        suggestions.append(str(result))
            except Exception as e:
                print(f"Geocoding error: {e}")
        
        # Fallback to common cities if geocoding fails or no service available
        if not suggestions:
            common_cities = [
                "New York, US", "Los Angeles, US", "Chicago, US",
                "Houston, US", "Phoenix, US", "Philadelphia, US",
                "San Antonio, US", "San Diego, US", "Dallas, US",
                "San Jose, US", "Austin, US", "Jacksonville, US",
                "Fort Worth, US", "Columbus, US", "Charlotte, US",
                "San Francisco, US", "Indianapolis, US", "Seattle, US",
                "Denver, US", "Washington, US", "Boston, US",
                "El Paso, US", "Nashville, US", "Detroit, US",
                "Oklahoma City, US", "Portland, US", "Las Vegas, US",
                "Memphis, US", "Louisville, US", "Baltimore, US"
            ]
            suggestions = [c for c in common_cities
                          if c.lower().startswith(search_text.lower())]
        
        return suggestions
    
    def _show_suggestions(self):
        """Display the suggestion dropdown"""
        if not self.suggestions:
            self._hide_suggestions()
            return
        
        # Clear existing widgets
        for widget in self.suggestion_widgets:
            widget.destroy()
        self.suggestion_widgets.clear()
        
        # Create suggestion items
        for i, suggestion in enumerate(self.suggestions):
            frame = ctk.CTkFrame(self.suggestion_frame,
                               fg_color="transparent", height=40)
            frame.pack(fill="x", padx=5, pady=2)
            
            # Icon based on type
            icon = "📍" if suggestion["type"] == "city" else "🕐"
            icon_label = ctk.CTkLabel(frame, text=icon, width=30)
            icon_label.pack(side="left", padx=(10, 5))
            
            # Suggestion text
            text_label = ctk.CTkLabel(frame, text=suggestion["text"],
                                    font=("Arial", 12), anchor="w")
            text_label.pack(side="left", fill="x", expand=True)
            
            # Bind hover and click events
            frame.bind("<Enter>", lambda e, idx=i: self._highlight_suggestion(idx))
            frame.bind("<Button-1>",
                      lambda e, txt=suggestion["text"]: self._select_suggestion(txt))
            
            self.suggestion_widgets.append(frame)
        
        # Position dropdown below search container
        self.suggestion_frame.place(in_=self.search_container,
                                  x=0, y=self.search_container.winfo_height() + 5,
                                  relwidth=1)
        self.suggestion_frame.lift()
    
    def _hide_suggestions(self):
        """Hide the suggestion dropdown and reset selection"""
        self.suggestion_frame.place_forget()
        self.selected_suggestion_index = -1
        for widget in self.suggestion_widgets:
            widget.destroy()
        self.suggestion_widgets.clear()
    
    def _select_suggestion(self, text):
        """Apply the selected suggestion to the search field"""
        self.search_var.set(text)
        self.search_entry.focus_set()
        self._hide_suggestions()
        self._perform_search()
    
    def _navigate_suggestions(self, direction):
        """Navigate through suggestions with arrow keys"""
        if not self.suggestions:
            return
            
        if direction == "down":
            self.selected_suggestion_index = min(self.selected_suggestion_index + 1, len(self.suggestions) - 1)
        elif direction == "up":
            self.selected_suggestion_index = max(self.selected_suggestion_index - 1, -1)
            
        # Update visual highlighting
        self._highlight_suggestion(self.selected_suggestion_index)
    
    def _navigate_suggestions_up(self, event):
        """Navigate suggestions upward."""
        self._navigate_suggestions("up")
        return "break"  # Prevent default behavior
    
    def _navigate_suggestions_down(self, event):
        """Navigate suggestions downward."""
        self._navigate_suggestions("down")
        return "break"  # Prevent default behavior
    
    def _highlight_suggestion(self, index):
        """Provide visual feedback on suggestion hover"""
        if index < 0 or index >= len(self.suggestion_widgets):
            return
            
        # Reset all suggestions to normal state
        for widget in self.suggestion_widgets:
            widget.configure(fg_color="transparent")
            
        # Highlight selected suggestion
        if index >= 0:
            self.suggestion_widgets[index].configure(fg_color=("#E0E0E0", "#404040"))
            self.selected_suggestion_index = index
    
    def clear(self):
        """Clear the search bar."""
        self._clear_search()
    
    def _get_current_location(self):
        """Get current location using IP geolocation and search for it."""
        try:
            if self.weather_service and hasattr(self.weather_service, 'geocoding_service'):
                location_result = self.weather_service.geocoding_service.get_current_location()
                if location_result and location_result.display_name:
                    # Set the location in the search bar and trigger search
                    self.search_var.set(location_result.display_name)
                    if self.on_search:
                        self.on_search(location_result.display_name)
                    return
                    
            # If geolocation fails, try alternative IP services
            import requests
            try:
                # Try ipinfo.io as backup
                response = requests.get("https://ipinfo.io/json", timeout=3)
                if response.status_code == 200:
                    data = response.json()
                    city = data.get('city')
                    region = data.get('region')
                    country = data.get('country')
                    if city and region:
                        location_str = f"{city}, {region}, {country}"
                        self.search_var.set(location_str)
                        if self.on_search:
                            self.on_search(location_str)
                        return
            except:
                pass
                
            # Final fallback - use a major city as default
            fallback_location = "London, UK"  # Changed from New York for better global coverage
            self.search_var.set(fallback_location)
            if self.on_search:
                self.on_search(fallback_location)
                
        except Exception as e:
            print(f"Error getting current location: {e}")
            # Fallback to default location
            fallback_location = "London, UK"
            self.search_var.set(fallback_location)
            if self.on_search:
                self.on_search(fallback_location)
    
    def _get_random_location(self):
        """Get a random location from a predefined list of interesting cities."""
        import random
        
        # List of interesting cities around the world
        random_cities = [
            "Tokyo, Japan",
            "Paris, France",
            "London, UK",
            "Sydney, Australia",
            "Rio de Janeiro, Brazil",
            "Cairo, Egypt",
            "Mumbai, India",
            "Moscow, Russia",
            "Cape Town, South Africa",
            "Bangkok, Thailand",
            "Istanbul, Turkey",
            "Barcelona, Spain",
            "Amsterdam, Netherlands",
            "Singapore",
            "Dubai, UAE",
            "Seoul, South Korea",
            "Mexico City, Mexico",
            "Buenos Aires, Argentina",
            "Stockholm, Sweden",
            "Reykjavik, Iceland",
            "Marrakech, Morocco",
            "Kyoto, Japan",
            "Venice, Italy",
            "Prague, Czech Republic",
            "Bali, Indonesia",
            "Santorini, Greece",
            "Machu Picchu, Peru",
            "Banff, Canada",
            "Queenstown, New Zealand",
            "Maldives"
        ]
        
        # Select a random city
        random_city = random.choice(random_cities)
        
        # Set the location in the search bar and trigger search
        self.search_var.set(random_city)
        if self.on_search:
            self.on_search(random_city)