"""Weather Dashboard - Main UI Component

Modern weather dashboard with Data Terminal aesthetic using CustomTkinter.
"""

import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime
import threading
from pathlib import Path

from ui.theme import DataTerminalTheme
from ui.components.weather_display import WeatherDisplayFrame
from ui.components.chart_display import ChartDisplayFrame
from ui.components.enhanced_search_bar import EnhancedSearchBarFrame as SearchBarFrame
from ui.components.loading_overlay import LoadingOverlay
from ui.components.status_bar import StatusBarFrame
from services.config_service import ConfigService
from services.weather_service import WeatherService, WeatherData
from services.logging_service import LoggingService

# Enhanced features availability check
try:
    from enhanced_search_bar import EnhancedSearchBarFrame
    from enhanced_weather_display import EnhancedWeatherDisplayFrame
    from enhanced_weather_service import EnhancedWeatherService
    ENHANCED_FEATURES_AVAILABLE = True
except ImportError:
    ENHANCED_FEATURES_AVAILABLE = False


class WeatherDashboard(ctk.CTk):
    """Main weather dashboard application window with enhanced features support."""
    
    def __init__(self, config_service: ConfigService, use_enhanced_features: bool = True):
        """Initialize the weather dashboard."""
        super().__init__()
        
        # Services
        self.config = config_service
        self.use_enhanced_features = use_enhanced_features and ENHANCED_FEATURES_AVAILABLE
        
        if self.use_enhanced_features:
            try:
                from enhanced_weather_service import EnhancedWeatherService
                self.weather_service = EnhancedWeatherService(config_service)
                self.logger = logging.getLogger('weather_dashboard.enhanced_ui')
            except ImportError:
                self.use_enhanced_features = False
                self.weather_service = WeatherService(config_service)
                self.logger = logging.getLogger('weather_dashboard.ui')
        else:
            self.weather_service = WeatherService(config_service)
            self.logger = logging.getLogger('weather_dashboard.ui')
        
        # State
        self.current_weather: Optional[WeatherData] = None
        self.current_location: Optional[str] = None
        self.is_loading = False
        
        # Setup UI
        self._setup_window()
        self._create_widgets()
        self._setup_layout()
        self._setup_bindings()
        
        # Load initial data
        self._load_initial_weather()
        
        self.logger.info("🎨 Weather Dashboard initialized")
    
    def _setup_window(self) -> None:
        """Configure main window properties with responsive design."""
        # Window configuration
        self.title("JTC Capstone Application")
        
        # Get screen dimensions for responsive design
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        
        # Calculate responsive window size (80% of screen for better UX)
        window_width = min(self.config.ui.window_width, int(screen_width * 0.8))
        window_height = min(self.config.ui.window_height, int(screen_height * 0.8))
        
        # Ensure minimum size requirements
        window_width = max(window_width, self.config.ui.min_width)
        window_height = max(window_height, self.config.ui.min_height)
        
        # Center the window on screen
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        
        # Set window geometry (centered by default)
        self.geometry(f"{window_width}x{window_height}+{x}+{y}")
        self.minsize(self.config.ui.min_width, self.config.ui.min_height)
        
        # Configure responsive grid weights
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        
        # Apply theme
        self.configure(fg_color=DataTerminalTheme.BACKGROUND)
        
        # Window icon (if available)
        try:
            icon_path = Path.cwd() / 'assets' / 'icon.ico'
            if icon_path.exists():
                self.iconbitmap(str(icon_path))
        except Exception:
            pass  # Icon not critical
        
        # Bind window resize events for responsive behavior
        self.bind('<Configure>', self._on_window_resize)
    
    def center_window(self) -> None:
        """Center the window on the screen."""
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f"{width}x{height}+{x}+{y}")
    
    def _on_window_resize(self, event) -> None:
        """Handle window resize events for responsive design."""
        # Only handle resize events for the main window
        if event.widget == self:
            # Get current window dimensions
            current_width = self.winfo_width()
            current_height = self.winfo_height()
            
            # Ensure minimum size constraints
            if current_width < self.config.ui.min_width or current_height < self.config.ui.min_height:
                new_width = max(current_width, self.config.ui.min_width)
                new_height = max(current_height, self.config.ui.min_height)
                self.geometry(f"{new_width}x{new_height}")
            
            # Update grid weights for responsive layout
            self.update_idletasks()
    
    def _create_widgets(self) -> None:
        """Create all UI widgets."""
        # Header with search
        self.header_frame = ctk.CTkFrame(
            self,
            **DataTerminalTheme.get_frame_style("main")
        )
        
        # Title
        self.title_label = ctk.CTkLabel(
            self.header_frame,
            text="⚡ Project CodeFront",
            **DataTerminalTheme.get_label_style("title")
        )
        
        # Search bar
        self.search_frame = SearchBarFrame(
            self.header_frame,
            on_search=self._on_city_search,
            on_suggestion_select=self._on_suggestion_select
        )
        
        # Status bar
        self.status_frame = ctk.CTkFrame(
            self.header_frame,
            **DataTerminalTheme.get_frame_style("default")
        )
        
        self.status_label = ctk.CTkLabel(
            self.status_frame,
            text="Ready",
            **DataTerminalTheme.get_label_style("caption")
        )
        
        self.last_update_label = ctk.CTkLabel(
            self.status_frame,
            text="",
            **DataTerminalTheme.get_label_style("caption")
        )
        
        # Main content area
        self.content_frame = ctk.CTkFrame(
            self,
            **DataTerminalTheme.get_frame_style("main")
        )
        
        # Weather display (left side)
        self.weather_display = WeatherDisplayFrame(
            self.content_frame,
            on_refresh=self._refresh_weather
        )
        
        # Chart display (right side)
        self.chart_display = ChartDisplayFrame(
            self.content_frame
        )
        
        # Loading overlay
        self.loading_overlay = LoadingOverlay(self)
    
    def _setup_layout(self) -> None:
        """Arrange widgets in the window with responsive design."""
        # Configure main window grid for responsive behavior
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)  # Content area expands
        
        # Header
        self.header_frame.grid(row=0, column=0, sticky="ew", padx=12, pady=(12, 8))
        self.header_frame.grid_columnconfigure(1, weight=1)
        
        # Header content with improved spacing
        self.title_label.grid(row=0, column=0, padx=(15, 25), pady=12, sticky="w")
        self.search_frame.grid(row=0, column=1, padx=12, pady=12, sticky="ew")
        
        # Status bar with responsive layout
        self.status_frame.grid(row=1, column=0, columnspan=2, sticky="ew", padx=12, pady=(8, 0))
        self.status_frame.grid_columnconfigure(1, weight=1)
        
        self.status_label.grid(row=0, column=0, padx=12, pady=6, sticky="w")
        self.last_update_label.grid(row=0, column=1, padx=12, pady=6, sticky="e")
        
        # Main content with responsive grid weights
        self.content_frame.grid(row=1, column=0, sticky="nsew", padx=12, pady=(8, 12))
        
        # Responsive content layout - left panel (weather) gets 40%, right panel (charts) gets 60%
        self.content_frame.grid_columnconfigure(0, weight=2, minsize=350)  # Weather display
        self.content_frame.grid_columnconfigure(1, weight=3, minsize=400)  # Chart display
        self.content_frame.grid_rowconfigure(0, weight=1)
        
        # Content layout with improved spacing
        self.weather_display.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        self.chart_display.grid(row=0, column=1, sticky="nsew", padx=(8, 0))
    
    def _setup_bindings(self) -> None:
        """Setup event bindings."""
        # Window events
        self.protocol("WM_DELETE_WINDOW", self._on_closing)
        
        # Keyboard shortcuts
        self.bind("<Control-r>", lambda e: self._refresh_weather())
        self.bind("<Control-q>", lambda e: self._on_closing())
        self.bind("<F5>", lambda e: self._refresh_weather())
        
        # Focus events
        self.bind("<Button-1>", self._on_click)
    
    def _load_initial_weather(self) -> None:
        """Load weather for default city."""
        default_city = self.config.app.default_city
        if default_city:
            self._fetch_weather(default_city)
        else:
            self._update_status("Enter a city name to get weather data", "info")
    
    def _on_city_search(self, query: str) -> None:
        """Handle city search."""
        if not query.strip():
            return
        
        self.logger.info(f"🔍 Searching for city: {query}")
        self._fetch_weather(query.strip())
    
    def _on_location_detect(self) -> None:
        """Handle location detection request (enhanced features only)."""
        if not self.use_enhanced_features:
            return
        
        self.logger.info("📍 Location detection requested")
        # For demo, use London as detected location
        self._fetch_weather("London", auto_detected=True)
    
    def _on_suggestion_select(self, city_data: Dict[str, str]) -> None:
        """Handle city suggestion selection."""
        city_name = city_data.get('name', '')
        if city_name:
            self.logger.info(f"📍 Selected city: {city_name}")
            self._fetch_weather(city_name)
    
    def _fetch_weather(self, city: str, auto_detected: bool = False) -> None:
        """Fetch weather data for a city."""
        if self.is_loading:
            return
        
        self.is_loading = True
        status_text = f"Fetching weather for {city}..."
        if auto_detected:
            status_text += " (auto-detected)"
        self._show_loading(status_text)
        
        # Run in background thread
        thread = threading.Thread(
            target=self._fetch_weather_thread,
            args=(city, auto_detected),
            daemon=True
        )
        thread.start()
    
    def _fetch_weather_thread(self, city: str, auto_detected: bool = False) -> None:
        """Fetch weather data in background thread."""
        try:
            if self.use_enhanced_features:
                # Fetch enhanced weather data
                weather_data = self.weather_service.get_enhanced_weather(city)
                try:
                    forecast_data = self.weather_service.get_forecast(city, days=5)
                except:
                    # Fallback to basic forecast if enhanced fails
                    basic_service = WeatherService(self.config)
                    forecast_data = basic_service.get_forecast(city, days=5)
            else:
                # Fetch current weather
                weather_data = self.weather_service.get_current_weather(city)
                
                # Fetch forecast for charts
                forecast_data = self.weather_service.get_forecast(city, days=5)
            
            # Update UI on main thread
            self.after(0, self._on_weather_success, weather_data, forecast_data, auto_detected)
            
        except Exception as e:
            self.logger.error(f"❌ Weather fetch failed: {e}")
            self.after(0, self._on_weather_error, str(e))
    
    def _on_weather_success(self, weather_data: WeatherData, forecast_data: List, auto_detected: bool = False) -> None:
        """Handle successful weather fetch."""
        self.current_weather = weather_data
        self.current_location = f"{weather_data.city}, {weather_data.country}"
        
        # Update displays
        self.weather_display.update_weather(weather_data)
        if forecast_data:
            self.chart_display.update_forecast(forecast_data)
        
        # Update search bar
        if hasattr(self.search_frame, 'set_current_location'):
            self.search_frame.set_current_location(self.current_location)
        elif hasattr(self.search_frame, 'set_current_city'):
            self.search_frame.set_current_city(self.current_location)
        
        # Update status
        status_text = f"Weather updated for {weather_data.city}"
        if auto_detected:
            status_text += " (auto-detected location)"
        if self.use_enhanced_features:
            status_text += " - Enhanced data loaded"
        
        self._update_status(status_text, "success")
        self._update_last_update()
        
        self._hide_loading()
        self.is_loading = False
        
        feature_type = "Enhanced" if self.use_enhanced_features else "Basic"
        self.logger.info(f"✅ {feature_type} weather display updated for {weather_data.city}")
    
    def _on_weather_error(self, error_message: str) -> None:
        """Handle weather fetch error."""
        self._update_status(f"Error: {error_message}", "error")
        self._hide_loading()
        self.is_loading = False
        
        # Show error dialog
        messagebox.showerror(
            "Weather Error",
            f"Failed to fetch weather data:\n\n{error_message}",
            parent=self
        )
    
    def _refresh_weather(self) -> None:
        """Refresh current weather data."""
        if self.current_weather:
            self._fetch_weather(self.current_weather.city)
        else:
            self._update_status("No city selected to refresh", "warning")
    
    def _show_loading(self, message: str) -> None:
        """Show loading overlay."""
        self.loading_overlay.show(message)
    
    def _hide_loading(self) -> None:
        """Hide loading overlay."""
        self.loading_overlay.hide()
    
    def _update_status(self, message: str, status_type: str = "info") -> None:
        """Update status bar message."""
        # Color based on status type
        colors = {
            "info": DataTerminalTheme.TEXT_SECONDARY,
            "success": DataTerminalTheme.SUCCESS,
            "warning": DataTerminalTheme.WARNING,
            "error": DataTerminalTheme.ERROR
        }
        
        color = colors.get(status_type, DataTerminalTheme.TEXT_SECONDARY)
        
        self.status_label.configure(
            text=message,
            text_color=color
        )
        
        # Auto-clear status after delay (except errors)
        if status_type != "error":
            self.after(5000, lambda: self.status_label.configure(
                text="Ready",
                text_color=DataTerminalTheme.TEXT_SECONDARY
            ))
    
    def _update_last_update(self) -> None:
        """Update last update timestamp."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.last_update_label.configure(text=f"Last update: {timestamp}")
    
    def _on_click(self, event) -> None:
        """Handle window click to remove focus from widgets."""
        self.focus_set()
    
    def _on_closing(self) -> None:
        """Handle window closing."""
        self.logger.info("🔌 Shutting down Weather Dashboard")
        
        try:
            # Save any pending data
            if hasattr(self.weather_service, '_save_cache'):
                self.weather_service._save_cache()
        except Exception as e:
            self.logger.warning(f"Error saving cache: {e}")
        
        self.destroy()
    
    def run(self) -> None:
        """Start the application main loop."""
        try:
            self.logger.info("🚀 Starting Weather Dashboard")
            self.mainloop()
        except KeyboardInterrupt:
            self.logger.info("⚡ Application interrupted by user")
        except Exception as e:
            self.logger.error(f"💥 Application crashed: {e}")
            raise
        finally:
            self.logger.info("👋 Weather Dashboard closed")