"""Data models and enums for the Activity Suggester feature.

This module contains all data structures, enums, and model classes used
throughout the activity suggester system.
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any


class ActivityCategory(Enum):
    """Activity categories for organization and filtering."""
    OUTDOOR = "outdoor"
    INDOOR = "indoor"
    SPORTS = "sports"
    CREATIVE = "creative"
    SOCIAL = "social"
    RELAXATION = "relaxation"
    EXERCISE = "exercise"
    ENTERTAINMENT = "entertainment"
    EDUCATIONAL = "educational"
    CULINARY = "culinary"


class WeatherSuitability(Enum):
    """Weather suitability ratings for activities."""
    PERFECT = "perfect"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"
    UNSUITABLE = "unsuitable"


class DifficultyLevel(Enum):
    """Activity difficulty levels."""
    EASY = "easy"
    MODERATE = "moderate"
    CHALLENGING = "challenging"
    EXPERT = "expert"


@dataclass
class ActivitySuggestion:
    """Data class for activity suggestions."""
    id: Optional[int] = None
    title: str = ""
    description: str = ""
    category: ActivityCategory = ActivityCategory.OUTDOOR
    difficulty: DifficultyLevel = DifficultyLevel.EASY
    duration_minutes: int = 60
    weather_suitability: WeatherSuitability = WeatherSuitability.GOOD
    required_items: List[str] = field(default_factory=list)
    location_type: str = "anywhere"  # indoor, outdoor, specific location
    cost_estimate: str = "free"  # free, low, medium, high
    group_size: str = "any"  # solo, small group, large group, any
    ai_reasoning: str = ""
    confidence_score: float = 0.0
    weather_condition: Optional[str] = None
    temperature: Optional[float] = None
    created_at: Optional[datetime] = None
    is_favorite: bool = False
    user_rating: Optional[int] = None
    times_suggested: int = 0
    times_completed: int = 0
    spotify_playlist_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        data = asdict(self)
        # Convert enums to strings
        data['category'] = self.category.value
        data['difficulty'] = self.difficulty.value
        data['weather_suitability'] = self.weather_suitability.value
        # Convert datetime to ISO string
        if self.created_at:
            data['created_at'] = self.created_at.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ActivitySuggestion':
        """Create from dictionary."""
        # Convert string enums back to enum objects
        if 'category' in data and isinstance(data['category'], str):
            data['category'] = ActivityCategory(data['category'])
        if 'difficulty' in data and isinstance(data['difficulty'], str):
            data['difficulty'] = DifficultyLevel(data['difficulty'])
        if 'weather_suitability' in data and isinstance(data['weather_suitability'], str):
            data['weather_suitability'] = WeatherSuitability(data['weather_suitability'])
        # Convert ISO string to datetime
        if 'created_at' in data and isinstance(data['created_at'], str):
            data['created_at'] = datetime.fromisoformat(data['created_at'])

        return cls(**data)


@dataclass
class UserPreferences:
    """User preferences for activity suggestions."""
    preferred_categories: List[ActivityCategory] = field(default_factory=list)
    preferred_difficulty: List[DifficultyLevel] = field(default_factory=list)
    max_duration_minutes: int = 180
    budget_preference: str = "any"  # free, low, medium, high, any
    group_preference: str = "any"  # solo, small, large, any
    indoor_outdoor_preference: str = "any"  # indoor, outdoor, any
    avoid_categories: List[ActivityCategory] = field(default_factory=list)
    favorite_activities: List[str] = field(default_factory=list)
    completed_activities: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        data = asdict(self)
        data['preferred_categories'] = [cat.value for cat in self.preferred_categories]
        data['preferred_difficulty'] = [diff.value for diff in self.preferred_difficulty]
        data['avoid_categories'] = [cat.value for cat in self.avoid_categories]
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UserPreferences':
        """Create from dictionary."""
        if 'preferred_categories' in data:
            data['preferred_categories'] = [ActivityCategory(cat) for cat in data['preferred_categories']]
        if 'preferred_difficulty' in data:
            data['preferred_difficulty'] = [DifficultyLevel(diff) for diff in data['preferred_difficulty']]
        if 'avoid_categories' in data:
            data['avoid_categories'] = [ActivityCategory(cat) for cat in data['avoid_categories']]

        return cls(**data)