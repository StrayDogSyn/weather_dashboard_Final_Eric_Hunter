"""Main Weather Dashboard Application.

Simplified entry point that uses the DashboardController for better
architecture and separation of concerns.
"""

import logging

import customtkinter as ctk
from dotenv import load_dotenv

from src.services.config_service import ConfigService
from src.ui.dashboard.dashboard_controller import DashboardController

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Set CustomTkinter appearance
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")


class WeatherDashboardApp:
    """Main Weather Dashboard Application."""

    def __init__(self):
        """Initialize the weather dashboard application."""
        self.config_service = None
        self.dashboard = None
        self._initialize_services()
        self._create_dashboard()

    def _initialize_services(self):
        """Initialize core services."""
        try:
            self.config_service = ConfigService()
            logger.info("Services initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize services: {e}")
            # Continue with None config_service for demo mode

    def _create_dashboard(self):
        """Create the main dashboard."""
        try:
            self.dashboard = DashboardController(self.config_service)
            self.dashboard.title("Professional Weather Dashboard - Project CodeFront")
            self.dashboard.geometry("1400x900")
            self.dashboard.minsize(1200, 800)

            # Configure grid weights for responsive design
            self.dashboard.grid_rowconfigure(1, weight=1)
            self.dashboard.grid_columnconfigure(0, weight=1)

            # Set up window closing protocol
            self.dashboard.protocol("WM_DELETE_WINDOW", self._on_closing)

            logger.info("Dashboard created successfully")

        except Exception as e:
            logger.error(f"Failed to create dashboard: {e}")
            raise

    def _on_closing(self):
        """Handle application closing."""
        try:
            if self.dashboard:
                self.dashboard.cleanup()
                self.dashboard.destroy()
            logger.info("Application closed successfully")
        except Exception as e:
            logger.error(f"Error during application closing: {e}")

    def run(self):
        """Run the application."""
        if self.dashboard:
            # Center the window
            self.dashboard.center_window()

            # Start the main loop
            logger.info("Starting Weather Dashboard...")
            self.dashboard.mainloop()
        else:
            logger.error("Dashboard not initialized")


def main():
    """Main entry point for the application."""
    try:
        app = WeatherDashboardApp()
        app.run()
    except Exception as e:
        logger.error(f"Failed to start application: {e}")
        raise


if __name__ == "__main__":
    main()
