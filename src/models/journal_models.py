"""Journal models for weather journal functionality."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any, List


@dataclass
class JournalEntry:
    """Model for a weather journal entry."""
    id: Optional[int] = None
    date: datetime = field(default_factory=datetime.now)
    weather_data: Optional[Dict[str, Any]] = None
    mood_score: int = 5  # 1-10 scale
    mood_tags: List[str] = field(default_factory=list)
    title: str = ""
    content: str = ""
    photos: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    location: str = ""
    temperature: Optional[float] = None
    weather_condition: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert journal entry to dictionary."""
        return {
            'id': self.id,
            'date': self.date.isoformat() if self.date else None,
            'weather_data': self.weather_data,
            'mood_score': self.mood_score,
            'mood_tags': self.mood_tags,
            'title': self.title,
            'content': self.content,
            'photos': self.photos,
            'tags': self.tags,
            'location': self.location,
            'temperature': self.temperature,
            'weather_condition': self.weather_condition
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'JournalEntry':
        """Create journal entry from dictionary."""
        entry = cls()
        entry.id = data.get('id')
        if data.get('date'):
            entry.date = datetime.fromisoformat(data['date'])
        entry.weather_data = data.get('weather_data')
        entry.mood_score = data.get('mood_score', 5)
        entry.mood_tags = data.get('mood_tags', [])
        entry.title = data.get('title', '')
        entry.content = data.get('content', '')
        entry.photos = data.get('photos', [])
        entry.tags = data.get('tags', [])
        entry.location = data.get('location', '')
        entry.temperature = data.get('temperature')
        entry.weather_condition = data.get('weather_condition', '')
        return entry


@dataclass
class MoodAnalysis:
    """Model for mood analysis results."""
    average_mood: float
    weather_correlation: Dict[str, float]
    seasonal_patterns: Dict[str, float]
    best_weather_for_mood: str
    recommendations: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert mood analysis to dictionary."""
        return {
            'average_mood': self.average_mood,
            'weather_correlation': self.weather_correlation,
            'seasonal_patterns': self.seasonal_patterns,
            'best_weather_for_mood': self.best_weather_for_mood,
            'recommendations': self.recommendations
        }


# Predefined mood tags for consistency
MOOD_TAGS = [
    'happy', 'sad', 'energetic', 'tired', 'calm', 'anxious',
    'excited', 'peaceful', 'stressed', 'content', 'motivated',
    'relaxed', 'focused', 'creative', 'social', 'introspective'
]

# Weather condition mappings for analysis
WEATHER_CONDITIONS = {
    'clear': ['clear', 'sunny', 'bright'],
    'cloudy': ['cloudy', 'overcast', 'partly cloudy'],
    'rainy': ['rain', 'drizzle', 'shower', 'thunderstorm'],
    'snowy': ['snow', 'blizzard', 'sleet'],
    'foggy': ['fog', 'mist', 'haze'],
    'windy': ['windy', 'breezy', 'gusty']
}