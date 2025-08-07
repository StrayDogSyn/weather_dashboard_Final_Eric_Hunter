"""Async Main Application for Weather Dashboard.

Provides fast startup with progressive loading using AsyncLoader and AsyncServiceManager.
This replaces the synchronous main.py with an async architecture for better performance.
"""

import asyncio
import logging
import os
import sys
import time
from pathlib import Path
from typing import Optional, Dict, Any

# Add src directory to path
src_path = Path(__file__).parent
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

# Environment setup
from dotenv import load_dotenv
load_dotenv()

# Async services
from services.async_service_manager import AsyncServiceManager
from services.async_loader import LoadingResult
from ui.components.progressive_loader import ProgressiveLoader


class AsyncWeatherApp:
    """Async Weather Dashboard Application.
    
    Provides fast startup with progressive loading and better user experience.
    """
    
    def __init__(self):
        """Initialize the async weather application."""
        self.logger = logging.getLogger(__name__)
        
        # Application state
        self.is_running = False
        self.startup_time = 0.0
        
        # Services
        self.service_manager: Optional[AsyncServiceManager] = None
        self.progressive_loader: Optional[ProgressiveLoader] = None
        
        # UI components
        self.root = None
        self.dashboard = None
        
        # Loading state
        self.loading_phase = "initializing"
        self.loading_progress = 0.0
        
        self.logger.info("AsyncWeatherApp initialized")
    
    def _setup_logging(self):
        """Setup logging configuration."""
        try:
            # Configure logging
            log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
            
            logging.basicConfig(
                level=getattr(logging, log_level),
                format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                handlers=[
                    logging.StreamHandler(sys.stdout),
                    logging.FileHandler('weather_dashboard.log', mode='a')
                ]
            )
            
            # Set specific logger levels
            logging.getLogger('urllib3').setLevel(logging.WARNING)
            logging.getLogger('requests').setLevel(logging.WARNING)
            
            self.logger.info(f"Logging configured with level: {log_level}")
            
        except Exception as e:
            print(f"Failed to setup logging: {e}")
            raise
    
    def _on_loading_progress(self, task_name: str, progress: float):
        """Handle loading progress updates.
        
        Args:
            task_name: Name of the loading task
            progress: Progress percentage (0.0 to 1.0)
        """
        try:
            self.loading_progress = progress
            
            # Update progressive loader if available
            if self.progressive_loader:
                self.progressive_loader.update_step(task_name, progress)
            
            # Log significant progress milestones
            if progress in [0.25, 0.5, 0.75, 1.0]:
                self.logger.info(f"Loading progress: {task_name} - {progress*100:.0f}%")
                
        except Exception as e:
            self.logger.error(f"Error updating loading progress: {e}")
    
    async def _create_skeleton_ui(self):
        """Create skeleton UI for immediate visual feedback."""
        try:
            self.logger.info("Creating skeleton UI")
            self.loading_phase = "ui_skeleton"
            
            # Import UI libraries
            try:
                import customtkinter as ctk
                ctk.set_appearance_mode("dark")
                ctk.set_default_color_theme("blue")
                ui_lib = ctk
                self.logger.info("Using CustomTkinter for UI")
            except ImportError:
                import tkinter as tk
                ui_lib = tk
                self.logger.warning("CustomTkinter not available, using Tkinter")
            
            # Create root window
            if hasattr(ui_lib, 'CTk'):
                self.root = ui_lib.CTk()
            else:
                self.root = ui_lib.Tk()
            
            # Configure window
            self.root.title("PROJECT CODEFRONT - Advanced Weather Intelligence System v3.5")
            self.root.geometry("1200x800")
            self.root.minsize(800, 600)
            
            # Center window
            self.root.update_idletasks()
            x = (self.root.winfo_screenwidth() // 2) - (1200 // 2)
            y = (self.root.winfo_screenheight() // 2) - (800 // 2)
            self.root.geometry(f"1200x800+{x}+{y}")
            
            # Create progressive loader
            self.progressive_loader = ProgressiveLoader(
                parent=self.root
            )
            
            # Show skeleton UI
            self.progressive_loader.show()
            
            # Update UI
            self.root.update()
            
            self.logger.info("Skeleton UI created successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to create skeleton UI: {e}")
            raise
    
    async def _initialize_services(self):
        """Initialize services asynchronously."""
        try:
            self.logger.info("Starting service initialization")
            self.loading_phase = "services"
            
            # Create service manager
            self.service_manager = AsyncServiceManager(
                progress_callback=self._on_loading_progress
            )
            
            # Initialize critical services first for fast startup
            self.logger.info("Initializing critical services")
            critical_results = await self.service_manager.initialize_critical_services()
            
            # Update UI with critical services loaded
            if self.progressive_loader:
                self.progressive_loader.update_step("Critical services loaded", 1.0)
                self.root.update()
            
            # Initialize remaining services in background
            self.logger.info("Initializing remaining services")
            all_results = await self.service_manager.initialize_all_services()
            
            # Log initialization summary
            summary = self.service_manager.get_initialization_summary()
            self.logger.info(f"Service initialization summary: {summary}")
            
            return all_results
            
        except Exception as e:
            self.logger.error(f"Service initialization failed: {e}")
            raise
    
    async def _create_dashboard(self):
        """Create the main dashboard UI."""
        try:
            self.logger.info("Creating main dashboard")
            self.loading_phase = "dashboard"
            
            # Update progressive loader
            if self.progressive_loader:
                self.progressive_loader.update_step("Loading dashboard...", 0.6)
                self.root.update()
            
            # Import dashboard
            from ui.professional_weather_dashboard import ProfessionalWeatherDashboard
            
            # Get required services
            weather_service = self.service_manager.get_service('weather_service')
            config_service = self.service_manager.get_service('config_service')
            
            if not weather_service:
                raise Exception("Weather service not available")
            
            # Create dashboard
            self.dashboard = ProfessionalWeatherDashboard(
                root=self.root,
                weather_service=weather_service,
                config_service=config_service
            )
            
            # Hide progressive loader and show dashboard
            if self.progressive_loader:
                await self.progressive_loader.transition_to_content()
            
            self.logger.info("Dashboard created successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to create dashboard: {e}")
            raise
    
    async def _load_initial_data(self):
        """Load initial weather data."""
        try:
            self.logger.info("Loading initial weather data")
            self.loading_phase = "data"
            
            # Update progressive loader
            if self.progressive_loader:
                self.progressive_loader.update_step("Loading weather data...", 0.8)
                self.root.update()
            
            # Get weather service
            weather_service = self.service_manager.get_service('weather_service')
            if not weather_service:
                self.logger.warning("Weather service not available for initial data load")
                return
            
            # Load default location data (London)
            try:
                # This will be loaded asynchronously in the background
                # The dashboard will handle the actual data loading
                self.logger.info("Initial data loading delegated to dashboard")
                
            except Exception as e:
                self.logger.warning(f"Failed to load initial data: {e}")
                # Continue without initial data
            
        except Exception as e:
            self.logger.error(f"Error during initial data loading: {e}")
            # Don't raise - this is not critical for startup
    
    async def _startup_sequence(self):
        """Execute the complete startup sequence."""
        start_time = time.time()
        
        try:
            self.logger.info("Starting async application startup")
            
            # Phase 1: Create skeleton UI (immediate feedback)
            await self._create_skeleton_ui()
            
            # Phase 2: Initialize services (parallel loading)
            service_results = await self._initialize_services()
            
            # Phase 3: Create dashboard (with loaded services)
            await self._create_dashboard()
            
            # Phase 4: Load initial data (background)
            await self._load_initial_data()
            
            # Startup complete
            self.startup_time = time.time() - start_time
            self.is_running = True
            self.loading_phase = "complete"
            
            self.logger.info(f"Async startup completed in {self.startup_time:.2f}s")
            
            # Log startup summary
            summary = self.service_manager.get_initialization_summary()
            self.logger.info(f"Startup summary: {summary}")
            
        except Exception as e:
            self.logger.error(f"Startup sequence failed: {e}")
            raise
    
    def _handle_window_close(self):
        """Handle window close event."""
        try:
            self.logger.info("Application closing")
            
            # Cleanup services
            if self.service_manager:
                self.service_manager.cleanup()
            
            # Cleanup progressive loader
            if self.progressive_loader:
                self.progressive_loader.destroy()
            
            # Destroy root window
            if self.root:
                self.root.quit()
                self.root.destroy()
            
            self.is_running = False
            self.logger.info("Application closed successfully")
            
        except Exception as e:
            self.logger.error(f"Error during application close: {e}")
    
    async def run_async(self):
        """Run the application asynchronously."""
        try:
            # Setup logging
            self._setup_logging()
            
            # Execute startup sequence
            await self._startup_sequence()
            
            # Setup window close handler
            if self.root:
                self.root.protocol("WM_DELETE_WINDOW", self._handle_window_close)
            
            # Run main loop
            self.logger.info("Starting main application loop")
            
            # Use async-friendly main loop
            while self.is_running and self.root:
                try:
                    self.root.update()
                    await asyncio.sleep(0.01)  # Small delay to prevent blocking
                except Exception as e:
                    if "invalid command name" in str(e).lower():
                        # Window was destroyed
                        break
                    else:
                        self.logger.error(f"Error in main loop: {e}")
                        break
            
            self.logger.info("Application main loop ended")
            
        except Exception as e:
            self.logger.error(f"Application run failed: {e}")
            raise
        finally:
            # Ensure cleanup
            self._handle_window_close()
    
    def run(self):
        """Run the application (sync wrapper for async run)."""
        try:
            # Run the async application
            asyncio.run(self.run_async())
        except KeyboardInterrupt:
            self.logger.info("Application interrupted by user")
        except Exception as e:
            self.logger.error(f"Application failed: {e}")
            raise


def main():
    """Main entry point for the async weather dashboard."""
    try:
        print("Starting PROJECT CODEFRONT - Advanced Weather Intelligence System...")
        
        # Create and run async application
        app = AsyncWeatherApp()
        app.run()
        
    except Exception as e:
        print(f"Failed to start application: {e}")
        logging.error(f"Application startup failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()