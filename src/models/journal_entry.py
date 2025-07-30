"""Journal Entry Data Model

This module defines the data model for weather journal entries with proper
validation and weather correlation functionality.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any, List
import json


@dataclass
class JournalEntry:
    """Data model for weather journal entries.
    
    Represents a single journal entry with associated weather data,
    mood tracking, and rich text content.
    """
    
    id: Optional[int] = None
    date_created: datetime = field(default_factory=datetime.now)
    weather_data: Optional[Dict[str, Any]] = None
    mood_rating: Optional[int] = None  # 1-10 scale
    entry_content: str = ""
    tags: List[str] = field(default_factory=list)
    location: Optional[str] = None
    
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
        
        # Validate tags are strings
        for tag in self.tags:
            if not isinstance(tag, str):
                raise ValueError("All tags must be strings")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert journal entry to dictionary for database storage.
        
        Returns:
            Dictionary representation of the journal entry
        """
        return {
            'id': self.id,
            'date_created': self.date_created.isoformat(),
            'weather_data': json.dumps(self.weather_data) if self.weather_data else None,
            'mood_rating': self.mood_rating,
            'entry_content': self.entry_content,
            'tags': json.dumps(self.tags),
            'location': self.location
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'JournalEntry':
        """Create journal entry from dictionary data.
        
        Args:
            data: Dictionary containing journal entry data
            
        Returns:
            JournalEntry instance
        """
        # Parse datetime
        date_created = datetime.fromisoformat(data['date_created']) if data.get('date_created') else datetime.now()
        
        # Parse JSON fields
        weather_data = json.loads(data['weather_data']) if data.get('weather_data') else None
        tags = json.loads(data['tags']) if data.get('tags') else []
        
        return cls(
            id=data.get('id'),
            date_created=date_created,
            weather_data=weather_data,
            mood_rating=data.get('mood_rating'),
            entry_content=data.get('entry_content', ''),
            tags=tags,
            location=data.get('location')
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
        return self.entry_content[:max_length].rsplit(' ', 1)[0] + '...'
    
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
            temp = self.weather_data.get('temperature', 'N/A')
            condition = self.weather_data.get('condition', 'Unknown')
            humidity = self.weather_data.get('humidity', 'N/A')
            
            return f"{condition}, {temp}°F, {humidity}% humidity"
        except (KeyError, TypeError):
            return "Weather data format error"
    
    def __str__(self) -> str:
        """String representation of journal entry."""
        return f"JournalEntry(date={self.date_created.strftime('%Y-%m-%d %H:%M')}, preview='{self.get_preview(50)}')"
    
    def __repr__(self) -> str:
        """Detailed string representation."""
        return (f"JournalEntry(id={self.id}, date_created={self.date_created}, "
                f"mood_rating={self.mood_rating}, tags={self.tags}, "
                f"has_weather={self.has_weather_data()})")