"""Application Configuration

Centralized configuration management for the weather dashboard application.
Contains all constants, settings, and configuration values.
"""

import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional

# Removed circular import - will use standard logging instead

@dataclass
class APIConfig:
    """API configuration settings."""

    openweather_api_key: str = ""
    openweather_backup_api_key: str = ""
    weatherapi_api_key: str = ""
    openweather_base_url: str = "https://api.openweathermap.org/data/2.5"
    weatherapi_base_url: str = "https://api.weatherapi.com/v1"
    geocoding_base_url: str = "https://api.openweathermap.org/geo/1.0"
    air_quality_base_url: str = "https://api.openweathermap.org/data/2.5/air_pollution"

    # AI Service API Keys
    gemini_api_key: str = ""
    openai_api_key: str = ""
    gemini_base_url: str = "https://generativelanguage.googleapis.com/v1beta"
    openai_base_url: str = "https://api.openai.com/v1"

    # Maps API Key
    google_maps_api_key: str = ""

    # GitHub API Key
    github_token: str = ""

    # Spotify API Keys removed

    request_timeout: int = 30
    max_retries: int = 3
    retry_delay: float = 1.0

@dataclass
class UIConfig:
    """UI configuration settings."""

    window_title: str = "PROJECT CODEFRONT - Advanced Weather Intelligence System v3.5"
    window_width: int = 1400
    window_height: int = 900
    min_width: int = 1200
    min_height: int = 800

    # Colors
    primary_color: str = "#2E86AB"
    secondary_color: str = "#A23B72"
    background_color: str = "#F18F01"
    text_color: str = "#C73E1D"
    accent_color: str = "#4CAF50"

    # Fonts
    title_font: tuple = ("Segoe UI", 24, "bold")
    subtitle_font: tuple = ("Segoe UI", 12)
    header_font: tuple = ("Segoe UI", 16, "bold")
    body_font: tuple = ("Segoe UI", 11)
    small_font: tuple = ("Segoe UI", 9)

    # Layout
    padding: int = 10
    margin: int = 5
    border_width: int = 2
    corner_radius: int = 8

@dataclass
class DataConfig:
    """Data management configuration."""

    cache_duration: int = 300  # 5 minutes
    max_cache_size: int = 100
    data_directory: str = "data"
    favorites_file: str = "favorites.json"
    recent_searches_file: str = "recent_searches.json"
    max_recent_searches: int = 10
    max_favorites: int = 50

@dataclass
class WeatherConfig:
    """Weather-specific configuration."""

    base_url: str = "https://api.openweathermap.org/data/2.5"
    api_key: str = ""
    default_units: str = "metric"  # metric, imperial, kelvin
    temperature_precision: int = 1
    pressure_unit: str = "hPa"
    wind_speed_unit: str = "m/s"
    visibility_unit: str = "km"
    cache_duration: int = 300  # Cache duration in seconds (5 minutes)

    # Thresholds
    high_temperature_threshold: float = 30.0  # Celsius
    low_temperature_threshold: float = 0.0  # Celsius
    high_wind_speed_threshold: float = 10.0  # m/s
    low_visibility_threshold: float = 1.0  # km

    # Air Quality Index thresholds
    aqi_thresholds: Dict[str, tuple] = None

    @property
    def units(self) -> str:
        """Get the units for weather data.

        Returns:
            Units string (metric, imperial, kelvin)
        """
        return self.default_units

    @property
    def timeout(self) -> int:
        """Get the request timeout for weather API calls.

        Returns:
            Timeout in seconds
        """
        return 30  # Default timeout for weather API requests

    def __post_init__(self):
        if self.aqi_thresholds is None:
            self.aqi_thresholds = {
                "Good": (0, 50),
                "Moderate": (51, 100),
                "Unhealthy for Sensitive Groups": (101, 150),
                "Unhealthy": (151, 200),
                "Very Unhealthy": (201, 300),
                "Hazardous": (301, 500),
            }

