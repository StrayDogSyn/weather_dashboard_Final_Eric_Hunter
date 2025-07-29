import sys
import logging
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from ui.weather_dashboard import WeatherDashboard
from services.config_service import ConfigService
from dotenv import load_dotenv

# Create logger for main module
logger = logging.getLogger(__name__)

def main():
    """Main application entry with window state management."""
    try:
        # Initialize logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(levelname)s [%(asctime)s] %(name)s: %(message)s',
            datefmt='%H:%M:%S'
        )
        
        logger.info("📝 Logging initialized - Level: INFO")
        logger.info("Starting Weather Dashboard...")
        
        # Load environment variables
        load_dotenv()
        
        # Initialize configuration service
        config_service = ConfigService()
        
        # Create application with window state management
        app = WeatherDashboard(config_service)
        
        # Additional window focus after creation
        app.after(50, lambda: app.focus_force())
        app.after(100, lambda: app.lift())
        
        logger.info("Weather Dashboard initialized successfully")
        
        # Start main loop
        app.mainloop()
        
    except Exception as e:
        logger.error(f"Application error: {e}")
    finally:
        logger.info("Application shutdown complete")

if __name__ == "__main__":
    main()