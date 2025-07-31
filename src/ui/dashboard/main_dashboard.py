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
from ..components.secure_api_manager import SecureAPIManager
from ..theme import DataTerminalTheme
from .weather_display_enhancer import WeatherDisplayEnhancer
from .ui_components import UIComponentsMixin
from .tab_manager import TabManagerMixin
from .weather_handler import WeatherHandlerMixin
# Puscifer audio integration removed
# Spotify integration removed


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
        
        # Initialize attributes
        self.auto_refresh_timer_id = None
        self._running = True
        self._scheduled_callbacks = set()  # Track scheduled after() calls
        
        # Add reference storage for callbacks
        self._callback_refs = []
        self._is_closing = False
        
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
        
        # Ensure weather labels exist after layout is set up
        try:
            self.logger.debug("Ensuring weather labels exist...")
            self._ensure_weather_labels_exist()
            self.logger.debug("Weather labels ensured successfully")
        except Exception as e:
            self.logger.exception(f"Error ensuring weather labels: {e}")
            # Don't raise here, labels can be created later
        
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
            self.protocol("WM_DELETE_WINDOW", self._on_user_close)
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
        
        # Puscifer audio system removed
        
        # Spotify integration removed
        
        self.logger.info("Professional Weather Dashboard initialized")
    
    # Puscifer audio setup methods removed
    
    # Spotify initialization method removed
    
    # Puscifer setup methods removed
    
    def _safe_initial_setup(self):
        """Safe initialization without problematic components"""
        try:
            # Set initial status
            self.logger.info("Setting up initial dashboard state...")
            
            # Load default weather if service is available
            if hasattr(self, 'weather_service') and self.weather_service:
                try:
                    # Use a simple, safe async call
                    self.after(500, self._safe_load_default_weather)
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
                # Use the weather handler mixin methods if available
                if hasattr(self, '_perform_weather_update'):
                    self.logger.info("Triggering weather update...")
                    self._perform_weather_update()
                else:
                    # Fallback: directly get weather data
                    self.logger.info("Getting weather data directly...")
                    weather_data = self.weather_service.get_current_weather(self.current_city)
                    if weather_data:
                        self.update_weather_display(weather_data)
                        self.logger.info("Weather data loaded successfully")
                    else:
                        self.logger.warning("No weather data received")
                
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
    
    def _ensure_weather_labels_exist(self):
        """Ensure all weather display labels exist"""
        try:
            # Find the weather display container
            weather_container = None
            for attr_name in ['weather_frame', 'main_weather_frame', 'weather_display']:
                if hasattr(self, attr_name):
                    weather_container = getattr(self, attr_name)
                    break
                    
            if not weather_container:
                self.logger.warning("No weather container found")
                return
                
            # Create missing labels
            if not hasattr(self, 'temp_label'):
                self.temp_label = ctk.CTkLabel(
                    weather_container,
                    text="--°C",
                    font=ctk.CTkFont(size=48, weight="bold"),
                    text_color="#00FFB3"
                )
                # Position appropriately in your layout
                
            if not hasattr(self, 'condition_label'):
                self.condition_label = ctk.CTkLabel(
                    weather_container,
                    text="Loading...",
                    font=ctk.CTkFont(size=16),
                    text_color="#B0B0B0"
                )
                
        except Exception as e:
            self.logger.error(f"Failed to ensure weather labels: {e}")
    
    def _ensure_weather_display_components(self):
        """Ensure weather display components exist"""
        try:
            # Call the new method to ensure labels exist
            self._ensure_weather_labels_exist()
            
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
        """Update main weather display with proper data handling"""
        try:
            self.logger.info(f"Updating weather display with data: {weather_data}")
            
            if not weather_data:
                self.logger.warning("No weather data provided")
                return
                
            # Update temperature - handle different possible field names
            temperature = None
            for temp_field in ['temperature', 'temp', 'current_temp']:
                temperature = weather_data.get(temp_field)
                if temperature is not None:
                    break
                    
            if temperature is not None:
                # Update main temperature display
                if hasattr(self, 'temp_label'):
                    self.temp_label.configure(text=f"{temperature:.1f}°C")
                
                # Update any other temperature displays
                temp_elements = ['main_temp_label', 'current_temp_label', 'weather_temp']
                for element_name in temp_elements:
                    if hasattr(self, element_name):
                        element = getattr(self, element_name)
                        if hasattr(element, 'configure'):
                            element.configure(text=f"{temperature:.1f}°C")
            
            # Update condition/description
            condition = weather_data.get('description') or weather_data.get('condition', 'Unknown')
            if hasattr(self, 'condition_label'):
                self.condition_label.configure(text=condition)
                
            # Update feels like
            feels_like = weather_data.get('feels_like')
            if feels_like and hasattr(self, 'feels_like_label'):
                self.feels_like_label.configure(text=f"Feels like {feels_like:.1f}°C")
                
            # Update other weather info
            humidity = weather_data.get('humidity')
            if humidity and hasattr(self, 'humidity_label'):
                self.humidity_label.configure(text=f"Humidity {humidity}%")
                
            # Store current weather data for other components
            self.current_weather_data = weather_data
            
            self.logger.info("✅ Weather display updated successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to update weather display: {e}")
            self.logger.error(f"Weather data was: {weather_data}")
    
    def after(self, ms, func=None, *args):
        """Override after method with proper reference handling."""
        # Check if we're closing (handle case where attribute doesn't exist yet)
        is_closing = getattr(self, '_is_closing', False)
        
        if func is not None and not is_closing:
            # Store reference to prevent garbage collection
            if hasattr(self, '_callback_refs'):
                self._callback_refs.append(func)
                # Clean old references periodically
                if len(self._callback_refs) > 100:
                    self._callback_refs = self._callback_refs[-50:]
        
        try:
            return super().after(ms, func, *args)
        except Exception as e:
            error_msg = str(e).lower()
            if "invalid command name" in error_msg:
                # Suppress DPI scaling errors
                if hasattr(self, 'logger'):
                    self.logger.debug(f"Suppressed CustomTkinter internal error: {e}")
                return None
            else:
                raise e
    
    def after_cancel(self, id):
        """Override after_cancel to remove from tracking set."""
        try:
            super().after_cancel(id)
            if hasattr(self, '_scheduled_callbacks'):
                self._scheduled_callbacks.discard(id)
        except Exception as e:
            # Callback may have already executed or been cancelled
            if hasattr(self, '_scheduled_callbacks'):
                self._scheduled_callbacks.discard(id)
            self.logger.debug(f"after_cancel error (ignored): {e}")
    
    def _cleanup_child_components(self):
        """Recursively cleanup all child components that have cleanup methods."""
        def cleanup_widget(widget):
            try:
                # Check if widget has cleanup method and call it
                if hasattr(widget, 'cleanup') and callable(getattr(widget, 'cleanup')):
                    widget.cleanup()
                    self.logger.debug(f"Cleaned up component: {widget.__class__.__name__}")
                
                # Recursively cleanup children
                if hasattr(widget, 'winfo_children'):
                    for child in widget.winfo_children():
                        cleanup_widget(child)
            except Exception as e:
                self.logger.debug(f"Error cleaning up widget {widget.__class__.__name__}: {e}")
        
        try:
            cleanup_widget(self)
        except Exception as e:
            self.logger.error(f"Error during child component cleanup: {e}")
    
    def destroy(self):
        """Proper cleanup on window close."""
        self._is_closing = True
        
        try:
            # Cancel all pending callbacks safely
            for widget in self.winfo_children():
                try:
                    widget.destroy()
                except:
                    pass
            
            # Clear callback references
            self._callback_refs.clear()
            
            # Cleanup services
            if hasattr(self, 'weather_service'):
                self.weather_service.clear_cache()
            
        except Exception as e:
            self.logger.error(f"Cleanup error: {e}")
        finally:
            super().destroy()
    
    def _on_user_close(self):
        """Handle user-initiated window close - ask for confirmation"""
        try:
            import tkinter.messagebox as msgbox
            if msgbox.askokcancel("Quit", "Do you want to quit the Weather Dashboard?"):
                self._on_closing()
        except Exception as e:
            self.logger.error(f"Error in user close handler: {e}")
            # If there's an error with the dialog, just close
            self._on_closing()
     
    def cleanup(self):
        """Cleanup resources"""
        try:
            self.logger.info("Starting application cleanup...")
            
            # Cancel any pending after callbacks
            for child in self.winfo_children():
                try:
                    child.destroy()
                except:
                    pass
            
            # Audio cleanup removed
            
            # Stop services
            if hasattr(self, 'ai_service'):
                self.ai_service.cleanup()
            
            self.logger.info("Application cleanup completed")
            
        except Exception as e:
            self.logger.error(f"Cleanup error: {e}")
    
    def _on_closing(self):
        """Handle application closing - cleanup timers and resources."""
        try:
            # Cancel auto-refresh timer
            if hasattr(self, 'auto_refresh_timer_id') and self.auto_refresh_timer_id:
                self.after_cancel(self.auto_refresh_timer_id)
                self.auto_refresh_timer_id = None
                self.logger.info("Auto-refresh timer cancelled")
            
            # Cancel all tracked scheduled callbacks
            if hasattr(self, '_scheduled_callbacks'):
                cancelled_count = 0
                for callback_id in list(self._scheduled_callbacks):
                    try:
                        self.after_cancel(callback_id)
                        cancelled_count += 1
                    except Exception:
                        pass  # Callback may have already executed
                self._scheduled_callbacks.clear()
                if cancelled_count > 0:
                    self.logger.info(f"Cancelled {cancelled_count} pending callbacks")
            
            # Call the new cleanup method
            self.cleanup()
            
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