"""Database models for weather dashboard.

Defines SQLAlchemy models for all persistent data structures.
"""

from typing import Any, Dict

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Float,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func

Base = declarative_base()


class WeatherHistory(Base):
    """Historical weather data storage."""

    __tablename__ = "weather_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    location = Column(String(255), nullable=False, index=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    timestamp = Column(DateTime, nullable=False, default=func.now(), index=True)

    # Weather conditions
    temperature = Column(Float, nullable=False)
    feels_like = Column(Float)
    humidity = Column(Integer)
    pressure = Column(Float)
    wind_speed = Column(Float)
    wind_direction = Column(Integer)
    visibility = Column(Float)
    uv_index = Column(Float)

    # Weather description
    condition = Column(String(100), nullable=False)
    description = Column(String(255))
    icon = Column(String(10))

    # Additional data as JSON
    raw_data = Column(JSON)

    # Metadata
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Indexes for performance
    __table_args__ = (
        Index("idx_location_timestamp", "location", "timestamp"),
        Index("idx_coordinates", "latitude", "longitude"),
        Index("idx_timestamp_desc", "timestamp", postgresql_using="btree"),
    )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "location": self.location,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "temperature": self.temperature,
            "feels_like": self.feels_like,
            "humidity": self.humidity,
            "pressure": self.pressure,
            "wind_speed": self.wind_speed,
            "wind_direction": self.wind_direction,
            "visibility": self.visibility,
            "uv_index": self.uv_index,
            "condition": self.condition,
            "description": self.description,
            "icon": self.icon,
            "raw_data": self.raw_data,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class UserPreferences(Base):
    """User preferences and settings storage."""

    __tablename__ = "user_preferences"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(100), nullable=False, unique=True, default="default")

    # UI Preferences
    theme = Column(String(50), default="light")
    temperature_unit = Column(String(10), default="celsius")
    wind_unit = Column(String(20), default="kmh")
    pressure_unit = Column(String(20), default="hPa")

    # Location preferences
    default_location = Column(String(255))
    favorite_locations = Column(JSON, default=list)
    recent_searches = Column(JSON, default=list)

    # Dashboard preferences
    dashboard_layout = Column(JSON, default=dict)
    visible_panels = Column(JSON, default=list)
    refresh_interval = Column(Integer, default=300)  # seconds

    # Notification preferences
    enable_notifications = Column(Boolean, default=True)
    weather_alerts = Column(Boolean, default=True)
    severe_weather_alerts = Column(Boolean, default=True)

    # Activity preferences
    preferred_activities = Column(JSON, default=list)
    activity_difficulty = Column(String(20), default="moderate")

    # Advanced settings
    api_settings = Column(JSON, default=dict)
    cache_settings = Column(JSON, default=dict)

    # Metadata
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "theme": self.theme,
            "temperature_unit": self.temperature_unit,
            "wind_unit": self.wind_unit,
            "pressure_unit": self.pressure_unit,
            "default_location": self.default_location,
            "favorite_locations": self.favorite_locations,
            "recent_searches": self.recent_searches,
            "dashboard_layout": self.dashboard_layout,
            "visible_panels": self.visible_panels,
            "refresh_interval": self.refresh_interval,
            "enable_notifications": self.enable_notifications,
            "weather_alerts": self.weather_alerts,
            "severe_weather_alerts": self.severe_weather_alerts,
            "preferred_activities": self.preferred_activities,
            "activity_difficulty": self.activity_difficulty,
            "api_settings": self.api_settings,
            "cache_settings": self.cache_settings,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class ActivityLog(Base):
    """Activity tracking and recommendations log."""

    __tablename__ = "activity_log"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(100), nullable=False, default="default", index=True)

    # Activity details
    activity_name = Column(String(255), nullable=False)
    activity_category = Column(String(100))
    activity_difficulty = Column(String(20))

    # Location and weather context
    location = Column(String(255), nullable=False)
    weather_condition = Column(String(100))
    temperature = Column(Float)

    # Activity execution
    selected_at = Column(DateTime, nullable=False, default=func.now())
    completed_at = Column(DateTime)
    duration_minutes = Column(Integer)

    # User feedback
    rating = Column(Integer)  # 1-5 scale
    feedback = Column(Text)
    would_recommend = Column(Boolean)

    # Weather snapshot at time of activity
    weather_snapshot = Column(JSON)

    # Metadata
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Indexes
    __table_args__ = (
        Index("idx_user_activity", "user_id", "selected_at"),
        Index("idx_activity_name", "activity_name"),
        Index("idx_location_activity", "location", "activity_name"),
    )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "activity_name": self.activity_name,
            "activity_category": self.activity_category,
            "activity_difficulty": self.activity_difficulty,
            "location": self.location,
            "weather_condition": self.weather_condition,
            "temperature": self.temperature,
            "selected_at": self.selected_at.isoformat() if self.selected_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "duration_minutes": self.duration_minutes,
            "rating": self.rating,
            "feedback": self.feedback,
            "would_recommend": self.would_recommend,
            "weather_snapshot": self.weather_snapshot,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class JournalEntry(Base):
    """Weather journal entries for mood and experience tracking."""

    __tablename__ = "journal_entries"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(100), nullable=False, default="default", index=True)

    # Entry details
    date = Column(DateTime, nullable=False, index=True)
    title = Column(String(255))
    notes = Column(Text)

    # Mood tracking
    mood = Column(String(50))  # happy, sad, energetic, calm, etc.
    mood_score = Column(Integer)  # 1-10 scale
    energy_level = Column(Integer)  # 1-10 scale

    # Weather impact
    weather_impact = Column(String(50))  # positive, negative, neutral
    weather_preference = Column(String(100))

    # Location context
    location = Column(String(255))

    # Weather snapshot when entry was created
    weather_snapshot = Column(JSON)

    # Tags and categories
    tags = Column(JSON, default=list)
    category = Column(String(100))

    # Privacy and sharing
    is_private = Column(Boolean, default=True)

    # Metadata
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Indexes
    __table_args__ = (
        Index("idx_user_date", "user_id", "date"),
        Index("idx_mood_date", "mood", "date"),
        Index("idx_location_date", "location", "date"),
    )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "date": self.date.isoformat() if self.date else None,
            "title": self.title,
            "notes": self.notes,
            "mood": self.mood,
            "mood_score": self.mood_score,
            "energy_level": self.energy_level,
            "weather_impact": self.weather_impact,
            "weather_preference": self.weather_preference,
            "location": self.location,
            "weather_snapshot": self.weather_snapshot,
            "tags": self.tags,
            "category": self.category,
            "is_private": self.is_private,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class DatabaseMigration(Base):
    """Track database schema migrations."""

    __tablename__ = "database_migrations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    version = Column(String(50), nullable=False, unique=True)
    description = Column(String(255))
    applied_at = Column(DateTime, default=func.now())
    checksum = Column(String(64))  # SHA-256 of migration content

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "version": self.version,
            "description": self.description,
            "applied_at": self.applied_at.isoformat() if self.applied_at else None,
            "checksum": self.checksum,
        }
