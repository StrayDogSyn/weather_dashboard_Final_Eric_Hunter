import sys
import logging
import time
from pathlib import Path
import io
import contextlib
import traceback

# Add src to path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from ui.dashboard import ProfessionalWeatherDashboard
from services.config_service import ConfigService
from dotenv import load_dotenv

# Global exception handler for division errors
def handle_exception(exc_type, exc_value, exc_traceback):
    """Global exception handler to catch division errors."""
    if exc_type == TypeError and "unsupported operand type(s) for /" in str(exc_value):
        print(f"\n🔥 GLOBAL DIVISION ERROR CAUGHT: {exc_value}")
        print(f"Traceback: {''.join(traceback.format_exception(exc_type, exc_value, exc_traceback))}")
        logging.error(f"GLOBAL DIVISION ERROR: {exc_value}")
        logging.error(f"Traceback: {''.join(traceback.format_exception(exc_type, exc_value, exc_traceback))}")
    else:
        # Call the default exception handler
        sys.__excepthook__(exc_type, exc_value, exc_traceback)

# Set the global exception handler
sys.excepthook = handle_exception

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
    """Main application entry point with comprehensive error handling."""
    try:
        # Load environment variables
        load_dotenv()
        
        # Debug: Check if API keys are loaded
        import os
        gemini_key = os.getenv("GEMINI_API_KEY")
        openai_key = os.getenv("OPENAI_API_KEY")
        openweather_key = os.getenv("OPENWEATHER_API_KEY")
        
        print(f"Debug - GEMINI_API_KEY loaded: {'Yes' if gemini_key else 'No'}")
        print(f"Debug - OPENAI_API_KEY loaded: {'Yes' if openai_key else 'No'}")
        print(f"Debug - OPENWEATHER_API_KEY loaded: {'Yes' if openweather_key else 'No'}")
        
        # Initialize logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(levelname)s [%(asctime)s] %(name)s: %(message)s',
            datefmt='%H:%M:%S'
        )
        
        logger.info("📝 Logging initialized - Level: INFO")
        logger.info("Starting Weather Dashboard application...")
        
        # Initialize configuration service with error protection
        logger.info("Initializing configuration service...")
        try:
            config_service = ConfigService()
            logger.debug("Configuration service initialized successfully")
        except Exception as e:
            logger.exception(f"Error initializing configuration service: {e}")
            raise
        
        # Apply stderr filter to suppress CustomTkinter DPI scaling errors
        original_stderr = sys.stderr
        sys.stderr = FilteredStderr(original_stderr)
        
        try:
            # Create application with professional dashboard, passing config service
            logger.info("Creating main application window...")
            try:
                app = ProfessionalWeatherDashboard(config_service=config_service)
                logger.debug("Main application window created successfully")
            except Exception as e:
                logger.exception(f"Error creating main application window: {e}")
                raise
            
            # Center window and update with error handling
            logger.info("Centering window and updating display...")
            try:
                app.center_window()
                app.update()
                logger.debug("Window centered and updated successfully")
            except Exception as e:
                logger.warning(f"Window centering/update warning (non-critical): {e}")
            
            logger.info("Weather Dashboard initialized successfully")
            
            # Small delay to ensure proper initialization
            time.sleep(0.1)
            
            # Start main loop
            logger.info("Starting application main loop...")
            try:
                app.mainloop()
            except Exception as e:
                logger.exception(f"Error in application main loop: {e}")
                raise
        finally:
            # Restore original stderr
            sys.stderr = original_stderr
        
    except TypeError as e:
        if "unsupported operand type(s) for /" in str(e):
            logger.error(f"DIVISION ERROR DETECTED: {e}")
            logger.error(f"Full traceback: {traceback.format_exc()}")
            print(f"\n🔥 CRITICAL ERROR: Division by NoneType detected!")
            print(f"Error: {e}")
            print(f"Traceback: {traceback.format_exc()}")
        else:
            logger.error(f"Type error: {e}")
            logger.error(f"Full traceback: {traceback.format_exc()}")
    except Exception as e:
        logger.error(f"Application error: {e}")
        logger.error(f"Full traceback: {traceback.format_exc()}")
    finally:
        logger.info("Application shutdown complete")

if __name__ == "__main__":
    main()