#!/usr/bin/env python3
"""
Main Dashboard UI - Professional Weather Dashboard Interface

This module implements the main dashboard interface that demonstrates:
- Advanced glassmorphic design implementation
- Professional layout management with responsive design
- Component composition and orchestration
- Real-time data visualization integration
- Modern UI/UX patterns and accessibility
- Weather-responsive theming and animations
"""

import customtkinter as ctk
import tkinter as tk
from tkinter import ttk
from typing import Dict, Any, Optional, Callable, List
from datetime import datetime, timedelta
import threading
from enum import Enum
from dataclasses import dataclass

from ..utils.logger import LoggerMixin
from .theme_manager import ThemeManager, WeatherTheme, GlassEffect
from .components.base_components import (
    GlassFrame, GlassButton, GlassLabel, GlassEntry, GlassProgressBar,
    ComponentSize, create_glass_card, create_glass_toolbar
)
from ..core.app_controller import AppController, AppState
from ..services.weather_service import WeatherData, ForecastData


class DashboardSection(Enum):
    """
    Dashboard section identifiers for navigation and layout management.

    This enum supports modular dashboard design with clear
    section separation and navigation.
    """
    OVERVIEW = "overview"
    TEMPERATURE_GRAPH = "temperature_graph"
    WEATHER_JOURNAL = "weather_journal"
    ACTIVITY_SUGGESTER = "activity_suggester"
    TEAM_COLLABORATION = "team_collaboration"
    SETTINGS = "settings"


@dataclass
class DashboardConfig:
    """
    Configuration for dashboard layout and behavior.

    This dataclass demonstrates professional configuration
    management with type safety and default values.
    """
    window_title: str = "Weather Dashboard - CodeFront Edition"
    window_size: tuple[int, int] = (1400, 900)
    min_window_size: tuple[int, int] = (1000, 700)
    auto_refresh_interval: int = 300  # seconds
    animation_duration: int = 300  # milliseconds
    enable_animations: bool = True
    enable_sound_effects: bool = False
    default_location: str = "New York, NY"
    theme_auto_update: bool = True


