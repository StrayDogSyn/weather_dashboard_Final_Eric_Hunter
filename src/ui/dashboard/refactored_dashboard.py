"""Refactored Weather Dashboard

A clean, modular implementation of the main weather dashboard.
"""

import logging
from typing import Any, Dict, Optional

import customtkinter as ctk

from ...core.event_bus import EventTypes, get_event_bus, publish_event
from ...core.interfaces import IConfigurationService, IWeatherService, IJournalService, IActivityService
from ...models.weather_models import WeatherData
from ..components.base_component import ContainerComponent
from ..components.weather_display import WeatherDisplay
from ..theme import DataTerminalTheme


class RefactoredWeatherDashboard(ContainerComponent):
    """Refactored weather dashboard with clean architecture."""

    def __init__(
        self,
        config_service: IConfigurationService,
        weather_service: IWeatherService,
        journal_service: Optional[IJournalService] = None,
        activity_service: Optional[IActivityService] = None,
        **kwargs
    ):
        """Initialize the refactored dashboard.

        Args:
            config_service: Configuration service
            weather_service: Weather service
            journal_service: Journal service (optional)
            activity_service: Activity service (optional)
            **kwargs: Additional arguments
        """
        self.config_service = config_service
        self.weather_service = weather_service
        self.journal_service = journal_service
        self.activity_service = activity_service

        # State
        self.current_location = "London"
        self.temp_unit = "C"
        self.auto_refresh_enabled = True
        self.refresh_interval = 300000  # 5 minutes

        # UI Components
        self.tabview = None
        self.search_entry = None
        self.status_bar = None
        self.weather_display = None

        super().__init__(**kwargs)

    def _setup_component(self, **kwargs) -> None:
        """Setup component-specific initialization."""
        # Configure appearance
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("dark-blue")

        # Apply theme
        self.theme = DataTerminalTheme()
        self.theme.apply_theme()

    def _subscribe_to_events(self) -> None:
        """Subscribe to dashboard events."""
        super()._subscribe_to_events()
        self.event_bus.subscribe(EventTypes.LOCATION_CHANGED, self._on_location_changed)
        self.event_bus.subscribe(EventTypes.THEME_CHANGED, self._on_theme_changed)
        self.event_bus.subscribe(EventTypes.ERROR_OCCURRED, self._on_error_occurred)

    def _create_widget(self) -> ctk.CTk:
        """Create the main dashboard widget.

        Returns:
            The main window
        """
        # Create main window
        self.main_window = ctk.CTk()
        self.main_window.title("Weather Dashboard")
        self.main_window.geometry("1400x900")
        self.main_window.minsize(1200, 800)

        # Configure grid
        self.main_window.grid_columnconfigure(0, weight=1)
        self.main_window.grid_rowconfigure(1, weight=1)

        # Create UI sections
        self._create_header()
        self._create_main_content()
        self._create_status_bar()

        # Setup keyboard shortcuts
        self._setup_keyboard_shortcuts()

        # Start auto-refresh
        self._start_auto_refresh()

        return self.main_window

    def _create_header(self) -> None:
        """Create the header section."""
        header_frame = ctk.CTkFrame(self.main_window)
        header_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=5)

        # Title
        title_label = ctk.CTkLabel(
            header_frame,
            text="🌤️ Weather Dashboard",
            font=("Arial", 20, "bold")
        )
        title_label.pack(side="left", padx=10, pady=5)

        # Search section
        search_frame = ctk.CTkFrame(header_frame)
        search_frame.pack(side="right", padx=10, pady=5)

        # Search entry
        self.search_entry = ctk.CTkEntry(
            search_frame,
            placeholder_text="Search location...",
            width=200
        )
        self.search_entry.pack(side="left", padx=5)
        self.search_entry.bind("<Return>", self._on_search_entered)

        # Search button
        search_button = ctk.CTkButton(
            search_frame,
            text="Search",
            command=self._on_search_clicked
        )
        search_button.pack(side="left", padx=5)

        # Temperature unit toggle
        unit_button = ctk.CTkButton(
            search_frame,
            text=f"°{self.temp_unit}",
            width=50,
            command=self._toggle_temperature_unit
        )
        unit_button.pack(side="left", padx=5)

    def _create_main_content(self) -> None:
        """Create the main content area."""
        content_frame = ctk.CTkFrame(self.main_window)
        content_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)

        # Create tabview
        self.tabview = ctk.CTkTabview(content_frame)
        self.tabview.pack(fill="both", expand=True, padx=10, pady=10)

        # Create tabs
        self._create_weather_tab()
        self._create_journal_tab()
        self._create_activities_tab()
        self._create_settings_tab()

    def _create_weather_tab(self) -> None:
        """Create the weather tab."""
        weather_tab = self.tabview.add("Weather")

        # Create weather display component
        self.weather_display = WeatherDisplay(
            parent=weather_tab,
            temp_unit=self.temp_unit
        )
        weather_widget = self.weather_display.create()
        weather_widget.pack(fill="both", expand=True, padx=10, pady=10)

        # Add to child components
        self.add_component("weather_display", self.weather_display)

    def _create_journal_tab(self) -> None:
        """Create the journal tab."""
        journal_tab = self.tabview.add("Journal")

        # Placeholder for journal functionality
        placeholder_label = ctk.CTkLabel(
            journal_tab,
            text="Journal functionality coming soon...",
            font=("Arial", 16)
        )
        placeholder_label.pack(expand=True)

    def _create_activities_tab(self) -> None:
        """Create the activities tab."""
        activities_tab = self.tabview.add("Activities")

        # Placeholder for activities functionality
        placeholder_label = ctk.CTkLabel(
            activities_tab,
            text="Activity suggestions coming soon...",
            font=("Arial", 16)
        )
        placeholder_label.pack(expand=True)

    def _create_settings_tab(self) -> None:
        """Create the settings tab."""
        settings_tab = self.tabview.add("Settings")

        # Settings content
        settings_frame = ctk.CTkFrame(settings_tab)
        settings_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Auto-refresh setting
        refresh_frame = ctk.CTkFrame(settings_frame)
        refresh_frame.pack(fill="x", padx=10, pady=5)

        refresh_label = ctk.CTkLabel(
            refresh_frame,
            text="Auto-refresh:",
            font=("Arial", 14, "bold")
        )
        refresh_label.pack(side="left", padx=10, pady=5)

        self.refresh_var = ctk.BooleanVar(value=self.auto_refresh_enabled)
        refresh_switch = ctk.CTkSwitch(
            refresh_frame,
            text="",
            variable=self.refresh_var,
            command=self._toggle_auto_refresh
        )
        refresh_switch.pack(side="right", padx=10, pady=5)

        # Theme setting
        theme_frame = ctk.CTkFrame(settings_frame)
        theme_frame.pack(fill="x", padx=10, pady=5)

        theme_label = ctk.CTkLabel(
            theme_frame,
            text="Theme:",
            font=("Arial", 14, "bold")
        )
        theme_label.pack(side="left", padx=10, pady=5)

        theme_button = ctk.CTkButton(
            theme_frame,
            text="Toggle Theme",
            command=self._toggle_theme
        )
        theme_button.pack(side="right", padx=10, pady=5)

    def _create_status_bar(self) -> None:
        """Create the status bar."""
        self.status_bar = ctk.CTkFrame(self.main_window)
        self.status_bar.grid(row=2, column=0, sticky="ew", padx=10, pady=5)

        # Status label
        self.status_label = ctk.CTkLabel(
            self.status_bar,
            text="Ready",
            font=("Arial", 10)
        )
        self.status_label.pack(side="left", padx=10, pady=2)

        # Time label
        self.time_label = ctk.CTkLabel(
            self.status_bar,
            text="",
            font=("Arial", 10)
        )
        self.time_label.pack(side="right", padx=10, pady=2)

        # Update time
        self._update_time()

    def _setup_keyboard_shortcuts(self) -> None:
        """Setup keyboard shortcuts."""
        self.main_window.bind("<Control-r>", lambda e: self._refresh_weather())
        self.main_window.bind("<Control-j>", lambda e: self.tabview.set("Journal"))
        self.main_window.bind("<Control-w>", lambda e: self.tabview.set("Weather"))
        self.main_window.bind("<Control-a>", lambda e: self.tabview.set("Activities"))
        self.main_window.bind("<Control-s>", lambda e: self.tabview.set("Settings"))
        self.main_window.bind("<F5>", lambda e: self._refresh_weather())
        self.main_window.bind("<Escape>", lambda e: self.search_entry.delete(0, "end"))

    def _start_auto_refresh(self) -> None:
        """Start auto-refresh functionality."""
        if self.auto_refresh_enabled:
            self._schedule_refresh()

    def _schedule_refresh(self) -> None:
        """Schedule the next weather refresh."""
        if self.auto_refresh_enabled and not self._is_destroyed:
            self.main_window.after(self.refresh_interval, self._refresh_weather)

    def _refresh_weather(self) -> None:
        """Refresh weather data."""
        try:
            self._update_status("Loading weather data...")
            publish_event(EventTypes.WEATHER_LOADING)

            # Get weather data
            weather_data = self.weather_service.get_current_weather(self.current_location)

            if weather_data:
                publish_event(EventTypes.WEATHER_UPDATED, weather_data)
                self._update_status("Weather data updated")
            else:
                publish_event(EventTypes.WEATHER_ERROR, {"error": "Failed to load weather data"})
                self._update_status("Failed to load weather data")

        except Exception as e:
            self.logger.error(f"Error refreshing weather: {e}")
            publish_event(EventTypes.WEATHER_ERROR, {"error": str(e)})
            self._update_status("Error loading weather data")
        finally:
            # Schedule next refresh
            self._schedule_refresh()

    def _on_search_entered(self, event: Any) -> None:
        """Handle search entry."""
        self._perform_search()

    def _on_search_clicked(self) -> None:
        """Handle search button click."""
        self._perform_search()

    def _perform_search(self) -> None:
        """Perform location search."""
        query = self.search_entry.get().strip()
        if not query:
            return

        try:
            self._update_status(f"Searching for {query}...")

            # Search for location
            locations = self.weather_service.search_locations(query)

            if locations:
                # Use first result
                location = locations[0]
                self.current_location = location.get('name', query)
                self._update_status(f"Location changed to {self.current_location}")
                publish_event(EventTypes.LOCATION_CHANGED, {"location": self.current_location})

                # Refresh weather
                self._refresh_weather()
            else:
                self._update_status("Location not found")

        except Exception as e:
            self.logger.error(f"Error searching location: {e}")
            self._update_status("Error searching location")

    def _toggle_temperature_unit(self) -> None:
        """Toggle temperature unit."""
        self.temp_unit = "F" if self.temp_unit == "C" else "C"

        # Update weather display
        if self.weather_display:
            self.weather_display.toggle_temperature_unit()

        self._update_status(f"Temperature unit changed to °{self.temp_unit}")

    def _toggle_auto_refresh(self) -> None:
        """Toggle auto-refresh."""
        self.auto_refresh_enabled = self.refresh_var.get()

        if self.auto_refresh_enabled:
            self._start_auto_refresh()
            publish_event(EventTypes.AUTO_REFRESH_STARTED)
            self._update_status("Auto-refresh enabled")
        else:
            publish_event(EventTypes.AUTO_REFRESH_STOPPED)
            self._update_status("Auto-refresh disabled")

    def _toggle_theme(self) -> None:
        """Toggle theme."""
        current_theme = ctk.get_appearance_mode()
        new_theme = "Light" if current_theme == "Dark" else "Dark"
        ctk.set_appearance_mode(new_theme)

        publish_event(EventTypes.THEME_CHANGED, {"theme": new_theme})
        self._update_status(f"Theme changed to {new_theme}")

    def _update_status(self, message: str) -> None:
        """Update status bar message.

        Args:
            message: Status message
        """
        if self.status_label:
            self.status_label.configure(text=message)

    def _update_time(self) -> None:
        """Update time display."""
        from datetime import datetime

        if self.time_label:
            current_time = datetime.now().strftime("%H:%M:%S")
            self.time_label.configure(text=current_time)

        # Update every second
        if not self._is_destroyed:
            self.main_window.after(1000, self._update_time)

    def _on_location_changed(self, data: Dict[str, Any]) -> None:
        """Handle location change event.

        Args:
            data: Location change data
        """
        location = data.get('location', self.current_location)
        self.current_location = location
        self._refresh_weather()

    def _on_theme_changed(self, data: Dict[str, Any]) -> None:
        """Handle theme change event.

        Args:
            data: Theme change data
        """
        # Theme changes are handled automatically by CustomTkinter
        pass

    def _on_error_occurred(self, data: Dict[str, Any]) -> None:
        """Handle error event.

        Args:
            data: Error data
        """
        error_message = data.get('error', 'Unknown error')
        component = data.get('component', 'Unknown')
        self.logger.error(f"Error in {component}: {error_message}")
        self._update_status(f"Error: {error_message}")

    def _get_main_widget(self) -> Optional[ctk.CTk]:
        """Get the main widget.

        Returns:
            The main window
        """
        return self.main_window

    def run(self) -> None:
        """Run the dashboard."""
        if self.main_window:
            self.main_window.mainloop()

    def get_current_location(self) -> str:
        """Get current location.

        Returns:
            Current location
        """
        return self.current_location

    def get_temperature_unit(self) -> str:
        """Get current temperature unit.

        Returns:
            Current temperature unit
        """
        return self.temp_unit

    def is_auto_refresh_enabled(self) -> bool:
        """Check if auto-refresh is enabled.

        Returns:
            True if auto-refresh is enabled
        """
        return self.auto_refresh_enabled
