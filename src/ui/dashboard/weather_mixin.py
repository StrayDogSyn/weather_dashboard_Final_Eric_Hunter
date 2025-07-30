"""Weather Operations Mixin

Handles weather data fetching, processing, and display updates.
"""

import threading
from typing import Optional
from datetime import datetime

from .base_dashboard import BaseDashboard
from services.weather_service import WeatherData


class WeatherMixin(BaseDashboard):
    """Mixin for weather operations and data management."""
    
    def __init__(self):
        """Initialize weather operations."""
        super().__init__()
        
        # Weather state
        self._weather_thread: Optional[threading.Thread] = None
        self._last_weather_update: Optional[datetime] = None
    
    def _load_initial_weather(self):
        """Load initial weather data on startup."""
        self._log_method_call("_load_initial_weather")
        
        try:
            # Check if config has a default location
            if self.config:
                default_location = self.config.get('default_location', 'New York')
                
                if default_location:
                    self._update_status(f"Loading weather for {default_location}...", self.STATUS_INFO)
                    self._fetch_weather(default_location)
                    return
            
            # No default location, show placeholder
            self._update_status("Enter a city name to get weather information", self.STATUS_INFO)
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"Initial weather load failed: {e}")
            self._update_status("Ready to search for weather", self.STATUS_INFO)
    
    def _fetch_weather(self, location: str):
        """Fetch weather data for the specified location."""
        self._log_method_call("_fetch_weather", location)
        
        if self.is_loading:
            self._update_status("Please wait for current request to complete", self.STATUS_WARNING)
            return
        
        if not location or not location.strip():
            self._update_status("Please enter a valid location", self.STATUS_WARNING)
            return
        
        location = location.strip()
        
        # Validate location
        if not self._validate_city_name(location):
            self._update_status("Location name must be at least 2 characters", self.STATUS_WARNING)
            return
        
        try:
            # Show loading state
            self._show_loading(f"Getting weather for {location}...")
            
            # Start weather fetch in background thread
            self._weather_thread = threading.Thread(
                target=self._fetch_weather_thread,
                args=(location,),
                daemon=True
            )
            self._weather_thread.start()
            
        except Exception as e:
            self._hide_loading()
            error_msg = self._truncate_error_message(str(e))
            self._update_status(f"Failed to start weather request: {error_msg}", self.STATUS_ERROR)
            if self.logger:
                self.logger.error(f"Weather fetch start error: {e}")
    
    def _fetch_weather_thread(self, location: str):
        """Fetch weather data in background thread."""
        try:
            if not self.weather_service:
                raise Exception("Weather service not available")
            
            # Fetch weather data
            weather_data = self.weather_service.get_weather(location)
            
            if weather_data:
                # Update UI on main thread
                self.after(0, lambda: self._on_weather_success(weather_data, location))
            else:
                self.after(0, lambda: self._on_weather_error("No weather data received", location))
                
        except Exception as e:
            error_msg = str(e)
            self.after(0, lambda: self._on_weather_error(error_msg, location))
    
    def _on_weather_success(self, weather_data: WeatherData, location: str):
        """Handle successful weather data retrieval."""
        self._log_method_call("_on_weather_success", location)
        
        try:
            # Hide loading state
            self._hide_loading()
            
            # Store weather data
            self.current_weather = weather_data
            self.current_location = location
            self._last_weather_update = datetime.now()
            
            # Update weather display
            if self.weather_display:
                self.weather_display.update_weather(weather_data)
            
            # Update status
            self._update_status(f"Weather updated for {location}", self.STATUS_SUCCESS)
            
            # Update last update timestamp
            self._update_last_update()
            
            # Log success
            if self.logger:
                temp = getattr(weather_data, 'temperature', 'N/A')
                condition = getattr(weather_data, 'condition', 'N/A')
                self.logger.info(f"🌤️ Weather loaded: {location} - {temp}°, {condition}")
                
        except Exception as e:
            if self.logger:
                self.logger.error(f"Weather success handler error: {e}")
            self._update_status("Weather data received but display failed", self.STATUS_ERROR)
    
    def _on_weather_error(self, error_message: str, location: str):
        """Handle weather data retrieval error."""
        self._log_method_call("_on_weather_error", error_message, location)
        
        try:
            # Hide loading state
            self._hide_loading()
            
            # Truncate error message for display
            display_error = self._truncate_error_message(error_message)
            
            # Update status with error
            self._update_status(f"Failed to get weather for {location}: {display_error}", self.STATUS_ERROR)
            
            # Log full error
            if self.logger:
                self.logger.error(f"❌ Weather fetch failed for {location}: {error_message}")
            
            # Clear weather display if this was the current location
            if self.current_location == location and self.weather_display:
                self.weather_display.show_error(f"Unable to load weather for {location}")
                
        except Exception as e:
            if self.logger:
                self.logger.error(f"Weather error handler error: {e}")
    
    def _refresh_weather(self):
        """Refresh weather data for current location."""
        self._log_method_call("_refresh_weather")
        
        if not self.current_location:
            self._update_status("No location to refresh", self.STATUS_WARNING)
            return
        
        if self.is_loading:
            self._update_status("Please wait for current request to complete", self.STATUS_WARNING)
            return
        
        # Refresh weather for current location
        self._update_status(f"Refreshing weather for {self.current_location}...", self.STATUS_INFO)
        self._fetch_weather(self.current_location)
    
    def _update_weather_display(self, weather_data: WeatherData):
        """Update the weather display with new data."""
        self._log_method_call("_update_weather_display")
        
        try:
            if not self.weather_display:
                if self.logger:
                    self.logger.error("Weather display not available")
                return
            
            # Update the display
            self.weather_display.update_weather(weather_data)
            
            # Update last update time
            self._update_last_update()
            
            if self.logger:
                self.logger.info("Weather display updated successfully")
                
        except Exception as e:
            if self.logger:
                self.logger.error(f"Weather display update failed: {e}")
            self._update_status("Failed to update weather display", self.STATUS_ERROR)
    
    def _get_weather_summary(self) -> str:
        """Get a summary of current weather data."""
        try:
            if not self.current_weather:
                return "No weather data available"
            
            location = self.current_location or "Unknown location"
            temp = getattr(self.current_weather, 'temperature', 'N/A')
            condition = getattr(self.current_weather, 'condition', 'N/A')
            
            return f"{location}: {temp}° - {condition}"
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"Weather summary generation failed: {e}")
            return "Weather summary unavailable"
    
    def _is_weather_data_stale(self, max_age_minutes: int = 30) -> bool:
        """Check if current weather data is stale."""
        try:
            if not self._last_weather_update:
                return True
            
            from datetime import timedelta
            max_age = timedelta(minutes=max_age_minutes)
            age = datetime.now() - self._last_weather_update
            
            return age > max_age
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"Weather staleness check failed: {e}")
            return True
    
    def _get_weather_age_string(self) -> str:
        """Get a human-readable string for weather data age."""
        try:
            if not self._last_weather_update:
                return "Never updated"
            
            age = datetime.now() - self._last_weather_update
            
            if age.total_seconds() < 60:
                return "Just now"
            elif age.total_seconds() < 3600:
                minutes = int(age.total_seconds() / 60)
                return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
            else:
                hours = int(age.total_seconds() / 3600)
                return f"{hours} hour{'s' if hours != 1 else ''} ago"
                
        except Exception as e:
            if self.logger:
                self.logger.error(f"Weather age calculation failed: {e}")
            return "Unknown age"