class WeatherDashboardUI(ctk.CTk, LoggerMixin):
    """
    Main Weather Dashboard UI Class.

    This class orchestrates the entire dashboard interface,
    demonstrating advanced UI architecture patterns including:
    - Component composition and lifecycle management
    - Event-driven UI updates and state synchronization
    - Responsive layout with glassmorphic design
    - Professional error handling and user feedback
    - Accessibility and usability best practices
    """

    def __init__(self, app_controller: AppController, config: Optional[DashboardConfig] = None):
        super().__init__()

        # Initialize core dependencies
        self.app_controller = app_controller
        self.config = config or DashboardConfig()
        self.theme_manager = ThemeManager()

        # UI state management
        self.current_section = DashboardSection.OVERVIEW
        self.is_loading = False
        self.last_weather_update = None
        self.animation_queue: List[Callable] = []

        # Component references
        self.sidebar: Optional[GlassFrame] = None
        self.main_content: Optional[GlassFrame] = None
        self.status_bar: Optional[GlassFrame] = None
        self.section_frames: Dict[DashboardSection, GlassFrame] = {}

        # Data references
        self.current_weather: Optional[WeatherData] = None
        self.forecast_data: Optional[List[ForecastData]] = None

        # Initialize UI
        self._setup_window()
        self._setup_layout()
        self._setup_event_bindings()
        self._setup_auto_refresh()

        # Subscribe to app controller events
        self._subscribe_to_events()

        self.logger.info("Weather Dashboard UI initialized successfully")

    def _setup_window(self) -> None:
        """
        Configure main window properties and styling.

        This method demonstrates professional window setup
        with proper sizing, theming, and accessibility.
        """
        # Window configuration
        self.title(self.config.window_title)
        self.geometry(f"{self.config.window_size[0]}x{self.config.window_size[1]}")
        self.minsize(*self.config.min_window_size)

        # Center window on screen
        self._center_window()

        # Set appearance mode and color theme
        ctk.set_appearance_mode("dark")  # Supports glassmorphic design
        ctk.set_default_color_theme("blue")

        # Configure window icon (if available)
        try:
            self.iconbitmap("assets/images/weather_icon.ico")
        except Exception:
            self.logger.debug("Window icon not found, using default")

        # Set up window close protocol
        self.protocol("WM_DELETE_WINDOW", self._on_window_close)

        self.logger.debug("Window setup completed")

    def _center_window(self) -> None:
        """
        Center the window on the screen.

        This method provides professional window positioning
        for optimal user experience.
        """
        self.update_idletasks()

        # Get screen dimensions
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()

        # Calculate center position
        x = (screen_width - self.config.window_size[0]) // 2
        y = (screen_height - self.config.window_size[1]) // 2

        self.geometry(f"{self.config.window_size[0]}x{self.config.window_size[1]}+{x}+{y}")

    def _setup_layout(self) -> None:
        """
        Create and configure the main dashboard layout.

        This method demonstrates advanced layout management
        with responsive design and glassmorphic styling.
        """
        # Configure grid weights for responsive design
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Create main layout sections
        self._create_sidebar()
        self._create_main_content()
        self._create_status_bar()

        # Initialize with overview section
        self._show_section(DashboardSection.OVERVIEW)

        self.logger.debug("Layout setup completed")

    def _create_sidebar(self) -> None:
        """
        Create the navigation sidebar with glassmorphic styling.

        This method demonstrates professional navigation design
        with visual hierarchy and interactive feedback.
        """
        # Create sidebar frame
        self.sidebar = GlassFrame(
            self,
            glass_effect=GlassEffect(
                background_opacity=0.15,
                border_opacity=0.3,
                blur_radius=20,
                corner_radius=0
            ),
            size=ComponentSize.LARGE
        )
        self.sidebar.grid(row=0, column=0, sticky="nsew", padx=(0, 1))
        self.sidebar.configure(width=280)

        # Sidebar header
        header_frame = GlassFrame(
            self.sidebar,
            glass_effect=GlassEffect(
                background_opacity=0.1,
                border_opacity=0.2,
                corner_radius=10
            )
        )
        header_frame.pack(fill="x", padx=15, pady=(15, 10))

        # App title
        title_label = GlassLabel(
            header_frame,
            text="CodeFront Initialized",
            text_style="heading",
            size=ComponentSize.LARGE
        )
        title_label.pack(pady=15)

        # Current time display
        self.time_label = GlassLabel(
            header_frame,
            text=self._get_current_time(),
            text_style="caption",
            size=ComponentSize.MEDIUM
        )
        self.time_label.pack(pady=(0, 15))

        # Navigation buttons
        nav_frame = GlassFrame(self.sidebar)
        nav_frame.pack(fill="x", padx=15, pady=10)

        # Define navigation items
        nav_items = [
            {"section": DashboardSection.OVERVIEW, "text": "🏠 Overview", "icon": None},
            {"section": DashboardSection.TEMPERATURE_GRAPH, "text": "📊 Temperature Graph", "icon": None},
            {"section": DashboardSection.WEATHER_JOURNAL, "text": "📝 Weather Journal", "icon": None},
            {"section": DashboardSection.ACTIVITY_SUGGESTER, "text": "🎯 Activity Suggester", "icon": None},
            {"section": DashboardSection.TEAM_COLLABORATION, "text": "👥 Team Collaboration", "icon": None},
            {"section": DashboardSection.SETTINGS, "text": "⚙️ Settings", "icon": None}
        ]

        self.nav_buttons: Dict[DashboardSection, GlassButton] = {}

        for item in nav_items:
            button = GlassButton(
                nav_frame,
                text=item["text"],
                size=ComponentSize.MEDIUM,
                command=lambda s=item["section"]: self._show_section(s)
            )
            button.pack(fill="x", pady=2)
            self.nav_buttons[item["section"]] = button

        # Weather summary in sidebar
        self._create_weather_summary()

        # Quick actions
        self._create_quick_actions()

    def _create_weather_summary(self) -> None:
        """
        Create weather summary widget for sidebar.

        This method demonstrates real-time data display
        with glassmorphic styling and responsive updates.
        """
        summary_frame = GlassFrame(
            self.sidebar,
            glass_effect=GlassEffect(
                background_opacity=0.1,
                border_opacity=0.2,
                corner_radius=10
            )
        )
        summary_frame.pack(fill="x", padx=15, pady=10)

        # Summary title
        summary_title = GlassLabel(
            summary_frame,
            text="Current Weather",
            text_style="subheading",
            size=ComponentSize.MEDIUM
        )
        summary_title.pack(pady=(10, 5))

        # Weather data labels
        self.weather_location_label = GlassLabel(
            summary_frame,
            text="Loading location...",
            text_style="normal",
            size=ComponentSize.SMALL
        )
        self.weather_location_label.pack(pady=2)

        self.weather_temp_label = GlassLabel(
            summary_frame,
            text="--°F",
            text_style="heading",
            size=ComponentSize.LARGE
        )
        self.weather_temp_label.pack(pady=5)

        self.weather_condition_label = GlassLabel(
            summary_frame,
            text="Loading...",
            text_style="normal",
            size=ComponentSize.MEDIUM
        )
        self.weather_condition_label.pack(pady=(0, 10))

        # Last update time
        self.last_update_label = GlassLabel(
            summary_frame,
            text="Last updated: Never",
            text_style="caption",
            size=ComponentSize.SMALL
        )
        self.last_update_label.pack(pady=(0, 10))

    def _create_quick_actions(self) -> None:
        """
        Create quick action buttons in sidebar.

        This method demonstrates action-oriented UI design
        with immediate user feedback and functionality.
        """
        actions_frame = GlassFrame(self.sidebar)
        actions_frame.pack(fill="x", padx=15, pady=10)

        actions_title = GlassLabel(
            actions_frame,
            text="Quick Actions",
            text_style="subheading",
            size=ComponentSize.MEDIUM
        )
        actions_title.pack(pady=(10, 5))

        # Refresh button
        self.refresh_button = GlassButton(
            actions_frame,
            text="🔄 Refresh Weather",
            size=ComponentSize.MEDIUM,
            command=self._refresh_weather_data
        )
        self.refresh_button.pack(fill="x", pady=2)

        # Location search button
        self.location_button = GlassButton(
            actions_frame,
            text="📍 Change Location",
            size=ComponentSize.MEDIUM,
            command=self._show_location_dialog
        )
        self.location_button.pack(fill="x", pady=2)

        # Export data button
        self.export_button = GlassButton(
            actions_frame,
            text="💾 Export Data",
            size=ComponentSize.MEDIUM,
            command=self._export_weather_data
        )
        self.export_button.pack(fill="x", pady=2)

    def _create_main_content(self) -> None:
        """
        Create the main content area with section management.

        This method demonstrates advanced content management
        with dynamic section loading and smooth transitions.
        """
        # Main content frame
        self.main_content = GlassFrame(
            self,
            glass_effect=GlassEffect(
                background_opacity=0.05,
                border_opacity=0.1,
                blur_radius=30,
                corner_radius=0
            ),
            size=ComponentSize.EXTRA_LARGE
        )
        self.main_content.grid(row=0, column=1, sticky="nsew", padx=(1, 0))

        # Content header
        self.content_header = GlassFrame(
            self.main_content,
            glass_effect=GlassEffect(
                background_opacity=0.1,
                border_opacity=0.2,
                corner_radius=10
            )
        )
        self.content_header.pack(fill="x", padx=20, pady=(20, 10))

        # Section title
        self.section_title = GlassLabel(
            self.content_header,
            text="Dashboard Overview",
            text_style="heading",
            size=ComponentSize.EXTRA_LARGE
        )
        self.section_title.pack(side="left", padx=20, pady=15)

        # Loading indicator
        self.loading_progress = GlassProgressBar(
            self.content_header,
            size=ComponentSize.MEDIUM
        )
        self.loading_progress.pack(side="right", padx=20, pady=15)
        self.loading_progress.pack_forget()  # Hidden by default

        # Content area for sections
        self.content_area = GlassFrame(
            self.main_content,
            glass_effect=GlassEffect(
                background_opacity=0.02,
                border_opacity=0.05,
                corner_radius=15
            )
        )
        self.content_area.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        # Initialize section frames
        self._initialize_section_frames()

    def _create_status_bar(self) -> None:
        """
        Create the status bar with system information.

        This method demonstrates professional status display
        with real-time system monitoring and user feedback.
        """
        self.status_bar = GlassFrame(
            self,
            glass_effect=GlassEffect(
                background_opacity=0.1,
                border_opacity=0.2,
                corner_radius=0
            )
        )
        self.status_bar.grid(row=1, column=0, columnspan=2, sticky="ew")
        self.status_bar.configure(height=30)

        # Status message
        self.status_label = GlassLabel(
            self.status_bar,
            text="Ready",
            text_style="caption",
            size=ComponentSize.SMALL
        )
        self.status_label.pack(side="left", padx=10, pady=5)

        # Connection status
        self.connection_label = GlassLabel(
            self.status_bar,
            text="🟢 Connected",
            text_style="caption",
            size=ComponentSize.SMALL
        )
        self.connection_label.pack(side="right", padx=10, pady=5)

    def _initialize_section_frames(self) -> None:
        """
        Initialize frames for each dashboard section.

        This method demonstrates modular UI architecture
        with lazy loading and efficient memory management.
        """
        for section in DashboardSection:
            frame = GlassFrame(
                self.content_area,
                glass_effect=GlassEffect(
                    background_opacity=0.03,
                    border_opacity=0.1,
                    corner_radius=10
                )
            )
            # Don't pack yet - will be shown when selected
            self.section_frames[section] = frame

        # Create initial content for each section
        self._create_overview_content()
        self._create_placeholder_content()

    def _create_overview_content(self) -> None:
        """
        Create content for the overview section.

        This method demonstrates dashboard overview design
        with key metrics and quick access to features.
        """
        overview_frame = self.section_frames[DashboardSection.OVERVIEW]

        # Welcome message
        welcome_label = GlassLabel(
            overview_frame,
            text=f"Welcome to your Weather Dashboard",
            text_style="heading",
            size=ComponentSize.LARGE
        )
        welcome_label.pack(pady=(30, 10))

        # Current date and time
        datetime_label = GlassLabel(
            overview_frame,
            text=datetime.now().strftime("%A, %B %d, %Y at %I:%M %p"),
            text_style="normal",
            size=ComponentSize.MEDIUM
        )
        datetime_label.pack(pady=(0, 30))

        # Quick stats grid
        stats_frame = GlassFrame(overview_frame)
        stats_frame.pack(fill="x", padx=50, pady=20)

        # Configure grid for stats
        for i in range(3):
            stats_frame.grid_columnconfigure(i, weight=1)

        # Create stat cards
        self._create_stat_card(stats_frame, "Today's High", "--°F", 0, 0)
        self._create_stat_card(stats_frame, "Current Humidity", "--%", 0, 1)
        self._create_stat_card(stats_frame, "Wind Speed", "-- mph", 0, 2)

        # Feature highlights
        features_frame = GlassFrame(overview_frame)
        features_frame.pack(fill="x", padx=50, pady=30)

        features_title = GlassLabel(
            features_frame,
            text="Dashboard Features",
            text_style="subheading",
            size=ComponentSize.LARGE
        )
        features_title.pack(pady=(20, 10))

        # Feature buttons
        feature_buttons_frame = GlassFrame(features_frame)
        feature_buttons_frame.pack(pady=20)

        feature_buttons = [
            {"text": "📊 View Temperature Trends", "section": DashboardSection.TEMPERATURE_GRAPH},
            {"text": "📝 Add Journal Entry", "section": DashboardSection.WEATHER_JOURNAL},
            {"text": "🎯 Get Activity Suggestions", "section": DashboardSection.ACTIVITY_SUGGESTER}
        ]

        for button_config in feature_buttons:
            button = GlassButton(
                feature_buttons_frame,
                text=button_config["text"],
                size=ComponentSize.LARGE,
                command=lambda s=button_config["section"]: self._show_section(s)
            )
            button.pack(pady=5)

    def _create_stat_card(self, parent, title: str, value: str, row: int, col: int) -> None:
        """
        Create a statistics card widget.

        Args:
            parent: Parent widget
            title: Card title
            value: Card value
            row: Grid row
            col: Grid column
        """
        card = create_glass_card(parent, title, size=ComponentSize.MEDIUM)
        card.grid(row=row, column=col, padx=10, pady=10, sticky="ew")

        value_label = GlassLabel(
            card,
            text=value,
            text_style="heading",
            size=ComponentSize.LARGE
        )
        value_label.pack(pady=(10, 20))

    def _create_placeholder_content(self) -> None:
        """
        Create placeholder content for sections not yet implemented.

        This method demonstrates professional development practices
        with clear user communication about feature status.
        """
        placeholder_sections = [
            DashboardSection.TEMPERATURE_GRAPH,
            DashboardSection.WEATHER_JOURNAL,
            DashboardSection.ACTIVITY_SUGGESTER,
            DashboardSection.TEAM_COLLABORATION,
            DashboardSection.SETTINGS
        ]

        for section in placeholder_sections:
            frame = self.section_frames[section]

            # Section title
            title = section.value.replace('_', ' ').title()
            title_label = GlassLabel(
                frame,
                text=f"{title} - Coming Soon",
                text_style="heading",
                size=ComponentSize.EXTRA_LARGE
            )
            title_label.pack(pady=(50, 20))

            # Description
            descriptions = {
                DashboardSection.TEMPERATURE_GRAPH: "Interactive temperature visualization with historical data and trends.",
                DashboardSection.WEATHER_JOURNAL: "Personal weather journal with rich text entries and search capabilities.",
                DashboardSection.ACTIVITY_SUGGESTER: "AI-powered activity recommendations based on current weather conditions.",
                DashboardSection.TEAM_COLLABORATION: "Share weather data and collaborate with your team members.",
                DashboardSection.SETTINGS: "Customize your dashboard preferences and API configurations."
            }

            desc_label = GlassLabel(
                frame,
                text=descriptions.get(section, "Feature description coming soon."),
                text_style="normal",
                size=ComponentSize.MEDIUM
            )
            desc_label.pack(pady=(0, 30), padx=50)

            # Progress indicator
            progress_label = GlassLabel(
                frame,
                text="🚧 Under Development",
                text_style="caption",
                size=ComponentSize.MEDIUM
            )
            progress_label.pack(pady=10)

    def _setup_event_bindings(self) -> None:
        """
        Set up event bindings for the dashboard.

        This method demonstrates comprehensive event handling
        for responsive user interactions and system events.
        """
        # Window events
        self.bind("<Configure>", self._on_window_resize)
        self.bind("<FocusIn>", self._on_window_focus)

        # Keyboard shortcuts
        self.bind("<Control-r>", lambda e: self._refresh_weather_data())
        self.bind("<Control-l>", lambda e: self._show_location_dialog())
        self.bind("<Control-s>", lambda e: self._show_section(DashboardSection.SETTINGS))
        self.bind("<F5>", lambda e: self._refresh_weather_data())

        # Focus management
        self.focus_set()

        self.logger.debug("Event bindings setup completed")

    def _setup_auto_refresh(self) -> None:
        """
        Set up automatic data refresh timer.

        This method demonstrates professional data management
        with automatic updates and user control.
        """
        def auto_refresh():
            if not self.is_loading:
                self._refresh_weather_data(silent=True)

            # Schedule next refresh
            self.after(self.config.auto_refresh_interval * 1000, auto_refresh)

        # Start auto-refresh timer
        self.after(5000, auto_refresh)  # First refresh after 5 seconds

        self.logger.debug(f"Auto-refresh setup with {self.config.auto_refresh_interval}s interval")

    def _subscribe_to_events(self) -> None:
        """
        Subscribe to app controller events.

        This method demonstrates event-driven architecture
        with loose coupling between UI and business logic.
        """
        # Subscribe to weather data updates
        self.app_controller.event_bus.subscribe(
            "weather_data_updated",
            self._on_weather_data_updated
        )

        # Subscribe to error events
        self.app_controller.event_bus.subscribe(
            "error_occurred",
            self._on_error_occurred
        )

        # Subscribe to loading state changes
        self.app_controller.event_bus.subscribe(
            "loading_state_changed",
            self._on_loading_state_changed
        )

        self.logger.debug("Event subscriptions setup completed")

    def _show_section(self, section: DashboardSection) -> None:
        """
        Show the specified dashboard section.

        Args:
            section: Section to display
        """
        if section == self.current_section:
            return

        # Hide current section
        if self.current_section in self.section_frames:
            self.section_frames[self.current_section].pack_forget()

        # Update navigation button states
        self._update_nav_button_states(section)

        # Show new section
        self.section_frames[section].pack(fill="both", expand=True, padx=10, pady=10)

        # Update section title
        section_titles = {
            DashboardSection.OVERVIEW: "Dashboard Overview",
            DashboardSection.TEMPERATURE_GRAPH: "Temperature Graph",
            DashboardSection.WEATHER_JOURNAL: "Weather Journal",
            DashboardSection.ACTIVITY_SUGGESTER: "Activity Suggester",
            DashboardSection.TEAM_COLLABORATION: "Team Collaboration",
            DashboardSection.SETTINGS: "Settings"
        }

        self.section_title.configure(text=section_titles.get(section, "Unknown Section"))

        # Update current section
        self.current_section = section

        # Update status
        self._update_status(f"Switched to {section.value.replace('_', ' ').title()}")

        self.logger.debug(f"Switched to section: {section.value}")

    def _update_nav_button_states(self, active_section: DashboardSection) -> None:
        """
        Update navigation button visual states.

        Args:
            active_section: Currently active section
        """
        for section, button in self.nav_buttons.items():
            if section == active_section:
                # Highlight active button
                button.configure(
                    fg_color=("#4A90E2", "#357ABD"),
                    text_color=("white", "white")
                )
            else:
                # Reset inactive buttons
                glass_config = button._get_glass_button_config()
                button.configure(
                    fg_color=glass_config['fg_color'],
                    text_color=glass_config['text_color']
                )

    def _refresh_weather_data(self, silent: bool = False) -> None:
        """
        Refresh weather data from API.

        Args:
            silent: Whether to show loading indicators
        """
        if self.is_loading:
            return

        self.is_loading = True

        if not silent:
            self._show_loading(True)
            self._update_status("Refreshing weather data...")

        # Refresh data in background thread
        def refresh_thread():
            try:
                # Request weather data update from app controller
                self.app_controller.request_weather_update()

            except Exception as e:
                self.logger.error(f"Error refreshing weather data: {e}")
                self.after(0, lambda: self._on_error_occurred(str(e)))
            finally:
                self.is_loading = False
                if not silent:
                    self.after(0, lambda: self._show_loading(False))

        threading.Thread(target=refresh_thread, daemon=True).start()

    def _show_location_dialog(self) -> None:
        """
        Show location change dialog.

        This method demonstrates professional dialog design
        with user input validation and error handling.
        """
        # Create dialog window
        dialog = ctk.CTkToplevel(self)
        dialog.title("Change Location")
        dialog.geometry("400x200")
        dialog.transient(self)
        dialog.grab_set()

        # Center dialog
        dialog.update_idletasks()
        x = self.winfo_x() + (self.winfo_width() // 2) - 200
        y = self.winfo_y() + (self.winfo_height() // 2) - 100
        dialog.geometry(f"400x200+{x}+{y}")

        # Dialog content
        dialog_frame = GlassFrame(dialog, size=ComponentSize.LARGE)
        dialog_frame.pack(fill="both", expand=True, padx=20, pady=20)

        title_label = GlassLabel(
            dialog_frame,
            text="Enter New Location",
            text_style="heading",
            size=ComponentSize.LARGE
        )
        title_label.pack(pady=(20, 10))

        location_entry = GlassEntry(
            dialog_frame,
            placeholder_text="City, State or ZIP code",
            size=ComponentSize.LARGE
        )
        location_entry.pack(pady=10, padx=20, fill="x")
        location_entry.focus()

        # Buttons
        button_frame = GlassFrame(dialog_frame)
        button_frame.pack(pady=20)

        def on_ok():
            location = location_entry.get().strip()
            if location:
                self._update_location(location)
                dialog.destroy()

        def on_cancel():
            dialog.destroy()

        ok_button = GlassButton(
            button_frame,
            text="OK",
            size=ComponentSize.MEDIUM,
            command=on_ok
        )
        ok_button.pack(side="left", padx=5)

        cancel_button = GlassButton(
            button_frame,
            text="Cancel",
            size=ComponentSize.MEDIUM,
            command=on_cancel
        )
        cancel_button.pack(side="left", padx=5)

        # Bind Enter key
        location_entry.bind("<Return>", lambda e: on_ok())
        dialog.bind("<Escape>", lambda e: on_cancel())

    def _export_weather_data(self) -> None:
        """
        Export weather data to file.

        This method demonstrates professional data export
        with user feedback and error handling.
        """
        self._update_status("Exporting weather data...")

        # Implementation would go here
        # For now, show a placeholder message

        self.after(1000, lambda: self._update_status("Export feature coming soon!"))

    def _update_location(self, location: str) -> None:
        """
        Update the current location.

        Args:
            location: New location string
        """
        self._update_status(f"Updating location to {location}...")

        # Update app controller with new location
        self.app_controller.update_location(location)

        # Refresh weather data
        self._refresh_weather_data()

    def _show_loading(self, show: bool) -> None:
        """
        Show or hide loading indicators.

        Args:
            show: Whether to show loading indicators
        """
        if show:
            self.loading_progress.pack(side="right", padx=20, pady=15)
            self.loading_progress.start()
        else:
            self.loading_progress.stop()
            self.loading_progress.pack_forget()

    def _update_status(self, message: str) -> None:
        """
        Update status bar message.

        Args:
            message: Status message to display
        """
        self.status_label.configure(text=message)

        # Auto-clear status after 5 seconds
        self.after(5000, lambda: self.status_label.configure(text="Ready"))

    def _get_current_time(self) -> str:
        """
        Get formatted current time string.

        Returns:
            Formatted time string
        """
        return datetime.now().strftime("%I:%M %p")

    def _update_time_display(self) -> None:
        """
        Update time display in sidebar.

        This method runs periodically to keep time current.
        """
        if hasattr(self, 'time_label'):
            self.time_label.configure(text=self._get_current_time())

        # Schedule next update
        self.after(60000, self._update_time_display)  # Update every minute

    # Event handlers
    def _on_weather_data_updated(self, weather_data: WeatherData) -> None:
        """
        Handle weather data update event.

        Args:
            weather_data: Updated weather data
        """
        self.current_weather = weather_data
        self.last_weather_update = datetime.now()

        # Update weather summary in sidebar
        if hasattr(self, 'weather_location_label'):
            location = f"{weather_data.city}, {weather_data.country}"
            self.weather_location_label.configure(text=location)
            self.weather_temp_label.configure(text=f"{weather_data.temperature:.0f}°F")
            self.weather_condition_label.configure(text=weather_data.condition)
            self.last_update_label.configure(
                text=f"Last updated: {self.last_weather_update.strftime('%I:%M %p')}"
            )

        # Update theme based on weather
        if self.config.theme_auto_update:
            weather_theme = self.theme_manager.get_weather_theme(weather_data.condition)
            self.theme_manager.apply_weather_theme(weather_theme)

        self._update_status("Weather data updated successfully")
        self.logger.info(f"Weather data updated for {location}")

    def _on_error_occurred(self, error_message: str) -> None:
        """
        Handle error event.

        Args:
            error_message: Error message to display
        """
        self._update_status(f"Error: {error_message}")
        self.connection_label.configure(text="🔴 Error")

        # Reset connection status after delay
        self.after(10000, lambda: self.connection_label.configure(text="🟢 Connected"))

        self.logger.error(f"UI Error: {error_message}")

    def _on_loading_state_changed(self, is_loading: bool) -> None:
        """
        Handle loading state change event.

        Args:
            is_loading: Whether app is currently loading
        """
        self.is_loading = is_loading
        self._show_loading(is_loading)

    def _on_window_resize(self, event) -> None:
        """
        Handle window resize event.

        Args:
            event: Tkinter event object
        """
        # Update responsive layout if needed
        pass

    def _on_window_focus(self, event) -> None:
        """
        Handle window focus event.

        Args:
            event: Tkinter event object
        """
        # Refresh data when window gains focus
        if not self.is_loading and self.last_weather_update:
            time_since_update = datetime.now() - self.last_weather_update
            if time_since_update > timedelta(minutes=10):
                self._refresh_weather_data(silent=True)

    def _on_window_close(self) -> None:
        """
        Handle window close event.

        This method ensures proper cleanup and graceful shutdown.
        """
        self.logger.info("Dashboard window closing")

        # Notify app controller of shutdown
        try:
            self.app_controller.shutdown()
        except Exception as e:
            self.logger.error(f"Error during shutdown: {e}")

        # Destroy window
        self.destroy()

    def run(self) -> None:
        """
        Start the dashboard UI main loop.

        This method starts the application and handles
        the main event loop with proper error handling.
        """
        try:
            # Start time update timer
            self.after(1000, self._update_time_display)

            # Initial weather data load
            self.after(1000, lambda: self._refresh_weather_data())

            self.logger.info("Starting Weather Dashboard UI")

            # Start main loop
            self.mainloop()

        except Exception as e:
            self.logger.error(f"Error in main loop: {e}")
            raise
        finally:
            self.logger.info("Weather Dashboard UI stopped")


def create_dashboard(app_controller: AppController, config: Optional[DashboardConfig] = None) -> WeatherDashboardUI:
    """
    Factory function to create and configure the dashboard UI.

    Args:
        app_controller: Application controller instance
        config: Optional dashboard configuration

    Returns:
        Configured WeatherDashboardUI instance
    """
    dashboard = WeatherDashboardUI(app_controller, config)
    return dashboard


if __name__ == "__main__":
    # Test the dashboard UI
    from ..core.app_controller import initialize_application

    # Initialize application
    app_controller = initialize_application()

    # Create and run dashboard
    config = DashboardConfig(
        window_title="Weather Dashboard - Development Mode",
        auto_refresh_interval=60,
        enable_animations=True
    )

    dashboard = create_dashboard(app_controller, config)
    dashboard.run()
