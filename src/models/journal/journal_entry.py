"""Journal entry model with weather integration and mood tracking."""

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class Mood(Enum):
    """Mood enumeration for journal entries."""

    HAPPY = "happy"
    NEUTRAL = "neutral"
    SAD = "sad"
    ENERGETIC = "energetic"
    TIRED = "tired"
    EXCITED = "excited"
    CALM = "calm"
    ANXIOUS = "anxious"
    CONTENT = "content"
    FRUSTRATED = "frustrated"

    @property
    def emoji(self) -> str:
        """Get emoji representation of mood."""
        mood_emojis = {
            self.HAPPY: "😊",
            self.NEUTRAL: "😐",
            self.SAD: "😢",
            self.ENERGETIC: "⚡",
            self.TIRED: "😴",
            self.EXCITED: "🤩",
            self.CALM: "😌",
            self.ANXIOUS: "😰",
            self.CONTENT: "😇",
            self.FRUSTRATED: "😤",
        }
        return mood_emojis.get(self, "😐")

    @property
    def color(self) -> str:
        """Get color representation of mood."""
        mood_colors = {
            self.HAPPY: "#4CAF50",  # Green
            self.NEUTRAL: "#9E9E9E",  # Gray
            self.SAD: "#2196F3",  # Blue
            self.ENERGETIC: "#FF9800",  # Orange
            self.TIRED: "#673AB7",  # Purple
            self.EXCITED: "#E91E63",  # Pink
            self.CALM: "#00BCD4",  # Cyan
            self.ANXIOUS: "#F44336",  # Red
            self.CONTENT: "#8BC34A",  # Light Green
            self.FRUSTRATED: "#FF5722",  # Deep Orange
        }
        return mood_colors.get(self, "#9E9E9E")


@dataclass
class WeatherSnapshot:
    """Weather data snapshot for journal entries."""

    temperature: float
    feels_like: float
    condition: str
    description: str
    humidity: int
    pressure: float
    wind_speed: float
    wind_direction: Optional[int] = None
    visibility: Optional[float] = None
    uv_index: Optional[float] = None
    cloudiness: Optional[int] = None
    icon: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "temperature": self.temperature,
            "feels_like": self.feels_like,
            "condition": self.condition,
            "description": self.description,
            "humidity": self.humidity,
            "pressure": self.pressure,
            "wind_speed": self.wind_speed,
            "wind_direction": self.wind_direction,
            "visibility": self.visibility,
            "uv_index": self.uv_index,
            "cloudiness": self.cloudiness,
            "icon": self.icon,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WeatherSnapshot":
        """Create from dictionary."""
        return cls(**data)

    @property
    def summary(self) -> str:
        """Get a human-readable weather summary."""
        return f"{self.temperature:.1f}°C, {self.description}, {self.humidity}% humidity"


@dataclass
class JournalEntry:
    """Journal entry with weather integration and mood tracking."""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    # Location and weather
    location: str = ""
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    weather_snapshot: Optional[WeatherSnapshot] = None

    # Mood and content
    mood: Optional[Mood] = None
    title: str = ""
    content: str = ""
    formatted_content: str = ""  # Rich text HTML content

    # Attachments and metadata
    photo_paths: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    word_count: int = 0

    # Auto-save tracking
    is_auto_saved: bool = False
    last_auto_save: Optional[datetime] = None

    def __post_init__(self):
        """Post-initialization processing."""
        self.update_word_count()

    def update_content(self, content: str, formatted_content: str = ""):
        """Update content and metadata."""
        self.content = content
        self.formatted_content = formatted_content or content
        self.updated_at = datetime.now()
        self.update_word_count()
        self.is_auto_saved = False

    def update_word_count(self):
        """Update word count from content."""
        # Remove HTML tags for word counting
        import re

        clean_text = re.sub(r"<[^>]+>", "", self.content)
        self.word_count = len(clean_text.split())

    def add_photo(self, photo_path: str):
        """Add photo attachment."""
        if photo_path not in self.photo_paths:
            self.photo_paths.append(photo_path)
            self.updated_at = datetime.now()
            self.is_auto_saved = False

    def remove_photo(self, photo_path: str):
        """Remove photo attachment."""
        if photo_path in self.photo_paths:
            self.photo_paths.remove(photo_path)
            self.updated_at = datetime.now()
            self.is_auto_saved = False

    def add_tag(self, tag: str):
        """Add tag to entry."""
        tag = tag.strip().lower()
        if tag and tag not in self.tags:
            self.tags.append(tag)
            self.updated_at = datetime.now()
            self.is_auto_saved = False

    def remove_tag(self, tag: str):
        """Remove tag from entry."""
        tag = tag.strip().lower()
        if tag in self.tags:
            self.tags.remove(tag)
            self.updated_at = datetime.now()
            self.is_auto_saved = False

    def mark_auto_saved(self):
        """Mark entry as auto-saved."""
        self.is_auto_saved = True
        self.last_auto_save = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "location": self.location,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "weather_snapshot": self.weather_snapshot.to_dict() if self.weather_snapshot else None,
            "mood": self.mood.value if self.mood else None,
            "title": self.title,
            "content": self.content,
            "formatted_content": self.formatted_content,
            "photo_paths": self.photo_paths,
            "tags": self.tags,
            "word_count": self.word_count,
            "is_auto_saved": self.is_auto_saved,
            "last_auto_save": self.last_auto_save.isoformat() if self.last_auto_save else None,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "JournalEntry":
        """Create from dictionary."""
        # Parse datetime fields
        created_at = datetime.fromisoformat(data["created_at"])
        updated_at = datetime.fromisoformat(data["updated_at"])
        last_auto_save = (
            datetime.fromisoformat(data["last_auto_save"]) if data.get("last_auto_save") else None
        )

        # Parse weather snapshot
        weather_snapshot = None
        if data.get("weather_snapshot"):
            weather_snapshot = WeatherSnapshot.from_dict(data["weather_snapshot"])

        # Parse mood
        mood = None
        if data.get("mood"):
            mood = Mood(data["mood"])

        return cls(
            id=data["id"],
            created_at=created_at,
            updated_at=updated_at,
            location=data.get("location", ""),
            latitude=data.get("latitude"),
            longitude=data.get("longitude"),
            weather_snapshot=weather_snapshot,
            mood=mood,
            title=data.get("title", ""),
            content=data.get("content", ""),
            formatted_content=data.get("formatted_content", ""),
            photo_paths=data.get("photo_paths", []),
            tags=data.get("tags", []),
            word_count=data.get("word_count", 0),
            is_auto_saved=data.get("is_auto_saved", False),
            last_auto_save=last_auto_save,
        )

    @property
    def preview_text(self) -> str:
        """Get preview text for entry list."""
        # Remove HTML tags and get first 100 characters
        import re

        clean_text = re.sub(r"<[^>]+>", "", self.content)
        return clean_text[:100] + "..." if len(clean_text) > 100 else clean_text

    @property
    def date_str(self) -> str:
        """Get formatted date string."""
        return self.created_at.strftime("%B %d, %Y")

    @property
    def time_str(self) -> str:
        """Get formatted time string."""
        return self.created_at.strftime("%I:%M %p")

    @property
    def mood_display(self) -> str:
        """Get mood display with emoji."""
        if self.mood:
            return f"{self.mood.emoji} {self.mood.value.title()}"
        return "😐 No mood set"

    @property
    def weather_display(self) -> str:
        """Get weather display string."""
        if self.weather_snapshot:
            return self.weather_snapshot.summary
        return "No weather data"