@dataclass
class LoggingConfig:
    """Logging configuration."""

    log_level: str = "INFO"
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    log_file: str = "weather_dashboard.log"
    max_log_size: int = 10 * 1024 * 1024  # 10MB
    backup_count: int = 5
    console_logging: bool = True
    file_logging: bool = True

class AppConfig:
    """Main application configuration class."""

    def __init__(self, config_file: Optional[str] = None):
        """Initialize application configuration.

        Args:
            config_file: Optional path to configuration file
        """
        self.api = APIConfig()
        self.ui = UIConfig()
        self.data = DataConfig()
        self.weather = WeatherConfig()
        self.logging = LoggingConfig()

        # Application-level settings
        self.default_city = "New York"
        self.cache_duration = 300  # Cache duration in seconds (5 minutes)

        # Load from environment variables
        self._load_from_environment()

        # Load from config file if provided
        if config_file:
            self._load_from_file(config_file)

        # Sync weather api_key with API configuration
        self.weather.api_key = self.api.openweather_api_key
        self.weather.base_url = self.api.openweather_base_url

    def _load_from_environment(self) -> None:
        """Load configuration from environment variables."""
        # API configuration
        if api_key := os.getenv("OPENWEATHER_API_KEY"):
            self.api.openweather_api_key = api_key
            logger = logging.getLogger(__name__)
            logger.debug(
                f"Loaded OPENWEATHER_API_KEY: {'[SET]' if api_key else '[EMPTY]'}"
            )

        # Backup OpenWeather API Key
        if backup_key := os.getenv("OPENWEATHER_API_KEY_BACKUP"):
            self.api.openweather_backup_api_key = backup_key
            logger = logging.getLogger(__name__)
            logger.debug(
                f"Loaded OPENWEATHER_API_KEY_BACKUP: {'[SET]' if backup_key else '[EMPTY]'}"
            )

        # WeatherAPI.com API Key
        if weatherapi_key := os.getenv("WEATHERAPI_API_KEY"):
            self.api.weatherapi_api_key = weatherapi_key
            logger = logging.getLogger(__name__)
            logger.debug(
                f"Loaded WEATHERAPI_API_KEY: {'[SET]' if weatherapi_key else '[EMPTY]'}"
            )

        # AI Service API Keys
        if gemini_key := os.getenv("GEMINI_API_KEY"):
            self.api.gemini_api_key = gemini_key
            logger = logging.getLogger(__name__)
            logger.debug(
                f"Loaded GEMINI_API_KEY: {'[SET]' if gemini_key else '[EMPTY]'}"
            )

        if openai_key := os.getenv("OPENAI_API_KEY"):
            self.api.openai_api_key = openai_key
            logger = logging.getLogger(__name__)
            logger.debug(
                f"Loaded OPENAI_API_KEY: {'[SET]' if openai_key else '[EMPTY]'}"
            )

        # Maps API Key
        if maps_key := os.getenv("GOOGLE_MAPS_API_KEY"):
            self.api.google_maps_api_key = maps_key
            logger = logging.getLogger(__name__)
            logger.debug(
                f"Loaded GOOGLE_MAPS_API_KEY: {'[SET]' if maps_key else '[EMPTY]'}"
            )

        # GitHub Token
        if github_token := os.getenv("GITHUB_TOKEN"):
            self.api.github_token = github_token
            logger = logging.getLogger(__name__)
            logger.debug(
                f"Loaded GITHUB_TOKEN: {'[SET]' if github_token else '[EMPTY]'}"
            )

        if timeout := os.getenv("API_TIMEOUT"):
            try:
                self.api.request_timeout = int(timeout)
            except ValueError:
                logger = logging.getLogger(__name__)
                logger.warning(f"Invalid API_TIMEOUT value: {timeout}")
                pass

        # Logging configuration
        if log_level := os.getenv("LOG_LEVEL"):
            self.logging.log_level = log_level.upper()

        # Data configuration
        if data_dir := os.getenv("DATA_DIRECTORY"):
            self.data.data_directory = data_dir

    def _load_from_file(self, config_file: str) -> None:
        """Load configuration from a file.

        Args:
            config_file: Path to configuration file
        """
        import json

        try:
            config_path = Path(config_file)
            if config_path.exists():
                with open(config_path, "r", encoding="utf-8") as f:
                    config_data = json.load(f)

                # Update configuration sections
                if "api" in config_data:
                    self._update_dataclass(self.api, config_data["api"])
                if "ui" in config_data:
                    self._update_dataclass(self.ui, config_data["ui"])
                if "data" in config_data:
                    self._update_dataclass(self.data, config_data["data"])
                if "weather" in config_data:
                    self._update_dataclass(self.weather, config_data["weather"])
                if "logging" in config_data:
                    self._update_dataclass(self.logging, config_data["logging"])

        except Exception as e:
            logger = get_logger(__name__)
            logger.warning(f"Could not load config file {config_file}: {e}")

    def _update_dataclass(self, obj: Any, data: Dict[str, Any]) -> None:
        """Update dataclass fields from dictionary.

        Args:
            obj: Dataclass object to update
            data: Dictionary with new values
        """
        for key, value in data.items():
            if hasattr(obj, key):
                setattr(obj, key, value)

    def get_data_path(self, filename: str) -> Path:
        """Get full path for a data file.

        Args:
            filename: Name of the data file

        Returns:
            Full path to the data file
        """
        data_dir = Path(self.data.data_directory)
        data_dir.mkdir(exist_ok=True)
        return data_dir / filename

    def validate(self) -> bool:
        """Validate configuration settings.

        Returns:
            True if configuration is valid, False otherwise
        """
        logger = get_logger(__name__)

        # Check required API key
        if not self.api.openweather_api_key:
            logger.error("OpenWeather API key is required")
            return False

        # Validate numeric values
        if self.api.request_timeout <= 0:
            logger.error("API timeout must be positive")
            return False

        if self.ui.window_width <= 0 or self.ui.window_height <= 0:
            logger.error("Window dimensions must be positive")
            return False

        return True

    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary.

        Returns:
            Configuration as dictionary
        """
        from dataclasses import asdict

        return {
            "api": asdict(self.api),
            "ui": asdict(self.ui),
            "data": asdict(self.data),
            "weather": asdict(self.weather),
            "logging": asdict(self.logging),
        }

# Weather condition mappings
WEATHER_ICONS = {
    "clear sky": "☀️",
    "few clouds": "🌤️",
    "scattered clouds": "⛅",
    "broken clouds": "☁️",
    "overcast clouds": "☁️",
    "shower rain": "🌦️",
    "rain": "🌧️",
    "thunderstorm": "⛈️",
    "snow": "❄️",
    "mist": "🌫️",
    "fog": "🌫️",
    "haze": "🌫️",
    "dust": "🌪️",
    "sand": "🌪️",
    "ash": "🌋",
    "squall": "💨",
    "tornado": "🌪️",
}

# Air quality color mappings
AQI_COLORS = {
    "Good": "#00E400",
    "Moderate": "#FFFF00",
    "Unhealthy for Sensitive Groups": "#FF7E00",
    "Unhealthy": "#FF0000",
    "Very Unhealthy": "#8F3F97",
    "Hazardous": "#7E0023",
}

# Unit conversion factors
UNIT_CONVERSIONS = {
    "temperature": {
        "celsius_to_fahrenheit": lambda c: (c * 9 / 5) + 32,
        "fahrenheit_to_celsius": lambda f: (f - 32) * 5 / 9,
        "kelvin_to_celsius": lambda k: k - 273.15,
        "celsius_to_kelvin": lambda c: c + 273.15,
    },
    "speed": {
        "mps_to_kmh": lambda mps: mps * 3.6,
        "mps_to_mph": lambda mps: mps * 2.237,
        "kmh_to_mps": lambda kmh: kmh / 3.6,
        "mph_to_mps": lambda mph: mph / 2.237,
    },
    "pressure": {
        "hpa_to_inhg": lambda hpa: hpa * 0.02953,
        "inhg_to_hpa": lambda inhg: inhg / 0.02953,
    },
}
