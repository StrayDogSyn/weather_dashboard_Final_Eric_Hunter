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
        """Perform the actual weather update with enhanced status feedback - Fixed threading."""
        try:
            # Validate current city
            if not hasattr(self, 'current_city') or not self.current_city or self.current_city.strip() == "":
                self.current_city = "London"  # Default fallback
            
            # Update status to loading safely
            if self.winfo_exists():
                self.ui_updater.schedule_update(lambda: self._safe_update_status("Fetching weather data...", "loading"))
            
            # Get current weather data
            weather_data = self._get_current_weather()
            
            if weather_data:
                # Store the data
                self.current_weather_data = weather_data
                
                # Update UI on main thread safely
                if self.winfo_exists():
                    self.ui_updater.schedule_update(lambda: self._update_weather_display(weather_data))
                
                # Update charts if available
                if self.winfo_exists():
                    self.ui_updater.schedule_update(lambda: self._update_charts())
                
                # Update last update time
                self.last_weather_update = datetime.now()
                
                # Update status to success
                if self.winfo_exists():
                    location = weather_data.get('location', self.current_city)
                    self.ui_updater.schedule_update(lambda: self._safe_update_status(f"Weather data updated for {location}", "success"))
                
                # Update connection status
                if self.winfo_exists():
                    self.ui_updater.schedule_update(lambda: self._safe_update_connection_status(True))
                
                self.logger.info("Weather data updated successfully")
            else:
                self.logger.warning("No weather data received")
                if self.winfo_exists():
                    self.ui_updater.schedule_update(lambda: self._safe_update_status("No weather data available", "warning"))
                
        except Exception as e:
            self.logger.error(f"Error performing weather update: {e}")
            error_msg = self._get_user_friendly_error(str(e))
            if self.winfo_exists():
                self.ui_updater.schedule_update(lambda: self._show_error_notification(error_msg))
        finally:
            if self.winfo_exists():
                self.ui_updater.schedule_update(lambda: self.hide_loading_state())
    
    def _on_search(self, event=None) -> None:
        """Handle search entry Enter key press."""
        self._search_weather()
    
    def _search_weather(self) -> None:
        """Search for weather data for the entered city with enhanced feedback."""
        try:
            city = self.search_entry.get().strip()
            if city:
                # Update status
                if hasattr(self, 'update_status'):
                    self.update_status(f"Searching weather for {city}...", "loading")
                
                self.show_loading_state()
                # Update the weather service with new city
                self.weather_service.set_city(city)
                self.current_city = city
                
                # Refresh weather data
                self._perform_weather_update()
            else:
                self.logger.warning("No city entered for search")
                if hasattr(self, 'update_status'):
                    self.update_status("Please enter a city name", "warning")
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
                if isinstance(weather_data, dict):
                    self.logger.warning(f"Weather service returned error: {weather_data.get('error', 'Unknown error')}")
                else:
                    self.logger.warning(f"Weather service returned non-dict data: {weather_data}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error getting current weather: {e}")
            return None
    
    def _safe_update_status(self, message: str, status_type: str = "info") -> None:
        """Safely update status with widget existence check."""
        try:
            if hasattr(self, 'update_status'):
                self.update_status(message, status_type)
        except Exception as e:
            self.logger.warning(f"Error updating status: {e}")
    
    def _safe_update_connection_status(self, connected: bool) -> None:
        """Safely update connection status with widget existence check."""
        try:
            if hasattr(self, 'update_connection_status'):
                self.update_connection_status(connected)
        except Exception as e:
            self.logger.warning(f"Error updating connection status: {e}")
    
    def _get_user_friendly_error(self, error_msg: str) -> str:
        """Convert technical error messages to user-friendly ones."""
        if "connection" in error_msg.lower():
            return "Unable to connect to weather service"
        elif "api" in error_msg.lower():
            return "Weather service temporarily unavailable"
        elif "timeout" in error_msg.lower():
            return "Request timed out, please try again"
        else:
            return f"Error: {error_msg[:50]}..."
    
    def _show_error_notification(self, error_msg: str) -> None:
        """Show error notification safely."""
        try:
            if hasattr(self, 'update_status'):
                self.update_status(error_msg, "error")
            if hasattr(self, 'update_connection_status'):
                self.update_connection_status(False)
        except Exception as e:
            self.logger.warning(f"Error showing error notification: {e}")
    
    def _update_weather_display(self, weather_data: Dict[str, Any]) -> None:
        """Update the weather display with new data - Fixed threading."""
        try:
            # Ensure we're on the main thread
            if not self.winfo_exists():
                return
                
            # Check if weather_data is valid
            if isinstance(weather_data, str):
                self.logger.error(f"Weather data is a string: {weather_data}")
                return
            
            if not isinstance(weather_data, dict):
                self.logger.error(f"Weather data is not a dictionary: {type(weather_data)}")
                return
            
            # Try to update enhanced weather display first
            if hasattr(self, 'enhanced_weather_display') and self.enhanced_weather_display:
                if hasattr(self.enhanced_weather_display, 'winfo_exists') and self.enhanced_weather_display.winfo_exists():
                    self.enhanced_weather_display.update_weather_data(weather_data)
                    self.logger.debug("Updated enhanced weather display")
            else:
                # Fallback to basic weather display
                self._update_basic_weather_display(weather_data)
            
            # Update location if different
            if 'location' in weather_data:
                location = weather_data['location']
                if location and location != self.current_city:
                    self.current_city = location
                    if hasattr(self, 'location_label') and self.location_label.winfo_exists():
                        self.location_label.configure(text=f"📍 {location}")
            
            # Store weather data for other components
            self.current_weather_data = weather_data
            
            # Update all dashboard components with new weather data
            self._update_all_dashboard_components(weather_data)
            
        except Exception as e:
            self.logger.error(f"Error updating weather display: {e}")
    
    def _update_basic_weather_display(self, weather_data: Dict[str, Any]) -> None:
        """Update basic weather display as fallback - Fixed threading."""
        try:
            # Update temperature
            if 'temperature' in weather_data and hasattr(self, 'temp_label') and self.temp_label.winfo_exists():
                temp = weather_data['temperature']
                if isinstance(temp, (int, float)):
                    self.temp_label.configure(text=f"{temp:.1f}°C")
            
            # Update condition
            if 'condition' in weather_data and hasattr(self, 'condition_label') and self.condition_label.winfo_exists():
                condition = weather_data['condition']
                if self.display_enhancer:
                    enhanced_condition = self.display_enhancer.enhance_weather_display(condition)
                    self.condition_label.configure(text=enhanced_condition)
                else:
                    self.condition_label.configure(text=str(condition))
            
            # Update feels like temperature
            if 'feels_like' in weather_data and hasattr(self, 'feels_like_label') and self.feels_like_label.winfo_exists():
                feels_like = weather_data['feels_like']
                if isinstance(feels_like, (int, float)):
                    self.feels_like_label.configure(text=f"Feels like: {feels_like:.1f}°C")
            
            # Update humidity
            if 'humidity' in weather_data and hasattr(self, 'humidity_label') and self.humidity_label.winfo_exists():
                humidity = weather_data['humidity']
                if isinstance(humidity, (int, float)):
                    self.humidity_label.configure(text=f"Humidity: {humidity:.0f}%")
            
            # Update wind speed
            if 'wind_speed' in weather_data and hasattr(self, 'wind_label') and self.wind_label.winfo_exists():
                wind_speed = weather_data['wind_speed']
                if isinstance(wind_speed, (int, float)):
                    self.wind_label.configure(text=f"Wind: {wind_speed:.1f} km/h")
            
            # Update pressure
            if 'pressure' in weather_data and hasattr(self, 'pressure_label'):
                pressure = weather_data['pressure']
                if isinstance(pressure, (int, float)):
                    self.pressure_label.configure(text=f"Pressure: {pressure:.0f} hPa")
                    
        except Exception as e:
            self.logger.error(f"Error updating basic weather display: {e}")
    
    def update_weather_display(self, weather_data):
        """Public method to update weather display with comprehensive data."""
        try:
            # Convert weather data to dictionary if needed
            if hasattr(weather_data, '__dict__'):
                data_dict = weather_data.__dict__
            elif hasattr(weather_data, 'to_dict'):
                data_dict = weather_data.to_dict()
            else:
                data_dict = weather_data
            
            # Get additional data if enhanced weather service is available
            if hasattr(self, 'weather_service') and self.weather_service:
                try:
                    # Get coordinates from weather data
                    lat = data_dict.get('coord', {}).get('lat') or data_dict.get('latitude')
                    lon = data_dict.get('coord', {}).get('lon') or data_dict.get('longitude')
                    
                    if lat is not None and lon is not None:
                        # Get air quality data
                        if hasattr(self.weather_service, 'get_air_quality'):
                            air_quality = self.weather_service.get_air_quality(lat, lon)
                            if air_quality:
                                data_dict['air_quality'] = air_quality
                        
                        # Get astronomical data
                        if hasattr(self.weather_service, 'get_astronomical_data'):
                            astronomical = self.weather_service.get_astronomical_data(lat, lon)
                            if astronomical:
                                data_dict['astronomical'] = astronomical
                        
                        # Get weather alerts
                        if hasattr(self.weather_service, 'get_weather_alerts'):
                            alerts = self.weather_service.get_weather_alerts(lat, lon)
                            if alerts:
                                data_dict['alerts'] = alerts
                    else:
                        self.logger.debug("No coordinates available for additional weather data")
                            
                except Exception as e:
                    self.logger.warning(f"Could not get additional weather data: {e}")
            
            # Update the display
            self._update_weather_display(data_dict)
            
            # Update auto-refresh component if available
            if hasattr(self, 'auto_refresh_component') and self.auto_refresh_component:
                self.auto_refresh_component.update_last_refresh()
            
        except Exception as e:
            self.logger.error(f"Error in update_weather_display: {e}")
    
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
    
    def _update_all_dashboard_components(self, weather_data: Dict[str, Any]) -> None:
        """Update all dashboard components with new weather data."""
        try:
            self.logger.debug("Updating all dashboard components with new weather data")
            
            # Update temperature charts
            self._update_temperature_charts_with_data(weather_data)
            
            # Update forecast charts if forecast data is available
            self._update_forecast_charts(weather_data)
            
            # Update analytics components
            self._update_analytics_with_weather_data(weather_data)
            
            # Update activity suggester
            self._update_activity_suggester_with_weather(weather_data)
            
            # Update journal components
            self._update_journal_with_weather_data(weather_data)
            
            # Update any other weather-dependent components
            self._update_weather_dependent_components(weather_data)
            
            self.logger.debug("All dashboard components updated successfully")
            
        except Exception as e:
            self.logger.error(f"Error updating dashboard components: {e}")
    
    def _update_temperature_charts_with_data(self, weather_data: Dict[str, Any]) -> None:
        """Update temperature charts with current weather data."""
        try:
            # Update main temperature chart
            if hasattr(self, 'temperature_chart') and self.temperature_chart:
                # If we have forecast data, use it
                if 'forecast' in weather_data:
                    self.temperature_chart.update_forecast(weather_data['forecast'])
                # Otherwise, add current temperature as a data point
                elif 'temperature' in weather_data:
                    current_temp = weather_data['temperature']
                    if hasattr(self.temperature_chart, 'add_current_temperature'):
                        self.temperature_chart.add_current_temperature(current_temp)
            
            # Update any other chart components
            chart_elements = ['forecast_chart', 'trend_chart', 'analytics_chart']
            for chart_name in chart_elements:
                if hasattr(self, chart_name):
                    chart = getattr(self, chart_name)
                    if hasattr(chart, 'update_weather_data'):
                        chart.update_weather_data(weather_data)
                        
        except Exception as e:
            self.logger.error(f"Error updating temperature charts with data: {e}")
    
    def _update_forecast_charts(self, weather_data: Dict[str, Any]) -> None:
        """Update forecast charts with weather data."""
        try:
            if 'forecast' in weather_data:
                forecast_data = weather_data['forecast']
                
                # Update forecast chart if available
                if hasattr(self, 'forecast_chart') and self.forecast_chart:
                    if hasattr(self.forecast_chart, 'update_forecast'):
                        self.forecast_chart.update_forecast(forecast_data)
                
                # Update any other forecast-dependent components
                forecast_elements = ['hourly_chart', 'daily_chart', 'extended_forecast']
                for element_name in forecast_elements:
                    if hasattr(self, element_name):
                        element = getattr(self, element_name)
                        if hasattr(element, 'update_forecast'):
                            element.update_forecast(forecast_data)
                            
        except Exception as e:
            self.logger.error(f"Error updating forecast charts: {e}")
    
    def _update_analytics_with_weather_data(self, weather_data: Dict[str, Any]) -> None:
        """Update analytics components with weather data."""
        try:
            # Update mood analytics
            if hasattr(self, 'mood_analytics') and self.mood_analytics:
                if hasattr(self.mood_analytics, 'update_weather_context'):
                    self.mood_analytics.update_weather_context(weather_data)
            
            # Update weather analytics
            if hasattr(self, 'weather_analytics') and self.weather_analytics:
                if hasattr(self.weather_analytics, 'add_weather_data'):
                    self.weather_analytics.add_weather_data(weather_data)
            
            # Update trend analytics
            analytics_elements = ['trend_analytics', 'comparison_analytics', 'historical_analytics']
            for analytics_name in analytics_elements:
                if hasattr(self, analytics_name):
                    analytics = getattr(self, analytics_name)
                    if hasattr(analytics, 'update_weather_data'):
                        analytics.update_weather_data(weather_data)
                        
        except Exception as e:
            self.logger.error(f"Error updating analytics with weather data: {e}")
    
    def _update_activity_suggester_with_weather(self, weather_data: Dict[str, Any]) -> None:
        """Update activity suggester with current weather conditions."""
        try:
            if hasattr(self, 'activity_suggester') and self.activity_suggester:
                if hasattr(self.activity_suggester, 'update_weather_conditions'):
                    self.activity_suggester.update_weather_conditions(weather_data)
                elif hasattr(self.activity_suggester, 'refresh_suggestions'):
                    self.activity_suggester.refresh_suggestions()
                    
        except Exception as e:
            self.logger.error(f"Error updating activity suggester with weather: {e}")
    
    def _update_journal_with_weather_data(self, weather_data: Dict[str, Any]) -> None:
        """Update journal components with weather data."""
        try:
            # Update weather journal
            if hasattr(self, 'weather_journal') and self.weather_journal:
                if hasattr(self.weather_journal, 'update_current_weather'):
                    self.weather_journal.update_current_weather(weather_data)
            
            # Update journal manager
            if hasattr(self, 'journal_manager') and self.journal_manager:
                if hasattr(self.journal_manager, 'set_weather_context'):
                    self.journal_manager.set_weather_context(weather_data)
                    
        except Exception as e:
            self.logger.error(f"Error updating journal with weather data: {e}")
    
    def _update_weather_dependent_components(self, weather_data: Dict[str, Any]) -> None:
        """Update any other weather-dependent components."""
        try:
            # Update maps component with weather overlay
            if hasattr(self, 'maps_component') and self.maps_component:
                if hasattr(self.maps_component, 'update_weather_overlay'):
                    self.maps_component.update_weather_overlay(weather_data)
            
            # Update notification system
            if hasattr(self, 'notification_manager') and self.notification_manager:
                if hasattr(self.notification_manager, 'check_weather_alerts'):
                    self.notification_manager.check_weather_alerts(weather_data)
            
            # Update any weather widgets
            widget_elements = ['weather_widget', 'mini_weather', 'status_weather']
            for widget_name in widget_elements:
                if hasattr(self, widget_name):
                    widget = getattr(self, widget_name)
                    if hasattr(widget, 'update_weather'):
                        widget.update_weather(weather_data)
                        
        except Exception as e:
            self.logger.error(f"Error updating weather-dependent components: {e}")