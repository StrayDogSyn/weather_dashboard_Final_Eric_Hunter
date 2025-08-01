import sys
import logging
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from ui.professional_weather_dashboard import ProfessionalWeatherDashboard
from dotenv import load_dotenv

def main():
    """Main entry point."""
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(levelname)s [%(asctime)s] %(name)s: %(message)s',
        datefmt='%H:%M:%S'
    )
    
    logger = logging.getLogger(__name__)
    logger.info("Starting Weather Dashboard...")
    
    # Load environment
    load_dotenv()
    
    try:
        # Create and run app
        app = ProfessionalWeatherDashboard()
        logger.info("Weather Dashboard UI initialized")
        app.mainloop()
    except Exception as e:
        logger.error(f"Application error: {e}")
        raise
    finally:
        logger.info("Application shutdown")

if __name__ == "__main__":
    main()