"""Professional Weather Dashboard - Clean Capstone Design

Minimalist weather dashboard with professional 2-column layout,
focused on essential information and clean aesthetics.
"""

from typing import Optional, List
import threading
from datetime import datetime
import logging
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import numpy as np
import tkinter as tk
import os
import sys

# Comprehensive error suppression before CustomTkinter import
original_stderr_write = sys.stderr.write

def patched_stderr_write(text):
    """Filter out CustomTkinter DPI scaling errors from stderr."""
    if "invalid command name" in text.lower():
        return  # Suppress the error
    return original_stderr_write(text)

sys.stderr.write = patched_stderr_write

# Import CustomTkinter and immediately disable DPI scaling methods
import customtkinter as ctk

# Disable CustomTkinter DPI scaling at the source
try:
    # Disable appearance mode tracking
    if hasattr(ctk, 'AppearanceModeTracker'):
        original_init = ctk.AppearanceModeTracker.__init__
        def disabled_init(self, *args, **kwargs):
            pass  # Do nothing
        ctk.AppearanceModeTracker.__init__ = disabled_init
        
    # Disable scaling tracking
    if hasattr(ctk, 'ScalingTracker'):
        original_scaling_init = ctk.ScalingTracker.__init__
        def disabled_scaling_init(self, *args, **kwargs):
            pass  # Do nothing
        ctk.ScalingTracker.__init__ = disabled_scaling_init
        
    # Patch any update or check_dpi_scaling methods
    for module_name in dir(ctk):
        module = getattr(ctk, module_name)
        if hasattr(module, 'update') and callable(getattr(module, 'update')):
            setattr(module, 'update', lambda *args, **kwargs: None)
        if hasattr(module, 'check_dpi_scaling') and callable(getattr(module, 'check_dpi_scaling')):
            setattr(module, 'check_dpi_scaling', lambda *args, **kwargs: None)
except Exception:
    pass  # Ignore any errors during patching

# Monkey patch to suppress any remaining CustomTkinter errors
original_report_callback_exception = tk.Tk.report_callback_exception

def patched_report_callback_exception(self, exc, val, tb):
    """Patched version that suppresses CustomTkinter DPI scaling errors."""
    if isinstance(val, tk.TclError):
        error_msg = str(val).lower()
        if "invalid command name" in error_msg:
            # Suppress all invalid command name errors from CustomTkinter
            return
    # Call original for other errors
    original_report_callback_exception(self, exc, val, tb)

# Apply the patch
tk.Tk.report_callback_exception = patched_report_callback_exception

from ui.components.temperature_chart import TemperatureChart
from ui.components.weather_journal import WeatherJournal
from ui.components.journal_manager import JournalManager
from ui.components.journal_search import JournalSearchComponent
from ui.components.journal_calendar import JournalCalendarComponent
from ui.components.photo_gallery import PhotoGalleryComponent
from ui.components.mood_analytics import MoodAnalyticsComponent
from ui.components.activity_suggester import ActivitySuggester
from services.enhanced_weather_service import EnhancedWeatherService
from services.config_service import ConfigService
from services.journal_service import JournalService
from models.weather_models import WeatherData, ForecastData
from services.logging_service import LoggingService
from ui.theme import DataTerminalTheme, WeatherTheme


class WeatherDisplayEnhancer:
    """Enhances existing weather display with better formatting and icons."""
    
    def __init__(self, weather_dashboard):
        self.dashboard = weather_dashboard
        self.weather_icons = {
            'clear': '☀️',
            'sunny': '☀️',
            'partly cloudy': '⛅',
            'cloudy': '☁️',
            'overcast': '☁️',
            'rain': '🌧️',
            'drizzle': '🌦️',
            'snow': '❄️',
            'thunderstorm': '⛈️',
            'fog': '🌫️',
            'mist': '🌫️',
            'default': '🌤️'
        }
        
    def enhance_display(self):
        """Enhance existing weather display with better formatting - NO DUPLICATION."""
        try:
            # Check if dashboard and widgets still exist before enhancing
            if not hasattr(self, 'dashboard') or not self.dashboard.winfo_exists():
                return
                
            self.add_weather_icons()
            self.improve_temperature_display()
            self.update_existing_weather_details()
            
        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.warning(f"Enhancement error (non-critical): {e}")
    
    def add_weather_icons(self):
        """Add weather icons to existing display."""
        try:
            # Check if condition label exists and is valid
            if not hasattr(self.dashboard, 'condition_label') or not self.dashboard.condition_label.winfo_exists():
                return
                
            # Get current condition text
            current_condition = self.dashboard.condition_label.cget('text').lower()
            
            # Find matching icon
            icon = self.weather_icons.get('default')
            for condition, emoji in self.weather_icons.items():
                if condition in current_condition:
                    icon = emoji
                    break
            
            # Update condition label with icon ONLY if not already present
            current_text = self.dashboard.condition_label.cget('text')
            if not any(emoji in current_text for emoji in self.weather_icons.values()):
                enhanced_text = f"{icon} {current_text}"
                self.dashboard.condition_label.configure(text=enhanced_text)
            
        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.warning(f"Icon enhancement error: {e}")
    
    def improve_temperature_display(self):
        """Improve temperature display formatting."""
        try:
            # Check if temp label exists and is valid
            if not hasattr(self.dashboard, 'temp_label') or not self.dashboard.temp_label.winfo_exists():
                return
                
            # Add degree symbol styling if not present
            temp_text = self.dashboard.temp_label.cget('text')
            if '°' not in temp_text and any(char.isdigit() for char in temp_text):
                # Extract number and add proper formatting
                import re
                numbers = re.findall(r'-?\d+', temp_text)
                if numbers:
                    enhanced_temp = f"{numbers[0]}°C"
                    self.dashboard.temp_label.configure(text=enhanced_temp)
            
        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.warning(f"Temperature enhancement error: {e}")
    
    def update_existing_weather_details(self):
        """Update existing weather detail labels - NO NEW WIDGETS CREATED."""
        try:
            # Only update existing labels, never create new ones
            if hasattr(self.dashboard, 'feels_like_label') and self.dashboard.feels_like_label.winfo_exists():
                current_text = self.dashboard.feels_like_label.cget('text')
                if '🌡️' not in current_text:
                    self.dashboard.feels_like_label.configure(text=f"🌡️ {current_text}")
            
            if hasattr(self.dashboard, 'humidity_label') and self.dashboard.humidity_label.winfo_exists():
                current_text = self.dashboard.humidity_label.cget('text')
                if '💧' not in current_text:
                    self.dashboard.humidity_label.configure(text=f"💧 {current_text}")
                
        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.warning(f"Details update error: {e}")


