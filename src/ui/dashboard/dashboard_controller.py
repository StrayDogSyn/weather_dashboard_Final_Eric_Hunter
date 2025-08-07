"""Dashboard Controller for Weather Dashboard.

Main orchestration class that coordinates all tab managers and handles
the primary application flow.
"""

import logging


from src.ui.safe_widgets import SafeCTkTabview
from src.utils.error_wrapper import ensure_main_thread
from src.ui.components.common.header import HeaderComponent
from src.ui.components.common.status_bar_component import StatusBarComponent
from src.ui.components.journal_tab_manager import JournalTabManager
from src.ui.dashboard.activities_tab_manager import ActivitiesTabManager
from src.ui.dashboard.base_dashboard import BaseDashboard
from src.ui.dashboard.comparison_tab_manager import ComparisonTabManager, MLComparisonTabManager
from src.ui.dashboard.maps_tab_manager import MapsTabManager
from src.ui.dashboard.settings_tab_manager import SettingsTabManager
from src.ui.dashboard.weather_tab_manager import WeatherTabManager


class DashboardController(BaseDashboard):
    """Main dashboard controller that orchestrates all components."""

    def __init__(self, config_service=None):
        """Initialize dashboard controller.

        Args:
            config_service: Configuration service instance
        """
        super().__init__(config_service)

        # Tab managers
        self.weather_tab_manager = None
        self.settings_tab_manager = None
        self.activities_tab_manager = None
        self.comparison_tab_manager = None
        self.ml_comparison_tab_manager = None
        self.journal_tab_manager = None
        self.maps_tab_manager = None

        # UI components
        self.header_component = None
        self.status_bar_component = None

        # Initialize UI
        self._create_main_interface()

    def _create_main_interface(self):
        """Create the main dashboard interface."""
        self._create_header_component()
        self._create_main_content()
        self._create_status_bar_component()

    def _create_main_content(self):
        """Create tab view and initialize tab managers."""
        self.tabview = SafeCTkTabview(self, corner_radius=10)
        self.tabview.grid(row=1, column=0, sticky="nsew", padx=20, pady=10)

        # Create tabs
        self.weather_tab = self.tabview.add("Weather")
        self.comparison_tab = self.tabview.add("🏙️ Team Compare")
        self.ml_comparison_tab = self.tabview.add("🧠 AI Analysis")
        self.activities_tab = self.tabview.add("Activities")
        self.journal_tab = self.tabview.add("📝 Journal")
        self.maps_tab = self.tabview.add("Maps")
        self.settings_tab = self.tabview.add("Settings")

        # Configure tab grids
        self._configure_tab_grids()

        # Initialize tab managers
        self._initialize_tab_managers()

        # Create tab content
        self._create_all_tabs()

    def _configure_tab_grids(self):
        """Configure grid layout for all tabs."""
        tabs = [
            self.weather_tab,
            self.comparison_tab,
            self.ml_comparison_tab,
            self.activities_tab,
            self.journal_tab,
            self.maps_tab,
            self.settings_tab,
        ]

        for tab in tabs:
            tab.grid_columnconfigure(0, weight=1)
            tab.grid_rowconfigure(0, weight=1)

    def _initialize_tab_managers(self):
        """Initialize all tab managers with required services."""
        self.weather_tab_manager = WeatherTabManager(self, self.weather_tab)

        self.settings_tab_manager = SettingsTabManager(
            self, self.config_service, self.weather_service
        )

        self.activities_tab_manager = ActivitiesTabManager(
            self, self.activity_service, self.cache_manager, logging.getLogger(__name__)
        )

        self.comparison_tab_manager = ComparisonTabManager(
            self.comparison_tab, self.weather_service, self.github_service
        )

        self.ml_comparison_tab_manager = MLComparisonTabManager(
            self.ml_comparison_tab, self.weather_service, self.github_service
        )

        self.journal_tab_manager = JournalTabManager(
            self.journal_tab, self.weather_service, self.theme_manager
        )

        self.maps_tab_manager = MapsTabManager(
            self.maps_tab, self.weather_service, self.config_service
        )

    def _create_all_tabs(self):
        """Create content for all tabs using their respective managers."""
        # Weather tab content is created automatically by WeatherTabManager in constructor
        # No need to call create_weather_tab as it doesn't exist

        # Create other tab contents
        self.activities_tab_manager.create_activities_tab(self.activities_tab)
        self.comparison_tab_manager.create_comparison_tab()
        self.settings_tab_manager.create_settings_tab(self.settings_tab)
        self._create_journal_tab()
        self._create_maps_tab()

    def _create_journal_tab(self):
        """Create journal tab content."""
        if self.journal_tab_manager:
            self.journal_tab_manager.create_journal_tab()

    def _create_maps_tab(self):
        """Create maps tab content using MapsTabManager."""
        if self.maps_tab_manager:
            # Maps tab content is created automatically by MapsTabManager in constructor
            pass

    def _create_header_component(self):
        """Create the header component."""
        self.header_component = HeaderComponent(
            self,
            on_search_callback=self._on_location_selected,
            height=80,
            fg_color=("#f8fafc", "#1e293b"),
        )
        self.header_component.grid(row=0, column=0, sticky="ew", padx=0, pady=0)

    def _create_status_bar_component(self):
        """Create the status bar component."""
        self.status_bar_component = StatusBarComponent(
            self, height=30, fg_color=("#f1f5f9", "#0f172a")
        )
        self.status_bar_component.grid(row=2, column=0, sticky="ew", padx=0, pady=0)

    def _on_location_selected(self, location_result):
        """Handle location selection from search.

        Args:
            location_result: Dictionary with location information
        """
        # Update current location in header
        if self.header_component:
            self.header_component.update_current_location(
                location_result.get("display_name", "Unknown")
            )

        # Update status
        if self.status_bar_component:
            self.status_bar_component.show_loading(
                f"Loading weather for {location_result.get('display_name', 'location')}..."
            )

        # Trigger weather update (this would typically call the weather service)
        # For now, just update the status
        if self.status_bar_component:
            self.timer_manager.schedule_once(
                'clear_location_status',
                2000,
                lambda: self.status_bar_component.clear_status()
            )

    @ensure_main_thread
    def update_weather_data(self, weather_data):
        """Update weather data across all relevant tabs.

        Args:
            weather_data: Weather data dictionary
        """
        if self.weather_tab_manager:
            self.weather_tab_manager.update_weather_display(weather_data)
        if self.activities_tab_manager:
            self.activities_tab_manager.update_activity_suggestions(weather_data)

        # Update status bar
        if self.status_bar_component:
            self.status_bar_component.show_success("Weather data updated")
            self.timer_manager.schedule_once(
                'clear_weather_status',
                3000,
                lambda: self.status_bar_component.clear_status()
            )

    def update_status(self, message, status_type="info"):
        """Update the status bar message.

        Args:
            message (str): Status message
            status_type (str): Type of status - 'info', 'success', 'warning', 'error'
        """
        if self.status_bar_component:
            self.status_bar_component.update_status(message, status_type)

    def update_connection_status(self, is_connected, message=""):
        """Update connection status in status bar.

        Args:
            is_connected (bool): Whether connected
            message (str): Optional custom message
        """
        if self.status_bar_component:
            self.status_bar_component.update_connection_status(is_connected, message)

    def cleanup(self):
        """Clean up resources."""
        if self.status_bar_component:
            self.status_bar_component.cleanup()
        super().cleanup() if hasattr(super(), "cleanup") else None
