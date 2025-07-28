"""
Activity Suggester Widget

This module contains the main ActivitySuggesterWidget class with layout methods
and UI structure. The widget is refactored to use separate modules for
UI components, business logic, and utilities.
"""

import customtkinter as ctk
import threading
from typing import List, Optional

from .models import (
    ActivitySuggestion, ActivityCategory, DifficultyLevel, 
    WeatherSuitability, UserPreferences
)
from ...services.weather_service import WeatherData
from .database import ActivityDatabase
from .ai_service import AIActivityGenerator
from .spotify_service import SpotifyIntegration
from .ui_components import ActivityUIComponents
from .activity_controller import ActivityController
from .utils import ActivityUtils
from ...ui.components.glass import (
    GlassFrame, GlassLabel, GlassButton
)
from ...utils.logger import LoggerMixin
from ...ui.theme_manager import ThemeManager
from ...core.database_manager import DatabaseManager


class ActivitySuggesterWidget(GlassFrame, LoggerMixin):
    """Main Activity Suggester widget with glassmorphic design."""

    def __init__(
        self,
        parent,
        database_manager: DatabaseManager,
        theme_manager: Optional[ThemeManager] = None,
        **kwargs
    ):
        super().__init__(parent, **kwargs)

        # Core dependencies
        self.database_manager = database_manager
        self.theme_manager = theme_manager or ThemeManager()

        # Initialize services
        self.activity_db = ActivityDatabase(database_manager)
        self.ai_generator = AIActivityGenerator()  # Will be configured later
        self.spotify_integration = SpotifyIntegration()  # Will be configured later

        # Initialize components
        self.ui_components = ActivityUIComponents(self)
        self.controller = ActivityController(self)

        # State management
        self.current_weather: Optional[WeatherData] = None
        self.user_preferences = self.activity_db.load_user_preferences()
        self.current_suggestions: List[ActivitySuggestion] = []
        self.selected_activity: Optional[ActivitySuggestion] = None
        self.is_generating = False

        # UI components
        self.suggestion_cards: List[ctk.CTkFrame] = []
        self.generation_thread: Optional[threading.Thread] = None

        # Initialize UI
        self._setup_ui()
        self._load_recent_suggestions()

        self.logger.info("Activity Suggester widget initialized")

    def configure_api_keys(self, gemini_api_key: Optional[str] = None,
                          spotify_client_id: Optional[str] = None,
                          spotify_client_secret: Optional[str] = None):
        """Configure API keys for AI and Spotify integration."""
        self.controller.configure_api_keys(gemini_api_key, spotify_client_id, spotify_client_secret)

    def _setup_ui(self):
        """Setup the main UI layout."""
        # Configure grid
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # Header section
        self._create_header()

        # Main content area
        self._create_main_content()

        # Sidebar for preferences and controls
        self._create_sidebar()

        # Status bar
        self._create_status_bar()

        # Apply glassmorphic styling
        self._apply_glass_styling()

    def _create_header(self):
        """Create header with title and quick actions."""
        header_frame = GlassFrame(self)
        header_frame.grid(row=0, column=0, columnspan=3, sticky="ew", padx=10, pady=(10, 5))
        header_frame.grid_columnconfigure(1, weight=1)

        # Title
        title_label = GlassLabel(
            header_frame,
            text="🎯 Activity Suggester",
            font=("Segoe UI", 24, "bold")
        )
        title_label.grid(row=0, column=0, sticky="w", padx=20, pady=15)

        # Quick action buttons
        actions_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        actions_frame.grid(row=0, column=2, sticky="e", padx=20, pady=15)

        self.generate_button = GlassButton(
            actions_frame,
            text="🔄 Generate New",
            command=self._generate_suggestions,
            width=140
        )
        self.generate_button.pack(side="left", padx=(0, 10))

        self.preferences_button = GlassButton(
            actions_frame,
            text="⚙️ Preferences",
            command=self._show_preferences,
            width=140
        )
        self.preferences_button.pack(side="left", padx=(0, 10))

        self.analytics_button = GlassButton(
            actions_frame,
            text="📊 Analytics",
            command=self._show_analytics,
            width=120
        )
        self.analytics_button.pack(side="left")

    def _create_sidebar(self):
        """Create sidebar with filters and preferences."""
        sidebar_frame = GlassFrame(self, width=280)
        sidebar_frame.grid(row=1, column=0, sticky="nsew", padx=(10, 5), pady=5)
        sidebar_frame.grid_propagate(False)

        # Weather info section
        weather_section = GlassFrame(sidebar_frame)
        weather_section.pack(fill="x", padx=10, pady=(10, 5))

        weather_title = GlassLabel(
            weather_section,
            text="🌤️ Current Weather",
            font=("Segoe UI", 14, "bold")
        )
        weather_title.pack(pady=(10, 5))

        self.weather_info_label = GlassLabel(
            weather_section,
            text="Weather data not available",
            font=("Segoe UI", 11)
        )
        self.weather_info_label.pack(pady=(0, 10))

        # Quick filters section
        filters_section = GlassFrame(sidebar_frame)
        filters_section.pack(fill="x", padx=10, pady=5)

        filters_title = GlassLabel(
            filters_section,
            text="🔍 Quick Filters",
            font=("Segoe UI", 14, "bold")
        )
        filters_title.pack(pady=(10, 5))

        # Category filter
        self.category_var = ctk.StringVar(value="all")
        category_menu = ctk.CTkOptionMenu(
            filters_section,
            variable=self.category_var,
            values=["all"] + [cat.value for cat in ActivityCategory],
            command=self._on_filter_changed
        )
        category_menu.pack(fill="x", padx=10, pady=2)

        # Difficulty filter
        self.difficulty_var = ctk.StringVar(value="all")
        difficulty_menu = ctk.CTkOptionMenu(
            filters_section,
            variable=self.difficulty_var,
            values=["all"] + [diff.value for diff in DifficultyLevel],
            command=self._on_filter_changed
        )
        difficulty_menu.pack(fill="x", padx=10, pady=2)

        # Duration filter
        duration_label = GlassLabel(filters_section, text="Max Duration (minutes):")
        duration_label.pack(pady=(10, 2))

        self.duration_var = ctk.IntVar(value=180)
        duration_slider = ctk.CTkSlider(
            filters_section,
            from_=15,
            to=300,
            variable=self.duration_var,
            command=self._on_filter_changed
        )
        duration_slider.pack(fill="x", padx=10, pady=(0, 5))

        self.duration_value_label = GlassLabel(filters_section, text="180 min")
        self.duration_value_label.pack(pady=(0, 10))

        # Favorites section
        favorites_section = GlassFrame(sidebar_frame)
        favorites_section.pack(fill="x", padx=10, pady=5)

        favorites_title = GlassLabel(
            favorites_section,
            text="⭐ Quick Actions",
            font=("Segoe UI", 14, "bold")
        )
        favorites_title.pack(pady=(10, 5))

        self.show_favorites_var = ctk.BooleanVar()
        favorites_checkbox = ctk.CTkCheckBox(
            favorites_section,
            text="Show only favorites",
            variable=self.show_favorites_var,
            command=self._on_filter_changed
        )
        favorites_checkbox.pack(pady=2)

        export_button = GlassButton(
            favorites_section,
            text="📤 Export Activities",
            command=self._export_activities,
            width=200
        )
        export_button.pack(fill="x", padx=10, pady=(5, 10))

    def _create_main_content(self):
        """Create main content area for activity suggestions."""
        main_frame = GlassFrame(self)
        main_frame.grid(row=1, column=1, sticky="nsew", padx=5, pady=5)
        main_frame.grid_rowconfigure(1, weight=1)
        main_frame.grid_columnconfigure(0, weight=1)

        # Content header
        content_header = ctk.CTkFrame(main_frame, fg_color="transparent")
        content_header.grid(row=0, column=0, sticky="ew", padx=15, pady=(15, 5))
        content_header.grid_columnconfigure(1, weight=1)

        suggestions_title = GlassLabel(
            content_header,
            text="💡 Activity Suggestions",
            font=("Segoe UI", 18, "bold")
        )
        suggestions_title.grid(row=0, column=0, sticky="w")

        self.suggestions_count_label = GlassLabel(
            content_header,
            text="0 suggestions",
            font=("Segoe UI", 12)
        )
        self.suggestions_count_label.grid(row=0, column=2, sticky="e")

        # Scrollable suggestions area
        self.suggestions_scroll = ctk.CTkScrollableFrame(
            main_frame,
            fg_color=("#F0F0F0", "#1A1A1A"),
            scrollbar_button_color=("#CCCCCC", "#444444")
        )
        self.suggestions_scroll.grid(row=1, column=0, sticky="nsew", padx=15, pady=(5, 15))
        self.suggestions_scroll.grid_columnconfigure(0, weight=1)

        # Loading indicator
        self.loading_frame = ctk.CTkFrame(self.suggestions_scroll, fg_color="transparent")
        self.loading_label = GlassLabel(
            self.loading_frame,
            text="🔄 Generating personalized suggestions...",
            font=("Segoe UI", 14)
        )
        self.loading_label.pack(pady=50)

        # Empty state
        self.empty_frame = ctk.CTkFrame(self.suggestions_scroll, fg_color="transparent")
        empty_label = GlassLabel(
            self.empty_frame,
            text="🎯 Click 'Generate New' to get personalized activity suggestions!",
            font=("Segoe UI", 14)
        )
        empty_label.pack(pady=50)
        self.empty_frame.pack(fill="both", expand=True)

    def _create_status_bar(self):
        """Create status bar with generation info."""
        status_frame = GlassFrame(self, height=40)
        status_frame.grid(row=2, column=0, columnspan=3, sticky="ew", padx=10, pady=(5, 10))
        status_frame.grid_propagate(False)
        status_frame.grid_columnconfigure(1, weight=1)

        self.status_label = GlassLabel(
            status_frame,
            text="Ready to generate activity suggestions",
            font=("Segoe UI", 10)
        )
        self.status_label.grid(row=0, column=0, sticky="w", padx=15, pady=10)

        self.ai_status_label = GlassLabel(
            status_frame,
            text="AI: Ready" if self.ai_generator.model else "AI: Fallback Mode",
            font=("Segoe UI", 10)
        )
        self.ai_status_label.grid(row=0, column=2, sticky="e", padx=15, pady=10)

    def _apply_glass_styling(self):
        """Apply glassmorphic styling to components."""
        if self.theme_manager:
            # Apply weather-responsive theme
            if self.current_weather:
                self.theme_manager.apply_weather_theme(self.current_weather.condition)

    def _load_recent_suggestions(self):
        """Load recent suggestions from database."""
        self.controller.load_recent_suggestions()

    def _generate_suggestions(self):
        """Generate new activity suggestions."""
        self.controller.generate_suggestions()

    def _update_suggestions_display(self):
        """Update the suggestions display with current suggestions."""
        # Clear existing cards
        for card in self.suggestion_cards:
            card.destroy()
        self.suggestion_cards.clear()

        # Hide empty state
        self.empty_frame.pack_forget()

        # Filter suggestions based on current filters
        filtered_suggestions = self.controller.filter_suggestions(self.current_suggestions)

        # Update count
        self.suggestions_count_label.configure(text=f"{len(filtered_suggestions)} suggestions")

        # Create suggestion cards
        for i, suggestion in enumerate(filtered_suggestions):
            card = self.ui_components.create_suggestion_card(suggestion, i)
            card.pack(fill="x", padx=10, pady=5)
            self.suggestion_cards.append(card)

        # Show empty state if no suggestions
        if not filtered_suggestions:
            self.empty_frame.pack(fill="both", expand=True)

    def _show_loading(self):
        """Show loading indicator."""
        self.empty_frame.pack_forget()
        for card in self.suggestion_cards:
            card.pack_forget()
        self.loading_frame.pack(fill="both", expand=True)

    def _hide_loading(self):
        """Hide loading indicator."""
        self.loading_frame.pack_forget()

    def _update_status(self, message: str):
        """Update status bar message."""
        self.status_label.configure(text=message)

    def _on_filter_changed(self, *args):
        """Handle filter changes."""
        self.controller.on_filter_changed(*args)

    def _toggle_favorite(self, suggestion: ActivitySuggestion):
        """Toggle favorite status of an activity."""
        self.controller.toggle_favorite(suggestion)

    def _mark_activity_complete(self, suggestion: ActivitySuggestion):
        """Mark an activity as completed."""
        self.controller.mark_activity_complete(suggestion)

    def _get_activity_music(self, suggestion: ActivitySuggestion):
        """Get music recommendations for activity."""
        self.controller.get_activity_music(suggestion)

    def _show_preferences(self):
        """Show user preferences dialog."""
        self.controller.show_preferences_dialog()

    def _show_analytics(self):
        """Show activity analytics dialog."""
        self.controller.show_analytics_dialog()

    def _export_activities(self):
        """Export activities to a file."""
        self.controller.export_activities()

    # Public API methods
    def set_weather_data(self, weather_data: dict):
        """Set current weather data for activity suggestions."""
        self.controller.set_weather_data(weather_data)
        
        # Update weather display
        if weather_data:
            weather_text = f"{weather_data.get('condition', 'N/A')} | {weather_data.get('temperature', 'N/A')}°C"
            self.weather_info_label.configure(text=weather_text)

    def set_user_preferences(self, preferences: UserPreferences):
        """Set user preferences for activity suggestions."""
        self.controller.set_user_preferences(preferences)

    def get_user_preferences(self) -> UserPreferences:
        """Get current user preferences."""
        return self.controller.get_user_preferences()

    def refresh_suggestions(self):
        """Refresh activity suggestions."""
        self.controller.refresh_suggestions()

    def get_activity_stats(self) -> dict:
        """Get activity statistics."""
        return self.controller.get_activity_stats()

    def export_activity_data(self, file_path: str) -> bool:
        """Export activity data to JSON file."""
        return self.controller.export_activity_data(file_path)


def create_activity_suggester(parent, database_manager: DatabaseManager, **kwargs) -> ActivitySuggesterWidget:
    """Factory function to create ActivitySuggesterWidget."""
    return ActivitySuggesterWidget(parent, database_manager, **kwargs)


if __name__ == "__main__":
    # Test the widget
    import tempfile
    import os

    app = ctk.CTk()
    app.title("Activity Suggester Test")
    app.geometry("1000x700")

    # Create test database
    db_path = os.path.join(tempfile.gettempdir(), "test_activities.db")
    
    # Mock database manager for testing
    class MockDatabaseManager:
        def __init__(self, db_path):
            self.db_path = db_path
        
        def get_connection(self):
            import sqlite3
            return sqlite3.connect(self.db_path)

    # Create widget
    db_manager = MockDatabaseManager(db_path)
    widget = create_activity_suggester(app, db_manager)
    widget.pack(fill="both", expand=True, padx=20, pady=20)

    # Set test weather data
    test_weather = {
        'condition': 'sunny',
        'temperature': 22,
        'humidity': 60,
        'wind_speed': 5
    }
    widget.set_weather_data(test_weather)

    app.mainloop()