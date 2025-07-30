"""Base Dashboard Module

Shared utilities, constants, and base functionality for the weather dashboard.
"""

import customtkinter as ctk
import logging
from typing import Optional, Dict, Any
from datetime import datetime

from services.config_service import ConfigService
from services.weather_service import WeatherService, WeatherData
from services.logging_service import LoggingService
from services.window_manager import WindowStateManager

# Enhanced features availability check
try:
    from ui.components.enhanced_search_bar import EnhancedSearchBarFrame
    from services.enhanced_weather_service import EnhancedWeatherService
    ENHANCED_FEATURES_AVAILABLE = True
except ImportError:
    ENHANCED_FEATURES_AVAILABLE = False


class BaseDashboard:
    """Base class with shared dashboard functionality and constants."""
    
    # Dashboard constants
    MIN_WINDOW_WIDTH = 1200
    MIN_WINDOW_HEIGHT = 800
    DEFAULT_WINDOW_TITLE = "JTC Capstone Application"
    
    # Status types
    STATUS_INFO = "info"
    STATUS_SUCCESS = "success"
    STATUS_WARNING = "warning"
    STATUS_ERROR = "error"
    
    # Status colors
    STATUS_COLORS = {
        STATUS_INFO: "gray70",
        STATUS_SUCCESS: "#00FF88",
        STATUS_WARNING: "orange",
        STATUS_ERROR: "red"
    }
    
    def __init__(self):
        """Initialize base dashboard functionality."""
        # State variables
        self.current_weather: Optional[WeatherData] = None
        self.current_location: Optional[str] = None
        self.is_loading = False
        self._resizing = False
        self._last_known_text = ""
        
        # Services will be initialized by child classes
        self.config: Optional[ConfigService] = None
        self.weather_service: Optional[WeatherService] = None
        self.logger: Optional[logging.Logger] = None
        self.window_manager: Optional[WindowStateManager] = None
        
        # Enhanced features flag
        self.use_enhanced_features = False
    
    def _get_status_color(self, status_type: str) -> str:
        """Get color for status type."""
        return self.STATUS_COLORS.get(status_type, self.STATUS_COLORS[self.STATUS_INFO])
    
    def _format_timestamp(self) -> str:
        """Format current timestamp for display."""
        return datetime.now().strftime("%I:%M %p")
    
    def _validate_city_name(self, city: str) -> bool:
        """Validate city name for search."""
        if not city or not city.strip():
            return False
        return len(city.strip()) >= 2
    
    def _truncate_error_message(self, message: str, max_length: int = 50) -> str:
        """Truncate error message for display."""
        if len(message) <= max_length:
            return message
        return f"{message[:max_length]}..."
    
    def _log_method_call(self, method_name: str, *args, **kwargs):
        """Log method calls for debugging."""
        if self.logger:
            args_str = ", ".join(str(arg) for arg in args)
            kwargs_str = ", ".join(f"{k}={v}" for k, v in kwargs.items())
            params = ", ".join(filter(None, [args_str, kwargs_str]))
            self.logger.debug(f"🔧 {method_name}({params})")