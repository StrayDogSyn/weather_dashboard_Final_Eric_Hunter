"""Database operations for the Activity Suggester feature.

This module handles all database interactions including activity storage,
user preferences, and analytics.
"""

import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any

from .models import ActivitySuggestion, UserPreferences, ActivityCategory, DifficultyLevel, WeatherSuitability


class ActivityDatabase:
    """Database manager for activity suggestions and user data."""

    def __init__(self, database_manager):
        self.db_manager = database_manager
        self.logger = logging.getLogger(__name__)
        self._initialize_tables()

    def _initialize_tables(self):
        """Initialize activity-related database tables."""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()

                # Activity suggestions table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS activity_suggestions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        title TEXT NOT NULL,
                        description TEXT,
                        category TEXT NOT NULL,
                        difficulty TEXT NOT NULL,
                        duration_minutes INTEGER,
                        weather_suitability TEXT,
                        required_items TEXT,  -- JSON array
                        location_type TEXT,
                        cost_estimate TEXT,
                        group_size TEXT,
                        ai_reasoning TEXT,
                        confidence_score REAL,
                        weather_condition TEXT,
                        temperature REAL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        is_favorite BOOLEAN DEFAULT FALSE,
                        user_rating INTEGER,
                        times_suggested INTEGER DEFAULT 0,
                        times_completed INTEGER DEFAULT 0,
                        spotify_playlist_id TEXT
                    )
                """)

                # User preferences table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS user_preferences (
                        id INTEGER PRIMARY KEY,
                        preferences_data TEXT  -- JSON data
                    )
                """)

                # Activity history table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS activity_history (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        activity_id INTEGER,
                        action_type TEXT,  -- suggested, favorited, completed, rated
                        action_data TEXT,  -- JSON data for additional info
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (activity_id) REFERENCES activity_suggestions (id)
                    )
                """)

                # Create indexes for better performance
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_activities_category ON activity_suggestions(category)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_activities_weather ON activity_suggestions(weather_condition)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_activities_created ON activity_suggestions(created_at)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_history_activity ON activity_history(activity_id)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_history_timestamp ON activity_history(timestamp)")

                conn.commit()
                self.logger.debug("Activity database tables initialized")

        except Exception as e:
            self.logger.error(f"Error initializing activity tables: {e}")
            raise

    def save_activity(self, activity: ActivitySuggestion) -> int:
        """Save activity suggestion to database."""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()

                if activity.id:
                    # Update existing activity
                    cursor.execute("""
                        UPDATE activity_suggestions SET
                            title = ?, description = ?, category = ?, difficulty = ?,
                            duration_minutes = ?, weather_suitability = ?, required_items = ?,
                            location_type = ?, cost_estimate = ?, group_size = ?,
                            ai_reasoning = ?, confidence_score = ?, weather_condition = ?,
                            temperature = ?, is_favorite = ?, user_rating = ?,
                            times_suggested = ?, times_completed = ?, spotify_playlist_id = ?
                        WHERE id = ?
                    """, (
                        activity.title, activity.description, activity.category.value,
                        activity.difficulty.value, activity.duration_minutes,
                        activity.weather_suitability.value, json.dumps(activity.required_items),
                        activity.location_type, activity.cost_estimate, activity.group_size,
                        activity.ai_reasoning, activity.confidence_score, activity.weather_condition,
                        activity.temperature, activity.is_favorite, activity.user_rating,
                        activity.times_suggested, activity.times_completed, activity.spotify_playlist_id,
                        activity.id
                    ))
                    activity_id = activity.id
                else:
                    # Insert new activity
                    cursor.execute("""
                        INSERT INTO activity_suggestions (
                            title, description, category, difficulty, duration_minutes,
                            weather_suitability, required_items, location_type, cost_estimate,
                            group_size, ai_reasoning, confidence_score, weather_condition,
                            temperature, is_favorite, user_rating, times_suggested,
                            times_completed, spotify_playlist_id
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        activity.title, activity.description, activity.category.value,
                        activity.difficulty.value, activity.duration_minutes,
                        activity.weather_suitability.value, json.dumps(activity.required_items),
                        activity.location_type, activity.cost_estimate, activity.group_size,
                        activity.ai_reasoning, activity.confidence_score, activity.weather_condition,
                        activity.temperature, activity.is_favorite, activity.user_rating,
                        activity.times_suggested, activity.times_completed, activity.spotify_playlist_id
                    ))
                    activity_id = cursor.lastrowid
                    activity.id = activity_id

                conn.commit()
                self.logger.debug(f"Activity saved with ID: {activity_id}")
                return activity_id

        except Exception as e:
            self.logger.error(f"Error saving activity: {e}")
            raise

    def load_activities(self, limit: int = 100, category: Optional[ActivityCategory] = None) -> List[ActivitySuggestion]:
        """Load activities from database."""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()

                query = "SELECT * FROM activity_suggestions"
                params = []

                if category:
                    query += " WHERE category = ?"
                    params.append(category.value)

                query += " ORDER BY created_at DESC LIMIT ?"
                params.append(limit)

                cursor.execute(query, params)
                rows = cursor.fetchall()

                activities = []
                for row in rows:
                    activity = ActivitySuggestion(
                        id=row[0],
                        title=row[1],
                        description=row[2],
                        category=ActivityCategory(row[3]),
                        difficulty=DifficultyLevel(row[4]),
                        duration_minutes=row[5],
                        weather_suitability=WeatherSuitability(row[6]) if row[6] else WeatherSuitability.GOOD,
                        required_items=json.loads(row[7]) if row[7] else [],
                        location_type=row[8],
                        cost_estimate=row[9],
                        group_size=row[10],
                        ai_reasoning=row[11],
                        confidence_score=row[12] or 0.0,
                        weather_condition=row[13],
                        temperature=row[14],
                        created_at=datetime.fromisoformat(row[15]) if row[15] else None,
                        is_favorite=bool(row[16]),
                        user_rating=row[17],
                        times_suggested=row[18] or 0,
                        times_completed=row[19] or 0,
                        spotify_playlist_id=row[20]
                    )
                    activities.append(activity)

                self.logger.debug(f"Loaded {len(activities)} activities")
                return activities

        except Exception as e:
            self.logger.error(f"Error loading activities: {e}")
            return []

    def save_user_preferences(self, preferences: UserPreferences):
        """Save user preferences to database."""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()

                preferences_json = json.dumps(preferences.to_dict())

                cursor.execute("""
                    INSERT OR REPLACE INTO user_preferences (id, preferences_data)
                    VALUES (1, ?)
                """, (preferences_json,))

                conn.commit()
                self.logger.debug("User preferences saved")

        except Exception as e:
            self.logger.error(f"Error saving user preferences: {e}")
            raise

    def load_user_preferences(self) -> UserPreferences:
        """Load user preferences from database."""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()

                cursor.execute("SELECT preferences_data FROM user_preferences WHERE id = 1")
                row = cursor.fetchone()

                if row and row[0]:
                    preferences_data = json.loads(row[0])
                    return UserPreferences.from_dict(preferences_data)
                else:
                    # Return default preferences
                    return UserPreferences()

        except Exception as e:
            self.logger.error(f"Error loading user preferences: {e}")
            return UserPreferences()

    def log_activity_action(self, activity_id: int, action_type: str, action_data: Optional[Dict] = None):
        """Log user action for activity analytics."""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()

                cursor.execute("""
                    INSERT INTO activity_history (activity_id, action_type, action_data)
                    VALUES (?, ?, ?)
                """, (activity_id, action_type, json.dumps(action_data) if action_data else None))

                conn.commit()
                self.logger.debug(f"Logged action '{action_type}' for activity {activity_id}")

        except Exception as e:
            self.logger.error(f"Error logging activity action: {e}")

    def get_activity_analytics(self) -> Dict[str, Any]:
        """Get activity analytics and statistics."""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()

                # Category distribution
                cursor.execute("""
                    SELECT category, COUNT(*) as count
                    FROM activity_suggestions
                    GROUP BY category
                    ORDER BY count DESC
                """)
                category_stats = dict(cursor.fetchall())

                # Most popular activities
                cursor.execute("""
                    SELECT title, times_suggested, times_completed, user_rating
                    FROM activity_suggestions
                    WHERE times_suggested > 0
                    ORDER BY times_suggested DESC
                    LIMIT 10
                """)
                popular_activities = cursor.fetchall()

                # Recent activity trends
                cursor.execute("""
                    SELECT action_type, COUNT(*) as count
                    FROM activity_history
                    WHERE timestamp >= datetime('now', '-7 days')
                    GROUP BY action_type
                """)
                recent_trends = dict(cursor.fetchall())

                return {
                    'category_distribution': category_stats,
                    'popular_activities': popular_activities,
                    'recent_trends': recent_trends,
                    'total_activities': len(self.load_activities(limit=1000)),
                    'favorites_count': len([a for a in self.load_activities(limit=1000) if a.is_favorite])
                }

        except Exception as e:
            self.logger.error(f"Error getting activity analytics: {e}")
            return {}

    def delete_activity(self, activity_id: int):
        """Delete an activity from the database."""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM activity_suggestions WHERE id = ?", (activity_id,))
                cursor.execute("DELETE FROM activity_history WHERE activity_id = ?", (activity_id,))
                conn.commit()
                self.logger.debug(f"Deleted activity {activity_id}")
        except Exception as e:
            self.logger.error(f"Error deleting activity: {e}")
            raise

    def search_activities(self, query: str, limit: int = 50) -> List[ActivitySuggestion]:
        """Search activities by title or description."""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT * FROM activity_suggestions 
                    WHERE title LIKE ? OR description LIKE ?
                    ORDER BY created_at DESC LIMIT ?
                """, (f"%{query}%", f"%{query}%", limit))
                
                rows = cursor.fetchall()
                activities = []
                for row in rows:
                    activity = ActivitySuggestion(
                        id=row[0], title=row[1], description=row[2],
                        category=ActivityCategory(row[3]), difficulty=DifficultyLevel(row[4]),
                        duration_minutes=row[5],
                        weather_suitability=WeatherSuitability(row[6]) if row[6] else WeatherSuitability.GOOD,
                        required_items=json.loads(row[7]) if row[7] else [],
                        location_type=row[8], cost_estimate=row[9], group_size=row[10],
                        ai_reasoning=row[11], confidence_score=row[12] or 0.0,
                        weather_condition=row[13], temperature=row[14],
                        created_at=datetime.fromisoformat(row[15]) if row[15] else None,
                        is_favorite=bool(row[16]), user_rating=row[17],
                        times_suggested=row[18] or 0, times_completed=row[19] or 0,
                        spotify_playlist_id=row[20]
                    )
                    activities.append(activity)
                return activities
        except Exception as e:
            self.logger.error(f"Error searching activities: {e}")
            return []