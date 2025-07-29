import sys
import os
import logging
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

# Single import - choose ONE GUI framework
from ui.weather_dashboard import WeatherDashboard  # OR professional_weather_dashboard
from services.config_service import ConfigService
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

class SingleInstanceApp:
    def __init__(self):
        self.lock_file = "weather_app.lock"
        
    def is_running(self):
        """Check if app is already running."""
        if os.path.exists(self.lock_file):
            try:
                with open(self.lock_file, 'r') as f:
                    pid = int(f.read().strip())
                    
                # Check if process is still running
                try:
                    os.kill(pid, 0)  # Signal 0 checks if process exists
                    return True
                except OSError:
                    # Process doesn't exist, remove stale lock
                    os.remove(self.lock_file)
                    return False
            except:
                # Invalid lock file, remove it
                try:
                    os.remove(self.lock_file)
                except:
                    pass
                return False
        return False
    
    def create_lock(self):
        """Create lock file with current PID."""
        with open(self.lock_file, 'w') as f:
            f.write(str(os.getpid()))
    
    def remove_lock(self):
        """Remove lock file."""
        try:
            if os.path.exists(self.lock_file):
                os.remove(self.lock_file)
        except:
            pass

def main():
    """Main application entry with optimized window startup."""
    # Check for existing instance
    app_instance = SingleInstanceApp()
    
    if app_instance.is_running():
        print("Weather Dashboard is already running!")
        return
    
    # Create lock file
    app_instance.create_lock()
    
    try:
        # Load environment variables
        load_dotenv()
        
        # Initialize logging ONCE
        logging.basicConfig(
            level=logging.INFO,
            format='%(levelname)s [%(asctime)s] %(name)s: %(message)s',
            datefmt='%H:%M:%S'
        )
        
        logger.info("📝 Logging initialized - Level: INFO")
        logger.info("Starting Weather Dashboard...")
        
        # Initialize required services
        config_service = ConfigService()
        
        # Create SINGLE GUI instance with optimized startup
        app = WeatherDashboard(config_service)
        
        # Force window to front after creation
        app.after(50, lambda: app.focus_force())
        
        logger.info("Weather Dashboard initialized successfully")
        
        # Start SINGLE event loop
        app.mainloop()
        
    except Exception as e:
        logger.error(f"Application error: {e}")
        
    finally:
        # Always clean up lock file
        app_instance.remove_lock()
        logger.info("👋 Weather Dashboard closed")

if __name__ == "__main__":
    main()