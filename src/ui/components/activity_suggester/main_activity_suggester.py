"""Main Activity Suggester Class

Combines all mixins to create the complete ActivitySuggester component.
"""

from ....services.ai_service import AIService
from ..base_component import BaseComponent

# Import mixins
from .ai_providers import AIProvidersMixin
from .database_manager import DatabaseManagerMixin
from .suggestion_engine import SuggestionEngineMixin
from .ui_components import UIComponentsMixin

# Optional imports for legacy AI services
try:
    import google.generativeai as genai

    GENAI_AVAILABLE = True
except ImportError:
    genai = None
    GENAI_AVAILABLE = False

try:
    import openai

    OPENAI_AVAILABLE = True
except ImportError:
    openai = None
    OPENAI_AVAILABLE = False


class ActivitySuggester(
    AIProvidersMixin, DatabaseManagerMixin, UIComponentsMixin, SuggestionEngineMixin, BaseComponent
):
    """Activity Suggester component that provides AI-powered activity recommendations based on weather."""

    def __init__(self, parent, weather_service, config_service, **kwargs):
        """Initialize the Activity Suggester.

        Args:
            parent: Parent widget
            weather_service: Weather service instance
            config_service: Configuration service instance
            **kwargs: Additional keyword arguments for CTkFrame
        """
        super().__init__(parent, **kwargs)

        # Store services
        self.weather_service = weather_service
        self.config_service = config_service

        # Initialize enhanced AI service
        self.ai_service = AIService(config_service)

        # Initialize legacy AI services
        self._initialize_gemini()
        self._initialize_openai()

        # Initialize data storage
        self.suggestions = []
        self.current_weather = None
        self.selected_category = "All"

        # Setup database
        self._setup_database()

        # Create UI
        self._create_ui()

        # Load initial suggestions
        self._refresh_suggestions()

    def update_location(self, location_data: dict):
        """Update activity suggester with new location context.

        Args:
            location_data: Dictionary containing location information
        """
        try:
            # Store location context
            self.current_location = location_data

            # Clear current weather to force refresh with new location
            self.current_weather = None

            # Update any location-specific preferences or context
            location_name = location_data.get(
                "display_name", location_data.get("city", "Unknown Location")
            )

            # Refresh suggestions for the new location
            self._refresh_suggestions()

            # Update UI to reflect new location context
            self._update_location_display(location_name)

        except Exception as e:
            print(f"Error updating activity suggester location: {e}")

    def update_weather_data(self, weather_data: dict):
        """Update activity suggester with current weather data.

        Args:
            weather_data: Current weather data dictionary
        """
        try:
            # Store current weather
            self.current_weather = weather_data

            # Refresh suggestions based on new weather
            self._refresh_suggestions()

        except Exception as e:
            print(f"Error updating activity suggester weather data: {e}")

    def _update_location_display(self, location_name: str):
        """Update UI elements to show current location context.

        Args:
            location_name: Name of the current location
        """
        try:
            # Update title or header if it exists
            if hasattr(self, "title_label"):
                self.title_label.configure(text=f"Activity Suggestions for {location_name}")

            # Update any location-specific UI elements
            # This can be expanded based on the actual UI structure

        except Exception as e:
            print(f"Error updating location display: {e}")

    def __del__(self):
        """Clean up database connection."""
        try:
            if hasattr(self, "conn"):
                self.conn.close()
        except:
            pass
