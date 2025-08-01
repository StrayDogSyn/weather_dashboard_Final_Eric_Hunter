"""Database Manager Mixin

Contains all database operations for activity preferences and history.
"""

import sqlite3
import threading
from pathlib import Path
from typing import Dict, List


class DatabaseManagerMixin:
    """Mixin class containing database management methods."""

    def _setup_database(self) -> None:
        """Setup SQLite for activity preferences."""
        self.db_path = Path("data") / "activity_preferences.db"
        self.db_path.parent.mkdir(exist_ok=True)

        # Create thread-local storage for database connections
        self._local = threading.local()

        # Initialize database schema
        self._get_db_connection()

    def _get_db_connection(self):
        """Get thread-local database connection."""
        if not hasattr(self._local, "conn") or self._local.conn is None:
            self._local.conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
            self._local.cursor = self._local.conn.cursor()

            # Create table if it doesn't exist
            self._local.cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS activity_preferences (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    activity_name TEXT,
                    category TEXT,
                    liked INTEGER,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    weather_condition TEXT,
                    temperature REAL
                )
            """
            )
            self._local.conn.commit()

        return self._local.conn, self._local.cursor

    def _get_user_activity_history(self) -> List[Dict]:
        """Get user's activity history from database."""
        try:
            conn, cursor = self._get_db_connection()
            cursor.execute(
                """
                SELECT activity_name, category, liked, weather_condition, temperature, timestamp
                FROM activity_preferences 
                ORDER BY timestamp DESC 
                LIMIT 20
            """
            )

            rows = cursor.fetchall()
            history = []

            for row in rows:
                history.append(
                    {
                        "activity_name": row[0],
                        "category": row[1],
                        "liked": bool(row[2]),
                        "weather_condition": row[3],
                        "temperature": row[4],
                        "timestamp": row[5],
                    }
                )

            return history

        except Exception as e:
            print(f"Error getting user activity history: {e}")
            return []

    def _save_activity_rating(self, activity: Dict, rating: int) -> None:
        """Save activity rating to database."""
        try:
            # Get current weather data for context
            weather_condition = "Unknown"
            temperature = 0.0

            if hasattr(self, "current_weather") and self.current_weather:
                weather_condition = self.current_weather.get("condition", "Unknown")
                temperature = self.current_weather.get("temperature", 0.0)

            # Insert rating into database
            conn, cursor = self._get_db_connection()
            cursor.execute(
                """
                INSERT INTO activity_preferences 
                (activity_name, category, liked, weather_condition, temperature)
                VALUES (?, ?, ?, ?, ?)
            """,
                (
                    activity.get("name", "Unknown"),
                    activity.get("category", "general"),
                    1 if rating >= 4 else 0,  # Consider 4+ stars as "liked"
                    weather_condition,
                    temperature,
                ),
            )

            conn.commit()
            print(f"Saved rating for activity: {activity.get('name')} - Rating: {rating}")

        except Exception as e:
            print(f"Error saving activity rating: {e}")

    def _get_preferred_categories(self) -> List[str]:
        """Get user's preferred activity categories based on history."""
        try:
            conn, cursor = self._get_db_connection()
            cursor.execute(
                """
                SELECT category, COUNT(*) as count
                FROM activity_preferences 
                WHERE liked = 1
                GROUP BY category
                ORDER BY count DESC
                LIMIT 5
            """
            )

            rows = cursor.fetchall()
            return [row[0] for row in rows]

        except Exception as e:
            print(f"Error getting preferred categories: {e}")
            return []

    def _get_weather_activity_correlations(self) -> Dict[str, List[str]]:
        """Get correlations between weather conditions and preferred activities."""
        try:
            conn, cursor = self._get_db_connection()
            cursor.execute(
                """
                SELECT weather_condition, activity_name, COUNT(*) as count
                FROM activity_preferences 
                WHERE liked = 1
                GROUP BY weather_condition, activity_name
                ORDER BY weather_condition, count DESC
            """
            )

            rows = cursor.fetchall()
            correlations = {}

            for row in rows:
                weather_condition = row[0]
                activity_name = row[1]

                if weather_condition not in correlations:
                    correlations[weather_condition] = []

                correlations[weather_condition].append(activity_name)

            return correlations

        except Exception as e:
            print(f"Error getting weather-activity correlations: {e}")
            return {}

    def _get_activity_stats(self) -> Dict:
        """Get statistics about user's activity preferences."""
        try:
            conn, cursor = self._get_db_connection()
            stats = {}

            # Total activities rated
            cursor.execute("SELECT COUNT(*) FROM activity_preferences")
            stats["total_rated"] = cursor.fetchone()[0]

            # Liked activities count
            cursor.execute("SELECT COUNT(*) FROM activity_preferences WHERE liked = 1")
            stats["liked_count"] = cursor.fetchone()[0]

            # Most active category
            cursor.execute(
                """
                SELECT category, COUNT(*) as count
                FROM activity_preferences 
                GROUP BY category
                ORDER BY count DESC
                LIMIT 1
            """
            )
            result = cursor.fetchone()
            stats["most_active_category"] = result[0] if result else "None"

            # Favorite weather for activities
            cursor.execute(
                """
                SELECT weather_condition, COUNT(*) as count
                FROM activity_preferences 
                WHERE liked = 1
                GROUP BY weather_condition
                ORDER BY count DESC
                LIMIT 1
            """
            )
            result = cursor.fetchone()
            stats["favorite_weather"] = result[0] if result else "None"

            return stats

        except Exception as e:
            print(f"Error getting activity stats: {e}")
            return {
                "total_rated": 0,
                "liked_count": 0,
                "most_active_category": "None",
                "favorite_weather": "None",
            }

    def _clear_activity_history(self) -> None:
        """Clear all activity history from database."""
        try:
            conn, cursor = self._get_db_connection()
            cursor.execute("DELETE FROM activity_preferences")
            conn.commit()
            print("Activity history cleared")

        except Exception as e:
            print(f"Error clearing activity history: {e}")

    def _export_activity_data(self) -> List[Dict]:
        """Export all activity data for backup or analysis."""
        try:
            conn, cursor = self._get_db_connection()
            cursor.execute(
                """
                SELECT * FROM activity_preferences 
                ORDER BY timestamp DESC
            """
            )

            rows = cursor.fetchall()
            columns = [description[0] for description in cursor.description]

            data = []
            for row in rows:
                data.append(dict(zip(columns, row)))

            return data

        except Exception as e:
            print(f"Error exporting activity data: {e}")
            return []

    def _close_database(self) -> None:
        """Close database connection."""
        try:
            if hasattr(self, "conn") and self.conn:
                self.conn.close()
                print("Database connection closed")

        except Exception as e:
            print(f"Error closing database: {e}")

    def __del__(self) -> None:
        """Cleanup database connection on object destruction."""
        try:
            self._close_database()
        except Exception:
            pass
