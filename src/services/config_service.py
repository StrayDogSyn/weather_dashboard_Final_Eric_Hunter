"""Configuration Service - Application Settings Management

Handles environment variables, API keys, and application configuration.
Implements IConfigurationService interface with proper validation.
"""

import logging
from pathlib import Path
from typing import Any, Dict, Optional

from ..config.app_config import AppConfig, UIConfig, WeatherConfig


class ConfigurationError(Exception):
    """Configuration related errors."""


class ConfigService:
    """Configuration service for managing application settings."""

    def __init__(self, config_file: Optional[str] = None):
        """Initialize the configuration service.

        Args:
            config_file: Optional path to configuration file

        Raises:
            ConfigurationError: If configuration is invalid
        """
        self._logger = logging.getLogger(__name__)

        try:
            self._config = AppConfig(config_file)

            # Ensure weather configuration is synced with API configuration
            self._sync_weather_config()

            # Validate configuration on initialization
            if not self.validate_configuration():
                raise ConfigurationError("Configuration validation failed")

            self._logger.info("Configuration service initialized successfully")

        except Exception as e:
            self._logger.error(f"Failed to initialize configuration service: {e}")
            raise ConfigurationError(f"Configuration initialization failed: {e}") from e

    def _sync_weather_config(self) -> None:
        """Synchronize weather configuration with API configuration.

        Ensures that weather.api_key and weather.base_url are always
        in sync with the main API configuration.
        """
        try:
            # Sync API key from main API config to weather config
            if self._config.api.openweather_api_key:
                self._config.weather.api_key = self._config.api.openweather_api_key

            # Sync base URL from main API config to weather config
            if self._config.api.openweather_base_url:
                self._config.weather.base_url = self._config.api.openweather_base_url

            self._logger.debug("Weather configuration synchronized with API configuration")

        except Exception as e:
            self._logger.warning(f"Failed to sync weather configuration: {e}")

    def get_api_key(self, service_name: str) -> Optional[str]:
        """Get API key for a specific service.

        Args:
            service_name: Name of the service (e.g., 'openweather', 'gemini')

        Returns:
            API key or None if not found
        """
        try:
            service_map = {
                "openweather": self._config.api.openweather_api_key,
                "openweather_backup": self._config.api.openweather_backup_api_key,
                "weatherapi": self._config.api.weatherapi_api_key,
                "gemini": self._config.api.gemini_api_key,
                "openai": self._config.api.openai_api_key,
                "google_maps": self._config.api.google_maps_api_key,
            }

            api_key = service_map.get(service_name.lower())
            return api_key if api_key and api_key.strip() else None

        except Exception as e:
            self._logger.error(f"Failed to get API key for {service_name}: {e}")
            return None

    def get_setting(self, key: str, default: Any = None) -> Any:
        """Get a configuration setting.

        Args:
            key: Configuration key (supports dot notation for nested keys)
            default: Default value if key not found

        Returns:
            Configuration value or default
        """
        try:
            # Handle nested keys with dot notation
            if "." in key:
                parts = key.split(".")
                obj = self._config
                for part in parts:
                    if hasattr(obj, part):
                        obj = getattr(obj, part)
                    else:
                        return default
                return obj

            # Handle top-level keys
            if hasattr(self._config, key):
                return getattr(self._config, key)

            # Handle special API key requests
            if key.endswith("_api_key"):
                service_name = key.replace("_api_key", "")
                return self.get_api_key(service_name)

            return default

        except Exception as e:
            self._logger.warning(f"Failed to get setting '{key}': {e}")
            return default

    def get_database_config(self) -> Dict[str, Any]:
        """Get database configuration.

        Returns:
            Database configuration dictionary
        """
        data_dir = self.get_data_directory()
        return {
            "database_path": str(data_dir / "weather_dashboard.db"),
            "connection_pool_size": 10,
            "timeout": 30,
            "journal_mode": "WAL",
            "foreign_keys": True,
        }

    def get_cache_config(self) -> Dict[str, Any]:
        """Get cache configuration.

        Returns:
            Cache configuration dictionary
        """
        return {
            "ttl_seconds": self._config.weather.cache_duration,
            "max_size": self._config.data.max_cache_size,
            "cleanup_interval": 3600,  # 1 hour
        }

    def validate_configuration(self) -> bool:
        """Validate the current configuration.

        Returns:
            True if configuration is valid, False otherwise
        """
        try:
            # Validate required API keys
            required_keys = ["openweather"]
            missing_keys = []

            for key in required_keys:
                if not self.get_api_key(key):
                    missing_keys.append(key)

            if missing_keys:
                self._logger.warning(f"Missing required API keys: {missing_keys}")
                return False

            # Validate data directory
            data_dir = self.get_data_directory()
            if not data_dir.exists():
                try:
                    data_dir.mkdir(parents=True, exist_ok=True)
                except Exception as e:
                    self._logger.error(f"Cannot create data directory {data_dir}: {e}")
                    return False

            # Validate configuration values
            if self._config.api.request_timeout <= 0:
                self._logger.error("Invalid request timeout")
                return False

            if self._config.weather.cache_duration <= 0:
                self._logger.error("Invalid cache duration")
                return False

            return True

        except Exception as e:
            self._logger.error(f"Configuration validation error: {e}")
            return False

    def get_data_directory(self) -> Path:
        """Get the data directory path.

        Returns:
            Path to data directory
        """
        return Path(self._config.data.data_directory).resolve()

    # Configuration property accessors
    @property
    def weather(self) -> WeatherConfig:
        """Get the weather configuration.

        Returns:
            WeatherConfig: The weather configuration object
        """
        return self._config.weather

    @property
    def ui(self) -> UIConfig:
        """Get the UI configuration.

        Returns:
            UIConfig: The UI configuration object
        """
        return self._config.ui

    @property
    def app(self) -> AppConfig:
        """Get the application configuration.

        Returns:
            AppConfig: The application configuration object
        """
        return self._config

    # Backward compatibility methods
    @property
    def config(self) -> AppConfig:
        """Get the application configuration (backward compatibility).

        Returns:
            AppConfig: The application configuration object
        """
        return self._config

    def get_api_key_by_name(self, key: str) -> Optional[str]:
        """Get API key by name (backward compatibility)."""
        # Map old key names to new service names
        key_map = {
            "gemini_api_key": "gemini",
            "openai_api_key": "openai",
            "openweather_api_key": "openweather",
            "google_maps_api_key": "google_maps",
        }

        service_name = key_map.get(key, key.replace("_api_key", ""))
        return self.get_api_key(service_name)

    def get_api_base_url(self) -> str:
        """Get the OpenWeather API base URL."""
        return self._config.api.openweather_base_url

    def get_request_timeout(self) -> int:
        """Get the API request timeout."""
        return self._config.api.request_timeout

    def get_window_config(self) -> Dict[str, Any]:
        """Get window configuration settings."""
        return {
            "title": self._config.ui.window_title,
            "width": self._config.ui.window_width,
            "height": self._config.ui.window_height,
            "min_width": self._config.ui.min_width,
            "min_height": self._config.ui.min_height,
        }

    def get_ui_colors(self) -> Dict[str, str]:
        """Get UI color configuration."""
        return {
            "primary": self._config.ui.primary_color,
            "secondary": self._config.ui.secondary_color,
            "background": self._config.ui.background_color,
            "text": self._config.ui.text_color,
            "accent": self._config.ui.accent_color,
        }

    def get_favorites_file_path(self) -> Path:
        """Get the favorites file path."""
        return self._config.get_data_path(self._config.data.favorites_file)

    def get_recent_searches_file_path(self) -> Path:
        """Get the recent searches file path."""
        return self._config.get_data_path(self._config.data.recent_searches_file)

    def get_weather_units(self) -> str:
        """Get the default weather units."""
        return self._config.weather.default_units

    def is_debug_mode(self) -> bool:
        """Check if debug mode is enabled."""
        return self._config.logging.log_level.upper() == "DEBUG"

    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value with fallback to default (backward compatibility)."""
        return self.get_setting(key, default)

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

                # Re-sync weather configuration if OpenWeather API key was updated
                if key_name == "openweather_api_key":
                    self._sync_weather_config()

                self._logger.info(f"Updated API key: {key_name}")
                return True
            else:
                self._logger.warning(f"Unknown API key: {key_name}")
                return False
        except Exception as e:
            self._logger.error(f"Failed to update API key {key_name}: {e}")
            return False

    def get_all_api_keys(self) -> Dict[str, str]:
        """Get all configured API keys.

        Returns:
            Dictionary of API key names and values
        """
        return {
            "openweather_api_key": self._config.api.openweather_api_key or "",
            "openweather_backup_api_key": self._config.api.openweather_backup_api_key or "",
            "weatherapi_api_key": self._config.api.weatherapi_api_key or "",
            "gemini_api_key": self._config.api.gemini_api_key or "",
            "openai_api_key": self._config.api.openai_api_key or "",
            "google_maps_api_key": self._config.api.google_maps_api_key or "",
            "github_token": self._config.api.github_token or "",
        }

    def reload_config(self) -> bool:
        """Reload configuration from environment variables.

        Returns:
            True if reload was successful, False otherwise
        """
        try:
            # Reinitialize the config to pick up new environment variables
            self._config = AppConfig()

            # Ensure weather configuration is synced after reload
            self._sync_weather_config()

            if not self.validate_configuration():
                raise ConfigurationError("Reloaded configuration is invalid")
            self._logger.info("Configuration reloaded successfully")
            return True
        except Exception as e:
            self._logger.error(f"Failed to reload configuration: {e}")
            return False

    def dispose(self) -> None:
        """Dispose of configuration service resources."""
        self._logger.debug("Configuration service disposed")
