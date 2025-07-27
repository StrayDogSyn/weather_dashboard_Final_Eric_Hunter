"""Data models for team collaboration feature.

This module contains all data structures and models used in the team collaboration
system for sharing weather data and creating team comparisons.
"""

from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Dict, List, Optional, Any


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
        """Convert config to dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CollaborationConfig':
        """Create config from dictionary."""
        return cls(**data)


@dataclass
class TeamMember:
    """Represents a team member in the collaboration system."""
    id: str
    name: str
    username: str
    email: Optional[str] = None
    role: str = "member"  # admin, maintainer, member
    cities_shared: int = 0
    contributions: int = 0
    last_active: Optional[datetime] = None
    avatar_url: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert team member to dictionary."""
        data = asdict(self)
        if self.last_active:
            data['last_active'] = self.last_active.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TeamMember':
        """Create team member from dictionary."""
        if 'last_active' in data and data['last_active']:
            data['last_active'] = datetime.fromisoformat(data['last_active'])
        return cls(**data)


@dataclass
class CityData:
    """Represents shared city weather data."""
    id: str
    city_name: str
    country: str
    latitude: float
    longitude: float
    current_weather: Dict[str, Any]
    shared_by: str
    shared_at: datetime
    tags: List[str] = None
    description: str = ""
    is_favorite: bool = False
    last_updated: Optional[datetime] = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []
        if self.last_updated is None:
            self.last_updated = self.shared_at

    def to_dict(self) -> Dict[str, Any]:
        """Convert city data to dictionary."""
        data = asdict(self)
        data['shared_at'] = self.shared_at.isoformat()
        if self.last_updated:
            data['last_updated'] = self.last_updated.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CityData':
        """Create city data from dictionary."""
        data = data.copy()
        data['shared_at'] = datetime.fromisoformat(data['shared_at'])
        if 'last_updated' in data and data['last_updated']:
            data['last_updated'] = datetime.fromisoformat(data['last_updated'])
        return cls(**data)

    @property
    def display_name(self) -> str:
        """Get display name for the city."""
        return f"{self.city_name}, {self.country}"

    def matches_search(self, search_term: str) -> bool:
        """Check if city matches search term."""
        if not search_term:
            return True
        
        search_lower = search_term.lower()
        return (
            search_lower in self.city_name.lower() or
            search_lower in self.country.lower() or
            any(search_lower in tag.lower() for tag in self.tags) or
            search_lower in self.description.lower()
        )


@dataclass
class TeamComparison:
    """Represents a team weather comparison."""
    id: str
    title: str
    cities: List[str]  # City names in format "City, Country"
    metrics: List[str]  # Weather metrics to compare
    created_by: str
    created_at: datetime
    data: Dict[str, Dict[str, Any]]  # Comparison data
    description: str = ""
    is_public: bool = True
    last_updated: Optional[datetime] = None
    
    def __post_init__(self):
        if self.last_updated is None:
            self.last_updated = self.created_at

    def to_dict(self) -> Dict[str, Any]:
        """Convert comparison to dictionary."""
        data = asdict(self)
        data['created_at'] = self.created_at.isoformat()
        if self.last_updated:
            data['last_updated'] = self.last_updated.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TeamComparison':
        """Create comparison from dictionary."""
        data = data.copy()
        data['created_at'] = datetime.fromisoformat(data['created_at'])
        if 'last_updated' in data and data['last_updated']:
            data['last_updated'] = datetime.fromisoformat(data['last_updated'])
        return cls(**data)

    @property
    def cities_count(self) -> int:
        """Get number of cities in comparison."""
        return len(self.cities)

    @property
    def metrics_count(self) -> int:
        """Get number of metrics in comparison."""
        return len(self.metrics)

    def has_data_for_city(self, city_name: str) -> bool:
        """Check if comparison has data for given city."""
        return city_name in self.data

    def get_metric_value(self, city_name: str, metric: str) -> Any:
        """Get metric value for a specific city."""
        if city_name in self.data and metric in self.data[city_name]:
            return self.data[city_name][metric]
        return None


@dataclass
class ActivityItem:
    """Represents a team activity item."""
    id: str
    type: str  # city_shared, comparison_created, data_updated, member_joined
    description: str
    user: str
    timestamp: datetime
    details: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.details is None:
            self.details = {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert activity item to dictionary."""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ActivityItem':
        """Create activity item from dictionary."""
        data = data.copy()
        data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        return cls(**data)

    @property
    def icon(self) -> str:
        """Get icon for activity type."""
        icons = {
            "city_shared": "🏙️",
            "comparison_created": "📊",
            "data_updated": "🔄",
            "member_joined": "👋",
            "default": "📝"
        }
        return icons.get(self.type, icons["default"])


@dataclass
class SyncStatus:
    """Represents synchronization status."""
    last_sync: Optional[datetime] = None
    is_syncing: bool = False
    sync_error: Optional[str] = None
    pending_changes: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert sync status to dictionary."""
        data = asdict(self)
        if self.last_sync:
            data['last_sync'] = self.last_sync.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SyncStatus':
        """Create sync status from dictionary."""
        data = data.copy()
        if 'last_sync' in data and data['last_sync']:
            data['last_sync'] = datetime.fromisoformat(data['last_sync'])
        return cls(**data)

    @property
    def is_connected(self) -> bool:
        """Check if currently connected and synced."""
        return self.last_sync is not None and not self.sync_error

    def format_last_sync(self) -> str:
        """Format last sync time for display."""
        if not self.last_sync:
            return "Never synced"
        
        now = datetime.now()
        diff = now - self.last_sync
        
        if diff.seconds < 60:
            return "Just now"
        elif diff.seconds < 3600:
            minutes = diff.seconds // 60
            return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
        elif diff.days == 0:
            hours = diff.seconds // 3600
            return f"{hours} hour{'s' if hours != 1 else ''} ago"
        elif diff.days == 1:
            return "Yesterday"
        else:
            return self.last_sync.strftime("%Y-%m-%d")


# Available weather metrics for comparisons
AVAILABLE_METRICS = [
    "temperature",
    "humidity", 
    "wind_speed",
    "pressure",
    "visibility",
    "uv_index",
    "feels_like",
    "dew_point",
    "cloud_cover"
]

# Metric display names
METRIC_DISPLAY_NAMES = {
    "temperature": "Temperature",
    "humidity": "Humidity",
    "wind_speed": "Wind Speed", 
    "pressure": "Pressure",
    "visibility": "Visibility",
    "uv_index": "UV Index",
    "feels_like": "Feels Like",
    "dew_point": "Dew Point",
    "cloud_cover": "Cloud Cover"
}

# Metric units
METRIC_UNITS = {
    "temperature": "°C",
    "humidity": "%",
    "wind_speed": "km/h",
    "pressure": "hPa", 
    "visibility": "km",
    "uv_index": "",
    "feels_like": "°C",
    "dew_point": "°C",
    "cloud_cover": "%"
}