"""Weather Handler Mixin

Contains all weather-related operations and update methods for the dashboard.
"""

import asyncio
from typing import Dict, Any, Optional
from datetime import datetime
from ..theme import DataTerminalTheme


class WeatherHandlerMixin:
    """Mixin class containing weather handling methods."""
    
    def _refresh_weather(self) -> None:
        """Refresh weather data and update display."""
        try:
            self.show_loading_state()
            self._schedule_weather_update()
        except Exception as e:
            self.logger.error(f"Error refreshing weather: {e}")
            self.hide_loading_state()
    
    def _schedule_weather_update(self) -> None:
        """Schedule weather update in a thread-safe manner."""
        try:
            # Cancel any existing update
            if hasattr(self, '_weather_update_id') and self._weather_update_id:
                self.after_cancel(self._weather_update_id)
            
            # Schedule new update
            self._weather_update_id = self.after(100, self._perform_weather_update)
        except Exception as e:
            self.logger.error(f"Error scheduling weather update: {e}")
            self.hide_loading_state()
    
    def _perform_weather_update(self) -> None:
        """Perform the actual weather update."""
        try:
            # Get current weather data
            weather_data = self._get_current_weather()
            
            if weather_data:
                # Update UI with new data
                self._update_weather_display(weather_data)
                
                # Update charts if available
                self._update_charts()
                
                # Update last update time
                self.last_weather_update = datetime.now()
                
                # Puscifer audio update removed
                
                self.logger.info("Weather data updated successfully")
            else:
                self.logger.warning("No weather data received")
                
        except Exception as e:
            self.logger.error(f"Error performing weather update: {e}")
        finally:
            self.hide_loading_state()
    
    def _on_search(self, event=None) -> None:
        """Handle search entry Enter key press."""
        self._search_weather()
    
    def _search_weather(self) -> None:
        """Search for weather data for the entered city."""
        try:
            city = self.search_entry.get().strip()
            if city:
                self.show_loading_state()
                # Update the weather service with new city
                self.weather_service.set_city(city)
                # Refresh weather data
                self._perform_weather_update()
            else:
                self.logger.warning("No city entered for search")
        except Exception as e:
            self.logger.error(f"Error searching weather: {e}")
            self.hide_loading_state()
    
    def _get_current_weather(self) -> Optional[Dict[str, Any]]:
        """Get current weather data from the weather service."""
        try:
            if not self.weather_service:
                self.logger.warning("Weather service not available")
                return None
            
            # Get weather data for current city
            weather_data = self.weather_service.get_current_weather(self.current_city)
            
            if weather_data and 'error' not in weather_data:
                return weather_data
            else:
                self.logger.warning(f"Weather service returned error: {weather_data.get('error', 'Unknown error')}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error getting current weather: {e}")
            return None
    
    def _update_weather_display(self, weather_data: Dict[str, Any]) -> None:
        """Update the weather display with new data."""
        try:
            # Update temperature
            if 'temperature' in weather_data:
                temp = weather_data['temperature']
                if isinstance(temp, (int, float)):
                    self.temp_label.configure(text=f"{temp:.1f}°C")
            
            # Update condition
            if 'condition' in weather_data:
                condition = weather_data['condition']
                if self.display_enhancer:
                    enhanced_condition = self.display_enhancer.enhance_weather_display(condition)
                    self.condition_label.configure(text=enhanced_condition)
                else:
                    self.condition_label.configure(text=str(condition))
            
            # Update feels like temperature
            if 'feels_like' in weather_data:
                feels_like = weather_data['feels_like']
                if isinstance(feels_like, (int, float)):
                    self.feels_like_label.configure(text=f"Feels like: {feels_like:.1f}°C")
            
            # Update humidity
            if 'humidity' in weather_data:
                humidity = weather_data['humidity']
                if isinstance(humidity, (int, float)):
                    self.humidity_label.configure(text=f"Humidity: {humidity:.0f}%")
            
            # Update wind speed
            if 'wind_speed' in weather_data:
                wind_speed = weather_data['wind_speed']
                if isinstance(wind_speed, (int, float)):
                    self.wind_label.configure(text=f"Wind: {wind_speed:.1f} km/h")
            
            # Update pressure
            if 'pressure' in weather_data:
                pressure = weather_data['pressure']
                if isinstance(pressure, (int, float)):
                    self.pressure_label.configure(text=f"Pressure: {pressure:.0f} hPa")
            
            # Update location if different
            if 'location' in weather_data:
                location = weather_data['location']
                if location and location != self.current_city:
                    self.current_city = location
                    self.location_label.configure(text=f"📍 {location}")
            
            # Store weather data for other components
            self.current_weather_data = weather_data
            
        except Exception as e:
            self.logger.error(f"Error updating weather display: {e}")
    
    def _update_charts(self) -> None:
        """Update temperature charts with latest data."""
        try:
            if hasattr(self, 'temperature_chart') and self.temperature_chart:
                # Update chart with current timeframe
                timeframe = getattr(self, 'chart_timeframe', '24h')
                self.temperature_chart.update_timeframe(timeframe)
                
        except Exception as e:
            self.logger.error(f"Error updating charts: {e}")
    
    def _handle_search(self) -> None:
        """Handle city search functionality."""
        try:
            search_term = self.search_entry.get().strip()
            
            if not search_term:
                self.logger.warning("Empty search term")
                return
            
            # Validate city name
            if len(search_term) < 2:
                self.logger.warning("Search term too short")
                return
            
            # Update current city
            old_city = self.current_city
            self.current_city = search_term
            
            # Clear search entry
            self.search_entry.delete(0, 'end')
            
            # Update location display immediately
            self.location_label.configure(text=f"📍 {search_term}")
            
            # Refresh weather for new city
            self._refresh_weather()
            
            self.logger.info(f"City changed from '{old_city}' to '{search_term}'")
            
        except Exception as e:
            self.logger.error(f"Error handling search: {e}")
    
    def _start_auto_refresh(self) -> None:
        """Start automatic weather refresh timer."""
        try:
            # Cancel existing timer
            if hasattr(self, '_auto_refresh_id') and self._auto_refresh_id:
                self.after_cancel(self._auto_refresh_id)
            
            # Schedule next refresh (15 minutes)
            refresh_interval = 15 * 60 * 1000  # 15 minutes in milliseconds
            self._auto_refresh_id = self.after(refresh_interval, self._auto_refresh_callback)
            
            self.logger.debug(f"Auto-refresh scheduled for {refresh_interval/1000/60} minutes")
            
        except Exception as e:
            self.logger.error(f"Error starting auto-refresh: {e}")
    
    def _auto_refresh_callback(self) -> None:
        """Callback for automatic weather refresh."""
        try:
            self.logger.info("Performing automatic weather refresh")
            self._refresh_weather()
            
            # Schedule next refresh
            self._start_auto_refresh()
            
        except Exception as e:
            self.logger.error(f"Error in auto-refresh callback: {e}")
    
    def _stop_auto_refresh(self) -> None:
        """Stop automatic weather refresh timer."""
        try:
            if hasattr(self, '_auto_refresh_id') and self._auto_refresh_id:
                self.after_cancel(self._auto_refresh_id)
                self._auto_refresh_id = None
                self.logger.debug("Auto-refresh timer stopped")
                
        except Exception as e:
            self.logger.error(f"Error stopping auto-refresh: {e}")
    
    def _load_initial_weather_data(self) -> None:
        """Load initial weather data on startup."""
        try:
            self.logger.info("Loading initial weather data")
            
            # Show loading state
            self.show_loading_state()
            
            # Schedule initial weather update
            self._schedule_weather_update()
            
            # Start auto-refresh timer
            self._start_auto_refresh()
            
        except Exception as e:
            self.logger.error(f"Error loading initial weather data: {e}")
            self.hide_loading_state()
    
    def _get_weather_summary(self) -> str:
        """Get a summary of current weather conditions."""
        try:
            if not hasattr(self, 'current_weather_data') or not self.current_weather_data:
                return "Weather data not available"
            
            data = self.current_weather_data
            
            # Build summary string
            summary_parts = []
            
            if 'temperature' in data:
                summary_parts.append(f"{data['temperature']:.1f}°C")
            
            if 'condition' in data:
                summary_parts.append(str(data['condition']))
            
            if 'humidity' in data:
                summary_parts.append(f"{data['humidity']:.0f}% humidity")
            
            if 'wind_speed' in data:
                summary_parts.append(f"{data['wind_speed']:.1f} km/h wind")
            
            return ", ".join(summary_parts) if summary_parts else "Weather data incomplete"
            
        except Exception as e:
            self.logger.error(f"Error getting weather summary: {e}")
            return "Error getting weather summary"
    
    def _cleanup_weather_timers(self) -> None:
        """Clean up weather-related timers."""
        try:
            # Stop auto-refresh
            self._stop_auto_refresh()
            
            # Cancel any pending weather updates
            if hasattr(self, '_weather_update_id') and self._weather_update_id:
                self.after_cancel(self._weather_update_id)
                self._weather_update_id = None
            
            self.logger.debug("Weather timers cleaned up")
            
        except Exception as e:
            self.logger.error(f"Error cleaning up weather timers: {e}")