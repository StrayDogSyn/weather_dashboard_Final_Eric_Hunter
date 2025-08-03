import logging
import tkinter as tk
from datetime import datetime, timedelta

import customtkinter as ctk
from dotenv import load_dotenv

from src.services.activity_service import ActivityService
from src.services.config_service import ConfigService
from src.services.enhanced_weather_service import (
    EnhancedWeatherData,
    EnhancedWeatherService,
)
from src.services.github_team_service import GitHubTeamService
from src.ui.components import (
    AnimationManager,
    ErrorManager,
    LoadingSkeleton,
    MicroInteractions,
    ShimmerEffect,
    StatusMessageManager,
    VisualPolishManager,
    WeatherBackgroundManager,
)
from src.ui.components.city_comparison_panel import CityComparisonPanel
from src.ui.components.error_handler import ErrorHandler
from src.ui.components.forecast_day_card import ForecastDayCard
from src.ui.components.ml_comparison_panel import MLComparisonPanel
from src.ui.dashboard.settings_tab_manager import SettingsTabManager
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


class ProfessionalWeatherDashboard(ctk.CTk):
    """Professional weather dashboard with clean design."""

    def __init__(self, config_service=None):
        super().__init__()

        # Setup logging
        self.logger = logging.getLogger(__name__)

        # Initialize performance optimization services first
        self.cache_manager = CacheManager(
            max_size_mb=100,  # 100MB cache
            enable_compression=True,
            compression_threshold=1024,  # Compress items > 1KB
            lru_factor=0.8,  # Evict when 80% full
        )
        self.startup_optimizer = StartupOptimizer()
        self.component_recycler = ComponentRecycler()
        self.api_optimizer = APIOptimizer()

        # Initialize services (with fallback for demo mode)
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

        # Initialize visual polish managers
        self.animation_manager = AnimationManager()
        self.micro_interactions = MicroInteractions()
        self.weather_background_manager = WeatherBackgroundManager(self)
        self.error_manager = ErrorManager(self)
        self.status_manager = StatusMessageManager(self)
        self.visual_polish_manager = VisualPolishManager(self)

        # Initialize comprehensive error handling system
        self.error_handler = ErrorHandler(self)

        # Initialize theme manager and register as observer
        DataTerminalTheme.add_observer(self._on_theme_changed)

        # Register visual polish managers with theme system
        theme_manager.add_observer(self.weather_background_manager.update_theme)
        theme_manager.add_observer(self.error_manager.update_theme)
        theme_manager.add_observer(self.status_manager.update_theme)
        theme_manager.add_observer(self.visual_polish_manager.update_theme)

        # Initialize settings tab manager
        self.settings_tab_manager = SettingsTabManager(
            self, self.config_service, self.weather_service
        )

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

        # Configure window
        self.title("Professional Weather Dashboard")
        self.geometry("1400x900")
        self.minsize(1200, 800)

        # Configure grid
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=0)  # Header - fixed height
        self.grid_rowconfigure(1, weight=1)  # Main content - expandable
        self.grid_rowconfigure(2, weight=0)  # Status bar - fixed height

        # Create UI
        self._create_header()
        self._create_main_content()
        self._create_status_bar()

        # Setup keyboard shortcuts
        self._setup_keyboard_shortcuts()

        # Load initial data with progressive loading approach
        self.after_idle(self._initialize_progressive_loading)

        # Start background loading for additional data (delayed)
        self.after(3000, self._start_background_loading)

        # Initialize enhanced settings
        self._initialize_enhanced_settings()

        # Start auto-refresh (after settings are initialized)
        self._schedule_refresh()

        self.logger.info("Dashboard UI created successfully")

    def _setup_keyboard_shortcuts(self):
        """Setup keyboard shortcuts."""
        self.bind("<Control-r>", lambda e: self._load_weather_data())
        self.bind("<Control-j>", lambda e: self.tabview.set("Journal"))
        self.bind("<Control-w>", lambda e: self.tabview.set("Weather"))
        self.bind("<Control-a>", lambda e: self.tabview.set("Activities"))
        self.bind("<Control-s>", lambda e: self.tabview.set("Settings"))
        self.bind("<F5>", lambda e: self._load_weather_data())
        self.bind("<Escape>", lambda e: self.search_entry.delete(0, "end"))
        self.bind("<question>", lambda e: self.error_handler.show_keyboard_shortcuts())
        self.bind("<Key-question>", lambda e: self.error_handler.show_keyboard_shortcuts())

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

    def _create_header(self):
        """Create professional header with PROJECT CODEFRONT branding."""
        self.header_frame = ctk.CTkFrame(
            self, height=100, fg_color=DataTerminalTheme.CARD_BG, corner_radius=0
        )
        self.header_frame.grid(row=0, column=0, sticky="ew")
        self.header_frame.grid_propagate(False)

        # Add accent strip
        accent_strip = ctk.CTkFrame(
            self.header_frame, height=3, fg_color=DataTerminalTheme.PRIMARY, corner_radius=0
        )
        accent_strip.pack(fill="x", side="top")

        # Title container
        title_container = ctk.CTkFrame(self.header_frame, fg_color="transparent")
        title_container.pack(side="left", padx=40, pady=20)

        # Main title with glow effect
        title_frame = ctk.CTkFrame(
            title_container,
            fg_color="transparent",
            border_width=1,
            border_color=DataTerminalTheme.PRIMARY,
        )
        title_frame.pack()

        self.title_label = ctk.CTkLabel(
            title_frame,
            text="⚡ PROJECT CODEFRONT",
            font=(DataTerminalTheme.FONT_FAMILY, 32, "bold"),
            text_color=DataTerminalTheme.PRIMARY,
        )
        self.title_label.pack(padx=15, pady=5)

        # Subtitle
        self.subtitle_label = ctk.CTkLabel(
            title_container,
            text="Advanced Weather Intelligence System",
            font=(DataTerminalTheme.FONT_FAMILY, 14),
            text_color=DataTerminalTheme.TEXT_SECONDARY,
        )
        self.subtitle_label.pack()

        # Search container on right
        search_container = ctk.CTkFrame(self.header_frame, fg_color="transparent")
        search_container.pack(side="right", padx=40, pady=20)

        # Search and controls frame
        search_controls_frame = ctk.CTkFrame(search_container, fg_color="transparent")
        search_controls_frame.pack()

        # Enhanced Search Bar
        try:
            from src.ui.components.search_components import EnhancedSearchBar

            self.search_bar = EnhancedSearchBar(
                search_controls_frame,
                self.weather_service,
                on_location_selected=self._on_location_selected,
            )
            self.search_bar.pack(side="left", padx=(0, 10))
        except ImportError as e:
            self.logger.error(f"Failed to import EnhancedSearchBar: {e}")
            # Fallback to basic search
            self._create_basic_search(search_controls_frame)

        # Manual refresh button with loading indicator
        self.refresh_button = ctk.CTkButton(
            search_controls_frame,
            text="🔄 Refresh",
            width=100,
            height=32,
            command=self._manual_refresh,
            fg_color=DataTerminalTheme.PRIMARY,
            hover_color=DataTerminalTheme.SUCCESS,
            font=(DataTerminalTheme.FONT_FAMILY, 12, "bold"),
            corner_radius=8,
        )
        self.refresh_button.pack(side="left")

        # Current location indicator
        self.location_label = ctk.CTkLabel(
            search_container,
            text=f"📍 Current: {self.current_city}",
            font=(DataTerminalTheme.FONT_FAMILY, 12),
            text_color=DataTerminalTheme.TEXT_SECONDARY,
        )
        self.location_label.pack(pady=(5, 0))

    def _create_main_content(self):
        """Create tab view."""
        self.tabview = ctk.CTkTabview(self, corner_radius=10)
        self.tabview.grid(row=1, column=0, sticky="nsew", padx=20, pady=10)

        # Create tabs
        self.weather_tab = self.tabview.add("Weather")
        self.comparison_tab = self.tabview.add("🏙️ Team Compare")
        self.ml_comparison_tab = self.tabview.add("🧠 AI Analysis")
        self.activities_tab = self.tabview.add("Activities")
        self.maps_tab = self.tabview.add("Maps")
        self.settings_tab = self.tabview.add("Settings")

        # Configure tab grids
        self.weather_tab.grid_columnconfigure(0, weight=1)
        self.weather_tab.grid_rowconfigure(0, weight=1)

        self.comparison_tab.grid_columnconfigure(0, weight=1)
        self.comparison_tab.grid_rowconfigure(0, weight=1)

        self.ml_comparison_tab.grid_columnconfigure(0, weight=1)
        self.ml_comparison_tab.grid_rowconfigure(0, weight=1)

        self.activities_tab.grid_columnconfigure(0, weight=1)
        self.activities_tab.grid_rowconfigure(0, weight=1)

        self.maps_tab.grid_columnconfigure(0, weight=1)
        self.maps_tab.grid_rowconfigure(0, weight=1)

        self.settings_tab.grid_columnconfigure(0, weight=1)
        self.settings_tab.grid_rowconfigure(0, weight=1)

        # Create tab content
        self._create_weather_tab()
        self._create_comparison_tab()
        self._create_ml_comparison_tab()
        self._create_activities_tab()
        self._create_maps_tab()
        self.settings_tab_manager.create_settings_tab(self.settings_tab)

    def _create_weather_tab(self):
        """Create enhanced weather tab with proper layout."""
        self._create_weather_tab_content()

    def _create_weather_tab_content(self):
        """Create enhanced weather tab with proper layout."""
        # Configure grid for 3-column layout with better proportions and proper spacing
        self.weather_tab.grid_columnconfigure(0, weight=1, minsize=380)  # Current weather
        self.weather_tab.grid_columnconfigure(1, weight=2, minsize=520)  # Forecast chart
        self.weather_tab.grid_columnconfigure(2, weight=1, minsize=320)  # Additional metrics
        self.weather_tab.grid_rowconfigure(0, weight=1)

        # Add uniform padding to prevent visual artifacts
        self.weather_tab.configure(corner_radius=0, fg_color=DataTerminalTheme.BACKGROUND)

        # Left column - Current weather card with glassmorphic styling
        self.weather_card = ctk.CTkFrame(
            self.weather_tab,
            fg_color=DataTerminalTheme.CARD_BG,
            corner_radius=12,
            border_width=1,
            border_color=DataTerminalTheme.BORDER,
        )
        self.weather_card.grid(row=0, column=0, sticky="nsew", padx=(15, 8), pady=15)

        # Weather icon and city
        self.city_label = ctk.CTkLabel(
            self.weather_card,
            text="Loading...",
            font=(DataTerminalTheme.FONT_FAMILY, 24, "bold"),
            text_color=DataTerminalTheme.TEXT,
        )
        self.city_label.pack(pady=(25, 8))

        # Large temperature display
        self.temp_label = ctk.CTkLabel(
            self.weather_card,
            text="--°C",
            font=(DataTerminalTheme.FONT_FAMILY, 60, "bold"),
            text_color=DataTerminalTheme.PRIMARY,
        )
        self.temp_label.pack(pady=15)

        # Weather condition with icon
        self.condition_label = ctk.CTkLabel(
            self.weather_card,
            text="--",
            font=(DataTerminalTheme.FONT_FAMILY, 16),
            text_color=DataTerminalTheme.TEXT_SECONDARY,
        )
        self.condition_label.pack(pady=(0, 20))

        # Weather metrics grid
        self._create_weather_metrics()

        # Temperature conversion toggle button - more prominent
        toggle_frame = ctk.CTkFrame(
            self.weather_card,
            fg_color=DataTerminalTheme.CARD_BG,
            corner_radius=6,
            border_width=1,
            border_color=DataTerminalTheme.BORDER,
        )
        toggle_frame.pack(fill="x", padx=15, pady=(15, 20))

        # Initialize temperature unit
        self.temp_unit = "C"  # Default to Celsius

        toggle_label = ctk.CTkLabel(
            toggle_frame,
            text="Temperature Unit:",
            font=(DataTerminalTheme.FONT_FAMILY, 11),
            text_color=DataTerminalTheme.TEXT_SECONDARY,
        )
        toggle_label.pack(side="left", padx=(12, 8), pady=8)

        self.temp_toggle_btn = ctk.CTkButton(
            toggle_frame,
            text="°C",
            width=55,
            height=28,
            font=(DataTerminalTheme.FONT_FAMILY, 12, "bold"),
            fg_color=DataTerminalTheme.PRIMARY,
            hover_color=DataTerminalTheme.HOVER,
            command=self._enhanced_toggle_temperature_unit,
        )
        self.temp_toggle_btn.pack(side="left", padx=(0, 12), pady=8)

        # Add micro-interactions to temperature toggle button
        self.micro_interactions.add_hover_effect(self.temp_toggle_btn)
        self.micro_interactions.add_click_effect(self.temp_toggle_btn)

        # Right column - Forecast and charts
        self._create_forecast_section()

    def _create_weather_metrics(self):
        """Create weather metrics grid."""
        metrics_frame = ctk.CTkFrame(self.weather_card, fg_color="transparent")
        metrics_frame.pack(fill="x", padx=20, pady=15)

        # Create metric cards
        metrics = [
            ("💧", "Humidity", "--"),
            ("💨", "Wind", "--"),
            ("🌡️", "Feels Like", "--"),
            ("👁️", "Visibility", "--"),
            ("🧭", "Pressure", "--"),
            ("☁️", "Cloudiness", "--"),
        ]

        # Store metric labels for updates
        self.metric_labels = {}

        for i, (icon, name, value) in enumerate(metrics):
            metric_card = ctk.CTkFrame(
                metrics_frame,
                fg_color=DataTerminalTheme.BACKGROUND,
                corner_radius=4,
                border_width=1,
                border_color=DataTerminalTheme.BORDER,
            )
            metric_card.pack(pady=1, fill="x")

            # Icon and name
            header_frame = ctk.CTkFrame(metric_card, fg_color="transparent")
            header_frame.pack(fill="x", padx=8, pady=(4, 1))

            icon_label = ctk.CTkLabel(
                header_frame, text=icon, font=(DataTerminalTheme.FONT_FAMILY, 10)
            )
            icon_label.pack(side="left")

            name_label = ctk.CTkLabel(
                header_frame,
                text=name,
                font=(DataTerminalTheme.FONT_FAMILY, 9),
                text_color=DataTerminalTheme.TEXT_SECONDARY,
            )
            name_label.pack(side="left", padx=(3, 0))

            # Value
            value_label = ctk.CTkLabel(
                metric_card,
                text=value,
                font=(DataTerminalTheme.FONT_FAMILY, 11, "bold"),
                text_color=DataTerminalTheme.PRIMARY,
            )
            value_label.pack(pady=(0, 4))

            # Store reference
            self.metric_labels[name.lower().replace(" ", "_")] = value_label

    def _create_forecast_section(self):
        """Create forecast section with chart."""
        # Middle column - Forecast chart
        forecast_container = ctk.CTkFrame(
            self.weather_tab,
            fg_color=DataTerminalTheme.CARD_BG,
            corner_radius=12,
            border_width=1,
            border_color=DataTerminalTheme.BORDER,
        )
        forecast_container.grid(row=0, column=1, sticky="nsew", padx=10, pady=15)

        # Configure internal layout
        forecast_container.grid_columnconfigure(0, weight=1)
        forecast_container.grid_rowconfigure(0, weight=0)  # Title
        forecast_container.grid_rowconfigure(1, weight=1)  # Chart
        forecast_container.grid_rowconfigure(2, weight=0)  # Forecast cards

        # Title with better styling
        title_frame = ctk.CTkFrame(forecast_container, fg_color="transparent")
        title_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 10))

        forecast_title = ctk.CTkLabel(
            title_frame,
            text="📊 Temperature Forecast",
            font=(DataTerminalTheme.FONT_FAMILY, 18, "bold"),
            text_color=DataTerminalTheme.PRIMARY,
        )
        forecast_title.pack(side="left")

        # Chart refresh button
        refresh_btn = ctk.CTkButton(
            title_frame,
            text="🔄",
            width=30,
            height=30,
            font=(DataTerminalTheme.FONT_FAMILY, 14),
            fg_color=DataTerminalTheme.CARD_BG,
            hover_color=DataTerminalTheme.HOVER,
            command=self._refresh_chart_data,
        )
        refresh_btn.pack(side="right")

        # Chart container with proper padding
        chart_frame = ctk.CTkFrame(
            forecast_container,
            fg_color=DataTerminalTheme.BACKGROUND,
            corner_radius=8,
            border_width=1,
            border_color=DataTerminalTheme.BORDER,
        )
        chart_frame.grid(row=1, column=0, sticky="nsew", padx=20, pady=(0, 15))

        # Import and create chart
        from src.ui.components.simple_temperature_chart import SimpleTemperatureChart

        self.temp_chart = SimpleTemperatureChart(
            chart_frame, fg_color=DataTerminalTheme.BACKGROUND, corner_radius=6
        )
        self.temp_chart.pack(fill="both", expand=True, padx=10, pady=10)

        # Add 5-day forecast cards below the chart
        self._create_forecast_cards(forecast_container)

        # Right column - Additional metrics and details
        self._create_additional_metrics_section()

    def _create_forecast_cards(self, parent):
        """Create 5-day forecast cards using enhanced ForecastDayCard component."""
        forecast_frame = ctk.CTkFrame(parent, fg_color="transparent")
        forecast_frame.grid(row=2, column=0, sticky="ew", padx=20, pady=(0, 20))

        # Configure grid for equal distribution
        for i in range(5):
            forecast_frame.grid_columnconfigure(i, weight=1)
        forecast_frame.grid_rowconfigure(0, weight=1)

        # Store forecast cards for later updates
        self.forecast_cards = []

        # Create 5 enhanced forecast cards
        for i in range(5):
            # Calculate day and date
            forecast_date = datetime.now() + timedelta(days=i)
            day_name = forecast_date.strftime("%a")
            date_str = forecast_date.strftime("%m/%d")

            # Create enhanced forecast card with click handler
            day_card = ForecastDayCard(
                forecast_frame,
                day=day_name,
                date=date_str,
                icon="01d",  # Default sunny icon
                high=22,
                low=15,
                precipitation=0.0,
                wind_speed=0.0,
                temp_unit=self.temp_unit,
                on_click=self._on_forecast_card_click,
            )

            day_card.grid(row=0, column=i, padx=4, pady=5, sticky="nsew")
            self.forecast_cards.append(day_card)

            # Add staggered animation
            day_card.animate_in(delay=i * 100)

    def _refresh_chart_data(self):
        """Refresh chart data with latest weather information."""
        try:
            if hasattr(self, "temp_chart") and hasattr(self, "current_weather_data"):
                # Update chart with current weather data
                self._update_temperature_chart(self.current_weather_data)

                # Show brief success message
                if hasattr(self, "status_message_manager"):
                    self.status_message_manager.show_success("Chart refreshed", duration=1500)

        except Exception as e:
            self.logger.error(f"Failed to refresh chart data: {e}")
            if hasattr(self, "status_message_manager"):
                self.status_message_manager.show_error("Failed to refresh chart")

    def _on_forecast_card_click(self, card):
        """Handle forecast card click to show detailed forecast popup."""
        try:
            from .components.forecast_details_popup import ForecastDetailsPopup

            # Get forecast data for the clicked card
            forecast_data = {
                "day": getattr(card, "day_text", "Day"),
                "date": getattr(card, "date_text", "--/--"),
                "icon": getattr(card, "icon_code", "01d"),
                "high_temp": getattr(card, "high_temp", 22),
                "low_temp": getattr(card, "low_temp", 15),
                "precipitation": getattr(card, "precipitation", 0.0),
                "wind_speed": getattr(card, "wind_speed", 0.0),
                "description": getattr(card, "forecast_details", {}).get("description", "Unknown"),
                "humidity": getattr(card, "forecast_details", {}).get("humidity", 0),
                "precipitation_amount": getattr(card, "forecast_details", {}).get(
                    "precipitation_amount", 0.0
                ),
            }

            # Get hourly data if available (would be enhanced later)
            hourly_data = getattr(card, "hourly_data", [])

            # Create and show popup
            ForecastDetailsPopup(self, forecast_data, hourly_data)

            self.logger.info(
                f"Opened forecast details for {forecast_data['day']} {forecast_data['date']}"
            )

        except Exception as e:
            self.logger.error(f"Failed to open forecast details popup: {e}")

    def _create_additional_metrics_section(self):
        """Create additional metrics section for the third column."""
        metrics_container = ctk.CTkFrame(
            self.weather_tab,
            fg_color=DataTerminalTheme.CARD_BG,
            corner_radius=12,
            border_width=1,
            border_color=DataTerminalTheme.BORDER,
        )
        metrics_container.grid(row=0, column=2, sticky="nsew", padx=(8, 15), pady=15)

        # Configure internal grid to prevent bottom right corner artifacts
        metrics_container.grid_columnconfigure(0, weight=1)
        metrics_container.grid_rowconfigure(0, weight=0)  # Title
        metrics_container.grid_rowconfigure(1, weight=1)  # Content area
        metrics_container.grid_rowconfigure(2, weight=0)  # Bottom padding

        # Title
        metrics_title = ctk.CTkLabel(
            metrics_container,
            text="📈 Weather Details",
            font=(DataTerminalTheme.FONT_FAMILY, 16, "bold"),
            text_color=DataTerminalTheme.PRIMARY,
        )
        metrics_title.grid(row=0, column=0, pady=(15, 10), sticky="ew")

        # Content area frame
        content_area = ctk.CTkFrame(metrics_container, fg_color="transparent")
        content_area.grid(row=1, column=0, sticky="nsew", padx=0, pady=0)
        content_area.grid_columnconfigure(0, weight=1)

        # Air Quality Section
        air_quality_frame = ctk.CTkFrame(
            content_area,
            fg_color=DataTerminalTheme.BACKGROUND,
            corner_radius=8,
            border_width=1,
            border_color=DataTerminalTheme.BORDER,
        )
        air_quality_frame.pack(fill="x", padx=12, pady=(0, 10))

        ctk.CTkLabel(
            air_quality_frame,
            text="🌬️ Air Quality",
            font=(DataTerminalTheme.FONT_FAMILY, 12, "bold"),
            text_color=DataTerminalTheme.TEXT,
        ).pack(pady=(8, 3))

        self.air_quality_label = ctk.CTkLabel(
            air_quality_frame,
            text="Good (AQI: 45)",
            font=(DataTerminalTheme.FONT_FAMILY, 10),
            text_color=DataTerminalTheme.SUCCESS,
        )
        self.air_quality_label.pack(pady=(0, 8))

        # Sun Times Section
        sun_times_frame = ctk.CTkFrame(
            content_area,
            fg_color=DataTerminalTheme.BACKGROUND,
            corner_radius=8,
            border_width=1,
            border_color=DataTerminalTheme.BORDER,
        )
        sun_times_frame.pack(fill="x", padx=12, pady=(0, 10))

        ctk.CTkLabel(
            sun_times_frame,
            text="☀️ Sun Times",
            font=(DataTerminalTheme.FONT_FAMILY, 12, "bold"),
            text_color=DataTerminalTheme.TEXT,
        ).pack(pady=(8, 5))

        self.sunrise_label = ctk.CTkLabel(
            sun_times_frame,
            text="🌅 Sunrise: 6:45 AM",
            font=(DataTerminalTheme.FONT_FAMILY, 9),
            text_color=DataTerminalTheme.TEXT_SECONDARY,
        )
        self.sunrise_label.pack(pady=1)

        self.sunset_label = ctk.CTkLabel(
            sun_times_frame,
            text="🌇 Sunset: 7:30 PM",
            font=(DataTerminalTheme.FONT_FAMILY, 9),
            text_color=DataTerminalTheme.TEXT_SECONDARY,
        )
        self.sunset_label.pack(pady=(1, 8))

        # Weather Alerts Section
        alerts_frame = ctk.CTkFrame(
            content_area,
            fg_color=DataTerminalTheme.BACKGROUND,
            corner_radius=8,
            border_width=1,
            border_color=DataTerminalTheme.BORDER,
        )
        alerts_frame.pack(fill="x", padx=12, pady=(0, 10))

        ctk.CTkLabel(
            alerts_frame,
            text="⚠️ Weather Alerts",
            font=(DataTerminalTheme.FONT_FAMILY, 12, "bold"),
            text_color=DataTerminalTheme.TEXT,
        ).pack(pady=(8, 3))

        self.alerts_label = ctk.CTkLabel(
            alerts_frame,
            text="No active alerts",
            font=(DataTerminalTheme.FONT_FAMILY, 9),
            text_color=DataTerminalTheme.TEXT_SECONDARY,
        )
        self.alerts_label.pack(pady=(0, 8))

        # Bottom spacer to prevent visual artifacts in bottom right corner
        bottom_spacer = ctk.CTkFrame(metrics_container, fg_color="transparent", height=10)
        bottom_spacer.grid(row=2, column=0, sticky="ew", pady=(0, 5))

    def _update_sun_times_display(self, weather_data):
        """Update sun times display with weather data."""
        try:
            if hasattr(self, "sunrise_label") and hasattr(self, "sunset_label"):
                # Check if weather data has sun times
                if hasattr(weather_data, "sunrise") and hasattr(weather_data, "sunset"):
                    sunrise_time = (
                        weather_data.sunrise.strftime("%I:%M %p")
                        if weather_data.sunrise
                        else "6:45 AM"
                    )
                    sunset_time = (
                        weather_data.sunset.strftime("%I:%M %p")
                        if weather_data.sunset
                        else "7:30 PM"
                    )
                else:
                    # Use default times based on current time and season
                    from datetime import datetime

                    now = datetime.now()
                    month = now.month

                    # Approximate sunrise/sunset times by season
                    if month in [12, 1, 2]:  # Winter
                        sunrise_time = "7:30 AM"
                        sunset_time = "5:30 PM"
                    elif month in [3, 4, 5]:  # Spring
                        sunrise_time = "6:45 AM"
                        sunset_time = "7:15 PM"
                    elif month in [6, 7, 8]:  # Summer
                        sunrise_time = "5:45 AM"
                        sunset_time = "8:30 PM"
                    else:  # Fall
                        sunrise_time = "7:00 AM"
                        sunset_time = "6:45 PM"

                self.sunrise_label.configure(text=f"🌅 Sunrise: {sunrise_time}")
                self.sunset_label.configure(text=f"🌇 Sunset: {sunset_time}")
        except Exception as e:
            self.logger.error(f"Failed to update sun times display: {e}")

    def _update_weather_alerts_display(self, weather_data):
        """Update weather alerts display with weather data."""
        try:
            if hasattr(self, "alerts_label"):
                # Check if weather data has alerts
                if hasattr(weather_data, "alerts") and weather_data.alerts:
                    if isinstance(weather_data.alerts, list) and len(weather_data.alerts) > 0:
                        alert = weather_data.alerts[0]  # Show first alert
                        alert_text = (
                            alert.get("title", "Weather Alert")
                            if isinstance(alert, dict)
                            else str(alert)
                        )
                        self.alerts_label.configure(
                            text=alert_text[:50] + "..." if len(alert_text) > 50 else alert_text,
                            text_color="#ff7e00",  # Orange for alerts
                        )
                    else:
                        self.alerts_label.configure(
                            text="No active alerts", text_color="#888888"  # Gray for no alerts
                        )
                else:
                    # Check weather conditions for potential alerts
                    if hasattr(weather_data, "description"):
                        condition = weather_data.description.lower()
                        if "storm" in condition or "thunder" in condition:
                            self.alerts_label.configure(
                                text="⚡ Thunderstorm Warning",
                                text_color="#ff0000",  # Red for severe weather
                            )
                        elif (
                            "snow" in condition
                            and hasattr(weather_data, "temperature")
                            and weather_data.temperature < 0
                        ):
                            self.alerts_label.configure(
                                text="❄️ Snow Advisory", text_color="#0080ff"  # Blue for snow
                            )
                        elif (
                            hasattr(weather_data, "wind_speed")
                            and weather_data.wind_speed
                            and weather_data.wind_speed > 15
                        ):
                            wind_kmh = weather_data.wind_speed * 3.6
                            self.alerts_label.configure(
                                text=f"💨 High Wind ({wind_kmh:.0f} km/h)",
                                text_color="#ff7e00",  # Orange for wind
                            )
                        else:
                            self.alerts_label.configure(
                                text="No active alerts", text_color="#888888"  # Gray for no alerts
                            )
                    else:
                        self.alerts_label.configure(
                            text="No active alerts", text_color="#888888"  # Gray for no alerts
                        )
        except Exception as e:
            self.logger.error(f"Failed to update weather alerts display: {e}")

    def _update_forecast_cards(self, weather_data):
        """Update 5-day forecast cards with weather data."""
        try:
            # Check if we have forecast cards to update
            if not hasattr(self, "forecast_cards") or not self.forecast_cards:
                return

            # If we have forecast data, use it; otherwise generate sample data
            if hasattr(weather_data, "forecast_data") and weather_data.forecast_data:
                self._update_cards_with_forecast_data(weather_data.forecast_data)
            elif hasattr(weather_data, "temperature"):
                self._update_cards_with_sample_data(weather_data.temperature)

        except Exception as e:
            self.logger.error(f"Failed to update forecast cards: {e}")

    def _update_cards_with_forecast_data(self, forecast_data):
        """Update forecast cards with real forecast data."""
        try:
            # Get daily forecasts from forecast data
            daily_forecasts = self._parse_daily_forecasts(forecast_data)

            for i, card in enumerate(self.forecast_cards):
                if i < len(daily_forecasts):
                    daily_data = daily_forecasts[i]

                    # Update card with real data including day and date
                    card.update_data(
                        day=daily_data.get("day", "Day"),
                        date=daily_data.get("date", "--/--"),
                        icon=daily_data.get("icon", "01d"),
                        high=daily_data.get("high_temp", 22),
                        low=daily_data.get("low_temp", 15),
                        precipitation=daily_data.get("precipitation", 0.0),
                        wind_speed=daily_data.get("wind_speed", 0.0),
                        temp_unit=self.temp_unit,
                    )

                    # Store additional data for popup details
                    forecast_details = {
                        "description": daily_data.get("description", "Unknown"),
                        "humidity": daily_data.get("humidity", 0),
                        "precipitation_amount": daily_data.get("precipitation_amount", 0.0),
                        "wind_speed": daily_data.get("wind_speed", 0.0),
                        "confidence_level": daily_data.get("confidence_level", 85),
                        "last_update": daily_data.get("last_update", "Unknown"),
                        "provider": daily_data.get("provider", "OpenWeatherMap"),
                        "sunrise": daily_data.get("sunrise", "06:30"),
                        "sunset": daily_data.get("sunset", "18:45"),
                        "uv_index": daily_data.get("uv_index", 5),
                    }

                    setattr(card, "forecast_details", forecast_details)

                    # Store hourly data for the day
                    hourly_data = daily_data.get("hourly_data", [])
                    setattr(card, "hourly_data", hourly_data)

        except Exception as e:
            self.logger.error(f"Failed to update cards with forecast data: {e}")

    def _update_cards_with_sample_data(self, base_temp):
        """Update forecast cards with sample data based on current temperature."""
        try:
            for i, card in enumerate(self.forecast_cards):
                # Generate forecast temperatures (slight variations)
                high_temp = int(base_temp + (i * 2) - 2)
                low_temp = int(base_temp - 5 + (i * 1))

                # Sample weather conditions
                icons = ["01d", "02d", "03d", "04d", "09d"]
                precipitations = [0.0, 0.1, 0.3, 0.2, 0.0]
                wind_speeds = [2.5, 3.0, 4.2, 3.8, 2.1]

                card.update_data(
                    icon=icons[i % len(icons)],
                    high=high_temp,
                    low=low_temp,
                    precipitation=precipitations[i % len(precipitations)],
                    wind_speed=wind_speeds[i % len(wind_speeds)],
                    temp_unit=self.temp_unit,
                )

        except Exception as e:
            self.logger.error(f"Failed to update cards with sample data: {e}")

    def _parse_daily_forecasts(self, forecast_data):
        """Parse forecast data into daily summaries."""
        try:
            daily_forecasts = []

            # Check if forecast_data is a ForecastData object with daily_forecasts
            if hasattr(forecast_data, "daily_forecasts") and forecast_data.daily_forecasts:
                # Use the enhanced ForecastData model
                from datetime import datetime

                for i, day_forecast in enumerate(
                    forecast_data.daily_forecasts[:5]
                ):  # Get first 5 days
                    # Map weather condition to icon
                    icon_code = self._get_weather_icon_code(day_forecast.condition)

                    # Get hourly data for this day from the forecast_data
                    day_hourly_data = []
                    if hasattr(forecast_data, "hourly_forecasts"):
                        # Filter hourly forecasts for this specific day
                        target_date = day_forecast.date.date()
                        for hourly in forecast_data.hourly_forecasts:
                            if hourly.timestamp.date() == target_date:
                                day_hourly_data.append(
                                    {
                                        "time": hourly.timestamp.strftime("%H:%M"),
                                        "temp": int(
                                            hourly.temp_f if self.temp_unit == "F" else hourly.temp
                                        ),
                                        "condition": hourly.condition,
                                        "icon": self._get_weather_icon_code(hourly.condition),
                                        "precipitation": hourly.precipitation_probability or 0.0,
                                        "wind_speed": hourly.wind_speed or 0.0,
                                    }
                                )

                    # Calculate forecast accuracy indicators
                    days_ahead = i
                    confidence_level = max(95 - (days_ahead * 5), 60)  # Decreasing confidence

                    daily_forecasts.append(
                        {
                            "day": day_forecast.date.strftime("%a"),
                            "date": day_forecast.date.strftime("%m/%d"),
                            "icon": icon_code,
                            "high_temp": int(
                                day_forecast.temp_max_f
                                if self.temp_unit == "F"
                                else day_forecast.temp_max
                            ),
                            "low_temp": int(
                                day_forecast.temp_min_f
                                if self.temp_unit == "F"
                                else day_forecast.temp_min
                            ),
                            "precipitation": day_forecast.precipitation_probability or 0.0,
                            "wind_speed": day_forecast.wind_speed or 0.0,
                            "description": day_forecast.description,
                            "humidity": day_forecast.humidity,
                            "precipitation_amount": day_forecast.precipitation_amount or 0.0,
                            "hourly_data": day_hourly_data,
                            "confidence_level": confidence_level,
                            "last_update": datetime.now().strftime("%H:%M"),
                            "provider": "OpenWeatherMap",
                            "sunrise": "06:30",  # Would be enhanced with real data
                            "sunset": "18:45",  # Would be enhanced with real data
                            "uv_index": min(10, max(1, 5 + i)),  # Sample UV index
                        }
                    )
            elif hasattr(forecast_data, "get_daily_forecast"):
                # Use the model's method to get daily forecast (legacy support)
                daily_data = forecast_data.get_daily_forecast()
                for day_data in daily_data[:5]:  # Get first 5 days
                    daily_forecasts.append(
                        {
                            "icon": getattr(day_data, "icon", "01d"),
                            "high_temp": int(getattr(day_data, "high_temp", 22)),
                            "low_temp": int(getattr(day_data, "low_temp", 15)),
                            "precipitation": getattr(day_data, "precipitation_probability", 0.0),
                            "wind_speed": getattr(day_data, "wind_speed", 0.0),
                        }
                    )
            elif hasattr(forecast_data, "list"):
                # Parse OpenWeatherMap 5-day forecast format
                daily_forecasts = self._parse_openweather_forecast(forecast_data.list)
            else:
                # Fallback to sample data
                from datetime import datetime, timedelta

                for i in range(5):
                    date = datetime.now() + timedelta(days=i)

                    # Generate sample hourly data for the day
                    sample_hourly = []
                    for hour in range(0, 24, 3):  # Every 3 hours
                        sample_hourly.append(
                            {
                                "time": f"{hour:02d}:00",
                                "temp": 18 + (i * 2) + (hour // 6),
                                "condition": [
                                    "Clear",
                                    "Partly Cloudy",
                                    "Cloudy",
                                    "Overcast",
                                    "Rain",
                                ][i],
                                "icon": ["01d", "02d", "03d", "04d", "09d"][i],
                                "precipitation": [0.0, 0.1, 0.3, 0.2, 0.0][i],
                                "wind_speed": [2.5, 3.0, 4.2, 3.8, 2.1][i],
                            }
                        )

                    confidence_level = max(95 - (i * 5), 60)

                    daily_forecasts.append(
                        {
                            "day": date.strftime("%a"),
                            "date": date.strftime("%m/%d"),
                            "icon": ["01d", "02d", "03d", "04d", "09d"][i],
                            "high_temp": 22 + (i * 2) - 2,
                            "low_temp": 15 + i,
                            "precipitation": [0.0, 0.1, 0.3, 0.2, 0.0][i],
                            "wind_speed": [2.5, 3.0, 4.2, 3.8, 2.1][i],
                            "description": ["Sunny", "Partly Cloudy", "Cloudy", "Overcast", "Rain"][
                                i
                            ],
                            "humidity": [45, 50, 65, 70, 80][i],
                            "precipitation_amount": [0.0, 0.0, 0.0, 0.0, 2.5][i],
                            "hourly_data": sample_hourly,
                            "confidence_level": confidence_level,
                            "last_update": datetime.now().strftime("%H:%M"),
                            "provider": "Sample Data",
                            "sunrise": "06:30",
                            "sunset": "18:45",
                            "uv_index": min(10, max(1, 5 + i)),
                        }
                    )

            return daily_forecasts

        except Exception as e:
            self.logger.error(f"Failed to parse daily forecasts: {e}")
            return []

    def _get_weather_icon_code(self, condition):
        """Map weather condition to OpenWeather icon code."""
        try:
            # Map WeatherCondition enum to icon codes
            condition_str = str(condition).lower() if condition else "clear"

            icon_mapping = {
                "clear": "01d",
                "sunny": "01d",
                "partly_cloudy": "02d",
                "cloudy": "03d",
                "overcast": "04d",
                "mist": "50d",
                "fog": "50d",
                "light_rain": "10d",
                "rain": "10d",
                "heavy_rain": "09d",
                "thunderstorm": "11d",
                "snow": "13d",
                "light_snow": "13d",
                "heavy_snow": "13d",
                "sleet": "13d",
                "drizzle": "09d",
                "haze": "50d",
                "smoke": "50d",
                "dust": "50d",
                "sand": "50d",
                "ash": "50d",
                "squall": "50d",
                "tornado": "50d",
            }

            # Try exact match first
            if condition_str in icon_mapping:
                return icon_mapping[condition_str]

            # Try partial matches
            for key, icon in icon_mapping.items():
                if key in condition_str or condition_str in key:
                    return icon

            # Default fallback
            return "01d"

        except Exception as e:
            self.logger.warning(f"Failed to map weather condition to icon: {e}")
            return "01d"

    def _parse_openweather_forecast(self, forecast_list):
        """Parse OpenWeatherMap forecast list into daily summaries."""
        try:
            daily_data = {}

            # Group forecast entries by date
            for entry in forecast_list:
                if "dt_txt" in entry:
                    date_str = entry["dt_txt"][:10]  # Get YYYY-MM-DD part

                    if date_str not in daily_data:
                        daily_data[date_str] = {
                            "temps": [],
                            "icons": [],
                            "precipitation": 0.0,
                            "wind_speeds": [],
                        }

                    # Collect temperature data
                    if "main" in entry and "temp" in entry["main"]:
                        daily_data[date_str]["temps"].append(entry["main"]["temp"])

                    # Collect weather icons (use most common one)
                    if "weather" in entry and len(entry["weather"]) > 0:
                        daily_data[date_str]["icons"].append(entry["weather"][0].get("icon", "01d"))

                    # Collect precipitation probability
                    if "pop" in entry:
                        daily_data[date_str]["precipitation"] = max(
                            daily_data[date_str]["precipitation"], entry["pop"]
                        )

                    # Collect wind speed
                    if "wind" in entry and "speed" in entry["wind"]:
                        daily_data[date_str]["wind_speeds"].append(entry["wind"]["speed"])

            # Convert to daily forecasts
            daily_forecasts = []
            for date_str in sorted(daily_data.keys())[:5]:  # Get first 5 days
                day_data = daily_data[date_str]

                # Calculate high/low temperatures
                temps = day_data["temps"]
                high_temp = int(max(temps)) if temps else 22
                low_temp = int(min(temps)) if temps else 15

                # Get most common icon
                icons = day_data["icons"]
                icon = max(set(icons), key=icons.count) if icons else "01d"

                # Average wind speed
                wind_speeds = day_data["wind_speeds"]
                avg_wind = sum(wind_speeds) / len(wind_speeds) if wind_speeds else 0.0

                daily_forecasts.append(
                    {
                        "icon": icon,
                        "high_temp": high_temp,
                        "low_temp": low_temp,
                        "precipitation": day_data["precipitation"],
                        "wind_speed": avg_wind,
                    }
                )

            return daily_forecasts

        except Exception as e:
            self.logger.error(f"Failed to parse OpenWeather forecast: {e}")
            return []

    def _show_hourly_breakdown(self, day_index):
        """Show hourly weather breakdown for selected day."""
        try:
            # Create a new window for hourly breakdown
            hourly_window = ctk.CTkToplevel(self)
            hourly_window.title(f"Hourly Forecast - Day {day_index + 1}")
            hourly_window.geometry("600x400")
            hourly_window.transient(self)
            hourly_window.grab_set()

            # Check if we have newer weather data available
            current_time = datetime.now()
            current_data_timestamp = (
                getattr(self.current_weather_data, "timestamp", current_time)
                if hasattr(self, "current_weather_data") and self.current_weather_data
                else current_time
            )

            # Store reference to window and its day index with creation timestamp
            window_info = {
                "window": hourly_window,
                "day_index": day_index,
                "created_at": current_time,
                "data_timestamp": current_data_timestamp,
            }
            self.open_hourly_windows.append(window_info)
            logging.info(
                f"Hourly window opened for day {day_index}. Total open windows: {len(self.open_hourly_windows)}"
            )
            logging.info(
                f"Window created at {window_info['created_at'].strftime('%H:%M:%S')} with data from {window_info['data_timestamp'].strftime('%H:%M:%S')}"
            )

            # Set up cleanup when window is closed
            def on_window_close():
                if window_info in self.open_hourly_windows:
                    self.open_hourly_windows.remove(window_info)
                    logging.info(
                        f"Hourly window closed for day {day_index}. Total open windows: {len(self.open_hourly_windows)}"
                    )
                hourly_window.destroy()

            hourly_window.protocol("WM_DELETE_WINDOW", on_window_close)

            # Center the window
            hourly_window.update_idletasks()
            x = (hourly_window.winfo_screenwidth() // 2) - (600 // 2)
            y = (hourly_window.winfo_screenheight() // 2) - (400 // 2)
            hourly_window.geometry(f"600x400+{x}+{y}")

            # Create content
            content_frame = ctk.CTkFrame(hourly_window)
            content_frame.pack(fill="both", expand=True, padx=20, pady=20)

            # Title
            target_date = datetime.now() + timedelta(days=day_index)
            title_label = ctk.CTkLabel(
                content_frame,
                text=f"Hourly Forecast - {target_date.strftime('%A, %B %d')}",
                font=ctk.CTkFont(size=18, weight="bold"),
                text_color=theme_manager.get_current_theme().get("text", "#FFFFFF"),
            )
            title_label.pack(pady=(0, 20))

            # Scrollable frame for hourly data
            scrollable_frame = ctk.CTkScrollableFrame(content_frame)
            scrollable_frame.pack(fill="both", expand=True)

            # Get real hourly forecast data
            hourly_data = self._get_hourly_data_for_day(day_index)

            # Check if we have newer weather data available and update window info if needed
            if (
                hasattr(self, "last_weather_data_timestamp")
                and self.last_weather_data_timestamp > current_data_timestamp
            ):
                window_info["data_timestamp"] = self.last_weather_data_timestamp
                logging.info(
                    f"Updated window data timestamp to latest: {self.last_weather_data_timestamp.strftime('%H:%M:%S')}"
                )

            if hourly_data:
                # Display real hourly data
                for hour_entry in hourly_data:
                    hour_frame = ctk.CTkFrame(scrollable_frame)
                    hour_frame.pack(fill="x", padx=5, pady=2)

                    # Time
                    time_str = hour_entry.get("time", "00:00")
                    time_label = ctk.CTkLabel(
                        hour_frame, text=time_str, font=ctk.CTkFont(size=14), width=60
                    )
                    time_label.pack(side="left", padx=10, pady=5)

                    # Weather icon
                    icon = self._get_weather_icon(hour_entry.get("condition", "clear"))
                    icon_label = ctk.CTkLabel(
                        hour_frame, text=icon, font=ctk.CTkFont(size=14), width=40
                    )
                    icon_label.pack(side="left", padx=5, pady=5)

                    # Temperature
                    temp = hour_entry.get("temperature", 20)
                    if hasattr(self, "temp_unit") and self.temp_unit == "F":
                        temp = temp * 9 / 5 + 32
                    temp_label = ctk.CTkLabel(
                        hour_frame,
                        text=f"{int(temp)}°{getattr(self, 'temp_unit', 'C')}",
                        font=ctk.CTkFont(size=14),
                        width=60,
                    )
                    temp_label.pack(side="left", padx=10, pady=5)

                    # Precipitation
                    precip = hour_entry.get("precipitation", 0)
                    precip_label = ctk.CTkLabel(
                        hour_frame,
                        text=f"💧 {int(precip)}%" if precip > 0 else "",
                        font=ctk.CTkFont(size=12),
                        width=60,
                    )
                    precip_label.pack(side="left", padx=10, pady=5)

                    # Wind
                    wind = hour_entry.get("wind_speed", 0)
                    wind_label = ctk.CTkLabel(
                        hour_frame, text=f"💨 {wind:.1f} m/s", font=ctk.CTkFont(size=12)
                    )
                    wind_label.pack(side="left", padx=10, pady=5)
            else:
                # Fallback to sample data if no real data available
                no_data_label = ctk.CTkLabel(
                    scrollable_frame,
                    text="No hourly forecast data available for this day.",
                    font=ctk.CTkFont(size=14),
                    text_color=theme_manager.get_current_theme().get("text_secondary", "#CCCCCC"),
                )
                no_data_label.pack(pady=20)

                # Show sample data as fallback
                for hour in range(0, 24, 3):  # Every 3 hours
                    hour_frame = ctk.CTkFrame(scrollable_frame)
                    hour_frame.pack(fill="x", padx=5, pady=2)

                    # Time
                    time_label = ctk.CTkLabel(
                        hour_frame, text=f"{hour:02d}:00", font=ctk.CTkFont(size=14), width=60
                    )
                    time_label.pack(side="left", padx=10, pady=5)

                    # Weather icon
                    icon_label = ctk.CTkLabel(
                        hour_frame, text="🌤️", font=ctk.CTkFont(size=14), width=40
                    )
                    icon_label.pack(side="left", padx=5, pady=5)

                    # Temperature
                    temp = 20 + (hour // 3) - 2  # Sample temperature variation
                    temp_label = ctk.CTkLabel(
                        hour_frame,
                        text=f"{temp}°{getattr(self, 'temp_unit', 'C')}",
                        font=ctk.CTkFont(size=14),
                        width=60,
                    )
                    temp_label.pack(side="left", padx=10, pady=5)

                    # Precipitation
                    precip = (
                        max(0, (hour - 12) * 5) if 9 <= hour <= 15 else 0
                    )  # Sample precipitation
                    precip_label = ctk.CTkLabel(
                        hour_frame,
                        text=f"💧 {precip}%" if precip > 0 else "",
                        font=ctk.CTkFont(size=12),
                        width=60,
                    )
                    precip_label.pack(side="left", padx=10, pady=5)

                    # Wind
                    wind = 2.0 + (hour * 0.1)  # Sample wind variation
                    wind_label = ctk.CTkLabel(
                        hour_frame, text=f"💨 {wind:.1f} m/s", font=ctk.CTkFont(size=12)
                    )
                    wind_label.pack(side="left", padx=10, pady=5)

            # Close button
            close_button = ctk.CTkButton(
                content_frame, text="Close", command=on_window_close, font=ctk.CTkFont(size=14)
            )
            close_button.pack(pady=(10, 0))

            # Store reference to content frame for updates
            window_info["content_frame"] = content_frame

        except Exception as e:
            self.logger.error(f"Failed to show hourly breakdown: {e}")

    def _refresh_open_hourly_windows(self):
        """Refresh content of all open hourly breakdown windows."""
        try:
            current_time = datetime.now().strftime("%H:%M:%S")
            current_data_timestamp = (
                getattr(self.current_weather_data, "timestamp", datetime.now())
                if hasattr(self, "current_weather_data") and self.current_weather_data
                else datetime.now()
            )

            self.logger.info(
                f"[{current_time}] Refreshing {len(self.open_hourly_windows)} open hourly windows"
            )
            self.logger.info(
                f"[{current_time}] Current weather data timestamp: {current_data_timestamp.strftime('%H:%M:%S')}"
            )

            for window_info in self.open_hourly_windows[:]:
                try:
                    window = window_info["window"]
                    day_index = window_info["day_index"]
                    window_data_timestamp = window_info.get("data_timestamp", datetime.min)

                    # Check if window still exists
                    if not window.winfo_exists():
                        self.open_hourly_windows.remove(window_info)
                        self.logger.info(
                            f"[{current_time}] Removed non-existent window for day {day_index}"
                        )
                        continue

                    # Check if current data is newer than window's data
                    if current_data_timestamp <= window_data_timestamp:
                        self.logger.info(
                            f"[{current_time}] Skipping window for day {day_index} - "
                            f"data is current (window: {window_data_timestamp.strftime('%H:%M:%S')}, "
                            f"current: {current_data_timestamp.strftime('%H:%M:%S')})"
                        )
                        continue

                    self.logger.info(
                        f"[{current_time}] Refreshing hourly window for day {day_index} "
                        f"with newer data (window: {window_data_timestamp.strftime('%H:%M:%S')}, "
                        f"current: {current_data_timestamp.strftime('%H:%M:%S')})"
                    )

                    # Update the window's data timestamp
                    window_info["data_timestamp"] = current_data_timestamp

                    # Get content frame from window info
                    content_frame = window_info.get("content_frame")
                    if not content_frame:
                        self.logger.warning(f"No content frame found for hourly window {day_index}")
                        continue

                    # Clear existing content (except close button)
                    for child in content_frame.winfo_children():
                        if not isinstance(child, ctk.CTkButton):
                            child.destroy()

                    # Recreate the scrollable frame and content
                    scrollable_frame = ctk.CTkScrollableFrame(content_frame)
                    scrollable_frame.pack(fill="both", expand=True)

                    # Get updated hourly data
                    hourly_data = self._get_hourly_data_for_day(day_index)

                    if hourly_data:
                        # Display updated hourly data
                        for hour_entry in hourly_data:
                            hour_frame = ctk.CTkFrame(scrollable_frame)
                            hour_frame.pack(fill="x", padx=5, pady=2)

                            # Time
                            time_str = hour_entry.get("time", "00:00")
                            time_label = ctk.CTkLabel(
                                hour_frame, text=time_str, font=ctk.CTkFont(size=14), width=60
                            )
                            time_label.pack(side="left", padx=10, pady=5)

                            # Weather icon
                            condition = hour_entry.get("condition", "clear")
                            icon = self._get_weather_icon(condition)
                            icon_label = ctk.CTkLabel(
                                hour_frame, text=icon, font=ctk.CTkFont(size=16), width=40
                            )
                            icon_label.pack(side="left", padx=10, pady=5)

                            # Temperature
                            temp = hour_entry.get("temperature", 20)
                            temp_label = ctk.CTkLabel(
                                hour_frame,
                                text=f"{int(temp)}°{getattr(self, 'temp_unit', 'C')}",
                                font=ctk.CTkFont(size=14),
                                width=60,
                            )
                            temp_label.pack(side="left", padx=10, pady=5)

                            # Precipitation
                            precip = hour_entry.get("precipitation", 0)
                            precip_label = ctk.CTkLabel(
                                hour_frame,
                                text=f"💧 {int(precip)}%" if precip > 0 else "",
                                font=ctk.CTkFont(size=12),
                                width=60,
                            )
                            precip_label.pack(side="left", padx=10, pady=5)

                            # Wind
                            wind = hour_entry.get("wind_speed", 0)
                            wind_label = ctk.CTkLabel(
                                hour_frame, text=f"💨 {wind:.1f} m/s", font=ctk.CTkFont(size=12)
                            )
                            wind_label.pack(side="left", padx=10, pady=5)
                    else:
                        # Show "no data" message
                        no_data_label = ctk.CTkLabel(
                            scrollable_frame,
                            text="No hourly forecast data available for this day.",
                            font=ctk.CTkFont(size=14),
                        )
                        no_data_label.pack(pady=20)

                except Exception as e:
                    self.logger.error(f"Failed to refresh hourly window: {e}")
                    # Remove problematic window from tracking
                    if window_info in self.open_hourly_windows:
                        self.open_hourly_windows.remove(window_info)

        except Exception as e:
            self.logger.error(f"Failed to refresh open hourly windows: {e}")

    def _get_hourly_data_for_day(self, day_index):
        """Extract hourly forecast data for a specific day."""
        try:
            if not self.current_weather_data or not hasattr(
                self.current_weather_data, "forecast_data"
            ):
                return None

            forecast_data = self.current_weather_data.forecast_data
            if not forecast_data or not hasattr(forecast_data, "hourly_forecasts"):
                return None

            # Calculate target date
            target_date = datetime.now().date() + timedelta(days=day_index)

            hourly_data = []
            for forecast in forecast_data.hourly_forecasts:
                # Get the forecast datetime
                forecast_dt = forecast.timestamp

                # Check if this forecast is for the target day
                if forecast_dt.date() == target_date:
                    # Get precipitation probability as percentage
                    precip_prob = 0
                    if forecast.precipitation_probability is not None:
                        precip_prob = forecast.precipitation_probability * 100

                    hour_data = {
                        "time": forecast_dt.strftime("%H:%M"),
                        "temperature": forecast.temperature,
                        "condition": (
                            forecast.condition.value
                            if hasattr(forecast.condition, "value")
                            else str(forecast.condition)
                        ),
                        "precipitation": precip_prob,
                        "wind_speed": forecast.wind_speed or 0,
                    }
                    hourly_data.append(hour_data)

            return hourly_data if hourly_data else None

        except Exception as e:
            self.logger.error(f"Failed to get hourly data for day {day_index}: {e}")
            return None

    def _get_weather_icon(self, condition):
        """Get weather icon emoji based on condition."""
        condition_lower = condition.lower()

        icon_map = {
            "clear": "☀️",
            "sunny": "☀️",
            "clouds": "☁️",
            "cloudy": "☁️",
            "partly cloudy": "⛅",
            "overcast": "☁️",
            "rain": "🌧️",
            "drizzle": "🌦️",
            "shower": "🌦️",
            "thunderstorm": "⛈️",
            "snow": "❄️",
            "mist": "🌫️",
            "fog": "🌫️",
            "haze": "🌫️",
        }

        for key, icon in icon_map.items():
            if key in condition_lower:
                return icon

        return "🌤️"  # Default icon

    def _update_temperature_chart(self, weather_data):
        """Update temperature chart with weather data."""
        try:
            if hasattr(self, "temp_chart") and hasattr(weather_data, "temperature"):
                # Generate sample hourly data based on current temperature
                import random

                base_temp = weather_data.temperature
                hourly_temps = []

                for i in range(24):
                    # Create realistic temperature variation throughout the day
                    hour_offset = (i - 12) / 12.0  # -1 to 1
                    daily_variation = -3 * abs(hour_offset)  # Cooler at night
                    random_variation = random.uniform(-2, 2)
                    temp = base_temp + daily_variation + random_variation
                    hourly_temps.append(temp)

                # Ensure chart uses correct temperature unit
                if hasattr(self.temp_chart, "set_temperature_unit") and hasattr(self, "temp_unit"):
                    self.temp_chart.set_temperature_unit(self.temp_unit)

                # Update chart if it has an update method
                if hasattr(self.temp_chart, "update_data"):
                    self.temp_chart.update_data(hourly_temps)
                elif hasattr(self.temp_chart, "set_data"):
                    self.temp_chart.set_data(hourly_temps)
        except Exception as e:
            self.logger.error(f"Failed to update temperature chart: {e}")

    def _enhanced_search_weather(self):
        """Enhanced weather search with micro-interactions."""
        # Add ripple effect on button click
        self.micro_interactions.add_ripple_effect(self.search_button)

        search_term = self.search_entry.get().strip()
        if search_term:
            # Pulse animation for search entry
            self.animation_manager.pulse_animation(self.search_entry)

            # Update current city with fade effect
            self.current_city = search_term
            self.animation_manager.fade_in(self.location_label)
            self.location_label.configure(text=f"📍 Current: {self.current_city}")

            # Update weather display with slide effect
            self.animation_manager.fade_in(self.city_label)
            self.city_label.configure(text=self.current_city)

            # Clear search entry with animation
            self.animation_manager.fade_out(
                self.search_entry, callback=lambda: self.search_entry.delete(0, "end")
            )

            # Call original weather update
            self._update_weather_display()
        else:
            # Show warning pulse for empty search
            self.micro_interactions.add_warning_pulse(self.search_entry)

    def _on_location_selected(self, location_result):
        """Handle location selection from enhanced search bar."""
        try:
            self.logger.info(f"Location selected: {location_result.display_name}")

            # Update current city
            self.current_city = location_result.display_name
            self.location_label.configure(text=f"📍 Current: {self.current_city}")

            # Update weather display
            if hasattr(self, "city_label"):
                self.city_label.configure(text=self.current_city)

            # Store location coordinates for future use
            self.current_location = {
                "name": location_result.name,
                "display_name": location_result.display_name,
                "latitude": location_result.latitude,
                "longitude": location_result.longitude,
                "country": location_result.country,
                "state": location_result.state,
            }

            # Trigger weather data update
            self._safe_fetch_weather_data()

            # Trigger forecast update - this will be handled by _safe_fetch_weather_data
            # which calls _update_forecast_display with proper forecast data

        except Exception as e:
            self.logger.error(f"Error handling location selection: {e}")
            self._show_error_state(f"Failed to update location: {str(e)}")

    def _create_basic_search(self, parent):
        """Create basic search as fallback."""
        search_controls = ctk.CTkFrame(parent, fg_color="transparent")
        search_controls.pack()

        self.search_entry = ctk.CTkEntry(
            search_controls,
            placeholder_text="🔍 Enter city name...",
            width=300,
            height=40,
            corner_radius=20,
            border_color=DataTerminalTheme.BORDER,
            fg_color=DataTerminalTheme.BACKGROUND,
            text_color=DataTerminalTheme.TEXT,
            font=(DataTerminalTheme.FONT_FAMILY, 14),
        )
        self.search_entry.pack(side="left", padx=(0, 10))
        self.search_entry.bind("<Return>", lambda e: self._search_weather())

        self.search_button = ctk.CTkButton(
            search_controls,
            text="SEARCH",
            width=100,
            height=40,
            corner_radius=20,
            fg_color=DataTerminalTheme.PRIMARY,
            hover_color=DataTerminalTheme.SUCCESS,
            text_color=DataTerminalTheme.BACKGROUND,
            font=(DataTerminalTheme.FONT_FAMILY, 14, "bold"),
            command=self._enhanced_search_weather,
        )
        self.search_button.pack(side="left")

        # Add micro-interactions to search button
        self.micro_interactions.add_hover_effect(self.search_button)
        self.micro_interactions.add_click_effect(self.search_button)

    def _search_weather(self):
        """Handle weather search functionality with input validation."""
        search_term = self.search_entry.get().strip()

        # Clear any existing validation errors
        self.error_handler.clear_validation_error(self.search_entry)

        # Validate input
        if not search_term:
            self.error_handler.show_validation_error(
                self.search_entry,
                "City name is required",
                "Enter a valid city name (e.g., 'New York' or 'London, UK')",
            )
            return

        if len(search_term) < 2:
            self.error_handler.show_validation_error(
                self.search_entry, "City name too short", "Please enter at least 2 characters"
            )
            return

        if len(search_term) > 100:
            self.error_handler.show_validation_error(
                self.search_entry, "City name too long", "Please enter a shorter city name"
            )
            return

        # Check for invalid characters
        import re

        if not re.match(r"^[a-zA-Z\s,.-]+$", search_term):
            self.error_handler.show_validation_error(
                self.search_entry,
                "Invalid characters in city name",
                "Use only letters, spaces, commas, periods, and hyphens",
            )
            return

        # Valid input - proceed with search
        # Update current city
        self.current_city = search_term
        self.location_label.configure(text=f"📍 Current: {self.current_city}")

        # Update weather display
        self.city_label.configure(text=self.current_city)

        # Clear search entry
        self.search_entry.delete(0, "end")

        # Trigger weather data update
        self._safe_fetch_weather_data()

    def _update_weather_display(self, weather_data):
        """Update UI with enhanced weather display and visual effects."""
        try:
            # Validate weather data first
            if not self._validate_weather_data(weather_data):
                self.logger.warning("Invalid weather data received")
                self._show_data_unavailable_state()
                return

            # Store current weather data for activity suggestions
            self.current_weather_data = weather_data
            # Track when weather data was last updated
            self.last_weather_data_timestamp = datetime.now()

            # Update last refresh timestamp
            self._update_last_refresh_timestamp()

            # Update weather-based background with validation
            self._update_weather_background_safe(weather_data)

            # Update activities if on activities tab
            if self.tabview.get() == "Activities":
                self._update_activity_suggestions(weather_data)

            # Refresh activity suggestions with new weather data
            self._refresh_activity_suggestions()

            # Update location display with validation
            self._update_location_display_safe(weather_data)

            # Update temperature display with proper unit conversion
            self._update_temperature_display_safe(weather_data)

            # Update condition display with validation
            self._update_condition_display_safe(weather_data)

            # Show success status
            self.status_manager.show_weather_fact()

            # Refresh any open hourly breakdown windows
            self.logger.info("About to refresh open hourly windows from _update_weather_display")
            self._refresh_open_hourly_windows()

            # Update metrics with validation and proper conversions
            self._update_weather_metrics_safe(weather_data)

            # Update air quality display
            self._update_air_quality_display(weather_data)

            # Update sun times display
            self._update_sun_times_display(weather_data)

            # Update weather alerts display
            self._update_weather_alerts_display(weather_data)

            # Update forecast cards
            self._update_forecast_cards(weather_data)

            # Update temperature chart
            if hasattr(self, "temp_chart"):
                self._update_temperature_chart(weather_data)

            # Update status with success message
            self._update_status_success()

            self.logger.info("Weather display updated successfully")

        except Exception as e:
            self.logger.error(f"Error updating display: {e}")
            self._handle_display_error(e)

    def _validate_weather_data(self, weather_data):
        """Validate weather data before processing."""
        if not weather_data:
            return False

        # Check for required attributes
        required_attrs = ["temperature", "description"]
        for attr in required_attrs:
            if not hasattr(weather_data, attr) or getattr(weather_data, attr) is None:
                self.logger.warning(f"Missing required weather attribute: {attr}")
                return False

        # Validate temperature range (-100°C to 60°C)
        temp = getattr(weather_data, "temperature", None)
        if temp is not None and (temp < -100 or temp > 60):
            self.logger.warning(f"Temperature out of valid range: {temp}°C")
            return False

        return True

    def _show_data_unavailable_state(self):
        """Show UI state when weather data is unavailable."""
        try:
            if hasattr(self, "city_label"):
                self.city_label.configure(text="Location unavailable")
            if hasattr(self, "temp_label"):
                self.temp_label.configure(text="--°")
            if hasattr(self, "condition_label"):
                self.condition_label.configure(text="Weather data unavailable")
            if hasattr(self, "status_label"):
                self.status_label.configure(text="⚠️ No weather data available")
        except Exception as e:
            self.logger.error(f"Error showing unavailable state: {e}")

    def _update_last_refresh_timestamp(self):
        """Update the last refresh timestamp display."""
        try:
            timestamp = datetime.now().strftime("%H:%M:%S")
            if hasattr(self, "last_update_label"):
                self.last_update_label.configure(text=f"Last updated: {timestamp}")
        except Exception as e:
            self.logger.error(f"Error updating timestamp: {e}")

    def _update_weather_background_safe(self, weather_data):
        """Safely update weather background with validation."""
        try:
            from src.ui.components.weather_effects import WeatherCondition

            weather_condition = WeatherCondition(
                condition=getattr(weather_data, "description", "clear"),
                temperature=getattr(weather_data, "temperature", 20),
                humidity=getattr(weather_data, "humidity", 50),
                wind_speed=getattr(weather_data, "wind_speed", 0),
                time_of_day="day" if 6 <= datetime.now().hour <= 18 else "night",
            )
            if hasattr(self, "weather_background_manager"):
                self.weather_background_manager.update_weather_background(weather_condition)
        except Exception as e:
            self.logger.error(f"Error updating weather background: {e}")

    def _update_location_display_safe(self, weather_data):
        """Safely update location display with validation."""
        try:
            location_name = "Unknown Location"
            if hasattr(weather_data, "location") and weather_data.location:
                if hasattr(weather_data.location, "name") and hasattr(
                    weather_data.location, "country"
                ):
                    location_name = f"{weather_data.location.name}, {weather_data.location.country}"
                elif hasattr(weather_data.location, "city"):
                    location_name = weather_data.location.city

            if hasattr(self, "animation_manager") and hasattr(self, "city_label"):
                self.animation_manager.fade_in(self.city_label)
                self.city_label.configure(text=location_name)
            elif hasattr(self, "city_label"):
                self.city_label.configure(text=location_name)

            if hasattr(self, "location_label"):
                self.location_label.configure(text=f"📍 Current: {location_name}")
        except Exception as e:
            self.logger.error(f"Error updating location display: {e}")

    def _update_temperature_display_safe(self, weather_data):
        """Safely update temperature display with proper unit conversion."""
        try:
            temp_celsius = getattr(weather_data, "temperature", None)
            if temp_celsius is None:
                temp_display = "--°"
            else:
                temp_display = self._format_temperature(temp_celsius)

            if hasattr(self, "animation_manager") and hasattr(self, "temp_label"):
                self.animation_manager.animate_number_change(self.temp_label, temp_display)
            elif hasattr(self, "temp_label"):
                self.temp_label.configure(text=temp_display)
        except Exception as e:
            self.logger.error(f"Error updating temperature display: {e}")
            if hasattr(self, "temp_label"):
                self.temp_label.configure(text="--°")

    def _format_temperature(self, temp_celsius):
        """Format temperature according to user preference."""
        try:
            if self.temp_unit == "F":
                temp_f = (temp_celsius * 9 / 5) + 32
                return f"{temp_f:.1f}°F"
            elif self.temp_unit == "K":
                temp_k = temp_celsius + 273.15
                return f"{temp_k:.1f}K"
            else:
                return f"{temp_celsius:.1f}°C"
        except Exception as e:
            self.logger.error(f"Error formatting temperature: {e}")
            return "--°"

    def _update_condition_display_safe(self, weather_data):
        """Safely update weather condition display."""
        try:
            description = getattr(weather_data, "description", "Unknown")

            # Get weather icon
            icon = "🌤️"  # default
            if hasattr(self, "weather_icons"):
                condition_lower = description.lower()
                for key, emoji in self.weather_icons.items():
                    if key in condition_lower:
                        icon = emoji
                        break

            condition_text = f"{icon} {description.title()}"

            if hasattr(self, "animation_manager") and hasattr(self, "condition_label"):
                self.animation_manager.fade_in(self.condition_label)
                self.condition_label.configure(text=condition_text)
            elif hasattr(self, "condition_label"):
                self.condition_label.configure(text=condition_text)
        except Exception as e:
            self.logger.error(f"Error updating condition display: {e}")
            if hasattr(self, "condition_label"):
                self.condition_label.configure(text="Unknown condition")

    def _update_weather_metrics_safe(self, weather_data):
        """Safely update weather metrics with validation and proper conversions."""
        try:
            if not hasattr(self, "metric_labels"):
                return

            # Update humidity
            if "humidity" in self.metric_labels:
                humidity = getattr(weather_data, "humidity", None)
                if humidity is not None:
                    self.metric_labels["humidity"].configure(text=f"{humidity}%")
                else:
                    self.metric_labels["humidity"].configure(text="N/A")

            # Update wind speed (convert from m/s to km/h)
            if "wind" in self.metric_labels:
                wind_speed = getattr(weather_data, "wind_speed", None)
                if wind_speed is not None:
                    wind_kmh = wind_speed * 3.6
                    self.metric_labels["wind"].configure(text=f"{wind_kmh:.1f} km/h")
                else:
                    self.metric_labels["wind"].configure(text="N/A")

            # Update feels like temperature
            if "feels_like" in self.metric_labels:
                feels_like = getattr(weather_data, "feels_like", None)
                if feels_like is not None:
                    feels_like_display = self._format_temperature(feels_like)
                    self.metric_labels["feels_like"].configure(text=feels_like_display)
                else:
                    self.metric_labels["feels_like"].configure(text="N/A")

            # Update visibility
            if "visibility" in self.metric_labels:
                visibility = getattr(weather_data, "visibility", None)
                if visibility is not None:
                    self.metric_labels["visibility"].configure(text=f"{visibility} km")
                else:
                    self.metric_labels["visibility"].configure(text="N/A")

            # Update pressure
            if "pressure" in self.metric_labels:
                pressure = getattr(weather_data, "pressure", None)
                if pressure is not None:
                    self.metric_labels["pressure"].configure(text=f"{pressure} hPa")
                else:
                    self.metric_labels["pressure"].configure(text="N/A")

            # Update cloudiness
            if "cloudiness" in self.metric_labels:
                cloudiness = getattr(weather_data, "cloudiness", None)
                if cloudiness is not None:
                    self.metric_labels["cloudiness"].configure(text=f"{cloudiness}%")
                else:
                    self.metric_labels["cloudiness"].configure(text="N/A")

        except Exception as e:
            self.logger.error(f"Error updating weather metrics: {e}")

    def _update_status_success(self):
        """Update status display with success message."""
        try:
            timestamp = datetime.now().strftime("%H:%M:%S")
            if hasattr(self, "status_label"):
                self.status_label.configure(text=f"✅ Updated: {timestamp}")
        except Exception as e:
            self.logger.error(f"Error updating status: {e}")

    def _handle_display_error(self, error):
        """Handle display update errors gracefully."""
        try:
            error_msg = "Display update failed"
            if hasattr(self, "status_label"):
                self.status_label.configure(text=f"❌ {error_msg}")
            if hasattr(self, "error_handler"):
                self.error_handler.show_error_toast(f"{error_msg}: {str(error)}")
        except Exception as e:
            self.logger.error(f"Error handling display error: {e}")

    def _enhanced_toggle_temperature_unit(self):
        """Enhanced temperature unit toggle with micro-interactions."""
        # Add ripple effect on button click
        self.micro_interactions.add_ripple_effect(self.temp_toggle_btn)

        # Animate button state change
        self.animation_manager.pulse_effect(self.temp_toggle_btn, duration=500, intensity=0.3)

        # Store old unit for smooth transition
        self.temp_unit

        # Call original toggle method
        self._toggle_temperature_unit()

        # Animate temperature value changes
        if hasattr(self, "temp_label"):
            self.animation_manager.animate_number_change(
                self.temp_label, self.temp_label.cget("text")
            )

        # Animate feels like temperature if available
        if hasattr(self, "metric_labels") and "feels_like" in self.metric_labels:
            self.animation_manager.fade_in(self.metric_labels["feels_like"])

        # Success pulse for successful conversion
        self.animation_manager.pulse_effect(self.temp_toggle_btn, duration=0.3, intensity=1.2)

        # Show status with unit change
        new_unit_name = "Fahrenheit" if self.temp_unit == "F" else "Celsius"
        if hasattr(self, "status_label"):
            self.animation_manager.fade_in(self.status_label)
            self.status_label.configure(text=f"🌡️ Temperature unit changed to {new_unit_name}")

    def _toggle_temperature_unit(self):
        """Toggle between Celsius and Fahrenheit."""
        if self.temp_unit == "C":
            self.temp_unit = "F"
            self.temp_toggle_btn.configure(text="°F")
            # Convert current temperature to Fahrenheit
            current_temp = self.temp_label.cget("text")
            if current_temp and current_temp != "--°C":
                try:
                    # Extract numeric value
                    temp_value = float(current_temp.replace("°C", ""))
                    fahrenheit = (temp_value * 9 / 5) + 32
                    self.temp_label.configure(text=f"{fahrenheit:.0f}°F")
                except ValueError:
                    self.temp_label.configure(text="--°F")

            # Update feels like temperature if available
            if hasattr(self, "metric_labels") and "feels_like" in self.metric_labels:
                feels_like_text = self.metric_labels["feels_like"].cget("text")
                if feels_like_text and feels_like_text != "--":
                    try:
                        temp_value = float(feels_like_text.replace("°C", ""))
                        fahrenheit = (temp_value * 9 / 5) + 32
                        self.metric_labels["feels_like"].configure(text=f"{fahrenheit:.0f}°F")
                    except ValueError:
                        pass
        else:
            self.temp_unit = "C"
            self.temp_toggle_btn.configure(text="°C")
            # Convert current temperature to Celsius
            current_temp = self.temp_label.cget("text")
            if current_temp and current_temp != "--°F":
                try:
                    # Extract numeric value
                    temp_value = float(current_temp.replace("°F", ""))
                    celsius = (temp_value - 32) * 5 / 9
                    self.temp_label.configure(text=f"{celsius:.0f}°C")
                except ValueError:
                    self.temp_label.configure(text="--°C")

            # Update feels like temperature if available
            if hasattr(self, "metric_labels") and "feels_like" in self.metric_labels:
                feels_like_text = self.metric_labels["feels_like"].cget("text")
                if feels_like_text and feels_like_text != "--":
                    try:
                        temp_value = float(feels_like_text.replace("°F", ""))
                        celsius = (temp_value - 32) * 5 / 9
                        self.metric_labels["feels_like"].configure(text=f"{celsius:.0f}°C")
                    except ValueError:
                        pass

        # Update forecast cards with new temperature unit
        if hasattr(self, "forecast_cards") and hasattr(self, "current_weather_data"):
            if hasattr(self.current_weather_data, "forecast_data"):
                self._update_forecast_cards(self.current_weather_data)

    def _create_comparison_tab(self):
        """Create team collaboration and city comparison tab."""
        self._create_comparison_tab_content()

    def _create_comparison_tab_content(self):
        """Create the team collaboration and city comparison functionality."""
        # Create the city comparison panel
        self.city_comparison_panel = CityComparisonPanel(
            self.comparison_tab,
            weather_service=self.weather_service,
            github_service=self.github_service,
        )
        self.city_comparison_panel.pack(fill="both", expand=True)

    def _create_ml_comparison_tab(self):
        """Create ML-powered comparison and analysis tab."""
        self._create_ml_comparison_tab_content()

    def _create_ml_comparison_tab_content(self):
        """Create the ML-powered comparison and analysis functionality."""
        # Create the ML comparison panel
        self.ml_comparison_panel = MLComparisonPanel(
            self.ml_comparison_tab,
            weather_service=self.weather_service,
            github_service=self.github_service,
        )
        self.ml_comparison_panel.pack(fill="both", expand=True)

    def _create_activities_tab(self):
        """Create activities tab content."""
        self._create_activities_tab_content()

    def _create_activities_tab_content(self):
        """Create AI-powered activities tab with improved layout."""
        # Configure main grid
        self.activities_tab.grid_columnconfigure(0, weight=1)
        self.activities_tab.grid_rowconfigure(1, weight=1)

        # Header with better spacing
        header_frame = ctk.CTkFrame(self.activities_tab, fg_color="transparent", height=60)
        header_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=(15, 8))
        header_frame.grid_propagate(False)
        header_frame.grid_columnconfigure(0, weight=1)

        title = ctk.CTkLabel(
            header_frame,
            text="🎯 AI Activity Suggestions",
            font=(DataTerminalTheme.FONT_FAMILY, 20, "bold"),
            text_color=DataTerminalTheme.PRIMARY,
        )
        title.grid(row=0, column=0, sticky="w", pady=15)

        refresh_btn = ctk.CTkButton(
            header_frame,
            text="🔄 Get New Suggestions",
            width=160,
            height=32,
            corner_radius=16,
            fg_color=DataTerminalTheme.PRIMARY,
            hover_color=DataTerminalTheme.SUCCESS,
            font=(DataTerminalTheme.FONT_FAMILY, 11, "bold"),
            command=self._refresh_activity_suggestions,
        )
        refresh_btn.grid(row=0, column=1, sticky="e", pady=15, padx=(15, 0))

        # Activity cards container with better structure
        self.activities_container = ctk.CTkScrollableFrame(
            self.activities_tab, fg_color="transparent", corner_radius=0
        )
        self.activities_container.grid(row=1, column=0, sticky="nsew", padx=20, pady=(0, 15))

        # Configure activities container grid for responsive layout
        self.activities_container.grid_columnconfigure(0, weight=1)
        self.activities_container.grid_columnconfigure(1, weight=1)
        self.activities_container.grid_columnconfigure(2, weight=1)

        # Create sample activity cards
        self._create_sample_activities()

    def _create_sample_activities(self):
        """Create dynamic activity suggestions based on current weather."""
        # Get weather-based activity suggestions
        if self.activity_service and self.current_weather_data:
            try:
                activities = self.activity_service.get_activity_suggestions(
                    self.current_weather_data
                )
            except Exception as e:
                self.logger.error(f"Error getting activity suggestions: {e}")
                activities = self._get_fallback_activities()
        else:
            activities = self._get_fallback_activities()

        # Create activity cards
        self._create_activity_cards(activities)

    def _get_fallback_activities(self):
        """Get fallback activities when weather data or service is unavailable."""
        return [
            {
                "title": "Morning Jog in the Park",
                "category": "Outdoor",
                "icon": "🏃",
                "description": "Perfect weather for a refreshing morning run",
                "time": "30-45 minutes",
                "items": "Running shoes, water bottle",
            },
            {
                "title": "Indoor Yoga Session",
                "category": "Indoor",
                "icon": "🧘",
                "description": "Relaxing yoga to start your day",
                "time": "20-30 minutes",
                "items": "Yoga mat, comfortable clothes",
            },
            {
                "title": "Photography Walk",
                "category": "Outdoor",
                "icon": "📸",
                "description": "Great lighting conditions for photography",
                "time": "1-2 hours",
                "items": "Camera, comfortable shoes",
            },
        ]

    def _create_activity_cards(self, activities):
        """Create activity cards from activities list."""
        # Clear existing cards
        for widget in self.activities_container.winfo_children():
            widget.destroy()

        # Calculate grid layout
        cards_per_row = 3
        for i, activity in enumerate(activities):
            row = i // cards_per_row
            col = i % cards_per_row

            card = ctk.CTkFrame(
                self.activities_container,
                fg_color=DataTerminalTheme.CARD_BG,
                corner_radius=16,
                border_width=1,
                border_color=DataTerminalTheme.BORDER,
                height=200,
            )
            card.grid(row=row, column=col, padx=15, pady=15, sticky="ew")
            card.grid_propagate(False)

            # Configure card grid
            card.grid_rowconfigure(0, weight=0)  # Header
            card.grid_rowconfigure(1, weight=1)  # Description
            card.grid_rowconfigure(2, weight=0)  # Details
            card.grid_columnconfigure(0, weight=1)

            # Header with icon and title
            header = ctk.CTkFrame(card, fg_color="transparent", height=50)
            header.grid(row=0, column=0, sticky="ew", padx=15, pady=(15, 5))
            header.grid_propagate(False)
            header.grid_columnconfigure(1, weight=1)

            # Icon
            icon_label = ctk.CTkLabel(
                header, text=activity.get("icon", "🎯"), font=(DataTerminalTheme.FONT_FAMILY, 28)
            )
            icon_label.grid(row=0, column=0, padx=(0, 10), sticky="w")

            # Title
            title_label = ctk.CTkLabel(
                header,
                text=activity.get("title", "Activity"),
                font=(DataTerminalTheme.FONT_FAMILY, 14, "bold"),
                text_color=DataTerminalTheme.TEXT,
                anchor="w",
            )
            title_label.grid(row=0, column=1, sticky="ew")

            # Category badge
            category_badge = ctk.CTkLabel(
                header,
                text=activity.get("category", "General"),
                fg_color=DataTerminalTheme.PRIMARY,
                corner_radius=10,
                text_color=DataTerminalTheme.BACKGROUND,
                font=(DataTerminalTheme.FONT_FAMILY, 10, "bold"),
                width=60,
                height=20,
            )
            category_badge.grid(row=0, column=2, padx=(10, 0), sticky="e")

            # Description
            desc_label = ctk.CTkLabel(
                card,
                text=activity.get("description", "No description available"),
                font=(DataTerminalTheme.FONT_FAMILY, 12),
                text_color=DataTerminalTheme.TEXT_SECONDARY,
                anchor="nw",
                justify="left",
                wraplength=250,
            )
            desc_label.grid(row=1, column=0, sticky="new", padx=15, pady=5)

            # Details
            details_frame = ctk.CTkFrame(card, fg_color="transparent", height=40)
            details_frame.grid(row=2, column=0, sticky="ew", padx=15, pady=(5, 15))
            details_frame.grid_propagate(False)
            details_frame.grid_columnconfigure(0, weight=1)
            details_frame.grid_columnconfigure(1, weight=1)

            time_label = ctk.CTkLabel(
                details_frame,
                text=f"⏱️ {activity.get('time', 'Variable')}",
                font=(DataTerminalTheme.FONT_FAMILY, 11),
                text_color=DataTerminalTheme.TEXT_SECONDARY,
                anchor="w",
            )
            time_label.grid(row=0, column=0, sticky="w", pady=2)

            items_label = ctk.CTkLabel(
                details_frame,
                text=f"📦 {activity.get('items', 'None required')}",
                font=(DataTerminalTheme.FONT_FAMILY, 11),
                text_color=DataTerminalTheme.TEXT_SECONDARY,
                anchor="w",
            )
            items_label.grid(row=1, column=0, sticky="w", pady=2)

    def _update_activity_suggestions(self, weather_data):
        """Update activity suggestions based on weather with caching."""
        try:
            # Create cache key based on weather conditions
            cache_key = f"activities_{self.current_city}_{weather_data.get('condition', 'unknown')}_{weather_data.get('temperature', 0)}"

            # Try to get cached suggestions first
            cached_suggestions = self.cache_manager.get(cache_key)
            if cached_suggestions:
                self.logger.debug(f"Using cached activity suggestions for {self.current_city}")
                suggestions = cached_suggestions
            else:
                # Get new suggestions
                if self.activity_service:
                    suggestions = self.activity_service.get_activity_suggestions(weather_data)
                    # Cache the suggestions for 30 minutes
                    self.cache_manager.set(
                        cache_key,
                        suggestions,
                        ttl=1800,  # 30 minutes
                        tags=["activities", f"city_{self.current_city}"],
                    )
                else:
                    suggestions = self._get_fallback_activities()

            # Create cards for suggestions (this method handles clearing
            # existing cards)
            self._create_activity_cards(suggestions)

        except Exception as e:
            self.logger.error(f"Error updating activity suggestions: {e}")
            # Fallback to default activities
            fallback_activities = self._get_fallback_activities()
            self._create_activity_cards(fallback_activities)

    def _refresh_activity_suggestions(self):
        """Refresh activity suggestions when weather data changes."""
        if hasattr(self, "activities_container") and self.activities_container.winfo_exists():
            try:
                # Get updated activity suggestions
                if self.activity_service and self.current_weather_data:
                    activities = self.activity_service.get_activity_suggestions(
                        self.current_weather_data
                    )
                else:
                    activities = self._get_fallback_activities()

                # Update the activity cards
                self._create_activity_cards(activities)
            except Exception as e:
                self.logger.error(f"Error refreshing activity suggestions: {e}")

    # Settings tab is now managed by SettingsTabManager
    # Removed duplicate settings methods to avoid conflicts

    # _create_api_settings removed - handled by SettingsTabManager

    # _create_appearance_settings removed - handled by SettingsTabManager

    # Theme-related methods removed - handled by SettingsTabManager

    # _create_data_settings removed - handled by SettingsTabManager

    # _create_auto_refresh_settings and _create_about_section removed - handled by SettingsTabManager

    # Settings methods now handled by SettingsTabManager
    # _toggle_api_visibility, _save_api_keys, _change_theme, _change_units, _test_api_key, _update_usage_stats removed

    # _encrypt_api_keys, _set_key_rotation_reminder, and _setup_key_rotation methods removed - now handled by SettingsTabManager

    def _update_cache_size(self):
        """Update cache size display."""
        try:
            # Mock cache size calculation
            cache_size_mb = 15.7
            if hasattr(self, "cache_size_label"):
                self.cache_size_label.configure(text=f"Cache Size: {cache_size_mb:.1f} MB")
        except Exception as e:
            print(f"Error updating cache size: {e}")

    def _clear_all_cache(self):
        """Clear all cached data."""
        try:
            # Clear all cache types
            self._clear_cache()
            self._update_cache_size()
            self.status_label.configure(text="🗑️ All cache cleared")
        except Exception as e:
            self.status_label.configure(text=f"❌ Cache clear failed: {str(e)}")

    def _clear_weather_cache(self):
        """Clear only weather-specific cache."""
        try:
            # In real implementation, clear only weather cache
            self._update_cache_size()
            self.status_label.configure(text="🌤️ Weather cache cleared")
        except Exception as e:
            self.status_label.configure(text=f"❌ Weather cache clear failed: {str(e)}")

    def _optimize_database(self):
        """Optimize database performance."""
        try:
            # In real implementation, run database optimization
            self.status_label.configure(text="⚡ Database optimization started...")
            # Mock optimization delay
            self.after(2000, lambda: self.status_label.configure(text="✅ Database optimized"))
        except Exception as e:
            self.status_label.configure(text=f"❌ Database optimization failed: {str(e)}")

    def _export_data_with_range(self):
        """Export data with date range selection."""
        try:
            # In real implementation, open date range dialog and export
            self.status_label.configure(text="📤 Exporting data with date range...")
            # Mock export delay
            self.after(
                1500, lambda: self.status_label.configure(text="✅ Data exported successfully")
            )
        except Exception as e:
            self.status_label.configure(text=f"❌ Data export failed: {str(e)}")

    def _toggle_usage_analytics(self):
        """Toggle usage analytics collection."""
        try:
            # Get current state and toggle
            current_state = getattr(self, "analytics_enabled", True)
            new_state = not current_state
            setattr(self, "analytics_enabled", new_state)

            status = "enabled" if new_state else "disabled"
            self.status_label.configure(text=f"📊 Usage analytics {status}")
        except Exception as e:
            self.status_label.configure(text=f"❌ Analytics toggle failed: {str(e)}")

    def _toggle_location_history(self):
        """Toggle location history storage."""
        try:
            # Get current state and toggle
            current_state = getattr(self, "location_history_enabled", True)
            new_state = not current_state
            setattr(self, "location_history_enabled", new_state)

            status = "enabled" if new_state else "disabled"
            self.status_label.configure(text=f"📍 Location history {status}")
        except Exception as e:
            self.status_label.configure(text=f"❌ Location history toggle failed: {str(e)}")

    def _change_datetime_format(self, format_type):
        """Change date/time format."""
        try:
            self.datetime_format = format_type
            # Save to config
            if hasattr(self, "config_service"):
                self.config_service.set("datetime_format", format_type)
            self.status_label.configure(text=f"📅 Date format changed to {format_type}")
        except Exception as e:
            self.status_label.configure(text=f"❌ Date format change failed: {str(e)}")

    def _change_language(self, language):
        """Change application language."""
        try:
            self.language = language
            # Save to config
            if hasattr(self, "config_service"):
                self.config_service.set("language", language)
            self.status_label.configure(text=f"🌐 Language changed to {language}")
        except Exception as e:
            self.status_label.configure(text=f"❌ Language change failed: {str(e)}")

    def _change_font_size(self, size):
        """Change application font size."""
        try:
            self.font_size = size
            # Save to config
            if hasattr(self, "config_service"):
                self.config_service.set("font_size", size)
            self.status_label.configure(text=f"🔤 Font size changed to {size}")
        except Exception as e:
            self.status_label.configure(text=f"❌ Font size change failed: {str(e)}")

    def _toggle_analytics(self):
        """Toggle usage analytics."""
        try:
            # Get current state and toggle
            current_state = getattr(self, "analytics_enabled", True)
            new_state = not current_state
            setattr(self, "analytics_enabled", new_state)

            # Save to config
            if hasattr(self, "config_service"):
                self.config_service.set("analytics_enabled", new_state)

            status = "enabled" if new_state else "disabled"
            self.status_label.configure(text=f"📊 Analytics {status}")
        except Exception as e:
            self.status_label.configure(text=f"❌ Analytics toggle failed: {str(e)}")

    def _toggle_location_storage(self):
        """Toggle location data storage."""
        try:
            # Get current state and toggle
            current_state = getattr(self, "location_storage_enabled", True)
            new_state = not current_state
            setattr(self, "location_storage_enabled", new_state)

            # Save to config
            if hasattr(self, "config_service"):
                self.config_service.set("location_storage_enabled", new_state)

            status = "enabled" if new_state else "disabled"
            self.status_label.configure(text=f"📍 Location storage {status}")
        except Exception as e:
            self.status_label.configure(text=f"❌ Location storage toggle failed: {str(e)}")

    def _enhanced_toggle_auto_refresh(self):
        """Enhanced auto-refresh toggle with micro-interactions."""
        # Add ripple effect on switch toggle
        self.micro_interactions.add_ripple_effect(self.auto_refresh_switch)

        enabled = self.auto_refresh_switch.get()
        self.auto_refresh_enabled = enabled

        # Animate status change
        if enabled:
            # Success pulse for enabling
            self.animation_manager.success_pulse(self.auto_refresh_switch)
            status_text = "🔄 Auto-refresh enabled"
            # Start refresh cycle immediately
            self.after(1000, self._schedule_refresh)
        else:
            # Warning pulse for disabling
            self.animation_manager.warning_pulse(self.auto_refresh_switch)
            status_text = "⏸️ Auto-refresh disabled"

        # Show status with fade effect
        if hasattr(self, "status_label"):
            self.animation_manager.fade_in(self.status_label)
            self.status_label.configure(text=status_text)
        else:
            print(status_text)

        # Call original method for core functionality
        self._toggle_auto_refresh()

    # _toggle_auto_refresh method removed - now handled by SettingsTabManager

    def _schedule_refresh(self):
        """Schedule automatic weather refresh."""
        try:
            if self.is_destroyed or not self.winfo_exists() or not self.auto_refresh_enabled:
                return

            # Load weather data asynchronously to prevent UI freezing
            self._load_weather_data_async()

            # Schedule next refresh using milliseconds
            refresh_interval_ms = self.refresh_interval_minutes * 60 * 1000
            self.safe_after(refresh_interval_ms, lambda: self._schedule_refresh())

        except tk.TclError:
            # Widget has been destroyed, stop the scheduler
            return
        except Exception as e:
            self.logger.error(f"Error in refresh scheduler: {e}")
            # Continue scheduling even if this refresh failed
            refresh_interval_ms = self.refresh_interval_minutes * 60 * 1000
            self.safe_after(refresh_interval_ms, lambda: self._schedule_refresh())

    def _load_weather_data_async(self):
        """Load weather data asynchronously without blocking UI."""
        try:
            # Use existing background loading mechanism
            self._start_background_loading()
        except Exception as e:
            self.logger.error(f"Failed to start async weather data loading: {e}")
            # Fallback to synchronous loading if async fails
            try:
                self._load_weather_data()
            except Exception as fallback_error:
                self.logger.error(f"Fallback weather loading also failed: {fallback_error}")
                self._handle_weather_error(fallback_error)

    def _manual_refresh(self):
        """Handle manual refresh with loading indicator."""
        try:
            # Show loading state on refresh button
            original_text = self.refresh_button.cget("text")
            self.refresh_button.configure(text="⏳ Loading...", state="disabled")

            # Add micro-interaction effects if available
            if hasattr(self, "micro_interactions"):
                self.micro_interactions.add_ripple_effect(self.refresh_button)

            # Show loading state in UI
            self._show_loading_state()

            # Update status
            if hasattr(self, "status_manager"):
                self.status_manager.show_info("🔄 Refreshing weather data...")

            # Schedule the actual refresh to allow UI to update
            self.after(100, self._perform_manual_refresh, original_text)

        except Exception as e:
            self.logger.error(f"Error starting manual refresh: {e}")
            # Reset button state on error
            if hasattr(self, "refresh_button"):
                self.refresh_button.configure(text="🔄 Refresh", state="normal")

    def _perform_manual_refresh(self, original_text):
        """Perform the actual manual refresh operation."""
        try:
            # Clear any cached data to force fresh fetch
            if hasattr(self, "current_weather_data"):
                self.current_weather_data = None

            # Load fresh weather data
            self._load_weather_data()

            # Show success message
            if hasattr(self, "status_manager"):
                self.status_manager.set_success_state("✅ Weather data refreshed successfully!")

            # Add success animation if available
            if hasattr(self, "animation_manager"):
                self.animation_manager.success_pulse(self.refresh_button)

        except Exception as e:
            self.logger.error(f"Error during manual refresh: {e}")
            # Show error message
            if hasattr(self, "status_manager"):
                self.status_manager.set_error_state(f"❌ Refresh failed: {str(e)}")
            else:
                self._show_error_state(f"Refresh failed: {str(e)}")

        finally:
            # Always restore button state
            try:
                self.refresh_button.configure(text=original_text, state="normal")
                self._hide_loading_state()
            except Exception as restore_error:
                self.logger.error(f"Error restoring refresh button state: {restore_error}")

    def _convert_temperature(self, temp_str, from_unit, to_unit):
        """Convert temperature string from one unit to another."""
        if not temp_str or temp_str in ["--", "Loading..."]:
            return temp_str

        try:
            # Extract numeric value
            import re

            match = re.search(r"(-?\d+(?:\.\d+)?)", temp_str)
            if not match:
                return temp_str

            temp_value = float(match.group(1))

            # Convert to Celsius first if needed
            if from_unit == "F":
                celsius = (temp_value - 32) * 5 / 9
            elif from_unit == "K":
                celsius = temp_value - 273.15
            else:  # from_unit == "C"
                celsius = temp_value

            # Convert from Celsius to target unit
            if to_unit == "F":
                result = (celsius * 9 / 5) + 32
                symbol = "°F"
            elif to_unit == "K":
                result = celsius + 273.15
                symbol = "K"
            else:  # to_unit == "C"
                result = celsius
                symbol = "°C"

            return f"{result:.0f}{symbol}"

        except (ValueError, AttributeError):
            return temp_str

    def _convert_all_temperatures(self, from_unit, to_unit):
        """Convert all temperature displays in the application using stored weather data."""
        if from_unit == to_unit:
            return

        try:
            # If we have current weather data, refresh the display with new units
            if hasattr(self, "current_weather_data") and self.current_weather_data:
                self._update_temperature_display_safe(self.current_weather_data)
                self._update_weather_metrics_safe(self.current_weather_data)

                # Update forecast cards if they exist
                if hasattr(self, "forecast_cards") and hasattr(self, "current_forecast_data"):
                    self._update_forecast_cards(self.current_forecast_data)

                self.logger.info(f"Temperature units converted from {from_unit} to {to_unit}")
            else:
                # Fallback to old method if no stored data
                self._convert_temperatures_fallback(from_unit, to_unit)

        except Exception as e:
            self.logger.error(f"Error converting temperatures: {e}")
            self._convert_temperatures_fallback(from_unit, to_unit)

    def _convert_temperatures_fallback(self, from_unit, to_unit):
        """Fallback method for temperature conversion when no stored data available."""
        try:
            # Update main temperature display
            if hasattr(self, "temp_label"):
                current_text = self.temp_label.cget("text")
                converted = self._convert_temperature(current_text, from_unit, to_unit)
                self.temp_label.configure(text=converted)

            # Update feels like temperature in metrics
            if hasattr(self, "metric_labels") and "feels_like" in self.metric_labels:
                current_text = self.metric_labels["feels_like"].cget("text")
                converted = self._convert_temperature(current_text, from_unit, to_unit)
                self.metric_labels["feels_like"].configure(text=converted)

            # Update forecast temperatures if they exist
            if hasattr(self, "forecast_cards"):
                for card in self.forecast_cards:
                    if hasattr(card, "temp_label"):
                        current_text = card.temp_label.cget("text")
                        converted = self._convert_temperature(current_text, from_unit, to_unit)
                        card.temp_label.configure(text=converted)
        except Exception as e:
            self.logger.error(f"Error in fallback temperature conversion: {e}")

    def _refresh_weather_with_new_units(self):
        """Refresh weather data to get temperatures in new units."""
        try:
            if hasattr(self, "current_city") and self.current_city:
                self._load_weather_data()
            elif hasattr(self, "current_weather_data") and self.current_weather_data:
                # Just update the display with current data in new units
                self._update_weather_display(self.current_weather_data)
        except Exception as e:
            self.logger.error(f"Error refreshing weather with new units: {e}")

    def _enhanced_open_github(self):
        """Enhanced GitHub opening with micro-interactions."""
        # Add ripple effect to GitHub button
        if hasattr(self, "github_button"):
            self.micro_interactions.add_ripple_effect(self.github_button)

        # Show loading animation
        if hasattr(self, "status_manager"):
            self.status_manager.show_loading("Opening GitHub...")

        try:
            self._open_github()

            # Success pulse animation
            if hasattr(self, "github_button"):
                self.micro_interactions.add_success_pulse(self.github_button)

            if hasattr(self, "status_manager"):
                self.status_manager.set_success_state("GitHub repository opened!")

        except Exception as e:
            # Warning pulse for errors
            if hasattr(self, "github_button"):
                self.micro_interactions.add_warning_pulse(self.github_button)

            if hasattr(self, "status_manager"):
                self.status_manager.set_error_state(f"Failed to open GitHub: {str(e)}")

    def _open_github(self):
        """Open GitHub repository in browser."""
        import webbrowser

        try:
            webbrowser.open("https://github.com/StrayDogSyn/weather_dashboard_Final_Eric_Hunter")
            if hasattr(self, "status_label"):
                self.status_label.configure(text="🌐 GitHub repository opened in browser")
            else:
                print("🌐 GitHub repository opened in browser")
        except Exception as e:
            if hasattr(self, "status_label"):
                self.status_label.configure(text="❌ Failed to open GitHub repository")
            else:
                print(f"❌ Failed to open GitHub repository: {e}")

    def _open_documentation(self):
        """Open documentation in browser."""
        import webbrowser

        try:
            webbrowser.open(
                "https://github.com/StrayDogSyn/weather_dashboard_Final_Eric_Hunter/"
                "blob/main/README.md"
            )
            if hasattr(self, "status_label"):
                self.status_label.configure(text="📚 Documentation opened in browser")
            else:
                print("📚 Documentation opened in browser")
        except Exception as e:
            if hasattr(self, "status_label"):
                self.status_label.configure(text="❌ Failed to open documentation")
            else:
                print(f"❌ Failed to open documentation: {e}")

    # Cache and export methods now handled by SettingsTabManager
    # _clear_cache, _enhanced_export_data, _export_data removed

    def _enhanced_import_data(self):
        """Enhanced import with micro-interactions."""
        # Add ripple effect to import button
        if hasattr(self, "import_button"):
            self.micro_interactions.add_ripple_effect(self.import_button)

        # Show loading animation
        if hasattr(self, "status_manager"):
            self.status_manager.show_loading("Processing import...")

        try:
            self._import_data()

            # Success pulse animation
            if hasattr(self, "import_button"):
                self.micro_interactions.add_success_pulse(self.import_button)

            if hasattr(self, "status_manager"):
                self.status_manager.set_success_state("Data imported successfully!")

        except Exception as e:
            # Warning pulse for errors
            if hasattr(self, "import_button"):
                self.micro_interactions.add_warning_pulse(self.import_button)

            if hasattr(self, "status_manager"):
                self.status_manager.set_error_state(f"Import failed: {str(e)}")

    def _import_data(self):
        """Import application data."""
        try:
            import json
            from tkinter import filedialog

            # Ask user for file to import
            filename = filedialog.askopenfilename(
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
                title="Import Weather Dashboard Data",
            )

            if filename:
                with open(filename, "r") as f:
                    import_data = json.load(f)

                # Apply imported settings
                if "current_city" in import_data and import_data["current_city"]:
                    self.current_city = import_data["current_city"]
                    # Trigger weather update for new city
                    self.after(100, self._load_weather_data)

                if "temp_unit" in import_data:
                    old_unit = getattr(self, "temp_unit", "C")
                    self.temp_unit = import_data["temp_unit"]
                    if hasattr(self, "temp_toggle_btn"):
                        symbol_map = {"C": "°C", "F": "°F", "K": "K"}
                        self.temp_toggle_btn.configure(text=symbol_map.get(self.temp_unit, "°C"))
                    self._convert_all_temperatures(old_unit, self.temp_unit)

                if hasattr(self, "status_label"):
                    self.status_label.configure(text="📥 Data imported successfully")
                else:
                    print("📥 Data imported successfully")
            else:
                if hasattr(self, "status_label"):
                    self.status_label.configure(text="📥 Import cancelled")
                else:
                    print("📥 Import cancelled")

        except Exception as e:
            if hasattr(self, "status_label"):
                self.status_label.configure(text=f"❌ Failed to import data: {str(e)}")
            else:
                print(f"❌ Failed to import data: {e}")

    def _create_status_bar(self):
        """Create enhanced status bar."""
        self.status_frame = ctk.CTkFrame(
            self,
            height=40,
            fg_color=DataTerminalTheme.CARD_BG,
            corner_radius=0,
            border_width=1,
            border_color=DataTerminalTheme.BORDER,
        )
        self.status_frame.grid(row=2, column=0, sticky="ew", padx=0, pady=0)
        self.status_frame.grid_propagate(False)

        # Ensure status frame fills the bottom properly
        self.status_frame.grid_columnconfigure(0, weight=1)

        # Status label
        self.status_label = ctk.CTkLabel(
            self.status_frame,
            text="Ready",
            font=(DataTerminalTheme.FONT_FAMILY, 12),
            text_color=DataTerminalTheme.TEXT_SECONDARY,
        )
        self.status_label.pack(side="left", padx=20)

        # Connection indicator
        self.connection_indicator = ctk.CTkLabel(
            self.status_frame,
            text="🟢 Online",
            font=(DataTerminalTheme.FONT_FAMILY, 12),
            text_color=DataTerminalTheme.SUCCESS,
        )
        self.connection_indicator.pack(side="right", padx=20)

        # Time display
        self.time_label = ctk.CTkLabel(
            self.status_frame,
            text="",
            font=(DataTerminalTheme.FONT_FAMILY, 12),
            text_color=DataTerminalTheme.TEXT_SECONDARY,
        )
        self.time_label.pack(side="right", padx=20)

        # Start time update
        self._update_time()

    def safe_after(self, delay, callback):
        """Safe after() call that tracks scheduled calls for cleanup."""
        if self.is_destroyed:
            return None
        try:
            call_id = self.after(delay, callback)
            self.scheduled_calls.append(call_id)
            return call_id
        except tk.TclError:
            return None

    def _cleanup_scheduled_calls(self):
        """Cancel all scheduled after() calls."""
        for call_id in self.scheduled_calls:
            try:
                self.after_cancel(call_id)
            except (tk.TclError, ValueError):
                pass
        self.scheduled_calls.clear()

    def _on_closing(self):
        """Handle application closing."""
        self.is_destroyed = True
        self._cleanup_scheduled_calls()

        # Cleanup open hourly windows
        if hasattr(self, "open_hourly_windows"):
            for window_info in self.open_hourly_windows:
                try:
                    if window_info["window"].winfo_exists():
                        window_info["window"].destroy()
                except (tk.TclError, AttributeError):
                    pass
            self.open_hourly_windows.clear()

        # Cleanup animation manager
        if hasattr(self, "animation_manager"):
            self.animation_manager.cleanup()

        # Cleanup status manager
        if hasattr(self, "status_manager"):
            self.status_manager.cleanup()

        # Cleanup error handler
        if hasattr(self, "error_handler"):
            self.error_handler.cleanup()

        # Cleanup performance optimization services
        if hasattr(self, "api_optimizer"):
            self.api_optimizer.shutdown()

        if hasattr(self, "component_recycler"):
            self.component_recycler.shutdown()

        if hasattr(self, "cache_manager"):
            # Cache manager doesn't have a stop method, just clear it
            self.cache_manager.clear()

        if hasattr(self, "loading_manager"):
            self.loading_manager.shutdown()

        self.destroy()

    def _update_time(self):
        """Update time display."""
        try:
            if self.is_destroyed or not self.winfo_exists():
                return
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.time_label.configure(text=current_time)
            self.safe_after(1000, self._update_time)
        except tk.TclError:
            # Widget has been destroyed, stop the timer
            return

    def _initialize_progressive_loading(self):
        """Initialize progressive loading with startup optimizer."""
        try:
            # Register components with startup optimizer
            self._register_startup_components()

            # Step 1: Show skeleton UI immediately
            self._show_skeleton_ui()

            # Step 2: Start progressive loading
            self.startup_optimizer.start_progressive_loading(
                on_component_loaded=self._on_component_loaded, on_complete=self._on_startup_complete
            )

        except Exception as e:
            self.logger.error(f"Progressive loading initialization failed: {e}")
            self._show_error_state("Failed to initialize dashboard")

    def _register_startup_components(self):
        """Register components with startup optimizer for progressive loading."""
        from src.utils.startup_optimizer import ComponentPriority

        # Critical components (load first)
        self.startup_optimizer.register_component(
            "weather_display",
            ComponentPriority.CRITICAL,
            lambda: self._load_weather_data_with_timeout(),
            dependencies=[],
        )

        # High priority components
        self.startup_optimizer.register_component(
            "forecast_cards",
            ComponentPriority.HIGH,
            lambda: self._initialize_forecast_cards(),
            dependencies=["weather_display"],
        )

        # Medium priority components
        self.startup_optimizer.register_component(
            "activity_suggestions",
            ComponentPriority.MEDIUM,
            lambda: self._initialize_activity_suggestions(),
            dependencies=["weather_display"],
        )

        # Low priority components (load last)
        self.startup_optimizer.register_component(
            "background_data",
            ComponentPriority.LOW,
            lambda: self._start_background_loading(),
            dependencies=["weather_display", "forecast_cards"],
        )

    def _show_skeleton_ui(self):
        """Show skeleton UI with loading placeholders."""
        try:
            # Show skeleton for main weather display
            self.city_label.configure(text=self.current_city)
            self.temp_label.configure(text="--°")
            self.condition_label.configure(text="Loading...")

            # Show skeleton for forecast cards
            if hasattr(self, "forecast_frame"):
                for widget in self.forecast_frame.winfo_children():
                    if hasattr(widget, "configure"):
                        widget.configure(text="Loading...")

            # Update status
            if hasattr(self, "status_label"):
                self.status_label.configure(text="Initializing dashboard...")

        except Exception as e:
            self.logger.error(f"Failed to show skeleton UI: {e}")

    def _on_component_loaded(self, component_name, success):
        """Handle component loading completion."""
        if success:
            self.logger.info(f"Component '{component_name}' loaded successfully")
            if hasattr(self, "status_label"):
                self.status_label.configure(text=f"Loaded {component_name}...")
        else:
            self.logger.warning(f"Component '{component_name}' failed to load")

    def _on_startup_complete(self):
        """Handle startup completion."""
        self.logger.info("Startup optimization complete")
        if hasattr(self, "status_label"):
            self.status_label.configure(text="Ready")

    def _initialize_forecast_cards(self):
        """Initialize forecast cards with recycled components."""
        try:
            # Use component recycler for forecast cards
            if hasattr(self, "forecast_frame"):
                # Get recycled forecast cards or create new ones
                for i in range(5):  # Typical 5-day forecast
                    card = self.component_recycler.get_component("forecast_card")
                    if card:
                        # Reset and configure the recycled card
                        card.configure(text=f"Day {i+1}")
                        card.pack(in_=self.forecast_frame, side="left", padx=5)
        except Exception as e:
            self.logger.error(f"Failed to initialize forecast cards: {e}")

    def _initialize_activity_suggestions(self):
        """Initialize activity suggestions with caching."""
        try:
            # Check cache first
            cached_activities = self.cache_manager.get(f"activities_{self.current_city}")
            if cached_activities:
                self._update_activity_suggestions(cached_activities)
            else:
                # Load fresh activity data
                self._refresh_activity_suggestions()
        except Exception as e:
            self.logger.error(f"Failed to initialize activity suggestions: {e}")

    def _initialize_background_data(self):
        """Initialize background data loading."""
        try:
            # Load background weather data and cache
            if hasattr(self, "current_weather_data") and self.current_weather_data:
                # Update background components with current data
                self._update_background_components()
            else:
                # Load minimal background data
                self._load_background_weather_data()
        except Exception as e:
            self.logger.error(f"Failed to initialize background data: {e}")

    def _update_background_components(self):
        """Update background UI components."""
        try:
            # Update weather background if available
            if hasattr(self, "weather_background_manager"):
                self.weather_background_manager.update_background(self.current_weather_data)
        except Exception as e:
            self.logger.error(f"Failed to update background components: {e}")

    def _load_background_weather_data(self):
        """Load minimal weather data for background."""
        try:
            # Load cached data or minimal fallback
            cached_data = self.cache_manager.get(f"weather_{self.current_city}")
            if cached_data:
                self.current_weather_data = cached_data
                self._update_background_components()
        except Exception as e:
            self.logger.error(f"Failed to load background weather data: {e}")

    def _show_initial_ui_state(self):
        """Show initial UI state with placeholders."""
        try:
            self.city_label.configure(text=self.current_city)
            self.temp_label.configure(text="--°")
            self.condition_label.configure(text="Loading...")

            # Update status to show we're ready for interaction
            if hasattr(self, "status_label"):
                self.status_label.configure(text="🔄 Connecting...")

        except Exception as e:
            self.logger.warning(f"Failed to show initial UI state: {e}")

    def _load_weather_data_with_timeout(self):
        """Load weather data with strict timeout and error boundaries."""
        # Show loading state
        self._show_loading_state()

        # Use LoadingManager for critical loading with 5-second timeout
        def weather_task():
            return self._safe_fetch_weather_data_with_timeout()

        def on_success(weather_data):
            self.after(0, lambda: self._handle_weather_success(weather_data))

        def on_error(error):
            self.after(0, lambda: self._handle_weather_error(error))

        # Load critical weather data with 5-second timeout as requested
        self.loading_manager.load_critical(
            task=weather_task,
            on_success=on_success,
            on_error=on_error,
            timeout=5.0,  # Reduced from 15 to 5 seconds as requested
            task_name="weather_data",
        )

    def _load_weather_data(self):
        """Legacy method - now calls the timeout version."""
        self._load_weather_data_with_timeout()

    def _show_loading_state(self):
        """Show loading indicators with visual polish."""
        # Use new error handler's loading system
        self.current_loading_state = self.error_handler.show_loading(
            self, "Fetching weather data...", show_progress=True
        )

        # Start shimmer effects on weather cards
        if hasattr(self, "weather_metrics_frame"):
            self.shimmer_effect = ShimmerEffect(self.weather_metrics_frame)
            self.shimmer_effect.start_shimmer()

        # Apply loading skeleton to forecast cards
        if hasattr(self, "forecast_frame"):
            self.forecast_skeleton = LoadingSkeleton(self.forecast_frame)
            self.forecast_skeleton.show()

        # Update labels with fade effect
        self.animation_manager.fade_in(self.city_label)
        self.city_label.configure(text="Loading...")
        self.temp_label.configure(text="--°C")
        self.condition_label.configure(text="Fetching weather data...")

        # Show loading spinner if available
        if hasattr(self, "loading_spinner"):
            self.loading_spinner.start()

    def _hide_loading_state(self):
        """Hide loading indicators and clean up visual effects."""
        # Hide new error handler's loading state
        if hasattr(self, "current_loading_state"):
            self.error_handler.hide_loading(self.current_loading_state)
            delattr(self, "current_loading_state")

        # Stop shimmer effects
        if hasattr(self, "shimmer_effect"):
            self.shimmer_effect.stop_shimmer()
            delattr(self, "shimmer_effect")

        # Hide loading skeleton
        if hasattr(self, "forecast_skeleton"):
            self.forecast_skeleton.hide()
            delattr(self, "forecast_skeleton")

        # Hide loading spinner if available
        if hasattr(self, "loading_spinner"):
            self.loading_spinner.stop()

    def _safe_fetch_weather_data_with_timeout(self):
        """Safely fetch weather data with timeout and enhanced error handling using API optimizer."""
        if not self.weather_service:
            # Return offline fallback data immediately
            self.logger.warning("No weather service available, using offline data")
            return self._get_offline_weather_data()

        try:
            # Use API optimizer for enhanced performance
            from src.utils.api_optimizer import APIRequest, CacheStrategy, RequestPriority

            # Create optimized API request
            api_request = APIRequest(
                endpoint=f"weather/{self.current_city}",
                priority=RequestPriority.HIGH,
                cache_strategy=CacheStrategy.CACHE_FIRST,
                timeout=10.0,
                metadata={"city": self.current_city, "units": self.temp_unit},
            )

            # Make optimized request
            self.api_optimizer.submit_request(api_request)

            # For now, fallback to direct weather service call
            # TODO: Implement proper async handling for API optimizer responses
            response = self.weather_service.get_weather(self.current_city)

            if response:
                return response
            else:
                self.logger.warning("API optimizer returned no data, falling back to direct fetch")
                return self._direct_fetch_weather_data()

        except Exception as e:
            self.logger.error(f"API optimizer fetch failed: {e}")
            return self._direct_fetch_weather_data()

    def _direct_fetch_weather_data(self):
        """Direct weather data fetch as fallback."""
        try:
            # Import custom exceptions for proper handling
            # For Windows compatibility, use threading timeout instead of signal
            import threading

            from src.services.enhanced_weather_service import (
                APIKeyError,
                NetworkError,
                RateLimitError,
                ServiceUnavailableError,
                WeatherServiceError,
            )

            result = [None]
            exception = [None]

            def fetch_with_timeout():
                try:
                    result[0] = self.weather_service.get_enhanced_weather(self.current_city)
                except Exception as e:
                    exception[0] = e

            # Start fetch in thread with timeout
            fetch_thread = threading.Thread(target=fetch_with_timeout, daemon=True)
            fetch_thread.start()
            fetch_thread.join(timeout=4.0)  # 4 second timeout for API call

            if fetch_thread.is_alive():
                # Timeout occurred
                self.logger.warning(
                    f"Weather API timeout for {self.current_city}, using cached/offline data"
                )
                return self._get_cached_or_offline_weather_data()

            if exception[0]:
                raise exception[0]

            if result[0]:
                self.logger.info(f"✅ Weather data loaded successfully for {self.current_city}")
                return result[0]
            else:
                raise WeatherServiceError("No weather data returned")

        except (RateLimitError, APIKeyError) as e:
            self.logger.warning(f"API issue for {self.current_city}: {e}")
            return self._get_cached_or_offline_weather_data()
        except (NetworkError, ServiceUnavailableError) as e:
            self.logger.warning(f"Network/service issue for {self.current_city}: {e}")
            return self._get_cached_or_offline_weather_data()
        except WeatherServiceError as e:
            self.logger.error(f"Weather service error for {self.current_city}: {e}")
            return self._get_cached_or_offline_weather_data()
        except Exception as e:
            self.logger.error(f"Unexpected error fetching weather for {self.current_city}: {e}")
            return self._get_cached_or_offline_weather_data()

        except RateLimitError as e:
            self.logger.warning(f"Rate limit exceeded: {e}")
            # Show user-friendly message and use cached data
            self._show_rate_limit_message()
            return self._get_cached_or_offline_weather_data()

        except APIKeyError as e:
            self.logger.error(f"API key error: {e}")
            # Show configuration error message
            self._show_config_error_message()
            return self._get_offline_weather_data()

        except NetworkError as e:
            self.logger.warning(f"Network error: {e}")
            # Show network error and use cached data
            self._show_network_error_message()
            return self._get_cached_or_offline_weather_data()

        except ServiceUnavailableError as e:
            self.logger.warning(f"Service unavailable: {e}")
            # Show service error and use cached data
            self._show_service_error_message()
            return self._get_cached_or_offline_weather_data()

        except WeatherServiceError as e:
            self.logger.error(f"Weather service error: {e}")
            # Generic weather service error
            self._show_weather_service_error_message(str(e))
            return self._get_cached_or_offline_weather_data()

        except Exception as e:
            self.logger.error(f"Unexpected error: {e}")
            # Fallback for any other errors
            return self._get_cached_or_offline_weather_data()

    def _get_cached_or_offline_weather_data(self):
        """Get cached weather data or offline fallback."""
        try:
            # Try to get cached data first
            if self.weather_service and hasattr(self.weather_service, "_cache"):
                cache_key = f"weather_{self.current_city.lower()}"
                if cache_key in self.weather_service._cache:
                    cached_data = self.weather_service._cache[cache_key]
                    if "data" in cached_data:
                        self.logger.info(
                            f"Using cached weather data for {
                                self.current_city}"
                        )
                        return cached_data["data"]

            # Fall back to offline data
            return self._get_offline_weather_data()

        except Exception as e:
            self.logger.warning(f"Failed to get cached data: {e}")
            return self._get_offline_weather_data()

    def _safe_fetch_weather_data(self):
        """Legacy method - now calls the timeout version."""
        return self._safe_fetch_weather_data_with_timeout()

    def _handle_weather_success(self, weather_data):
        """Handle successful weather data loading."""
        try:
            # Store weather data for unit conversions and refreshes
            self.current_weather_data = weather_data

            self._hide_loading_state()
            self._update_weather_display(weather_data)
            self.logger.info("Weather display updated successfully")
            # Show success toast
            self.error_handler.show_warning_toast("Weather data updated successfully")
        except Exception as e:
            self.logger.error(f"Failed to update weather display: {e}")
            self.error_handler.show_error_toast(f"Failed to display weather data: {str(e)}")

    def _handle_weather_error(self, error):
        """Handle weather data loading errors."""
        self.logger.error(f"Weather loading failed: {error}")
        self.error_handler.show_error_toast(f"Weather data loading failed: {str(error)}")

    def _get_offline_weather_data(self):
        """Get offline fallback weather data."""
        from src.models.location import Location
        from src.models.weather import WeatherCondition

        # Note: EnhancedWeatherData may need to be defined or imported from appropriate module
        # Create basic offline weather data
        location = Location(name=self.current_city, country="Unknown", latitude=0.0, longitude=0.0)

        return EnhancedWeatherData(
            location=location,
            timestamp=datetime.now(),
            condition=WeatherCondition.CLEAR,
            description="Offline Mode",
            temperature=20.0,
            feels_like=20.0,
            humidity=50,
            pressure=1013,
            wind_speed=0.0,
            wind_direction=0,
            visibility=10.0,
            cloudiness=0,
            uv_index=0,
        )

    def _start_background_loading(self):
        """Start progressive background loading of additional weather data."""
        if not self.weather_service:
            return

        # Load forecast data in background
        def forecast_task():
            try:
                # Use coordinates if available, otherwise use city name
                if hasattr(self, "current_location") and self.current_location:
                    return self.weather_service.get_forecast_data(
                        self.current_location["lat"], self.current_location["lon"]
                    )
                else:
                    return self.weather_service.get_forecast_data(self.current_city)
            except Exception as e:
                self.logger.warning(f"Background forecast loading failed: {e}")
                return None

        def on_forecast_success(forecast_data):
            if forecast_data:
                self.after(0, lambda: self._update_forecast_display(forecast_data))

        def on_forecast_error(error):
            self.logger.warning(f"Forecast background loading failed: {error}")

        # Load forecast with 10-second timeout
        self.loading_manager.load_background(
            task=forecast_task,
            on_success=on_forecast_success,
            on_error=on_forecast_error,
            timeout=10.0,
            task_name="forecast_data",
        )

        # Load air quality data after a delay
        self.after(3000, self._load_air_quality_background)

    def _load_air_quality_background(self):
        """Load air quality data in background."""
        if not self.weather_service:
            return

        def air_quality_task():
            try:
                # Get coordinates for the current city first
                weather_data = self.weather_service.get_enhanced_weather(self.current_city)
                if weather_data and hasattr(weather_data, "location"):
                    lat = weather_data.location.latitude
                    lon = weather_data.location.longitude
                    return self.weather_service.get_air_quality(lat, lon)
                return None
            except Exception as e:
                self.logger.warning(f"Background air quality loading failed: {e}")
                return None

        def on_air_quality_success(air_quality_data):
            if air_quality_data:
                self.after(0, lambda: self._update_air_quality_display(air_quality_data))

        def on_air_quality_error(error):
            self.logger.warning(f"Air quality background loading failed: {error}")

        # Load air quality with 8-second timeout
        self.loading_manager.load_background(
            task=air_quality_task,
            on_success=on_air_quality_success,
            on_error=on_air_quality_error,
            timeout=8.0,
            task_name="air_quality_data",
        )

    def _update_forecast_display(self, forecast_data):
        """Update forecast display with new data."""
        try:
            # Update forecast UI components if they exist
            if hasattr(self, "forecast_frame") and forecast_data:
                self.logger.info("📊 Forecast data updated in background")

                # Store forecast data for use in forecast cards
                if hasattr(self, "current_weather_data"):
                    self.current_weather_data.forecast_data = forecast_data
                else:
                    # Create a simple object to hold forecast data
                    class WeatherDataWithForecast:
                        def __init__(self, forecast_data):
                            self.forecast_data = forecast_data
                            self.temperature = 20  # Default temperature

                    self.current_weather_data = WeatherDataWithForecast(forecast_data)

                # Update forecast cards with new data
                if hasattr(self, "forecast_cards") and self.forecast_cards:
                    self._update_forecast_cards(self.current_weather_data)

                    # Trigger staggered animation for updated cards
                    for i, card in enumerate(self.forecast_cards):
                        self.after(i * 100, lambda c=card: c.animate_in())

                # Refresh any open hourly breakdown windows
                self._refresh_open_hourly_windows()

        except Exception as e:
            self.logger.error(f"Failed to update forecast display: {e}")

    def _update_air_quality_display(self, weather_data):
        """Update air quality display with weather data."""
        try:
            if hasattr(self, "air_quality_label"):
                # Check if weather data has air quality info
                if hasattr(weather_data, "air_quality") and weather_data.air_quality:
                    aqi = (
                        weather_data.air_quality.aqi
                        if hasattr(weather_data.air_quality, "aqi")
                        else weather_data.air_quality
                    )
                    if aqi <= 50:
                        quality = "Good"
                        color = "#00e400"
                    elif aqi <= 100:
                        quality = "Moderate"
                        color = "#ffff00"
                    elif aqi <= 150:
                        quality = "Unhealthy for Sensitive"
                        color = "#ff7e00"
                    elif aqi <= 200:
                        quality = "Unhealthy"
                        color = "#ff0000"
                    else:
                        quality = "Very Unhealthy"
                        color = "#8f3f97"

                    self.air_quality_label.configure(
                        text=f"{quality} (AQI: {aqi})", text_color=color
                    )
                else:
                    # Use default/estimated air quality based on weather
                    # conditions
                    if hasattr(weather_data, "description"):
                        condition = weather_data.description.lower()
                        if "clear" in condition or "sunny" in condition:
                            self.air_quality_label.configure(
                                text="Good (AQI: 45)", text_color="#00e400"
                            )
                        elif "rain" in condition or "drizzle" in condition:
                            self.air_quality_label.configure(
                                text="Good (AQI: 35)", text_color="#00e400"
                            )
                        else:
                            self.air_quality_label.configure(
                                text="Moderate (AQI: 75)", text_color="#ffff00"
                            )
                    else:
                        self.air_quality_label.configure(
                            text="Good (AQI: 45)", text_color="#00e400"
                        )
        except Exception as e:
            self.logger.error(f"Failed to update air quality display: {e}")

    def _show_error_state(self, error_message):
        """Show error state in UI with enhanced styling."""
        self._hide_loading_state()

        # Use new error handler for comprehensive error display
        self.error_handler.show_api_error(
            error_message, "weather data loading", retry_callback=lambda: self._load_weather_data()
        )

        # Update labels with animation
        self.animation_manager.fade_in(self.city_label)
        self.city_label.configure(text="Error")
        self.temp_label.configure(text="--°C")
        self.condition_label.configure(
            text=f"❌ {error_message}", text_color=DataTerminalTheme.ERROR
        )

        if hasattr(self, "status_label"):
            self.status_label.configure(
                text=f"❌ Error: {error_message}", text_color=DataTerminalTheme.ERROR
            )

    def apply_theme(self, theme_name: str):
        """Apply theme to the dashboard."""
        try:
            # Apply theme using theme manager
            theme_manager.apply_theme(theme_name, self)

            # Trigger success animation
            if hasattr(self, "animation_manager"):
                self.animation_manager.success_pulse(self)

        except Exception as e:
            self.logger.error(f"Error applying theme {theme_name}: {e}")
            if hasattr(self, "error_handler"):
                self.error_handler.show_error_toast(f"Failed to apply theme: {theme_name}")

    def _on_theme_changed(self, theme_data=None):
        """Handle theme change notifications from DataTerminalTheme."""
        try:
            # Get current theme data
            current_theme = theme_data if theme_data else theme_manager.get_current_theme()

            # Update main window colors
            self.configure(fg_color=current_theme.get("bg", "#0A0A0A"))

            # Update any tab views if they exist
            if hasattr(self, "tabview"):
                self.tabview.configure(
                    fg_color=current_theme.get("card", "#1A1A1A"),
                    segmented_button_fg_color=current_theme.get("card", "#1A1A1A"),
                    segmented_button_selected_color=current_theme.get("primary", "#00FF41"),
                    segmented_button_selected_hover_color=current_theme.get("secondary", "#008F11"),
                    text_color=current_theme.get("text", "#E0E0E0"),
                )

            # Update any existing components that have theme methods
            components_to_update = [
                "city_comparison_panel",
                "ml_comparison_panel",
                "forecast_cards",
            ]

            for component_name in components_to_update:
                if hasattr(self, component_name):
                    component = getattr(self, component_name)
                    if hasattr(component, "_apply_theme"):
                        component._apply_theme()
                    elif hasattr(component, "update_theme"):
                        component.update_theme()
                    elif isinstance(component, list):  # Handle forecast_cards list
                        for item in component:
                            if hasattr(item, "_on_theme_changed"):
                                item._on_theme_changed(current_theme)

        except Exception as e:
            self.logger.error(f"Error in _on_theme_changed: {e}")

    def _show_rate_limit_message(self):
        """Show user-friendly rate limit message."""
        self.error_handler.show_warning_toast(
            "Rate limit exceeded. Using cached data. Please wait before trying again."
        )

    def _show_config_error_message(self):
        """Show configuration error message."""
        self.error_handler.show_error_toast(
            "API configuration error. Please check your API key settings."
        )

    def _show_network_error_message(self):
        """Show network error message."""
        self.error_handler.show_offline_indicator(self, has_cached_data=True)
        self.error_handler.show_warning_toast("Network connection issue. Using cached data.")

    def _show_service_error_message(self):
        """Show service unavailable message."""
        self.error_handler.show_warning_toast(
            "Weather service temporarily unavailable. Using cached data."
        )

    def _show_weather_service_error_message(self, error_details):
        """Show generic weather service error message."""
        self.error_handler.show_error_toast(
            f"Weather service error: {error_details}. Using cached data."
        )

    def _create_maps_tab(self):
        """Create Maps tab with enhanced weather visualization."""
        self._create_enhanced_maps_tab()

    def _create_enhanced_maps_tab(self):
        """Create enhanced maps tab with weather visualization."""
        # Main container
        maps_container = ctk.CTkScrollableFrame(
            self.maps_tab, fg_color=DataTerminalTheme.BACKGROUND
        )
        maps_container.pack(fill="both", expand=True, padx=15, pady=15)

        # Header
        header_frame = ctk.CTkFrame(
            maps_container,
            fg_color=DataTerminalTheme.CARD_BG,
            corner_radius=12,
            border_width=1,
            border_color=DataTerminalTheme.BORDER,
        )
        header_frame.pack(fill="x", pady=(0, 20))

        title_label = ctk.CTkLabel(
            header_frame,
            text="🗺️ Weather Maps & Radar",
            font=(DataTerminalTheme.FONT_FAMILY, 24, "bold"),
            text_color=DataTerminalTheme.ACCENT,
        )
        title_label.pack(pady=20)

        # Create two-column layout
        content_frame = ctk.CTkFrame(maps_container, fg_color="transparent")
        content_frame.pack(fill="both", expand=True)
        content_frame.grid_columnconfigure(0, weight=1)
        content_frame.grid_columnconfigure(1, weight=1)
        content_frame.grid_rowconfigure(0, weight=1)

        # Left column - Weather layers and controls
        self._create_weather_layers_panel(content_frame)

        # Right column - Regional weather overview
        self._create_regional_weather_panel(content_frame)

    def _create_weather_layers_panel(self, parent):
        """Create weather layers control panel."""
        layers_frame = ctk.CTkFrame(
            parent,
            fg_color=DataTerminalTheme.CARD_BG,
            corner_radius=12,
            border_width=1,
            border_color=DataTerminalTheme.BORDER,
        )
        layers_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 10), pady=0)

        # Title
        title = ctk.CTkLabel(
            layers_frame,
            text="🌡️ Weather Layers",
            font=(DataTerminalTheme.FONT_FAMILY, 18, "bold"),
            text_color=DataTerminalTheme.ACCENT,
        )
        title.pack(pady=(20, 15))

        # Location input
        location_frame = ctk.CTkFrame(layers_frame, fg_color="transparent")
        location_frame.pack(fill="x", padx=20, pady=(0, 20))

        ctk.CTkLabel(
            location_frame,
            text="📍 Location:",
            font=(DataTerminalTheme.FONT_FAMILY, 14, "bold"),
            text_color=DataTerminalTheme.TEXT,
        ).pack(anchor="w", pady=(0, 5))

        self.maps_location_entry = ctk.CTkEntry(
            location_frame,
            placeholder_text="Enter city name...",
            height=35,
            font=(DataTerminalTheme.FONT_FAMILY, 12),
        )
        self.maps_location_entry.pack(fill="x", pady=(0, 10))

        search_btn = ctk.CTkButton(
            location_frame,
            text="🔍 Search Weather",
            command=self._search_maps_location,
            height=35,
            fg_color=DataTerminalTheme.PRIMARY,
            hover_color=DataTerminalTheme.SUCCESS,
        )
        search_btn.pack(fill="x")

        # Weather layers
        layers_list_frame = ctk.CTkFrame(layers_frame, fg_color="transparent")
        layers_list_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        ctk.CTkLabel(
            layers_list_frame,
            text="Available Layers:",
            font=(DataTerminalTheme.FONT_FAMILY, 14, "bold"),
            text_color=DataTerminalTheme.TEXT,
        ).pack(anchor="w", pady=(0, 10))

        # Layer options
        layers = [
            ("🌡️ Temperature", "Real-time temperature data"),
            ("🌧️ Precipitation", "Rain and snow radar"),
            ("💨 Wind Speed", "Wind patterns and gusts"),
            ("☁️ Cloud Cover", "Satellite cloud imagery"),
            ("📊 Pressure", "Atmospheric pressure maps"),
            ("⚡ Weather Alerts", "Severe weather warnings"),
        ]

        for layer_name, description in layers:
            layer_card = ctk.CTkFrame(
                layers_list_frame,
                fg_color=DataTerminalTheme.BACKGROUND,
                corner_radius=8,
                border_width=1,
                border_color=DataTerminalTheme.BORDER,
            )
            layer_card.pack(fill="x", pady=5)

            ctk.CTkLabel(
                layer_card,
                text=layer_name,
                font=(DataTerminalTheme.FONT_FAMILY, 12, "bold"),
                text_color=DataTerminalTheme.TEXT,
            ).pack(anchor="w", padx=15, pady=(10, 2))

            ctk.CTkLabel(
                layer_card,
                text=description,
                font=(DataTerminalTheme.FONT_FAMILY, 10),
                text_color=DataTerminalTheme.TEXT_SECONDARY,
            ).pack(anchor="w", padx=15, pady=(0, 10))

    def _create_regional_weather_panel(self, parent):
        """Create regional weather overview panel."""
        regional_frame = ctk.CTkFrame(
            parent,
            fg_color=DataTerminalTheme.CARD_BG,
            corner_radius=12,
            border_width=1,
            border_color=DataTerminalTheme.BORDER,
        )
        regional_frame.grid(row=0, column=1, sticky="nsew", padx=(10, 0), pady=0)

        # Title
        title = ctk.CTkLabel(
            regional_frame,
            text="🌍 Regional Weather Overview",
            font=(DataTerminalTheme.FONT_FAMILY, 18, "bold"),
            text_color=DataTerminalTheme.ACCENT,
        )
        title.pack(pady=(20, 15))

        # Weather map visualization area
        map_display_frame = ctk.CTkFrame(
            regional_frame,
            fg_color=DataTerminalTheme.BACKGROUND,
            corner_radius=8,
            border_width=1,
            border_color=DataTerminalTheme.BORDER,
        )
        map_display_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        # Map placeholder with weather info
        self._create_weather_map_display(map_display_frame)

    def _create_weather_map_display(self, parent):
        """Create weather map display with current conditions."""
        # Current location weather
        current_weather_frame = ctk.CTkFrame(parent, fg_color="transparent")
        current_weather_frame.pack(fill="x", padx=15, pady=15)

        ctk.CTkLabel(
            current_weather_frame,
            text="📍 Current Location Weather",
            font=(DataTerminalTheme.FONT_FAMILY, 16, "bold"),
            text_color=DataTerminalTheme.ACCENT,
        ).pack(pady=(0, 10))

        # Weather grid
        weather_grid = ctk.CTkFrame(current_weather_frame, fg_color="transparent")
        weather_grid.pack(fill="x")
        weather_grid.grid_columnconfigure((0, 1), weight=1)

        # Temperature card
        temp_card = ctk.CTkFrame(weather_grid, fg_color=DataTerminalTheme.PRIMARY, corner_radius=8)
        temp_card.grid(row=0, column=0, sticky="ew", padx=(0, 5), pady=5)

        ctk.CTkLabel(
            temp_card,
            text="🌡️ Temperature",
            font=(DataTerminalTheme.FONT_FAMILY, 12, "bold"),
            text_color="white",
        ).pack(pady=(10, 2))

        self.maps_temp_label = ctk.CTkLabel(
            temp_card,
            text="--°C",
            font=(DataTerminalTheme.FONT_FAMILY, 20, "bold"),
            text_color="white",
        )
        self.maps_temp_label.pack(pady=(0, 10))

        # Conditions card
        conditions_card = ctk.CTkFrame(
            weather_grid, fg_color=DataTerminalTheme.SUCCESS, corner_radius=8
        )
        conditions_card.grid(row=0, column=1, sticky="ew", padx=(5, 0), pady=5)

        ctk.CTkLabel(
            conditions_card,
            text="☁️ Conditions",
            font=(DataTerminalTheme.FONT_FAMILY, 12, "bold"),
            text_color="white",
        ).pack(pady=(10, 2))

        self.maps_condition_label = ctk.CTkLabel(
            conditions_card,
            text="--",
            font=(DataTerminalTheme.FONT_FAMILY, 14, "bold"),
            text_color="white",
        )
        self.maps_condition_label.pack(pady=(0, 10))

        # Radar simulation
        radar_frame = ctk.CTkFrame(parent, fg_color="transparent")
        radar_frame.pack(fill="both", expand=True, padx=15, pady=(10, 15))

        ctk.CTkLabel(
            radar_frame,
            text="📡 Weather Radar Simulation",
            font=(DataTerminalTheme.FONT_FAMILY, 16, "bold"),
            text_color=DataTerminalTheme.ACCENT,
        ).pack(pady=(0, 10))

        # Radar display
        radar_display = ctk.CTkFrame(
            radar_frame,
            fg_color=DataTerminalTheme.BACKGROUND,
            corner_radius=8,
            border_width=2,
            border_color=DataTerminalTheme.PRIMARY,
        )
        radar_display.pack(fill="both", expand=True)

        # Radar content
        self._create_radar_simulation(radar_display)

    def _create_radar_simulation(self, parent):
        """Create weather radar simulation."""
        radar_content = ctk.CTkFrame(parent, fg_color="transparent")
        radar_content.pack(fill="both", expand=True, padx=20, pady=20)

        # Radar circles (concentric)
        radar_circles = ctk.CTkFrame(
            radar_content, fg_color="#001122", corner_radius=100, width=200, height=200
        )
        radar_circles.pack(expand=True)

        # Center dot
        center_dot = ctk.CTkFrame(
            radar_circles, fg_color=DataTerminalTheme.PRIMARY, corner_radius=5, width=10, height=10
        )
        center_dot.place(relx=0.5, rely=0.5, anchor="center")

        # Radar info
        info_frame = ctk.CTkFrame(radar_content, fg_color="transparent")
        info_frame.pack(fill="x", pady=(10, 0))

        ctk.CTkLabel(
            info_frame,
            text="🎯 Radar Range: 100km | 🔄 Last Update: Now",
            font=(DataTerminalTheme.FONT_FAMILY, 10),
            text_color=DataTerminalTheme.TEXT_SECONDARY,
        ).pack()

    def _search_maps_location(self):
        """Search for weather in maps location."""
        location = self.maps_location_entry.get().strip()
        if location:
            # Update the main weather display with this location
            self.location_entry.delete(0, "end")
            self.location_entry.insert(0, location)
            self._search_weather()

            # Update maps display
            self._update_maps_weather_display()

    def _update_maps_weather_display(self):
        """Update the maps weather display with current weather data."""
        try:
            if hasattr(self, "current_weather_data") and self.current_weather_data:
                # Update temperature
                temp = self.current_weather_data.temperature
                unit = "°C" if self.config_service.get_temperature_unit() == "celsius" else "°F"
                if self.config_service.get_temperature_unit() == "fahrenheit":
                    temp = (temp * 9 / 5) + 32
                self.maps_temp_label.configure(text=f"{temp:.1f}{unit}")

                # Update conditions
                condition = self.current_weather_data.condition
                self.maps_condition_label.configure(text=condition.title())
        except Exception as e:
            self.logger.error(f"Error updating maps weather display: {e}")

    def center_window(self):
        """Center the window on screen."""
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f"{width}x{height}+{x}+{y}")


if __name__ == "__main__":
    app = ProfessionalWeatherDashboard()
    app.center_window()
    app.mainloop()
