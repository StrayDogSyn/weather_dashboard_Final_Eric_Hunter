"""Team collaboration features package.

This package provides team collaboration functionality including:
- Team member management
- City sharing and comparison
- Activity tracking
- GitHub integration
"""

from .collaboration_widget import TeamCollaborationWidget
from .collaboration_controller import CollaborationController
from .models import (
    CollaborationConfig,
    TeamMember,
    CityData,
    TeamComparison,
    TeamActivity,
    SyncStatus,
    CollaborationSession
)
from .database import CollaborationDatabase

# UI Components
from .ui_cards import (
    MemberCard,
    CityCard,
    ComparisonCard,
    ActivityCard
)
from .ui_viewers import (
    ComparisonViewer,
    CityDetailsViewer
)
from .ui_utilities import (
    SelectedCitiesDisplay,
    LoadingOverlay,
    StatusBar,
    create_share_city_dialog,
    create_comparison_dialog
)

# Backward compatibility - import original UI components
try:
    from .ui_components import (
        MemberCard as MemberCardLegacy,
        CityCard as CityCardLegacy,
        ComparisonCard as ComparisonCardLegacy,
        ActivityCard as ActivityCardLegacy,
        ComparisonViewer as ComparisonViewerLegacy,
        CityDetailsViewer as CityDetailsViewerLegacy,
        SelectedCitiesDisplay as SelectedCitiesDisplayLegacy,
        LoadingOverlay as LoadingOverlayLegacy,
        StatusBar as StatusBarLegacy,
        create_share_city_dialog as create_share_city_dialog_legacy
    )
except ImportError:
    # Legacy components not available
    pass

__all__ = [
    # Core components
    'TeamCollaborationWidget',
    'CollaborationController',
    'CollaborationConfig',
    'TeamMember',
    'CityData',
    'TeamComparison',
    'TeamActivity',
    'SyncStatus',
    'CollaborationSession',
    'CollaborationDatabase',
    # UI Cards
    'MemberCard',
    'CityCard',
    'ComparisonCard',
    'ActivityCard',
    # UI Viewers
    'ComparisonViewer',
    'CityDetailsViewer',
    # UI Utilities
    'SelectedCitiesDisplay',
    'LoadingOverlay',
    'StatusBar',
    'create_share_city_dialog',
    'create_comparison_dialog'
]