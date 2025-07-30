import sys
import logging
import time
from pathlib import Path
import io
import contextlib

# Add src to path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from ui.professional_weather_dashboard import ProfessionalWeatherDashboard
from services.config_service import ConfigService
from dotenv import load_dotenv

# Custom stderr filter to suppress CustomTkinter DPI scaling errors
class FilteredStderr:
    def __init__(self, original_stderr):
        self.original_stderr = original_stderr
        self.buffer = ""
    
    def write(self, text):
        self.buffer += text
        if '\n' in self.buffer:
            lines = self.buffer.split('\n')
            self.buffer = lines[-1]  # Keep incomplete line
            
            for line in lines[:-1]:
                # Filter out CustomTkinter DPI scaling errors
                if not ("invalid command name" in line.lower() and 
                       ("update" in line.lower() or "check_dpi_scaling" in line.lower() or "safe_wrapper" in line.lower() or "safe_callback" in line.lower())):
                    self.original_stderr.write(line + '\n')
                    self.original_stderr.flush()
    
    def flush(self):
        if self.buffer:
            # Check the remaining buffer
            if not ("invalid command name" in self.buffer.lower() and 
                   ("update" in self.buffer.lower() or "check_dpi_scaling" in self.buffer.lower() or "safe_wrapper" in self.buffer.lower() or "safe_callback" in self.buffer.lower())):
                self.original_stderr.write(self.buffer)
                self.original_stderr.flush()
            self.buffer = ""

# Create logger for main module
logger = logging.getLogger(__name__)

def main():
    """Main application entry with window state management."""
    try:
        # Load environment variables
        load_dotenv()
        
        # Initialize logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(levelname)s [%(asctime)s] %(name)s: %(message)s',
            datefmt='%H:%M:%S'
        )
        
        logger.info("📝 Logging initialized - Level: INFO")
        logger.info("Starting Weather Dashboard...")
        
        # Initialize configuration service
        config_service = ConfigService()
        
        # Apply stderr filter to suppress CustomTkinter DPI scaling errors
        original_stderr = sys.stderr
        sys.stderr = FilteredStderr(original_stderr)
        
        try:
            # Create application with professional dashboard
            app = ProfessionalWeatherDashboard()
            
            # Center window and update with error handling
            try:
                app.center_window()
                app.update()
            except Exception as e:
                logger.warning(f"Window centering/update warning (non-critical): {e}")
            
            logger.info("Weather Dashboard initialized successfully")
            
            # Small delay to ensure proper initialization
            time.sleep(0.1)
            
            # Start main loop
            app.mainloop()
        finally:
            # Restore original stderr
            sys.stderr = original_stderr
        
    except Exception as e:
        logger.error(f"Application error: {e}")
    finally:
        logger.info("Application shutdown complete")

if __name__ == "__main__":
    main()