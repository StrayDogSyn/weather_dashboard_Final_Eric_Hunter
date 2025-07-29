"""Weather Dashboard Controller

Handles UI event management and coordinates between UI components and services.
Separates event handling logic from UI presentation.
"""

import logging
import asyncio
from typing import Dict, Any, Optional, Callable, List
from datetime import datetime
import tkinter as tk
from tkinter import messagebox, ttk

from services.service_factory import get_service_factory
from processors.weather_processor import WeatherDataProcessor, ProcessedWeatherData
from parsers.api_response_parser import APIResponseParser


class WeatherDashboardController:
    """Controller for weather dashboard UI events and data flow."""
    
    def __init__(self, dashboard_ui=None):
        """Initialize the dashboard controller.
        
        Args:
            dashboard_ui: Reference to the main dashboard UI component
        """
        self.logger = logging.getLogger(__name__)
        self.dashboard_ui = dashboard_ui
        
        # Initialize services
        self.service_factory = get_service_factory()
        self.weather_service = self.service_factory.get_weather_service()
        self.config_service = self.service_factory.get_config_service()
        self.logging_service = self.service_factory.get_logging_service()
        
        # Initialize processors
        self.weather_processor = WeatherDataProcessor(self.config_service)
        self.api_parser = APIResponseParser()
        
        # State management
        self.current_location = None
        self.current_weather_data = None
        self.is_loading = False
        self.auto_refresh_enabled = True
        self.refresh_interval = 300000  # 5 minutes in milliseconds
        
        # Event callbacks
        self.on_weather_updated = None
        self.on_error_occurred = None
        self.on_loading_changed = None
        
        # UI update queue for thread safety
        self.ui_update_queue = []
        
        self.logger.info("Weather dashboard controller initialized")
    
    def set_dashboard_ui(self, dashboard_ui):
        """Set reference to dashboard UI component.
        
        Args:
            dashboard_ui: Dashboard UI component instance
        """
        self.dashboard_ui = dashboard_ui
        self.logger.debug("Dashboard UI reference set")
    
    def set_event_callbacks(self, on_weather_updated: Callable = None,
                          on_error_occurred: Callable = None,
                          on_loading_changed: Callable = None):
        """Set event callback functions.
        
        Args:
            on_weather_updated: Callback for weather data updates
            on_error_occurred: Callback for error handling
            on_loading_changed: Callback for loading state changes
        """
        self.on_weather_updated = on_weather_updated
        self.on_error_occurred = on_error_occurred
        self.on_loading_changed = on_loading_changed
        self.logger.debug("Event callbacks configured")
    
    async def handle_search_request(self, location: str) -> bool:
        """Handle weather search request.
        
        Args:
            location: Location to search for
            
        Returns:
            True if search was successful, False otherwise
        """
        if not location or not location.strip():
            self._handle_error("Please enter a valid location", "INVALID_INPUT")
            return False
        
        location = location.strip()
        self.logger.info(f"Handling search request for: {location}")
        
        try:
            # Set loading state
            self._set_loading_state(True)
            
            # Fetch weather data
            weather_data = await self._fetch_weather_data(location)
            if not weather_data:
                return False
            
            # Process the data
            processed_data = self._process_weather_data(weather_data)
            if not processed_data:
                return False
            
            # Update state
            self.current_location = location
            self.current_weather_data = processed_data
            
            # Notify UI of successful update
            self._notify_weather_updated(processed_data)
            
            # Add to recent searches
            self._add_to_recent_searches(location)
            
            self.logger.info(f"Successfully processed weather data for {location}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error handling search request: {e}")
            self._handle_error(f"Failed to get weather data: {str(e)}", "SEARCH_ERROR")
            return False
        finally:
            self._set_loading_state(False)
    
    def handle_refresh_request(self) -> bool:
        """Handle weather data refresh request.
        
        Returns:
            True if refresh was successful, False otherwise
        """
        if not self.current_location:
            self._handle_error("No location to refresh", "NO_LOCATION")
            return False
        
        self.logger.info(f"Handling refresh request for: {self.current_location}")
        
        # Use asyncio to handle the async search
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If loop is already running, schedule the coroutine
                asyncio.create_task(self.handle_search_request(self.current_location))
            else:
                # If no loop is running, run the coroutine
                loop.run_until_complete(self.handle_search_request(self.current_location))
            return True
        except Exception as e:
            self.logger.error(f"Error handling refresh request: {e}")
            self._handle_error(f"Failed to refresh weather data: {str(e)}", "REFRESH_ERROR")
            return False
    
    def handle_favorite_add(self, location: str) -> bool:
        """Handle adding location to favorites.
        
        Args:
            location: Location to add to favorites
            
        Returns:
            True if successfully added, False otherwise
        """
        try:
            # This would typically interact with a favorites service
            # For now, we'll use the dashboard UI's favorites manager
            if self.dashboard_ui and hasattr(self.dashboard_ui, 'search_bar'):
                search_bar = self.dashboard_ui.search_bar
                if hasattr(search_bar, 'favorites_manager'):
                    success = search_bar.favorites_manager.add_favorite(location)
                    if success:
                        self.logger.info(f"Added {location} to favorites")
                        return True
            
            self.logger.warning(f"Failed to add {location} to favorites")
            return False
            
        except Exception as e:
            self.logger.error(f"Error adding favorite: {e}")
            self._handle_error(f"Failed to add favorite: {str(e)}", "FAVORITE_ERROR")
            return False
    
    def handle_favorite_remove(self, location: str) -> bool:
        """Handle removing location from favorites.
        
        Args:
            location: Location to remove from favorites
            
        Returns:
            True if successfully removed, False otherwise
        """
        try:
            # This would typically interact with a favorites service
            if self.dashboard_ui and hasattr(self.dashboard_ui, 'search_bar'):
                search_bar = self.dashboard_ui.search_bar
                if hasattr(search_bar, 'favorites_manager'):
                    success = search_bar.favorites_manager.remove_favorite(location)
                    if success:
                        self.logger.info(f"Removed {location} from favorites")
                        return True
            
            self.logger.warning(f"Failed to remove {location} from favorites")
            return False
            
        except Exception as e:
            self.logger.error(f"Error removing favorite: {e}")
            self._handle_error(f"Failed to remove favorite: {str(e)}", "FAVORITE_ERROR")
            return False
    
    def handle_unit_change(self, new_unit: str) -> bool:
        """Handle weather unit change.
        
        Args:
            new_unit: New unit system ('metric', 'imperial', 'kelvin')
            
        Returns:
            True if successfully changed, False otherwise
        """
        try:
            # Update configuration
            if self.config_service:
                self.config_service.set_weather_units(new_unit)
            
            # Refresh current weather data with new units
            if self.current_location:
                self.handle_refresh_request()
            
            self.logger.info(f"Changed weather units to: {new_unit}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error changing units: {e}")
            self._handle_error(f"Failed to change units: {str(e)}", "UNIT_ERROR")
            return False
    
    def handle_auto_refresh_toggle(self, enabled: bool) -> None:
        """Handle auto-refresh toggle.
        
        Args:
            enabled: Whether auto-refresh should be enabled
        """
        self.auto_refresh_enabled = enabled
        
        if enabled and self.dashboard_ui:
            # Schedule next refresh
            self._schedule_auto_refresh()
            self.logger.info("Auto-refresh enabled")
        else:
            self.logger.info("Auto-refresh disabled")
    
    def handle_theme_change(self, theme: str) -> bool:
        """Handle UI theme change.
        
        Args:
            theme: New theme name
            
        Returns:
            True if successfully changed, False otherwise
        """
        try:
            # Update configuration
            if self.config_service:
                self.config_service.set_ui_theme(theme)
            
            # Apply theme to UI
            if self.dashboard_ui and hasattr(self.dashboard_ui, 'apply_theme'):
                self.dashboard_ui.apply_theme(theme)
            
            self.logger.info(f"Changed theme to: {theme}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error changing theme: {e}")
            self._handle_error(f"Failed to change theme: {str(e)}", "THEME_ERROR")
            return False
    
    def get_current_weather_data(self) -> Optional[ProcessedWeatherData]:
        """Get current weather data.
        
        Returns:
            Current processed weather data or None
        """
        return self.current_weather_data
    
    def get_current_location(self) -> Optional[str]:
        """Get current location.
        
        Returns:
            Current location string or None
        """
        return self.current_location
    
    def is_loading_data(self) -> bool:
        """Check if data is currently being loaded.
        
        Returns:
            True if loading, False otherwise
        """
        return self.is_loading
    
    async def _fetch_weather_data(self, location: str) -> Optional[Dict[str, Any]]:
        """Fetch weather data from service.
        
        Args:
            location: Location to fetch data for
            
        Returns:
            Raw weather data or None if failed
        """
        try:
            # Get weather data from service
            weather_data = await self.weather_service.get_weather_data(location)
            
            # Parse the response
            parsed_response = self.api_parser.parse(weather_data, 'weather')
            
            if not parsed_response.success:
                self._handle_error(
                    parsed_response.error_message or "Failed to parse weather data",
                    parsed_response.error_code or "PARSE_ERROR"
                )
                return None
            
            return parsed_response.data
            
        except Exception as e:
            self.logger.error(f"Error fetching weather data: {e}")
            raise
    
    def _process_weather_data(self, raw_data: Dict[str, Any]) -> Optional[ProcessedWeatherData]:
        """Process raw weather data.
        
        Args:
            raw_data: Raw weather data from API
            
        Returns:
            Processed weather data or None if failed
        """
        try:
            processed_data = self.weather_processor.process(raw_data)
            
            # Validate processed data
            if not self.weather_processor.validate(processed_data):
                self._handle_error("Invalid weather data received", "VALIDATION_ERROR")
                return None
            
            return processed_data
            
        except Exception as e:
            self.logger.error(f"Error processing weather data: {e}")
            self._handle_error(f"Failed to process weather data: {str(e)}", "PROCESSING_ERROR")
            return None
    
    def _set_loading_state(self, loading: bool) -> None:
        """Set loading state and notify UI.
        
        Args:
            loading: Whether data is being loaded
        """
        self.is_loading = loading
        
        if self.on_loading_changed:
            try:
                self.on_loading_changed(loading)
            except Exception as e:
                self.logger.error(f"Error in loading state callback: {e}")
    
    def _notify_weather_updated(self, weather_data: ProcessedWeatherData) -> None:
        """Notify UI of weather data update.
        
        Args:
            weather_data: Updated weather data
        """
        if self.on_weather_updated:
            try:
                self.on_weather_updated(weather_data)
            except Exception as e:
                self.logger.error(f"Error in weather update callback: {e}")
    
    def _handle_error(self, message: str, error_code: str) -> None:
        """Handle error and notify UI.
        
        Args:
            message: Error message
            error_code: Error code
        """
        self.logger.error(f"Controller error [{error_code}]: {message}")
        
        if self.on_error_occurred:
            try:
                self.on_error_occurred(message, error_code)
            except Exception as e:
                self.logger.error(f"Error in error callback: {e}")
        else:
            # Fallback to messagebox if no callback is set
            messagebox.showerror("Error", message)
    
    def _add_to_recent_searches(self, location: str) -> None:
        """Add location to recent searches.
        
        Args:
            location: Location to add
        """
        try:
            if self.dashboard_ui and hasattr(self.dashboard_ui, 'search_bar'):
                search_bar = self.dashboard_ui.search_bar
                if hasattr(search_bar, 'recent_searches_manager'):
                    search_bar.recent_searches_manager.add_search(location)
        except Exception as e:
            self.logger.error(f"Error adding to recent searches: {e}")
    
    def _schedule_auto_refresh(self) -> None:
        """Schedule automatic refresh."""
        if self.auto_refresh_enabled and self.dashboard_ui:
            try:
                # Schedule refresh using tkinter's after method
                self.dashboard_ui.after(self.refresh_interval, self._auto_refresh_callback)
            except Exception as e:
                self.logger.error(f"Error scheduling auto refresh: {e}")
    
    def _auto_refresh_callback(self) -> None:
        """Callback for automatic refresh."""
        if self.auto_refresh_enabled and self.current_location:
            self.logger.debug("Performing automatic refresh")
            self.handle_refresh_request()
            
            # Schedule next refresh
            self._schedule_auto_refresh()


