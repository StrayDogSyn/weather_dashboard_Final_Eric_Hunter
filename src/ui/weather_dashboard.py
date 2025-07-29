"""Weather Dashboard - Main UI Component

Modern weather dashboard with Data Terminal aesthetic using CustomTkinter.
"""

import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
import logging
import requests
from typing import Optional, List, Dict, Any
from datetime import datetime
import threading
from pathlib import Path

from ui.theme import DataTerminalTheme
from ui.components.weather_display import WeatherDisplayFrame
from ui.components.temperature_chart import TemperatureChart
from ui.components.loading_overlay import LoadingOverlay
from services.window_manager import WindowStateManager
from services.config_service import ConfigService
from services.weather_service import WeatherService, WeatherData
from services.logging_service import LoggingService

# Enhanced features availability check
try:
    from enhanced_search_bar import EnhancedSearchBarFrame
    # from enhanced_weather_display import EnhancedWeatherDisplayFrame
    from enhanced_weather_service import EnhancedWeatherService
    ENHANCED_FEATURES_AVAILABLE = True
except ImportError:
    ENHANCED_FEATURES_AVAILABLE = False


class WeatherDashboard(ctk.CTk):
    """Main weather dashboard application window with enhanced features support."""
    
    def __init__(self, config_service: ConfigService, use_enhanced_features: bool = True):
        """Initialize the weather dashboard."""
        super().__init__()
        
        # Initialize window state manager
        self.window_manager = WindowStateManager()
        
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
        
        # Setup window properties FIRST
        self.setup_window_properties()
        
        # Setup UI with enhanced initialization
        self.setup_ui()
        self._setup_bindings()
        
        # Apply maximized state after UI is ready
        self.after(10, self.ensure_maximized_startup)
        
        # Load initial data
        self._load_initial_weather()
        
        self.logger.info("🎨 Weather Dashboard initialized")
    
    def setup_window_properties(self):
        """Configure basic window properties."""
        self.title("JTC Capstone Application")
        
        # Set minimum size
        self.minsize(1200, 800)
        
        # Apply saved window state
        self.window_manager.apply_window_state(self)
        
        # Configure close protocol
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def ensure_maximized_startup(self):
        """Ensure window opens maximized with multiple fallback methods."""
        try:
            # Method 1: Standard maximization
            self.state('zoomed')
            self.logger.info("Applied zoomed state")
            
        except Exception as e1:
            self.logger.warning(f"Zoomed state failed: {e1}")
            try:
                # Method 2: Alternative maximization
                self.attributes('-zoomed', True)
                self.logger.info("Applied -zoomed attribute")
                
            except Exception as e2:
                self.logger.warning(f"Zoomed attribute failed: {e2}")
                try:
                    # Method 3: Full screen geometry
                    screen_width = self.winfo_screenwidth()
                    screen_height = self.winfo_screenheight()
                    self.geometry(f"{screen_width}x{screen_height}+0+0")
                    self.logger.info(f"Applied full screen geometry: {screen_width}x{screen_height}")
                    
                except Exception as e3:
                    self.logger.error(f"All maximization methods failed: {e3}")
                    # Final fallback
                    self.geometry("1920x1080+0+0")
        
        # Ensure window is visible and focused
        self.lift()
        self.focus_force()
        self.attributes('-topmost', True)
        self.after(100, lambda: self.attributes('-topmost', False))
    

    
    def setup_ui(self):
        """Setup UI components after window configuration."""
        # Configure main grid for responsive layout
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        # Create main container
        self.main_container = ctk.CTkFrame(self, fg_color="transparent")
        self.main_container.grid(row=0, column=0, sticky="nsew", padx=0, pady=0)
        
        # Setup responsive layout
        self.setup_responsive_layout()
    
    def setup_responsive_layout(self):
        """Setup responsive layout that works in all window sizes."""
        # Configure main container grid
        self.main_container.grid_columnconfigure(0, weight=1)
        self.main_container.grid_rowconfigure(1, weight=1)
        
        # Header section
        self.header_frame = ctk.CTkFrame(self.main_container, height=80)
        self.header_frame.grid(row=0, column=0, sticky="ew", padx=0, pady=0)
        self.header_frame.grid_propagate(False)
        
        # Content section
        self.content_frame = ctk.CTkFrame(self.main_container)
        self.content_frame.grid(row=1, column=0, sticky="nsew", padx=0, pady=0)
        
        # Setup header and content
        self.setup_header()
        self.setup_content()
    
    def setup_header(self):
        """Setup header with working search functionality."""
        self.header_frame.grid_columnconfigure(1, weight=1)
        
        # Left side - branding
        left_frame = ctk.CTkFrame(self.header_frame, fg_color="transparent")
        left_frame.grid(row=0, column=0, sticky="w", padx=20, pady=10)
        
        title_label = ctk.CTkLabel(
            left_frame,
            text="⚡ Project CodeFront",
            font=("Segoe UI", 20, "bold"),
            text_color="#00FF88"
        )
        title_label.pack(anchor="w")
        
        # Right side - search and location
        right_frame = ctk.CTkFrame(self.header_frame, fg_color="transparent")
        right_frame.grid(row=0, column=1, sticky="e", padx=20, pady=10)
        
        # Current location
        self.location_label = ctk.CTkLabel(
            right_frame,
            text="Current: Austin, US",
            font=("Segoe UI", 10),
            text_color="gray70"
        )
        self.location_label.pack(anchor="e")
        
        # Search area
        search_container = ctk.CTkFrame(right_frame, fg_color="transparent")
        search_container.pack(anchor="e", pady=(5, 0))
        
        self.search_entry = ctk.CTkEntry(
            search_container,
            placeholder_text="Search cities, coordinates, or zip codes...",
            width=300,
            height=32
        )
        self.search_entry.pack(side="left", padx=(0, 5))
        
        # Bind Enter key to search
        self.search_entry.bind("<Return>", self.on_search_enter)
        self.search_entry.bind("<KP_Enter>", self.on_search_enter)  # Numpad Enter
        
        search_btn = ctk.CTkButton(
            search_container,
            text="SEARCH",
            width=80,
            height=32,
            command=self.on_search_click
        )
        search_btn.pack(side="left")
    
    def setup_content(self):
        """Setup main content area."""
        # Configure content frame for horizontal layout
        self.content_frame.grid_columnconfigure(1, weight=1)
        self.content_frame.grid_rowconfigure(0, weight=1)
        
        # Left panel - weather info
        self.weather_panel = ctk.CTkFrame(self.content_frame, width=400)
        self.weather_panel.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        self.weather_panel.grid_propagate(False)
        
        # Right panel - charts
        self.chart_panel = ctk.CTkFrame(self.content_frame)
        self.chart_panel.grid(row=0, column=1, sticky="nsew", padx=(0, 10), pady=10)
        
        # Setup panels
        self.setup_weather_display()
        self.setup_chart_display()
        
        # Setup status bar
        self.setup_status_bar()
    
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
            
            # Update component scaling
            self._update_component_scaling(current_width, current_height)
            
            # Adjust grid weights based on aspect ratio
            if current_width > current_height * 1.5:  # Wide screen
                self.content_frame.grid_columnconfigure(0, weight=2)
                self.content_frame.grid_columnconfigure(1, weight=3)
            else:  # Standard or tall screen
                self.content_frame.grid_columnconfigure(0, weight=2)
                self.content_frame.grid_columnconfigure(1, weight=3)
    
    def _update_component_scaling(self, width, height):
        """Scale components based on window dimensions."""
        # Adjust font sizes based on window size
        base_font_size = max(12, min(16, width // 120))
        
        # Update chart dimensions
        if hasattr(self, 'chart_display') and self.chart_display:
            chart_width = max(600, width * 0.6)
            chart_height = max(400, height * 0.4)
            if hasattr(self.chart_display, 'update_size'):
                self.chart_display.update_size(chart_width, chart_height)
            else:
                # Fallback for older chart components
                self.chart_display.configure(width=int(chart_width), height=int(chart_height))
        
        # Update weather display scaling
        if hasattr(self, 'weather_display'):
            display_width = max(300, width * 0.25)
            self.weather_display.configure(width=int(display_width))
        
        # Update search frame scaling
        if hasattr(self, 'search_frame'):
            search_width = max(250, min(400, width * 0.25))
            # Update search entry if it exists within search_frame
            for child in self.search_frame.winfo_children():
                if hasattr(child, 'configure'):
                    try:
                        config_options = child.configure()
                        if config_options and 'width' in config_options:
                            child.configure(width=int(search_width))
                    except (AttributeError, TypeError):
                        pass  # Skip widgets that don't support width configuration
        
        # Update main content frame padding
        if hasattr(self, 'content_frame'):
            padding = max(10, min(30, width // 80))
            self.content_frame.grid_configure(padx=padding, pady=padding)
        
        # Update title font size for responsive text
        title_font_size = max(18, min(24, width // 100))
        if hasattr(self, 'title_label'):
            current_font = self.title_label.cget('font')
            if isinstance(current_font, tuple) and len(current_font) >= 2:
                font_family = current_font[0]
                font_weight = current_font[2] if len(current_font) > 2 else 'bold'
                self.title_label.configure(font=(font_family, title_font_size, font_weight))
    

    

    
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
                except (requests.exceptions.RequestException, ValueError, KeyError) as e:
                    # Fallback to basic forecast if enhanced fails
                    self.logger.warning(f"Enhanced forecast failed, using basic: {e}")
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
        
        # Update location label in header
        self.location_label.configure(text=f"Current: {self.current_location}")
        
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
        # Truncate long error messages for status bar
        display_error = error_message if len(error_message) <= 50 else f"{error_message[:50]}..."
        self._update_status(f"Error: {display_error}", "error")
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
        if hasattr(self, 'status_label'):
            # Set color based on status type
            colors = {
                "info": "gray70",
                "success": "#00FF88",
                "warning": "orange",
                "error": "red"
            }
            color = colors.get(status_type, "gray70")
            
            self.status_label.configure(
                text=message,
                text_color=color
            )
        
        self.logger.info(f"Status: {message}")
        
        # Auto-clear status after delay (except errors)
        if status_type != "error":
            self.after(5000, lambda: self._update_status("Ready"))
    
    def _update_last_update(self) -> None:
        """Update last update timestamp."""
        timestamp = datetime.now().strftime("%I:%M %p")
        
        if hasattr(self, 'last_update_label'):
            self.last_update_label.configure(text=f"Last updated: {timestamp}")
    
    def _on_click(self, event) -> None:
        """Handle window click to remove focus from widgets."""
        self.focus_set()
    
    def on_search_enter(self, event):
        """Handle Enter key press in search entry."""
        self.perform_search()
        return "break"  # Prevent default behavior
    
    def on_search_click(self):
        """Handle search button click."""
        self.perform_search()
    
    def on_search(self):
        """Handle search button click (legacy method)."""
        self.perform_search()
    
    def perform_search(self):
        """Perform the actual search operation."""
        try:
            # Get search term
            search_term = self.search_entry.get().strip()
            
            if not search_term:
                self._update_status("Please enter a city name", "warning")
                return
            
            # Update status
            self._update_status(f"Searching for {search_term}...")
            
            # Clear search entry
            self.search_entry.delete(0, 'end')
            
            # Perform weather search
            self._on_city_search(search_term)
            
        except Exception as e:
             self.logger.error(f"Search error: {e}")
             self._update_status("Search failed. Please try again.", "error")
    
    def search_weather(self, city_name):
        """Search for weather data for specified city."""
        try:
            # Log search attempt
            self.logger.info(f"📍 Searching for weather in: {city_name}")
            
            # Update location display
            self.location_label.configure(text=f"Current: {city_name}")
            
            # Get weather service instance
            if hasattr(self, 'weather_service'):
                # Fetch weather data
                weather_data = self.weather_service.get_current_weather(city_name)
                
                if weather_data:
                    # Update weather display
                    self.update_weather_display(weather_data)
                    
                    # Get forecast data
                    forecast_data = self.weather_service.get_forecast(city_name)
                    if forecast_data:
                        self.update_chart_display(forecast_data)
                    
                    self._update_status(f"Weather updated for {city_name}")
                    self.logger.info(f"✅ Weather data updated for {city_name}")
                else:
                    self._update_status(f"No weather data found for {city_name}", "warning")
                    self.logger.warning(f"❌ No weather data found for {city_name}")
            else:
                self._update_status("Weather service not available", "error")
                self.logger.error("Weather service not initialized")
                
        except Exception as e:
            self.logger.error(f"Weather search error: {e}")
            self._update_status(f"Failed to get weather for {city_name}", "error")
    
    def update_status(self, message):
        """Update status bar message."""
        try:
            if hasattr(self, 'status_label'):
                self.status_label.configure(text=message)
            self.logger.info(f"Status: {message}")
        except Exception as e:
            self.logger.error(f"Status update error: {e}")
    
    def setup_weather_display(self):
        """Setup weather display panel."""
        # Create weather display using existing component
        self.weather_display = WeatherDisplayFrame(
            self.weather_panel,
            on_refresh=self._refresh_weather
        )
        self.weather_display.pack(fill="both", expand=True, padx=10, pady=10)
    
    def setup_chart_display(self):
        """Setup chart display panel."""
        # Create chart display using existing component
        self.chart_display = TemperatureChart(
            self.chart_panel
        )
        self.chart_display.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Create loading overlay
        self.loading_overlay = LoadingOverlay(self)
    
    def setup_status_bar(self):
        """Setup status bar for the application."""
        # Status bar frame
        self.status_frame = ctk.CTkFrame(self.main_container, height=30)
        self.status_frame.grid(row=2, column=0, sticky="ew", padx=0, pady=0)
        self.status_frame.grid_propagate(False)
        self.status_frame.grid_columnconfigure(1, weight=1)
        
        # Configure main container to accommodate status bar
        self.main_container.grid_rowconfigure(2, weight=0)
        
        # Status label
        self.status_label = ctk.CTkLabel(
            self.status_frame,
            text="Ready",
            font=("Segoe UI", 10),
            text_color="gray70"
        )
        self.status_label.grid(row=0, column=0, padx=10, pady=5, sticky="w")
        
        # Last update label
        self.last_update_label = ctk.CTkLabel(
            self.status_frame,
            text="",
            font=("Segoe UI", 10),
            text_color="gray70"
        )
        self.last_update_label.grid(row=0, column=1, padx=10, pady=5, sticky="e")
    
    def on_closing(self) -> None:
        """Handle window closing with state save."""
        try:
            # Save window state
            self.window_manager.save_window_config(self)
            
            # Cleanup and close
            self.logger.info("🔌 Shutting down Weather Dashboard")
            
            # Save any pending data
            if hasattr(self, 'weather_service'):
                try:
                    # Don't clear cache on close, just save it
                    pass
                except Exception as e:
                    self.logger.error(f"Error saving data on close: {e}")
            
            self.destroy()
            
        except Exception as e:
            self.logger.error(f"Shutdown error: {e}")
        finally:
            self.logger.info("👋 Weather Dashboard closed")
    
    def _on_closing(self) -> None:
        """Handle window closing (legacy method)."""
        self.on_closing()
    
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