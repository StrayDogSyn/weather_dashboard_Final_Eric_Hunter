"""Activity Data Repository

Handles data access operations for weather-related activities and recommendations.
"""

import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from .base_repository import BaseRepository


class ActivityType(Enum):
    """Types of weather-dependent activities."""

    OUTDOOR_SPORTS = "outdoor_sports"
    INDOOR_ACTIVITIES = "indoor_activities"
    TRAVEL = "travel"
    GARDENING = "gardening"
    PHOTOGRAPHY = "photography"
    EVENTS = "events"
    EXERCISE = "exercise"
    RECREATION = "recreation"


class WeatherSuitability(Enum):
    """Weather suitability levels for activities."""

    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"
    UNSUITABLE = "unsuitable"


@dataclass
class ActivityRecommendation:
    """Weather-based activity recommendation."""

    id: Optional[str] = None
    activity_name: str = ""
    activity_type: ActivityType = ActivityType.RECREATION
    description: str = ""
    suitability: WeatherSuitability = WeatherSuitability.FAIR
    confidence_score: float = 0.0  # 0.0 to 1.0

    # Weather conditions
    min_temperature: Optional[float] = None
    max_temperature: Optional[float] = None
    max_wind_speed: Optional[float] = None
    max_precipitation: Optional[float] = None
    min_visibility: Optional[float] = None

    # Timing
    recommended_time: Optional[str] = None  # "morning", "afternoon", "evening"
    duration_hours: Optional[float] = None

    # Additional info
    equipment_needed: List[str] = None
    safety_notes: List[str] = None
    alternative_activities: List[str] = None

    # Metadata
    created_at: Optional[datetime] = None
    location: Optional[str] = None
    user_id: Optional[str] = None

    def __post_init__(self):
        """Initialize lists if None."""
        if self.equipment_needed is None:
            self.equipment_needed = []
        if self.safety_notes is None:
            self.safety_notes = []
        if self.alternative_activities is None:
            self.alternative_activities = []
        if self.created_at is None:
            self.created_at = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "id": self.id,
            "activity_name": self.activity_name,
            "activity_type": self.activity_type.value,
            "description": self.description,
            "suitability": self.suitability.value,
            "confidence_score": self.confidence_score,
            "min_temperature": self.min_temperature,
            "max_temperature": self.max_temperature,
            "max_wind_speed": self.max_wind_speed,
            "max_precipitation": self.max_precipitation,
            "min_visibility": self.min_visibility,
            "recommended_time": self.recommended_time,
            "duration_hours": self.duration_hours,
            "equipment_needed": self.equipment_needed,
            "safety_notes": self.safety_notes,
            "alternative_activities": self.alternative_activities,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "location": self.location,
            "user_id": self.user_id,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ActivityRecommendation":
        """Create from dictionary."""
        created_at = None
        if data.get("created_at"):
            created_at = datetime.fromisoformat(data["created_at"])

        return cls(
            id=data.get("id"),
            activity_name=data.get("activity_name", ""),
            activity_type=ActivityType(data.get("activity_type", "recreation")),
            description=data.get("description", ""),
            suitability=WeatherSuitability(data.get("suitability", "fair")),
            confidence_score=data.get("confidence_score", 0.0),
            min_temperature=data.get("min_temperature"),
            max_temperature=data.get("max_temperature"),
            max_wind_speed=data.get("max_wind_speed"),
            max_precipitation=data.get("max_precipitation"),
            min_visibility=data.get("min_visibility"),
            recommended_time=data.get("recommended_time"),
            duration_hours=data.get("duration_hours"),
            equipment_needed=data.get("equipment_needed", []),
            safety_notes=data.get("safety_notes", []),
            alternative_activities=data.get("alternative_activities", []),
            created_at=created_at,
            location=data.get("location"),
            user_id=data.get("user_id"),
        )


