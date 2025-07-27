"""Clean configuration management with environment variable loading."""

import os
from dataclasses import dataclass
from typing import Optional
from pathlib import Path

# Load environment variables from .env file if available
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).parent.parent / '.env'
    if env_path.exists():
        load_dotenv(env_path)
except ImportError:
    pass  # Continue without dotenv if not installed


@dataclass(frozen=True)
class Settings:
    """Immutable application configuration settings."""
    
    # Required settings
    openweather_api_key: str
    
    # Optional service integrations
    gemini_api_key: Optional[str] = None
    github_token: Optional[str] = None
    spotify_client_id: Optional[str] = None
    spotify_client_secret: Optional[str] = None
    
    # Application settings
    database_path: str = "data/weather_dashboard.db"
    debug_mode: bool = False
    
    def __post_init__(self) -> None:
        """Validate required settings after initialization."""
        if not self.openweather_api_key:
            raise ValueError(
                "OPENWEATHER_API_KEY is required. "
                "Please set it in your .env file or environment variables."
            )
    
    @property
    def has_gemini(self) -> bool:
        """Check if Gemini AI is configured."""
        return bool(self.gemini_api_key)
    
    @property
    def has_github(self) -> bool:
        """Check if GitHub integration is configured."""
        return bool(self.github_token)
    
    @property
    def has_spotify(self) -> bool:
        """Check if Spotify integration is configured."""
        return bool(self.spotify_client_id and self.spotify_client_secret)


def load_settings() -> Settings:
    """Load and validate configuration settings from environment."""
    return Settings(
        openweather_api_key=os.getenv('OPENWEATHER_API_KEY', ''),
        gemini_api_key=os.getenv('GEMINI_API_KEY'),
        github_token=os.getenv('GITHUB_TOKEN'),
        spotify_client_id=os.getenv('SPOTIFY_CLIENT_ID'),
        spotify_client_secret=os.getenv('SPOTIFY_CLIENT_SECRET'),
        database_path=os.getenv('DATABASE_PATH', 'data/weather_dashboard.db'),
        debug_mode=os.getenv('DEBUG_MODE', 'false').lower() == 'true'
    )


# Global settings instance - lazy loaded
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Get global settings instance (lazy loaded)."""
    global _settings
    if _settings is None:
        _settings = load_settings()
    return _settings