"""Journal Entry Data Model

This module defines the data model for weather journal entries with proper
validation and weather correlation functionality.
"""

import json
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class JournalEntry:
    """Data model for weather journal entries.

    Represents a single journal entry with associated weather data,
    mood tracking, photo attachments, and rich text content.
    """

    id: Optional[int] = None
    date_created: datetime = field(default_factory=datetime.now)
    weather_data: Optional[Dict[str, Any]] = None
    mood_rating: Optional[int] = None  # 1-10 scale
    entry_content: str = ""
    tags: List[str] = field(default_factory=list)
    location: Optional[str] = None
    category: Optional[str] = None  # daily weather, travel, outdoor activities, etc.
    photos: List[str] = field(default_factory=list)  # List of photo file paths
    template_used: Optional[str] = None  # Template name if entry was created from template
    created_at: Optional[datetime] = field(default_factory=datetime.now)
    updated_at: Optional[datetime] = field(default_factory=datetime.now)

    def __post_init__(self):
        """Validate data after initialization."""
        self.validate()

    def validate(self) -> None:
        """Validate journal entry data.

        Raises:
            ValueError: If validation fails
        """
        if self.mood_rating is not None:
            if not isinstance(self.mood_rating, int) or not 1 <= self.mood_rating <= 10:
                raise ValueError("Mood rating must be an integer between 1 and 10")

        if not isinstance(self.entry_content, str):
            raise ValueError("Entry content must be a string")

        if not isinstance(self.tags, list):
            raise ValueError("Tags must be a list")

        if not isinstance(self.photos, list):
            raise ValueError("Photos must be a list")

        # Validate tags are strings
        for tag in self.tags:
            if not isinstance(tag, str):
                raise ValueError("All tags must be strings")

        # Validate photo paths are strings
        for photo in self.photos:
            if not isinstance(photo, str):
                raise ValueError("All photo paths must be strings")

        # Validate category if provided
        if self.category is not None and not isinstance(self.category, str):
            raise ValueError("Category must be a string")

        # Validate template_used if provided
        if self.template_used is not None and not isinstance(self.template_used, str):
            raise ValueError("Template used must be a string")

    def to_dict(self) -> Dict[str, Any]:
        """Convert journal entry to dictionary for database storage.

        Returns:
            Dictionary representation of the journal entry
        """
        return {
            "id": self.id,
            "date_created": self.date_created.isoformat(),
            "weather_data": json.dumps(self.weather_data) if self.weather_data else None,
            "mood_rating": self.mood_rating,
            "entry_content": self.entry_content,
            "tags": json.dumps(self.tags),
            "location": self.location,
            "category": self.category,
            "photos": json.dumps(self.photos),
            "template_used": self.template_used,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "JournalEntry":
        """Create journal entry from dictionary data.

        Args:
            data: Dictionary containing journal entry data

        Returns:
            JournalEntry instance
        """
        if not isinstance(data, dict):
            raise ValueError("Data must be a dictionary")
            
        # Parse datetime fields with error handling
        try:
            date_created = (
                datetime.fromisoformat(str(data["date_created"]))
                if data.get("date_created")
                else datetime.now()
            )
        except (ValueError, TypeError):
            date_created = datetime.now()
            
        try:
            created_at = (
                datetime.fromisoformat(str(data["created_at"])) 
                if data.get("created_at") 
                else datetime.now()
            )
        except (ValueError, TypeError):
            created_at = datetime.now()
            
        try:
            updated_at = (
                datetime.fromisoformat(str(data["updated_at"])) 
                if data.get("updated_at") 
                else datetime.now()
            )
        except (ValueError, TypeError):
            updated_at = datetime.now()

        # Parse JSON fields with error handling
        weather_data = None
        if data.get("weather_data"):
            try:
                if isinstance(data["weather_data"], str):
                    weather_data = json.loads(data["weather_data"])
                elif isinstance(data["weather_data"], dict):
                    weather_data = data["weather_data"]
            except (json.JSONDecodeError, TypeError):
                weather_data = None
                
        tags = []
        if data.get("tags"):
            try:
                if isinstance(data["tags"], str):
                    parsed_tags = json.loads(data["tags"])
                    tags = parsed_tags if isinstance(parsed_tags, list) else []
                elif isinstance(data["tags"], list):
                    tags = [str(tag) for tag in data["tags"] if tag is not None]
            except (json.JSONDecodeError, TypeError):
                tags = []
                
        photos = []
        if data.get("photos"):
            try:
                if isinstance(data["photos"], str):
                    parsed_photos = json.loads(data["photos"])
                    photos = parsed_photos if isinstance(parsed_photos, list) else []
                elif isinstance(data["photos"], list):
                    photos = [str(photo) for photo in data["photos"] if photo is not None]
            except (json.JSONDecodeError, TypeError):
                photos = []
        
        # Validate mood_rating
        mood_rating = data.get("mood_rating")
        if mood_rating is not None:
            try:
                mood_rating = int(mood_rating)
                if not 1 <= mood_rating <= 10:
                    mood_rating = None
            except (ValueError, TypeError):
                mood_rating = None

        return cls(
            id=data.get("id"),
            date_created=date_created,
            weather_data=weather_data,
            mood_rating=mood_rating,
            entry_content=str(data.get("entry_content", "")),
            tags=tags,
            location=str(data["location"]) if data.get("location") is not None else None,
            category=str(data["category"]) if data.get("category") is not None else None,
            photos=photos,
            template_used=str(data["template_used"]) if data.get("template_used") is not None else None,
            created_at=created_at,
            updated_at=updated_at,
        )

    def get_preview(self, max_length: int = 100) -> str:
        """Get a preview of the entry content.

        Args:
            max_length: Maximum length of preview text

        Returns:
            Truncated entry content for preview
        """
        if len(self.entry_content) <= max_length:
            return self.entry_content
        return self.entry_content[:max_length].rsplit(" ", 1)[0] + "..."

    def add_tag(self, tag: str) -> None:
        """Add a tag to the entry.

        Args:
            tag: Tag to add
        """
        if tag and tag not in self.tags:
            self.tags.append(tag.strip().lower())

    def remove_tag(self, tag: str) -> None:
        """Remove a tag from the entry.

        Args:
            tag: Tag to remove
        """
        if tag in self.tags:
            self.tags.remove(tag)

    def add_photo(self, photo_path: str) -> None:
        """Add a photo to the entry.

        Args:
            photo_path: Path to the photo file
        """
        if photo_path and photo_path not in self.photos:
            self.photos.append(photo_path)
            self.updated_at = datetime.now()

    def remove_photo(self, photo_path: str) -> None:
        """Remove a photo from the entry.

        Args:
            photo_path: Path to the photo file to remove
        """
        if photo_path in self.photos:
            self.photos.remove(photo_path)
            self.updated_at = datetime.now()

    def get_photo_count(self) -> int:
        """Get the number of photos attached to this entry.

        Returns:
            Number of photos
        """
        return len(self.photos)

    def has_photos(self) -> bool:
        """Check if the entry has any photos.

        Returns:
            True if entry has photos, False otherwise
        """
        return len(self.photos) > 0

    def get_weather_condition(self) -> Optional[str]:
        """Extract weather condition from weather data.

        Returns:
            Weather condition string or None
        """
        if self.weather_data and "weather" in self.weather_data:
            weather_list = self.weather_data["weather"]
            if weather_list and len(weather_list) > 0:
                return weather_list[0].get("main", "").lower()
        return None

    def get_temperature(self) -> Optional[float]:
        """Extract temperature from weather data.

        Returns:
            Temperature in Celsius or None
        """
        if self.weather_data and "main" in self.weather_data:
            return self.weather_data["main"].get("temp")
        return None

    def get_mood_description(self) -> str:
        """Get a descriptive text for the mood rating.

        Returns:
            Mood description string
        """
        if self.mood_rating is None:
            return "Not rated"

        mood_descriptions = {
            1: "Terrible",
            2: "Very Bad",
            3: "Bad",
            4: "Poor",
            5: "Okay",
            6: "Good",
            7: "Very Good",
            8: "Great",
            9: "Excellent",
            10: "Perfect",
        }
        return mood_descriptions.get(self.mood_rating, "Unknown")

    def matches_search_terms(self, search_terms: List[str]) -> bool:
        """Check if entry matches search terms.

        Args:
            search_terms: List of search terms to match

        Returns:
            True if entry matches any search term
        """
        if not search_terms:
            return True

        searchable_text = f"{self.entry_content} {' '.join(self.tags)} {self.location or ''} {self.category or ''}".lower()

        return any(term.lower() in searchable_text for term in search_terms)

    def update_timestamp(self) -> None:
        """Update the updated_at timestamp to current time."""
        self.updated_at = datetime.now()

    def get_search_text(self) -> str:
        """Get all searchable text content for full-text search.

        Returns:
            Combined searchable text
        """
        parts = [self.entry_content]

        if self.tags:
            parts.extend(self.tags)

        if self.location:
            parts.append(self.location)

        if self.category:
            parts.append(self.category)

        if self.weather_data:
            weather_condition = self.get_weather_condition()
            if weather_condition:
                parts.append(weather_condition)

        return " ".join(parts)

    @staticmethod
    def get_available_categories() -> List[str]:
        """Get list of available entry categories.

        Returns:
            List of category names
        """
        return [
            "daily weather",
            "travel",
            "outdoor activities",
            "seasonal observations",
            "weather events",
            "personal reflection",
            "photography",
            "nature",
            "sports",
            "gardening",
        ]

    @staticmethod
    def get_available_templates() -> Dict[str, Dict[str, Any]]:
        """Get available entry templates.

        Returns:
            Dictionary of template configurations
        """
        return {
            "daily_weather": {
                "name": "Daily Weather",
                "category": "daily weather",
                "content_template": "Today's weather: {weather_condition}\nTemperature: {temperature}°C\n\nHow I felt: \nWhat I did: \nNotable observations: ",
                "suggested_tags": ["daily", "routine", "weather"],
            },
            "travel": {
                "name": "Travel Entry",
                "category": "travel",
                "content_template": "Location: {location}\nWeather: {weather_condition}\nTemperature: {temperature}°C\n\nTravel highlights: \nWeather impact: \nMemorable moments: ",
                "suggested_tags": ["travel", "adventure", "exploration"],
            },
            "outdoor_activity": {
                "name": "Outdoor Activity",
                "category": "outdoor activities",
                "content_template": "Activity: \nLocation: {location}\nWeather conditions: {weather_condition}\nTemperature: {temperature}°C\n\nActivity details: \nWeather impact: \nOverall experience: ",
                "suggested_tags": ["outdoor", "activity", "exercise"],
            },
            "weather_event": {
                "name": "Weather Event",
                "category": "weather events",
                "content_template": "Weather event: {weather_condition}\nLocation: {location}\nTemperature: {temperature}°C\n\nEvent description: \nImpact: \nPersonal observations: ",
                "suggested_tags": ["weather", "event", "observation"],
            },
        }

    def has_weather_data(self) -> bool:
        """Check if entry has associated weather data.

        Returns:
            True if weather data exists
        """
        return self.weather_data is not None and len(self.weather_data) > 0

    def get_weather_summary(self) -> str:
        """Get a summary of weather conditions.

        Returns:
            Human-readable weather summary
        """
        if not self.has_weather_data():
            return "No weather data available"

        try:
            temp = self.weather_data.get("temperature", "N/A")
            condition = self.weather_data.get("condition", "Unknown")
            humidity = self.weather_data.get("humidity", "N/A")

            return f"{condition}, {temp}°F, {humidity}% humidity"
        except (KeyError, TypeError):
            return "Weather data format error"

    def __str__(self) -> str:
        """String representation of journal entry."""
        return f"JournalEntry(date={self.date_created.strftime('%Y-%m-%d %H:%M')}, preview='{self.get_preview(50)}')"

    def __repr__(self) -> str:
        """Detailed string representation."""
        return (
            f"JournalEntry(id={self.id}, date_created={self.date_created}, "
            f"mood_rating={self.mood_rating}, tags={self.tags}, "
            f"has_weather={self.has_weather_data()})"
        )