class ActivityRepository(BaseRepository[ActivityRecommendation, str]):
    """Repository for activity recommendations and weather suitability data."""

    def __init__(self, db_path: str = "activities.db"):
        super().__init__()
        self.db_path = db_path
        self._init_database()

    def _init_database(self):
        """Initialize SQLite database for activity data."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS activity_recommendations (
                    id TEXT PRIMARY KEY,
                    activity_data TEXT NOT NULL,
                    activity_type TEXT,
                    suitability TEXT,
                    confidence_score REAL,
                    location TEXT,
                    user_id TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """
            )

            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS user_activity_preferences (
                    user_id TEXT,
                    activity_type TEXT,
                    preference_score REAL,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (user_id, activity_type)
                )
            """
            )

            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS activity_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT,
                    activity_name TEXT,
                    activity_type TEXT,
                    weather_conditions TEXT,
                    user_rating INTEGER,
                    completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """
            )

            # Create indexes for better performance
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_activity_type "
                "ON activity_recommendations(activity_type)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_activity_location "
                "ON activity_recommendations(location)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_activity_user ON activity_recommendations(user_id)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_history_user ON activity_history(user_id)"
            )

            conn.commit()

    async def get_by_id(self, activity_id: str) -> Optional[ActivityRecommendation]:
        """Get activity recommendation by ID."""
        # Check memory cache first
        cached = self._get_from_cache(activity_id)
        if cached:
            return cached

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT activity_data FROM activity_recommendations WHERE id = ?", (activity_id,)
            )
            row = cursor.fetchone()

            if row:
                activity_dict = json.loads(row[0])
                activity = ActivityRecommendation.from_dict(activity_dict)
                self._set_cache(activity_id, activity)
                return activity

        return None

    async def get_all(
        self, limit: Optional[int] = None, offset: int = 0
    ) -> List[ActivityRecommendation]:
        """Get all activity recommendations with pagination."""
        with sqlite3.connect(self.db_path) as conn:
            query = "SELECT activity_data FROM activity_recommendations ORDER BY created_at DESC"
            params = []

            if limit:
                query += " LIMIT ? OFFSET ?"
                params.extend([limit, offset])

            cursor = conn.execute(query, params)
            rows = cursor.fetchall()

            return [ActivityRecommendation.from_dict(json.loads(row[0])) for row in rows]

    async def create(self, entity: ActivityRecommendation) -> ActivityRecommendation:
        """Create new activity recommendation."""
        if not entity.id:
            entity.id = (
                f"activity_{datetime.now().strftime('%Y%m%d_%H%M%S')}_"
                f"{hash(entity.activity_name) % 10000}"
            )

        entity.created_at = datetime.now()
        activity_dict = entity.to_dict()

        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT INTO activity_recommendations "
                "(id, activity_data, activity_type, suitability, confidence_score, "
                "location, user_id, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    entity.id,
                    json.dumps(activity_dict),
                    entity.activity_type.value,
                    entity.suitability.value,
                    entity.confidence_score,
                    entity.location,
                    entity.user_id,
                    entity.created_at.isoformat(),
                ),
            )
            conn.commit()

        self._set_cache(entity.id, entity)
        return entity

    async def update(
        self, activity_id: str, entity: ActivityRecommendation
    ) -> Optional[ActivityRecommendation]:
        """Update existing activity recommendation."""
        entity.id = activity_id
        activity_dict = entity.to_dict()

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "UPDATE activity_recommendations SET activity_data = ?, "
                "activity_type = ?, suitability = ?, confidence_score = ?, "
                "location = ?, user_id = ? WHERE id = ?",
                (
                    json.dumps(activity_dict),
                    entity.activity_type.value,
                    entity.suitability.value,
                    entity.confidence_score,
                    entity.location,
                    entity.user_id,
                    activity_id,
                ),
            )

            if cursor.rowcount > 0:
                conn.commit()
                self._set_cache(activity_id, entity)
                return entity

        return None

    async def delete(self, activity_id: str) -> bool:
        """Delete activity recommendation."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "DELETE FROM activity_recommendations WHERE id = ?", (activity_id,)
            )
            conn.commit()

            self._invalidate_cache(activity_id)
            return cursor.rowcount > 0

    async def exists(self, activity_id: str) -> bool:
        """Check if activity recommendation exists."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT 1 FROM activity_recommendations WHERE id = ?", (activity_id,)
            )
            return cursor.fetchone() is not None

    async def find_by_criteria(self, criteria: Dict[str, Any]) -> List[ActivityRecommendation]:
        """Find activities matching criteria."""
        query_parts = ["SELECT activity_data FROM activity_recommendations WHERE 1=1"]
        params = []

        if "activity_type" in criteria:
            query_parts.append("AND activity_type = ?")
            params.append(criteria["activity_type"])

        if "suitability" in criteria:
            query_parts.append("AND suitability = ?")
            params.append(criteria["suitability"])

        if "location" in criteria:
            query_parts.append("AND location = ?")
            params.append(criteria["location"])

        if "user_id" in criteria:
            query_parts.append("AND user_id = ?")
            params.append(criteria["user_id"])

        if "min_confidence" in criteria:
            query_parts.append("AND confidence_score >= ?")
            params.append(criteria["min_confidence"])

        query_parts.append("ORDER BY confidence_score DESC, created_at DESC")

        if "limit" in criteria:
            query_parts.append("LIMIT ?")
            params.append(criteria["limit"])

        query = " ".join(query_parts)

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(query, params)
            rows = cursor.fetchall()

            return [ActivityRecommendation.from_dict(json.loads(row[0])) for row in rows]

    async def get_recommendations_for_weather(
        self, temperature: float, wind_speed: float, precipitation: float, visibility: float
    ) -> List[ActivityRecommendation]:
        """Get activity recommendations based on current weather conditions."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT activity_data FROM activity_recommendations WHERE "
                "(min_temperature IS NULL OR min_temperature <= ?) AND "
                "(max_temperature IS NULL OR max_temperature >= ?) AND "
                "(max_wind_speed IS NULL OR max_wind_speed >= ?) AND "
                "(max_precipitation IS NULL OR max_precipitation >= ?) AND "
                "(min_visibility IS NULL OR min_visibility <= ?) "
                "ORDER BY confidence_score DESC",
                (temperature, temperature, wind_speed, precipitation, visibility),
            )
            rows = cursor.fetchall()

            return [ActivityRecommendation.from_dict(json.loads(row[0])) for row in rows]

    async def get_by_activity_type(
        self, activity_type: ActivityType, limit: int = 10
    ) -> List[ActivityRecommendation]:
        """Get recommendations by activity type."""
        return await self.find_by_criteria(
            {"activity_type": activity_type.value, "limit": limit}
        )

    async def get_user_recommendations(
        self, user_id: str, limit: int = 20
    ) -> List[ActivityRecommendation]:
        """Get personalized recommendations for user."""
        return await self.find_by_criteria(
            {"user_id": user_id, "limit": limit}
        )

    async def set_user_activity_preference(
        self, user_id: str, activity_type: ActivityType, preference_score: float
    ) -> bool:
        """Set user preference score for activity type."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT OR REPLACE INTO user_activity_preferences "
                "(user_id, activity_type, preference_score, last_updated) "
                "VALUES (?, ?, ?, ?)",
                (user_id, activity_type.value, preference_score, datetime.now().isoformat()),
            )
            conn.commit()
            return True

    async def get_user_activity_preferences(self, user_id: str) -> Dict[str, float]:
        """Get user activity preferences."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT activity_type, preference_score FROM user_activity_preferences "
                "WHERE user_id = ?",
                (user_id,),
            )
            rows = cursor.fetchall()

            return {row[0]: row[1] for row in rows}

    async def log_activity_completion(
        self,
        user_id: str,
        activity_name: str,
        activity_type: ActivityType,
        weather_conditions: Dict[str, Any],
        user_rating: int,
    ) -> bool:
        """Log completed activity for learning user preferences."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT INTO activity_history (user_id, activity_name, activity_type, "
                "weather_conditions, user_rating) VALUES (?, ?, ?, ?, ?)",
                (
                    user_id,
                    activity_name,
                    activity_type.value,
                    json.dumps(weather_conditions),
                    user_rating,
                ),
            )
            conn.commit()
            return True

    async def get_activity_history(
        self, user_id: str, limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get user activity history."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT activity_name, activity_type, weather_conditions, user_rating, completed_at FROM activity_history WHERE user_id = ? ORDER BY completed_at DESC LIMIT ?",
                (user_id, limit),
            )
            rows = cursor.fetchall()

            return [
                {
                    "activity_name": row[0],
                    "activity_type": row[1],
                    "weather_conditions": json.loads(row[2]),
                    "user_rating": row[3],
                    "completed_at": row[4],
                }
                for row in rows
            ]

    async def get_popular_activities(
        self, activity_type: Optional[ActivityType] = None, limit: int = 10
    ) -> List[Tuple[str, int, float]]:
        """Get popular activities based on completion history."""
        query = "SELECT activity_name, COUNT(*) as completion_count, AVG(user_rating) as avg_rating FROM activity_history"
        params = []

        if activity_type:
            query += " WHERE activity_type = ?"
            params.append(activity_type.value)

        query += " GROUP BY activity_name ORDER BY completion_count DESC, avg_rating DESC LIMIT ?"
        params.append(limit)

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(query, params)
            rows = cursor.fetchall()

            return [(row[0], row[1], row[2]) for row in rows]

    async def cleanup_old_recommendations(self, days_to_keep: int = 30) -> int:
        """Clean up old activity recommendations."""
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "DELETE FROM activity_recommendations WHERE created_at < ?",
                (cutoff_date.isoformat(),),
            )
            conn.commit()

            # Clear related cache entries
            self._clear_cache()

            return cursor.rowcount

    async def count(self, criteria: Optional[Dict[str, Any]] = None) -> int:
        """Count activity recommendations."""
        if not criteria:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("SELECT COUNT(*) FROM activity_recommendations")
                return cursor.fetchone()[0]

        # Build count query with criteria
        query_parts = ["SELECT COUNT(*) FROM activity_recommendations WHERE 1=1"]
        params = []

        if "activity_type" in criteria:
            query_parts.append("AND activity_type = ?")
            params.append(criteria["activity_type"])

        if "user_id" in criteria:
            query_parts.append("AND user_id = ?")
            params.append(criteria["user_id"])

        query = " ".join(query_parts)

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(query, params)
            return cursor.fetchone()[0]
