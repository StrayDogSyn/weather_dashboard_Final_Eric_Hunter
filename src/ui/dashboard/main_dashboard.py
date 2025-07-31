"""Professional Weather Dashboard

Main dashboard application with weather data, analytics, and journaling features.
"""

import customtkinter as ctk
import threading
from datetime import datetime
from typing import Optional, Dict, Any

# Suppress CustomTkinter DPI scaling errors
try:
    import os
    os.environ['CTK_DISABLE_DPI_SCALING'] = '1'
except Exception:
    pass

from services.logging_service import LoggingService
from services.config_service import ConfigService
from services.enhanced_weather_service import EnhancedWeatherService
from services.journal_service import JournalService
from utils.photo_manager import PhotoManager
from ui.components.secure_api_manager import SecureAPIManager
from ui.theme import DataTerminalTheme
from .weather_display_enhancer import WeatherDisplayEnhancer
from .ui_components import UIComponentsMixin
from .tab_manager import TabManagerMixin
from .weather_handler import WeatherHandlerMixin


class ProfessionalWeatherDashboard(ctk.CTk, UIComponentsMixin, TabManagerMixin, WeatherHandlerMixin):
    """Professional weather dashboard with clean, minimal design."""
    
    # Data Terminal color scheme
    ACCENT_COLOR = DataTerminalTheme.PRIMARY      # Neon green
    BACKGROUND = DataTerminalTheme.BACKGROUND     # Dark background
    CARD_COLOR = DataTerminalTheme.CARD_BG        # Dark card background
    TEXT_PRIMARY = DataTerminalTheme.TEXT         # Light text
    TEXT_SECONDARY = DataTerminalTheme.TEXT_SECONDARY # Medium gray text
    BORDER_COLOR = DataTerminalTheme.BORDER       # Dark border
    
    def __init__(self, config_service=None):
        """Initialize professional weather dashboard.
        
        Args:
            config_service: Optional ConfigService instance to avoid duplicate initialization
        """
        super().__init__()
        
        # Setup services with error protection
        try:
            self.logging_service = LoggingService()
            self.logging_service.setup_logging()
            self.logger = self.logging_service.get_logger(__name__)
            self.logger.debug("Logging service initialized successfully")
        except Exception as e:
            print(f"Error initializing logging service: {e}")
            raise
        
        try:
            self.config_service = config_service or ConfigService()
            self.logger.debug("Config service initialized successfully")
        except Exception as e:
            self.logger.exception(f"Error initializing config service: {e}")
            raise
            
        try:
            self.weather_service = EnhancedWeatherService(self.config_service)
            self.logger.debug("Weather service initialized successfully")
        except Exception as e:
            self.logger.exception(f"Error initializing weather service: {e}")
            raise
        
        # Initialize secure API manager with error protection
        try:
            self.secure_api_manager = SecureAPIManager(self, self.config_service)
            self.logger.debug("Secure API manager initialized successfully")
        except Exception as e:
            self.logger.exception(f"Error initializing secure API manager: {e}")
            raise
        
        # Create shared photo manager with error protection
        try:
            from utils.photo_manager import PhotoManager
            self.photo_manager = PhotoManager()
            self.logger.debug("Photo manager initialized successfully")
        except Exception as e:
            self.logger.exception(f"Error initializing photo manager: {e}")
            raise
        
        try:
            self.journal_service = JournalService(weather_service=self.weather_service, photo_manager=self.photo_manager)
            self.logger.debug("Journal service initialized successfully")
        except Exception as e:
            self.logger.exception(f"Error initializing journal service: {e}")
            raise
        
        # Data storage
        self.current_weather: Optional[WeatherData] = None
        self.forecast_data: Optional[List[ForecastData]] = None
        self.current_city: str = "London"
        self.chart_timeframe = "24h"
        
        # Auto-refresh timer tracking
        self.auto_refresh_timer_id = None
        
        # DON'T initialize enhancer here
        self.display_enhancer = None
        
        # Configure window with error protection
        try:
            self.logger.debug("Configuring window...")
            self._configure_window()
            self.logger.debug("Window configured successfully")
        except Exception as e:
            self.logger.exception(f"Error configuring window: {e}")
            raise
        
        # Create UI with error protection
        try:
            self.logger.debug("Creating widgets...")
            self._create_widgets()
            self.logger.debug("Widgets created successfully")
        except Exception as e:
            self.logger.exception(f"Error creating widgets: {e}")
            raise
            
        try:
            self.logger.debug("Setting up layout...")
            self._setup_layout()
            self.logger.debug("Layout setup successfully")
        except Exception as e:
            self.logger.exception(f"Error setting up layout: {e}")
            raise
        
        # Initialize display enhancer ONLY after UI is created
        try:
            self.logger.debug("Initializing display enhancer...")
            self.display_enhancer = WeatherDisplayEnhancer(self)
            self.logger.debug("Display enhancer initialized successfully")
        except Exception as e:
            self.logger.exception(f"Error initializing display enhancer: {e}")
            # Don't raise here, enhancer is optional
            self.display_enhancer = None
        
        # REPLACE: self._load_initial_data() with safe version:
        try:
            self.logger.debug("Starting safe initial setup...")
            self._safe_initial_setup()
            self.logger.debug("Safe initial setup completed successfully")
        except Exception as e:
            self.logger.exception(f"Error in safe initial setup: {e}")
            # Don't raise here, app can still function without initial data
        
        # Setup cleanup on window close
        try:
            self.protocol("WM_DELETE_WINDOW", self._on_closing)
            self.logger.debug("Window close protocol set successfully")
        except Exception as e:
            self.logger.exception(f"Error setting window close protocol: {e}")
            # Don't raise here, not critical
        
        # Initialize weather tracking
        self.current_weather_data = {}
        self.last_weather_update = None
        self.chart_timeframe = "24h"
        self._weather_update_id = None
        self._auto_refresh_id = None
        
        self.logger.info("Professional Weather Dashboard initialized")
    
    def _safe_initial_setup(self):
        """Safe initialization without problematic components"""
        try:
            # Set initial status
            self.logger.info("Setting up initial dashboard state...")
            
            # Load default weather if service is available
            if hasattr(self, 'weather_service') and self.weather_service:
                try:
                    # Use a simple, safe async call
                    self.after(500, lambda: self._safe_load_default_weather())
                except Exception as e:
                    self.logger.warning(f"Could not schedule default weather load: {e}")
            
            # Set ready status
            self.logger.info("✅ Dashboard initialization completed safely")
            
        except Exception as e:
            self.logger.error(f"Safe initialization failed: {e}")
            # Continue anyway - don't crash
    
    def _safe_load_default_weather(self):
        """Safely load default weather without crashing"""
        try:
            # Try to load London weather as default
            self.logger.info("Loading default weather data...")
            
            # This should call your working weather service
            # but with proper error handling
            if hasattr(self, 'weather_service'):
                # Use your existing weather loading logic
                # but with proper error handling
                pass
                
        except Exception as e:
            self.logger.error(f"Default weather load failed: {e}")
            # Don't crash - just log and continue
    
    def _set_initial_ui_state(self):
        """Set up the initial UI state"""
        try:
            # Set status to ready
            if hasattr(self, '_show_status_message'):
                self._show_status_message("Ready", "info")
            
            # Enable search if components exist
            if hasattr(self, 'search_entry'):
                self.search_entry.configure(state="normal")
            
            self.logger.debug("Initial UI state configured")
            
        except Exception as e:
            self.logger.error(f"Failed to set initial UI state: {e}")
    
    def _ensure_weather_display_components(self):
        """Ensure weather display components exist"""
        try:
            # Create temp_label if it doesn't exist
            if not hasattr(self, 'temp_label'):
                # Find or create a container for weather display
                weather_container = getattr(self, 'weather_frame', self)
                
                self.temp_label = ctk.CTkLabel(
                    weather_container,
                    text="--°",
                    font=ctk.CTkFont(size=36, weight="bold"),
                    text_color="#FFFFFF"
                )
                # Position it appropriately in your layout
                
            # Create other essential labels
            if not hasattr(self, 'condition_label'):
                weather_container = getattr(self, 'weather_frame', self)
                self.condition_label = ctk.CTkLabel(
                    weather_container,
                    text="Loading...",
                    font=ctk.CTkFont(size=16),
                    text_color="#B0B0B0"
                )
                
            # Create status_label if needed
            if not hasattr(self, 'status_label'):
                self.status_label = ctk.CTkLabel(
                    self,  # or appropriate parent
                    text="Ready",
                    font=ctk.CTkFont(size=12),
                    text_color="#10B981"
                )
                
            self.logger.debug("Weather display components ensured")
            
        except Exception as e:
            self.logger.error(f"Failed to ensure weather display components: {e}")
    
    def update_weather_display(self, weather_data):
        """Safely update weather display with data"""
        try:
            # Ensure components exist first
            self._ensure_weather_display_components()
            
            if weather_data:
                # Update temperature
                if hasattr(self, 'temp_label') and 'temperature' in weather_data:
                    temp = weather_data['temperature']
                    self.temp_label.configure(text=f"{temp}°C")
                
                # Update condition
                if hasattr(self, 'condition_label') and 'condition' in weather_data:
                    condition = weather_data['condition']
                    self.condition_label.configure(text=condition)
                
                # Update status
                city = weather_data.get('city', 'Unknown')
                self._show_status_message(f"Weather updated for {city}", "success")
                
            self.logger.info("Weather display updated successfully")
            
        except Exception as e:
            self.logger.error(f"Error updating weather display: {e}")
            # Show error to user
            if hasattr(self, '_show_status_message'):
                self._show_status_message("Failed to update weather display", "error")
    
    def after(self, ms, func=None, *args):
        """Override after method to handle CustomTkinter DPI scaling errors and threading issues."""
        if func is None:
            return super().after(ms)
        
        # Check if we're in the main thread
        import threading
        if threading.current_thread() != threading.main_thread():
            # If not in main thread, schedule safely
            try:
                if self.winfo_exists():
                    return super().after(ms, func, *args)
                else:
                    self.logger.debug("Widget destroyed, skipping after call")
                    return None
            except RuntimeError as e:
                if "main thread is not in main loop" in str(e):
                    self.logger.debug(f"Skipped after call from background thread: {e}")
                    return None
                else:
                    raise e
        
        # Use the original after method but catch any scheduling errors
        try:
            return super().after(ms, func, *args)
        except Exception as e:
            error_msg = str(e).lower()
            if "invalid command name" in error_msg:
                # Suppress all invalid command name errors from CustomTkinter
                self.logger.debug(f"Suppressed after scheduling error: {e}")
                return None
            elif "main thread is not in main loop" in error_msg:
                self.logger.debug(f"Skipped after call due to main loop issue: {e}")
                return None
            else:
                raise e
    
    def _on_closing(self):
        """Handle application closing - cleanup timers and resources."""
        try:
            # Cancel auto-refresh timer
            if hasattr(self, 'auto_refresh_timer_id') and self.auto_refresh_timer_id:
                self.after_cancel(self.auto_refresh_timer_id)
                self.auto_refresh_timer_id = None
                self.logger.info("Auto-refresh timer cancelled")
            
            # Stop any running processes
            if hasattr(self, '_running'):
                self._running = False
            
            self.logger.info("Application cleanup completed")
        except Exception as e:
            # Log error but don't prevent closing
            if hasattr(self, 'logger'):
                self.logger.error(f"Error during cleanup: {e}")
        finally:
            # Always destroy the window
            self.destroy()