"""Configuration Service - Application Settings Management

Handles environment variables, API keys, and application configuration.
Updated to work with the new centralized configuration system.
"""

import os
import logging
from typing import Dict, Any, Optional
from pathlib import Path

from config.app_config import AppConfig, WeatherConfig, UIConfig


class ConfigService:
    """Configuration service for managing application settings."""
    
    def __init__(self, config_file: Optional[str] = None):
        """Initialize the configuration service.
        
        Args:
            config_file: Optional path to configuration file
        """
        self.logger = logging.getLogger(__name__)
        self._config = AppConfig(config_file)
        
        # Validate configuration on initialization
        if not self._config.validate():
            self.logger.error("Configuration validation failed")
            raise ValueError("Invalid configuration")
        
        self.logger.info("Configuration service initialized")
    
    @property
    def config(self) -> AppConfig:
        """Get the application configuration.
        
        Returns:
            Application configuration object
        """
        return self._config
    
    @property
    def weather(self) -> WeatherConfig:
        """Get the weather configuration.
        
        Returns:
            WeatherConfig instance
        """
        return self._config.weather
    
    @property
    def ui(self) -> UIConfig:
        """Get the UI configuration.
        
        Returns:
            UIConfig instance
        """
        return self._config.ui
    
    @property
    def app(self) -> AppConfig:
        """Get the app configuration.
        
        Returns:
            AppConfig instance
        """
        return self._config
    
    def get_api_key(self) -> str:
        """Get the OpenWeather API key.
        
        Returns:
            API key string
        """
        return self._config.api.openweather_api_key
    
    def get_api_base_url(self) -> str:
        """Get the OpenWeather API base URL.
        
        Returns:
            API base URL string
        """
        return self._config.api.openweather_base_url
    
    def get_request_timeout(self) -> int:
        """Get the API request timeout.
        
        Returns:
            Timeout in seconds
        """
        return self._config.api.request_timeout
    
    def get_window_config(self) -> Dict[str, Any]:
        """Get window configuration settings.
        
        Returns:
            Dictionary with window configuration
        """
        return {
            'title': self._config.ui.window_title,
            'width': self._config.ui.window_width,
            'height': self._config.ui.window_height,
            'min_width': self._config.ui.min_width,
            'min_height': self._config.ui.min_height
        }
    
    def get_ui_colors(self) -> Dict[str, str]:
        """Get UI color configuration.
        
        Returns:
            Dictionary with color settings
        """
        return {
            'primary': self._config.ui.primary_color,
            'secondary': self._config.ui.secondary_color,
            'background': self._config.ui.background_color,
            'text': self._config.ui.text_color,
            'accent': self._config.ui.accent_color
        }
    
    def get_data_directory(self) -> Path:
        """Get the data directory path.
        
        Returns:
            Path to data directory
        """
        return Path(self._config.data.data_directory)
    
    def get_favorites_file_path(self) -> Path:
        """Get the favorites file path.
        
        Returns:
            Path to favorites file
        """
        return self._config.get_data_path(self._config.data.favorites_file)
    
    def get_recent_searches_file_path(self) -> Path:
        """Get the recent searches file path.
        
        Returns:
            Path to recent searches file
        """
        return self._config.get_data_path(self._config.data.recent_searches_file)
    
    def get_weather_units(self) -> str:
        """Get the default weather units.
        
        Returns:
            Units string (metric, imperial, kelvin)
        """
        return self._config.weather.default_units
    
    def is_debug_mode(self) -> bool:
        """Check if debug mode is enabled.
        
        Returns:
            True if debug mode is enabled, False otherwise
        """
        return self._config.logging.log_level.upper() == "DEBUG"
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value with fallback to default.
        
        Args:
            key: Configuration key to retrieve
            default: Default value if key not found
            
        Returns:
            Configuration value or default
        """
        # Handle special cases for enhanced features
        if key == 'use_enhanced_features':
            return True  # Enable enhanced features by default
        
        # Try to get from nested configuration objects
        try:
            # Check if it's a nested key (e.g., 'api.timeout')
            if '.' in key:
                parts = key.split('.')
                obj = self._config
                for part in parts:
                    obj = getattr(obj, part)
                return obj
            else:
                # Check top-level config attributes
                if hasattr(self._config, key):
                    return getattr(self._config, key)
        except (AttributeError, TypeError):
            pass
        
        return default