import sys
import logging
import threading
import time
import tkinter as tk
from pathlib import Path
from typing import Dict, Any, Optional
import os
import json
from datetime import datetime
import asyncio

# Add src to path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from utils.loading_manager import LoadingManager
from dotenv import load_dotenv

# Async loading imports
try:
    from src.services.async_service_manager import AsyncServiceManager
    from src.services.async_loader import LoadingResult
    from src.ui.components.progressive_loader import ProgressiveLoader
    ASYNC_AVAILABLE = True
except ImportError as e:
    logging.warning(f"Async loading not available: {e}")
    ASYNC_AVAILABLE = False


def ensure_directories():
    """Ensure all required directories exist"""
    required_dirs = [
        'cache',
        'config',
        'data',
        'logs',
        'assets',
        'assets/weather_images'
    ]
    
    for dir_path in required_dirs:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
    
    # Create default config if not exists
    config_file = Path('config/settings.json')
    if not config_file.exists():
        default_config = {
            'theme': 'midnight',
            'temperature_unit': 'celsius',
            'cache_ttl': 3600,
            'created_at': datetime.now().isoformat()
        }
        config_file.parent.mkdir(exist_ok=True)
        with open(config_file, 'w') as f:
            json.dump(default_config, f, indent=2)


def setup_logging():
    """Configure logging with rotation"""
    log_dir = Path('logs')
    log_dir.mkdir(exist_ok=True)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_dir / 'weather_dashboard.log', encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # Set console encoding to UTF-8 for Windows
    if sys.platform == 'win32':
        try:
            import codecs
            sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
            sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')
        except (AttributeError, OSError):
            pass  # Fallback if encoding setup fails


# Lazy imports for UI components
try:
    import customtkinter as ctk
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")
except ImportError:
    ctk = None


class WeatherApp(ctk.CTk):
    """Main Weather Application class with enhanced service initialization."""
    
    def __init__(self):
        """Initialize the weather application with proper service handling."""
        super().__init__()
        
        self.logger = logging.getLogger(__name__)
        self.weather_service = None
        
        # Initialize TimerManager first
        try:
            from src.utils.timer_manager import TimerManager
            self.timer_manager = TimerManager(self)
            self.logger.info("TimerManager initialized successfully")
        except ImportError as e:
            self.logger.error(f"TimerManager import error: {e}")
            self.timer_manager = None
        
        # Set up window close protocol
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        try:
            # Import from correct location
            from src.services.weather.enhanced_weather_service import EnhancedWeatherService
            from src.services.config.config_service import ConfigService
            
            # Initialize config service first
            config_service = ConfigService()
            
            # Initialize enhanced weather service
            self.weather_service = EnhancedWeatherService(config_service)
            self.logger.info("Enhanced weather service initialized successfully")
            
        except ImportError as e:
            self.logger.error(f"Import error: {e}")
            # Fallback to basic service
            try:
                from src.services.weather.weather_service import WeatherService
                self.weather_service = WeatherService()
                self.logger.info("Fallback to basic weather service")
            except ImportError as fallback_error:
                self.logger.error(f"Fallback service import error: {fallback_error}")
                self.weather_service = None
        except Exception as e:
            self.logger.error(f"Weather service initialization error: {e}")
            self.weather_service = None
    
    def on_closing(self):
        """Clean shutdown"""
        self.logger.info("Shutting down application...")
        
        # Stop all timers
        if hasattr(self, 'timer_manager') and self.timer_manager:
            self.timer_manager.shutdown()
        
        # Stop background services
        if hasattr(self, 'api_optimizer'):
            self.api_optimizer.shutdown()
            
        # Close thread pools
        if hasattr(self, 'async_loader'):
            self.async_loader.executor.shutdown(wait=False)
        
        # Destroy window
        self.destroy()


