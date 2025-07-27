#!/usr/bin/env python3
"""
Configuration Manager - Professional API Key and Settings Management

This module demonstrates advanced configuration management patterns including:
- Secure API key handling with environment variables
- Fallback configuration systems
- Type-safe configuration access
- Professional error handling for missing configurations
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict
from dotenv import load_dotenv


@dataclass
class APIConfig:
    """Type-safe API configuration container."""
    openweather_api_key: str = ""
    weather_api_key: str = ""
    gemini_api_key: str = ""
    spotify_client_id: str = ""
    spotify_client_secret: str = ""
    github_token: str = ""


@dataclass
class UIConfig:
    """Glassmorphic UI configuration settings."""
    window_width: int = 1400
    window_height: int = 900
    glass_opacity: float = 0.85
    blur_radius: int = 20
    corner_radius: int = 15
    animation_duration: int = 300
    theme_mode: str = "dark"


@dataclass
class AppConfig:
    """Main application configuration."""
    default_city: str = "Austin"
    temperature_unit: str = "fahrenheit"  # fahrenheit, celsius, kelvin
    update_interval: int = 300  # seconds
    max_journal_entries: int = 1000
    enable_animations: bool = True
    enable_sounds: bool = True
    auto_save_interval: int = 60  # seconds
    cache_ttl_minutes: int = 10  # cache time-to-live in minutes


class ConfigManager:
    """
    Professional configuration management system.

    This class demonstrates enterprise-level configuration patterns:
    - Environment variable integration
    - Secure API key management
    - Configuration file persistence
    - Type-safe configuration access
    - Graceful fallback handling
    """

    def __init__(self, config_dir: Optional[Path] = None):
        """Initialize the configuration manager."""
        self.logger = logging.getLogger(__name__)

        # Load .env file from project root first
        project_root = Path(__file__).parent.parent.parent
        env_file = project_root / ".env"
        if env_file.exists():
            load_dotenv(env_file)
            self.logger.info(f"Loaded environment variables from {env_file}")

        # Set up configuration directory
        if config_dir is None:
            config_dir = Path.home() / ".weather_dashboard"

        self.config_dir = config_dir
        self.config_file = self.config_dir / "config.json"
        self.env_file = self.config_dir / ".env"

        # Also try to load .env from config directory
        if self.env_file.exists():
            load_dotenv(self.env_file)
            self.logger.info(f"Loaded environment variables from {self.env_file}")

        # Ensure config directory exists
        self.config_dir.mkdir(exist_ok=True)

        # Initialize configuration objects
        self.api_config = APIConfig()
        self.ui_config = UIConfig()
        self.app_config = AppConfig()

        # Load configuration
        self._load_configuration()

    def _load_configuration(self) -> None:
        """
        Load configuration from multiple sources with proper precedence.

        Loading order (highest to lowest precedence):
        1. Environment variables
        2. Configuration file
        3. Default values
        """
        try:
            # Load from configuration file first
            self._load_from_file()

            # Override with environment variables
            self._load_from_environment()

            # Validate critical configuration
            self._validate_configuration()

            self.logger.info("Configuration loaded successfully")

        except Exception as e:
            self.logger.error(f"Failed to load configuration: {e}")
            # Continue with default values

    def _load_from_file(self) -> None:
        """Load configuration from JSON file."""
        if not self.config_file.exists():
            self.logger.info("No configuration file found, using defaults")
            return

        try:
            with open(self.config_file, 'r') as f:
                config_data = json.load(f)

            # Update configuration objects
            if 'api' in config_data:
                self._update_dataclass(self.api_config, config_data['api'])

            if 'ui' in config_data:
                self._update_dataclass(self.ui_config, config_data['ui'])

            if 'app' in config_data:
                self._update_dataclass(self.app_config, config_data['app'])

            self.logger.debug("Configuration loaded from file")

        except Exception as e:
            self.logger.error(f"Error loading configuration file: {e}")

    def _load_from_environment(self) -> None:
        """
        Load configuration from environment variables.

        This method demonstrates secure API key management using environment variables,
        which is a professional security practice for sensitive configuration data.
        """
        # API Keys (most critical - must be in environment for security)
        self.api_config.openweather_api_key = os.getenv('OPENWEATHER_API_KEY', self.api_config.openweather_api_key)
        self.api_config.weather_api_key = os.getenv('WEATHER_API_KEY', self.api_config.weather_api_key)
        self.api_config.gemini_api_key = os.getenv('GEMINI_API_KEY', self.api_config.gemini_api_key)
        self.api_config.spotify_client_id = os.getenv('SPOTIFY_CLIENT_ID', self.api_config.spotify_client_id)
        self.api_config.spotify_client_secret = os.getenv('SPOTIFY_CLIENT_SECRET', self.api_config.spotify_client_secret)
        self.api_config.github_token = os.getenv('GITHUB_TOKEN', self.api_config.github_token)

        # Application settings
        if os.getenv('DEFAULT_CITY'):
            self.app_config.default_city = os.getenv('DEFAULT_CITY')

        if os.getenv('TEMPERATURE_UNIT'):
            self.app_config.temperature_unit = os.getenv('TEMPERATURE_UNIT')

        # UI settings
        if os.getenv('WINDOW_WIDTH'):
            try:
                self.ui_config.window_width = int(os.getenv('WINDOW_WIDTH'))
            except ValueError:
                self.logger.warning("Invalid WINDOW_WIDTH environment variable")

        if os.getenv('WINDOW_HEIGHT'):
            try:
                self.ui_config.window_height = int(os.getenv('WINDOW_HEIGHT'))
            except ValueError:
                self.logger.warning("Invalid WINDOW_HEIGHT environment variable")

    def _update_dataclass(self, obj: Any, data: Dict[str, Any]) -> None:
        """Update dataclass object with dictionary data."""
        for key, value in data.items():
            if hasattr(obj, key):
                setattr(obj, key, value)

    def _validate_configuration(self) -> None:
        """
        Validate critical configuration settings.

        This method ensures that essential API keys are available and
        configuration values are within acceptable ranges.
        """
        # Check for at least one weather API key
        if not self.api_config.openweather_api_key and not self.api_config.weather_api_key:
            self.logger.warning(
                "No weather API keys configured. Some features may not work. "
                "Please set OPENWEATHER_API_KEY or WEATHER_API_KEY environment variables."
            )

        # Validate UI configuration ranges
        if self.ui_config.window_width < 800:
            self.logger.warning("Window width too small, setting to minimum 800px")
            self.ui_config.window_width = 800

        if self.ui_config.window_height < 600:
            self.logger.warning("Window height too small, setting to minimum 600px")
            self.ui_config.window_height = 600

        if not 0.1 <= self.ui_config.glass_opacity <= 1.0:
            self.logger.warning("Invalid glass opacity, resetting to default")
            self.ui_config.glass_opacity = 0.85

    def save_configuration(self) -> None:
        """
        Save current configuration to file.

        Note: API keys are NOT saved to file for security reasons.
        They should only be provided via environment variables.
        """
        try:
            config_data = {
                'ui': asdict(self.ui_config),
                'app': asdict(self.app_config),
                # Deliberately exclude API config for security
            }

            with open(self.config_file, 'w') as f:
                json.dump(config_data, f, indent=2)

            self.logger.info("Configuration saved successfully")

        except Exception as e:
            self.logger.error(f"Failed to save configuration: {e}")

    def get_api_config(self) -> APIConfig:
        """Get API configuration."""
        return self.api_config

    def get_ui_config(self) -> UIConfig:
        """Get UI configuration."""
        return self.ui_config

    def get_app_config(self) -> AppConfig:
        """Get application configuration."""
        return self.app_config

    def update_setting(self, category: str, key: str, value: Any) -> None:
        """
        Update a specific configuration setting.

        Args:
            category: Configuration category ('ui', 'app')
            key: Setting key
            value: New value
        """
        try:
            if category == 'ui' and hasattr(self.ui_config, key):
                setattr(self.ui_config, key, value)
            elif category == 'app' and hasattr(self.app_config, key):
                setattr(self.app_config, key, value)
            else:
                raise ValueError(f"Invalid configuration setting: {category}.{key}")

            # Auto-save after update
            self.save_configuration()

            self.logger.debug(f"Updated setting {category}.{key} = {value}")

        except Exception as e:
            self.logger.error(f"Failed to update setting {category}.{key}: {e}")

    def create_sample_env_file(self) -> None:
        """
        Create a sample .env file with placeholder values.

        This helps users understand what environment variables are needed.
        """
        sample_env_content = """
# Weather Dashboard API Configuration
# Copy this file to .env and fill in your actual API keys

# Weather APIs (at least one required)
OPENWEATHER_API_KEY=your_openweather_api_key_here
WEATHER_API_KEY=your_weather_api_key_here

# AI Integration (optional)
GEMINI_API_KEY=your_gemini_api_key_here

# Spotify Integration (optional)
SPOTIFY_CLIENT_ID=your_spotify_client_id_here
SPOTIFY_CLIENT_SECRET=your_spotify_client_secret_here

# GitHub Integration (optional)
GITHUB_TOKEN=your_github_token_here

# Application Settings (optional)
DEFAULT_CITY=Austin
TEMPERATURE_UNIT=fahrenheit
WINDOW_WIDTH=1400
WINDOW_HEIGHT=900
""".strip()

        sample_file = self.config_dir / ".env.sample"

        try:
            with open(sample_file, 'w') as f:
                f.write(sample_env_content)

            self.logger.info(f"Sample environment file created: {sample_file}")

        except Exception as e:
            self.logger.error(f"Failed to create sample .env file: {e}")
