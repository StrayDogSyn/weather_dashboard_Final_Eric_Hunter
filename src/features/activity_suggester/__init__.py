"""Activity Suggester Feature Package.

This package provides AI-powered activity recommendations based on weather conditions
with a modern glassmorphic interface. The package is organized into separate modules
for better maintainability and modularity.
"""

from .models import (
    ActivityCategory,
    WeatherSuitability,
    DifficultyLevel,
    ActivitySuggestion,
    UserPreferences,
)
from .activity_widget import ActivitySuggesterWidget, create_activity_suggester
from .database import ActivityDatabase
from .ai_service import AIActivityGenerator
from .spotify_service import SpotifyIntegration
from .ui_components import ActivityUIComponents
from .activity_controller import ActivityController
from .utils import ActivityUtils, DataExporter, ActivityValidator, WeatherUtils

__all__ = [
    # Models
    'ActivityCategory',
    'WeatherSuitability', 
    'DifficultyLevel',
    'ActivitySuggestion',
    'UserPreferences',
    
    # Main widget
    'ActivitySuggesterWidget',
    'create_activity_suggester',
    
    # Services
    'ActivityDatabase',
    'AIActivityGenerator',
    'SpotifyIntegration',
    
    # Components
    'ActivityUIComponents',
    'ActivityController',
    
    # Utilities
    'ActivityUtils',
    'DataExporter',
    'ActivityValidator',
    'WeatherUtils',
]