class ProgressiveWeatherApp:
    """Progressive loading weather application with skeleton UI."""

    def __init__(self):
        """Initialize the progressive loading app."""
        self.logger = logging.getLogger(__name__)
        self.loading_manager = LoadingManager(max_workers=3, ui_widget=None)
        self.root = None
        self.dashboard = None
        self.status_label = None
        self.search_bar = None
        self.weather_service = None
        self.progress_steps = [
            "Initializing...",
            "Connecting to weather service...",
            "Loading forecast data...",
            "Ready"
        ]
        self.current_step = 0
        self.cancel_event = threading.Event()
        
        # Track after() call IDs to prevent invalid command errors
        self.pending_after_calls = []

        # Hardcoded London data for instant display
        self.cached_london_data = {
            "location": "London, UK",
            "temperature": "15°C",
            "condition": "Partly Cloudy",
            "humidity": "65%",
            "wind_speed": "12 km/h",
            "pressure": "1013 hPa"
        }

    def create_skeleton_ui(self):
        """Create immediate skeleton UI with loading indicators."""
        if ctk:
            self.root = ctk.CTk()
        else:
            self.root = tk.Tk()

        self.root.title("Weather Dashboard - Loading...")
        self.root.geometry("1200x800")

        if not ctk:
            self.root.configure(bg='#1a1a1a')

        # Initialize weather service for search
        self._initialize_weather_service()

        # Main container
        if ctk:
            main_frame = ctk.CTkFrame(self.root, fg_color="transparent")
        else:
            main_frame = tk.Frame(self.root, bg='#1a1a1a')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # Header with app title and search
        if ctk:
            header_frame = ctk.CTkFrame(main_frame, height=120)
        else:
            header_frame = tk.Frame(main_frame, bg='#2d2d2d', height=120)
        header_frame.pack(fill=tk.X, pady=(0, 20))
        header_frame.pack_propagate(False)

        # Title
        if ctk:
            title_label = ctk.CTkLabel(
                header_frame,
                text="🌤️ Weather Dashboard",
                font=ctk.CTkFont(size=24, weight="bold")
            )
        else:
            title_label = tk.Label(
                header_frame,
                text="🌤️ Weather Dashboard",
                font=("Arial", 24, "bold"),
                fg='#ffffff',
                bg='#2d2d2d'
            )
        title_label.pack(pady=(10, 5))

        # Search bar
        if ctk and self.weather_service:
            try:
                from src.ui.components.search_components import EnhancedSearchBar
                self.search_bar = EnhancedSearchBar(
                    header_frame,
                    self.weather_service,
                    on_location_selected=self._on_location_selected
                )
                self.search_bar.pack(pady=(5, 10))
            except ImportError as e:
                self.logger.warning(f"Could not load search bar: {e}")

        # Add some spacing if search bar failed to load
        if not self.search_bar:
            if ctk:
                spacer = ctk.CTkFrame(header_frame, height=50, fg_color="transparent")
            else:
                spacer = tk.Frame(header_frame, height=50, bg='#2d2d2d')
            spacer.pack()

        # Content area with cached London data
        if ctk:
            content_frame = ctk.CTkFrame(main_frame)
        else:
            content_frame = tk.Frame(main_frame, bg='#2d2d2d')
        content_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 20))

        # Quick weather display with cached data
        if ctk:
            weather_frame = ctk.CTkFrame(content_frame)
        else:
            weather_frame = tk.Frame(content_frame, bg='#3d3d3d')
        weather_frame.pack(fill=tk.X, padx=20, pady=20)

        if ctk:
            self.location_label = ctk.CTkLabel(
                weather_frame,
                text=self.cached_london_data["location"],
                font=ctk.CTkFont(size=18, weight="bold")
            )
        else:
            self.location_label = tk.Label(
                weather_frame,
                text=self.cached_london_data["location"],
                font=("Arial", 18, "bold"),
                fg='#ffffff',
                bg='#3d3d3d'
            )
        self.location_label.pack(pady=10)

        if ctk:
            temp_label = ctk.CTkLabel(
                weather_frame,
                text=self.cached_london_data["temperature"],
                font=ctk.CTkFont(size=36, weight="bold"),
                text_color='#4CAF50'
            )
        else:
            temp_label = tk.Label(
                weather_frame,
                text=self.cached_london_data["temperature"],
                font=("Arial", 36, "bold"),
                fg='#4CAF50',
                bg='#3d3d3d'
            )
        temp_label.pack()

        if ctk:
            condition_label = ctk.CTkLabel(
                weather_frame,
                text=self.cached_london_data["condition"],
                font=ctk.CTkFont(size=14)
            )
        else:
            condition_label = tk.Label(
                weather_frame,
                text=self.cached_london_data["condition"],
                font=("Arial", 14),
                fg='#cccccc',
                bg='#3d3d3d'
            )
        condition_label.pack(pady=(0, 10))

        # Status bar with progress
        if ctk:
            status_frame = ctk.CTkFrame(main_frame, height=40)
        else:
            status_frame = tk.Frame(main_frame, bg='#2d2d2d', height=40)
        status_frame.pack(fill=tk.X)
        status_frame.pack_propagate(False)

        if ctk:
            self.status_label = ctk.CTkLabel(
                status_frame,
                text=self.progress_steps[0],
                font=ctk.CTkFont(size=12),
                text_color='#4CAF50'
            )
        else:
            self.status_label = tk.Label(
                status_frame,
                text=self.progress_steps[0],
                font=("Arial", 12),
                fg='#4CAF50',
                bg='#2d2d2d'
            )
        self.status_label.pack(expand=True)

        self.logger.info("Skeleton UI created and displayed")
        return self.root

    def _initialize_weather_service(self):
        """Initialize the weather service for search functionality."""
        try:
            from src.services.config.config_service import ConfigService
            from src.services.weather.enhanced_weather_service import EnhancedWeatherService

            # Initialize config service first
            config_service = ConfigService()

            # Initialize weather service with config
            self.weather_service = EnhancedWeatherService(config_service)
            self.logger.info("Weather service initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize weather service: {e}")
            self.weather_service = None

    def _on_location_selected(self, location_result):
        """Handle location selection from search bar."""
        try:
            self.logger.info(f"Location selected: {location_result.display_name}")

            # Update the cached data display
            if hasattr(self, 'location_label') and self.location_label:
                if ctk:
                    self.location_label.configure(text=location_result.display_name)
                else:
                    self.location_label.config(text=location_result.display_name)

            # If dashboard is loaded, update it
            if self.dashboard:
                # Trigger weather data reload for new location
                self.dashboard.current_location = location_result.display_name
                self.dashboard._safe_fetch_weather_data()

        except Exception as e:
            self.logger.error(f"Error handling location selection: {e}")

    def update_progress(self, step_index: int):
        """Update progress indicator."""
        if step_index < len(self.progress_steps) and self.status_label:
            self.current_step = step_index
            if ctk:
                self.status_label.configure(text=self.progress_steps[step_index])
            else:
                self.status_label.config(text=self.progress_steps[step_index])
            self.root.update_idletasks()
            self.logger.info(f"Progress: {self.progress_steps[step_index]}")

    def load_dashboard_component(self):
        """Load the main dashboard component."""
        try:
            # Lazy import to avoid blocking startup
            from src.ui.professional_weather_dashboard import ProfessionalWeatherDashboard

            # Create dashboard but don't load data yet
            self.dashboard = ProfessionalWeatherDashboard()
            return True
        except Exception as e:
            self.logger.error(f"Failed to load dashboard component: {e}")
            return False

    def load_weather_data(self):
        """Load real weather data in background."""
        try:
            if self.dashboard:
                # Load weather data without blocking
                self.dashboard._safe_fetch_weather_data()
                return True
            return False
        except Exception as e:
            self.logger.error(f"Failed to load weather data: {e}")
            return False

    def load_forecast_data(self):
        """Load forecast data in background."""
        try:
            if self.dashboard:
                # Start background loading for forecast
                self.dashboard._start_background_loading()
                return True
            return False
        except Exception as e:
            self.logger.error(f"Failed to load forecast data: {e}")
            return False

    def replace_skeleton_with_dashboard(self):
        """Replace skeleton UI with full dashboard."""
        try:
            if self.root:
                # Cancel any pending after() calls to prevent invalid command errors
                self._cancel_pending_calls()
                
                # Clear skeleton content
                for widget in self.root.winfo_children():
                    # Cancel any widget-specific after() calls
                    try:
                        if hasattr(widget, 'after_cancel') and hasattr(widget, 'tk'):
                            # Try to cancel any pending calls on this widget
                            pass
                    except:
                        pass
                    widget.destroy()

                # Create new dashboard in the same window
                self.dashboard = None
                from src.ui.professional_weather_dashboard import ProfessionalWeatherDashboard
                from src.services.config.config_service import ConfigService
                
                # Initialize config service
                config_service = ConfigService()
                
                # Create dashboard with proper error handling
                self.dashboard = ProfessionalWeatherDashboard(master=self.root, config_service=config_service)

                self.root.title("Weather Dashboard")
                self.logger.info("Skeleton UI replaced with full dashboard")
                return True
            return False
        except Exception as e:
            self.logger.error(f"Failed to replace skeleton UI: {e}")
            return False
    
    def _cancel_pending_calls(self):
        """Cancel any pending after() calls to prevent invalid command errors."""
        try:
            # Cancel all tracked after() calls
            for call_id in self.pending_after_calls:
                try:
                    if self.root and hasattr(self.root, 'after_cancel'):
                        self.root.after_cancel(call_id)
                except Exception as cancel_error:
                    self.logger.debug(f"Error canceling call {call_id}: {cancel_error}")
            
            # Clear the list
            self.pending_after_calls.clear()
            
        except Exception as e:
            self.logger.debug(f"Error canceling pending calls: {e}")
    
    def _safe_after(self, delay, callback):
        """Safely schedule an after() call and track it."""
        try:
            if self.root and hasattr(self.root, 'after'):
                call_id = self.root.after(delay, callback)
                self.pending_after_calls.append(call_id)
                return call_id
        except Exception as e:
            self.logger.debug(f"Error scheduling after() call: {e}")
        return None
    
    def replace_with_dashboard(self):
        """Replace current UI with full dashboard - enhanced version."""
        try:
            if not self.root:
                self.logger.error("No root window available for dashboard replacement")
                return False
                
            # Import necessary components
            from src.ui.professional_weather_dashboard import ProfessionalWeatherDashboard
            from src.services.config.config_service import ConfigService
            from src.ui.safe_widgets import SafeWidget
            
            # Clear existing content safely
            for widget in self.root.winfo_children():
                try:
                    widget.destroy()
                except Exception as widget_error:
                    self.logger.warning(f"Error destroying widget: {widget_error}")
            
            # Initialize services
            config_service = ConfigService()
            
            # Create new dashboard with error handling
            try:
                self.dashboard = ProfessionalWeatherDashboard(
                    master=self.root, 
                    config_service=config_service
                )
                
                # Update window title
                self.root.title("Weather Dashboard - Ready")
                
                # Log successful replacement
                self.logger.info("Successfully replaced skeleton with full dashboard")
                
                return True
                
            except Exception as dashboard_error:
                self.logger.error(f"Failed to create dashboard: {dashboard_error}")
                
                # Create fallback UI
                self._create_fallback_ui()
                return False
                
        except Exception as e:
            self.logger.error(f"Critical error in dashboard replacement: {e}")
            return False
    
    def _create_fallback_ui(self):
        """Create a simple fallback UI if dashboard creation fails."""
        try:
            if ctk:
                fallback_frame = ctk.CTkFrame(self.root)
                fallback_label = ctk.CTkLabel(
                    fallback_frame,
                    text="Weather Dashboard\n\nSorry, there was an error loading the full interface.\nPlease check the logs for details.",
                    font=ctk.CTkFont(size=16)
                )
            else:
                fallback_frame = tk.Frame(self.root, bg='#2d2d2d')
                fallback_label = tk.Label(
                    fallback_frame,
                    text="Weather Dashboard\n\nSorry, there was an error loading the full interface.\nPlease check the logs for details.",
                    font=("Arial", 16),
                    fg='#ffffff',
                    bg='#2d2d2d'
                )
            
            fallback_frame.pack(fill=tk.BOTH, expand=True)
            fallback_label.pack(expand=True)
            
            self.root.title("Weather Dashboard - Error")
            self.logger.info("Fallback UI created")
            
        except Exception as fallback_error:
            self.logger.error(f"Failed to create fallback UI: {fallback_error}")

    def start_progressive_loading(self):
        """Start the progressive loading sequence."""
        def loading_sequence():
            try:
                # Step 1: Initializing
                self._safe_after(0, lambda: self.update_progress(0))
                time.sleep(0.5)

                if self.cancel_event.is_set():
                    return

                # Step 2: Connecting to weather service
                self._safe_after(0, lambda: self.update_progress(1))
                time.sleep(1.0)

                if self.cancel_event.is_set():
                    return

                # Step 3: Loading forecast data
                self._safe_after(0, lambda: self.update_progress(2))
                time.sleep(2.0)

                if self.cancel_event.is_set():
                    return

                # Step 4: Setting up dashboard
                self._safe_after(0, lambda: self.update_progress(3))

                # Replace skeleton with full dashboard after a brief delay
                self._safe_after(1000, self.replace_skeleton_with_dashboard)

            except Exception as e:
                self.logger.error(f"Progressive loading failed: {e}")

        # Start loading in background thread
        loading_thread = threading.Thread(target=loading_sequence)
        loading_thread.start()

    def run(self):
        """Run the progressive loading application."""
        try:
            # Create and show skeleton UI immediately
            self.create_skeleton_ui()

            # Start progressive loading
            self.start_progressive_loading()
            
            # Run main loop
            self.root.mainloop()
            
        except Exception as e:
            self.logger.error(f"Application error: {e}")
            raise
        finally:
            # Cancel any ongoing operations
            self.cancel_event.set()
            if self.loading_manager:
                self.loading_manager.shutdown()
            self.logger.info("Application shutdown")


