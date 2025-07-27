#!/usr/bin/env python3
"""
Weather Dashboard - Professional Capstone Project

A modern glassmorphic weather dashboard demonstrating advanced Python development
practices, API integration, and professional UI design patterns.

Author: Eric Hunter
Project: Python Bootcamp Capstone - Weather Dashboard
Tech Stack: Python, CustomTkinter, OpenWeatherMap API, SQLite, GitHub API
"""

import sys
import threading
from pathlib import Path
from typing import Optional, Dict, Any
import logging

# Add src directory to path for imports
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

# Core imports
import customtkinter as ctk
from tkinter import messagebox

# Core application components
from src.core.config_manager import ConfigManager
from src.core.database_manager import DatabaseManager
from src.utils.logger import setup_logging

# Services
from src.services.weather_service import SyncWeatherService
from src.services.github_service import GitHubService

# Feature widgets
from src.features.temperature_graph import TemperatureGraphWidget
from src.features.weather_journal import WeatherJournalWidget
from src.features.activity_suggester import ActivitySuggesterWidget
from src.features.team_collaboration import TeamCollaborationWidget

# Configure logging
setup_logging()
logger = logging.getLogger(__name__)


class WeatherDashboardApp:
    """
    Main application class that orchestrates all dashboard components.

    This class demonstrates professional application architecture with:
    - Dependency injection for service management
    - Graceful error handling and recovery
    - Resource management and cleanup
    - Modular feature integration
    - Professional logging and monitoring
    """

    def __init__(self):
        """Initialize the weather dashboard application."""
        self.config_manager: Optional[ConfigManager] = None
        self.weather_service: Optional[SyncWeatherService] = None
        self.database: Optional[DatabaseManager] = None
        self.github_service: Optional[GitHubService] = None

        # UI components
        self.root: Optional[ctk.CTk] = None
        self.dashboard_ui = None
        self.temperature_graph: Optional[TemperatureGraphWidget] = None
        self.weather_journal: Optional[WeatherJournalWidget] = None
        self.activity_suggester: Optional[ActivitySuggesterWidget] = None
        self.team_collaboration: Optional[TeamCollaborationWidget] = None

        # Application state
        self.is_running = False
        self.current_weather: Optional[Dict[str, Any]] = None
        self.update_thread: Optional[threading.Thread] = None

        logger.info("Weather Dashboard Application initialized")

    def initialize_services(self) -> bool:
        """
        Initialize all application services with proper error handling.

        Returns:
            bool: True if all services initialized successfully
        """
        try:
            # Initialize configuration manager
            self.config_manager = ConfigManager()
            logger.info(f"Configuration manager initialized")

            # Initialize database
            self.database = DatabaseManager()

            # Initialize weather service
            self.weather_service = SyncWeatherService(self.config_manager)

            # Initialize GitHub service (optional)
            api_config = self.config_manager.get_api_config()
            github_token = api_config.github_token
            if github_token:
                try:
                    self.github_service = GitHubService(github_token)
                    logger.info("GitHub service initialized for team collaboration")
                except Exception as e:
                    logger.warning(f"Failed to initialize GitHub service: {e}")
                    # GitHub service is optional, so we continue
            else:
                logger.warning("GitHub token not configured - team features disabled")

            logger.info("All services initialized successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize services: {e}")
            return False

    def create_ui(self) -> bool:
        """
        Create and configure the main UI components.

        Returns:
            bool: True if UI created successfully
        """
        try:
            # Configure CustomTkinter
            ctk.set_appearance_mode("dark")
            ctk.set_default_color_theme("blue")

            # Create main window
            self.root = ctk.CTk()
            self.root.title("Weather Dashboard v1.0")
            self.root.geometry("1400x900")
            self.root.minsize(1200, 800)

            # Set window icon (if available)
            try:
                icon_path = Path("assets/icon.ico")
                if icon_path.exists():
                    self.root.iconbitmap(str(icon_path))
            except Exception:
                pass  # Icon not critical

            # Create a simple dashboard layout
            self._create_dashboard_layout()

            # Initialize feature widgets
            self._initialize_feature_widgets()

            # Setup event handlers
            self._setup_event_handlers()

            logger.info("UI components created successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to create UI: {e}")
            return False

    def _create_dashboard_layout(self):
        """
        Create the main dashboard layout with tabs for different features.
        """
        # Create main container
        self.main_frame = ctk.CTkFrame(self.root)
        self.main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Create title
        title_label = ctk.CTkLabel(
            self.main_frame,
            text="Weather Dashboard",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title_label.pack(pady=(10, 20))

        # Create tabview for different features
        self.tabview = ctk.CTkTabview(self.main_frame)
        self.tabview.pack(fill="both", expand=True, padx=10, pady=10)

        # Add tabs
        self.tabview.add("Temperature Graph")
        self.tabview.add("Weather Journal")
        self.tabview.add("Activity Suggester")
        self.tabview.add("Team Collaboration")

        # Create a simple dashboard UI object to maintain compatibility
        class SimpleDashboardUI:
            def __init__(self, tabview):
                self.main_content = tabview
                self.current_city = "New York"

            def register_feature_widget(self, name, widget):
                pass

            def update_status(self, message):
                pass

        self.dashboard_ui = SimpleDashboardUI(self.tabview)

    def _initialize_feature_widgets(self):
        """Initialize all feature widgets and integrate them with the dashboard."""
        try:
            # Get the tabview for placing widgets
            tabview = self.dashboard_ui.main_content

            # Temperature Graph Widget
            temp_tab = tabview.tab("Temperature Graph")
            self.temperature_graph = TemperatureGraphWidget(
                parent=temp_tab,
                database_manager=self.database
            )

            # Weather Journal Widget
            journal_tab = tabview.tab("Weather Journal")
            self.weather_journal = WeatherJournalWidget(
                parent=journal_tab,
                database_manager=self.database
            )

            # Activity Suggester Widget
            activity_tab = tabview.tab("Activity Suggester")
            api_config = self.config_manager.get_api_config()
            self.activity_suggester = ActivitySuggesterWidget(
                parent=activity_tab,
                database_manager=self.database
            )
            # Configure API keys for AI and Spotify integration
            self.activity_suggester.configure_api_keys(
                gemini_api_key=api_config.gemini_api_key,
                spotify_client_id=api_config.spotify_client_id,
                spotify_client_secret=api_config.spotify_client_secret
            )

            # Team Collaboration Widget (if GitHub available)
            if self.github_service:
                team_tab = tabview.tab("Team Collaboration")
                self.team_collaboration = TeamCollaborationWidget(
                    parent=team_tab,
                    github_service=self.github_service
                )

            # Register widgets with dashboard
            self.dashboard_ui.register_feature_widget("temperature_graph", self.temperature_graph)
            self.dashboard_ui.register_feature_widget("weather_journal", self.weather_journal)
            self.dashboard_ui.register_feature_widget("activity_suggester", self.activity_suggester)

            if self.team_collaboration:
                self.dashboard_ui.register_feature_widget("team_collaboration", self.team_collaboration)

            logger.info("Feature widgets initialized and registered")

        except Exception as e:
            logger.error(f"Failed to initialize feature widgets: {e}")

    def _setup_event_handlers(self):
        """Setup application-wide event handlers."""
        # Window close handler
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def _on_weather_update(self, weather_data: Dict[str, Any]):
        """Handle weather data updates across all components."""
        self.current_weather = weather_data

        # Update all feature widgets with new weather data
        if self.temperature_graph:
            self.temperature_graph.update_weather_data(weather_data)

        if self.weather_journal:
            self.weather_journal.set_weather_data(weather_data)

        if self.activity_suggester:
            self.activity_suggester.update_weather_data(weather_data)

        if self.team_collaboration:
            self.team_collaboration.update_weather_data(weather_data)

        logger.debug("Weather data updated across all components")

    def _show_error_dialog(self, title: str, message: str, error_type: str = "Error"):
        """Show error dialog to user."""
        if self.root:
            messagebox.showerror(title, message)

    def start_background_updates(self):
        """Start background thread for periodic updates."""
        if self.update_thread and self.update_thread.is_alive():
            return

        self.is_running = True
        self.update_thread = threading.Thread(
            target=self._background_update_loop,
            daemon=True
        )
        self.update_thread.start()
        logger.info("Background update thread started")

    def _background_update_loop(self):
        """Background loop for periodic data updates."""
        import time

        while self.is_running:
            try:
                # Update weather data every 10 minutes
                if self.weather_service and self.dashboard_ui:
                    current_city = getattr(self.dashboard_ui, 'current_city', None)
                    if current_city:
                        weather_data = self.weather_service.get_current_weather(current_city)
                        if weather_data:
                            # Schedule UI update on main thread
                            self.root.after(0, lambda data=weather_data: self._on_weather_update(data))

                # Sleep for update interval (10 minutes)
                time.sleep(10 * 60)  # Convert minutes to seconds

            except Exception as e:
                logger.error(f"Background update error: {e}")
                time.sleep(60)  # Wait 1 minute before retrying

    def run(self) -> int:
        """
        Run the weather dashboard application.

        Returns:
            int: Exit code (0 for success, 1 for error)
        """
        try:
            logger.info("Starting Weather Dashboard Application")

            # Initialize services
            if not self.initialize_services():
                return 1

            # Create UI
            if not self.create_ui():
                return 1

            # Start background updates
            self.start_background_updates()

            # Show splash screen or welcome message
            self._show_welcome_message()

            # Start main event loop
            logger.info("Starting main application loop")
            self.root.mainloop()

            logger.info("Application closed successfully")
            return 0

        except KeyboardInterrupt:
            logger.info("Application interrupted by user")
            return 0
        except Exception as e:
            logger.error(f"Fatal application error: {e}")
            return 1
        finally:
            self.cleanup()

    def _show_welcome_message(self):
        """Show welcome message with app info."""
        if self.root:
            welcome_text = (
                "Welcome to Weather Dashboard!\n\n"
                "Features: Temperature Graphs, Weather Journal, Activity Suggestions"
            )
            if self.github_service:
                welcome_text += ", Team Collaboration"

            logger.info("Ready - Welcome to Weather Dashboard!")

    def on_closing(self):
        """Handle application closing."""
        try:
            logger.info("Application closing initiated")

            # Save current configuration
            if self.config_manager:
                pass  # Configuration saving handled by ConfigManager

            # Stop background updates
            self.is_running = False

            # Close database connections
            if self.database:
                self.database.close()

            # Destroy UI
            if self.root:
                self.root.destroy()

        except Exception as e:
            logger.error(f"Error during application closing: {e}")
        finally:
            # Force exit if needed
            sys.exit(0)

    def cleanup(self):
        """Cleanup application resources."""
        try:
            self.is_running = False

            # Wait for background thread to finish
            if self.update_thread and self.update_thread.is_alive():
                self.update_thread.join(timeout=2.0)

            # Close services
            if self.database:
                self.database.close()

            logger.info("Application cleanup completed")

        except Exception as e:
            logger.error(f"Error during cleanup: {e}")


def main() -> int:
    """
    Application entry point.

    Sets up logging and launches the weather dashboard application.
    This function demonstrates professional application startup patterns.
    """
    try:
        # Setup application logging
        setup_logging()

        # Create application data directory if it doesn't exist
        app_data_dir = Path.home() / ".weather_dashboard"
        app_data_dir.mkdir(exist_ok=True)

        logger.info("=" * 50)
        logger.info("Weather Dashboard Application Starting")
        logger.info("=" * 50)

        # Create and run the application
        app = WeatherDashboardApp()
        exit_code = app.run()

        logger.info("=" * 50)
        logger.info("Weather Dashboard Application Finished")
        logger.info("=" * 50)

        return exit_code

    except Exception as e:
        logging.error(f"Fatal error in main: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
