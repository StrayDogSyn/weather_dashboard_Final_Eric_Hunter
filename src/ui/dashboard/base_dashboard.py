"""Base dashboard class with core setup functionality."""

import logging
import tkinter as tk

import customtkinter as ctk
from dotenv import load_dotenv

from src.services.activity_service import ActivityService
from src.services.config_service import ConfigService
from src.services.enhanced_weather_service import (
    EnhancedWeatherService
)
from src.services.github_team_service import GitHubTeamService
from src.ui.components import (
    AnimationManager,
    ErrorManager,
    MicroInteractions,
    StatusMessageManager,
    VisualPolishManager,
    WeatherBackgroundManager,
)
from src.ui.theme import DataTerminalTheme
from src.ui.theme_manager import theme_manager
from src.utils.api_optimizer import APIOptimizer
from src.utils.cache_manager import CacheManager
from src.utils.component_recycler import ComponentRecycler
from src.utils.loading_manager import LoadingManager
from src.utils.startup_optimizer import StartupOptimizer

# Load environment variables
load_dotenv()

# Configure appearance
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")


class BaseDashboard(ctk.CTk):
    """Base dashboard class with core setup and initialization."""

    def __init__(self, config_service=None):
        super().__init__()

        # Setup logging
        self.logger = logging.getLogger(__name__)

        # Initialize performance optimization services first
        self._initialize_optimization_services()

        # Initialize core services
        self._initialize_core_services(config_service)

        # Initialize visual polish managers
        self._initialize_visual_managers()

        # Initialize theme system
        self._initialize_theme_system()

        # Initialize state variables
        self._initialize_state()

        # Configure window
        self._configure_window()

        # Setup keyboard shortcuts
        self._setup_keyboard_shortcuts()

        # Initialize enhanced settings
        self._initialize_enhanced_settings()

        self.logger.info("Base dashboard initialized successfully")

    def _initialize_optimization_services(self):
        """Initialize performance optimization services."""
        self.cache_manager = CacheManager(
            max_size_mb=100,  # 100MB cache
            enable_compression=True,
            compression_threshold=1024,  # Compress items > 1KB
            lru_factor=0.8,  # Evict when 80% full
        )
        self.startup_optimizer = StartupOptimizer()
        self.component_recycler = ComponentRecycler()
        self.api_optimizer = APIOptimizer()

    def _initialize_core_services(self, config_service):
        """Initialize core services with fallback for demo mode."""
        try:
            self.config_service = config_service or ConfigService()
            self.weather_service = EnhancedWeatherService(self.config_service)
            self.activity_service = ActivityService(self.config_service)
            github_token = (
                self.config_service.get_setting("api.github_token") if self.config_service else None
            )
            self.github_service = GitHubTeamService(github_token=github_token)
            self.loading_manager = LoadingManager()
        except Exception as e:
            self.logger.warning(f"Running in demo mode without API keys: {e}")
            self.config_service = None
            self.weather_service = None
            self.activity_service = None
            self.github_service = GitHubTeamService()  # GitHub service can work without API keys
            self.loading_manager = LoadingManager()  # Still initialize for offline mode

    def _initialize_visual_managers(self):
        """Initialize visual polish managers."""
        self.animation_manager = AnimationManager()
        self.micro_interactions = MicroInteractions()
        self.weather_background_manager = WeatherBackgroundManager(self)
        self.error_manager = ErrorManager(self)
        self.status_manager = StatusMessageManager(self)
        self.visual_polish_manager = VisualPolishManager(self)

    def _initialize_theme_system(self):
        """Initialize theme system and register observers."""
        # Initialize theme manager and register as observer
        DataTerminalTheme.add_observer(self._on_theme_changed)

        # Register visual polish managers with theme system
        theme_manager.add_observer(self.weather_background_manager.update_theme)
        theme_manager.add_observer(self.error_manager.update_theme)
        theme_manager.add_observer(self.status_manager.update_theme)
        theme_manager.add_observer(self.visual_polish_manager.update_theme)

    def _initialize_state(self):
        """Initialize state variables."""
        # Weather icons mapping
        self.weather_icons = {
            "clear": "☀️",
            "partly cloudy": "⛅",
            "cloudy": "☁️",
            "overcast": "☁️",
            "rain": "🌧️",
            "drizzle": "🌦️",
            "thunderstorm": "⛈️",
            "snow": "❄️",
            "mist": "🌫️",
            "fog": "🌫️",
        }

        # Track scheduled after() calls for cleanup
        self.scheduled_calls = []

        # Track open hourly breakdown windows
        self.open_hourly_windows = []
        self.is_destroyed = False

        # Bind cleanup to window close
        self.protocol("WM_DELETE_WINDOW", self._on_closing)

        # State
        self.current_city = "London"
        self.temp_unit = "C"  # Default temperature unit
        self.current_weather_data = None  # Store current weather for activity suggestions

        # Auto-refresh timer
        self.auto_refresh_enabled = True
        self.refresh_interval = 300000  # 5 minutes in milliseconds

    def _configure_window(self):
        """Configure window properties."""
        self.title("Professional Weather Dashboard")
        self.geometry("1400x900")
        self.minsize(1200, 800)

        # Configure grid
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

    def _setup_keyboard_shortcuts(self):
        """Setup keyboard shortcuts."""
        self.bind("<Control-r>", lambda e: self._load_weather_data())
        self.bind("<Control-j>", lambda e: self.tabview.set("Journal"))
        self.bind("<Control-w>", lambda e: self.tabview.set("Weather"))
        self.bind("<Control-a>", lambda e: self.tabview.set("Activities"))
        self.bind("<Control-s>", lambda e: self.tabview.set("Settings"))
        self.bind("<F5>", lambda e: self._load_weather_data())
        self.bind(
            "<Escape>",
            lambda e: self.search_entry.delete(0, "end") if hasattr(self, "search_entry") else None,
        )

    def _initialize_enhanced_settings(self):
        """Initialize enhanced settings with default values."""
        try:
            # Initialize settings state variables
            self.analytics_enabled = True
            self.location_history_enabled = True
            self.refresh_interval_minutes = 5
            self.refresh_interval = 300000  # 5 minutes in milliseconds
            self.quiet_hours_enabled = False
            self.quiet_start_hour = 22
            self.quiet_end_hour = 7
            self.wifi_only_refresh = False
            self.date_format = "%Y-%m-%d"
            self.time_format = "%H:%M"
            self.selected_language = "English"
            self.font_size = 12

            # Load saved settings if config service is available
            if self.config_service:
                self.analytics_enabled = self.config_service.get_setting(
                    "privacy.analytics_enabled", True
                )
                self.location_history_enabled = self.config_service.get_setting(
                    "privacy.location_history_enabled", True
                )
                self.refresh_interval_minutes = self.config_service.get_setting(
                    "refresh.interval_minutes", 5
                )
                self.quiet_hours_enabled = self.config_service.get_setting(
                    "refresh.quiet_hours_enabled", False
                )
                self.quiet_start_hour = self.config_service.get_setting(
                    "refresh.quiet_start_hour", 22
                )
                self.quiet_end_hour = self.config_service.get_setting("refresh.quiet_end_hour", 7)
                self.wifi_only_refresh = self.config_service.get_setting("refresh.wifi_only", False)
                self.date_format = self.config_service.get_setting(
                    "appearance.date_format", "%Y-%m-%d"
                )
                self.time_format = self.config_service.get_setting(
                    "appearance.time_format", "%H:%M"
                )
                self.selected_language = self.config_service.get_setting(
                    "appearance.language", "English"
                )
                self.font_size = self.config_service.get_setting("appearance.font_size", 12)

            # Schedule periodic updates
            self.after(5000, self._update_usage_stats)  # Update usage stats every 5 seconds
            self.after(10000, self._update_cache_size)  # Update cache size every 10 seconds

        except Exception as e:
            self.logger.warning(f"Failed to initialize enhanced settings: {e}")

    def _on_theme_changed(self):
        """Handle theme changes."""
        # This method should be implemented by subclasses

    def _load_weather_data(self):
        """Load weather data - to be implemented by subclasses."""

    def _update_usage_stats(self):
        """Update usage statistics - to be implemented by subclasses."""

    def _update_cache_size(self):
        """Update cache size display - to be implemented by subclasses."""

    def safe_after(self, delay, callback):
        """Safely schedule a callback with cleanup tracking."""
        if not self.is_destroyed:
            call_id = self.after(delay, callback)
            self.scheduled_calls.append(call_id)
            return call_id
        return None

    def _cleanup_scheduled_calls(self):
        """Clean up all scheduled after() calls."""
        for call_id in self.scheduled_calls:
            try:
                self.after_cancel(call_id)
            except tk.TclError:
                pass  # Call was already executed or cancelled
        self.scheduled_calls.clear()

    def _on_closing(self):
        """Handle window closing."""
        try:
            self.is_destroyed = True

            # Clean up scheduled calls
            self._cleanup_scheduled_calls()

            # Close any open hourly windows
            for window in self.open_hourly_windows[:]:
                try:
                    if window.winfo_exists():
                        window.destroy()
                except tk.TclError:
                    pass

            # Clean up services
            if hasattr(self, "loading_manager") and self.loading_manager:
                self.loading_manager.shutdown()

            # Destroy the main window
            self.destroy()

        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")
            # Force destroy if cleanup fails
            try:
                self.destroy()
            except Exception:
                pass

    def center_window(self):
        """Center the window on screen."""
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f"{width}x{height}+{x}+{y}")
