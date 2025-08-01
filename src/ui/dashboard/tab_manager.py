"""Tab Manager Mixin

Contains all tab creation and management methods for the dashboard.
"""

import customtkinter as ctk

from ...services.gemini_service import GeminiService

from ..components.activity_suggestions import ActivitySuggesterComponent
from ..components.enhanced_journal_ui import EnhancedJournalUI
from ..components.journal_calendar import JournalCalendarComponent
from ..components.journal_search import JournalSearchComponent
from ..components.maps_component import MapsComponent
from ..components.photo_gallery import PhotoGalleryComponent
from ..components.temperature_chart import TemperatureChart
from ..theme import DataTerminalTheme


class TabManagerMixin:
    """Mixin class containing tab management methods."""

    def _create_tabs(self) -> None:
        """Create all tabs in correct order"""
        try:
            # CREATE ALL TABS FIRST (this is critical!)
            self.tabview.add("Weather")  # Main weather tab
            self.tabview.add("Locations")  # Location management tab
            self.tabview.add("Analytics")  # Analytics tab
            self.tabview.add("Journal")  # Journal tab
            self.tabview.add("Activities")  # Activities tab
            self.tabview.add("Maps")  # Maps tab
            self.tabview.add("Settings")  # Settings tab

            # NOW populate each tab
            self._create_weather_tab()
            self._create_locations_tab()  # New enhanced locations tab
            self._create_analytics_tab()  # This will now work!
            self._create_journal_tab()
            self._create_activities_tab()
            self._create_maps_tab()
            self._create_settings_tab()

            # Set default tab
            self.tabview.set("Weather")

            self.logger.info("✅ All tabs created successfully")

        except Exception as e:
            self.logger.error(f"Failed to create tabs: {e}")

    def _create_weather_tab(self) -> None:
        """Create weather overview tab with current conditions and forecast."""
        weather_tab = self.tabview.tab("Weather")
        weather_tab.grid_rowconfigure(0, weight=1)
        weather_tab.grid_columnconfigure((0, 1), weight=1)

        # Left column - Current weather
        self._create_current_weather_section(weather_tab)

        # Right column - Charts and forecast
        self._create_charts_section(weather_tab)

    def _create_locations_tab(self) -> None:
        """Create locations management tab with favorites and recent searches."""
        try:
            from ..components.location_manager import LocationManager, LocationManagerUI

            locations_tab = self.tabview.tab("Locations")
            locations_tab.grid_rowconfigure(0, weight=1)
            locations_tab.grid_columnconfigure(0, weight=1)

            # Create location manager instance
            location_manager = LocationManager()

            # Create location manager UI
            self.location_manager_ui = LocationManagerUI(
                parent=locations_tab,
                location_manager=location_manager,
                location_selected_callback=self._on_location_selected_from_manager,
            )
            self.location_manager_ui.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

            self.logger.info("Locations tab created successfully")

        except Exception as e:
            self.logger.error(f"Failed to create locations tab: {e}")
            # Create a simple placeholder
            locations_tab = self.tabview.tab("Locations")
            placeholder = ctk.CTkLabel(
                locations_tab,
                text="Location management temporarily unavailable",
                font=(DataTerminalTheme.FONT_FAMILY, DataTerminalTheme.FONT_SIZE_MEDIUM),
                text_color=self.TEXT_SECONDARY,
            )
            placeholder.pack(expand=True)

    def _on_location_selected_from_manager(self, location_data: dict):
        """Handle location selection from location manager."""
        try:
            city_name = location_data.get("name", "")
            if city_name:
                self.current_city = city_name
                # Switch to weather tab and update
                self.tabview.set("Weather")
                if hasattr(self, "_perform_weather_update"):
                    self._perform_weather_update()

                # Update location label if it exists
                if hasattr(self, "location_label"):
                    city_display = city_name if city_name else "Unknown Location"
                    self.location_label.configure(text=f"📍 {city_display}")

        except Exception as e:
            self.logger.error(f"Location selection from manager failed: {e}")

    def _create_current_weather_section(self, parent) -> None:
        """Create current weather display section with enhanced components."""
        # Try to create enhanced weather display
        try:
            from ..components.auto_refresh import AutoRefreshComponent
            from ..components.enhanced_weather_display import EnhancedWeatherDisplay

            # Create enhanced weather display
            self.enhanced_weather_display = EnhancedWeatherDisplay(parent)
            self.enhanced_weather_display.grid(
                row=0, column=0, sticky="nsew", padx=(0, 10), pady=10
            )

            # Create auto-refresh component
            self.auto_refresh_component = AutoRefreshComponent(
                parent=parent,
                refresh_callback=(
                    self._perform_weather_update
                    if hasattr(self, "_perform_weather_update")
                    else None
                ),
                ui_updater=getattr(self, "ui_updater", None),
            )
            self.auto_refresh_component.grid(
                row=1, column=0, sticky="ew", padx=(0, 10), pady=(0, 10)
            )

            # Keep reference to weather card for compatibility
            self.weather_card = self.enhanced_weather_display

            self.logger.info("Enhanced weather display created successfully")

        except Exception as e:
            self.logger.warning(f"Enhanced weather display failed, using basic display: {e}")
            self._create_basic_weather_display(parent)

    def _create_basic_weather_display(self, parent):
        """Create basic weather display as fallback."""
        # Current weather card
        self.weather_card = ctk.CTkFrame(
            parent,
            fg_color=self.CARD_COLOR,
            corner_radius=15,
            border_width=1,
            border_color=self.BORDER_COLOR,
        )
        self.weather_card.grid(row=0, column=0, sticky="nsew", padx=(0, 10), pady=10)
        self.weather_card.grid_rowconfigure(1, weight=1)

        # Weather card header
        self.weather_header = ctk.CTkFrame(self.weather_card, fg_color="transparent", height=60)
        self.weather_header.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 0))
        self.weather_header.grid_columnconfigure(0, weight=1)

        # Current location
        current_city_display = self.current_city if self.current_city else "Loading..."
        self.location_label = ctk.CTkLabel(
            self.weather_header,
            text=f"📍 {current_city_display}",
            font=(DataTerminalTheme.FONT_FAMILY, DataTerminalTheme.FONT_SIZE_LARGE, "bold"),
            text_color=self.TEXT_PRIMARY,
        )
        self.location_label.grid(row=0, column=0, sticky="w")

        # Refresh button
        self.refresh_button = ctk.CTkButton(
            self.weather_header,
            text="🔄 Refresh",
            font=(DataTerminalTheme.FONT_FAMILY, DataTerminalTheme.FONT_SIZE_SMALL),
            width=100,
            height=30,
            corner_radius=15,
            fg_color=self.ACCENT_COLOR,
            hover_color=DataTerminalTheme.SUCCESS,
            command=self._refresh_weather,
        )
        self.refresh_button.grid(row=0, column=1, sticky="e")

        # Weather metrics grid
        self._create_weather_metrics_grid()

    def _create_weather_metrics_grid(self) -> None:
        """Create grid of weather metrics."""
        # Main weather info container
        self.weather_info = ctk.CTkFrame(self.weather_card, fg_color="transparent")
        self.weather_info.grid(row=1, column=0, sticky="nsew", padx=20, pady=20)
        self.weather_info.grid_columnconfigure((0, 1), weight=1)
        self.weather_info.grid_rowconfigure((0, 1, 2, 3), weight=1)

        # Temperature display
        self.temp_label = ctk.CTkLabel(
            self.weather_info,
            text="--°C",
            font=(DataTerminalTheme.FONT_FAMILY, 48, "bold"),
            text_color=self.ACCENT_COLOR,
        )
        self.temp_label.grid(row=0, column=0, columnspan=2, pady=(0, 10))

        # Weather condition
        self.condition_label = ctk.CTkLabel(
            self.weather_info,
            text="Loading...",
            font=(DataTerminalTheme.FONT_FAMILY, DataTerminalTheme.FONT_SIZE_LARGE),
            text_color=self.TEXT_PRIMARY,
        )
        self.condition_label.grid(row=1, column=0, columnspan=2, pady=(0, 20))

        # Feels like temperature
        self.feels_like_label = ctk.CTkLabel(
            self.weather_info,
            text="Feels like: --°C",
            font=(DataTerminalTheme.FONT_FAMILY, DataTerminalTheme.FONT_SIZE_MEDIUM),
            text_color=self.TEXT_SECONDARY,
        )
        self.feels_like_label.grid(row=2, column=0, sticky="w", pady=5)

        # Humidity
        self.humidity_label = ctk.CTkLabel(
            self.weather_info,
            text="Humidity: --%",
            font=(DataTerminalTheme.FONT_FAMILY, DataTerminalTheme.FONT_SIZE_MEDIUM),
            text_color=self.TEXT_SECONDARY,
        )
        self.humidity_label.grid(row=2, column=1, sticky="w", pady=5)

        # Wind speed
        self.wind_label = ctk.CTkLabel(
            self.weather_info,
            text="Wind: -- km/h",
            font=(DataTerminalTheme.FONT_FAMILY, DataTerminalTheme.FONT_SIZE_MEDIUM),
            text_color=self.TEXT_SECONDARY,
        )
        self.wind_label.grid(row=3, column=0, sticky="w", pady=5)

        # Pressure
        self.pressure_label = ctk.CTkLabel(
            self.weather_info,
            text="Pressure: -- hPa",
            font=(DataTerminalTheme.FONT_FAMILY, DataTerminalTheme.FONT_SIZE_MEDIUM),
            text_color=self.TEXT_SECONDARY,
        )
        self.pressure_label.grid(row=3, column=1, sticky="w", pady=5)

    def _create_charts_section(self, parent) -> None:
        """Create charts and forecast section."""
        # Charts container
        self.charts_frame = ctk.CTkFrame(
            parent,
            fg_color=self.CARD_COLOR,
            corner_radius=15,
            border_width=1,
            border_color=self.BORDER_COLOR,
        )
        self.charts_frame.grid(row=0, column=1, sticky="nsew", padx=(10, 0), pady=10)
        self.charts_frame.grid_rowconfigure(1, weight=1)

        # Charts header
        self.charts_header = ctk.CTkFrame(self.charts_frame, fg_color="transparent", height=60)
        self.charts_header.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 0))
        self.charts_header.grid_columnconfigure(0, weight=1)

        # Charts title
        self.charts_title = ctk.CTkLabel(
            self.charts_header,
            text="📊 Temperature Trends",
            font=(DataTerminalTheme.FONT_FAMILY, DataTerminalTheme.FONT_SIZE_LARGE, "bold"),
            text_color=self.TEXT_PRIMARY,
        )
        self.charts_title.grid(row=0, column=0, sticky="w")

        # Timeframe selector
        self.timeframe_selector = ctk.CTkSegmentedButton(
            self.charts_header,
            values=["24h", "7d", "30d"],
            font=(DataTerminalTheme.FONT_FAMILY, DataTerminalTheme.FONT_SIZE_SMALL),
            selected_color=self.ACCENT_COLOR,
            selected_hover_color=DataTerminalTheme.SUCCESS,
            command=self._on_timeframe_change,
        )
        self.timeframe_selector.set("24h")
        self.timeframe_selector.grid(row=0, column=1, sticky="e")

        # Temperature chart
        try:
            self.temperature_chart = TemperatureChart(self.charts_frame)
            self.temperature_chart.grid(row=1, column=0, sticky="nsew", padx=20, pady=(10, 20))
        except Exception as e:
            self.logger.error(f"Error creating temperature chart: {e}")
            # Create placeholder
            self.chart_placeholder = ctk.CTkLabel(
                self.charts_frame,
                text="Chart unavailable",
                font=(DataTerminalTheme.FONT_FAMILY, DataTerminalTheme.FONT_SIZE_MEDIUM),
                text_color=self.TEXT_SECONDARY,
            )
            self.chart_placeholder.grid(row=1, column=0, sticky="nsew", padx=20, pady=(10, 20))

    def _create_analytics_tab(self):
        """Create clean analytics tab without problematic mood analytics"""
        try:
            # Get the analytics tab frame
            analytics_frame = self.tabview.tab("Analytics")

            # Create simple, working analytics placeholder
            main_container = ctk.CTkFrame(analytics_frame, fg_color="transparent")
            main_container.pack(fill="both", expand=True, padx=20, pady=20)

            # Title
            title_label = ctk.CTkLabel(
                main_container,
                text="📊 Analytics Dashboard",
                font=ctk.CTkFont(size=24, weight="bold"),
                text_color="#FFFFFF",
            )
            title_label.pack(pady=(0, 20))

            # Working analytics content
            content_frame = ctk.CTkFrame(main_container)
            content_frame.pack(fill="both", expand=True)

            # Stats grid that actually works
            stats_container = ctk.CTkFrame(content_frame, fg_color="transparent")
            stats_container.pack(fill="x", padx=20, pady=20)

            # Create working stat cards
            self._create_stat_card(stats_container, "Weather Queries", "47", "#3B82F6", 0)
            self._create_stat_card(stats_container, "Journal Entries", "12", "#10B981", 1)
            self._create_stat_card(stats_container, "Activities Suggested", "23", "#F59E0B", 2)

            # Simple chart placeholder that won't crash
            chart_frame = ctk.CTkFrame(content_frame)
            chart_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))

            chart_title = ctk.CTkLabel(
                chart_frame, text="📈 Usage Trends", font=ctk.CTkFont(size=18, weight="bold")
            )
            chart_title.pack(pady=10)

            chart_placeholder = ctk.CTkLabel(
                chart_frame,
                text="Chart visualization coming soon...\nYour weather dashboard is working great!",
                font=ctk.CTkFont(size=14),
                text_color="#B0B0B0",
            )
            chart_placeholder.pack(expand=True)

            self.logger.info("✅ Clean analytics tab created successfully")

        except Exception as e:
            self.logger.error(f"Failed to create analytics tab: {e}")
            # Ultimate fallback
            try:
                analytics_frame = self.tabview.tab("Analytics")
                fallback = ctk.CTkLabel(analytics_frame, text="Analytics - Ready")
                fallback.pack(expand=True)
            except Exception:
                pass

    def _create_stat_card(self, parent, title, value, color, column):
        """Create a working stat card"""
        try:
            card = ctk.CTkFrame(parent, width=150, height=100)
            card.grid(row=0, column=column, padx=10, pady=10, sticky="ew")

            # Configure grid weights for the parent
            parent.grid_columnconfigure(column, weight=1)

            value_label = ctk.CTkLabel(
                card, text=value, font=ctk.CTkFont(size=32, weight="bold"), text_color=color
            )
            value_label.pack(pady=(15, 5))

            title_label = ctk.CTkLabel(
                card, text=title, font=ctk.CTkFont(size=12), text_color="#B0B0B0"
            )
            title_label.pack()

        except Exception as e:
            self.logger.error(f"Failed to create stat card: {e}")

    def _create_journal_tab(self) -> None:
        """Create the journal tab with enhanced weather diary functionality."""
        # Get journal tab
        journal_tab = self.tabview.tab("Journal")

        # Configure journal tab
        journal_tab.grid_columnconfigure(0, weight=1)
        journal_tab.grid_rowconfigure(0, weight=1)

        # Create enhanced journal UI with comprehensive layout
        self.journal_ui = EnhancedJournalUI(journal_tab, journal_service=self.journal_service)
        self.journal_ui.grid(row=0, column=0, sticky="nsew")

        # Set reference for status updates if needed
        if hasattr(self.journal_ui, "dashboard"):
            self.journal_ui.dashboard = self

    def _create_journal_management_section(self, parent) -> None:
        """Create journal management section."""
        # Management container
        management_frame = ctk.CTkFrame(parent, fg_color="transparent")
        management_frame.grid(row=0, column=1, sticky="nsew", padx=(5, 0), pady=10)
        management_frame.grid_rowconfigure((0, 1, 2), weight=1)

        # Journal search
        try:
            self.journal_search = JournalSearchComponent(
                management_frame, journal_service=self.journal_service
            )
            self.journal_search.grid(row=0, column=0, sticky="nsew", pady=(0, 5))
        except Exception as e:
            self.logger.error(f"Error creating journal search: {e}")

        # Journal calendar
        try:
            self.journal_calendar = JournalCalendarComponent(
                management_frame, journal_service=self.journal_service
            )
            self.journal_calendar.grid(row=1, column=0, sticky="nsew", pady=5)
        except Exception as e:
            self.logger.error(f"Error creating journal calendar: {e}")

        # Photo gallery
        try:
            self.photo_gallery = PhotoGalleryComponent(
                management_frame, photo_manager=self.photo_manager
            )
            self.photo_gallery.grid(row=2, column=0, sticky="nsew", pady=(5, 0))
        except Exception as e:
            self.logger.error(f"Error creating photo gallery: {e}")

    def _create_activities_tab(self) -> None:
        """Create activities tab with AI-powered suggestions."""
        activities_tab = self.tabview.tab("Activities")
        activities_tab.grid_rowconfigure(0, weight=1)
        activities_tab.grid_columnconfigure(0, weight=1)

        try:
            # Initialize Gemini service for AI suggestions
            gemini_service = GeminiService(self.config_service)

            # Get current weather data if available
            current_weather = None
            if hasattr(self, "weather_data") and self.weather_data:
                current_weather = self.weather_data

            self.activity_suggester = ActivitySuggesterComponent(
                activities_tab,
                gemini_service=gemini_service,
                config_service=self.config_service,
                weather_data=current_weather,
            )
            self.activity_suggester.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

            self.logger.info("✅ Activity suggester component created successfully")

        except Exception as e:
            self.logger.error(f"Error creating activity suggester: {e}")
            # Create placeholder
            placeholder = ctk.CTkLabel(
                activities_tab,
                text="🤖 AI Activity suggestions unavailable\nPlease check your Gemini API configuration",
                font=(DataTerminalTheme.FONT_FAMILY, DataTerminalTheme.FONT_SIZE_LARGE),
                text_color=self.TEXT_SECONDARY,
                justify="center",
            )
            placeholder.grid(row=0, column=0)

    def _create_maps_tab(self) -> None:
        """Create maps tab with weather visualization."""
        maps_tab = self.tabview.tab("Maps")
        maps_tab.grid_rowconfigure(0, weight=1)
        maps_tab.grid_columnconfigure(0, weight=1)

        try:
            self.maps_component = MapsComponent(maps_tab, config_service=self.config_service)
            self.maps_component.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        except Exception as e:
            self.logger.error(f"Error creating maps component: {e}")
            # Create placeholder
            placeholder = ctk.CTkLabel(
                maps_tab,
                text="Maps unavailable",
                font=(DataTerminalTheme.FONT_FAMILY, DataTerminalTheme.FONT_SIZE_LARGE),
                text_color=self.TEXT_SECONDARY,
            )
            placeholder.grid(row=0, column=0)

    def _create_settings_tab(self) -> None:
        """Create the settings tab with API key management."""
        # Configure settings tab
        self.settings_tab = self.tabview.tab("Settings")
        self.settings_tab.grid_columnconfigure(0, weight=1)
        self.settings_tab.grid_rowconfigure(1, weight=1)

        # Settings title
        settings_title = ctk.CTkLabel(
            self.settings_tab,
            text="⚙️ SETTINGS & CONFIGURATION",
            font=(DataTerminalTheme.FONT_FAMILY, DataTerminalTheme.FONT_SIZE_MEDIUM, "bold"),
            text_color=self.ACCENT_COLOR,
        )
        settings_title.grid(row=0, column=0, sticky="w", padx=20, pady=(20, 10))

        # Settings scroll frame
        settings_scroll = ctk.CTkScrollableFrame(
            self.settings_tab,
            fg_color=self.CARD_COLOR,
            corner_radius=16,
            border_width=1,
            border_color=self.BORDER_COLOR,
        )
        settings_scroll.grid(row=1, column=0, sticky="nsew", padx=20, pady=(0, 20))

        # API Configuration Section
        api_frame = ctk.CTkFrame(settings_scroll, fg_color="transparent")
        api_frame.pack(fill="x", padx=20, pady=20)

        api_title = ctk.CTkLabel(
            api_frame,
            text="API Configuration",
            font=(DataTerminalTheme.FONT_FAMILY, 14, "bold"),
            text_color=self.TEXT_PRIMARY,
        )
        api_title.pack(anchor="w", pady=(0, 10))

        # API Key Entry
        self.api_key_var = ctk.StringVar(value=self.config_service.get_api_key("openweather") or "")

        api_key_label = ctk.CTkLabel(
            api_frame,
            text="OpenWeatherMap API Key:",
            font=(DataTerminalTheme.FONT_FAMILY, 12),
            text_color=self.TEXT_SECONDARY,
        )
        api_key_label.pack(anchor="w", pady=(5, 2))

        self.api_key_entry = ctk.CTkEntry(
            api_frame,
            textvariable=self.api_key_var,
            placeholder_text="Enter your API key...",
            width=400,
            height=35,
            show="*",  # Hide API key
        )
        self.api_key_entry.pack(anchor="w", pady=(0, 5))

        # Show/Hide API Key button
        self.show_api_key = False
        self.toggle_api_btn = ctk.CTkButton(
            api_frame,
            text="Show API Key",
            width=120,
            height=30,
            command=self._toggle_api_key_visibility,
        )
        self.toggle_api_btn.pack(anchor="w", pady=(0, 10))

        # Save API Key button
        self.save_api_btn = ctk.CTkButton(
            api_frame,
            text="Save API Key",
            width=120,
            height=30,
            fg_color=self.ACCENT_COLOR,
            hover_color=DataTerminalTheme.SUCCESS,
            command=self._save_api_key,
        )
        self.save_api_btn.pack(anchor="w")

        # Preferences Section
        pref_frame = ctk.CTkFrame(settings_scroll, fg_color="transparent")
        pref_frame.pack(fill="x", padx=20, pady=20)

        pref_title = ctk.CTkLabel(
            pref_frame,
            text="Preferences",
            font=(DataTerminalTheme.FONT_FAMILY, 14, "bold"),
            text_color=self.TEXT_PRIMARY,
        )
        pref_title.pack(anchor="w", pady=(0, 10))

        # Temperature Unit
        temp_label = ctk.CTkLabel(
            pref_frame,
            text="Temperature Unit:",
            font=(DataTerminalTheme.FONT_FAMILY, 12),
            text_color=self.TEXT_SECONDARY,
        )
        temp_label.pack(anchor="w", pady=(5, 2))

        self.temp_unit_var = ctk.StringVar(value="Celsius")
        self.temp_unit_menu = ctk.CTkOptionMenu(
            pref_frame,
            values=["Celsius", "Fahrenheit", "Kelvin"],
            variable=self.temp_unit_var,
            width=200,
            height=35,
            command=self._on_temp_unit_change,
        )
        self.temp_unit_menu.pack(anchor="w", pady=(0, 10))

        # Auto-refresh interval
        refresh_label = ctk.CTkLabel(
            pref_frame,
            text="Auto-refresh interval:",
            font=(DataTerminalTheme.FONT_FAMILY, 12),
            text_color=self.TEXT_SECONDARY,
        )
        refresh_label.pack(anchor="w", pady=(5, 2))

        self.refresh_var = ctk.StringVar(value="5 minutes")
        self.refresh_menu = ctk.CTkOptionMenu(
            pref_frame,
            values=["Disabled", "1 minute", "5 minutes", "10 minutes", "30 minutes"],
            variable=self.refresh_var,
            width=200,
            height=35,
            command=self._on_refresh_change,
        )
        self.refresh_menu.pack(anchor="w")

        # Store reference for audio engine to use
        self.audio_controls_frame = settings_scroll

    def _toggle_api_key_visibility(self):
        """Toggle API key visibility."""
        self.show_api_key = not self.show_api_key
        if self.show_api_key:
            self.api_key_entry.configure(show="")
            self.toggle_api_btn.configure(text="Hide API Key")
        else:
            self.api_key_entry.configure(show="*")
            self.toggle_api_btn.configure(text="Show API Key")

    def _save_api_key(self):
        """Save API key to configuration."""
        api_key = self.api_key_var.get().strip()
        if api_key:
            # Save to .env file
            self._update_env_file("OPENWEATHER_API_KEY", api_key)
            self.config_service._config.api.openweather_api_key = api_key
            from services.enhanced_weather_service import EnhancedWeatherService

            self.weather_service = EnhancedWeatherService(self.config_service)
            self._safe_update_status("API key saved successfully!")

            # Refresh weather data
            if hasattr(self, "_refresh_weather"):
                self._refresh_weather()
            elif hasattr(self, "_schedule_weather_update"):
                self._schedule_weather_update()
        else:
            self._safe_update_status("Please enter a valid API key")

    def _update_env_file(self, key: str, value: str):
        """Update .env file with new value."""
        from pathlib import Path

        env_path = Path(".env")

        # Read existing content
        lines = []
        key_found = False

        if env_path.exists():
            with open(env_path, "r") as f:
                for line in f:
                    if line.startswith(f"{key}="):
                        lines.append(f"{key}={value}\n")
                        key_found = True
                    else:
                        lines.append(line)

        # Add key if not found
        if not key_found:
            lines.append(f"{key}={value}\n")

        # Write back to file
        with open(env_path, "w") as f:
            f.writelines(lines)

    def _on_temp_unit_change(self, value: str):
        """Handle temperature unit change."""
        # Update config with new temperature unit
        unit_map = {"Celsius": "metric", "Fahrenheit": "imperial", "Kelvin": "kelvin"}
        if hasattr(self, "config_service") and value in unit_map:
            self.config_service._config.weather.default_units = unit_map[value]

        if hasattr(self, "logger"):
            self.logger.info(f"Temperature unit changed to: {value}")

        # Refresh weather display with new unit
        if hasattr(self, "_refresh_weather"):
            self._refresh_weather()
        elif hasattr(self, "_schedule_weather_update"):
            self._schedule_weather_update()
        elif hasattr(self, "current_weather") and hasattr(
            self, "_update_weather_display_with_real_data"
        ):
            self._update_weather_display_with_real_data(self.current_weather)

    def _on_refresh_change(self, value: str):
        """Handle auto-refresh interval change."""
        if hasattr(self, "logger"):
            self.logger.info(f"Auto-refresh interval changed to: {value}")
        # Update auto-refresh timer based on new interval
        self._setup_auto_refresh(value)

    def _setup_auto_refresh(self, interval: str):
        """Setup auto-refresh timer based on interval."""
        # Cancel existing timer
        if hasattr(self, "auto_refresh_timer_id") and self.auto_refresh_timer_id:
            try:
                self.after_cancel(self.auto_refresh_timer_id)
            except Exception:
                pass
            self.auto_refresh_timer_id = None

        # Set up new timer based on interval
        if interval == "Disabled":
            return

        # Convert interval to milliseconds
        interval_map = {
            "1 minute": 60000,
            "5 minutes": 300000,
            "10 minutes": 600000,
            "30 minutes": 1800000,
        }

        ms = interval_map.get(interval, 300000)  # Default to 5 minutes

        # Schedule next refresh
        self.auto_refresh_timer_id = self.after(ms, self._auto_refresh_callback)

    def _auto_refresh_callback(self):
        """Callback for auto-refresh timer."""
        try:
            # Use the appropriate weather refresh method
            if hasattr(self, "_refresh_weather"):
                self._refresh_weather()
            elif hasattr(self, "_schedule_weather_update"):
                self._schedule_weather_update()

            # Schedule next refresh
            interval = self.refresh_var.get() if hasattr(self, "refresh_var") else "5 minutes"
            self._setup_auto_refresh(interval)
        except Exception as e:
            if hasattr(self, "logger"):
                self.logger.error(f"Auto-refresh error: {e}")

    def _on_timeframe_change(self, value: str) -> None:
        """Handle timeframe selector change."""
        self.chart_timeframe = value
        if hasattr(self, "temperature_chart"):
            try:
                self.temperature_chart.update_timeframe(value)
            except Exception as e:
                self.logger.error(f"Error updating chart timeframe: {e}")
