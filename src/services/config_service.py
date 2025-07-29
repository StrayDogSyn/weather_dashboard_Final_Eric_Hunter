"""Configuration Service - Application Settings Management

Handles environment variables, API keys, and application configuration.
"""

import os
from typing import Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class WeatherConfig:
    """Weather API configuration."""
    api_key: str
    base_url: str = "https://api.openweathermap.org/data/2.5"
    units: str = "metric"  # metric, imperial, kelvin
    timeout: int = 10


@dataclass
class UIConfig:
    """UI configuration and theming."""
    theme: str = "dark"
    window_width: int = 1200
    window_height: int = 800
    min_width: int = 800
    min_height: int = 600
    
    # Data Terminal Color Scheme
    bg_color: str = "#121212"
    primary_color: str = "#00FFAB"
    accent_color: str = "#2C2C2C"
    text_color: str = "#EAEAEA"
    font_family: str = "JetBrains Mono"
    font_size: int = 12


@dataclass
class AppConfig:
    """Application configuration."""
    debug_mode: bool = False
    log_level: str = "INFO"
    cache_duration: int = 300  # 5 minutes
    auto_refresh: bool = True
    refresh_interval: int = 600  # 10 minutes
    default_city: str = "London"


class ConfigService:
    """Configuration service for managing application settings."""
    
    def __init__(self):
        """Initialize configuration service."""
        self._weather_config: Optional[WeatherConfig] = None
        self._ui_config: Optional[UIConfig] = None
        self._app_config: Optional[AppConfig] = None
        self._load_config()
    
    def _load_config(self) -> None:
        """Load configuration from environment variables."""
        # Weather API configuration
        api_key = os.getenv('OPENWEATHER_API_KEY', '')
        self._weather_config = WeatherConfig(
            api_key=api_key,
            base_url=os.getenv('WEATHER_API_URL', "https://api.openweathermap.org/data/2.5"),
            units=os.getenv('WEATHER_UNITS', 'metric'),
            timeout=int(os.getenv('API_TIMEOUT', '10'))
        )
        
        # UI configuration
        self._ui_config = UIConfig(
            theme=os.getenv('UI_THEME', 'dark'),
            window_width=int(os.getenv('WINDOW_WIDTH', '1200')),
            window_height=int(os.getenv('WINDOW_HEIGHT', '800')),
            font_size=int(os.getenv('FONT_SIZE', '12'))
        )
        
        # Application configuration
        self._app_config = AppConfig(
            debug_mode=os.getenv('DEBUG_MODE', 'false').lower() == 'true',
            log_level=os.getenv('LOG_LEVEL', 'INFO'),
            cache_duration=int(os.getenv('CACHE_DURATION', '300')),
            auto_refresh=os.getenv('AUTO_REFRESH', 'true').lower() == 'true',
            refresh_interval=int(os.getenv('REFRESH_INTERVAL', '600')),
            default_city=os.getenv('DEFAULT_CITY', 'London')
        )
    
    @property
    def weather(self) -> WeatherConfig:
        """Get weather API configuration."""
        return self._weather_config
    
    @property
    def ui(self) -> UIConfig:
        """Get UI configuration."""
        return self._ui_config
    
    @property
    def app(self) -> AppConfig:
        """Get application configuration."""
        return self._app_config
    
    def get_config_dict(self) -> Dict[str, Any]:
        """Get all configuration as dictionary."""
        return {
            'weather': {
                'api_key': '***' if self._weather_config.api_key else None,
                'base_url': self._weather_config.base_url,
                'units': self._weather_config.units,
                'timeout': self._weather_config.timeout
            },
            'ui': {
                'theme': self._ui_config.theme,
                'window_size': f"{self._ui_config.window_width}x{self._ui_config.window_height}",
                'font': f"{self._ui_config.font_family} {self._ui_config.font_size}pt"
            },
            'app': {
                'debug_mode': self._app_config.debug_mode,
                'log_level': self._app_config.log_level,
                'cache_duration': self._app_config.cache_duration,
                'auto_refresh': self._app_config.auto_refresh
            }
        }
    
    def validate_config(self) -> tuple[bool, list[str]]:
        """Validate configuration and return status with any errors."""
        errors = []
        
        # Validate API key
        if not self._weather_config.api_key:
            errors.append("OpenWeather API key is required")
        elif self._weather_config.api_key == 'your_api_key_here':
            errors.append("Please replace placeholder API key with actual key")
        
        # Validate UI settings
        if self._ui_config.window_width < self._ui_config.min_width:
            errors.append(f"Window width must be at least {self._ui_config.min_width}px")
        
        if self._ui_config.window_height < self._ui_config.min_height:
            errors.append(f"Window height must be at least {self._ui_config.min_height}px")
        
        # Validate app settings
        if self._app_config.cache_duration < 60:
            errors.append("Cache duration must be at least 60 seconds")
        
        return len(errors) == 0, errors