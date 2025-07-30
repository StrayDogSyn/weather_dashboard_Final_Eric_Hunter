"""Professional Weather Dashboard - Clean Capstone Design

Minimalist weather dashboard with professional 2-column layout,
focused on essential information and clean aesthetics.
"""

import customtkinter as ctk
from typing import Optional, List
import threading
from datetime import datetime
import logging
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import numpy as np
from ui.components.temperature_chart import TemperatureChart

from services.enhanced_weather_service import EnhancedWeatherService
from services.config_service import ConfigService
from models.weather_models import WeatherData, ForecastData
from services.logging_service import LoggingService
from ui.theme import DataTerminalTheme


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
        """Override after method to handle CustomTkinter DPI scaling errors."""
        try:
            return super().after(ms, func, *args)
        except Exception as e:
            error_msg = str(e).lower()
            if "invalid command name" in error_msg and ("update" in error_msg or "check_dpi_scaling" in error_msg):
                # Suppress CustomTkinter DPI scaling errors
                self.logger.debug(f"Suppressed CustomTkinter internal error: {e}")
                return None
            else:
                # Re-raise other errors
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
            base_font_size = max(12, min(16, width // 120))
            
            # Update chart dimensions
            if hasattr(self, 'temperature_chart') and hasattr(self.temperature_chart, 'update_size'):
                chart_width = max(600, width * 0.6)
                chart_height = max(400, height * 0.4)
                self.temperature_chart.update_size(chart_width, chart_height)
            
            # Update weather card scaling
            if hasattr(self, 'weather_card') and self.weather_card.winfo_exists():
                card_width = max(300, width * 0.25)
                self.weather_card.configure(width=card_width)
            
            # Update header elements scaling
            if hasattr(self, 'search_entry') and self.search_entry.winfo_exists():
                search_width = max(250, min(400, width * 0.25))
                self.search_entry.configure(width=search_width)
            
            # Update main frame padding based on screen size
            if hasattr(self, 'main_frame') and self.main_frame.winfo_exists():
                padding = max(10, min(30, width // 80))
                self.main_frame.grid_configure(padx=padding, pady=padding)
            
            # Update font sizes for responsive text
            title_font_size = max(20, min(28, width // 80))
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
            self.geometry("1920x1080")
            self.state('zoomed')
            self.minsize(1200, 800)
            
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
    
    def _create_widgets(self) -> None:
        """Create all UI widgets with clean design."""
        # Header
        self._create_header()
        
        # Main content area
        self._create_main_content()
        
        # Status bar
        self._create_status_bar()
    
    def _create_header(self) -> None:
        """Create enhanced header with title and search."""
        self.header_frame = ctk.CTkFrame(
            self,
            fg_color=self.CARD_COLOR,
            corner_radius=0,
            height=120,  # Increased height for larger banner
            border_width=2,
            border_color=self.ACCENT_COLOR
        )
        
        # Header accent strip for enhanced visual appeal
        self.header_accent = ctk.CTkFrame(
            self.header_frame,
            fg_color=self.ACCENT_COLOR,
            height=3,
            corner_radius=0
        )
        
        # Create title container as instance variable first
        self.title_container = ctk.CTkFrame(self.header_frame, fg_color="transparent")
        
        # Title glow frame for enhanced visual effects
        self.title_glow_frame = ctk.CTkFrame(
            self.title_container,
            fg_color="transparent",
            border_width=1,
            border_color=self.ACCENT_COLOR,
            corner_radius=8
        )
        
        # Enhanced App title with larger font and visual effects
        self.title_label = ctk.CTkLabel(
            self.title_glow_frame,
            text="⚡ PROJECT CODEFRONT",
            font=(DataTerminalTheme.FONT_FAMILY, 36, "bold"),  # Increased from 24 to 36
            text_color=self.ACCENT_COLOR  # Using neon green for pop
        )
        
        # Add subtitle for enhanced branding
        self.subtitle_label = ctk.CTkLabel(
            self.title_container,
            text="Advanced Weather Intelligence System",
            font=(DataTerminalTheme.FONT_FAMILY, 14, "normal"),
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
        self.weather_tab.grid_columnconfigure(1, weight=1)
        self.weather_tab.grid_rowconfigure(0, weight=1)
        
        # Create left column - Current weather
        self._create_current_weather_in_tab()
        
        # Create right column - Analytics
        self._create_analytics_in_tab()
    
    def _create_current_weather_in_tab(self) -> None:
        """Create current weather section within the weather tab."""
        # Create a container for the section
        self.weather_section = ctk.CTkFrame(
            self.weather_tab,
            fg_color="transparent"
        )
        
        # Section title
        self.weather_title = ctk.CTkLabel(
            self.weather_section,
            text="CURRENT WEATHER",
            font=(DataTerminalTheme.FONT_FAMILY, DataTerminalTheme.FONT_SIZE_MEDIUM, "bold"),
            text_color=self.ACCENT_COLOR,
            anchor="w"
        )
        self.weather_title.pack(anchor="w", padx=10, pady=(0, 10))
        
        # Create the weather card
        self._create_weather_card()
        
        # Position the section in the weather tab
        self.weather_section.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
    
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
        """Create comprehensive weather metrics grid."""
        # Create metrics grid frame
        self.metrics_grid = ctk.CTkFrame(
            self.weather_section,
            fg_color="transparent"
        )
        self.metrics_grid.pack(fill="x", padx=10, pady=(10, 0))
        
        # Configure grid layout (3 columns, 3 rows)
        for i in range(3):
            self.metrics_grid.grid_columnconfigure(i, weight=1, uniform="col")
        
        # Create metric boxes
        metrics = [
            ("HUMIDITY", "65%", 0, 0),
            ("PRESSURE", "1013 hPa", 0, 1),
            ("VISIBILITY", "10 km", 0, 2),
            ("WIND SPEED", "15 km/h", 1, 0),
            ("WIND DIR", "NW", 1, 1),
            ("CLOUDINESS", "40%", 1, 2),
            ("MIN TEMP", "15°C", 2, 0),
            ("MAX TEMP", "22°C", 2, 1),
            ("UV INDEX", "3", 2, 2)
        ]
        
        for label, value, row, col in metrics:
            metric_frame = ctk.CTkFrame(
                self.metrics_grid,
                fg_color=self.CARD_COLOR,
                corner_radius=8,
                border_width=1,
                border_color=self.BORDER_COLOR,
                height=60
            )
            metric_frame.grid(row=row, column=col, padx=2, pady=2, sticky="ew")
            metric_frame.grid_propagate(False)
            
            # Metric label
            metric_label = ctk.CTkLabel(
                metric_frame,
                text=label,
                font=(DataTerminalTheme.FONT_FAMILY, 10, "bold"),
                text_color=self.TEXT_SECONDARY
            )
            metric_label.pack(pady=(8, 0))
            
            # Metric value
            metric_value = ctk.CTkLabel(
                metric_frame,
                text=value,
                font=(DataTerminalTheme.FONT_FAMILY, 14, "bold"),
                text_color=self.ACCENT_COLOR
            )
            metric_value.pack()
    
    def _create_analytics_in_tab(self) -> None:
        """Create temperature forecast panel within the weather tab."""
        # Create a container for the analytics section
        self.analytics_section = ctk.CTkFrame(
            self.weather_tab,
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
        self.journal_tab.grid_rowconfigure(1, weight=1)
        
        # Journal title
        journal_title = ctk.CTkLabel(
            self.journal_tab,
            text="WEATHER JOURNAL",
            font=(DataTerminalTheme.FONT_FAMILY, DataTerminalTheme.FONT_SIZE_MEDIUM, "bold"),
            text_color=self.ACCENT_COLOR
        )
        journal_title.grid(row=0, column=0, sticky="w", padx=20, pady=(20, 10))
        
        # Journal content frame
        journal_frame = ctk.CTkFrame(
            self.journal_tab,
            fg_color=self.CARD_COLOR,
            corner_radius=16,
            border_width=1,
            border_color=self.BORDER_COLOR
        )
        journal_frame.grid(row=1, column=0, sticky="nsew", padx=20, pady=(0, 20))
        
        # Placeholder content
        placeholder_label = ctk.CTkLabel(
            journal_frame,
            text="📔 Weather Diary & Mood Tracking\n\nComing Soon:\n• Daily weather reflections\n• Mood correlation analysis\n• Personal weather insights\n• Historical journal entries",
            font=(DataTerminalTheme.FONT_FAMILY, 16),
            text_color=self.TEXT_SECONDARY,
            justify="left"
        )
        placeholder_label.pack(expand=True, padx=40, pady=40)
    
    def _create_activities_tab(self) -> None:
        """Create the activities tab content for AI-powered suggestions."""
        # Configure activities tab
        self.activities_tab.grid_columnconfigure(0, weight=1)
        self.activities_tab.grid_rowconfigure(1, weight=1)
        
        # Activities title
        activities_title = ctk.CTkLabel(
            self.activities_tab,
            text="ACTIVITY SUGGESTIONS",
            font=(DataTerminalTheme.FONT_FAMILY, DataTerminalTheme.FONT_SIZE_MEDIUM, "bold"),
            text_color=self.ACCENT_COLOR
        )
        activities_title.grid(row=0, column=0, sticky="w", padx=20, pady=(20, 10))
        
        # Activities content frame
        activities_frame = ctk.CTkFrame(
            self.activities_tab,
            fg_color=self.CARD_COLOR,
            corner_radius=16,
            border_width=1,
            border_color=self.BORDER_COLOR
        )
        activities_frame.grid(row=1, column=0, sticky="nsew", padx=20, pady=(0, 20))
        
        # Placeholder content
        placeholder_label = ctk.CTkLabel(
            activities_frame,
            text="🎯 AI-Powered Activity Recommendations\n\nComing Soon:\n• Weather-based activity suggestions\n• Indoor/outdoor recommendations\n• Seasonal activity planning\n• Personalized suggestions based on preferences",
            font=(DataTerminalTheme.FONT_FAMILY, 16),
            text_color=self.TEXT_SECONDARY,
            justify="left"
        )
        placeholder_label.pack(expand=True, padx=40, pady=40)
    
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
        
        # Settings content frame
        settings_frame = ctk.CTkFrame(
            self.settings_tab,
            fg_color=self.CARD_COLOR,
            corner_radius=16,
            border_width=1,
            border_color=self.BORDER_COLOR
        )
        settings_frame.grid(row=1, column=0, sticky="nsew", padx=20, pady=(0, 20))
        
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
        """Setup the layout with proper spacing for tabbed interface."""
        # Header
        self.header_frame.grid(row=0, column=0, sticky="ew", padx=0, pady=0)
        self.header_frame.grid_propagate(False)
        
        # Header accent strip
        self.header_accent.pack(fill="x", side="top")
        
        # Header content - Enhanced title section
        self.title_container.pack(side="left", padx=40, pady=20)
        
        # Title glow frame
        self.title_glow_frame.pack(anchor="w", padx=10, pady=5)
        
        # Title and subtitle positioning
        self.title_label.pack(anchor="w", pady=(0, 5))
        self.subtitle_label.pack(anchor="center", pady=(0, 0))
        
        # Search area on the right
        self.search_container.pack(side="right", padx=40, pady=20)
        
        # Search controls
        self.search_controls.pack()
        
        self.search_entry.pack(side="left", padx=(0, 10))
        self.search_button.pack(side="left")
        
        # Current location below search
        self.current_location_label.pack(pady=(5, 0))
        
        # Main content (now contains tabview)
        self.main_frame.grid(row=1, column=0, sticky="nsew", padx=20, pady=20)
        
        # Weather card layout (within weather tab)
        self.weather_card.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Weather card content
        self.city_label.pack(pady=(40, 10))
        self.temp_label.pack(pady=10)
        self.condition_label.pack(pady=(0, 30))
        
        self.info_frame.pack(fill="x", padx=40, pady=(0, 40))
        self.feels_like_label.pack(pady=5)
        self.humidity_label.pack(pady=5)
        
        # Analytics card layout (within weather tab)
        self.analytics_card.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Status bar
        self.status_frame.grid(row=2, column=0, sticky="ew", padx=0, pady=0)
        self.status_label.pack(side="left", padx=20, pady=10)
    
    def _load_initial_data(self) -> None:
        """Load initial weather data."""
        threading.Thread(target=self._fetch_weather_data, daemon=True).start()
    
    def _fetch_weather_data(self) -> None:
        """Fetch real weather data from API."""
        try:
            # Show loading state - check if widget exists first
            if hasattr(self, 'status_label') and self.status_label.winfo_exists():
                self.after(0, lambda: self._safe_update_status("Loading weather data..."))
            
            # Get real weather data
            weather_data = self.weather_service.get_enhanced_weather(self.current_city)
            
            # Store the data
            self.current_weather = weather_data
            
            # Note: Forecast data will be implemented in future updates
            # For now, we'll focus on current weather data
            
            # Update UI on main thread - check if widget exists first
            if self.winfo_exists():
                self.after(0, lambda: self._update_weather_display_with_real_data(weather_data))
            
        except Exception as e:
            self.logger.error(f"Failed to fetch weather data: {e}")
            error_msg = self._get_user_friendly_error(str(e))
            if hasattr(self, 'status_label') and self.status_label.winfo_exists():
                self.after(0, lambda: self._show_error_notification(error_msg))
    
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


# Removed duplicate main() function and __main__ block
# Main application entry point is now exclusively in main.py