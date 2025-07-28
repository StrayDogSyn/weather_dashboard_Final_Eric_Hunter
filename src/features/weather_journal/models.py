#!/usr/bin/env python3
"""
Weather Journal Models - Data structures and enums

This module contains all data models, enums, and data structures
used by the Weather Journal feature.
"""

from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum


class EntryMood(Enum):
    """
    Mood options for journal entries.

    This enum provides structured mood tracking
    for weather correlation analysis.
    """
    VERY_HAPPY = "😄"
    HAPPY = "😊"
    NEUTRAL = "😐"
    SAD = "😔"
    VERY_SAD = "😢"
    ENERGETIC = "⚡"
    CALM = "😌"
    ANXIOUS = "😰"
    EXCITED = "🤩"
    TIRED = "😴"


class SearchFilter(Enum):
    """
    Search filter options for journal entries.

    This enum supports comprehensive search capabilities
    with multiple filtering criteria.
    """
    ALL = "all"
    TITLE = "title"
    CONTENT = "content"
    MOOD = "mood"
    WEATHER = "weather"
    DATE = "date"
    TAGS = "tags"


@dataclass
class JournalEntry:
    """
    Journal entry data structure.

    This dataclass provides comprehensive journal entry
    with weather correlation and metadata.
    """
    id: Optional[int] = None
    title: str = ""
    content: str = ""
    mood: Optional[EntryMood] = None
    tags: List[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    # Weather data at time of entry
    weather_temperature: Optional[float] = None
    weather_condition: Optional[str] = None
    weather_humidity: Optional[float] = None
    weather_pressure: Optional[float] = None
    weather_wind_speed: Optional[float] = None
    weather_location: Optional[str] = None

    # Entry metadata
    word_count: int = 0
    reading_time: int = 0  # estimated reading time in minutes
    is_favorite: bool = False
    is_private: bool = False

    def __post_init__(self):
        if self.tags is None:
            self.tags = []
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = self.created_at

        # Calculate word count and reading time
        self._update_metadata()

    def _update_metadata(self):
        """Update entry metadata based on content."""
        words = len(self.content.split())
        self.word_count = words
        self.reading_time = max(1, words // 200)  # Assume 200 words per minute

    def update_content(self, title: str, content: str):
        """Update entry content and metadata."""
        self.title = title
        self.content = content
        self.updated_at = datetime.now()
        self._update_metadata()

    def add_tag(self, tag: str):
        """Add a tag to the entry."""
        tag = tag.strip().lower()
        if tag and tag not in self.tags:
            self.tags.append(tag)

    def remove_tag(self, tag: str):
        """Remove a tag from the entry."""
        tag = tag.strip().lower()
        if tag in self.tags:
            self.tags.remove(tag)

    def to_dict(self) -> Dict[str, Any]:
        """Convert entry to dictionary for serialization."""
        data = asdict(self)

        # Convert datetime objects to ISO strings
        if self.created_at:
            data['created_at'] = self.created_at.isoformat()
        if self.updated_at:
            data['updated_at'] = self.updated_at.isoformat()

        # Convert mood enum to value
        if self.mood:
            data['mood'] = self.mood.value

        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'JournalEntry':
        """Create entry from dictionary."""
        # Convert ISO strings to datetime objects
        if 'created_at' in data and data['created_at']:
            data['created_at'] = datetime.fromisoformat(data['created_at'])
        if 'updated_at' in data and data['updated_at']:
            data['updated_at'] = datetime.fromisoformat(data['updated_at'])

        # Convert mood value to enum
        if 'mood' in data and data['mood']:
            for mood in EntryMood:
                if mood.value == data['mood']:
                    data['mood'] = mood
                    break

        return cls(**data)