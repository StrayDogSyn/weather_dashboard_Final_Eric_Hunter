"""Team Collaboration Feature Package.

This package provides team collaboration functionality for sharing weather data,
creating team comparisons, and tracking team activity through GitHub integration.
"""

from .models import (
    CollaborationConfig,
    TeamActivity,
    SyncStatus,
    CollaborationSession,
)
from .collaboration_controller import CollaborationController
from .collaboration_widget import TeamCollaborationWidget

__all__ = [
    'CollaborationConfig',
    'TeamActivity',
    'SyncStatus',
    'CollaborationSession',
    'CollaborationController',
    'TeamCollaborationWidget',
]