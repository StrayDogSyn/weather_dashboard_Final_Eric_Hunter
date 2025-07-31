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
        import uuid
        self.instance_id = str(uuid.uuid4())[:8]
        self.logger = logging.getLogger(__name__)
        self._config = AppConfig(config_file)
        
        # Debug: Check API keys in ConfigService
        print(f"Debug - ConfigService init [{self.instance_id}]: Gemini API key: {'[SET]' if self._config.api.gemini_api_key and self._config.api.gemini_api_key.strip() else '[EMPTY]'}")
        print(f"Debug - ConfigService init [{self.instance_id}]: OpenAI API key: {'[SET]' if self._config.api.openai_api_key and self._config.api.openai_api_key.strip() else '[EMPTY]'}")
        print(f"Debug - ConfigService init [{self.instance_id}]: OpenWeather API key: {'[SET]' if self._config.api.openweather_api_key and self._config.api.openweather_api_key.strip() else '[EMPTY]'}")
        
        # Validate configuration on initialization
        if not self._config.validate():
            self.logger.error("Configuration validation failed")
            raise ValueError("Invalid configuration")
        
        self.logger.info(f"Configuration service initialized [{self.instance_id}]")
    
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
    
    def get_api_key_by_name(self, key: str) -> Optional[str]:
        """Get API key configuration value by key.
        
        Args:
            key: Configuration key
            
        Returns:
            Configuration value or None if not found
        """
        try:
            print(f"Debug - ConfigService[{self.instance_id}].get_api_key_by_name() called with key: '{key}'")
            print(f"Debug - ConfigService[{self.instance_id}].get_api_key_by_name() - _config exists: {hasattr(self, '_config')}")
            print(f"Debug - ConfigService[{self.instance_id}].get_api_key_by_name() - _config.api exists: {hasattr(self._config, 'api') if hasattr(self, '_config') else 'NO_CONFIG'}")
            
            if key == 'gemini_api_key':
                value = self._config.api.gemini_api_key
                print(f"Debug - ConfigService[{self.instance_id}].get_api_key_by_name('{key}'): {'[SET]' if value else '[EMPTY]'}")
                return value
            elif key == 'openai_api_key':
                value = self._config.api.openai_api_key
                print(f"Debug - ConfigService[{self.instance_id}].get_api_key_by_name('{key}'): {'[SET]' if value else '[EMPTY]'}")
                return value
            elif key == 'openweather_api_key':
                value = self._config.api.openweather_api_key
                print(f"Debug - ConfigService.get_api_key_by_name('{key}'): {'[SET]' if value else '[EMPTY]'}")
                return value
            elif key == 'google_maps_api_key':
                value = self._config.api.google_maps_api_key
                print(f"Debug - ConfigService[{self.instance_id}].get_api_key_by_name('{key}'): {'[SET]' if value else '[EMPTY]'}")
                return value
            else:
                print(f"Debug - ConfigService[{self.instance_id}].get_api_key_by_name() - Unknown key: '{key}'")
                return None
        except Exception as e:
            print(f"Debug - ConfigService[{self.instance_id}].get_api_key_by_name() - EXCEPTION: {e}")
            import traceback
            traceback.print_exc()
            return None
    
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
        print(f"Debug - ConfigService[{self.instance_id}].get() called with key: '{key}', default: {default}")
        
        # Handle API keys specifically
        if key == 'gemini_api_key':
            value = self._config.api.gemini_api_key
            print(f"Debug - ConfigService[{self.instance_id}].get('{key}'): {'[SET]' if value else '[EMPTY]'} (value: {repr(value)})")
            return value if value else default
        elif key == 'openai_api_key':
            value = self._config.api.openai_api_key
            print(f"Debug - ConfigService[{self.instance_id}].get('{key}'): {'[SET]' if value else '[EMPTY]'} (value: {repr(value)})")
            return value if value else default
        elif key == 'openweather_api_key':
            value = self._config.api.openweather_api_key
            print(f"Debug - ConfigService[{self.instance_id}].get('{key}'): {'[SET]' if value else '[EMPTY]'} (value: {repr(value)})")
            return value if value else default
        elif key == 'google_maps_api_key':
            value = self._config.api.google_maps_api_key
            print(f"Debug - ConfigService[{self.instance_id}].get('{key}'): {'[SET]' if value else '[EMPTY]'} (value: {repr(value)})")
            return value if value else default
        
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
        
        print(f"Debug - ConfigService[{self.instance_id}].get('{key}') - returning default: {default}")
        return default
    
    def update_api_key(self, key_name: str, key_value: str) -> bool:
        """Update an API key in the configuration.
        
        Args:
            key_name: Name of the API key (e.g., 'openweather_api_key')
            key_value: New API key value
            
        Returns:
            True if update was successful, False otherwise
        """
        try:
            if hasattr(self._config.api, key_name):
                setattr(self._config.api, key_name, key_value)
                self.logger.info(f"Updated API key: {key_name}")
                return True
            else:
                self.logger.warning(f"Unknown API key: {key_name}")
                return False
        except Exception as e:
            self.logger.error(f"Failed to update API key {key_name}: {e}")
            return False
    
    def get_all_api_keys(self) -> Dict[str, str]:
        """Get all configured API keys.
        
        Returns:
            Dictionary of API key names and values
        """
        return {
            'openweather_api_key': self._config.api.openweather_api_key or '',
            'openweather_backup_api_key': self._config.api.openweather_backup_api_key or '',
            'weatherapi_api_key': self._config.api.weatherapi_api_key or '',
            'gemini_api_key': self._config.api.gemini_api_key or '',
            'openai_api_key': self._config.api.openai_api_key or '',
            'google_maps_api_key': self._config.api.google_maps_api_key or ''
            # Spotify configuration removed
        }
    
    def reload_config(self) -> bool:
        """Reload configuration from environment variables.
        
        Returns:
            True if reload was successful, False otherwise
        """
        try:
            # Reinitialize the config to pick up new environment variables
            self._config = AppConfig()
            self.logger.info("Configuration reloaded successfully")
            return True
        except Exception as e:
            self.logger.error(f"Failed to reload configuration: {e}")
            return False