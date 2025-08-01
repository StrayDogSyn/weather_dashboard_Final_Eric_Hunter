"""Professional Weather Dashboard

Main dashboard application with weather data, analytics, and journaling features.
Updated to use SafeWidget for enhanced lifecycle management.
"""

from typing import List, Optional

import customtkinter as ctk

# Suppress CustomTkinter DPI scaling errors
try:
    import os
    os.environ["CTK_DISABLE_DPI_SCALING"] = "1"
except Exception:
    pass

from ..models.weather_models import ForecastData, WeatherData
from ..services.config_service import ConfigService
from ..services.enhanced_weather_service import EnhancedWeatherService
from ..services.journal_service import JournalService
from ..services.logging_service import LoggingService
from ..services.thread_safe_service import ThreadSafeUIUpdater

# Import safe widgets and components
from .safe_widgets import SafeCTk
from .components.secure_api_manager import SecureAPIManager
from .theme import DataTerminalTheme
from .dashboard.tab_manager import TabManagerMixin
from .dashboard.ui_components import UIComponentsMixin
from .dashboard.weather_display_enhancer import WeatherDisplayEnhancer
from .dashboard.weather_handler import WeatherHandlerMixin


class ProfessionalWeatherDashboard(SafeCTk):
    """Professional weather dashboard with clean, minimal design and safe widget lifecycle."""

    # Data Terminal color scheme
    ACCENT_COLOR = DataTerminalTheme.PRIMARY  # Neon green
    BACKGROUND = DataTerminalTheme.BACKGROUND  # Dark background
    CARD_COLOR = DataTerminalTheme.CARD_BG  # Dark card background
    TEXT_PRIMARY = DataTerminalTheme.TEXT  # Light text
    TEXT_SECONDARY = DataTerminalTheme.TEXT_SECONDARY  # Medium gray text
    BORDER_COLOR = DataTerminalTheme.BORDER  # Dark border

    def __init__(self, config_service=None):
        """Initialize the professional weather dashboard."""
        super().__init__()
        
        # Initialize services
        self.config_service = config_service or ConfigService()
        self.weather_service = EnhancedWeatherService(self.config_service)
        self.journal_service = JournalService()
        self.logging_service = LoggingService()
        self.ui_updater = ThreadSafeUIUpdater(self)
        
        # Initialize components
        self.api_manager = SecureAPIManager(self, self.config_service)
        self.weather_enhancer = WeatherDisplayEnhancer(self)
        
        # Configure theme
        DataTerminalTheme.configure_customtkinter()
        
        # Setup UI
        self._configure_window()
        self._create_widgets()
        
        # Initialize data
        self.current_weather: Optional[WeatherData] = None
        self.forecast_data: Optional[List[ForecastData]] = None
        
        # Setup cleanup
        self.protocol("WM_DELETE_WINDOW", self._on_closing)
        
    def _configure_window(self) -> None:
        """Configure main window properties with enhanced styling."""
        self.title("🌤️ Professional Weather Dashboard - CodeFront Analytics")
        self.configure(fg_color=self.BACKGROUND)
        
        # Set window size and position
        self.geometry("1800x1200")
        self.minsize(1200, 800)
        
    def _create_widgets(self) -> None:
        """Create all UI widgets with clean design."""
        # Main container
        self.main_container = ctk.CTkFrame(self, fg_color="transparent")
        self.main_container.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Header
        self._create_header()
        
        # Content area
        self._create_content_area()
        
        # Status bar
        self._create_status_bar()
        
    def _create_header(self) -> None:
        """Create the header section."""
        self.header_frame = ctk.CTkFrame(self.main_container, height=80, fg_color=self.CARD_COLOR)
        self.header_frame.pack(fill="x", pady=(0, 20))
        self.header_frame.pack_propagate(False)
        
        # Title
        self.title_label = ctk.CTkLabel(
            self.header_frame,
            text="🌤️ Professional Weather Dashboard",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color=self.ACCENT_COLOR
        )
        self.title_label.pack(side="left", padx=20, pady=20)
        
    def _create_content_area(self) -> None:
        """Create the main content area with tabs."""
        self.content_frame = ctk.CTkFrame(self.main_container, fg_color=self.CARD_COLOR)
        self.content_frame.pack(fill="both", expand=True, pady=(0, 20))
        
        # Create tabview
        self.tabview = ctk.CTkTabview(self.content_frame, fg_color=self.BACKGROUND)
        self.tabview.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Add tabs
        self._create_tabs()
        
    def _create_tabs(self) -> None:
        """Create all dashboard tabs."""
        # Weather tab
        self.weather_tab = self.tabview.add("Weather")
        self._setup_weather_tab()
        
        # Journal tab
        self.journal_tab = self.tabview.add("Journal")
        self._setup_journal_tab()
        
        # Activities tab
        self.activities_tab = self.tabview.add("Activities")
        self._setup_activities_tab()
        
        # Settings tab
        self.settings_tab = self.tabview.add("Settings")
        self._setup_settings_tab()
        
    def _setup_weather_tab(self) -> None:
        """Setup the weather tab content."""
        weather_label = ctk.CTkLabel(
            self.weather_tab,
            text="Weather data will be displayed here",
            font=ctk.CTkFont(size=16),
            text_color=self.TEXT_PRIMARY
        )
        weather_label.pack(pady=50)
        
    def _setup_journal_tab(self) -> None:
        """Setup the journal tab content."""
        journal_label = ctk.CTkLabel(
            self.journal_tab,
            text="Journal entries will be displayed here",
            font=ctk.CTkFont(size=16),
            text_color=self.TEXT_PRIMARY
        )
        journal_label.pack(pady=50)
        
    def _setup_activities_tab(self) -> None:
        """Setup the activities tab content."""
        activities_label = ctk.CTkLabel(
            self.activities_tab,
            text="Activity suggestions will be displayed here",
            font=ctk.CTkFont(size=16),
            text_color=self.TEXT_PRIMARY
        )
        activities_label.pack(pady=50)
        
    def _setup_settings_tab(self) -> None:
        """Setup the settings tab content."""
        settings_label = ctk.CTkLabel(
            self.settings_tab,
            text="Settings will be displayed here",
            font=ctk.CTkFont(size=16),
            text_color=self.TEXT_PRIMARY
        )
        settings_label.pack(pady=50)
        
    def _create_status_bar(self) -> None:
        """Create the status bar."""
        self.status_frame = ctk.CTkFrame(self.main_container, height=30, fg_color=self.CARD_COLOR)
        self.status_frame.pack(fill="x")
        self.status_frame.pack_propagate(False)
        
        self.status_label = ctk.CTkLabel(
            self.status_frame,
            text="Ready",
            font=ctk.CTkFont(size=12),
            text_color=self.TEXT_SECONDARY
        )
        self.status_label.pack(side="left", padx=10, pady=5)
        
    def update_weather_data(self, weather_data: WeatherData, forecast_data: List[ForecastData] = None) -> None:
        """Update the dashboard with new weather data."""
        self.current_weather = weather_data
        self.forecast_data = forecast_data or []
        
        # Update status
        self.status_label.configure(text=f"Weather updated for {weather_data.location}")
        
        # Schedule UI update using safe_after
        self.safe_after(100, self._refresh_weather_display)
        
    def _refresh_weather_display(self) -> None:
        """Refresh the weather display with current data."""
        if self.current_weather:
            # Update weather tab content
            pass
            
    def center_window(self) -> None:
        """Center the window on screen."""
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f"{width}x{height}+{x}+{y}")
        
    def _on_closing(self) -> None:
        """Handle window closing with proper cleanup."""
        try:
            # Cleanup any pending operations
            self.cleanup_after_callbacks()
            
            # Close services
            if hasattr(self, 'weather_service'):
                self.weather_service.cleanup()
            if hasattr(self, 'journal_service'):
                self.journal_service.cleanup()
                
        except Exception as e:
            print(f"Error during cleanup: {e}")
        finally:
            self.quit()
            self.destroy()
            
    def __del__(self) -> None:
        """Cleanup when object is destroyed."""
        try:
            self.cleanup_after_callbacks()
        except:
            pass