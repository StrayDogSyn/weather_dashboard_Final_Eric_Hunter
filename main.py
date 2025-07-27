#!/usr/bin/env python3
"""
Weather Dashboard Application - Main Entry Point

A comprehensive weather dashboard application built with CustomTkinter,
integrating multiple weather data sources, AI-powered insights, and
collaborative features using clean architecture principles.

Features:
- Real-time weather data from OpenWeatherMap
- Temperature trend visualization
- Weather journal with personal notes
- AI-powered activity suggestions via Gemini AI
- Music recommendations via Spotify
- Team collaboration via GitHub integration
- Modern, responsive UI with CustomTkinter
- Clean architecture with separated concerns

This is the single application entry point that integrates all services
and UI components using the clean architecture pattern.

Author: Eric Hunter
Version: 2.0.0 (Clean Architecture)
"""

import sys
import threading
from pathlib import Path
from typing import Optional, Dict, Any
import logging

# Core imports
import tkinter as tk
from tkinter import messagebox

# Import clean architecture services
from config.settings import load_settings
from data.database import Database
from services.weather_service import WeatherService
from services.gemini_service import GeminiService
from services.github_service import GitHubService
from services.spotify_service import SpotifyService

# Import Hunter theme UI
from src.ui.dashboard_ui import HunterDashboardUI

# Import utilities
from src.utils.logger import setup_logging

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
        # Core services (clean architecture)
        self.settings = None
        self.database: Optional[Database] = None
        self.weather_service: Optional[WeatherService] = None
        self.gemini_service: Optional[GeminiService] = None
        self.github_service: Optional[GitHubService] = None
        self.spotify_service: Optional[SpotifyService] = None

        # UI components
        self.root: Optional[tk.Tk] = None
        self.dashboard_ui: Optional[HunterDashboardUI] = None

        # Application state
        self.is_running = False
        self.current_weather: Optional[Dict[str, Any]] = None
        self.update_thread: Optional[threading.Thread] = None

        logger.info("Weather Dashboard Application initialized")

    def initialize_services(self) -> bool:
        """
        Initialize all core services.

        Returns:
            bool: True if all services initialized successfully, False otherwise
        """
        try:
            logger.info("Initializing core services...")

            # Initialize settings
            self.settings = load_settings()
            logger.info("Settings loaded successfully")

            # Initialize database
            self.database = Database()
            logger.info("Database initialized successfully")

            # Initialize weather service
            self.weather_service = WeatherService()
            logger.info("Weather service initialized")

            # Initialize optional services
            # Gemini AI service
            if self.settings.gemini_api_key:
                try:
                    self.gemini_service = GeminiService()
                    logger.info("Gemini AI service initialized")
                except Exception as e:
                    logger.warning(f"Gemini AI service initialization failed: {e}")
                    self.gemini_service = None
            else:
                logger.info("Gemini API key not provided, skipping Gemini service")

            # GitHub service
            if self.settings.github_token:
                try:
                    self.github_service = GitHubService()
                    logger.info("GitHub service initialized")
                except Exception as e:
                    logger.warning(f"GitHub service initialization failed: {e}")
                    self.github_service = None
            else:
                logger.info("GitHub token not provided, skipping GitHub service")

            # Spotify service
            if self.settings.spotify_client_id and self.settings.spotify_client_secret:
                try:
                    self.spotify_service = SpotifyService()
                    logger.info("Spotify service initialized")
                except Exception as e:
                    logger.warning(f"Spotify service initialization failed: {e}")
                    self.spotify_service = None
            else:
                logger.info("Spotify credentials not provided, skipping Spotify service")

            logger.info("Core services initialized successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize services: {e}")
            return False

    def create_ui(self) -> bool:
        """
        Create and setup the Hunter theme UI.

        Returns:
            bool: True if UI created successfully, False otherwise
        """
        try:
            logger.info("Creating Hunter theme UI...")

            # Create main window
            self.root = tk.Tk()
            self.root.title("Hunter Weather Dashboard")
            self.root.geometry("1200x800")

            # Create Hunter dashboard UI
            self.dashboard_ui = HunterDashboardUI(
                self.root,
                weather_callback=self._handle_weather_request
            )

            # Setup event handlers
            self._setup_event_handlers()

            logger.info("Hunter theme UI created successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to create UI: {e}")
            return False

    def _handle_weather_request(self, location: str):
        """
        Handle weather data request from the UI.
        
        Args:
            location: The location to get weather data for
        """
        try:
            if self.weather_service:
                weather_data = self.weather_service.get_weather(location)
                if weather_data and self.dashboard_ui:
                    # Convert weather data to dictionary format
                    weather_dict = {
                        'location': getattr(weather_data, 'location', location),
                        'temperature': getattr(weather_data, 'temperature', 'N/A'),
                        'condition': getattr(weather_data, 'condition', 'Unknown'),
                        'humidity': getattr(weather_data, 'humidity', 'N/A'),
                        'wind_speed': getattr(weather_data, 'wind_speed', 'N/A'),
                        'pressure': getattr(weather_data, 'pressure', 'N/A')
                    }
                    self.dashboard_ui.update_weather_display(weather_dict)
                    self.current_weather = weather_data
                    logger.info(f"Weather data updated for {location}")
                else:
                    logger.warning(f"Failed to get weather data for {location}")
            else:
                logger.error("Weather service not available")
        except Exception as e:
            logger.error(f"Error handling weather request: {e}")

    def _setup_event_handlers(self):
        """Setup application-wide event handlers."""
        try:
            # Setup window close event
            self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
            
            # Setup initial weather data
            if self.weather_service:
                initial_weather = self.weather_service.get_weather("New York")
                if initial_weather:
                    self._on_weather_update(initial_weather)
            
            logger.info("Event handlers setup completed")
        except Exception as e:
            logger.error(f"Failed to setup event handlers: {e}")

    def _on_weather_update(self, weather_data):
        """Handle weather data updates across all components."""
        self.current_weather = weather_data
        
        if self.dashboard_ui:
            # Convert weather data to dictionary format for UI
            weather_dict = {
                'location': getattr(weather_data, 'location', 'Unknown'),
                'temperature': getattr(weather_data, 'temperature', 'N/A'),
                'condition': getattr(weather_data, 'condition', 'Unknown'),
                'humidity': getattr(weather_data, 'humidity', 'N/A'),
                'wind_speed': getattr(weather_data, 'wind_speed', 'N/A'),
                'pressure': getattr(weather_data, 'pressure', 'N/A')
            }
            self.dashboard_ui.update_weather_display(weather_dict)
        
        logger.debug(f"Weather data updated: {getattr(weather_data, 'location', 'Unknown')} - {getattr(weather_data, 'temperature', 'N/A')}°")

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
                if self.weather_service and self.dashboard_ui and self.current_weather:
                    # Get location from current weather data
                    location = getattr(self.current_weather, 'location', 'New York')
                    weather_data = self.weather_service.get_weather(location)
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

            # Stop background updates
            self.is_running = False

            # Database cleanup (SQLite connections are auto-managed)
            if self.database:
                logger.info("Database cleanup completed")

            # Cleanup UI
            if self.dashboard_ui:
                self.dashboard_ui.cleanup()
            
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

            # Database cleanup handled automatically by SQLite
            if self.database:
                logger.info("Database cleanup completed")

            logger.info("Application cleanup completed")

        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
            # Database cleanup handled automatically by SQLite


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