def replace_with_dashboard(splash_screen, services):
    """Replace splash with dashboard - FIX master/parent issue"""
    logger = logging.getLogger(__name__)
    
    try:
        # Import the dashboard class
        from src.ui.professional_weather_dashboard import ProfessionalWeatherDashboard
        
        # Create dashboard with parent, not master
        dashboard = ProfessionalWeatherDashboard(
            parent=splash_screen,  # Use parent parameter
            weather_service=services.get('weather'),
            config_service=services.get('config')
        )
        
        # Properly transition
        splash_screen.withdraw()
        dashboard.mainloop()
        
    except Exception as e:
        logger.error(f"Dashboard creation failed: {e}")
        # Show error dialog
        show_error_dialog(str(e))


def show_error_dialog(message):
    """Show error dialog to user."""
    try:
        import tkinter.messagebox as messagebox
        messagebox.showerror(
            "Dashboard Error",
            f"Failed to create weather dashboard:\n\n{message}\n\nPlease check the logs for more details."
        )
    except Exception as dialog_error:
        # Fallback to console output
        print(f"ERROR: {message}")
        print(f"Failed to show error dialog: {dialog_error}")


async def main_async():
    """Async main entry point for faster startup."""
    # Setup logging first
    setup_logging()
    logger = logging.getLogger(__name__)
    
    logger.info("Starting Weather Dashboard (Async Mode)...")
    
    # Ensure required directories exist
    ensure_directories()
    
    # Load environment
    load_dotenv()
    
    try:
        # Import async main application
        from src.async_main import AsyncWeatherApp
        
        # Create and run async application
        app = AsyncWeatherApp()
        await app.run_async()
        
    except Exception as e:
        logger.error(f"Async application failed: {e}")
        logger.info("Falling back to synchronous mode...")
        raise


