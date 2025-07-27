"""Features package for weather dashboard components.

This package contains all the major feature modules of the weather dashboard,
each organized into their own modular subpackages.
"""

# Import main widgets from each feature
try:
    from .activity_suggester import ActivitySuggesterWidget, create_activity_suggester_widget
except ImportError:
    ActivitySuggesterWidget = None
    create_activity_suggester_widget = None

try:
    from .weather_journal import WeatherJournalWidget
except ImportError:
    WeatherJournalWidget = None

try:
    from .team_collaboration import TeamCollaborationWidget
except ImportError:
    TeamCollaborationWidget = None

try:
    from .temperature_graph import ChartController
except ImportError:
    ChartController = None

__all__ = [
    'ActivitySuggesterWidget',
    'create_activity_suggester_widget',
    'WeatherJournalWidget', 
    'TeamCollaborationWidget',
    'ChartController',
]