class ProfessionalWeatherDashboard(ctk.CTk):
    """Professional weather dashboard with clean, minimal design."""
    
    # Data Terminal color scheme
    ACCENT_COLOR = DataTerminalTheme.PRIMARY      # Neon green
    BACKGROUND = DataTerminalTheme.BACKGROUND     # Dark background
    CARD_COLOR = DataTerminalTheme.CARD_BG        # Dark card background
    TEXT_PRIMARY = DataTerminalTheme.TEXT         # Light text
    TEXT_SECONDARY = DataTerminalTheme.TEXT_SECONDARY # Medium gray text
    BORDER_COLOR = DataTerminalTheme.BORDER       # Dark border
    
    def __init__(self):
        """Initialize professional weather dashboard."""
        super().__init__()
        
        # Setup services
        self.logging_service = LoggingService()
        self.logging_service.setup_logging()
        self.logger = self.logging_service.get_logger(__name__)
        
        self.config_service = ConfigService()
        self.weather_service = EnhancedWeatherService(self.config_service)
        self.journal_service = JournalService()
        
        # Data storage
        self.current_weather: Optional[WeatherData] = None
        self.forecast_data: Optional[List[ForecastData]] = None
        self.current_city: str = "London"
        self.chart_timeframe = "24h"
        
        # DON'T initialize enhancer here
        self.display_enhancer = None
        
        # Configure window
        self._configure_window()
        
        # Create UI
        self._create_widgets()
        self._setup_layout()
        
        # Initialize display enhancer ONLY after UI is created
        self.display_enhancer = WeatherDisplayEnhancer(self)
        
        # Load initial data
        self._load_initial_data()
        
        self.logger.info("Professional Weather Dashboard initialized")
    
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
    
    def on_window_resize(self, event):
        """Handle window resize for responsive design."""
        try:
            if event.widget == self and self.winfo_exists():  # Only handle main window resize
                try:
                    width = self.winfo_width()
                    height = self.winfo_height()
                    
                    # Update component sizes based on window size
                    self.update_component_scaling(width, height)
                except Exception as e:
                    self.logger.warning(f"Window resize handling warning: {e}")
        except Exception as e:
            # Suppress DPI scaling and update command errors
            if "invalid command name" not in str(e).lower():
                self.logger.warning(f"Window resize event error: {e}")
    
    def update_component_scaling(self, width, height):
        """Scale components based on window dimensions."""
        try:
            # Check if window still exists
            if not self.winfo_exists():
                return
                
            # Adjust font sizes based on window size
            base_font_size = max(12, min(18, width // 100))
            
            # Update chart dimensions with better scaling
            if hasattr(self, 'temperature_chart') and hasattr(self.temperature_chart, 'update_size'):
                chart_width = max(700, width * 0.45)
                chart_height = max(500, height * 0.45)
                self.temperature_chart.update_size(chart_width, chart_height)
            
            # Update weather card scaling with better proportions
            if hasattr(self, 'weather_card') and self.weather_card.winfo_exists():
                card_width = max(350, width * 0.4)
                self.weather_card.configure(width=card_width)
            
            # Update header elements scaling
            if hasattr(self, 'search_entry') and self.search_entry.winfo_exists():
                search_width = max(300, min(500, width * 0.28))
                self.search_entry.configure(width=search_width)
            
            # Update main frame padding based on screen size
            if hasattr(self, 'main_frame') and self.main_frame.winfo_exists():
                padding = max(15, min(40, width // 60))
                self.main_frame.grid_configure(padx=padding, pady=padding)
            
            # Update font sizes for responsive text
            title_font_size = max(22, min(32, width // 60))
            if hasattr(self, 'title_label') and self.title_label.winfo_exists():
                self.title_label.configure(font=(DataTerminalTheme.FONT_FAMILY, title_font_size, "bold"))
                
            # Schedule enhancement after scaling - with existence check
            if self.display_enhancer and self.winfo_exists():
                self.after(100, self._safe_enhance_display)
        except Exception as e:
            self.logger.warning(f"Component scaling error: {e}")

    def _configure_window(self) -> None:
        """Configure main window with professional styling and fullscreen default."""
        try:
            self.title("JTC Capstone Application")
            self.geometry("1600x1000")
            self.minsize(1400, 900)
            
            # Set theme and appearance with error handling
            try:
                ctk.set_appearance_mode("dark")
                ctk.set_default_color_theme("dark-blue")
            except Exception as e:
                self.logger.warning(f"CustomTkinter theme configuration warning: {e}")
                
            self.configure(fg_color=self.BACKGROUND)
            
            # Configure grid weights for responsive design
            self.grid_columnconfigure(0, weight=1)
            self.grid_rowconfigure(1, weight=1)  # Main content area
            
            # Bind resize event with error handling
            try:
                self.bind('<Configure>', self.on_window_resize)
            except Exception as e:
                self.logger.warning(f"Window resize binding warning: {e}")
                
        except Exception as e:
            self.logger.error(f"Window configuration error: {e}")
    
    def center_window(self) -> None:
        """Center the window on the screen."""
        try:
            # Use default window size for centering calculation
            window_width = 1600
            window_height = 1000
            
            # Get screen dimensions
            screen_width = self.winfo_screenwidth()
            screen_height = self.winfo_screenheight()
            
            # Calculate true center position
            center_x = int((screen_width - window_width) // 2)
            center_y = int((screen_height - window_height) // 2)
            
            # Ensure window doesn't go off-screen (minimum 10px margin)
            center_x = max(10, min(center_x, screen_width - window_width - 10))
            center_y = max(40, min(center_y, screen_height - window_height - 40))  # 40px top margin for taskbar
                
            # Set window geometry with center position
            self.geometry(f"{window_width}x{window_height}+{center_x}+{center_y}")
            
            self.logger.info(f"Window centered at {center_x},{center_y} with size {window_width}x{window_height} on screen {screen_width}x{screen_height}")
            
        except Exception as e:
            self.logger.warning(f"Window centering warning: {e}")
            # Fallback to default geometry
            self.geometry("1800x1200")
    
    def _create_widgets(self) -> None:
        """Create all UI widgets with clean design."""
        # Header
        self._create_header()
        
        # Main content area
        self._create_main_content()
        
        # Status bar
        self._create_status_bar()
    
    def _create_header(self) -> None:
        """Create clean header with title and search."""
        self.header_frame = ctk.CTkFrame(
            self,
            fg_color=self.CARD_COLOR,
            corner_radius=0,
            height=100,
            border_width=0
        )
        
        # Header accent strip
        self.header_accent = ctk.CTkFrame(
            self.header_frame,
            fg_color=self.ACCENT_COLOR,
            height=2,
            corner_radius=0
        )
        
        # Title container
        self.title_container = ctk.CTkFrame(self.header_frame, fg_color="transparent")
        
        # Clean app title
        self.title_label = ctk.CTkLabel(
            self.title_container,
            text="⚡ PROJECT CODEFRONT",
            font=(DataTerminalTheme.FONT_FAMILY, 28, "bold"),
            text_color=self.ACCENT_COLOR
        )
        
        # Subtitle
        self.subtitle_label = ctk.CTkLabel(
            self.title_container,
            text="Advanced Weather Intelligence System",
            font=(DataTerminalTheme.FONT_FAMILY, 12, "normal"),
            text_color=self.TEXT_SECONDARY
        )
        
        # Search container for organizing search components
        self.search_container = ctk.CTkFrame(self.header_frame, fg_color="transparent")
        
        # Search controls container
        self.search_controls = ctk.CTkFrame(self.search_container, fg_color="transparent")
        
        # Search bar
        self.search_entry = ctk.CTkEntry(
            self.search_controls,
            placeholder_text="🔍 Enter city name...",
            font=(DataTerminalTheme.FONT_FAMILY, DataTerminalTheme.FONT_SIZE_MEDIUM),
            width=300,
            height=40,
            corner_radius=20,
            border_color=self.BORDER_COLOR,
            fg_color=self.BACKGROUND
        )
        self.search_entry.bind("<Return>", self._on_search)
        
        # Search button
        self.search_button = ctk.CTkButton(
            self.search_controls,
            text="SEARCH",
            font=(DataTerminalTheme.FONT_FAMILY, DataTerminalTheme.FONT_SIZE_MEDIUM, "bold"),
            width=100,
            height=40,
            corner_radius=20,
            fg_color=self.ACCENT_COLOR,
            hover_color=DataTerminalTheme.SUCCESS,
            command=self._search_weather
        )
        
        # Current location indicator
        self.current_location_label = ctk.CTkLabel(
            self.search_container,
            text="Current: London, GB",
            font=(DataTerminalTheme.FONT_FAMILY, DataTerminalTheme.FONT_SIZE_SMALL),
            text_color=self.TEXT_SECONDARY
        )
    
    def _create_main_content(self) -> None:
        """Create main tabbed interface."""
        self.main_frame = ctk.CTkFrame(
            self,
            fg_color="transparent"
        )
        
        # Configure main frame grid
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(0, weight=1)
        
        # Create tab navigation system
        self._create_tab_navigation()
        
        # Create tab content
        self._create_weather_tab()
        self._create_journal_tab()
        self._create_activities_tab()
        self._create_settings_tab()
    
    def _create_tab_navigation(self) -> None:
        """Create the main tab navigation system."""
        self.tabview = ctk.CTkTabview(
            self.main_frame,
            fg_color=self.CARD_COLOR,
            segmented_button_fg_color=self.BACKGROUND,
            segmented_button_selected_color=self.ACCENT_COLOR,
            segmented_button_selected_hover_color=DataTerminalTheme.SUCCESS,
            segmented_button_unselected_color=self.CARD_COLOR,
            segmented_button_unselected_hover_color=DataTerminalTheme.HOVER,
            text_color=self.TEXT_PRIMARY,
            text_color_disabled=self.TEXT_SECONDARY,
            corner_radius=12,
            border_width=1,
            border_color=self.BORDER_COLOR
        )
        
        # Create tabs with icons
        self.weather_tab = self.tabview.add("🌤️ Weather")
        self.journal_tab = self.tabview.add("📔 Journal")
        self.activities_tab = self.tabview.add("🎯 Activities")
        self.settings_tab = self.tabview.add("⚙️ Settings")
        
        # Position tabview
        self.tabview.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
    
    def _create_weather_tab(self) -> None:
        """Create the weather tab content with current weather and forecast."""
        # Configure weather tab grid
        self.weather_tab.grid_columnconfigure(0, weight=1)
        self.weather_tab.grid_rowconfigure(0, weight=1)
        
        # Create regular frame for weather content (no scrollbar)
        self.weather_content = ctk.CTkFrame(
            self.weather_tab,
            fg_color="transparent"
        )
        self.weather_content.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        
        # Configure content frame grid
        self.weather_content.grid_columnconfigure(0, weight=1)
        self.weather_content.grid_columnconfigure(1, weight=1)
        self.weather_content.grid_rowconfigure(0, weight=1)
        
        # Create left column - Current weather
        self._create_current_weather_in_tab()
        
        # Create right column - Analytics
        self._create_analytics_in_tab()
    
    def _create_current_weather_in_tab(self) -> None:
        """Create current weather section with refresh capability."""
        # Create a container for the section
        self.weather_section = ctk.CTkFrame(
            self.weather_content,
            fg_color="transparent"
        )
        
        # Add header frame for title and refresh button
        header_frame = ctk.CTkFrame(self.weather_section, fg_color="transparent")
        header_frame.pack(fill="x", padx=10, pady=(0, 10))
        
        # Section title
        self.weather_title = ctk.CTkLabel(
            header_frame,
            text="CURRENT WEATHER",
            font=(DataTerminalTheme.FONT_FAMILY, DataTerminalTheme.FONT_SIZE_MEDIUM, "bold"),
            text_color=self.ACCENT_COLOR,
            anchor="w"
        )
        self.weather_title.pack(side="left")
        
        # Refresh button
        self.refresh_button = ctk.CTkButton(
            header_frame,
            text="🔄 Refresh",
            width=100,
            height=30,
            font=(DataTerminalTheme.FONT_FAMILY, 12, "bold"),
            fg_color=self.ACCENT_COLOR,
            hover_color=DataTerminalTheme.SUCCESS,
            command=self._manual_refresh
        )
        self.refresh_button.pack(side="right", padx=(0, 10))
        
        # Last update label
        self.last_update_label = ctk.CTkLabel(
            header_frame,
            text="",
            font=(DataTerminalTheme.FONT_FAMILY, 10),
            text_color=self.TEXT_SECONDARY
        )
        self.last_update_label.pack(side="right", padx=(0, 10))
        
        # Create the weather card
        self._create_weather_card()
        
        # Position the section in the weather tab
        self.weather_section.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        
        # Setup auto-refresh
        self._setup_auto_refresh()
    
    def _create_weather_card(self) -> None:
        """Create large current weather card."""
        self.weather_card = ctk.CTkFrame(
            self.weather_section,  # Changed parent from main_frame to weather_section
            fg_color=self.CARD_COLOR,
            corner_radius=16,
            border_width=1,
            border_color=self.BORDER_COLOR
        )
        
        # City name
        self.city_label = ctk.CTkLabel(
            self.weather_card,
            text="London",
            font=(DataTerminalTheme.FONT_FAMILY, 28, "bold"),
            text_color=self.TEXT_PRIMARY
        )
        
        # Large temperature display
        self.temp_label = ctk.CTkLabel(
            self.weather_card,
            text="22°C",
            font=(DataTerminalTheme.FONT_FAMILY, 72, "normal"),
            text_color=self.ACCENT_COLOR
        )
        
        # Weather condition
        self.condition_label = ctk.CTkLabel(
            self.weather_card,
            text="Partly Cloudy",
            font=(DataTerminalTheme.FONT_FAMILY, 18),
            text_color=self.TEXT_SECONDARY
        )
        
        # Essential info grid
        self.info_frame = ctk.CTkFrame(
            self.weather_card,
            fg_color="transparent"
        )
        
        # Feels like
        self.feels_like_label = ctk.CTkLabel(
            self.info_frame,
            text="🌡️ Feels like: 24°C",
            font=(DataTerminalTheme.FONT_FAMILY, 16),
            text_color=self.TEXT_SECONDARY
        )
        
        # Humidity
        self.humidity_label = ctk.CTkLabel(
            self.info_frame,
            text="💧 Humidity: 65%",
            font=(DataTerminalTheme.FONT_FAMILY, 16),
            text_color=self.TEXT_SECONDARY
        )
        
        # Create comprehensive weather metrics grid
        self._create_weather_metrics_grid()
    
    def _create_weather_metrics_grid(self) -> None:
        """Create comprehensive weather metrics grid with dynamic updates."""
        self.metrics_grid = ctk.CTkFrame(self.weather_section, fg_color="transparent")
        self.metrics_grid.pack(fill="x", padx=10, pady=(10, 0))
        
        # Store metric widgets for updates
        self.metric_widgets = {}
        
        # Configure grid with better spacing
        for i in range(3):
            self.metrics_grid.grid_columnconfigure(i, weight=1, uniform="col", minsize=120)
        
        # Define metrics with keys for updates
        metrics_config = [
            ("humidity", "HUMIDITY", "-%", 0, 0, "💧"),
            ("pressure", "PRESSURE", "- hPa", 0, 1, "🌡️"),
            ("visibility", "VISIBILITY", "- km", 0, 2, "👁️"),
            ("wind_speed", "WIND SPEED", "- km/h", 1, 0, "💨"),
            ("wind_dir", "WIND DIR", "-", 1, 1, "🧭"),
            ("cloudiness", "CLOUDINESS", "-%", 1, 2, "☁️"),
            ("temp_min", "MIN TEMP", "-°C", 2, 0, "❄️"),
            ("temp_max", "MAX TEMP", "-°C", 2, 1, "🔥"),
            ("uv_index", "UV INDEX", "-", 2, 2, "☀️")
        ]
        
        for key, label, default_value, row, col, icon in metrics_config:
            metric_frame = ctk.CTkFrame(
                self.metrics_grid,
                fg_color=self.CARD_COLOR,
                corner_radius=8,
                border_width=1,
                border_color=self.BORDER_COLOR,
                height=80,  # Increased height
                width=140   # Set minimum width
            )
            metric_frame.grid(row=row, column=col, padx=3, pady=3, sticky="ew")
            metric_frame.grid_propagate(False)
            
            # Container for vertical layout
            content_frame = ctk.CTkFrame(metric_frame, fg_color="transparent")
            content_frame.pack(expand=True, fill="both", padx=5, pady=5)
            
            # Icon and label on same line
            label_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
            label_frame.pack()
            
            ctk.CTkLabel(
                label_frame,
                text=f"{icon} {label}",
                font=(DataTerminalTheme.FONT_FAMILY, 9, "bold"),
                text_color=self.TEXT_SECONDARY
            ).pack()
            
            # Value with better spacing
            value_label = ctk.CTkLabel(
                content_frame,
                text=default_value,
                font=(DataTerminalTheme.FONT_FAMILY, 13, "bold"),
                text_color=self.ACCENT_COLOR
            )
            value_label.pack(pady=(2, 0))
            
            self.metric_widgets[key] = value_label

    def _update_metrics_grid(self, weather_data) -> None:
        """Update metrics grid with real weather data."""
        try:
            # Handle temperature conversion
            temp_min = weather_data.raw_data.get('main', {}).get('temp_min', weather_data.temperature)
            temp_max = weather_data.raw_data.get('main', {}).get('temp_max', weather_data.temperature)
            
            updates = {
                "humidity": f"{weather_data.humidity}%",
                "pressure": f"{weather_data.pressure} hPa",
                "visibility": f"{weather_data.visibility:.1f} km" if weather_data.visibility else "10+ km",
                "wind_speed": f"{weather_data.wind_speed_kmh:.0f} km/h" if weather_data.wind_speed else "0 km/h",
                "wind_dir": weather_data.wind_direction_text if weather_data.wind_direction else "N/A",
                "cloudiness": f"{weather_data.cloudiness}%" if weather_data.cloudiness is not None else "N/A",
                "temp_min": f"{temp_min:.0f}°C",
                "temp_max": f"{temp_max:.0f}°C",
                "uv_index": str(weather_data.uv_index) if weather_data.uv_index else "N/A"
            }
            
            for key, value in updates.items():
                if key in self.metric_widgets and self.metric_widgets[key].winfo_exists():
                    self.metric_widgets[key].configure(text=value)
                    
        except Exception as e:
            self.logger.error(f"Error updating metrics: {e}")
    
    def _create_analytics_in_tab(self) -> None:
        """Create temperature forecast panel within the weather tab."""
        # Create a container for the analytics section
        self.analytics_section = ctk.CTkFrame(
            self.weather_content,
            fg_color="transparent"
        )
        
        # Section title
        self.forecast_title = ctk.CTkLabel(
            self.analytics_section,
            text="TEMPERATURE FORECAST",
            font=(DataTerminalTheme.FONT_FAMILY, DataTerminalTheme.FONT_SIZE_MEDIUM, "bold"),
            text_color=self.ACCENT_COLOR,
            anchor="w"
        )
        self.forecast_title.pack(anchor="w", padx=10, pady=(0, 10))
        
        self.analytics_card = ctk.CTkFrame(
            self.analytics_section,
            fg_color=self.CARD_COLOR,
            corner_radius=16,
            border_width=1,
            border_color=self.BORDER_COLOR
        )
        
        # Analytics title
        self.analytics_title = ctk.CTkLabel(
            self.analytics_card,
            text="Temperature Forecast (5 Days)",
            font=(DataTerminalTheme.FONT_FAMILY, 16, "bold"),
            text_color=self.TEXT_PRIMARY
        )
        
        # Position the section in the weather tab
        self.analytics_section.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
        
        # Chart container - Enhanced Temperature Chart
        self.temperature_chart = TemperatureChart(
            self.analytics_card
        )
        self.temperature_chart.pack(fill="both", expand=True, padx=10, pady=10)
    
    def _create_journal_tab(self) -> None:
        """Create the journal tab content for weather diary and mood tracking."""
        # Configure journal tab
        self.journal_tab.grid_columnconfigure(0, weight=1)
        self.journal_tab.grid_rowconfigure(0, weight=1)
        
        # Create main journal container with notebook for advanced features
        self.journal_notebook = ctk.CTkTabview(
            self.journal_tab,
            fg_color=self.CARD_COLOR,
            segmented_button_fg_color=self.BACKGROUND,
            segmented_button_selected_color=self.ACCENT_COLOR,
            segmented_button_selected_hover_color=DataTerminalTheme.SUCCESS,
            segmented_button_unselected_color=self.CARD_COLOR,
            segmented_button_unselected_hover_color=DataTerminalTheme.HOVER,
            text_color=self.TEXT_PRIMARY,
            corner_radius=12,
            border_width=1,
            border_color=self.BORDER_COLOR
        )
        
        # Create journal sub-tabs
        self.journal_entries_tab = self.journal_notebook.add("📝 Entries")
        self.journal_search_tab = self.journal_notebook.add("🔍 Search")
        self.journal_calendar_tab = self.journal_notebook.add("📅 Calendar")
        self.journal_photos_tab = self.journal_notebook.add("📸 Photos")
        self.journal_analytics_tab = self.journal_notebook.add("📊 Analytics")
        
        # Position the notebook
        self.journal_notebook.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        
        # Create content for each tab
        self._create_journal_entries_content()
        self._create_journal_search_content()
        self._create_journal_calendar_content()
        self._create_journal_photos_content()
        self._create_journal_analytics_content()
    
    def _create_journal_entries_content(self) -> None:
        """Create the main journal entries interface."""
        # Configure entries tab
        self.journal_entries_tab.grid_columnconfigure(0, weight=1)
        self.journal_entries_tab.grid_rowconfigure(0, weight=1)
        
        # Create the JournalManager component with enhanced functionality
        weather_theme = WeatherTheme()
        self.journal_manager = JournalManager(
            self.journal_entries_tab,
            self.weather_service,
            weather_theme
        )
        self.journal_manager.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
    
    def _create_journal_search_content(self) -> None:
        """Create the advanced search interface."""
        # Configure search tab
        self.journal_search_tab.grid_columnconfigure(0, weight=1)
        self.journal_search_tab.grid_rowconfigure(0, weight=1)
        
        # Create search component
        self.journal_search = JournalSearchComponent(
            self.journal_search_tab,
            self.journal_service
        )
        # The component creates its own frame internally, no need to grid the component
    
    def _create_journal_calendar_content(self) -> None:
        """Create the calendar view interface."""
        # Configure calendar tab
        self.journal_calendar_tab.grid_columnconfigure(0, weight=1)
        self.journal_calendar_tab.grid_rowconfigure(0, weight=1)
        
        # Create calendar component
        self.journal_calendar = JournalCalendarComponent(
            self.journal_calendar_tab,
            self.journal_service
        )
        # The component creates its own frame internally, no need to grid the component
    
    def _create_journal_photos_content(self) -> None:
        """Create the photo gallery interface."""
        # Configure photos tab
        self.journal_photos_tab.grid_columnconfigure(0, weight=1)
        self.journal_photos_tab.grid_rowconfigure(0, weight=1)
        
        # Create photo gallery component
        self.journal_photos = PhotoGalleryComponent(
            self.journal_photos_tab,
            self.journal_service
        )
        # The component creates its own frame internally, no need to grid the component
    
    def _create_journal_analytics_content(self) -> None:
        """Create the mood analytics interface."""
        # Configure analytics tab
        self.journal_analytics_tab.grid_columnconfigure(0, weight=1)
        self.journal_analytics_tab.grid_rowconfigure(0, weight=1)
        
        # Create mood analytics component
        self.journal_mood_analytics = MoodAnalyticsComponent(
            self.journal_analytics_tab,
            self.journal_service
        )
        # The component creates its own frame internally, no need to grid the component
    
    def _create_activities_tab(self) -> None:
        """Create the activities tab content for AI-powered suggestions."""
        # Configure activities tab
        self.activities_tab.grid_columnconfigure(0, weight=1)
        self.activities_tab.grid_rowconfigure(0, weight=1)
        
        # Create the activity suggester component
        self.activity_suggester = ActivitySuggester(
            self.activities_tab,
            weather_service=self.weather_service,
            config_service=self.config_service
        )
        self.activity_suggester.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
    
    def _create_settings_tab(self) -> None:
        """Create the settings tab content for API keys and preferences."""
        # Configure settings tab
        self.settings_tab.grid_columnconfigure(0, weight=1)
        self.settings_tab.grid_rowconfigure(1, weight=1)
        
        # Settings title
        settings_title = ctk.CTkLabel(
            self.settings_tab,
            text="SETTINGS & PREFERENCES",
            font=(DataTerminalTheme.FONT_FAMILY, DataTerminalTheme.FONT_SIZE_MEDIUM, "bold"),
            text_color=self.ACCENT_COLOR
        )
        settings_title.grid(row=0, column=0, sticky="w", padx=20, pady=(20, 10))
        
        # Create scrollable frame for settings content
        self.settings_scrollable = ctk.CTkScrollableFrame(
            self.settings_tab,
            fg_color=self.CARD_COLOR,
            corner_radius=16,
            border_width=1,
            border_color=self.BORDER_COLOR,
            scrollbar_button_color=self.ACCENT_COLOR,
            scrollbar_button_hover_color=self.TEXT_PRIMARY
        )
        self.settings_scrollable.grid(row=1, column=0, sticky="nsew", padx=20, pady=(0, 20))
        
        # Settings content frame inside scrollable
        settings_frame = ctk.CTkFrame(
            self.settings_scrollable,
            fg_color="transparent"
        )
        
        # Placeholder content
        placeholder_label = ctk.CTkLabel(
            settings_frame,
            text="⚙️ Application Settings\n\nComing Soon:\n• API key management\n• Temperature unit preferences\n• Theme customization\n• Notification settings\n• Data export options",
            font=(DataTerminalTheme.FONT_FAMILY, 16),
            text_color=self.TEXT_SECONDARY,
            justify="left"
        )
        placeholder_label.pack(expand=True, padx=40, pady=40)
    

    
    def _create_status_bar(self) -> None:
        """Create clean status bar."""
        self.status_frame = ctk.CTkFrame(
            self,
            fg_color=self.CARD_COLOR,
            corner_radius=0,
            height=40,
            border_width=1,
            border_color=self.BORDER_COLOR
        )
        
        self.status_label = ctk.CTkLabel(
            self.status_frame,
            text="Ready",
            font=(DataTerminalTheme.FONT_FAMILY, 12),
            text_color=self.TEXT_SECONDARY
        )
    
    def _setup_layout(self) -> None:
        """Setup clean, organized layout with proper spacing."""
        # Header
        self.header_frame.grid(row=0, column=0, sticky="ew", padx=0, pady=0)
        self.header_frame.grid_propagate(False)
        
        # Header accent strip
        self.header_accent.pack(fill="x", side="top")
        
        # Header content - Clean title section
        self.title_container.pack(side="left", padx=30, pady=15)
        
        # Title positioning - simplified
        self.title_label.pack(anchor="w", pady=(5, 2))
        self.subtitle_label.pack(anchor="w", pady=(0, 5))
        
        # Search area on the right - cleaner spacing
        self.search_container.pack(side="right", padx=30, pady=15)
        
        # Search controls - simplified
        self.search_controls.pack()
        self.search_entry.pack(side="left", padx=(0, 8))
        self.search_button.pack(side="left")
        
        # Current location - cleaner positioning
        self.current_location_label.pack(pady=(8, 0))
        
        # Main content with better spacing
        self.main_frame.grid(row=1, column=0, sticky="nsew", padx=15, pady=15)
        
        # Weather card - cleaner layout
        self.weather_card.pack(fill="both", expand=True, padx=15, pady=15)
        
        # Weather card content - organized spacing
        self.city_label.pack(pady=(30, 8))
        self.temp_label.pack(pady=8)
        self.condition_label.pack(pady=(0, 20))
        
        # Info section - cleaner organization
        self.info_frame.pack(fill="x", padx=30, pady=(0, 30))
        self.feels_like_label.pack(pady=3)
        self.humidity_label.pack(pady=3)
        
        # Analytics card - better spacing
        self.analytics_card.pack(fill="both", expand=True, padx=15, pady=(0, 15))
        
        # Status bar - clean positioning
        self.status_frame.grid(row=2, column=0, sticky="ew", padx=0, pady=0)
        self.status_label.pack(side="left", padx=15, pady=8)
    
    def _load_initial_data(self) -> None:
        """Load initial weather data."""
        threading.Thread(target=self._fetch_weather_data, daemon=True).start()
    
    def _fetch_weather_data(self) -> None:
        """Fetch real weather data from API."""
        try:
            # Show loading state
            if hasattr(self, 'status_label') and self.status_label.winfo_exists():
                self.after(0, self._schedule_loading_status)
            
            # Show loading indicators
            self.after(0, self.show_loading_state)
            
            # Get current weather
            weather_data = self.weather_service.get_enhanced_weather(self.current_city)
            self.current_weather = weather_data
            
            # Get forecast data
            try:
                # Fetch 5-day forecast
                forecast_url = f"{self.weather_service.base_url}/forecast"
                params = {
                    'q': self.current_city,
                    'appid': self.weather_service.api_key,
                    'units': 'metric'
                }
                
                import requests
                response = requests.get(forecast_url, params=params, timeout=10)
                if response.status_code == 200:
                    forecast_json = response.json()
                    # Process forecast data for chart
                    self._process_forecast_data(forecast_json)
            except Exception as e:
                self.logger.warning(f"Forecast fetch failed: {e}")
            
            # Update UI on main thread
            if self.winfo_exists():
                self.after(0, self._schedule_weather_update, weather_data)
                # Hide loading state and update timestamp
                self.after(0, self.hide_loading_state)
                
        except Exception as e:
            self.logger.error(f"Failed to fetch weather data: {e}")
            error_msg = self._get_user_friendly_error(str(e))
            try:
                if hasattr(self, 'status_label') and self.status_label.winfo_exists():
                    self.after(0, self._schedule_error_notification, error_msg)
            except tk.TclError:
                # Widget has been destroyed, ignore
                pass
            # Hide loading state on error
            try:
                self.after(0, self.hide_loading_state)
            except tk.TclError:
                # Widget has been destroyed, ignore
                pass
    
    def _get_user_friendly_error(self, error: str) -> str:
        """Convert technical errors to user-friendly messages."""
        if "401" in error or "API key" in error.lower():
            return "Invalid API key. Please check settings."
        elif "404" in error or "not found" in error.lower():
            return "City not found. Please check spelling."
        elif "connection" in error.lower():
            return "No internet connection."
        else:
            return "Unable to fetch weather data. Please try again."
    
    def _process_forecast_data(self, forecast_json):
        """Process forecast data for temperature chart."""
        try:
            forecast_list = forecast_json.get('list', [])
            
            # Update chart if it exists using the correct method
            if hasattr(self, 'temperature_chart') and self.temperature_chart.winfo_exists():
                self.after(0, self._schedule_chart_update, forecast_list)
                
        except Exception as e:
            self.logger.error(f"Error processing forecast: {e}")
    
    def _update_temperature_chart(self, chart_data):
        """Update temperature chart with new data."""
        try:
            if hasattr(self, 'temperature_chart') and self.temperature_chart.winfo_exists():
                self.temperature_chart.update_data_storage(chart_data)
                self.temperature_chart.refresh_chart_display()
        except Exception as e:
            self.logger.error(f"Error updating temperature chart: {e}")
    
    def _update_weather_display(self) -> None:
        """Update weather display with current data."""
        # Update with real data when available
        self.city_label.configure(text=self.current_city)
        self.status_label.configure(text="Data updated successfully")
        
        # Apply display enhancements
        if self.display_enhancer:
            self.display_enhancer.enhance_display()
    
    def _update_weather_display_with_real_data(self, weather_data) -> None:
        """Update weather display with real API data."""
        try:
            # Update city name - handle both dict and object location
            if hasattr(weather_data, 'location'):
                if isinstance(weather_data.location, dict):
                    city_name = weather_data.location.get('name', self.current_city)
                else:
                    city_name = weather_data.location.name
            else:
                city_name = self.current_city
            self.city_label.configure(text=city_name)
            
            # Update temperature
            if hasattr(weather_data, 'temperature'):
                self.temp_label.configure(text=f"{int(weather_data.temperature)}°C")
            
            # Update weather condition
            if hasattr(weather_data, 'description'):
                self.condition_label.configure(text=weather_data.description)
            
            # Update feels like temperature
            if hasattr(weather_data, 'feels_like'):
                self.feels_like_label.configure(text=f"🌡️ Feels like: {int(weather_data.feels_like)}°C")
            
            # Update humidity
            if hasattr(weather_data, 'humidity'):
                self.humidity_label.configure(text=f"💧 Humidity: {weather_data.humidity}%")
            
            # Update metrics grid with comprehensive weather data
            if hasattr(self, 'metric_widgets') and self.metric_widgets:
                self._update_metrics_grid(weather_data)
            
            # Update status
            self.status_label.configure(text="Weather data updated successfully")
            
            # Apply display enhancements
            if self.display_enhancer:
                self.display_enhancer.enhance_display()
                
            # Update temperature chart if available
            if hasattr(self, 'temperature_chart') and self.forecast_data:
                self.temperature_chart.update_chart_data(self.forecast_data)
                
        except Exception as e:
            self.logger.error(f"Error updating weather display: {e}")
            self.status_label.configure(text="Error displaying weather data")
    
    def _safe_update_status(self, message: str) -> None:
        """Safely update status label with existence check."""
        try:
            if hasattr(self, 'status_label') and self.status_label.winfo_exists():
                self.status_label.configure(text=message)
        except Exception as e:
            self.logger.warning(f"Failed to update status: {e}")
    
    def _safe_enhance_display(self) -> None:
        """Safely enhance display with existence checks."""
        try:
            if self.display_enhancer and self.winfo_exists():
                self.display_enhancer.enhance_display()
        except Exception as e:
            self.logger.warning(f"Display enhancement error: {e}")
    
    def _show_error_notification(self, error_msg: str) -> None:
        """Show user-friendly error notification."""
        # Update status with error message
        self._safe_update_status(f"Error: {error_msg}")
        
        # You could also implement a popup notification here
        # For now, we'll just log and update the status bar
        self.logger.warning(f"User notification: {error_msg}")
    
    def _on_search(self, event=None) -> None:
        """Handle search entry return key."""
        self._search_weather()
    
    def _search_weather(self) -> None:
        """Search for weather in specified city."""
        city = self.search_entry.get().strip()
        if city:
            self.current_city = city
            self.search_entry.delete(0, 'end')
            threading.Thread(target=self._fetch_weather_data, daemon=True).start()
    

    
    def run(self) -> None:
        """Start the application."""
        if hasattr(self, '_running') and self._running:
            self.logger.warning("Application is already running")
            return
            
        self._running = True
        self.logger.info("Starting Professional Weather Dashboard")
        try:
            self.mainloop()
        except KeyboardInterrupt:
            self.logger.info("Application interrupted by user")
        except Exception as e:
            self.logger.error(f"Application error: {str(e)}")
        finally:
            self._running = False
            self.logger.info("Professional Weather Dashboard stopped")
    
    def _manual_refresh(self):
        """Manual refresh triggered by user."""
        threading.Thread(target=self._fetch_weather_data, daemon=True).start()
    
    def _setup_auto_refresh(self):
        """Setup automatic refresh every 5 minutes."""
        # Start auto refresh cycle
        self.after(300000, self._auto_refresh_cycle)
    
    def _auto_refresh_cycle(self):
        """Auto refresh cycle method."""
        if self.winfo_exists():
            threading.Thread(target=self._fetch_weather_data, daemon=True).start()
            # Schedule next refresh
            self.after(300000, self._auto_refresh_cycle)  # 5 minutes
    
    def _update_refresh_timestamp(self):
        """Update the last refresh timestamp."""
        if hasattr(self, 'last_update_label'):
            current_time = datetime.now().strftime("%H:%M:%S")
            self.last_update_label.configure(text=f"Last updated: {current_time}")
    
    def _schedule_weather_update(self, weather_data):
        """Helper method to schedule weather display update."""
        self._update_weather_display_with_real_data(weather_data)
    
    def _schedule_error_notification(self, error_msg):
        """Helper method to schedule error notification."""
        self._show_error_notification(error_msg)
    
    def _schedule_loading_status(self):
        """Helper method to schedule loading status update."""
        self._safe_update_status("Loading weather data...")
    
    def _schedule_chart_update(self, forecast_list):
        """Helper method to schedule chart update."""
        if hasattr(self, 'temperature_chart'):
            self.temperature_chart.update_forecast(forecast_list)
    
    def show_loading_state(self):
        """Show loading indicators on all data fields."""
        loading_text = "Loading..."
        self.temp_label.configure(text=loading_text)
        self.condition_label.configure(text=loading_text)
        self.feels_like_label.configure(text=loading_text)
        self.humidity_label.configure(text=loading_text)
        
        # Disable refresh button
        if hasattr(self, 'refresh_button'):
            self.refresh_button.configure(state="disabled", text="⏳ Loading...")
    
    def hide_loading_state(self):
        """Hide loading indicators."""
        # Re-enable refresh button
        if hasattr(self, 'refresh_button'):
            self.refresh_button.configure(state="normal", text="🔄 Refresh")
        
        # Update last refresh time
        if hasattr(self, 'last_update_label'):
            current_time = datetime.now().strftime("%H:%M")
            self.last_update_label.configure(text=f"Updated: {current_time}")


if __name__ == "__main__":
    # Load environment variables
    from dotenv import load_dotenv
    import os
    
    # Load .env file from project root
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    env_path = os.path.join(project_root, '.env')
    load_dotenv(env_path)
    
    app = ProfessionalWeatherDashboard()
    app.center_window()
    app.run()