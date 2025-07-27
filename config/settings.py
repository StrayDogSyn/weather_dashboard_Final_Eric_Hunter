"""Configuration management with environment variable loading and validation."""

import os
from dataclasses import dataclass
from typing import Optional
from pathlib import Path

# Load environment variables from .env file if it exists
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).parent.parent / '.env'
    load_dotenv(env_path)
except ImportError:
    print("Warning: python-dotenv not installed. Using system environment variables only.")


@dataclass
class Settings:
    """Application configuration settings."""
    
    # Weather API
    openweather_api_key: str
    
    # AI Services
    gemini_api_key: Optional[str] = None
    
    # GitHub Integration
    github_token: Optional[str] = None
    
    # Spotify Integration
    spotify_client_id: Optional[str] = None
    spotify_client_secret: Optional[str] = None
    
    # Database
    database_path: str = "data/weather_dashboard.db"
    
    # Application
    debug_mode: bool = False


def load_settings() -> Settings:
    """Load and validate configuration settings."""
    
    # Required settings
    openweather_key = os.getenv('OPENWEATHER_API_KEY')
    if not openweather_key:
        raise ValueError(
            "OPENWEATHER_API_KEY is required. "
            "Please set it in your .env file or environment variables."
        )
    
    return Settings(
        openweather_api_key=openweather_key,
        gemini_api_key=os.getenv('GEMINI_API_KEY'),
        github_token=os.getenv('GITHUB_TOKEN'),
        spotify_client_id=os.getenv('SPOTIFY_CLIENT_ID'),
        spotify_client_secret=os.getenv('SPOTIFY_CLIENT_SECRET'),
        database_path=os.getenv('DATABASE_PATH', 'data/weather_dashboard.db'),
        debug_mode=os.getenv('DEBUG_MODE', 'false').lower() == 'true'
    )


# Global settings instance
settings = load_settings()