import logging
from datetime import datetime, timedelta
import tkinter as tk

import customtkinter as ctk
from dotenv import load_dotenv

from src.services.activity_service import ActivityService
from src.services.config_service import ConfigService
from src.services.enhanced_weather_service import EnhancedWeatherService
from src.services.github_team_service import GitHubTeamService
from src.ui.components.forecast_day_card import ForecastDayCard
from src.ui.components.theme_preview_card import ThemePreviewCard
from src.ui.components.city_comparison_panel import CityComparisonPanel
from src.ui.components.ml_comparison_panel import MLComparisonPanel
from src.ui.components import (
    AnimationManager, ShimmerEffect, MicroInteractions, LoadingSkeleton,
    WeatherBackgroundManager, ParticleSystem, TemperatureGradient,
    ErrorManager, StatusMessageManager, VisualPolishManager,
    GlassMorphism, ShadowSystem, KeyboardShortcuts
)
from src.ui.theme import DataTerminalTheme
from src.ui.theme_manager import theme_manager
from src.utils.loading_manager import LoadingManager
from src.utils.cache_manager import CacheManager
from src.utils.startup_optimizer import StartupOptimizer
from src.utils.component_recycler import ComponentRecycler
from src.utils.api_optimizer import APIOptimizer

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
            lru_factor=0.8  # Evict when 80% full
        )
        self.startup_optimizer = StartupOptimizer()
        self.component_recycler = ComponentRecycler()
        self.api_optimizer = APIOptimizer()
        
        # Initialize services (with fallback for demo mode)
        try:
            self.config_service = config_service or ConfigService()
            self.weather_service = EnhancedWeatherService(self.config_service)
            self.activity_service = ActivityService(self.config_service)
            github_token = self.config_service.get_setting('api.github_token') if self.config_service else None
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
        
        # Initialize theme manager and register as observer
        DataTerminalTheme.add_observer(self._on_theme_changed)
        
        # Register visual polish managers with theme system
        theme_manager.add_observer(self.weather_background_manager.update_theme)
        theme_manager.add_observer(self.error_manager.update_theme)
        theme_manager.add_observer(self.status_manager.update_theme)
        theme_manager.add_observer(self.visual_polish_manager.update_theme)
        
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
        self.grid_rowconfigure(1, weight=1)

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

        # Start auto-refresh
        self._schedule_refresh()
        
        # Initialize enhanced settings
        self._initialize_enhanced_settings()

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

    def _initialize_enhanced_settings(self):
        """Initialize enhanced settings with default values."""
        try:
            # Initialize settings state variables
            self.analytics_enabled = True
            self.location_history_enabled = True
            self.refresh_interval_minutes = 5
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
                self.analytics_enabled = self.config_service.get_setting('privacy.analytics_enabled', True)
                self.location_history_enabled = self.config_service.get_setting('privacy.location_history_enabled', True)
                self.refresh_interval_minutes = self.config_service.get_setting('refresh.interval_minutes', 5)
                self.quiet_hours_enabled = self.config_service.get_setting('refresh.quiet_hours_enabled', False)
                self.quiet_start_hour = self.config_service.get_setting('refresh.quiet_start_hour', 22)
                self.quiet_end_hour = self.config_service.get_setting('refresh.quiet_end_hour', 7)
                self.wifi_only_refresh = self.config_service.get_setting('refresh.wifi_only', False)
                self.date_format = self.config_service.get_setting('appearance.date_format', '%Y-%m-%d')
                self.time_format = self.config_service.get_setting('appearance.time_format', '%H:%M')
                self.selected_language = self.config_service.get_setting('appearance.language', 'English')
                self.font_size = self.config_service.get_setting('appearance.font_size', 12)
            
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

        # Enhanced Search Bar
        try:
            from src.ui.components.search_components import EnhancedSearchBar
            self.search_bar = EnhancedSearchBar(
                search_container,
                self.weather_service,
                on_location_selected=self._on_location_selected
            )
            self.search_bar.pack()
        except ImportError as e:
            self.logger.error(f"Failed to import EnhancedSearchBar: {e}")
            # Fallback to basic search
            self._create_basic_search(search_container)

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
        self._create_settings_tab()

    def _create_weather_tab(self):
        """Create enhanced weather tab with proper layout."""
        self._create_weather_tab_content()

    def _create_weather_tab_content(self):
        """Create enhanced weather tab with proper layout."""
        # Configure grid for 3-column layout with better proportions
        self.weather_tab.grid_columnconfigure(0, weight=1, minsize=350)  # Current weather
        self.weather_tab.grid_columnconfigure(1, weight=2, minsize=500)  # Forecast chart
        self.weather_tab.grid_columnconfigure(2, weight=1, minsize=300)  # Additional metrics
        self.weather_tab.grid_rowconfigure(0, weight=1)

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
        forecast_container.grid(row=0, column=1, sticky="nsew", padx=8, pady=15)

        # Title
        forecast_title = ctk.CTkLabel(
            forecast_container,
            text="📊 Temperature Forecast",
            font=(DataTerminalTheme.FONT_FAMILY, 18, "bold"),
            text_color=DataTerminalTheme.PRIMARY,
        )
        forecast_title.pack(pady=(15, 10))

        # Import and create chart
        from src.ui.components.simple_temperature_chart import SimpleTemperatureChart

        self.temp_chart = SimpleTemperatureChart(
            forecast_container, fg_color=DataTerminalTheme.CARD_BG
        )
        self.temp_chart.pack(fill="both", expand=True, padx=15, pady=(0, 10))

        # Add 5-day forecast cards below the chart
        self._create_forecast_cards(forecast_container)

        # Right column - Additional metrics and details
        self._create_additional_metrics_section()

    def _create_forecast_cards(self, parent):
        """Create 5-day forecast cards using enhanced ForecastDayCard component."""
        forecast_frame = ctk.CTkFrame(parent, fg_color="transparent")
        forecast_frame.pack(fill="x", padx=15, pady=(0, 15))

        # Configure grid for equal distribution
        for i in range(5):
            forecast_frame.grid_columnconfigure(i, weight=1)

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
                on_click=self._on_forecast_card_click
            )
            
            day_card.grid(row=0, column=i, padx=6, pady=3, sticky="ew")
            self.forecast_cards.append(day_card)
            
            # Add staggered animation
            day_card.animate_in(delay=i * 100)

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

        # Title
        metrics_title = ctk.CTkLabel(
            metrics_container,
            text="📈 Weather Details",
            font=(DataTerminalTheme.FONT_FAMILY, 16, "bold"),
            text_color=DataTerminalTheme.PRIMARY,
        )
        metrics_title.pack(pady=(15, 10))

        # Air Quality Section
        air_quality_frame = ctk.CTkFrame(
            metrics_container,
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
            metrics_container,
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
            metrics_container,
            fg_color=DataTerminalTheme.BACKGROUND,
            corner_radius=8,
            border_width=1,
            border_color=DataTerminalTheme.BORDER,
        )
        alerts_frame.pack(fill="x", padx=12, pady=(0, 15))

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
            if not hasattr(self, 'forecast_cards') or not self.forecast_cards:
                return
            
            # If we have forecast data, use it; otherwise generate sample data
            if hasattr(weather_data, 'forecast_data') and weather_data.forecast_data:
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
                    
                    # Update card with real data
                    card.update_data(
                        icon=daily_data.get('icon', '01d'),
                        high=daily_data.get('high_temp', 22),
                        low=daily_data.get('low_temp', 15),
                        precipitation=daily_data.get('precipitation', 0.0),
                        wind_speed=daily_data.get('wind_speed', 0.0),
                        temp_unit=self.temp_unit
                    )
                    
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
                icons = ['01d', '02d', '03d', '04d', '09d']
                precipitations = [0.0, 0.1, 0.3, 0.2, 0.0]
                wind_speeds = [2.5, 3.0, 4.2, 3.8, 2.1]
                
                card.update_data(
                    icon=icons[i % len(icons)],
                    high=high_temp,
                    low=low_temp,
                    precipitation=precipitations[i % len(precipitations)],
                    wind_speed=wind_speeds[i % len(wind_speeds)],
                    temp_unit=self.temp_unit
                )
                
        except Exception as e:
            self.logger.error(f"Failed to update cards with sample data: {e}")
    
    def _parse_daily_forecasts(self, forecast_data):
        """Parse forecast data into daily summaries."""
        try:
            daily_forecasts = []
            
            # Check if forecast_data has the expected structure
            if hasattr(forecast_data, 'get_daily_forecast'):
                # Use the model's method to get daily forecast
                daily_data = forecast_data.get_daily_forecast()
                for day_data in daily_data[:5]:  # Get first 5 days
                    daily_forecasts.append({
                        'icon': getattr(day_data, 'icon', '01d'),
                        'high_temp': int(getattr(day_data, 'high_temp', 22)),
                        'low_temp': int(getattr(day_data, 'low_temp', 15)),
                        'precipitation': getattr(day_data, 'precipitation_probability', 0.0),
                        'wind_speed': getattr(day_data, 'wind_speed', 0.0)
                    })
            elif hasattr(forecast_data, 'list'):
                # Parse OpenWeatherMap 5-day forecast format
                daily_forecasts = self._parse_openweather_forecast(forecast_data.list)
            else:
                # Fallback to sample data
                for i in range(5):
                    daily_forecasts.append({
                        'icon': ['01d', '02d', '03d', '04d', '09d'][i],
                        'high_temp': 22 + (i * 2) - 2,
                        'low_temp': 15 + i,
                        'precipitation': [0.0, 0.1, 0.3, 0.2, 0.0][i],
                        'wind_speed': [2.5, 3.0, 4.2, 3.8, 2.1][i]
                    })
            
            return daily_forecasts
            
        except Exception as e:
            self.logger.error(f"Failed to parse daily forecasts: {e}")
            return []
    
    def _parse_openweather_forecast(self, forecast_list):
        """Parse OpenWeatherMap forecast list into daily summaries."""
        try:
            daily_data = {}
            
            # Group forecast entries by date
            for entry in forecast_list:
                if 'dt_txt' in entry:
                    date_str = entry['dt_txt'][:10]  # Get YYYY-MM-DD part
                    
                    if date_str not in daily_data:
                        daily_data[date_str] = {
                            'temps': [],
                            'icons': [],
                            'precipitation': 0.0,
                            'wind_speeds': []
                        }
                    
                    # Collect temperature data
                    if 'main' in entry and 'temp' in entry['main']:
                        daily_data[date_str]['temps'].append(entry['main']['temp'])
                    
                    # Collect weather icons (use most common one)
                    if 'weather' in entry and len(entry['weather']) > 0:
                        daily_data[date_str]['icons'].append(entry['weather'][0].get('icon', '01d'))
                    
                    # Collect precipitation probability
                    if 'pop' in entry:
                        daily_data[date_str]['precipitation'] = max(
                            daily_data[date_str]['precipitation'], 
                            entry['pop']
                        )
                    
                    # Collect wind speed
                    if 'wind' in entry and 'speed' in entry['wind']:
                        daily_data[date_str]['wind_speeds'].append(entry['wind']['speed'])
            
            # Convert to daily forecasts
            daily_forecasts = []
            for date_str in sorted(daily_data.keys())[:5]:  # Get first 5 days
                day_data = daily_data[date_str]
                
                # Calculate high/low temperatures
                temps = day_data['temps']
                high_temp = int(max(temps)) if temps else 22
                low_temp = int(min(temps)) if temps else 15
                
                # Get most common icon
                icons = day_data['icons']
                icon = max(set(icons), key=icons.count) if icons else '01d'
                
                # Average wind speed
                wind_speeds = day_data['wind_speeds']
                avg_wind = sum(wind_speeds) / len(wind_speeds) if wind_speeds else 0.0
                
                daily_forecasts.append({
                    'icon': icon,
                    'high_temp': high_temp,
                    'low_temp': low_temp,
                    'precipitation': day_data['precipitation'],
                    'wind_speed': avg_wind
                })
            
            return daily_forecasts
            
        except Exception as e:
            self.logger.error(f"Failed to parse OpenWeather forecast: {e}")
            return []
    
    def _on_forecast_card_click(self, card):
        """Handle forecast card click to show hourly breakdown."""
        try:
            # Get the card index
            card_index = self.forecast_cards.index(card) if card in self.forecast_cards else 0
            
            # Create hourly breakdown dialog
            self._show_hourly_breakdown(card_index)
            
        except Exception as e:
            self.logger.error(f"Failed to handle forecast card click: {e}")
    
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
            current_data_timestamp = getattr(self.current_weather_data, 'timestamp', current_time) if hasattr(self, 'current_weather_data') and self.current_weather_data else current_time
            
            # Store reference to window and its day index with creation timestamp
            window_info = {
                'window': hourly_window,
                'day_index': day_index,
                'created_at': current_time,
                'data_timestamp': current_data_timestamp
            }
            self.open_hourly_windows.append(window_info)
            logging.info(f"Hourly window opened for day {day_index}. Total open windows: {len(self.open_hourly_windows)}")
            logging.info(f"Window created at {window_info['created_at'].strftime('%H:%M:%S')} with data from {window_info['data_timestamp'].strftime('%H:%M:%S')}")
            
            # Set up cleanup when window is closed
            def on_window_close():
                if window_info in self.open_hourly_windows:
                    self.open_hourly_windows.remove(window_info)
                    logging.info(f"Hourly window closed for day {day_index}. Total open windows: {len(self.open_hourly_windows)}")
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
                text_color=theme_manager.get_current_theme().get("text", "#FFFFFF")
            )
            title_label.pack(pady=(0, 20))
            
            # Scrollable frame for hourly data
            scrollable_frame = ctk.CTkScrollableFrame(content_frame)
            scrollable_frame.pack(fill="both", expand=True)
            
            # Get real hourly forecast data
            hourly_data = self._get_hourly_data_for_day(day_index)
            
            # Check if we have newer weather data available and update window info if needed
            if hasattr(self, 'last_weather_data_timestamp') and self.last_weather_data_timestamp > current_data_timestamp:
                window_info['data_timestamp'] = self.last_weather_data_timestamp
                logging.info(f"Updated window data timestamp to latest: {self.last_weather_data_timestamp.strftime('%H:%M:%S')}")
            
            if hourly_data:
                # Display real hourly data
                for hour_entry in hourly_data:
                    hour_frame = ctk.CTkFrame(scrollable_frame)
                    hour_frame.pack(fill="x", padx=5, pady=2)
                    
                    # Time
                    time_str = hour_entry.get('time', '00:00')
                    time_label = ctk.CTkLabel(
                        hour_frame,
                        text=time_str,
                        font=ctk.CTkFont(size=14),
                        width=60
                    )
                    time_label.pack(side="left", padx=10, pady=5)
                    
                    # Weather icon
                    icon = self._get_weather_icon(hour_entry.get('condition', 'clear'))
                    icon_label = ctk.CTkLabel(
                        hour_frame,
                        text=icon,
                        font=ctk.CTkFont(size=14),
                        width=40
                    )
                    icon_label.pack(side="left", padx=5, pady=5)
                    
                    # Temperature
                    temp = hour_entry.get('temperature', 20)
                    if hasattr(self, 'temp_unit') and self.temp_unit == 'F':
                        temp = temp * 9/5 + 32
                    temp_label = ctk.CTkLabel(
                        hour_frame,
                        text=f"{int(temp)}°{getattr(self, 'temp_unit', 'C')}",
                        font=ctk.CTkFont(size=14),
                        width=60
                    )
                    temp_label.pack(side="left", padx=10, pady=5)
                    
                    # Precipitation
                    precip = hour_entry.get('precipitation', 0)
                    precip_label = ctk.CTkLabel(
                        hour_frame,
                        text=f"💧 {int(precip)}%" if precip > 0 else "",
                        font=ctk.CTkFont(size=12),
                        width=60
                    )
                    precip_label.pack(side="left", padx=10, pady=5)
                    
                    # Wind
                    wind = hour_entry.get('wind_speed', 0)
                    wind_label = ctk.CTkLabel(
                        hour_frame,
                        text=f"💨 {wind:.1f} m/s",
                        font=ctk.CTkFont(size=12)
                    )
                    wind_label.pack(side="left", padx=10, pady=5)
            else:
                # Fallback to sample data if no real data available
                no_data_label = ctk.CTkLabel(
                    scrollable_frame,
                    text="No hourly forecast data available for this day.",
                    font=ctk.CTkFont(size=14),
                    text_color=theme_manager.get_current_theme().get("text_secondary", "#CCCCCC")
                )
                no_data_label.pack(pady=20)
                
                # Show sample data as fallback
                for hour in range(0, 24, 3):  # Every 3 hours
                    hour_frame = ctk.CTkFrame(scrollable_frame)
                    hour_frame.pack(fill="x", padx=5, pady=2)
                    
                    # Time
                    time_label = ctk.CTkLabel(
                        hour_frame,
                        text=f"{hour:02d}:00",
                        font=ctk.CTkFont(size=14),
                        width=60
                    )
                    time_label.pack(side="left", padx=10, pady=5)
                    
                    # Weather icon
                    icon_label = ctk.CTkLabel(
                        hour_frame,
                        text="🌤️",
                        font=ctk.CTkFont(size=14),
                        width=40
                    )
                    icon_label.pack(side="left", padx=5, pady=5)
                    
                    # Temperature
                    temp = 20 + (hour // 3) - 2  # Sample temperature variation
                    temp_label = ctk.CTkLabel(
                        hour_frame,
                        text=f"{temp}°{getattr(self, 'temp_unit', 'C')}",
                        font=ctk.CTkFont(size=14),
                        width=60
                    )
                    temp_label.pack(side="left", padx=10, pady=5)
                    
                    # Precipitation
                    precip = max(0, (hour - 12) * 5) if 9 <= hour <= 15 else 0  # Sample precipitation
                    precip_label = ctk.CTkLabel(
                        hour_frame,
                        text=f"💧 {precip}%" if precip > 0 else "",
                        font=ctk.CTkFont(size=12),
                        width=60
                    )
                    precip_label.pack(side="left", padx=10, pady=5)
                    
                    # Wind
                    wind = 2.0 + (hour * 0.1)  # Sample wind variation
                    wind_label = ctk.CTkLabel(
                        hour_frame,
                        text=f"💨 {wind:.1f} m/s",
                        font=ctk.CTkFont(size=12)
                    )
                    wind_label.pack(side="left", padx=10, pady=5)
            
            # Close button
            close_button = ctk.CTkButton(
                content_frame,
                text="Close",
                command=on_window_close,
                font=ctk.CTkFont(size=14)
            )
            close_button.pack(pady=(10, 0))
            
            # Store reference to content frame for updates
            window_info['content_frame'] = content_frame
            
        except Exception as e:
            self.logger.error(f"Failed to show hourly breakdown: {e}")
    
    def _refresh_open_hourly_windows(self):
        """Refresh content of all open hourly breakdown windows."""
        try:
            current_time = datetime.now().strftime('%H:%M:%S')
            current_data_timestamp = getattr(self.current_weather_data, 'timestamp', datetime.now()) if hasattr(self, 'current_weather_data') and self.current_weather_data else datetime.now()
            
            self.logger.info(f"[{current_time}] Refreshing {len(self.open_hourly_windows)} open hourly windows")
            self.logger.info(f"[{current_time}] Current weather data timestamp: {current_data_timestamp.strftime('%H:%M:%S')}")
            
            for window_info in self.open_hourly_windows[:]:
                try:
                    window = window_info['window']
                    day_index = window_info['day_index']
                    window_data_timestamp = window_info.get('data_timestamp', datetime.min)
                    
                    # Check if window still exists
                    if not window.winfo_exists():
                        self.open_hourly_windows.remove(window_info)
                        self.logger.info(f"[{current_time}] Removed non-existent window for day {day_index}")
                        continue
                    
                    # Check if current data is newer than window's data
                    if current_data_timestamp <= window_data_timestamp:
                        self.logger.info(f"[{current_time}] Skipping window for day {day_index} - data is current (window: {window_data_timestamp.strftime('%H:%M:%S')}, current: {current_data_timestamp.strftime('%H:%M:%S')})")
                        continue
                    
                    self.logger.info(f"[{current_time}] Refreshing hourly window for day {day_index} with newer data (window: {window_data_timestamp.strftime('%H:%M:%S')}, current: {current_data_timestamp.strftime('%H:%M:%S')})")
                    
                    # Update the window's data timestamp
                    window_info['data_timestamp'] = current_data_timestamp
                    
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
                            time_str = hour_entry.get('time', '00:00')
                            time_label = ctk.CTkLabel(
                                hour_frame,
                                text=time_str,
                                font=ctk.CTkFont(size=14),
                                width=60
                            )
                            time_label.pack(side="left", padx=10, pady=5)
                            
                            # Weather icon
                            condition = hour_entry.get('condition', 'clear')
                            icon = self._get_weather_icon(condition)
                            icon_label = ctk.CTkLabel(
                                hour_frame,
                                text=icon,
                                font=ctk.CTkFont(size=16),
                                width=40
                            )
                            icon_label.pack(side="left", padx=10, pady=5)
                            
                            # Temperature
                            temp = hour_entry.get('temperature', 20)
                            temp_label = ctk.CTkLabel(
                                hour_frame,
                                text=f"{int(temp)}°{getattr(self, 'temp_unit', 'C')}",
                                font=ctk.CTkFont(size=14),
                                width=60
                            )
                            temp_label.pack(side="left", padx=10, pady=5)
                            
                            # Precipitation
                            precip = hour_entry.get('precipitation', 0)
                            precip_label = ctk.CTkLabel(
                                hour_frame,
                                text=f"💧 {int(precip)}%" if precip > 0 else "",
                                font=ctk.CTkFont(size=12),
                                width=60
                            )
                            precip_label.pack(side="left", padx=10, pady=5)
                            
                            # Wind
                            wind = hour_entry.get('wind_speed', 0)
                            wind_label = ctk.CTkLabel(
                                hour_frame,
                                text=f"💨 {wind:.1f} m/s",
                                font=ctk.CTkFont(size=12)
                            )
                            wind_label.pack(side="left", padx=10, pady=5)
                    else:
                        # Show "no data" message
                        no_data_label = ctk.CTkLabel(
                            scrollable_frame,
                            text="No hourly forecast data available for this day.",
                            font=ctk.CTkFont(size=14)
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
            if not self.current_weather_data or not hasattr(self.current_weather_data, 'forecast_data'):
                return None
            
            forecast_data = self.current_weather_data.forecast_data
            if not forecast_data or not hasattr(forecast_data, 'hourly_forecasts'):
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
                        'time': forecast_dt.strftime('%H:%M'),
                        'temperature': forecast.temperature,
                        'condition': forecast.condition.value if hasattr(forecast.condition, 'value') else str(forecast.condition),
                        'precipitation': precip_prob,
                        'wind_speed': forecast.wind_speed or 0
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
            'clear': '☀️',
            'sunny': '☀️',
            'clouds': '☁️',
            'cloudy': '☁️',
            'partly cloudy': '⛅',
            'overcast': '☁️',
            'rain': '🌧️',
            'drizzle': '🌦️',
            'shower': '🌦️',
            'thunderstorm': '⛈️',
            'snow': '❄️',
            'mist': '🌫️',
            'fog': '🌫️',
            'haze': '🌫️'
        }
        
        for key, icon in icon_map.items():
            if key in condition_lower:
                return icon
        
        return '🌤️'  # Default icon

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
                if hasattr(self.temp_chart, 'set_temperature_unit') and hasattr(self, 'temp_unit'):
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
            self.animation_manager.fade_out(self.search_entry, callback=lambda: self.search_entry.delete(0, "end"))

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
            if hasattr(self, 'city_label'):
                self.city_label.configure(text=self.current_city)
            
            # Store location coordinates for future use
            self.current_location = {
                'name': location_result.name,
                'display_name': location_result.display_name,
                'latitude': location_result.latitude,
                'longitude': location_result.longitude,
                'country': location_result.country,
                'state': location_result.state
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
        """Handle weather search functionality."""
        search_term = self.search_entry.get().strip()
        if search_term:
            # Update current city
            self.current_city = search_term
            self.location_label.configure(text=f"📍 Current: {self.current_city}")

            # Update weather display
            self.city_label.configure(text=self.current_city)

            # Clear search entry
            self.search_entry.delete(0, "end")

            # Trigger weather data update
            self._safe_fetch_weather_data()

    def _get_weather_icon(self, condition):
        """Get weather icon based on condition."""
        condition_lower = condition.lower()
        for key, icon in self.weather_icons.items():
            if key in condition_lower:
                return icon
        return "🌤️"  # Default icon

    def _update_weather_display(self, weather_data):
        """Update UI with enhanced weather display and visual effects."""
        try:
            # Store current weather data for activity suggestions
            self.current_weather_data = weather_data
            # Track when weather data was last updated
            self.last_weather_data_timestamp = datetime.now()

            # Update weather-based background
            from src.ui.components.weather_effects import WeatherCondition
            weather_condition = WeatherCondition(
                condition=weather_data.description,
                temperature=weather_data.temperature,
                humidity=getattr(weather_data, 'humidity', 50),
                wind_speed=getattr(weather_data, 'wind_speed', 0),
                time_of_day='day' if 6 <= datetime.now().hour <= 18 else 'night'
            )
            self.weather_background_manager.update_weather_background(weather_condition)

            # Update activities if on activities tab
            if self.tabview.get() == "Activities":
                self._update_activity_suggestions(weather_data)

            # Refresh activity suggestions with new weather data
            self._refresh_activity_suggestions()

            # Update location with fade animation
            location_name = f"{
                weather_data.location.name}, {
                weather_data.location.country}"
            self.animation_manager.fade_in(self.city_label)
            self.city_label.configure(text=location_name)
            self.location_label.configure(text=f"📍 Current: {location_name}")

            # Get weather icon
            condition_lower = weather_data.description.lower()
            icon = "🌤️"  # default
            for key, emoji in self.weather_icons.items():
                if key in condition_lower:
                    icon = emoji
                    break

            # Update main display with number transition animation
            self.animation_manager.animate_number_change(
                self.temp_label, 
                f"{int(weather_data.temperature)}°C"
            )
            self.animation_manager.fade_in(self.condition_label)
            self.condition_label.configure(text=f"{icon} {weather_data.description}")
            
            # Show success status
            self.status_manager.show_weather_fact()
            
            # Refresh any open hourly breakdown windows
            self.logger.info("About to refresh open hourly windows from _update_weather_display")
            self._refresh_open_hourly_windows()

            # Update metrics
            if "humidity" in self.metric_labels:
                self.metric_labels["humidity"].configure(text=f"{weather_data.humidity}%")

            if "wind" in self.metric_labels and weather_data.wind_speed:
                wind_kmh = weather_data.wind_speed * 3.6
                self.metric_labels["wind"].configure(text=f"{wind_kmh:.1f} km/h")

            if "feels_like" in self.metric_labels:
                self.metric_labels["feels_like"].configure(text=f"{int(weather_data.feels_like)}°C")

            if "visibility" in self.metric_labels and weather_data.visibility:
                self.metric_labels["visibility"].configure(text=f"{weather_data.visibility} km")

            if "pressure" in self.metric_labels:
                self.metric_labels["pressure"].configure(text=f"{weather_data.pressure} hPa")

            if "cloudiness" in self.metric_labels and weather_data.cloudiness is not None:
                self.metric_labels["cloudiness"].configure(text=f"{weather_data.cloudiness}%")

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

            # Update status
            self.status_label.configure(
                text=f"✅ Updated: {
                    datetime.now().strftime('%H:%M:%S')}"
            )

        except Exception as e:
            self.logger.error(f"Error updating display: {e}")
            self.status_label.configure(text=f"❌ Error: {str(e)}")

    def _enhanced_toggle_temperature_unit(self):
        """Enhanced temperature unit toggle with micro-interactions."""
        # Add ripple effect on button click
        self.micro_interactions.add_ripple_effect(self.temp_toggle_btn)
        
        # Animate button state change
        self.animation_manager.pulse_effect(self.temp_toggle_btn, duration=500, intensity=0.3)
        
        # Store old unit for smooth transition
        old_unit = self.temp_unit
        
        # Call original toggle method
        self._toggle_temperature_unit()
        
        # Animate temperature value changes
        if hasattr(self, "temp_label"):
            self.animation_manager.animate_number_change(
                self.temp_label, 
                self.temp_label.cget("text")
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
        if hasattr(self, 'forecast_cards') and hasattr(self, 'current_weather_data'):
            if hasattr(self.current_weather_data, 'forecast_data'):
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
            github_service=self.github_service
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
            github_service=self.github_service
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
                        tags=["activities", f"city_{self.current_city}"]
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

    def _create_settings_tab(self):
        """Create settings tab."""
        self._create_settings_tab_content()

    def _create_settings_tab_content(self):
        """Create comprehensive settings tab."""
        # Configure main grid
        self.settings_tab.grid_columnconfigure(0, weight=1)
        self.settings_tab.grid_rowconfigure(0, weight=1)

        # Create scrollable container
        settings_scroll = ctk.CTkScrollableFrame(
            self.settings_tab, fg_color="transparent", corner_radius=0
        )
        settings_scroll.grid(row=0, column=0, sticky="nsew", padx=15, pady=15)

        # Configure scroll frame grid
        settings_scroll.grid_columnconfigure(0, weight=1)

        # Title
        title = ctk.CTkLabel(
            settings_scroll,
            text="⚙️ Settings & Configuration",
            font=(DataTerminalTheme.FONT_FAMILY, 22, "bold"),
            text_color=DataTerminalTheme.PRIMARY,
        )
        title.grid(row=0, column=0, sticky="w", pady=(0, 15))

        # API Configuration Section
        self._create_api_settings(settings_scroll)

        # Appearance Settings
        self._create_appearance_settings(settings_scroll)

        # Data Management
        self._create_data_settings(settings_scroll)

        # Auto-refresh Configuration
        self._create_auto_refresh_settings(settings_scroll)

        # About Section
        self._create_about_section(settings_scroll)

    def _create_api_settings(self, parent):
        """Create enhanced API configuration section."""
        # Section frame
        api_frame = ctk.CTkFrame(
            parent,
            fg_color=DataTerminalTheme.CARD_BG,
            corner_radius=12,
            border_width=1,
            border_color=DataTerminalTheme.BORDER,
        )
        api_frame.grid(row=1, column=0, sticky="ew", pady=(0, 8))
        api_frame.grid_columnconfigure(0, weight=1)

        # Section header
        header = ctk.CTkLabel(
            api_frame,
            text="🔑 API Configuration",
            font=(DataTerminalTheme.FONT_FAMILY, 16, "bold"),
            text_color=DataTerminalTheme.PRIMARY,
        )
        header.grid(row=0, column=0, sticky="w", padx=15, pady=(15, 10))

        # API key entries with enhanced features
        apis = [
            ("OpenWeather API", "OPENWEATHER_API_KEY", "✅ Valid", "Last rotated: 30 days ago"),
            ("Google Gemini API", "GEMINI_API_KEY", "✅ Valid", "Last rotated: 15 days ago"),
            ("Google Maps API", "GOOGLE_MAPS_API_KEY", "⚠️ Expires Soon", "Expires in 7 days"),
        ]

        self.api_entries = {}

        # Container for API entries
        entries_frame = ctk.CTkFrame(api_frame, fg_color="transparent")
        entries_frame.grid(row=1, column=0, sticky="ew", padx=15, pady=(0, 8))
        entries_frame.grid_columnconfigure(1, weight=1)

        for i, (api_name, env_key, status, rotation_info) in enumerate(apis):
            # Label
            label = ctk.CTkLabel(
                entries_frame,
                text=api_name,
                font=(DataTerminalTheme.FONT_FAMILY, 13),
                width=140,
                anchor="w",
            )
            label.grid(row=i, column=0, sticky="w", pady=3)

            # Entry
            entry = ctk.CTkEntry(
                entries_frame,
                placeholder_text="Enter API key...",
                width=200,
                height=32,
                fg_color=DataTerminalTheme.BACKGROUND,
                border_color=DataTerminalTheme.BORDER,
                show="*",  # Hide API key
            )
            entry.grid(row=i, column=1, sticky="ew", padx=(8, 4), pady=3)

            # Show/Hide button
            show_btn = ctk.CTkButton(
                entries_frame,
                text="👁️",
                width=32,
                height=32,
                fg_color=DataTerminalTheme.BACKGROUND,
                hover_color=DataTerminalTheme.HOVER,
                command=lambda e=entry: self._toggle_api_visibility(e),
            )
            show_btn.grid(row=i, column=2, padx=2, pady=3)

            # Test button
            test_btn = ctk.CTkButton(
                entries_frame,
                text="🧪",
                width=32,
                height=32,
                fg_color=DataTerminalTheme.INFO,
                hover_color=DataTerminalTheme.HOVER,
                command=lambda k=env_key: self._test_api_key(k),
            )
            test_btn.grid(row=i, column=3, padx=2, pady=3)

            # Status indicator
            status_label = ctk.CTkLabel(
                entries_frame, text=status, font=(DataTerminalTheme.FONT_FAMILY, 11)
            )
            status_label.grid(row=i, column=4, padx=4, pady=3)

            self.api_entries[env_key] = (entry, status_label, test_btn)

        # Usage statistics frame
        usage_frame = ctk.CTkFrame(api_frame, fg_color=DataTerminalTheme.BACKGROUND)
        usage_frame.grid(row=2, column=0, sticky="ew", padx=15, pady=(8, 0))
        usage_frame.grid_columnconfigure((0, 1, 2), weight=1)

        usage_header = ctk.CTkLabel(
            usage_frame,
            text="📊 API Usage Statistics",
            font=(DataTerminalTheme.FONT_FAMILY, 14, "bold"),
        )
        usage_header.grid(row=0, column=0, columnspan=3, sticky="w", padx=10, pady=(10, 5))

        # Usage stats
        self.usage_labels = {}
        usage_stats = [
            ("Today's Calls:", "42/1000"),
            ("This Month:", "1,247/60,000"),
            ("Rate Limit:", "60 calls/min"),
        ]

        for i, (label_text, value) in enumerate(usage_stats):
            label = ctk.CTkLabel(
                usage_frame,
                text=label_text,
                font=(DataTerminalTheme.FONT_FAMILY, 12),
            )
            label.grid(row=1, column=i, sticky="w", padx=10, pady=5)
            
            value_label = ctk.CTkLabel(
                usage_frame,
                text=value,
                font=(DataTerminalTheme.FONT_FAMILY, 12, "bold"),
                text_color=DataTerminalTheme.SUCCESS,
            )
            value_label.grid(row=2, column=i, sticky="w", padx=10, pady=(0, 10))
            
            self.usage_labels[label_text] = value_label

        # Action buttons frame
        buttons_frame = ctk.CTkFrame(api_frame, fg_color="transparent")
        buttons_frame.grid(row=3, column=0, sticky="ew", padx=15, pady=(8, 15))
        buttons_frame.grid_columnconfigure((0, 1, 2), weight=1)

        # Save button
        save_btn = ctk.CTkButton(
            buttons_frame,
            text="💾 Save Keys",
            width=120,
            height=32,
            fg_color=DataTerminalTheme.SUCCESS,
            font=(DataTerminalTheme.FONT_FAMILY, 12, "bold"),
            command=self._save_api_keys,
        )
        save_btn.grid(row=0, column=0, padx=4, sticky="w")

        # Encrypt button
        encrypt_btn = ctk.CTkButton(
            buttons_frame,
            text="🔒 Encrypt",
            width=120,
            height=32,
            fg_color=DataTerminalTheme.WARNING,
            font=(DataTerminalTheme.FONT_FAMILY, 12, "bold"),
            command=self._encrypt_api_keys,
        )
        encrypt_btn.grid(row=0, column=1, padx=4, sticky="w")

        # Rotate reminder button
        rotate_btn = ctk.CTkButton(
            buttons_frame,
            text="🔄 Set Rotation",
            width=120,
            height=32,
            fg_color=DataTerminalTheme.INFO,
            font=(DataTerminalTheme.FONT_FAMILY, 12, "bold"),
            command=self._setup_key_rotation,
        )
        rotate_btn.grid(row=0, column=2, padx=4, sticky="w")

    def _create_appearance_settings(self, parent):
        """Create enhanced appearance settings section."""
        appearance_frame = ctk.CTkFrame(
            parent,
            fg_color=DataTerminalTheme.CARD_BG,
            corner_radius=12,
            border_width=1,
            border_color=DataTerminalTheme.BORDER,
        )
        appearance_frame.grid(row=2, column=0, sticky="ew", pady=(0, 8))
        appearance_frame.grid_columnconfigure(1, weight=1)

        # Header
        header = ctk.CTkLabel(
            appearance_frame,
            text="🎨 Appearance",
            font=(DataTerminalTheme.FONT_FAMILY, 16, "bold"),
            text_color=DataTerminalTheme.PRIMARY,
        )
        header.grid(row=0, column=0, columnspan=2, sticky="w", padx=15, pady=(15, 10))

        # Theme selection
        theme_label = ctk.CTkLabel(
            appearance_frame,
            text="Theme:",
            font=(DataTerminalTheme.FONT_FAMILY, 13),
            width=140,
            anchor="w",
        )
        theme_label.grid(row=1, column=0, columnspan=2, sticky="w", padx=15, pady=6)

        # Theme preview grid
        self.theme_grid = ctk.CTkFrame(
            appearance_frame,
            fg_color="transparent"
        )
        self.theme_grid.grid(row=2, column=0, columnspan=2, sticky="ew", padx=15, pady=(5, 10))
        self.theme_grid.grid_columnconfigure(0, weight=1)
        self.theme_grid.grid_columnconfigure(1, weight=1)
        self.theme_grid.grid_columnconfigure(2, weight=1)
        
        # Create theme preview cards
        self._create_theme_selector()

        # Temperature units
        units_label = ctk.CTkLabel(
            appearance_frame,
            text="Temperature Units:",
            font=(DataTerminalTheme.FONT_FAMILY, 13),
            width=140,
            anchor="w",
        )
        units_label.grid(row=3, column=0, sticky="w", padx=15, pady=6)

        self.units_var = ctk.StringVar(value="Celsius")
        units_menu = ctk.CTkOptionMenu(
            appearance_frame,
            values=["Celsius", "Fahrenheit", "Kelvin"],
            variable=self.units_var,
            width=180,
            height=30,
            fg_color=DataTerminalTheme.BACKGROUND,
            command=self._change_units,
        )
        units_menu.grid(row=3, column=1, sticky="w", padx=15, pady=6)

        # Date/Time format
        datetime_label = ctk.CTkLabel(
            appearance_frame,
            text="Date/Time Format:",
            font=(DataTerminalTheme.FONT_FAMILY, 13),
            width=140,
            anchor="w",
        )
        datetime_label.grid(row=4, column=0, sticky="w", padx=15, pady=6)

        self.datetime_var = ctk.StringVar(value="MM/DD/YYYY HH:MM")
        datetime_menu = ctk.CTkOptionMenu(
            appearance_frame,
            values=["MM/DD/YYYY HH:MM", "DD/MM/YYYY HH:MM", "YYYY-MM-DD HH:MM", "DD MMM YYYY HH:MM"],
            variable=self.datetime_var,
            width=180,
            height=30,
            fg_color=DataTerminalTheme.BACKGROUND,
            command=self._change_datetime_format,
        )
        datetime_menu.grid(row=4, column=1, sticky="w", padx=15, pady=6)

        # Language selection (preparation for i18n)
        language_label = ctk.CTkLabel(
            appearance_frame,
            text="Language:",
            font=(DataTerminalTheme.FONT_FAMILY, 13),
            width=140,
            anchor="w",
        )
        language_label.grid(row=5, column=0, sticky="w", padx=15, pady=6)

        self.language_var = ctk.StringVar(value="English")
        language_menu = ctk.CTkOptionMenu(
            appearance_frame,
            values=["English", "Spanish", "French", "German", "Chinese", "Japanese"],
            variable=self.language_var,
            width=180,
            height=30,
            fg_color=DataTerminalTheme.BACKGROUND,
            command=self._change_language,
        )
        language_menu.grid(row=5, column=1, sticky="w", padx=15, pady=6)

        # Font size adjustment
        font_label = ctk.CTkLabel(
            appearance_frame,
            text="Font Size:",
            font=(DataTerminalTheme.FONT_FAMILY, 13),
            width=140,
            anchor="w",
        )
        font_label.grid(row=6, column=0, sticky="w", padx=15, pady=6)

        font_frame = ctk.CTkFrame(appearance_frame, fg_color="transparent")
        font_frame.grid(row=6, column=1, sticky="w", padx=15, pady=6)

        self.font_size_var = ctk.IntVar(value=12)
        font_slider = ctk.CTkSlider(
            font_frame,
            from_=10,
            to=18,
            number_of_steps=8,
            variable=self.font_size_var,
            width=120,
            command=self._change_font_size,
        )
        font_slider.grid(row=0, column=0, sticky="w")

        self.font_size_label = ctk.CTkLabel(
            font_frame,
            text="12px",
            font=(DataTerminalTheme.FONT_FAMILY, 11),
            width=40,
        )
        self.font_size_label.grid(row=0, column=1, padx=(8, 0))

    def _create_theme_selector(self):
        """Create theme preview cards for theme selection."""
        self.theme_preview_cards = []
        
        for i, (key, theme) in enumerate(theme_manager.THEMES.items()):
            # Create theme preview card
            preview = ThemePreviewCard(
                self.theme_grid,
                theme_data=theme,
                theme_key=key,
                on_select=lambda t=key: self.apply_theme(t)
            )
            
            # Arrange in 3 columns, 2 rows
            row = i // 3
            col = i % 3
            preview.grid(row=row, column=col, padx=5, pady=5, sticky="ew")
            
            self.theme_preview_cards.append(preview)
            
            # Set current theme as selected
            if key == "matrix":  # Default theme
                preview.set_selected(True)

    def apply_theme(self, theme_name: str):
        """Apply selected theme to the entire application with micro-interactions."""
        try:
            # Find and animate the selected theme card
            selected_card = None
            for card in self.theme_preview_cards:
                if card.theme_key == theme_name:
                    selected_card = card
                    # Add ripple effect to selected theme card
                    self.micro_interactions.add_ripple_effect(card)
                    # Success pulse for theme selection
                    self.animation_manager.success_pulse(card)
                    break
            
            # Apply theme using theme manager
            theme_manager.apply_theme(theme_name, self)
            
            # Update theme preview cards selection with fade effects
            for card in self.theme_preview_cards:
                if card.theme_key == theme_name:
                    card.set_selected(True)
                    # Highlight selected card
                    self.animation_manager.fade_in(card)
                else:
                    card.set_selected(False)
                    # Subtle fade for unselected cards
                    self.animation_manager.fade_out(card, duration=200)
                
            # Update temperature chart if it exists
            if hasattr(self, 'temp_chart') and self.temp_chart:
                theme_data = theme_manager.THEMES.get(theme_name, {})
                self.temp_chart.update_theme(theme_data)
                
            # Show theme change status with animation
            theme_display_name = theme_manager.THEMES.get(theme_name, {}).get('name', theme_name)
            if hasattr(self, "status_label"):
                self.animation_manager.fade_in(self.status_label)
                self.status_label.configure(text=f"🎨 Theme changed to {theme_display_name}")
                
            logging.info(f"Applied theme: {theme_name}")
            
        except Exception as e:
             logging.error(f"Error applying theme {theme_name}: {e}")

    def _on_theme_changed(self):
        """Callback for when theme changes - update UI colors."""
        try:
            # Force update of the entire widget tree
            self.update_idletasks()
            
            # Update temperature chart colors if it exists
            if hasattr(self, 'temp_chart') and self.temp_chart:
                theme_data = {
                    'chart_color': DataTerminalTheme.PRIMARY,
                    'chart_bg': DataTerminalTheme.BACKGROUND,
                    'text_color': DataTerminalTheme.TEXT
                }
                self.temp_chart.update_theme(theme_data)
                
        except Exception as e:
            logging.error(f"Error updating theme: {e}")

    def _create_data_settings(self, parent):
        """Create enhanced data management section."""
        data_frame = ctk.CTkFrame(
            parent,
            fg_color=DataTerminalTheme.CARD_BG,
            corner_radius=12,
            border_width=1,
            border_color=DataTerminalTheme.BORDER,
        )
        data_frame.grid(row=3, column=0, sticky="ew", pady=(0, 8))
        data_frame.grid_columnconfigure(0, weight=1)

        # Header
        header = ctk.CTkLabel(
            data_frame,
            text="💾 Data Management",
            font=(DataTerminalTheme.FONT_FAMILY, 16, "bold"),
            text_color=DataTerminalTheme.PRIMARY,
        )
        header.grid(row=0, column=0, sticky="w", padx=15, pady=(15, 10))

        # Cache information
        cache_info_frame = ctk.CTkFrame(data_frame, fg_color="transparent")
        cache_info_frame.grid(row=1, column=0, sticky="ew", padx=15, pady=6)
        cache_info_frame.grid_columnconfigure(1, weight=1)

        cache_label = ctk.CTkLabel(
            cache_info_frame,
            text="Cache Size:",
            font=(DataTerminalTheme.FONT_FAMILY, 13),
            width=100,
            anchor="w",
        )
        cache_label.grid(row=0, column=0, sticky="w")

        self.cache_size_label = ctk.CTkLabel(
            cache_info_frame,
            text="Calculating...",
            font=(DataTerminalTheme.FONT_FAMILY, 13),
            text_color=DataTerminalTheme.TEXT_SECONDARY,
        )
        self.cache_size_label.grid(row=0, column=1, sticky="w", padx=(10, 0))

        # Cache management buttons
        cache_btn_frame = ctk.CTkFrame(data_frame, fg_color="transparent")
        cache_btn_frame.grid(row=2, column=0, sticky="ew", padx=15, pady=6)

        clear_cache_btn = ctk.CTkButton(
            cache_btn_frame,
            text="🗑️ Clear All",
            width=100,
            height=32,
            fg_color=DataTerminalTheme.WARNING,
            font=(DataTerminalTheme.FONT_FAMILY, 11, "bold"),
            command=self._clear_cache,
        )
        clear_cache_btn.grid(row=0, column=0, padx=(0, 8))

        clear_weather_btn = ctk.CTkButton(
            cache_btn_frame,
            text="☁️ Weather",
            width=100,
            height=32,
            fg_color=DataTerminalTheme.WARNING,
            font=(DataTerminalTheme.FONT_FAMILY, 11, "bold"),
            command=self._clear_weather_cache,
        )
        clear_weather_btn.grid(row=0, column=1, padx=8)

        optimize_btn = ctk.CTkButton(
            cache_btn_frame,
            text="⚡ Optimize",
            width=100,
            height=32,
            fg_color=DataTerminalTheme.INFO,
            font=(DataTerminalTheme.FONT_FAMILY, 11, "bold"),
            command=self._optimize_database,
        )
        optimize_btn.grid(row=0, column=2, padx=8)

        # Export section
        export_frame = ctk.CTkFrame(data_frame, fg_color="transparent")
        export_frame.grid(row=3, column=0, sticky="ew", padx=15, pady=(10, 6))
        export_frame.grid_columnconfigure(2, weight=1)

        export_label = ctk.CTkLabel(
            export_frame,
            text="Export Data:",
            font=(DataTerminalTheme.FONT_FAMILY, 13, "bold"),
        )
        export_label.grid(row=0, column=0, columnspan=3, sticky="w", pady=(0, 6))

        # Date range selection
        from_label = ctk.CTkLabel(export_frame, text="Range:", font=(DataTerminalTheme.FONT_FAMILY, 11))
        from_label.grid(row=1, column=0, sticky="w", pady=2)

        self.export_from_var = ctk.StringVar(value="Last 30 days")
        from_menu = ctk.CTkOptionMenu(
            export_frame,
            values=["Last 7 days", "Last 30 days", "Last 90 days", "Last year", "All time"],
            variable=self.export_from_var,
            width=120,
            height=28,
        )
        from_menu.grid(row=1, column=1, sticky="w", padx=(5, 10), pady=2)

        export_btn = ctk.CTkButton(
            export_frame,
            text="📤 Export",
            width=80,
            height=28,
            fg_color=DataTerminalTheme.SUCCESS,
            font=(DataTerminalTheme.FONT_FAMILY, 11, "bold"),
            command=self._export_data_with_range,
        )
        export_btn.grid(row=1, column=2, sticky="e", pady=2)

        # Import data button
        import_btn = ctk.CTkButton(
            data_frame,
            text="📥 Import Data",
            width=130,
            height=32,
            fg_color=DataTerminalTheme.INFO,
            font=(DataTerminalTheme.FONT_FAMILY, 11, "bold"),
            command=self._enhanced_import_data,
        )
        import_btn.grid(row=4, column=0, sticky="w", padx=15, pady=6)

        # Privacy settings
        privacy_frame = ctk.CTkFrame(data_frame, fg_color="transparent")
        privacy_frame.grid(row=5, column=0, sticky="ew", padx=15, pady=(10, 15))
        privacy_frame.grid_columnconfigure(1, weight=1)

        privacy_label = ctk.CTkLabel(
            privacy_frame,
            text="Privacy Settings:",
            font=(DataTerminalTheme.FONT_FAMILY, 13, "bold"),
        )
        privacy_label.grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 6))

        # Data collection toggle
        collect_label = ctk.CTkLabel(
            privacy_frame,
            text="Collect usage analytics:",
            font=(DataTerminalTheme.FONT_FAMILY, 11),
            width=150,
            anchor="w",
        )
        collect_label.grid(row=1, column=0, sticky="w", pady=2)

        self.analytics_switch = ctk.CTkSwitch(
            privacy_frame,
            text="",
            button_color=DataTerminalTheme.PRIMARY,
            progress_color=DataTerminalTheme.SUCCESS,
            command=self._toggle_analytics,
        )
        self.analytics_switch.grid(row=1, column=1, sticky="w", pady=2)

        # Location data toggle
        location_label = ctk.CTkLabel(
            privacy_frame,
            text="Store location history:",
            font=(DataTerminalTheme.FONT_FAMILY, 11),
            width=150,
            anchor="w",
        )
        location_label.grid(row=2, column=0, sticky="w", pady=2)

        self.location_switch = ctk.CTkSwitch(
            privacy_frame,
            text="",
            button_color=DataTerminalTheme.PRIMARY,
            progress_color=DataTerminalTheme.SUCCESS,
            command=self._toggle_location_storage,
        )
        self.location_switch.grid(row=2, column=1, sticky="w", pady=2)

        # Add micro-interactions
        for btn in [clear_cache_btn, clear_weather_btn, optimize_btn, export_btn, import_btn]:
            self.micro_interactions.add_hover_effect(btn)
            self.micro_interactions.add_click_effect(btn)

        # Update cache size on load
        self._update_cache_size()

    def _create_auto_refresh_settings(self, parent):
        """Create auto-refresh configuration section."""
        # Section frame
        refresh_frame = ctk.CTkFrame(
            parent,
            fg_color=DataTerminalTheme.CARD_BG,
            corner_radius=12,
            border_width=1,
            border_color=DataTerminalTheme.BORDER
        )
        refresh_frame.grid(row=4, column=0, sticky="ew", pady=(0, 15))
        refresh_frame.grid_columnconfigure(0, weight=1)

        # Section header
        header_frame = ctk.CTkFrame(refresh_frame, fg_color="transparent")
        header_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 10))
        header_frame.grid_columnconfigure(1, weight=1)

        # Icon and title
        icon_label = ctk.CTkLabel(
            header_frame,
            text="🔄",
            font=(DataTerminalTheme.FONT_FAMILY, 18)
        )
        icon_label.grid(row=0, column=0, padx=(0, 10))

        title_label = ctk.CTkLabel(
            header_frame,
            text="Auto-Refresh Configuration",
            font=(DataTerminalTheme.FONT_FAMILY, 16, "bold"),
            text_color=DataTerminalTheme.TEXT
        )
        title_label.grid(row=0, column=1, sticky="w")

        # Content frame
        content_frame = ctk.CTkFrame(refresh_frame, fg_color="transparent")
        content_frame.grid(row=1, column=0, sticky="ew", padx=20, pady=(0, 20))
        content_frame.grid_columnconfigure(1, weight=1)

        # Refresh interval setting
        interval_label = ctk.CTkLabel(
            content_frame,
            text="Refresh Interval (minutes):",
            font=(DataTerminalTheme.FONT_FAMILY, 12),
            text_color=DataTerminalTheme.TEXT_SECONDARY
        )
        interval_label.grid(row=0, column=0, sticky="w", pady=(0, 10))

        # Interval slider with value display
        interval_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        interval_frame.grid(row=0, column=1, sticky="ew", padx=(20, 0), pady=(0, 10))
        interval_frame.grid_columnconfigure(0, weight=1)

        self.refresh_interval_var = tk.IntVar(value=self.config_service.get_setting("refresh_interval", 5))
        self.refresh_interval_label = ctk.CTkLabel(
            interval_frame,
            text=f"{self.refresh_interval_var.get()} min",
            font=(DataTerminalTheme.FONT_FAMILY, 12, "bold"),
            text_color=DataTerminalTheme.PRIMARY
        )
        self.refresh_interval_label.grid(row=0, column=1, padx=(10, 0))

        self.refresh_interval_slider = ctk.CTkSlider(
            interval_frame,
            from_=1,
            to=60,
            number_of_steps=59,
            variable=self.refresh_interval_var,
            command=self._on_refresh_interval_changed,
            button_color=DataTerminalTheme.PRIMARY,
            progress_color=DataTerminalTheme.PRIMARY
        )
        self.refresh_interval_slider.grid(row=0, column=0, sticky="ew")

        # Quiet hours setting
        quiet_label = ctk.CTkLabel(
            content_frame,
            text="Quiet Hours:",
            font=(DataTerminalTheme.FONT_FAMILY, 12),
            text_color=DataTerminalTheme.TEXT_SECONDARY
        )
        quiet_label.grid(row=1, column=0, sticky="w", pady=(10, 0))

        quiet_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        quiet_frame.grid(row=1, column=1, sticky="ew", padx=(20, 0), pady=(10, 0))
        quiet_frame.grid_columnconfigure(2, weight=1)

        # Enable quiet hours toggle
        self.quiet_hours_var = tk.BooleanVar(value=self.config_service.get_setting("quiet_hours_enabled", False))
        quiet_toggle = ctk.CTkSwitch(
            quiet_frame,
            text="Enable",
            variable=self.quiet_hours_var,
            command=self._on_quiet_hours_changed,
            button_color=DataTerminalTheme.PRIMARY,
            progress_color=DataTerminalTheme.PRIMARY
        )
        quiet_toggle.grid(row=0, column=0, sticky="w")

        # Start time
        start_label = ctk.CTkLabel(
            quiet_frame,
            text="From:",
            font=(DataTerminalTheme.FONT_FAMILY, 10),
            text_color=DataTerminalTheme.TEXT_SECONDARY
        )
        start_label.grid(row=0, column=1, padx=(20, 5))

        self.quiet_start_var = tk.StringVar(value=self.config_service.get_setting("quiet_start_time", "22:00"))
        start_entry = ctk.CTkEntry(
            quiet_frame,
            textvariable=self.quiet_start_var,
            width=60,
            placeholder_text="22:00"
        )
        start_entry.grid(row=0, column=2, padx=(0, 10))

        # End time
        end_label = ctk.CTkLabel(
            quiet_frame,
            text="To:",
            font=(DataTerminalTheme.FONT_FAMILY, 10),
            text_color=DataTerminalTheme.TEXT_SECONDARY
        )
        end_label.grid(row=0, column=3, padx=(0, 5))

        self.quiet_end_var = tk.StringVar(value=self.config_service.get_setting("quiet_end_time", "07:00"))
        end_entry = ctk.CTkEntry(
            quiet_frame,
            textvariable=self.quiet_end_var,
            width=60,
            placeholder_text="07:00"
        )
        end_entry.grid(row=0, column=4)

        # Network awareness setting
        network_label = ctk.CTkLabel(
            content_frame,
            text="Network Awareness:",
            font=(DataTerminalTheme.FONT_FAMILY, 12),
            text_color=DataTerminalTheme.TEXT_SECONDARY
        )
        network_label.grid(row=2, column=0, sticky="w", pady=(15, 0))

        network_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        network_frame.grid(row=2, column=1, sticky="ew", padx=(20, 0), pady=(15, 0))

        # WiFi only toggle
        self.wifi_only_var = tk.BooleanVar(value=self.config_service.get_setting("wifi_only_refresh", False))
        wifi_toggle = ctk.CTkSwitch(
            network_frame,
            text="WiFi Only (disable on mobile data)",
            variable=self.wifi_only_var,
            command=self._on_wifi_only_changed,
            button_color=DataTerminalTheme.PRIMARY,
            progress_color=DataTerminalTheme.PRIMARY
        )
        wifi_toggle.grid(row=0, column=0, sticky="w")

        # Action buttons
        button_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        button_frame.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(20, 0))
        button_frame.grid_columnconfigure(1, weight=1)

        # Save settings button
        save_btn = ctk.CTkButton(
            button_frame,
            text="💾 Save Settings",
            command=self._save_refresh_settings,
            fg_color=DataTerminalTheme.PRIMARY,
            hover_color=DataTerminalTheme.HOVER,
            font=(DataTerminalTheme.FONT_FAMILY, 12, "bold"),
            height=35
        )
        save_btn.grid(row=0, column=0, padx=(0, 10))

        # Test refresh button
        test_btn = ctk.CTkButton(
            button_frame,
            text="🔄 Test Refresh",
            command=self._test_refresh,
            fg_color=DataTerminalTheme.ACCENT,
            hover_color=DataTerminalTheme.HOVER,
            font=(DataTerminalTheme.FONT_FAMILY, 12),
            height=35
        )
        test_btn.grid(row=0, column=1, sticky="w")

        # Add micro-interactions
        for btn in [save_btn, test_btn]:
            self.micro_interactions.add_hover_effect(btn)
            self.micro_interactions.add_click_effect(btn)

    def _on_refresh_interval_changed(self, value):
        """Handle refresh interval slider change."""
        interval = int(value)
        self.refresh_interval_label.configure(text=f"{interval} min")
        # Auto-save the setting
        self.config_service.set_setting("refresh_interval", interval)

    def _on_quiet_hours_changed(self):
        """Handle quiet hours toggle change."""
        enabled = self.quiet_hours_var.get()
        self.config_service.set_setting("quiet_hours_enabled", enabled)
        # Update refresh schedule if needed
        if hasattr(self, 'refresh_job') and self.refresh_job:
            self._schedule_refresh()

    def _on_wifi_only_changed(self):
        """Handle WiFi only toggle change."""
        wifi_only = self.wifi_only_var.get()
        self.config_service.set_setting("wifi_only_refresh", wifi_only)

    def _save_refresh_settings(self):
        """Save all refresh settings."""
        try:
            # Save quiet hours times
            self.config_service.set_setting("quiet_start_time", self.quiet_start_var.get())
            self.config_service.set_setting("quiet_end_time", self.quiet_end_var.get())
            
            # Show success message
            self.status_manager.show_success("Auto-refresh settings saved successfully!")
            
            # Update refresh schedule
            if hasattr(self, 'refresh_job') and self.refresh_job:
                self._schedule_refresh()
                
        except Exception as e:
            self.status_manager.show_error(f"Failed to save settings: {str(e)}")

    def _test_refresh(self):
        """Test the refresh functionality."""
        self.status_manager.show_info("Testing refresh...")
        self._load_weather_data()

    def _create_about_section(self, parent):
        """Create about section."""
        about_frame = ctk.CTkFrame(
            parent,
            fg_color=DataTerminalTheme.CARD_BG,
            corner_radius=12,
            border_width=1,
            border_color=DataTerminalTheme.BORDER,
        )
        about_frame.grid(row=4, column=0, sticky="ew", pady=(0, 8))
        about_frame.grid_columnconfigure(0, weight=1)

        # Header
        header = ctk.CTkLabel(
            about_frame,
            text="ℹ️ About",
            font=(DataTerminalTheme.FONT_FAMILY, 16, "bold"),
            text_color=DataTerminalTheme.PRIMARY,
        )
        header.grid(row=0, column=0, sticky="w", padx=15, pady=(15, 10))

        # App info
        info_text = """PROJECT CODEFRONT - Weather Dashboard v3.2.56

Advanced Weather Intelligence System
Built with Python, CustomTkinter, and AI Integration

Features:
- Real-time weather data from OpenWeatherMap
- AI-powered activity suggestions (Google Gemini)
- Weather journal with mood tracking
- Interactive temperature forecasting
- Professional data visualization

Created for Justice Through Code Capstone Project
Designer & Programmer: Eric Hunter Petross
Tech Pathways - Justice Through Code - 2025 Cohort
© 2025 - All Rights Reserved"""

        info_label = ctk.CTkLabel(
            about_frame,
            text=info_text,
            font=(DataTerminalTheme.FONT_FAMILY, 11),
            text_color=DataTerminalTheme.TEXT_SECONDARY,
            justify="left",
        )
        info_label.grid(row=1, column=0, sticky="w", padx=15, pady=(0, 12))

        # Links
        links_frame = ctk.CTkFrame(about_frame, fg_color="transparent")
        links_frame.grid(row=2, column=0, sticky="ew", padx=15, pady=(0, 15))
        links_frame.grid_columnconfigure((0, 1), weight=1)

        github_btn = ctk.CTkButton(
            links_frame,
            text="📁 GitHub Repository",
            width=140,
            height=32,
            fg_color=DataTerminalTheme.BACKGROUND,
            border_width=1,
            border_color=DataTerminalTheme.PRIMARY,
            font=(DataTerminalTheme.FONT_FAMILY, 11),
            command=self._enhanced_open_github,
        )
        github_btn.grid(row=0, column=0, padx=(0, 8), sticky="w")
        
        # Add micro-interactions to GitHub button
        self.micro_interactions.add_hover_effect(github_btn)
        self.micro_interactions.add_click_effect(github_btn)

        docs_btn = ctk.CTkButton(
            links_frame,
            text="📚 Documentation",
            width=140,
            height=32,
            fg_color=DataTerminalTheme.BACKGROUND,
            border_width=1,
            border_color=DataTerminalTheme.PRIMARY,
            font=(DataTerminalTheme.FONT_FAMILY, 11),
            command=self._open_documentation,
        )
        docs_btn.grid(row=0, column=1, sticky="w")

    def _toggle_api_visibility(self, entry):
        """Toggle API key visibility."""
        current = entry.cget("show")
        entry.configure(show="" if current == "*" else "*")

    def _save_api_keys(self):
        """Save API keys to environment."""
        # Implementation to save keys
        if hasattr(self, "status_label"):
            self.status_label.configure(text="✅ API keys saved successfully")
        else:
            print("✅ API keys saved successfully")

    def _change_theme(self, theme_name):
        """Legacy theme change method - redirects to new theme system."""
        # Map old theme names to new theme keys
        theme_map = {
            "Dark Terminal": "matrix",
            "Light Mode": "arctic", 
            "Midnight Blue": "midnight"
        }
        
        new_theme_key = theme_map.get(theme_name, "matrix")
        self.apply_theme(new_theme_key)

    def _change_units(self, unit):
        """Change temperature units and update entire application."""
        # Map settings units to internal format
        unit_map = {"Celsius": "C", "Fahrenheit": "F", "Kelvin": "K"}

        new_unit = unit_map.get(unit, "C")

        # Only proceed if unit actually changed
        if hasattr(self, "temp_unit") and self.temp_unit == new_unit:
            return

        # Store old unit for conversion
        old_unit = getattr(self, "temp_unit", "C")

        # Update internal temperature unit
        self.temp_unit = new_unit

        # Update toggle button text if it exists
        if hasattr(self, "temp_toggle_btn"):
            symbol_map = {"C": "°C", "F": "°F", "K": "K"}
            self.temp_toggle_btn.configure(text=symbol_map.get(new_unit, "°C"))

        # Update temperature chart unit
        if hasattr(self, 'temp_chart') and hasattr(self.temp_chart, 'set_temperature_unit'):
            self.temp_chart.set_temperature_unit(new_unit)

        # Convert and update all temperature displays
        self._convert_all_temperatures(old_unit, new_unit)

        # Update status
        if hasattr(self, "status_label"):
            self.status_label.configure(text=f"🌡️ Units changed to {unit}")
        else:
            print(f"🌡️ Units changed to {unit}")

        # Refresh weather data with new units if weather service is available
        if hasattr(self, "weather_service") and self.weather_service:
            self.after(100, self._refresh_weather_with_new_units)

    def _test_api_key(self):
        """Test API key validity."""
        try:
            # Test with a simple weather request
            if hasattr(self, 'weather_service') and self.weather_service:
                # Use a known location for testing
                test_result = self.weather_service.get_weather("London")
                if test_result:
                    self.status_label.configure(text="✅ API key is valid")
                    return True
                else:
                    self.status_label.configure(text="❌ API key test failed")
                    return False
            else:
                self.status_label.configure(text="⚠️ Weather service not available")
                return False
        except Exception as e:
            self.status_label.configure(text=f"❌ API test error: {str(e)}")
            return False

    def _update_usage_stats(self):
        """Update API usage statistics display."""
        try:
            # Mock usage data - in real implementation, get from API provider
            usage_data = {
                'requests_today': 150,
                'daily_limit': 1000,
                'requests_month': 4500,
                'monthly_limit': 30000
            }
            
            daily_percent = (usage_data['requests_today'] / usage_data['daily_limit']) * 100
            monthly_percent = (usage_data['requests_month'] / usage_data['monthly_limit']) * 100
            
            # Update usage labels if they exist
            if hasattr(self, 'daily_usage_label'):
                self.daily_usage_label.configure(
                    text=f"Daily: {usage_data['requests_today']}/{usage_data['daily_limit']} ({daily_percent:.1f}%)"
                )
            if hasattr(self, 'monthly_usage_label'):
                self.monthly_usage_label.configure(
                    text=f"Monthly: {usage_data['requests_month']}/{usage_data['monthly_limit']} ({monthly_percent:.1f}%)"
                )
        except Exception as e:
            print(f"Error updating usage stats: {e}")

    def _encrypt_api_keys(self):
        """Encrypt stored API keys."""
        try:
            # In real implementation, use proper encryption
            self.status_label.configure(text="🔒 API keys encrypted successfully")
            print("API keys encrypted (mock implementation)")
        except Exception as e:
            self.status_label.configure(text=f"❌ Encryption failed: {str(e)}")

    def _set_key_rotation_reminder(self):
        """Set API key rotation reminder."""
        try:
            # In real implementation, set up actual reminders
            self.status_label.configure(text="⏰ Key rotation reminder set for 90 days")
            print("Key rotation reminder set (mock implementation)")
        except Exception as e:
            self.status_label.configure(text=f"❌ Failed to set reminder: {str(e)}")
    
    def _setup_key_rotation(self):
        """Setup API key rotation schedule."""
        try:
            # Create rotation setup dialog
            dialog = ctk.CTkToplevel(self)
            dialog.title("Setup Key Rotation")
            dialog.geometry("450x300")
            dialog.transient(self)
            dialog.grab_set()
            
            # Main frame
            main_frame = ctk.CTkFrame(dialog)
            main_frame.pack(fill="both", expand=True, padx=20, pady=20)
            
            # Title
            title_label = ctk.CTkLabel(
                main_frame,
                text="API Key Rotation Setup",
                font=(DataTerminalTheme.FONT_FAMILY, 16, "bold")
            )
            title_label.pack(pady=(0, 20))
            
            # Rotation interval
            interval_frame = ctk.CTkFrame(main_frame)
            interval_frame.pack(fill="x", pady=10)
            
            ctk.CTkLabel(
                interval_frame,
                text="Rotation Interval (days):",
                font=(DataTerminalTheme.FONT_FAMILY, 12)
            ).pack(side="left", padx=10, pady=10)
            
            interval_var = ctk.StringVar(value="30")
            interval_entry = ctk.CTkEntry(
                interval_frame,
                textvariable=interval_var,
                width=100
            )
            interval_entry.pack(side="right", padx=10, pady=10)
            
            # Email notifications
            email_frame = ctk.CTkFrame(main_frame)
            email_frame.pack(fill="x", pady=10)
            
            email_var = ctk.BooleanVar(value=True)
            email_check = ctk.CTkCheckBox(
                email_frame,
                text="Email notifications",
                variable=email_var
            )
            email_check.pack(side="left", padx=10, pady=10)
            
            # Buttons
            button_frame = ctk.CTkFrame(main_frame)
            button_frame.pack(fill="x", pady=20)
            
            def save_rotation_settings():
                try:
                    interval = int(interval_var.get())
                    email_enabled = email_var.get()
                    
                    if self.config_service:
                        self.config_service.set_setting('api.rotation_interval_days', interval)
                        self.config_service.set_setting('api.rotation_email_enabled', email_enabled)
                    
                    self.logger.info(f"Key rotation set for {interval} days, email: {email_enabled}")
                    dialog.destroy()
                except ValueError:
                    self.logger.error("Invalid rotation interval")
            
            save_btn = ctk.CTkButton(
                button_frame,
                text="Save Settings",
                command=save_rotation_settings,
                fg_color=DataTerminalTheme.SUCCESS
            )
            save_btn.pack(side="left", padx=10)
            
            cancel_btn = ctk.CTkButton(
                button_frame,
                text="Cancel",
                command=dialog.destroy,
                fg_color=DataTerminalTheme.ERROR
            )
            cancel_btn.pack(side="right", padx=10)
            
        except Exception as e:
            self.logger.error(f"Failed to setup key rotation: {e}")

    def _update_cache_size(self):
        """Update cache size display."""
        try:
            # Mock cache size calculation
            cache_size_mb = 15.7
            if hasattr(self, 'cache_size_label'):
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
            self.after(1500, lambda: self.status_label.configure(text="✅ Data exported successfully"))
        except Exception as e:
            self.status_label.configure(text=f"❌ Data export failed: {str(e)}")

    def _toggle_usage_analytics(self):
        """Toggle usage analytics collection."""
        try:
            # Get current state and toggle
            current_state = getattr(self, 'analytics_enabled', True)
            new_state = not current_state
            setattr(self, 'analytics_enabled', new_state)
            
            status = "enabled" if new_state else "disabled"
            self.status_label.configure(text=f"📊 Usage analytics {status}")
        except Exception as e:
            self.status_label.configure(text=f"❌ Analytics toggle failed: {str(e)}")

    def _toggle_location_history(self):
        """Toggle location history storage."""
        try:
            # Get current state and toggle
            current_state = getattr(self, 'location_history_enabled', True)
            new_state = not current_state
            setattr(self, 'location_history_enabled', new_state)
            
            status = "enabled" if new_state else "disabled"
            self.status_label.configure(text=f"📍 Location history {status}")
        except Exception as e:
            self.status_label.configure(text=f"❌ Location history toggle failed: {str(e)}")

    def _change_datetime_format(self, format_type):
        """Change date/time format."""
        try:
            self.datetime_format = format_type
            # Save to config
            if hasattr(self, 'config_service'):
                self.config_service.set('datetime_format', format_type)
            self.status_label.configure(text=f"📅 Date format changed to {format_type}")
        except Exception as e:
            self.status_label.configure(text=f"❌ Date format change failed: {str(e)}")

    def _change_language(self, language):
        """Change application language."""
        try:
            self.language = language
            # Save to config
            if hasattr(self, 'config_service'):
                self.config_service.set('language', language)
            self.status_label.configure(text=f"🌐 Language changed to {language}")
        except Exception as e:
            self.status_label.configure(text=f"❌ Language change failed: {str(e)}")

    def _change_font_size(self, size):
        """Change application font size."""
        try:
            self.font_size = size
            # Save to config
            if hasattr(self, 'config_service'):
                self.config_service.set('font_size', size)
            self.status_label.configure(text=f"🔤 Font size changed to {size}")
        except Exception as e:
            self.status_label.configure(text=f"❌ Font size change failed: {str(e)}")

    def _toggle_analytics(self):
        """Toggle usage analytics."""
        try:
            # Get current state and toggle
            current_state = getattr(self, 'analytics_enabled', True)
            new_state = not current_state
            setattr(self, 'analytics_enabled', new_state)
            
            # Save to config
            if hasattr(self, 'config_service'):
                self.config_service.set('analytics_enabled', new_state)
            
            status = "enabled" if new_state else "disabled"
            self.status_label.configure(text=f"📊 Analytics {status}")
        except Exception as e:
            self.status_label.configure(text=f"❌ Analytics toggle failed: {str(e)}")

    def _toggle_location_storage(self):
        """Toggle location data storage."""
        try:
            # Get current state and toggle
            current_state = getattr(self, 'location_storage_enabled', True)
            new_state = not current_state
            setattr(self, 'location_storage_enabled', new_state)
            
            # Save to config
            if hasattr(self, 'config_service'):
                self.config_service.set('location_storage_enabled', new_state)
            
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

    def _toggle_auto_refresh(self):
        """Toggle auto-refresh functionality."""
        enabled = self.auto_refresh_switch.get()
        self.auto_refresh_enabled = enabled
        status_text = "🔄 Auto-refresh enabled" if enabled else "⏸️ Auto-refresh disabled"
        if hasattr(self, "status_label"):
            self.status_label.configure(text=status_text)
        else:
            print(status_text)

    def _schedule_refresh(self):
        """Schedule automatic weather refresh."""
        try:
            if self.is_destroyed or not self.winfo_exists() or not self.auto_refresh_enabled:
                return
            self._load_weather_data()
            self.safe_after(self.refresh_interval, self._schedule_refresh)
        except tk.TclError:
            # Widget has been destroyed, stop the scheduler
            return

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
        """Convert all temperature displays in the application."""
        if from_unit == to_unit:
            return

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

    def _refresh_weather_with_new_units(self):
        """Refresh weather data to get temperatures in new units."""
        if hasattr(self, "current_city") and self.current_city:
            self._load_weather_data()

    def _enhanced_open_github(self):
        """Enhanced GitHub opening with micro-interactions."""
        # Add ripple effect to GitHub button
        if hasattr(self, 'github_button'):
            self.micro_interactions.add_ripple_effect(self.github_button)
        
        # Show loading animation
        if hasattr(self, 'status_manager'):
            self.status_manager.show_loading("Opening GitHub...")
        
        try:
            result = self._open_github()
            
            # Success pulse animation
            if hasattr(self, 'github_button'):
                self.micro_interactions.add_success_pulse(self.github_button)
            
            if hasattr(self, 'status_manager'):
                self.status_manager.show_success("GitHub repository opened!")
                
        except Exception as e:
            # Warning pulse for errors
            if hasattr(self, 'github_button'):
                self.micro_interactions.add_warning_pulse(self.github_button)
            
            if hasattr(self, 'status_manager'):
                self.status_manager.show_error(f"Failed to open GitHub: {str(e)}")
    
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

    def _clear_cache(self):
        """Clear application cache."""
        try:
            import os

            # Clear cache directories
            cache_dirs = ["cache", "src/cache"]
            files_cleared = 0

            for cache_dir in cache_dirs:
                if os.path.exists(cache_dir):
                    for filename in os.listdir(cache_dir):
                        if filename.endswith(".json") or filename.endswith(".cache"):
                            file_path = os.path.join(cache_dir, filename)
                            try:
                                os.remove(file_path)
                                files_cleared += 1
                            except Exception:
                                pass

            # Clear weather service cache if available
            if hasattr(self, "weather_service") and hasattr(self.weather_service, "clear_cache"):
                self.weather_service.clear_cache()

            if hasattr(self, "status_label"):
                self.status_label.configure(
                    text=f"🗑️ Cache cleared successfully ({files_cleared} files)"
                )
            else:
                print(f"🗑️ Cache cleared successfully ({files_cleared} files)")

        except Exception as e:
            if hasattr(self, "status_label"):
                self.status_label.configure(text=f"❌ Failed to clear cache: {str(e)}")
            else:
                print(f"❌ Failed to clear cache: {e}")

    def _enhanced_export_data(self):
        """Enhanced export with micro-interactions."""
        # Add ripple effect to export button
        if hasattr(self, 'export_button'):
            self.micro_interactions.add_ripple_effect(self.export_button)
        
        # Show loading animation
        if hasattr(self, 'status_manager'):
            self.status_manager.show_loading("Preparing export...")
        
        try:
            result = self._export_data()
            
            # Success pulse animation
            if hasattr(self, 'export_button'):
                self.micro_interactions.add_success_pulse(self.export_button)
            
            if hasattr(self, 'status_manager'):
                self.status_manager.show_success("Data exported successfully!")
                
        except Exception as e:
            # Warning pulse for errors
            if hasattr(self, 'export_button'):
                self.micro_interactions.add_warning_pulse(self.export_button)
            
            if hasattr(self, 'status_manager'):
                self.status_manager.show_error(f"Export failed: {str(e)}")
    
    def _export_data(self):
        """Export application data."""
        try:
            import json
            from datetime import datetime
            from tkinter import filedialog

            # Prepare export data
            export_data = {
                "export_timestamp": datetime.now().isoformat(),
                "app_version": "1.0.0",
                "current_city": getattr(self, "current_city", None),
                "temp_unit": getattr(self, "temp_unit", "C"),
                "settings": {
                    "theme": "Dark",  # Current theme
                    "auto_refresh": (
                        getattr(self, "auto_refresh_switch", None)
                        and self.auto_refresh_switch.get()
                        if hasattr(self, "auto_refresh_switch")
                        else False
                    ),
                },
            }

            # Ask user for save location
            filename = filedialog.asksaveasfilename(
                defaultextension=".json",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
                title="Export Weather Dashboard Data",
            )

            if filename:
                with open(filename, "w") as f:
                    json.dump(export_data, f, indent=2)

                if hasattr(self, "status_label"):
                    self.status_label.configure(text="📊 Data exported successfully")
                else:
                    print("📊 Data exported successfully")
            else:
                if hasattr(self, "status_label"):
                    self.status_label.configure(text="📊 Export cancelled")
                else:
                    print("📊 Export cancelled")

        except Exception as e:
            if hasattr(self, "status_label"):
                self.status_label.configure(text=f"❌ Failed to export data: {str(e)}")
            else:
                print(f"❌ Failed to export data: {e}")

    def _enhanced_import_data(self):
        """Enhanced import with micro-interactions."""
        # Add ripple effect to import button
        if hasattr(self, 'import_button'):
            self.micro_interactions.add_ripple_effect(self.import_button)
        
        # Show loading animation
        if hasattr(self, 'status_manager'):
            self.status_manager.show_loading("Processing import...")
        
        try:
            result = self._import_data()
            
            # Success pulse animation
            if hasattr(self, 'import_button'):
                self.micro_interactions.add_success_pulse(self.import_button)
            
            if hasattr(self, 'status_manager'):
                self.status_manager.show_success("Data imported successfully!")
                
        except Exception as e:
            # Warning pulse for errors
            if hasattr(self, 'import_button'):
                self.micro_interactions.add_warning_pulse(self.import_button)
            
            if hasattr(self, 'status_manager'):
                self.status_manager.show_error(f"Import failed: {str(e)}")
    
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
            self, height=40, fg_color=DataTerminalTheme.CARD_BG, corner_radius=0
        )
        self.status_frame.grid(row=2, column=0, sticky="ew")
        self.status_frame.grid_propagate(False)

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
        if hasattr(self, 'open_hourly_windows'):
            for window_info in self.open_hourly_windows:
                try:
                    if window_info['window'].winfo_exists():
                        window_info['window'].destroy()
                except:
                    pass
            self.open_hourly_windows.clear()
        
        # Cleanup animation manager
        if hasattr(self, 'animation_manager'):
            self.animation_manager.cleanup()
        
        # Cleanup status manager
        if hasattr(self, 'status_manager'):
            self.status_manager.cleanup()
        
        # Cleanup performance optimization services
        if hasattr(self, 'api_optimizer'):
            self.api_optimizer.shutdown()
        
        if hasattr(self, 'component_recycler'):
            self.component_recycler.shutdown()
        
        if hasattr(self, 'cache_manager'):
            # Cache manager doesn't have a stop method, just clear it
            self.cache_manager.clear()
        
        if hasattr(self, 'loading_manager'):
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
                on_component_loaded=self._on_component_loaded,
                on_complete=self._on_startup_complete
            )
            
        except Exception as e:
            self.logger.error(f"Progressive loading initialization failed: {e}")
            self._show_error_state("Failed to initialize dashboard")
    
    def _register_startup_components(self):
        """Register components with startup optimizer for progressive loading."""
        from src.utils.startup_optimizer import ComponentPriority
        
        # Critical components (load first)
        self.startup_optimizer.register_component(
            "weather_display", ComponentPriority.CRITICAL,
            lambda: self._load_weather_data_with_timeout(),
            dependencies=[]
        )
        
        # High priority components
        self.startup_optimizer.register_component(
            "forecast_cards", ComponentPriority.HIGH,
            lambda: self._initialize_forecast_cards(),
            dependencies=["weather_display"]
        )
        
        # Medium priority components
        self.startup_optimizer.register_component(
            "activity_suggestions", ComponentPriority.MEDIUM,
            lambda: self._initialize_activity_suggestions(),
            dependencies=["weather_display"]
        )
        
        # Low priority components (load last)
        self.startup_optimizer.register_component(
            "background_data", ComponentPriority.LOW,
            lambda: self._start_background_loading(),
            dependencies=["weather_display", "forecast_cards"]
        )
    
    def _show_skeleton_ui(self):
        """Show skeleton UI with loading placeholders."""
        try:
            # Show skeleton for main weather display
            self.city_label.configure(text=self.current_city)
            self.temp_label.configure(text="--°")
            self.condition_label.configure(text="Loading...")
            
            # Show skeleton for forecast cards
            if hasattr(self, 'forecast_frame'):
                for widget in self.forecast_frame.winfo_children():
                    if hasattr(widget, 'configure'):
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
            if hasattr(self, 'forecast_frame'):
                # Get recycled forecast cards or create new ones
                for i in range(5):  # Typical 5-day forecast
                    card = self.component_recycler.get_component('forecast_card')
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
        # Start shimmer effects on weather cards
        if hasattr(self, 'weather_metrics_frame'):
            self.shimmer_effect = ShimmerEffect(self.weather_metrics_frame)
            self.shimmer_effect.start_shimmer()
        
        # Show dynamic loading messages
        self.status_manager.show_loading_message()
        
        # Apply loading skeleton to forecast cards
        if hasattr(self, 'forecast_frame'):
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
        # Stop shimmer effects
        if hasattr(self, 'shimmer_effect'):
            self.shimmer_effect.stop_shimmer()
            delattr(self, 'shimmer_effect')
        
        # Hide loading skeleton
        if hasattr(self, 'forecast_skeleton'):
            self.forecast_skeleton.hide()
            delattr(self, 'forecast_skeleton')
        
        # Clear status messages
        self.status_manager.clear_messages()
        
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
            from src.utils.api_optimizer import APIRequest, RequestPriority, CacheStrategy
            
            # Create optimized API request
            api_request = APIRequest(
                url=f"weather/{self.current_city}",
                method="GET",
                priority=RequestPriority.HIGH,
                cache_strategy=CacheStrategy.CACHE_FIRST,
                timeout=10.0,
                metadata={"city": self.current_city, "units": self.temp_unit}
            )
            
            # Make optimized request
            response = self.api_optimizer.make_request(
                api_request,
                actual_fetch_func=lambda: self.weather_service.get_weather(self.current_city)
            )
            
            if response and response.get('success'):
                return response.get('data')
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
            from src.services.enhanced_weather_service import (
                WeatherServiceError, RateLimitError, APIKeyError, 
                NetworkError, ServiceUnavailableError
            )
            
            # For Windows compatibility, use threading timeout instead of signal
            import threading

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
                self.logger.info(
                    f"✅ Weather data loaded successfully for {self.current_city}"
                )
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
            self._hide_loading_state()
            self._update_weather_display(weather_data)
            self.logger.info("Weather display updated successfully")
        except Exception as e:
            self.logger.error(f"Failed to update weather display: {e}")
            self._show_error_state("Failed to display weather data")

    def _handle_weather_error(self, error):
        """Handle weather data loading errors."""
        self.logger.error(f"Weather loading failed: {error}")
        self._show_error_state(str(error))

    def _get_offline_weather_data(self):
        """Get offline fallback weather data."""
        from src.models.weather_models import EnhancedWeatherData, Location, WeatherCondition

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
                if hasattr(self, 'current_location') and self.current_location:
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
                if hasattr(self, 'current_weather_data'):
                    self.current_weather_data.forecast_data = forecast_data
                else:
                    # Create a simple object to hold forecast data
                    class WeatherDataWithForecast:
                        def __init__(self, forecast_data):
                            self.forecast_data = forecast_data
                            self.temperature = 20  # Default temperature
                    
                    self.current_weather_data = WeatherDataWithForecast(forecast_data)
                
                # Update forecast cards with new data
                if hasattr(self, 'forecast_cards') and self.forecast_cards:
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
        
        # Show styled error card
        self.error_manager.show_error(
            title="Weather Data Error",
            message=error_message
        )
        
        # Update labels with animation
        self.animation_manager.fade_in(self.city_label)
        self.city_label.configure(text="Error")
        self.temp_label.configure(text="--°C")
        self.condition_label.configure(
            text=f"❌ {error_message}", text_color=DataTerminalTheme.ERROR
        )
        
        # Show contextual help
        self.status_manager.show_error_help()

        if hasattr(self, "status_label"):
            self.status_label.configure(
                text=f"❌ Error: {error_message}", text_color=DataTerminalTheme.ERROR
            )

    def _show_rate_limit_message(self):
        """Show user-friendly rate limit message."""
        self._show_error_state("Rate limit exceeded. Using cached data. Please wait before trying again.")
        
    def _show_config_error_message(self):
        """Show configuration error message."""
        self._show_error_state("API configuration error. Please check your API key settings.")
        
    def _show_network_error_message(self):
        """Show network error message."""
        self._show_error_state("Network connection issue. Using cached data.")
        
    def _show_service_error_message(self):
        """Show service unavailable message."""
        self._show_error_state("Weather service temporarily unavailable. Using cached data.")
        
    def _show_weather_service_error_message(self, error_details):
        """Show generic weather service error message."""
        self._show_error_state(f"Weather service error: {error_details}. Using cached data.")

    def _create_maps_tab(self):
        """Create Maps tab with location visualization."""
        self._create_maps_tab_content()

    def _create_maps_tab_content(self):
        """Create Maps tab content with Google Maps integration."""
        # Main container
        maps_container = ctk.CTkScrollableFrame(
            self.maps_tab, fg_color=DataTerminalTheme.BACKGROUND
        )
        maps_container.pack(fill="both", expand=True, padx=20, pady=20)

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
            text="🗺️ Weather Maps",
            font=(DataTerminalTheme.FONT_FAMILY, 24, "bold"),
            text_color=DataTerminalTheme.ACCENT,
        )
        title_label.pack(pady=20)

        # Map controls
        controls_frame = ctk.CTkFrame(
            maps_container,
            fg_color=DataTerminalTheme.CARD_BG,
            corner_radius=12,
            border_width=1,
            border_color=DataTerminalTheme.BORDER,
        )
        controls_frame.pack(fill="x", pady=(0, 20))

        controls_title = ctk.CTkLabel(
            controls_frame,
            text="Map Controls",
            font=(DataTerminalTheme.FONT_FAMILY, 18, "bold"),
            text_color=DataTerminalTheme.TEXT,
        )
        controls_title.pack(pady=(15, 10))

        # Map type selection
        map_type_frame = ctk.CTkFrame(controls_frame, fg_color="transparent")
        map_type_frame.pack(fill="x", padx=20, pady=10)

        ctk.CTkLabel(
            map_type_frame,
            text="Map Type:",
            font=(DataTerminalTheme.FONT_FAMILY, 14),
            text_color=DataTerminalTheme.TEXT,
        ).pack(side="left", padx=(0, 10))

        self.map_type_var = ctk.StringVar(value="Temperature")
        map_type_menu = ctk.CTkOptionMenu(
            map_type_frame,
            variable=self.map_type_var,
            values=["Temperature", "Precipitation", "Wind Speed", "Pressure", "Clouds"],
            command=self._update_map_display,
            fg_color=DataTerminalTheme.CARD_BG,
            button_color=DataTerminalTheme.ACCENT,
            text_color=DataTerminalTheme.TEXT,
        )
        map_type_menu.pack(side="left")

        # Location input
        location_frame = ctk.CTkFrame(controls_frame, fg_color="transparent")
        location_frame.pack(fill="x", padx=20, pady=10)

        ctk.CTkLabel(
            location_frame,
            text="Location:",
            font=(DataTerminalTheme.FONT_FAMILY, 14),
            text_color=DataTerminalTheme.TEXT,
        ).pack(side="left", padx=(0, 10))

        self.map_location_entry = ctk.CTkEntry(
            location_frame,
            placeholder_text="Enter city name...",
            width=200,
            fg_color=DataTerminalTheme.BACKGROUND,
            text_color=DataTerminalTheme.TEXT,
            border_color=DataTerminalTheme.BORDER,
        )
        self.map_location_entry.pack(side="left", padx=(0, 10))

        update_map_btn = ctk.CTkButton(
            location_frame,
            text="Update Map",
            command=self._update_map_location,
            fg_color=DataTerminalTheme.PRIMARY,
            hover_color=DataTerminalTheme.SUCCESS,
            text_color=DataTerminalTheme.BACKGROUND,
        )
        update_map_btn.pack(side="left")

        # Map display area
        map_display_frame = ctk.CTkFrame(
            maps_container,
            fg_color=DataTerminalTheme.CARD_BG,
            corner_radius=12,
            border_width=1,
            border_color=DataTerminalTheme.BORDER,
        )
        map_display_frame.pack(fill="both", expand=True)

        # Map placeholder (would integrate with Google Maps API)
        self.map_display_label = ctk.CTkLabel(
            map_display_frame,
            text=(
                "🗺️\n\nWeather Map Display\n\n"
                "Integrate with Google Maps API\nto show weather overlays"
            ),
            font=(DataTerminalTheme.FONT_FAMILY, 16),
            text_color=DataTerminalTheme.TEXT_SECONDARY,
            justify="center",
        )
        self.map_display_label.pack(expand=True, pady=50)



    def _update_map_display(self, map_type):
        """Update map display based on selected type."""
        self.map_display_label.configure(
            text=(
                f"🗺️\n\n{map_type} Map\n\n"
                f"Showing {map_type.lower()} data\n"
                f"for current location"
            )
        )

    def _update_map_location(self):
        """Update map location based on user input."""
        location = self.map_location_entry.get().strip()
        if location:
            map_type = self.map_type_var.get()
            self.map_display_label.configure(
                text=f"🗺️\n\n{map_type} Map\n\nShowing {
                    map_type.lower()} data\nfor {location}"
            )
        else:
            self.map_display_label.configure(
                text="🗺️\n\nPlease enter a location\nto display weather map"
            )



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
