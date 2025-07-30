import sys
import logging
import time
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from ui.professional_weather_dashboard import ProfessionalWeatherDashboard
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
        
        # Create application with professional dashboard
        app = ProfessionalWeatherDashboard()
        
        # Force window to center and update with error handling
        try:
            app.update()
            app.update_idletasks()
        except Exception as e:
            logger.warning(f"Window update warning (non-critical): {e}")
        
        logger.info("Weather Dashboard initialized successfully")
        
        # Small delay to ensure proper initialization
        time.sleep(0.1)
        
        # Start main loop
        app.mainloop()
        
    except Exception as e:
        logger.error(f"Application error: {e}")
    finally:
        logger.info("Application shutdown complete")

if __name__ == "__main__":
    main()