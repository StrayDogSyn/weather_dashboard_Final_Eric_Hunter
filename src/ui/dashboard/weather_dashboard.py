"""Weather Dashboard - Main Application Window

Refactored modular weather dashboard using mixin architecture.
This file serves as the main coordinator, inheriting functionality from focused mixins.
"""

import customtkinter as ctk
import logging
from typing import Optional

# Import all mixin classes
from .base_dashboard import BaseDashboard
from .window_mixin import WindowMixin
from .layout_mixin import LayoutMixin
from .event_mixin import EventMixin
from .search_mixin import SearchMixin
from .weather_mixin import WeatherMixin
from .status_mixin import StatusMixin

# Import services
from services.config_service import ConfigService
from services.weather_service import WeatherService
from services.logging_service import LoggingService

# Enhanced features check
try:
    from enhanced_weather_service import EnhancedWeatherService
    ENHANCED_WEATHER_AVAILABLE = True
except ImportError:
    ENHANCED_WEATHER_AVAILABLE = False


class WeatherDashboard(WindowMixin, LayoutMixin, EventMixin, 
                      SearchMixin, WeatherMixin, StatusMixin, 
                      ctk.CTk):
    """Main Weather Dashboard Application.
    
    Combines all dashboard functionality through multiple inheritance.
    Each mixin provides focused, single-responsibility functionality:
    
    - WindowMixin: Window management and configuration
    - LayoutMixin: UI layout and component creation
    - EventMixin: Event handling and user interactions
    - SearchMixin: Search functionality and location detection
    - WeatherMixin: Weather data operations
    - StatusMixin: Status updates and loading states
    """
    
    def __init__(self):
        """Initialize the Weather Dashboard application."""
        # Initialize all parent classes
        ctk.CTk.__init__(self)
        WindowMixin.__init__(self)
        LayoutMixin.__init__(self)
        EventMixin.__init__(self)
        SearchMixin.__init__(self)
        WeatherMixin.__init__(self)
        StatusMixin.__init__(self)
        
        # Initialize services
        self._initialize_services()
        
        # Setup the application
        self._setup_application()
    
    def _initialize_services(self):
        """Initialize all required services."""
        try:
            # Initialize configuration service
            self.config = ConfigService()
            
            # Initialize logging service
            logging_service = LoggingService(self.config)
            self.logger = logging_service.get_logger("WeatherDashboard")
            
            # Check for enhanced features
            self.use_enhanced_features = (
                ENHANCED_WEATHER_AVAILABLE and 
                self.config.get('use_enhanced_features', False)
            )
            
            # Initialize weather service
            if self.use_enhanced_features:
                self.weather_service = EnhancedWeatherService(self.config)
                self.logger.info("✨ Enhanced weather service initialized")
            else:
                self.weather_service = WeatherService(self.config)
                self.logger.info("🌤️ Standard weather service initialized")
            
            self.logger.info("🚀 Weather Dashboard services initialized")
            
        except Exception as e:
            print(f"Service initialization failed: {e}")
            # Create minimal fallback logger
            self.logger = logging.getLogger("WeatherDashboard")
            raise
    
    def _setup_application(self):
        """Set up the complete application."""
        try:
            # Setup window
            self._setup_window()
            
            # Setup UI layout
            self._setup_ui()
            
            # Setup status bar
            self._setup_status_bar()
            
            # Setup event bindings
            self._setup_bindings()
            
            # Load initial weather
            self._load_initial_weather()
            
            self.logger.info("🎯 Weather Dashboard setup complete")
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"Application setup failed: {e}")
            raise
    
    def run(self):
        """Start the application main loop."""
        try:
            if self.logger:
                self.logger.info("🟢 Starting Weather Dashboard...")
            
            # Start the main event loop
            self.mainloop()
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"Application runtime error: {e}")
            raise
        finally:
            if self.logger:
                self.logger.info("🔴 Weather Dashboard stopped")


# Convenience function for backward compatibility
def create_weather_dashboard() -> WeatherDashboard:
    """Create and return a new WeatherDashboard instance."""
    return WeatherDashboard()


if __name__ == "__main__":
    # Direct execution for testing
    app = create_weather_dashboard()
    app.run()