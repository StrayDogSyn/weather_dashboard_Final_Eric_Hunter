"""Tab Manager Mixin

Contains all tab creation and management methods for the dashboard.
"""

import customtkinter as ctk
from ui.components.temperature_chart import TemperatureChart
from ui.components.weather_journal import WeatherJournal
from ui.components.journal_manager import JournalManager
from ui.components.journal_search import JournalSearchComponent
from ui.components.journal_calendar import JournalCalendarComponent
from ui.components.photo_gallery import PhotoGalleryComponent
from ui.components.mood_analytics import MoodAnalyticsComponent
from ui.components.activity_suggester import ActivitySuggester
from ui.components.maps_component import MapsComponent
from ui.theme import DataTerminalTheme


class TabManagerMixin:
    """Mixin class containing tab management methods."""
    
    def _create_tabs(self) -> None:
        """Create all dashboard tabs."""
        # Weather Overview Tab
        self._create_weather_tab()
        
        # Analytics Tab
        self._create_analytics_tab()
        
        # Journal Tab
        self._create_journal_tab()
        
        # Activities Tab
        self._create_activities_tab()
        
        # Maps Tab
        self._create_maps_tab()
        
        # Settings Tab
        self._create_settings_tab()
    
    def _create_weather_tab(self) -> None:
        """Create weather overview tab with current conditions and forecast."""
        weather_tab = self.tabview.add("🌤️ Weather")
        weather_tab.grid_rowconfigure(0, weight=1)
        weather_tab.grid_columnconfigure((0, 1), weight=1)
        
        # Left column - Current weather
        self._create_current_weather_section(weather_tab)
        
        # Right column - Charts and forecast
        self._create_charts_section(weather_tab)
    
    def _create_current_weather_section(self, parent) -> None:
        """Create current weather display section."""
        # Current weather card
        self.weather_card = ctk.CTkFrame(
            parent,
            fg_color=self.CARD_COLOR,
            corner_radius=15,
            border_width=1,
            border_color=self.BORDER_COLOR
        )
        self.weather_card.grid(row=0, column=0, sticky="nsew", padx=(0, 10), pady=10)
        self.weather_card.grid_rowconfigure(1, weight=1)
        
        # Weather card header
        self.weather_header = ctk.CTkFrame(
            self.weather_card,
            fg_color="transparent",
            height=60
        )
        self.weather_header.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 0))
        self.weather_header.grid_columnconfigure(0, weight=1)
        
        # Current location
        self.location_label = ctk.CTkLabel(
            self.weather_header,
            text=f"📍 {self.current_city}",
            font=(DataTerminalTheme.FONT_FAMILY, DataTerminalTheme.FONT_SIZE_LARGE, "bold"),
            text_color=self.TEXT_PRIMARY
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
            command=self._refresh_weather
        )
        self.refresh_button.grid(row=0, column=1, sticky="e")
        
        # Weather metrics grid
        self._create_weather_metrics_grid()
    
    def _create_weather_metrics_grid(self) -> None:
        """Create grid of weather metrics."""
        # Main weather info container
        self.weather_info = ctk.CTkFrame(
            self.weather_card,
            fg_color="transparent"
        )
        self.weather_info.grid(row=1, column=0, sticky="nsew", padx=20, pady=20)
        self.weather_info.grid_columnconfigure((0, 1), weight=1)
        self.weather_info.grid_rowconfigure((0, 1, 2, 3), weight=1)
        
        # Temperature display
        self.temp_label = ctk.CTkLabel(
            self.weather_info,
            text="--°C",
            font=(DataTerminalTheme.FONT_FAMILY, 48, "bold"),
            text_color=self.ACCENT_COLOR
        )
        self.temp_label.grid(row=0, column=0, columnspan=2, pady=(0, 10))
        
        # Weather condition
        self.condition_label = ctk.CTkLabel(
            self.weather_info,
            text="Loading...",
            font=(DataTerminalTheme.FONT_FAMILY, DataTerminalTheme.FONT_SIZE_LARGE),
            text_color=self.TEXT_PRIMARY
        )
        self.condition_label.grid(row=1, column=0, columnspan=2, pady=(0, 20))
        
        # Feels like temperature
        self.feels_like_label = ctk.CTkLabel(
            self.weather_info,
            text="Feels like: --°C",
            font=(DataTerminalTheme.FONT_FAMILY, DataTerminalTheme.FONT_SIZE_MEDIUM),
            text_color=self.TEXT_SECONDARY
        )
        self.feels_like_label.grid(row=2, column=0, sticky="w", pady=5)
        
        # Humidity
        self.humidity_label = ctk.CTkLabel(
            self.weather_info,
            text="Humidity: --%",
            font=(DataTerminalTheme.FONT_FAMILY, DataTerminalTheme.FONT_SIZE_MEDIUM),
            text_color=self.TEXT_SECONDARY
        )
        self.humidity_label.grid(row=2, column=1, sticky="w", pady=5)
        
        # Wind speed
        self.wind_label = ctk.CTkLabel(
            self.weather_info,
            text="Wind: -- km/h",
            font=(DataTerminalTheme.FONT_FAMILY, DataTerminalTheme.FONT_SIZE_MEDIUM),
            text_color=self.TEXT_SECONDARY
        )
        self.wind_label.grid(row=3, column=0, sticky="w", pady=5)
        
        # Pressure
        self.pressure_label = ctk.CTkLabel(
            self.weather_info,
            text="Pressure: -- hPa",
            font=(DataTerminalTheme.FONT_FAMILY, DataTerminalTheme.FONT_SIZE_MEDIUM),
            text_color=self.TEXT_SECONDARY
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
            border_color=self.BORDER_COLOR
        )
        self.charts_frame.grid(row=0, column=1, sticky="nsew", padx=(10, 0), pady=10)
        self.charts_frame.grid_rowconfigure(1, weight=1)
        
        # Charts header
        self.charts_header = ctk.CTkFrame(
            self.charts_frame,
            fg_color="transparent",
            height=60
        )
        self.charts_header.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 0))
        self.charts_header.grid_columnconfigure(0, weight=1)
        
        # Charts title
        self.charts_title = ctk.CTkLabel(
            self.charts_header,
            text="📊 Temperature Trends",
            font=(DataTerminalTheme.FONT_FAMILY, DataTerminalTheme.FONT_SIZE_LARGE, "bold"),
            text_color=self.TEXT_PRIMARY
        )
        self.charts_title.grid(row=0, column=0, sticky="w")
        
        # Timeframe selector
        self.timeframe_selector = ctk.CTkSegmentedButton(
            self.charts_header,
            values=["24h", "7d", "30d"],
            font=(DataTerminalTheme.FONT_FAMILY, DataTerminalTheme.FONT_SIZE_SMALL),
            selected_color=self.ACCENT_COLOR,
            selected_hover_color=DataTerminalTheme.SUCCESS,
            command=self._on_timeframe_change
        )
        self.timeframe_selector.set("24h")
        self.timeframe_selector.grid(row=0, column=1, sticky="e")
        
        # Temperature chart
        try:
            self.temperature_chart = TemperatureChart(
                self.charts_frame
            )
            self.temperature_chart.grid(row=1, column=0, sticky="nsew", padx=20, pady=(10, 20))
        except Exception as e:
            self.logger.error(f"Error creating temperature chart: {e}")
            # Create placeholder
            self.chart_placeholder = ctk.CTkLabel(
                self.charts_frame,
                text="Chart unavailable",
                font=(DataTerminalTheme.FONT_FAMILY, DataTerminalTheme.FONT_SIZE_MEDIUM),
                text_color=self.TEXT_SECONDARY
            )
            self.chart_placeholder.grid(row=1, column=0, sticky="nsew", padx=20, pady=(10, 20))
    
    def _create_analytics_tab(self) -> None:
        """Create analytics tab with consistent geometry management"""
        try:
            # Get the analytics tab frame
            analytics_frame = self.tabview.add("📈 Analytics")
            
            # CRITICAL: Use ONLY pack() OR ONLY grid() - never mix them in same parent
            
            # Option A: Use pack() for everything (recommended for tabs)
            if hasattr(self, 'mood_analytics') and self.mood_analytics:
                # Check if mood_analytics is a widget that can be packed
                if hasattr(self.mood_analytics, 'pack'):
                    self.mood_analytics.pack(fill='both', expand=True, padx=10, pady=10)
                else:
                    # If it's a custom component, wrap it in a frame
                    wrapper_frame = ctk.CTkFrame(analytics_frame)
                    wrapper_frame.pack(fill='both', expand=True, padx=10, pady=10)
                    
                    # Add mood_analytics to wrapper if it has content
                    if hasattr(self.mood_analytics, 'create_widgets'):
                        self.mood_analytics.create_widgets(wrapper_frame)
            else:
                # Try to create mood analytics component
                try:
                    self.mood_analytics = MoodAnalyticsComponent(
                        analytics_frame,
                        journal_service=self.journal_service
                    )
                    # Use pack instead of grid to avoid conflicts
                    if hasattr(self.mood_analytics, 'get_frame'):
                        self.mood_analytics.get_frame().pack(fill='both', expand=True, padx=10, pady=10)
                    else:
                        self.mood_analytics.pack(fill='both', expand=True, padx=10, pady=10)
                except Exception as e:
                    self.logger.error(f"Error creating mood analytics: {e}")
                    # Create placeholder using pack (not grid)
                    placeholder = ctk.CTkLabel(
                        analytics_frame,
                        text="📊 Analytics Dashboard\n\nMood tracking and weather correlations coming soon...",
                        font=ctk.CTkFont(size=16),
                        text_color="#B0B0B0"
                    )
                    placeholder.pack(expand=True, fill='both', padx=20, pady=50)
                    
            self.logger.info("Analytics tab created successfully with pack geometry")
            
        except Exception as e:
            self.logger.error(f"Failed to create analytics tab: {e}")
            # Fallback: simple placeholder
            try:
                analytics_frame = self.tabview.add("📈 Analytics")
                fallback_label = ctk.CTkLabel(analytics_frame, text="Analytics - Loading...")
                fallback_label.pack(expand=True)
            except:
                pass
    
    def _create_journal_tab(self) -> None:
        """Create journal tab with writing and management features."""
        journal_tab = self.tabview.add("📝 Journal")
        journal_tab.grid_rowconfigure(0, weight=1)
        journal_tab.grid_columnconfigure((0, 1), weight=1)
        
        # Left side - Journal writing
        try:
            self.weather_journal = WeatherJournal(
                journal_tab,
                weather_service=self.weather_service
            )
            self.weather_journal.grid(row=0, column=0, sticky="nsew", padx=(0, 5), pady=10)
        except Exception as e:
            self.logger.error(f"Error creating weather journal: {e}")
        
        # Right side - Journal management
        self._create_journal_management_section(journal_tab)
    
    def _create_journal_management_section(self, parent) -> None:
        """Create journal management section."""
        # Management container
        management_frame = ctk.CTkFrame(
            parent,
            fg_color="transparent"
        )
        management_frame.grid(row=0, column=1, sticky="nsew", padx=(5, 0), pady=10)
        management_frame.grid_rowconfigure((0, 1, 2), weight=1)
        
        # Journal search
        try:
            self.journal_search = JournalSearchComponent(
                management_frame,
                journal_service=self.journal_service
            )
            self.journal_search.grid(row=0, column=0, sticky="nsew", pady=(0, 5))
        except Exception as e:
            self.logger.error(f"Error creating journal search: {e}")
        
        # Journal calendar
        try:
            self.journal_calendar = JournalCalendarComponent(
                management_frame,
                journal_service=self.journal_service
            )
            self.journal_calendar.grid(row=1, column=0, sticky="nsew", pady=5)
        except Exception as e:
            self.logger.error(f"Error creating journal calendar: {e}")
        
        # Photo gallery
        try:
            self.photo_gallery = PhotoGalleryComponent(
                management_frame,
                photo_manager=self.photo_manager
            )
            self.photo_gallery.grid(row=2, column=0, sticky="nsew", pady=(5, 0))
        except Exception as e:
            self.logger.error(f"Error creating photo gallery: {e}")
    
    def _create_activities_tab(self) -> None:
        """Create activities tab with AI-powered suggestions."""
        activities_tab = self.tabview.add("🎯 Activities")
        activities_tab.grid_rowconfigure(0, weight=1)
        activities_tab.grid_columnconfigure(0, weight=1)
        
        try:
            self.activity_suggester = ActivitySuggester(
                activities_tab,
                weather_service=self.weather_service,
                config_service=self.config_service
            )
            self.activity_suggester.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        except Exception as e:
            self.logger.error(f"Error creating activity suggester: {e}")
            # Create placeholder
            placeholder = ctk.CTkLabel(
                activities_tab,
                text="Activity suggestions unavailable",
                font=(DataTerminalTheme.FONT_FAMILY, DataTerminalTheme.FONT_SIZE_LARGE),
                text_color=self.TEXT_SECONDARY
            )
            placeholder.grid(row=0, column=0)
    
    def _create_maps_tab(self) -> None:
        """Create maps tab with weather visualization."""
        maps_tab = self.tabview.add("🗺️ Maps")
        maps_tab.grid_rowconfigure(0, weight=1)
        maps_tab.grid_columnconfigure(0, weight=1)
        
        try:
            self.maps_component = MapsComponent(
                maps_tab,
                config_service=self.config_service
            )
            self.maps_component.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        except Exception as e:
            self.logger.error(f"Error creating maps component: {e}")
            # Create placeholder
            placeholder = ctk.CTkLabel(
                maps_tab,
                text="Maps unavailable",
                font=(DataTerminalTheme.FONT_FAMILY, DataTerminalTheme.FONT_SIZE_LARGE),
                text_color=self.TEXT_SECONDARY
            )
            placeholder.grid(row=0, column=0)
    
    def _create_settings_tab(self) -> None:
        """Create settings tab with API management."""
        settings_tab = self.tabview.add("⚙️ Settings")
        settings_tab.grid_rowconfigure(0, weight=1)
        settings_tab.grid_columnconfigure(0, weight=1)
        
        # Add secure API manager to settings tab
        if hasattr(self, 'secure_api_manager'):
            api_section = self.secure_api_manager.create_api_section(settings_tab)
            api_section.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
    
    def _on_timeframe_change(self, value: str) -> None:
        """Handle timeframe selector change."""
        self.chart_timeframe = value
        if hasattr(self, 'temperature_chart'):
            try:
                self.temperature_chart.update_timeframe(value)
            except Exception as e:
                self.logger.error(f"Error updating chart timeframe: {e}")