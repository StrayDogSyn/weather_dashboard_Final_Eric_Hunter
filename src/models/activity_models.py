"""Activity models for AI-powered activity suggestions."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class ActivityCategory(Enum):
    """Categories for activities."""

    FITNESS = "fitness"
    OUTDOOR = "outdoor"
    CREATIVE = "creative"
    SOCIAL = "social"
    RELAXATION = "relaxation"
    EDUCATIONAL = "educational"
    ENTERTAINMENT = "entertainment"
    SPORTS = "sports"
    ADVENTURE = "adventure"
    CULTURAL = "cultural"


class DifficultyLevel(Enum):
    """Difficulty levels for activities."""

    VERY_EASY = 1
    EASY = 2
    MODERATE = 3
    HARD = 4
    VERY_HARD = 5


class CostRange(Enum):
    """Cost ranges for activities."""

    FREE = "free"
    LOW = "low"  # $1-20
    MEDIUM = "medium"  # $21-50
    HIGH = "high"  # $51+


@dataclass
class ActivitySuggestion:
    """Model for an AI-generated activity suggestion."""

    id: str
    title: str
    description: str
    category: ActivityCategory
    indoor: bool
    duration_minutes: int
    difficulty_level: int  # 1-5
    equipment_needed: List[str] = field(default_factory=list)
    weather_suitability: Dict[str, float] = field(default_factory=dict)
    cost_estimate: str = "free"
    safety_considerations: List[str] = field(default_factory=list)
    user_rating: Optional[int] = None
    times_suggested: int = 0
    times_completed: int = 0
    last_suggested: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """Convert activity suggestion to dictionary."""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "category": self.category.value,
            "indoor": self.indoor,
            "duration_minutes": self.duration_minutes,
            "difficulty_level": self.difficulty_level,
            "equipment_needed": self.equipment_needed,
            "weather_suitability": self.weather_suitability,
            "cost_estimate": self.cost_estimate,
            "safety_considerations": self.safety_considerations,
            "user_rating": self.user_rating,
            "times_suggested": self.times_suggested,
            "times_completed": self.times_completed,
            "last_suggested": self.last_suggested.isoformat() if self.last_suggested else None,
            "created_at": self.created_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ActivitySuggestion":
        """Create activity suggestion from dictionary."""
        suggestion = cls(
            id=data["id"],
            title=data["title"],
            description=data["description"],
            category=ActivityCategory(data["category"]),
            indoor=data["indoor"],
            duration_minutes=data["duration_minutes"],
            difficulty_level=data["difficulty_level"],
            equipment_needed=data.get("equipment_needed", []),
            weather_suitability=data.get("weather_suitability", {}),
            cost_estimate=data.get("cost_estimate", "free"),
            safety_considerations=data.get("safety_considerations", []),
            user_rating=data.get("user_rating"),
            times_suggested=data.get("times_suggested", 0),
            times_completed=data.get("times_completed", 0),
        )

        if data.get("last_suggested"):
            suggestion.last_suggested = datetime.fromisoformat(data["last_suggested"])
        if data.get("created_at"):
            suggestion.created_at = datetime.fromisoformat(data["created_at"])

        return suggestion

    def get_suitability_score(self, weather_condition: str = "current") -> float:
        """Get weather suitability score for given condition.

        Args:
            weather_condition: Weather condition key

        Returns:
            Suitability score (0.0 to 1.0)
        """
        return self.weather_suitability.get(weather_condition, 0.5)

    def is_suitable_for_time(self, available_minutes: int) -> bool:
        """Check if activity fits in available time.

        Args:
            available_minutes: Available time in minutes

        Returns:
            True if activity fits, False otherwise
        """
        return self.duration_minutes <= available_minutes

    def matches_difficulty(self, user_fitness_level: int, tolerance: int = 1) -> bool:
        """Check if activity difficulty matches user fitness level.

        Args:
            user_fitness_level: User's fitness level (1-5)
            tolerance: Allowed difficulty difference

        Returns:
            True if difficulty is appropriate, False otherwise
        """
        return abs(self.difficulty_level - user_fitness_level) <= tolerance


@dataclass
class UserPreferences:
    """Model for user activity preferences and history."""

    user_id: str = "default"
    favorite_categories: List[ActivityCategory] = field(default_factory=list)
    fitness_level: int = 3  # 1-5 scale
    budget_range: str = "free"
    equipment_available: List[str] = field(default_factory=list)
    time_availability: int = 60  # minutes
    indoor_preference: float = 0.5  # 0.0 (outdoor) to 1.0 (indoor)
    activity_history: List[str] = field(default_factory=list)
    completed_activities: List[str] = field(default_factory=list)
    rated_activities: Dict[str, int] = field(default_factory=dict)
    blacklisted_activities: List[str] = field(default_factory=list)
    preferred_times: List[str] = field(default_factory=lambda: ["morning", "afternoon", "evening"])
    weather_preferences: Dict[str, float] = field(default_factory=dict)
    last_updated: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """Convert user preferences to dictionary."""
        return {
            "user_id": self.user_id,
            "favorite_categories": [cat.value for cat in self.favorite_categories],
            "fitness_level": self.fitness_level,
            "budget_range": self.budget_range,
            "equipment_available": self.equipment_available,
            "time_availability": self.time_availability,
            "indoor_preference": self.indoor_preference,
            "activity_history": self.activity_history,
            "completed_activities": self.completed_activities,
            "rated_activities": self.rated_activities,
            "blacklisted_activities": self.blacklisted_activities,
            "preferred_times": self.preferred_times,
            "weather_preferences": self.weather_preferences,
            "last_updated": self.last_updated.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "UserPreferences":
        """Create user preferences from dictionary."""
        preferences = cls(
            user_id=data.get("user_id", "default"),
            favorite_categories=[
                ActivityCategory(cat) for cat in data.get("favorite_categories", [])
            ],
            fitness_level=data.get("fitness_level", 3),
            budget_range=data.get("budget_range", "free"),
            equipment_available=data.get("equipment_available", []),
            time_availability=data.get("time_availability", 60),
            indoor_preference=data.get("indoor_preference", 0.5),
            activity_history=data.get("activity_history", []),
            completed_activities=data.get("completed_activities", []),
            rated_activities=data.get("rated_activities", {}),
            blacklisted_activities=data.get("blacklisted_activities", []),
            preferred_times=data.get("preferred_times", ["morning", "afternoon", "evening"]),
            weather_preferences=data.get("weather_preferences", {}),
        )

        if data.get("last_updated"):
            preferences.last_updated = datetime.fromisoformat(data["last_updated"])

        return preferences

    def add_activity_rating(self, activity_id: str, rating: int):
        """Add or update activity rating.

        Args:
            activity_id: Activity identifier
            rating: Rating (1-5)
        """
        self.rated_activities[activity_id] = rating
        self.last_updated = datetime.now()

    def complete_activity(self, activity_id: str):
        """Mark activity as completed.

        Args:
            activity_id: Activity identifier
        """
        if activity_id not in self.completed_activities:
            self.completed_activities.append(activity_id)
        self.last_updated = datetime.now()

    def blacklist_activity(self, activity_id: str):
        """Add activity to blacklist.

        Args:
            activity_id: Activity identifier
        """
        if activity_id not in self.blacklisted_activities:
            self.blacklisted_activities.append(activity_id)
        self.last_updated = datetime.now()

    def get_category_preference_score(self, category: ActivityCategory) -> float:
        """Get preference score for activity category.

        Args:
            category: Activity category

        Returns:
            Preference score (0.0 to 1.0)
        """
        if category in self.favorite_categories:
            return 1.0
        return 0.3  # Neutral score for non-favorite categories


@dataclass
class TimeContext:
    """Model for time and scheduling context."""

    current_time: datetime = field(default_factory=datetime.now)
    available_minutes: int = 60
    time_of_day: str = ""  # morning, afternoon, evening, night
    day_of_week: str = ""
    season: str = ""
    is_weekend: bool = False
    is_holiday: bool = False

    def __post_init__(self):
        """Initialize computed fields."""
        if not self.time_of_day:
            hour = self.current_time.hour
            if 5 <= hour < 12:
                self.time_of_day = "morning"
            elif 12 <= hour < 17:
                self.time_of_day = "afternoon"
            elif 17 <= hour < 21:
                self.time_of_day = "evening"
            else:
                self.time_of_day = "night"

        if not self.day_of_week:
            self.day_of_week = self.current_time.strftime("%A").lower()

        if not self.season:
            month = self.current_time.month
            if month in [12, 1, 2]:
                self.season = "winter"
            elif month in [3, 4, 5]:
                self.season = "spring"
            elif month in [6, 7, 8]:
                self.season = "summer"
            else:
                self.season = "autumn"

        self.is_weekend = self.current_time.weekday() >= 5

    def to_dict(self) -> Dict[str, Any]:
        """Convert time context to dictionary."""
        return {
            "current_time": self.current_time.isoformat(),
            "available_minutes": self.available_minutes,
            "time_of_day": self.time_of_day,
            "day_of_week": self.day_of_week,
            "season": self.season,
            "is_weekend": self.is_weekend,
            "is_holiday": self.is_holiday,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TimeContext":
        """Create time context from dictionary."""
        context = cls(
            current_time=datetime.fromisoformat(data["current_time"]),
            available_minutes=data.get("available_minutes", 60),
            time_of_day=data.get("time_of_day", ""),
            day_of_week=data.get("day_of_week", ""),
            season=data.get("season", ""),
            is_weekend=data.get("is_weekend", False),
            is_holiday=data.get("is_holiday", False),
        )
        return context


@dataclass
class ActivityPlan:
    """Model for planned activities."""

    id: str
    activity_suggestion: ActivitySuggestion
    planned_date: datetime
    planned_duration: int
    status: str = "planned"  # planned, in_progress, completed, cancelled
    notes: str = ""
    weather_forecast: Optional[Dict[str, Any]] = None
    reminders: List[datetime] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """Convert activity plan to dictionary."""
        return {
            "id": self.id,
            "activity_suggestion": self.activity_suggestion.to_dict(),
            "planned_date": self.planned_date.isoformat(),
            "planned_duration": self.planned_duration,
            "status": self.status,
            "notes": self.notes,
            "weather_forecast": self.weather_forecast,
            "reminders": [r.isoformat() for r in self.reminders],
            "created_at": self.created_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ActivityPlan":
        """Create activity plan from dictionary."""
        plan = cls(
            id=data["id"],
            activity_suggestion=ActivitySuggestion.from_dict(data["activity_suggestion"]),
            planned_date=datetime.fromisoformat(data["planned_date"]),
            planned_duration=data["planned_duration"],
            status=data.get("status", "planned"),
            notes=data.get("notes", ""),
            weather_forecast=data.get("weather_forecast"),
        )

        if data.get("reminders"):
            plan.reminders = [datetime.fromisoformat(r) for r in data["reminders"]]
        if data.get("created_at"):
            plan.created_at = datetime.fromisoformat(data["created_at"])

        return plan


# Default equipment categories
EQUIPMENT_CATEGORIES = {
    "fitness": [
        "yoga mat",
        "dumbbells",
        "resistance bands",
        "running shoes",
        "water bottle",
        "towel",
        "fitness tracker",
    ],
    "outdoor": [
        "hiking boots",
        "backpack",
        "sunscreen",
        "hat",
        "sunglasses",
        "first aid kit",
        "map",
        "compass",
        "flashlight",
    ],
    "creative": [
        "sketchbook",
        "pencils",
        "paints",
        "brushes",
        "camera",
        "notebook",
        "pens",
        "craft supplies",
    ],
    "sports": ["ball", "racket", "helmet", "protective gear", "cleats", "gloves", "sports bag"],
    "water": ["swimsuit", "goggles", "towel", "sunscreen", "life jacket", "snorkel", "fins"],
}

# Activity difficulty descriptions
DIFFICULTY_DESCRIPTIONS = {
    1: "Very Easy - Suitable for beginners, minimal physical effort",
    2: "Easy - Light activity, comfortable for most people",
    3: "Moderate - Some physical effort required, average fitness",
    4: "Hard - Challenging activity, good fitness level needed",
    5: "Very Hard - Intense activity, high fitness level required",
}
