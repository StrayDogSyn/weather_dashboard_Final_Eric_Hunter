#!/usr/bin/env python3
"""
Weather Dashboard Application - Main Entry Point (Dependency Injection Refactored)

This is the main entry point for the Weather Dashboard application.
It demonstrates the BEFORE/AFTER pattern for dependency injection,
replacing tight coupling with proper dependency injection patterns.

Author: Eric Hunter (Cortana Builder Agent)
Version: 3.0.0 (Dependency Injection Implementation)
"""

import asyncio
import sys
import os
from pathlib import Path
import logging
from typing import Optional

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import dependency injection infrastructure
from src.core.interfaces import (
    IWeatherService, IDatabase, ICacheService, IConfigurationService,
    ILoggingService, IGeminiService, IGitHubService, ISpotifyService
)
from src.core.dependency_container import get_container, set_container, DependencyContainer
from src.core.service_registry import (
    get_service_registry, configure_for_production, configure_for_development, configure_for_testing
)

# Import UI components
import customtkinter as ctk
from src.ui.dashboard_ui import HunterDashboardUI


class WeatherDashboardApp:
    """Main application class for the Weather Dashboard (Dependency Injection Refactored).
    
    BEFORE: This class used to directly instantiate services, creating tight coupling:
    - self.weather_service = OpenWeatherService()  # ❌ Tight coupling
    - self.cache = MemoryCache()                   # ❌ Hard to test
    - self.database = SQLiteDatabase("weather.db") # ❌ No configuration
    
    AFTER: Now uses dependency injection with interfaces:
    - Services are injected through constructor or resolved from container
    - Interface-based design enables easy testing and swapping implementations
    - Configuration-driven service setup with proper lifetime management
    """
    
    def __init__(self, environment: str = 'production'):
        """Initialize the Weather Dashboard application with dependency injection.
        
        Args:
            environment: Application environment ('production', 'development', 'testing')
        """
        self.environment = environment
        self.container = get_container()
        self.service_registry = get_service_registry()
        
        # Services will be injected via dependency container
        self._config_service: Optional[IConfigurationService] = None
        self._logger: Optional[ILoggingService] = None
        self._database: Optional[IDatabase] = None
        self._weather_service: Optional[IWeatherService] = None
        self._cache_service: Optional[ICacheService] = None
        self._gemini_service: Optional[IGeminiService] = None
        self._github_service: Optional[IGitHubService] = None
        self._spotify_service: Optional[ISpotifyService] = None
        
        self.ui = None
        self.root = None
        
        # Configure services based on environment
        self._configure_services()
        
        # Resolve core services
        self._resolve_core_services()
        
        self._logger.info("Weather Dashboard Application initializing with dependency injection",
                         environment=environment)

    def _configure_services(self):
        """Configure services based on environment using dependency injection.
        
        This method demonstrates the new service configuration approach:
        - Environment-specific service registration
        - Proper service lifetime management
        - Interface-based service resolution
        """
        try:
            if self.environment == 'production':
                configure_for_production(
                    config_path=None,  # Use default config
                    database_path=None,  # Use default database
                    cache_dir=None  # Use default cache directory
                )
            elif self.environment == 'development':
                configure_for_development(
                    config_path=None,
                    use_mock_external=True  # Use mock external services for development
                )
            elif self.environment == 'testing':
                configure_for_testing()
            else:
                raise ValueError(f"Unknown environment: {self.environment}")
            
            # Validate service configuration
            validation_results = self.service_registry.validate_configuration()
            if not validation_results['is_valid']:
                raise RuntimeError(f"Service configuration validation failed: {validation_results['errors']}")
            
        except Exception as e:
            print(f"Error configuring services: {e}")
            raise
    
    def _resolve_core_services(self):
        """Resolve core services from the dependency container.
        
        This method demonstrates the new service resolution approach:
        - Services are resolved from container instead of directly instantiated
        - Interface-based resolution enables easy testing and configuration
        - Proper error handling for missing services
        """
        try:
            # Resolve core services through dependency injection
            self._config_service = self.container.resolve(IConfigurationService)
            self._logger = self.container.resolve(ILoggingService)
            self._database = self.container.resolve(IDatabase)
            self._weather_service = self.container.resolve(IWeatherService)
            self._cache_service = self.container.resolve(ICacheService)
            
            # Resolve external services
            self._gemini_service = self.container.resolve(IGeminiService)
            self._github_service = self.container.resolve(IGitHubService)
            self._spotify_service = self.container.resolve(ISpotifyService)
            
            self._logger.info("All core services resolved successfully through dependency injection")
            
        except Exception as e:
            print(f"Error resolving services: {e}")
            raise

    def initialize_ui(self):
        """Initialize the user interface with injected dependencies.
        
        BEFORE: UI received concrete service instances:
        - HunterDashboardUI(weather_service=OpenWeatherService(), ...)
        
        AFTER: UI receives interface-based services:
        - HunterDashboardUI(weather_service=IWeatherService, ...)
        """
        try:
            self._logger.info("Initializing UI with dependency injection...")
            
            # Set CustomTkinter appearance
            ctk.set_appearance_mode("dark")
            ctk.set_default_color_theme("blue")
            
            # Create main window
            self.root = ctk.CTk()
            self.root.title("Hunter Weather Dashboard (DI)")
            self.root.geometry("1400x900")
            
            # Initialize dashboard UI with injected services
            # Note: This demonstrates interface-based dependency injection
            self.ui = HunterDashboardUI(
                root=self.root,
                weather_service=self._weather_service,  # ✅ Injected IWeatherService
                database=self._database,                # ✅ Injected IDatabase
                settings=self._config_service.get_all_settings(),  # ✅ From IConfigurationService
                github_service=self._github_service     # ✅ Injected IGitHubService
            )
            
            self._logger.info("UI initialized successfully with dependency injection")
            
        except Exception as e:
            self._logger.error(f"Error initializing UI: {e}")
            raise

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
        """Setup application-wide event handlers with dependency injection.
        
        This method demonstrates how event handling works with injected services:
        - Uses injected logger instead of global logger
        - Proper error handling with dependency-injected services
        """
        try:
            # Setup window close event
            self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
            
            # Setup initial weather data
            if self._weather_service:
                initial_weather = self._weather_service.get_weather("New York")
                if initial_weather:
                    self._on_weather_update(initial_weather)
            
            self._logger.info("Event handlers setup completed")
        except Exception as e:
            self._logger.error(f"Failed to setup event handlers: {e}")

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
        Run the weather dashboard application with dependency injection.
        
        This method demonstrates the new application lifecycle:
        - Services are already configured and resolved during initialization
        - UI is initialized with injected dependencies
        - Proper error handling with injected logging service

        Returns:
            int: Exit code (0 for success, 1 for error)
        """
        try:
            self._logger.info("Starting Weather Dashboard Application with dependency injection")

            # Initialize UI (services are already resolved)
            self.initialize_ui()

            # Setup event handlers
            self._setup_event_handlers()

            # Show splash screen or welcome message
            self._show_welcome_message()

            # Start main event loop
            self._logger.info("Starting main application loop")
            self.root.mainloop()

            self._logger.info("Application closed successfully")
            return 0

        except KeyboardInterrupt:
            self._logger.info("Application interrupted by user")
            return 0
        except Exception as e:
            self._logger.error(f"Fatal application error: {e}")
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
        """Cleanup application resources with dependency injection.
        
        This method demonstrates proper resource cleanup with dependency injection:
        - Uses injected services for logging and cleanup
        - Proper disposal of dependency container resources
        """
        try:
            # Close database through injected service
            if self._database:
                # Note: IDatabase interface should include a close method
                # For now, we'll handle this gracefully
                try:
                    if hasattr(self._database, 'close'):
                        self._database.close()
                    self._logger.info("Database cleanup completed through dependency injection")
                except Exception as e:
                    self._logger.warning(f"Error closing database: {e}")
            
            # Clear cache through injected service
            if self._cache_service:
                try:
                    self._cache_service.clear_all()
                    self._logger.info("Cache cleared through dependency injection")
                except Exception as e:
                    self._logger.warning(f"Error clearing cache: {e}")

            # Reset dependency container for clean shutdown
            from src.core.dependency_container import reset_container
            reset_container()

            self._logger.info("Application cleanup completed with dependency injection")

        except Exception as e:
            if self._logger:
                self._logger.error(f"Error during cleanup: {e}")
            else:
                print(f"Error during cleanup: {e}")
            # Database cleanup handled automatically by SQLite


def main() -> int:
    """
    Application entry point with dependency injection.

    This function demonstrates the new application startup pattern:
    - Environment-based configuration
    - Dependency injection container setup
    - Proper error handling and logging
    """
    import argparse
    
    # Parse command line arguments for environment configuration
    parser = argparse.ArgumentParser(description='Weather Dashboard with Dependency Injection')
    parser.add_argument('--env', choices=['production', 'development', 'testing'], 
                       default='production', help='Application environment')
    parser.add_argument('--debug', action='store_true', help='Enable debug logging')
    
    args = parser.parse_args()
    
    try:
        # Create application data directory if it doesn't exist
        app_data_dir = Path.home() / ".weather_dashboard"
        app_data_dir.mkdir(exist_ok=True)

        print("=" * 50)
        print("Weather Dashboard Application Starting (Dependency Injection)")
        print(f"Environment: {args.env}")
        print("=" * 50)

        # Create and run the application with dependency injection
        app = WeatherDashboardApp(environment=args.env)
        exit_code = app.run()

        print("=" * 50)
        print("Weather Dashboard Application Finished")
        print("=" * 50)

        return exit_code

    except Exception as e:
        print(f"Fatal error in main: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
