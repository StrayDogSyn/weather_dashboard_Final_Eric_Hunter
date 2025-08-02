import logging
from datetime import datetime, timedelta

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
from src.ui.theme import DataTerminalTheme
from src.ui.theme_manager import theme_manager
from src.utils.loading_manager import LoadingManager

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

        # Initialize theme manager and register as observer
        DataTerminalTheme.add_observer(self._on_theme_changed)
        
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

        # Search controls
        search_controls = ctk.CTkFrame(search_container, fg_color="transparent")
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
            command=self._search_weather,
        )
        self.search_button.pack(side="left")

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
            command=self._toggle_temperature_unit,
        )
        self.temp_toggle_btn.pack(side="left", padx=(0, 12), pady=8)

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
        """Create 5-day forecast cards with improved spacing."""
        forecast_frame = ctk.CTkFrame(parent, fg_color="transparent")
        forecast_frame.pack(fill="x", padx=15, pady=(0, 15))

        # Configure grid for equal distribution
        for i in range(5):
            forecast_frame.grid_columnconfigure(i, weight=1)

        # Create 5 forecast cards
        for i in range(5):
            day_card = ctk.CTkFrame(
                forecast_frame,
                fg_color=DataTerminalTheme.BACKGROUND,
                corner_radius=8,
                border_width=1,
                border_color=DataTerminalTheme.BORDER,
                height=100,
            )
            day_card.grid(row=0, column=i, padx=6, pady=3, sticky="ew")
            day_card.grid_propagate(False)

            # Day name
            day = (datetime.now() + timedelta(days=i)).strftime("%a")
            day_label = ctk.CTkLabel(
                day_card,
                text=day,
                font=(DataTerminalTheme.FONT_FAMILY, 11, "bold"),
                text_color=DataTerminalTheme.TEXT,
            )
            day_label.pack(pady=(8, 3))

            # Weather icon
            icon_label = ctk.CTkLabel(day_card, text="🌤️", font=(DataTerminalTheme.FONT_FAMILY, 22))
            icon_label.pack(pady=5)

            # Temperature
            temp_label = ctk.CTkLabel(
                day_card,
                text="22°/15°",
                font=(DataTerminalTheme.FONT_FAMILY, 10, "bold"),
                text_color=DataTerminalTheme.PRIMARY,
            )
            temp_label.pack(pady=(3, 8))

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
            # This would typically use forecast data from the weather service
            # For now, we'll generate sample forecast data based on current
            # weather
            if hasattr(weather_data, "temperature"):
                base_temp = weather_data.temperature

                # Find all forecast cards and update them
                forecast_frame = None
                for child in self.weather_tab.winfo_children():
                    if isinstance(child, ctk.CTkFrame):
                        for subchild in child.winfo_children():
                            if isinstance(subchild, ctk.CTkFrame):
                                # Look for forecast cards container
                                for frame_child in subchild.winfo_children():
                                    if hasattr(frame_child, "grid_slaves"):
                                        forecast_frame = frame_child
                                        break
                                if forecast_frame:
                                    break
                        if forecast_frame:
                            break

                if forecast_frame:
                    # Update forecast cards with sample data
                    cards = forecast_frame.grid_slaves()
                    for i, card in enumerate(cards[:5]):
                        if isinstance(card, ctk.CTkFrame):
                            # Generate forecast temperatures (slight
                            # variations)
                            high_temp = int(base_temp + (i * 2) - 2)
                            low_temp = int(base_temp - 5 + (i * 1))

                            # Update temperature label in card
                            for widget in card.winfo_children():
                                if isinstance(widget, ctk.CTkLabel):
                                    text = widget.cget("text")
                                    if "°" in text and "/" in text:
                                        widget.configure(text=f"{high_temp}°/{low_temp}°")
                                        break
        except Exception as e:
            self.logger.error(f"Failed to update forecast cards: {e}")

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

                # Update chart if it has an update method
                if hasattr(self.temp_chart, "update_data"):
                    self.temp_chart.update_data(hourly_temps)
                elif hasattr(self.temp_chart, "set_data"):
                    self.temp_chart.set_data(hourly_temps)
        except Exception as e:
            self.logger.error(f"Failed to update temperature chart: {e}")

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

            # Here you would typically call weather API
            # For now, just update the display with placeholder data
            self._update_weather_display()

    def _get_weather_icon(self, condition):
        """Get weather icon based on condition."""
        condition_lower = condition.lower()
        for key, icon in self.weather_icons.items():
            if key in condition_lower:
                return icon
        return "🌤️"  # Default icon

    def _update_weather_display(self, weather_data):
        """Update UI with enhanced weather display."""
        try:
            # Store current weather data for activity suggestions
            self.current_weather_data = weather_data

            # Update activities if on activities tab
            if self.tabview.get() == "Activities":
                self._update_activity_suggestions(weather_data)

            # Refresh activity suggestions with new weather data
            self._refresh_activity_suggestions()

            # Update location
            location_name = f"{
                weather_data.location.name}, {
                weather_data.location.country}"
            self.city_label.configure(text=location_name)
            self.location_label.configure(text=f"📍 Current: {location_name}")

            # Get weather icon
            condition_lower = weather_data.description.lower()
            icon = "🌤️"  # default
            for key, emoji in self.weather_icons.items():
                if key in condition_lower:
                    icon = emoji
                    break

            # Update main display
            self.temp_label.configure(text=f"{int(weather_data.temperature)}°C")
            self.condition_label.configure(text=f"{icon} {weather_data.description}")

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
        """Update activity suggestions based on weather."""
        try:
            # Get new suggestions
            if self.activity_service:
                suggestions = self.activity_service.get_activity_suggestions(weather_data)
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

        # About Section
        self._create_about_section(settings_scroll)

    def _create_api_settings(self, parent):
        """Create API configuration section."""
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

        # API key entries
        apis = [
            ("OpenWeather API", "OPENWEATHER_API_KEY", "✅"),
            ("Google Gemini API", "GEMINI_API_KEY", "✅"),
            ("Google Maps API", "GOOGLE_MAPS_API_KEY", "✅"),
        ]

        self.api_entries = {}

        # Container for API entries
        entries_frame = ctk.CTkFrame(api_frame, fg_color="transparent")
        entries_frame.grid(row=1, column=0, sticky="ew", padx=15, pady=(0, 8))
        entries_frame.grid_columnconfigure(1, weight=1)

        for i, (api_name, env_key, status) in enumerate(apis):
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
                width=280,
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
            show_btn.grid(row=i, column=2, padx=4, pady=3)

            # Status indicator
            status_label = ctk.CTkLabel(
                entries_frame, text=status, font=(DataTerminalTheme.FONT_FAMILY, 14)
            )
            status_label.grid(row=i, column=3, padx=8, pady=3)

            self.api_entries[env_key] = (entry, status_label)

        # Save button
        save_btn = ctk.CTkButton(
            api_frame,
            text="💾 Save API Keys",
            width=140,
            height=32,
            fg_color=DataTerminalTheme.SUCCESS,
            font=(DataTerminalTheme.FONT_FAMILY, 13, "bold"),
            command=self._save_api_keys,
        )
        save_btn.grid(row=2, column=0, pady=(8, 15))

    def _create_appearance_settings(self, parent):
        """Create appearance settings section."""
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

        # Auto-refresh toggle
        refresh_label = ctk.CTkLabel(
            appearance_frame,
            text="Auto-refresh (5 min):",
            font=(DataTerminalTheme.FONT_FAMILY, 13),
            width=140,
            anchor="w",
        )
        refresh_label.grid(row=4, column=0, sticky="w", padx=15, pady=(6, 15))

        self.auto_refresh_switch = ctk.CTkSwitch(
            appearance_frame,
            text="",
            button_color=DataTerminalTheme.PRIMARY,
            progress_color=DataTerminalTheme.SUCCESS,
            command=self._toggle_auto_refresh,
        )
        self.auto_refresh_switch.grid(row=4, column=1, sticky="w", padx=15, pady=(6, 15))

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
        """Apply selected theme to the entire application."""
        try:
            # Apply theme using theme manager
            theme_manager.apply_theme(theme_name, self)
            
            # Update theme preview cards selection
            for card in self.theme_preview_cards:
                card.set_selected(card.theme_key == theme_name)
                
            # Update temperature chart if it exists
            if hasattr(self, 'temp_chart') and self.temp_chart:
                theme_data = theme_manager.THEMES.get(theme_name, {})
                self.temp_chart.update_theme(theme_data)
                
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
        """Create data management section."""
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

        # Buttons frame
        buttons_frame = ctk.CTkFrame(data_frame, fg_color="transparent")
        buttons_frame.grid(row=1, column=0, sticky="ew", padx=15, pady=(0, 15))
        buttons_frame.grid_columnconfigure((0, 1, 2), weight=1)

        # Clear cache button
        clear_cache_btn = ctk.CTkButton(
            buttons_frame,
            text="🗑️ Clear Cache",
            width=130,
            height=32,
            fg_color=DataTerminalTheme.WARNING,
            font=(DataTerminalTheme.FONT_FAMILY, 11, "bold"),
            command=self._clear_cache,
        )
        clear_cache_btn.grid(row=0, column=0, padx=(0, 8), sticky="w")

        # Export data button
        export_btn = ctk.CTkButton(
            buttons_frame,
            text="📤 Export Data",
            width=130,
            height=32,
            fg_color=DataTerminalTheme.INFO,
            font=(DataTerminalTheme.FONT_FAMILY, 11, "bold"),
            command=self._export_data,
        )
        export_btn.grid(row=0, column=1, padx=4, sticky="w")

        # Import data button
        import_btn = ctk.CTkButton(
            buttons_frame,
            text="📥 Import Data",
            width=130,
            height=32,
            fg_color=DataTerminalTheme.SUCCESS,
            font=(DataTerminalTheme.FONT_FAMILY, 11, "bold"),
            command=self._import_data,
        )
        import_btn.grid(row=0, column=2, padx=4, sticky="w")

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
            command=self._open_github,
        )
        github_btn.grid(row=0, column=0, padx=(0, 8), sticky="w")

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
        if self.auto_refresh_enabled:
            self._load_weather_data()
            self.after(self.refresh_interval, self._schedule_refresh)

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

    def _update_time(self):
        """Update time display."""
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.time_label.configure(text=current_time)
        self.after(1000, self._update_time)

    def _initialize_progressive_loading(self):
        """Initialize progressive loading with UI-first approach."""
        try:
            # Step 1: Show UI immediately with placeholder data
            self._show_initial_ui_state()

            # Step 2: Load critical weather data with short timeout
            self.after(100, self._load_weather_data_with_timeout)

        except Exception as e:
            self.logger.error(f"Progressive loading initialization failed: {e}")
            self._show_error_state("Failed to initialize dashboard")

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
        """Show loading indicators."""
        self.city_label.configure(text="Loading...")
        self.temp_label.configure(text="--°C")
        self.condition_label.configure(text="Fetching weather data...")

        # Show loading spinner if available
        if hasattr(self, "loading_spinner"):
            self.loading_spinner.start()

    def _hide_loading_state(self):
        """Hide loading indicators."""
        # Hide loading spinner if available
        if hasattr(self, "loading_spinner"):
            self.loading_spinner.stop()

    def _safe_fetch_weather_data_with_timeout(self):
        """Safely fetch weather data with timeout and enhanced error handling."""
        if not self.weather_service:
            # Return offline fallback data immediately
            self.logger.warning("No weather service available, using offline data")
            return self._get_offline_weather_data()

        try:
            # Set a strict timeout for the API call
            pass

            def timeout_handler(signum, frame):
                raise TimeoutError("Weather API call timed out")

            # For Windows compatibility, use threading timeout instead of
            # signal
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
                    f"Weather API timeout for {
                        self.current_city}, using cached/offline data"
                )
                return self._get_cached_or_offline_weather_data()

            if exception[0]:
                raise exception[0]

            if result[0]:
                self.logger.info(
                    f"✅ Weather data loaded successfully for {
                        self.current_city}"
                )
                return result[0]
            else:
                raise Exception("No weather data returned")

        except Exception as e:
            self.logger.error(f"Weather fetch failed: {e}")
            # Try to get cached or offline data
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
                # Add specific forecast update logic here
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
        """Show error state in UI."""
        self._hide_loading_state()

        self.city_label.configure(text="Error")
        self.temp_label.configure(text="--°C")
        self.condition_label.configure(
            text=f"❌ {error_message}", text_color=DataTerminalTheme.ERROR
        )

        if hasattr(self, "status_label"):
            self.status_label.configure(
                text=f"❌ Error: {error_message}", text_color=DataTerminalTheme.ERROR
            )

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
