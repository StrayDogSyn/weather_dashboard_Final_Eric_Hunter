import sys
import logging
import time
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from ui.dashboard.main_dashboard import ProfessionalWeatherDashboard
from services.config_service import ConfigService
from dotenv import load_dotenv

def main():
    """Main application entry with enhanced error handling."""
    try:
        # Initialize logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(levelname)s [%(asctime)s] %(name)s: %(message)s',
            datefmt='%H:%M:%S'
        )
        
        logger = logging.getLogger(__name__)
        logger.info("📝 Logging initialized - Level: INFO")
        logger.info("Starting Weather Dashboard with threading fixes...")
        
        # Load environment variables
        load_dotenv()
        
        # Initialize configuration service
        config_service = ConfigService()
        
        # Create and run application
        app = ProfessionalWeatherDashboard(config_service=config_service)
        
        # Small delay for initialization
        time.sleep(0.1)
        
        # Center and start
        app.center_window()
        logger.info("✅ Weather Dashboard ready!")
        
        # Start application
        app.run()
        
    except Exception as e:
        logging.error(f"Application startup error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        logging.info("Application shutdown complete")

if __name__ == "__main__":
    main()