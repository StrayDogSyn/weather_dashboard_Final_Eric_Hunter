"""Data models for team collaboration feature.

This module contains all data structures and models used for team collaboration,
including configuration, team data, and collaboration entities.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime


@dataclass
class CollaborationConfig:
    """Configuration for team collaboration features."""
    auto_sync: bool = True
    sync_interval: int = 300  # seconds
    max_cities_display: int = 50
    max_comparisons_display: int = 20
    enable_notifications: bool = True
    default_comparison_metrics: List[str] = None

    def __post_init__(self):
        if self.default_comparison_metrics is None:
            self.default_comparison_metrics = [
                "temperature", "humidity", "wind_speed", "pressure"
            ]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            'auto_sync': self.auto_sync,
            'sync_interval': self.sync_interval,
            'max_cities_display': self.max_cities_display,
            'max_comparisons_display': self.max_comparisons_display,
            'enable_notifications': self.enable_notifications,
            'default_comparison_metrics': self.default_comparison_metrics
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CollaborationConfig':
        """Create from dictionary."""
        return cls(
            auto_sync=data.get('auto_sync', True),
            sync_interval=data.get('sync_interval', 300),
            max_cities_display=data.get('max_cities_display', 50),
            max_comparisons_display=data.get('max_comparisons_display', 20),
            enable_notifications=data.get('enable_notifications', True),
            default_comparison_metrics=data.get('default_comparison_metrics', [
                "temperature", "humidity", "wind_speed", "pressure"
            ])
        )


@dataclass
class TeamActivity:
    """Represents a team activity or action."""
    id: str
    user: str
    action: str  # added_city, created_comparison, updated_data, etc.
    target: str  # city name, comparison name, etc.
    timestamp: datetime
    details: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            'id': self.id,
            'user': self.user,
            'action': self.action,
            'target': self.target,
            'timestamp': self.timestamp.isoformat(),
            'details': self.details,
            'metadata': self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TeamActivity':
        """Create from dictionary."""
        return cls(
            id=data['id'],
            user=data['user'],
            action=data['action'],
            target=data['target'],
            timestamp=datetime.fromisoformat(data['timestamp']),
            details=data.get('details'),
            metadata=data.get('metadata', {})
        )


@dataclass
class SyncStatus:
    """Represents synchronization status."""
    last_sync: Optional[datetime] = None
    is_syncing: bool = False
    last_error: Optional[str] = None
    pending_changes: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            'last_sync': self.last_sync.isoformat() if self.last_sync else None,
            'is_syncing': self.is_syncing,
            'last_error': self.last_error,
            'pending_changes': self.pending_changes
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SyncStatus':
        """Create from dictionary."""
        return cls(
            last_sync=datetime.fromisoformat(data['last_sync']) if data.get('last_sync') else None,
            is_syncing=data.get('is_syncing', False),
            last_error=data.get('last_error'),
            pending_changes=data.get('pending_changes', 0)
        )


@dataclass
class CollaborationSession:
    """Represents an active collaboration session."""
    session_id: str
    participants: List[str]
    created_at: datetime
    last_activity: datetime
    active_comparisons: List[str] = field(default_factory=list)
    shared_cities: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            'session_id': self.session_id,
            'participants': self.participants,
            'created_at': self.created_at.isoformat(),
            'last_activity': self.last_activity.isoformat(),
            'active_comparisons': self.active_comparisons,
            'shared_cities': self.shared_cities
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CollaborationSession':
        """Create from dictionary."""
        return cls(
            session_id=data['session_id'],
            participants=data['participants'],
            created_at=datetime.fromisoformat(data['created_at']),
            last_activity=datetime.fromisoformat(data['last_activity']),
            active_comparisons=data.get('active_comparisons', []),
            shared_cities=data.get('shared_cities', [])
        )