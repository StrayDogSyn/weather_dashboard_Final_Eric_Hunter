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

from .theme import DataTerminalTheme
from .components.weather_display import WeatherDisplayFrame
from .components.chart_display import ChartDisplayFrame
from .components.search_bar import SearchBarFrame
from .components.loading_overlay import LoadingOverlay
from ..services.config_service import ConfigService
from ..services.weather_service import WeatherService, WeatherData
from ..services.logging_service import LoggingService


class WeatherDashboard(ctk.CTk):
    """Main weather dashboard application window."""
    
    def __init__(self, config_service: ConfigService):
        """Initialize the weather dashboard."""
        super().__init__()
        
        # Services
        self.config = config_service
        self.weather_service = WeatherService(config_service)
        self.logger = logging.getLogger('weather_dashboard.ui')
        
        # State
        self.current_weather: Optional[WeatherData] = None
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
        """Configure main window properties."""
        # Window configuration
        self.title("Weather Dashboard - Data Terminal")
        self.geometry(f"{self.config.ui.window_width}x{self.config.ui.window_height}")
        self.minsize(800, 600)
        
        # Center window on screen
        self.center_window()
        
        # Configure grid
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
    
    def center_window(self) -> None:
        """Center the window on the screen."""
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f"{width}x{height}+{x}+{y}")
    
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
            text="⚡ WEATHER TERMINAL",
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
        """Arrange widgets in the window."""
        # Header
        self.header_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 5))
        self.header_frame.grid_columnconfigure(1, weight=1)
        
        # Header content
        self.title_label.grid(row=0, column=0, padx=(10, 20), pady=10, sticky="w")
        self.search_frame.grid(row=0, column=1, padx=10, pady=10, sticky="ew")
        
        # Status bar
        self.status_frame.grid(row=1, column=0, columnspan=2, sticky="ew", padx=10, pady=(5, 0))
        self.status_frame.grid_columnconfigure(1, weight=1)
        
        self.status_label.grid(row=0, column=0, padx=10, pady=5, sticky="w")
        self.last_update_label.grid(row=0, column=1, padx=10, pady=5, sticky="e")
        
        # Main content
        self.content_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=(5, 10))
        self.content_frame.grid_columnconfigure(0, weight=1)
        self.content_frame.grid_columnconfigure(1, weight=1)
        self.content_frame.grid_rowconfigure(0, weight=1)
        
        # Content layout
        self.weather_display.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
        self.chart_display.grid(row=0, column=1, sticky="nsew", padx=(5, 0))
    
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
        default_city = self.config.weather.default_city
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
    
    def _on_suggestion_select(self, city_data: Dict[str, str]) -> None:
        """Handle city suggestion selection."""
        city_name = city_data.get('name', '')
        if city_name:
            self.logger.info(f"📍 Selected city: {city_name}")
            self._fetch_weather(city_name)
    
    def _fetch_weather(self, city: str) -> None:
        """Fetch weather data for a city."""
        if self.is_loading:
            return
        
        self.is_loading = True
        self._show_loading(f"Fetching weather for {city}...")
        
        # Run in background thread
        thread = threading.Thread(
            target=self._fetch_weather_thread,
            args=(city,),
            daemon=True
        )
        thread.start()
    
    def _fetch_weather_thread(self, city: str) -> None:
        """Fetch weather data in background thread."""
        try:
            # Fetch current weather
            weather_data = self.weather_service.get_current_weather(city)
            
            # Fetch forecast for charts
            forecast_data = self.weather_service.get_forecast(city, days=5)
            
            # Update UI on main thread
            self.after(0, self._on_weather_success, weather_data, forecast_data)
            
        except Exception as e:
            self.logger.error(f"❌ Weather fetch failed: {e}")
            self.after(0, self._on_weather_error, str(e))
    
    def _on_weather_success(self, weather_data: WeatherData, forecast_data: List) -> None:
        """Handle successful weather fetch."""
        self.current_weather = weather_data
        
        # Update displays
        self.weather_display.update_weather(weather_data)
        self.chart_display.update_forecast(forecast_data)
        
        # Update search bar
        self.search_frame.set_current_city(f"{weather_data.city}, {weather_data.country}")
        
        # Update status
        self._update_status(f"Weather updated for {weather_data.city}", "success")
        self._update_last_update()
        
        self._hide_loading()
        self.is_loading = False
        
        self.logger.info(f"✅ Weather display updated for {weather_data.city}")
    
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