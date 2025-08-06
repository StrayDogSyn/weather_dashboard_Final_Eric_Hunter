from typing import Optional, Dict, Any, List, Callable
import logging
import threading
import customtkinter as ctk
from src.utils.error_wrapper import ensure_main_thread

# Import enhanced static maps component
try:
    from ..components.enhanced_static_maps import EnhancedStaticMapsComponent
    ENHANCED_MAPS_AVAILABLE = True
except ImportError as e:
    logging.getLogger(__name__).warning(f"Enhanced static maps not available: {e}")
    ENHANCED_MAPS_AVAILABLE = False
    # Fallback to basic static maps
    try:
        from ..components.static_maps_component import StaticMapsComponent
        STATIC_MAPS_AVAILABLE = True
    except ImportError as e2:
        logging.getLogger(__name__).warning(f"Static maps not available: {e2}")
        STATIC_MAPS_AVAILABLE = False

class ThreadSafeMapsTabManager:
    """Simple maps tab manager using static Google Maps."""
    
    def __init__(self, parent, weather_service, config_service):
        self.parent = parent
        self.weather_service = weather_service
        self.config_service = config_service
        self.logger = logging.getLogger(__name__)
        
        # Maps component
        self.maps_component = None
        self.map_widget = None
        self._shutdown_event = threading.Event()
        
        # Public access to shutdown event for external cleanup
        self.shutdown_event = self._shutdown_event
        
        # Initialize UI
        self._setup_ui()
        
        # Connect weather controls to map updates if available
        if hasattr(self, 'weather_controls') and hasattr(self.weather_controls, 'set_update_callback'):
            self.weather_controls.set_update_callback(self._handle_location_update)
        
    def _setup_ui(self):
        """Setup the maps interface using static Google Maps."""
        # Create main container
        self.main_frame = ctk.CTkFrame(
            self.parent,
            fg_color=("#F8F9FA", "#1A1A1A"),
            corner_radius=0
        )
        self.main_frame.pack(fill="both", expand=True)
        
        # Create title
        self.map_title = ctk.CTkLabel(
            self.main_frame,
            text="Weather Map",
            font=("Arial", 18, "bold")
        )
        self.map_title.pack(pady=10)
        
        # Create main content area
        self.main_content = ctk.CTkFrame(self.main_frame)
        self.main_content.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Create status label
        self.status_label = ctk.CTkLabel(
            self.main_frame,
            text="Loading map...",
            font=("Arial", 12)
        )
        self.status_label.pack(pady=5)
        
        # Initialize maps interface
        self._create_maps_interface()
    
    def _create_maps_interface(self):
        """Create the maps interface using static maps API"""
        try:
            # Clear any existing content
            for widget in self.main_content.winfo_children():
                widget.destroy()
            
            # Try to use the enhanced static maps component first
            try:
                if ENHANCED_MAPS_AVAILABLE:
                    from ..components.enhanced_static_maps import EnhancedStaticMapsComponent
                    
                    self.logger.info("Creating enhanced static maps interface...")
                    
                    # Create enhanced static maps widget
                    self.map_widget = EnhancedStaticMapsComponent(
                        self.main_content,
                        weather_service=self.weather_service,
                        config=self.config_service
                    )
                    self.map_widget.pack(fill="both", expand=True)
                    
                    # Update map title for enhanced version
                    self.map_title.configure(text="Enhanced Weather Map")
                    
                elif STATIC_MAPS_AVAILABLE:
                    from ..components.static_maps_component import StaticMapsComponent
                    
                    self.logger.info("Creating static maps interface...")
                    
                    # Create static maps widget
                    self.map_widget = StaticMapsComponent(
                        self.main_content,
                        weather_service=self.weather_service,
                        config=self.config_service
                    )
                    self.map_widget.pack(fill="both", expand=True)
                    
                    # Update map title for basic version
                    self.map_title.configure(text="Codefront - Google Navigation Mode")
                    
                else:
                    raise ImportError("No maps components available")
                
                # Connect to weather service if available
                if self.weather_service:
                    # Update with current weather
                    try:
                        current_weather = self.weather_service.get_current_weather()
                        if current_weather:
                            self.map_widget.update_weather_data(current_weather)
                    except Exception as e:
                        self.logger.warning(f"Could not get initial weather data: {e}")
                    
                    # Connect for future updates
                    if hasattr(self.weather_service, 'add_observer'):
                        self.weather_service.add_observer(self._on_weather_update)
                
                # Update map title
                self.map_title.configure(text="Codefront - Google Navigation Mode")
                
                # Update status
                self._update_status("Map loaded successfully", "normal")
                self.logger.info("Static maps interface created successfully")
                
                return True
                
            except ImportError as e:
                self.logger.warning(f"Static maps component not available: {e}")
                # Fall through to other options
            
            # If static maps fail, try weather visualization
            try:
                from ..components.weather_visualization_panel import WeatherVisualizationPanel
                
                self.logger.info("Using weather visualization fallback...")
                
                self.map_widget = WeatherVisualizationPanel(
                    self.main_content,
                    weather_service=self.weather_service,
                    config=self.config_service
                )
                self.map_widget.pack(fill="both", expand=True)
                
                # Update titles for visualization
                self.map_title.configure(text="Weather Radar Visualization")
                self._update_status("Weather visualization active", "normal")
                
                return True
                
            except ImportError as e:
                self.logger.warning(f"Weather visualization not available: {e}")
            
            # Final fallback - static message
            self._create_static_fallback()
            return False
            
        except Exception as e:
            self.logger.error(f"Failed to create maps interface: {e}")
            self._create_static_fallback()
            return False
    
    def _create_static_fallback(self):
        """Create static fallback when no maps are available"""
        fallback_label = ctk.CTkLabel(
            self.main_content,
            text="Maps functionality is currently unavailable.\nPlease check your Google Maps API key configuration.",
            font=("Arial", 16),
            text_color=("#666666", "#CCCCCC")
        )
        fallback_label.pack(expand=True)
        self._update_status("Maps unavailable", "error")
    
    def _update_status(self, message, status_type="normal", duration=None):
        """Update status message"""
        try:
            if hasattr(self, 'status_label'):
                color_map = {
                    "normal": ("#2E7D32", "#4CAF50"),
                    "error": ("#C62828", "#F44336"),
                    "warning": ("#F57C00", "#FF9800")
                }
                colors = color_map.get(status_type, color_map["normal"])
                self.status_label.configure(text=message, text_color=colors)
                
                if duration:
                    self.after(duration, lambda: self._update_status("Ready", "normal"))
        except Exception as e:
            self.logger.error(f"Failed to update status: {e}")
    
    @ensure_main_thread
    def _on_weather_update(self, weather_data):
        """Handle weather data updates"""
        try:
            if hasattr(self, 'map_widget') and hasattr(self.map_widget, 'update_weather_data'):
                # Use safe UI update
                def _update():
                    self.map_widget.update_weather_data(weather_data)
                
                if hasattr(self.parent, 'safe_after_idle'):
                    self.parent.safe_after_idle(_update)
                elif hasattr(self.parent, 'after_idle'):
                    self.parent.after_idle(_update)
                else:
                    # Direct call if no after_idle available
                    _update()
                    
        except Exception as e:
            self.logger.error(f"Failed to update map weather: {e}")
    
    def _handle_location_update(self, location_data):
        """Handle location updates from weather controls"""
        try:
            if hasattr(self, 'map_widget'):
                lat = location_data.get('lat')
                lon = location_data.get('lon')
                name = location_data.get('name', '')
                
                if lat and lon:
                    # Use safe UI update
                    def _update():
                        self.map_widget.update_location(lat, lon, name)
                    
                    if hasattr(self.parent, 'safe_after_idle'):
                        self.parent.safe_after_idle(_update)
                    elif hasattr(self.parent, 'after_idle'):
                        self.parent.after_idle(_update)
                    else:
                        # Direct call if no after_idle available
                        _update()
                        
        except Exception as e:
            self.logger.error(f"Failed to update map location: {e}")
    
    def refresh_map(self):
        """Public method to refresh the map"""
        try:
            if hasattr(self, 'map_widget'):
                if hasattr(self.map_widget, '_update_map'):
                    # Static maps component
                    self.map_widget._update_map()
                elif hasattr(self.map_widget, 'refresh'):
                    # Other map types
                    self.map_widget.refresh()
                    
                self._update_status("Map refreshed", "normal", duration=2000)
                
        except Exception as e:
            self.logger.error(f"Failed to refresh map: {e}")
            self._update_status(f"Refresh failed: {str(e)}", "error")
    
    def get_current_location(self):
        """Get the current location from the maps component."""
        if self.map_widget and hasattr(self.map_widget, 'get_current_location'):
            return self.map_widget.get_current_location()
        elif self.maps_component and hasattr(self.maps_component, 'get_current_location'):
            return self.maps_component.get_current_location()
        return None
    
    def set_location(self, latitude, longitude, zoom=None):
        """Set the location on the maps component."""
        if self.map_widget and hasattr(self.map_widget, 'update_location'):
            self.map_widget.update_location(latitude, longitude)
        elif self.maps_component and hasattr(self.maps_component, 'set_location'):
            self.maps_component.set_location(latitude, longitude, zoom)
    
    def search_location(self, query):
        """Search for a location using the maps component."""
        if self.map_widget and hasattr(self.map_widget, '_search_location'):
            self.map_widget._search_location(query)
        elif self.maps_component and hasattr(self.maps_component, 'search_location'):
            self.maps_component.search_location(query)

    def cleanup(self):
        """Clean up resources when the tab is closed."""
        try:
            # Signal shutdown
            self._shutdown_event.set()
            
            # Clean up map widget
            if self.map_widget:
                if hasattr(self.map_widget, 'cleanup'):
                    self.map_widget.cleanup()
                self.map_widget = None
            
            # Clean up maps component (legacy)
            if self.maps_component:
                if hasattr(self.maps_component, 'cleanup'):
                    self.maps_component.cleanup()
                self.maps_component = None
            
            self.logger.info("Maps tab manager cleaned up successfully")
            
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")