def main_sync():
    """Synchronous main entry point (fallback)."""
    # Setup logging first
    setup_logging()
    logger = logging.getLogger(__name__)
    
    logger.info("Starting Weather Dashboard (Sync Mode)...")
    
    # Ensure required directories exist
    ensure_directories()
    
    # Load environment
    load_dotenv()

    dashboard = None
    try:
        # Import and create the professional dashboard directly
        from src.ui.professional_weather_dashboard import ProfessionalWeatherDashboard
        from src.services.config.config_service import ConfigService
        from src.ui.safe_widgets import SafeWidget

        # Initialize config service
        config_service = ConfigService()
        logger.info("Configuration service initialized successfully")

        # Create and run the dashboard
        dashboard = ProfessionalWeatherDashboard(config_service=config_service)
        logger.info("Dashboard created successfully")

        # Start the main loop
        dashboard.mainloop()

    except Exception as e:
        logger.error(f"Failed to start dashboard: {e}")
        raise
    finally:
        # Cleanup all safe widgets
        try:
            from src.ui.safe_widgets import SafeWidget
            SafeWidget.cleanup_all_widgets()
            logger.info("Safe widget cleanup completed")
        except Exception as cleanup_error:
            logger.error(f"Error during cleanup: {cleanup_error}")
        
        # Ensure dashboard cleanup
        if dashboard:
            try:
                dashboard.destroy()
            except Exception as destroy_error:
                logger.error(f"Error destroying dashboard: {destroy_error}")
        
        logger.info("Application shutdown complete")


def main():
    """Main entry point - Force sync mode for stability."""
    # Force sync mode for stability
    os.environ['ASYNC_MODE'] = 'false'
    
    # Setup logging first
    setup_logging()
    logger = logging.getLogger(__name__)
    
    try:
        logger.info("Starting in SYNC mode for stability")
        
        # Use synchronous mode only
        main_sync()
        
    except KeyboardInterrupt:
        logger.info("Application interrupted by user")
    except Exception as e:
        logger.exception(f"Application failed to start: {e}")
        # Show error dialog
        try:
            import tkinter.messagebox as mb
            mb.showerror("Startup Error", f"Failed to start: {str(e)}")
        except:
            pass
        raise


if __name__ == "__main__":
    main()
