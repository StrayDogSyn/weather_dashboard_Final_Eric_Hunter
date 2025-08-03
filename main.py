import sys
import logging
import threading
import time
import tkinter as tk
from pathlib import Path
from typing import Dict, Any

# Add src to path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from utils.loading_manager import LoadingManager
from dotenv import load_dotenv

# Lazy imports for UI components
try:
    import customtkinter as ctk
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")
except ImportError:
    ctk = None


class ProgressiveWeatherApp:
    """Progressive loading weather application with skeleton UI."""

    def __init__(self):
        """Initialize the progressive loading app."""
        self.logger = logging.getLogger(__name__)
        self.loading_manager = LoadingManager(max_workers=3)
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
            from src.services.config_service import ConfigService
            from src.services.enhanced_weather_service import EnhancedWeatherService

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
            if self.dashboard and self.root:
                # Clear skeleton content
                for widget in self.root.winfo_children():
                    widget.destroy()

                # Create new dashboard in the same window
                self.dashboard = None
                from src.ui.professional_weather_dashboard import ProfessionalWeatherDashboard
                self.dashboard = ProfessionalWeatherDashboard(master=self.root)

                self.root.title("Weather Dashboard")
                self.logger.info("Skeleton UI replaced with full dashboard")
                return True
            return False
        except Exception as e:
            self.logger.error(f"Failed to replace skeleton UI: {e}")
            return False

    def start_progressive_loading(self):
        """Start the progressive loading sequence."""
        def loading_sequence():
            try:
                # Step 1: Initializing
                self.root.after(0, lambda: self.update_progress(0))
                time.sleep(0.5)

                if self.cancel_event.is_set():
                    return

                # Step 2: Connecting to weather service
                self.root.after(0, lambda: self.update_progress(1))
                time.sleep(1.0)

                if self.cancel_event.is_set():
                    return

                # Step 3: Loading forecast data
                self.root.after(0, lambda: self.update_progress(2))
                time.sleep(2.0)

                if self.cancel_event.is_set():
                    return

                # Step 4: Ready
                self.root.after(0, lambda: self.update_progress(3))

                # Replace skeleton with full dashboard after a brief delay
                self.root.after(1000, self.replace_skeleton_with_dashboard)

            except Exception as e:
                self.logger.error(f"Progressive loading failed: {e}")

        # Start loading in background thread
        loading_thread = threading.Thread(target=loading_sequence, daemon=True)
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


def main():
    """Main entry point for the weather dashboard."""
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
        # Import and create the professional dashboard directly
        from src.ui.professional_weather_dashboard import ProfessionalWeatherDashboard
        from src.services.config_service import ConfigService

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


if __name__ == "__main__":
    main()
