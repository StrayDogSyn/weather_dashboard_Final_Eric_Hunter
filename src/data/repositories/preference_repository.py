"""User Preference Repository

Handles data access operations for user preferences and settings.
"""

import json
import sqlite3
from datetime import datetime
from typing import Any, Dict, List, Optional

from ...models.user.preference_models import UserPreferences
from .base_repository import BaseRepository


class PreferenceRepository(BaseRepository[UserPreferences, str]):
    """Repository for user preferences with SQLite persistence."""

    def __init__(self, db_path: str = "user_preferences.db"):
        super().__init__()
        self.db_path = db_path
        self._init_database()

    def _init_database(self):
        """Initialize SQLite database for user preferences."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS user_preferences (
                    user_id TEXT PRIMARY KEY,
                    preferences_data TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    version TEXT DEFAULT '1.0'
                )
            """
            )

            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS favorite_locations (
                    user_id TEXT,
                    location_name TEXT,
                    location_data TEXT,
                    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (user_id, location_name),
                    FOREIGN KEY (user_id) REFERENCES user_preferences(user_id)
                )
            """
            )

            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS preference_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT,
                    change_type TEXT,
                    old_value TEXT,
                    new_value TEXT,
                    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES user_preferences(user_id)
                )
            """
            )

            conn.commit()

    async def get_by_id(self, user_id: str) -> Optional[UserPreferences]:
        """Get user preferences by user ID."""
        # Check memory cache first
        cached = self._get_from_cache(user_id)
        if cached:
            return cached

        # Check database
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT preferences_data FROM user_preferences WHERE user_id = ?", (user_id,)
            )
            row = cursor.fetchone()

            if row:
                preferences_dict = json.loads(row[0])
                preferences = UserPreferences.from_dict(preferences_dict)
                self._set_cache(user_id, preferences)
                return preferences

        return None

    async def get_all(self, limit: Optional[int] = None, offset: int = 0) -> List[UserPreferences]:
        """Get all user preferences with pagination."""
        with sqlite3.connect(self.db_path) as conn:
            query = "SELECT preferences_data FROM user_preferences ORDER BY updated_at DESC"
            params = []

            if limit:
                query += " LIMIT ? OFFSET ?"
                params.extend([limit, offset])

            cursor = conn.execute(query, params)
            rows = cursor.fetchall()

            return [UserPreferences.from_dict(json.loads(row[0])) for row in rows]

    async def create(self, entity: UserPreferences) -> UserPreferences:
        """Create new user preferences."""
        if not entity.user_id:
            raise ValueError("User ID is required for creating preferences")

        entity.created_at = datetime.now()
        entity.updated_at = datetime.now()

        preferences_dict = entity.to_dict()

        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT INTO user_preferences (user_id, preferences_data, created_at, "
                "updated_at, version) VALUES (?, ?, ?, ?, ?)",
                (
                    entity.user_id,
                    json.dumps(preferences_dict),
                    entity.created_at.isoformat(),
                    entity.updated_at.isoformat(),
                    entity.version,
                ),
            )
            conn.commit()

        # Cache the new preferences
        self._set_cache(entity.user_id, entity)
        return entity

    async def update(self, user_id: str, entity: UserPreferences) -> Optional[UserPreferences]:
        """Update existing user preferences."""
        # Get current preferences for change tracking
        current_prefs = await self.get_by_id(user_id)

        entity.user_id = user_id
        entity.update_timestamp()

        preferences_dict = entity.to_dict()

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "UPDATE user_preferences SET preferences_data = ?, updated_at = ?, "
                "version = ? WHERE user_id = ?",
                (
                    json.dumps(preferences_dict),
                    entity.updated_at.isoformat(),
                    entity.version,
                    user_id,
                ),
            )

            if cursor.rowcount > 0:
                # Log the change if we had previous preferences
                if current_prefs:
                    await self._log_preference_change(user_id, current_prefs, entity)

                conn.commit()

                # Update cache
                self._set_cache(user_id, entity)
                return entity

        return None

    async def delete(self, user_id: str) -> bool:
        """Delete user preferences."""
        with sqlite3.connect(self.db_path) as conn:
            # Delete related data first
            conn.execute("DELETE FROM favorite_locations WHERE user_id = ?", (user_id,))
            conn.execute("DELETE FROM preference_history WHERE user_id = ?", (user_id,))

            # Delete main preferences
            cursor = conn.execute("DELETE FROM user_preferences WHERE user_id = ?", (user_id,))
            conn.commit()

            self._invalidate_cache(user_id)
            return cursor.rowcount > 0

    async def exists(self, user_id: str) -> bool:
        """Check if user preferences exist."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT 1 FROM user_preferences WHERE user_id = ?", (user_id,))
            return cursor.fetchone() is not None

    async def get_or_create_default(self, user_id: str) -> UserPreferences:
        """Get user preferences or create default ones if they don't exist."""
        preferences = await self.get_by_id(user_id)

        if preferences is None:
            # Create default preferences
            preferences = UserPreferences(user_id=user_id)
            preferences = await self.create(preferences)

        return preferences

    async def update_units(
        self, user_id: str, units_dict: Dict[str, str]
    ) -> Optional[UserPreferences]:
        """Update only unit preferences."""
        preferences = await self.get_by_id(user_id)
        if not preferences:
            return None

        # Update units
        from ...models.user.preference_models import UnitPreferences

        preferences.units = UnitPreferences.from_dict(units_dict)

        return await self.update(user_id, preferences)

    async def update_notifications(
        self, user_id: str, notifications_dict: Dict[str, Any]
    ) -> Optional[UserPreferences]:
        """Update only notification preferences."""
        preferences = await self.get_by_id(user_id)
        if not preferences:
            return None

        # Update notifications
        from ...models.user.preference_models import NotificationPreferences

        preferences.notifications = NotificationPreferences.from_dict(notifications_dict)

        return await self.update(user_id, preferences)

    async def update_display(
        self, user_id: str, display_dict: Dict[str, Any]
    ) -> Optional[UserPreferences]:
        """Update only display preferences."""
        preferences = await self.get_by_id(user_id)
        if not preferences:
            return None

        # Update display settings
        from ...models.user.preference_models import DisplayPreferences

        preferences.display = DisplayPreferences.from_dict(display_dict)

        return await self.update(user_id, preferences)

    async def add_favorite_location(
        self, user_id: str, location_name: str, location_data: Dict[str, Any]
    ) -> bool:
        """Add a favorite location for user."""
        preferences = await self.get_by_id(user_id)
        if not preferences:
            return False

        # Add to preferences object
        if location_name not in preferences.favorite_locations:
            preferences.favorite_locations.append(location_name)
            await self.update(user_id, preferences)

        # Store detailed location data
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT OR REPLACE INTO favorite_locations (user_id, location_name, "
                "location_data) VALUES (?, ?, ?)",
                (user_id, location_name, json.dumps(location_data)),
            )
            conn.commit()

        return True

    async def remove_favorite_location(self, user_id: str, location_name: str) -> bool:
        """Remove a favorite location for user."""
        preferences = await self.get_by_id(user_id)
        if not preferences:
            return False

        # Remove from preferences object
        if location_name in preferences.favorite_locations:
            preferences.favorite_locations.remove(location_name)
            await self.update(user_id, preferences)

        # Remove detailed location data
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "DELETE FROM favorite_locations WHERE user_id = ? AND "
                "location_name = ?",
                (user_id, location_name),
            )
            conn.commit()
            return cursor.rowcount > 0

        return False

    async def get_favorite_locations(self, user_id: str) -> List[Dict[str, Any]]:
        """Get detailed favorite location data for user."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT location_name, location_data FROM favorite_locations "
                "WHERE user_id = ? ORDER BY added_at",
                (user_id,),
            )
            rows = cursor.fetchall()

            return [{"name": row[0], "data": json.loads(row[1])} for row in rows]

    async def set_default_location(self, user_id: str, location_name: str) -> bool:
        """Set default location for user."""
        preferences = await self.get_by_id(user_id)
        if not preferences:
            return False

        preferences.default_location = location_name
        updated = await self.update(user_id, preferences)
        return updated is not None

    async def get_preference_history(
        self, user_id: str, limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get preference change history for user."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT change_type, old_value, new_value, changed_at FROM "
                "preference_history WHERE user_id = ? ORDER BY changed_at DESC LIMIT ?",
                (user_id, limit),
            )
            rows = cursor.fetchall()

            return [
                {
                    "change_type": row[0],
                    "old_value": row[1],
                    "new_value": row[2],
                    "changed_at": row[3],
                }
                for row in rows
            ]

    async def _log_preference_change(
        self, user_id: str, old_prefs: UserPreferences, new_prefs: UserPreferences
    ):
        """Log preference changes for audit trail."""
        changes = []

        # Compare units
        if old_prefs.units.to_dict() != new_prefs.units.to_dict():
            changes.append(
                {
                    "change_type": "units",
                    "old_value": json.dumps(old_prefs.units.to_dict()),
                    "new_value": json.dumps(new_prefs.units.to_dict()),
                }
            )

        # Compare notifications
        if old_prefs.notifications.to_dict() != new_prefs.notifications.to_dict():
            changes.append(
                {
                    "change_type": "notifications",
                    "old_value": json.dumps(old_prefs.notifications.to_dict()),
                    "new_value": json.dumps(new_prefs.notifications.to_dict()),
                }
            )

        # Compare display settings
        if old_prefs.display.to_dict() != new_prefs.display.to_dict():
            changes.append(
                {
                    "change_type": "display",
                    "old_value": json.dumps(old_prefs.display.to_dict()),
                    "new_value": json.dumps(new_prefs.display.to_dict()),
                }
            )

        # Compare favorite locations
        if old_prefs.favorite_locations != new_prefs.favorite_locations:
            changes.append(
                {
                    "change_type": "favorite_locations",
                    "old_value": json.dumps(old_prefs.favorite_locations),
                    "new_value": json.dumps(new_prefs.favorite_locations),
                }
            )

        # Log changes
        if changes:
            with sqlite3.connect(self.db_path) as conn:
                for change in changes:
                    conn.execute(
                        "INSERT INTO preference_history (user_id, change_type, "
                        "old_value, new_value) VALUES (?, ?, ?, ?)",
                        (user_id, change["change_type"], change["old_value"], change["new_value"]),
                    )
                conn.commit()

    async def count(self, criteria: Optional[Dict[str, Any]] = None) -> int:
        """Count user preferences records."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT COUNT(*) FROM user_preferences")
            return cursor.fetchone()[0]

    async def cleanup_old_history(self, days_to_keep: int = 90) -> int:
        """Clean up old preference history records."""
        cutoff_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        cutoff_date = cutoff_date.replace(day=cutoff_date.day - days_to_keep)

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "DELETE FROM preference_history WHERE changed_at < ?", (cutoff_date.isoformat(),)
            )
            conn.commit()
            return cursor.rowcount
