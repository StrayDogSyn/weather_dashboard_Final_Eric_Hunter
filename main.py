import sys
import logging
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from ui.dashboard import ProfessionalWeatherDashboard
from services.config_service import ConfigService
from dotenv import load_dotenv

# Create logger for main module
logger = logging.getLogger(__name__)

def main():
    """Main application entry point."""
    try:
        # Load environment variables
        load_dotenv()
        
        # Initialize clean logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(levelname)s [%(asctime)s] %(name)s: %(message)s',
            datefmt='%H:%M:%S'
        )
        
        logger.info("🌤️ Starting Weather Dashboard...")
        
        # Initialize services
        config_service = ConfigService()
        
        # Create application
        app = ProfessionalWeatherDashboard(config_service=config_service)
        
        # Center and start
        app.center_window()
        logger.info("✅ Weather Dashboard ready!")
        
        # Run application
        app.mainloop()
        
    except Exception as e:
        logger.error(f"Application error: {e}")
        print(f"ERROR: {e}")
        
    finally:
        logger.info("Application shutdown complete")

if __name__ == "__main__":
    main()