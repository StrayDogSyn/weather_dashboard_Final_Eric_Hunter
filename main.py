import sys
import logging
import atexit
import weakref
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Now import with correct paths
from src.ui.professional_weather_dashboard import ProfessionalWeatherDashboard
from src.services.config_service import ConfigService
from src.core.container import ServiceContainer
from src.ui.safe_widgets import SafeWidget
from dotenv import load_dotenv

# Track all after callbacks for cleanup
_after_ids = weakref.WeakSet()

def cleanup_callbacks():
    """Clean up all pending after callbacks before exit."""
    # Clean up SafeWidget callbacks
    SafeWidget.cleanup_all_widgets()
    
    # Clean up tracked widgets
    for widget in list(_after_ids):
        try:
            if widget.winfo_exists():
                # Cancel all pending after callbacks
                for after_id in widget.tk.call('after', 'info'):
                    try:
                        widget.after_cancel(after_id)
                    except:
                        pass
        except:
            pass

def main():
    """Main application entry with proper cleanup."""
    load_dotenv()
    
    # Initialize logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(levelname)s [%(asctime)s] %(name)s: %(message)s',
        datefmt='%H:%M:%S'
    )
    
    logger = logging.getLogger(__name__)
    logger.info("📝 Logging initialized - Level: INFO")
    logger.info("Starting Weather Dashboard with enhanced cleanup...")
    
    # Register cleanup
    atexit.register(cleanup_callbacks)
    
    # Initialize services
    container = ServiceContainer()
    container.register_singleton(ConfigService, ConfigService)
    
    try:
        # Get config service from container
        config_service = container.resolve(ConfigService)
        
        # Create application
        app = ProfessionalWeatherDashboard(config_service=config_service)
        
        # Add to cleanup tracking
        _after_ids.add(app)
        
        # Set proper cleanup on window close
        app.protocol("WM_DELETE_WINDOW", lambda: [cleanup_callbacks(), app.quit()])
        
        # Center and start
        app.center_window()
        logger.info("✅ Weather Dashboard ready!")
        
        # Start application
        app.mainloop()
        
    except KeyboardInterrupt:
        logger.info("Application interrupted by user")
        cleanup_callbacks()
    except Exception as e:
        logger.error(f"Application error: {e}")
        import traceback
        traceback.print_exc()
        cleanup_callbacks()
    finally:
        cleanup_callbacks()
        logging.info("Application shutdown complete")

if __name__ == "__main__":
    main()