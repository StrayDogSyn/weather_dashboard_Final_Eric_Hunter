#!/usr/bin/env python3
"""Weather Dashboard - Main Application Entry Point

Modern weather dashboard with CustomTkinter UI and real-time data visualization.
"""

import os
import sys
import logging
from pathlib import Path

# Add src directory to Python path
src_dir = Path(__file__).parent / 'src'
sys.path.insert(0, str(src_dir))

from dotenv import load_dotenv
from ui.weather_dashboard import WeatherDashboard
from ui.professional_weather_dashboard import ProfessionalWeatherDashboard
from services.config_service import ConfigService
from services.logging_service import LoggingService


def setup_environment():
    """Setup environment variables and configuration."""
    # Load environment variables
    env_path = src_dir.parent / '.env'
    if env_path.exists():
        load_dotenv(env_path)
    else:
        # Load from .env.example as fallback
        example_env = src_dir.parent / '.env.example'
        if example_env.exists():
            load_dotenv(example_env)
            print("⚠️  Using .env.example - Please create .env with your API keys")


def setup_logging():
    """Setup application logging."""
    log_level = os.getenv('LOG_LEVEL', 'INFO')
    debug_mode = os.getenv('DEBUG_MODE', 'false').lower() == 'true'
    
    logging_service = LoggingService()
    logging_service.setup_logging(
        level=getattr(logging, log_level.upper()),
        debug_mode=debug_mode
    )
    
    return logging_service.get_logger(__name__)


def main():
    """Main application entry point."""
    try:
        # Setup environment and logging
        setup_environment()
        logger = setup_logging()
        
        logger.info("🚀 Starting Weather Dashboard...")
        
        # Validate API key
        api_key = os.getenv('OPENWEATHER_API_KEY')
        if not api_key or api_key == 'your_api_key_here':
            logger.error("❌ OpenWeather API key not configured")
            print("\n❌ Error: OpenWeather API key not found!")
            print("Please:")
            print("1. Copy .env.example to .env")
            print("2. Add your OpenWeather API key to .env")
            print("3. Get a free API key at: https://openweathermap.org/api\n")
            return 1
        
        # Initialize and run dashboard with professional design
        config_service = ConfigService()
        
        # Check for professional mode preference
        use_professional = os.getenv('USE_PROFESSIONAL_UI', 'true').lower() == 'true'
        
        if use_professional:
            try:
                dashboard = ProfessionalWeatherDashboard()
                logger.info("✅ Professional Weather Dashboard initialized successfully")
            except Exception as e:
                logger.warning(f"⚠️ Professional dashboard unavailable, using standard: {e}")
                dashboard = WeatherDashboard(config_service, use_enhanced_features=True)
                logger.info("✅ Standard Weather Dashboard initialized successfully")
        else:
            dashboard = WeatherDashboard(config_service, use_enhanced_features=True)
            logger.info("✅ Standard Weather Dashboard initialized successfully")
        
        dashboard.run()
        
        return 0
        
    except KeyboardInterrupt:
        print("\n👋 Dashboard closed by user")
        return 0
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        logging.exception("Fatal error in main application")
        return 1


if __name__ == "__main__":
    sys.exit(main())