class SearchController:
    """Controller specifically for search functionality."""
    
    def __init__(self, dashboard_controller: WeatherDashboardController):
        """Initialize search controller.
        
        Args:
            dashboard_controller: Main dashboard controller
        """
        self.logger = logging.getLogger(__name__)
        self.dashboard_controller = dashboard_controller
        
        # Search state
        self.search_suggestions = []
        self.is_searching = False
    
    def handle_search_input_change(self, search_text: str) -> None:
        """Handle search input text changes.
        
        Args:
            search_text: Current search input text
        """
        if len(search_text) >= 2:  # Start suggesting after 2 characters
            self._update_search_suggestions(search_text)
    
    def handle_search_submit(self, location: str) -> None:
        """Handle search form submission.
        
        Args:
            location: Location to search for
        """
        if not self.is_searching:
            self.is_searching = True
            try:
                # Use asyncio to handle the async search
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    asyncio.create_task(self._perform_search(location))
                else:
                    loop.run_until_complete(self._perform_search(location))
            except Exception as e:
                self.logger.error(f"Error submitting search: {e}")
                self.is_searching = False
    
    def handle_suggestion_select(self, suggestion: str) -> None:
        """Handle selection of search suggestion.
        
        Args:
            suggestion: Selected suggestion
        """
        self.handle_search_submit(suggestion)
    
    async def _perform_search(self, location: str) -> None:
        """Perform the actual search.
        
        Args:
            location: Location to search for
        """
        try:
            await self.dashboard_controller.handle_search_request(location)
        finally:
            self.is_searching = False
    
    def _update_search_suggestions(self, search_text: str) -> None:
        """Update search suggestions based on input.
        
        Args:
            search_text: Current search text
        """
        # This would typically query a location service for suggestions
        # For now, we'll use a simple implementation
        self.search_suggestions = self._get_location_suggestions(search_text)
    
    def _get_location_suggestions(self, search_text: str) -> List[str]:
        """Get location suggestions for search text.
        
        Args:
            search_text: Search text to get suggestions for
            
        Returns:
            List of location suggestions
        """
        # This is a simplified implementation
        # In a real application, this would query a geocoding service
        common_cities = [
            "New York, NY", "Los Angeles, CA", "Chicago, IL", "Houston, TX",
            "Phoenix, AZ", "Philadelphia, PA", "San Antonio, TX", "San Diego, CA",
            "Dallas, TX", "San Jose, CA", "Austin, TX", "Jacksonville, FL",
            "London, UK", "Paris, France", "Tokyo, Japan", "Sydney, Australia",
            "Toronto, Canada", "Berlin, Germany", "Rome, Italy", "Madrid, Spain"
        ]
        
        search_lower = search_text.lower()
        suggestions = [city for city in common_cities if search_lower in city.lower()]
        
        return suggestions[:5]  # Return top 5 suggestions