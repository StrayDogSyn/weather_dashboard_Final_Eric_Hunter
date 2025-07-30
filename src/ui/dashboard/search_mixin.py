"""Search Functionality Mixin

Handles search operations, location detection, and suggestion management.
"""

import customtkinter as ctk
from typing import Optional, Dict, Any
import threading

from .base_dashboard import BaseDashboard


class SearchMixin(BaseDashboard):
    """Mixin for search functionality and location management."""
    
    def __init__(self):
        """Initialize search functionality."""
        super().__init__()
        
        # Search state
        self._search_in_progress = False
        self._last_search_query = ""
    
    def _on_city_search(self, city: str):
        """Handle city search request."""
        self._log_method_call("_on_city_search", city)
        
        if not city or not city.strip():
            self._update_status("Please enter a city name", self.STATUS_WARNING)
            return
        
        city = city.strip()
        
        # Validate city name
        if not self._validate_city_name(city):
            self._update_status("City name must be at least 2 characters", self.STATUS_WARNING)
            return
        
        # Prevent duplicate searches
        if city.lower() == self._last_search_query.lower() and not self.is_loading:
            self._update_status(f"Already showing weather for {city}", self.STATUS_INFO)
            return
        
        # Perform the search
        self._perform_search(city)
    
    def _on_location_detect(self):
        """Handle location detection request."""
        self._log_method_call("_on_location_detect")
        
        if self.is_loading:
            self._update_status("Please wait for current operation to complete", self.STATUS_WARNING)
            return
        
        try:
            # Show loading state
            self._show_loading("Detecting your location...")
            
            # Start location detection in background thread
            threading.Thread(
                target=self._detect_location_thread,
                daemon=True
            ).start()
            
        except Exception as e:
            self._hide_loading()
            error_msg = self._truncate_error_message(str(e))
            self._update_status(f"Location detection failed: {error_msg}", self.STATUS_ERROR)
            if self.logger:
                self.logger.error(f"Location detection error: {e}")
    
    def _on_suggestion_select(self, suggestion: Dict[str, Any]):
        """Handle suggestion selection from autocomplete."""
        self._log_method_call("_on_suggestion_select", suggestion)
        
        try:
            # Extract city name from suggestion
            city_name = suggestion.get('name', '')
            if not city_name:
                city_name = suggestion.get('display_name', '')
            
            if city_name:
                self._perform_search(city_name)
            else:
                self._update_status("Invalid suggestion selected", self.STATUS_WARNING)
                
        except Exception as e:
            error_msg = self._truncate_error_message(str(e))
            self._update_status(f"Suggestion selection failed: {error_msg}", self.STATUS_ERROR)
            if self.logger:
                self.logger.error(f"Suggestion selection error: {e}")
    
    def _perform_search(self, query: str):
        """Perform weather search for the given query."""
        self._log_method_call("_perform_search", query)
        
        if self.is_loading:
            self._update_status("Please wait for current search to complete", self.STATUS_WARNING)
            return
        
        if not self._validate_city_name(query):
            self._update_status("Invalid search query", self.STATUS_WARNING)
            return
        
        # Store search query
        self._last_search_query = query
        
        # Delegate to weather fetching
        if hasattr(self, '_fetch_weather'):
            self._fetch_weather(query)
        else:
            self._update_status("Weather service not available", self.STATUS_ERROR)
    
    def _detect_location_thread(self):
        """Detect user location in background thread."""
        try:
            if not self.weather_service:
                raise Exception("Weather service not available")
            
            # Use weather service location detection
            if hasattr(self.weather_service, 'detect_location'):
                location_data = self.weather_service.detect_location()
                
                if location_data and 'city' in location_data:
                    city = location_data['city']
                    
                    # Update UI on main thread
                    self.after(0, lambda: self._on_location_detected(city))
                else:
                    self.after(0, lambda: self._on_location_detection_failed("Could not determine location"))
            else:
                self.after(0, lambda: self._on_location_detection_failed("Location detection not supported"))
                
        except Exception as e:
            error_msg = str(e)
            self.after(0, lambda: self._on_location_detection_failed(error_msg))
    
    def _on_location_detected(self, city: str):
        """Handle successful location detection."""
        self._log_method_call("_on_location_detected", city)
        
        try:
            self._hide_loading()
            
            if city:
                self._update_status(f"Location detected: {city}", self.STATUS_SUCCESS)
                
                # Update search field if available
                self._update_search_field(city)
                
                # Perform search for detected location
                self._perform_search(city)
            else:
                self._update_status("Location detected but city unknown", self.STATUS_WARNING)
                
        except Exception as e:
            if self.logger:
                self.logger.error(f"Location detection success handler error: {e}")
    
    def _on_location_detection_failed(self, error_message: str):
        """Handle failed location detection."""
        self._log_method_call("_on_location_detection_failed", error_message)
        
        self._hide_loading()
        error_msg = self._truncate_error_message(error_message)
        self._update_status(f"Location detection failed: {error_msg}", self.STATUS_ERROR)
        
        if self.logger:
            self.logger.error(f"Location detection failed: {error_message}")
    
    def _update_search_field(self, text: str):
        """Update the search field with the given text."""
        try:
            # Update enhanced search bar
            if self.enhanced_search_bar and hasattr(self.enhanced_search_bar, 'set_search_text'):
                self.enhanced_search_bar.set_search_text(text)
            
            # Update standard search bar
            elif self.search_bar and hasattr(self.search_bar, 'set_search_text'):
                self.search_bar.set_search_text(text)
            
            # Update fallback search entry
            elif self.fallback_search_entry:
                self.fallback_search_entry.delete(0, 'end')
                self.fallback_search_entry.insert(0, text)
                
        except Exception as e:
            if self.logger:
                self.logger.error(f"Failed to update search field: {e}")
    
    def _get_search_text(self) -> str:
        """Get current search text from active search widget."""
        try:
            # Check enhanced search bar
            if self.enhanced_search_bar and hasattr(self.enhanced_search_bar, 'get_search_text'):
                return self.enhanced_search_bar.get_search_text().strip()
            
            # Check standard search bar
            if self.search_bar and hasattr(self.search_bar, 'get_search_text'):
                return self.search_bar.get_search_text().strip()
            
            # Check fallback search entry
            if self.fallback_search_entry:
                return self.fallback_search_entry.get().strip()
            
            return ""
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"Failed to get search text: {e}")
            return ""
    
    def _clear_search_text(self):
        """Clear search text from all search widgets."""
        try:
            # Clear enhanced search bar
            if self.enhanced_search_bar and hasattr(self.enhanced_search_bar, 'clear_search'):
                self.enhanced_search_bar.clear_search()
            
            # Clear standard search bar
            if self.search_bar and hasattr(self.search_bar, 'clear_search'):
                self.search_bar.clear_search()
            
            # Clear fallback search entry
            if self.fallback_search_entry:
                self.fallback_search_entry.delete(0, 'end')
                
        except Exception as e:
            if self.logger:
                self.logger.error(f"Failed to clear search text: {e}")
    
    def _validate_search_widget(self) -> bool:
        """Validate that search widgets are properly configured."""
        try:
            # Check if any search widget is available
            has_enhanced = self.enhanced_search_bar is not None
            has_standard = self.search_bar is not None
            has_fallback = self.fallback_search_entry is not None
            
            if not (has_enhanced or has_standard or has_fallback):
                if self.logger:
                    self.logger.error("No search widgets available")
                return False
            
            # Test search functionality
            search_text = self._get_search_text()
            
            if self.logger:
                self.logger.debug(f"Search widget validation: enhanced={has_enhanced}, standard={has_standard}, fallback={has_fallback}")
            
            return True
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"Search widget validation failed: {e}")
            return False