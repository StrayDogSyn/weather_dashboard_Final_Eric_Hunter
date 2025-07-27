#!/usr/bin/env python3
"""
Weather Journal Database - Database operations and persistence

This module handles all database operations for the Weather Journal feature
including CRUD operations, search, and analytics.
"""

import json
from datetime import datetime
from typing import Dict, List, Optional

from ...utils.logger import LoggerMixin
from ...core.database_manager import DatabaseManager
from .models import JournalEntry, EntryMood, SearchFilter


class JournalDatabase(LoggerMixin):
    """
    Database manager for journal entries.

    This class provides comprehensive database operations
    for journal entry persistence and retrieval.
    """

    def __init__(self, database_manager: DatabaseManager):
        self.database_manager = database_manager
        self._create_tables()

    def _create_tables(self):
        """Create journal tables if they don't exist."""
        try:
            with self.database_manager.get_connection() as conn:
                cursor = conn.cursor()

                # Create journal entries table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS journal_entries (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        title TEXT NOT NULL,
                        content TEXT NOT NULL,
                        mood TEXT,
                        tags TEXT,  -- JSON array of tags
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        weather_temperature REAL,
                        weather_condition TEXT,
                        weather_humidity REAL,
                        weather_pressure REAL,
                        weather_wind_speed REAL,
                        weather_location TEXT,
                        word_count INTEGER DEFAULT 0,
                        reading_time INTEGER DEFAULT 0,
                        is_favorite BOOLEAN DEFAULT FALSE,
                        is_private BOOLEAN DEFAULT FALSE
                    )
                """)

                # Create search index for full-text search
                cursor.execute("""
                    CREATE VIRTUAL TABLE IF NOT EXISTS journal_search
                    USING fts5(title, content, tags, weather_condition)
                """)

                conn.commit()

        except Exception as e:
            self.logger.error(f"Error creating journal tables: {e}")
            raise

    def save_entry(self, entry: JournalEntry) -> int:
        """Save journal entry to database."""
        try:
            with self.database_manager.get_connection() as conn:
                cursor = conn.cursor()

                tags_json = json.dumps(entry.tags) if entry.tags else '[]'
                mood_value = entry.mood.value if entry.mood else None

                if entry.id is None:
                    # Insert new entry
                    cursor.execute("""
                        INSERT INTO journal_entries (
                            title, content, mood, tags, created_at, updated_at,
                            weather_temperature, weather_condition, weather_humidity,
                            weather_pressure, weather_wind_speed, weather_location,
                            word_count, reading_time, is_favorite, is_private
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        entry.title, entry.content, mood_value, tags_json,
                        entry.created_at, entry.updated_at,
                        entry.weather_temperature, entry.weather_condition,
                        entry.weather_humidity, entry.weather_pressure,
                        entry.weather_wind_speed, entry.weather_location,
                        entry.word_count, entry.reading_time,
                        entry.is_favorite, entry.is_private
                    ))

                    entry.id = cursor.lastrowid

                    # Add to search index
                    cursor.execute("""
                        INSERT INTO journal_search (rowid, title, content, tags, weather_condition)
                        VALUES (?, ?, ?, ?, ?)
                    """, (
                        entry.id, entry.title, entry.content,
                        ' '.join(entry.tags), entry.weather_condition or ''
                    ))

                else:
                    # Update existing entry
                    cursor.execute("""
                        UPDATE journal_entries SET
                            title = ?, content = ?, mood = ?, tags = ?, updated_at = ?,
                            weather_temperature = ?, weather_condition = ?,
                            weather_humidity = ?, weather_pressure = ?,
                            weather_wind_speed = ?, weather_location = ?,
                            word_count = ?, reading_time = ?,
                            is_favorite = ?, is_private = ?
                        WHERE id = ?
                    """, (
                        entry.title, entry.content, mood_value, tags_json, entry.updated_at,
                        entry.weather_temperature, entry.weather_condition,
                        entry.weather_humidity, entry.weather_pressure,
                        entry.weather_wind_speed, entry.weather_location,
                        entry.word_count, entry.reading_time,
                        entry.is_favorite, entry.is_private, entry.id
                    ))

                    # Update search index
                    cursor.execute("""
                        UPDATE journal_search SET
                            title = ?, content = ?, tags = ?, weather_condition = ?
                        WHERE rowid = ?
                    """, (
                        entry.title, entry.content, ' '.join(entry.tags),
                        entry.weather_condition or '', entry.id
                    ))

                conn.commit()
                return entry.id

        except Exception as e:
            self.logger.error(f"Error saving journal entry: {e}")
            raise

    def get_entry(self, entry_id: int) -> Optional[JournalEntry]:
        """Get journal entry by ID."""
        try:
            with self.database_manager.get_connection() as conn:
                cursor = conn.cursor()

                cursor.execute("""
                    SELECT * FROM journal_entries WHERE id = ?
                """, (entry_id,))

                row = cursor.fetchone()
                if row:
                    return self._row_to_entry(row)

                return None

        except Exception as e:
            self.logger.error(f"Error getting journal entry {entry_id}: {e}")
            return None

    def get_all_entries(self, limit: Optional[int] = None, offset: int = 0) -> List[JournalEntry]:
        """Get all journal entries."""
        try:
            with self.database_manager.get_connection() as conn:
                cursor = conn.cursor()

                query = "SELECT * FROM journal_entries ORDER BY updated_at DESC"
                params = []

                if limit:
                    query += " LIMIT ? OFFSET ?"
                    params.extend([limit, offset])

                cursor.execute(query, params)
                rows = cursor.fetchall()

                return [self._row_to_entry(row) for row in rows]

        except Exception as e:
            self.logger.error(f"Error getting journal entries: {e}")
            return []

    def search_entries(self, query: str, filter_type: SearchFilter = SearchFilter.ALL) -> List[JournalEntry]:
        """Search journal entries."""
        try:
            with self.database_manager.get_connection() as conn:
                cursor = conn.cursor()

                if filter_type == SearchFilter.ALL:
                    # Full-text search
                    cursor.execute("""
                        SELECT je.* FROM journal_entries je
                        JOIN journal_search js ON je.id = js.rowid
                        WHERE journal_search MATCH ?
                        ORDER BY je.updated_at DESC
                    """, (query,))
                else:
                    # Specific field search
                    field_map = {
                        SearchFilter.TITLE: "title",
                        SearchFilter.CONTENT: "content",
                        SearchFilter.MOOD: "mood",
                        SearchFilter.WEATHER: "weather_condition",
                        SearchFilter.TAGS: "tags"
                    }

                    field = field_map.get(filter_type, "title")
                    cursor.execute(f"""
                        SELECT * FROM journal_entries
                        WHERE {field} LIKE ?
                        ORDER BY updated_at DESC
                    """, (f"%{query}%",))

                rows = cursor.fetchall()
                return [self._row_to_entry(row) for row in rows]

        except Exception as e:
            self.logger.error(f"Error searching journal entries: {e}")
            return []

    def delete_entry(self, entry_id: int) -> bool:
        """Delete journal entry."""
        try:
            with self.database_manager.get_connection() as conn:
                cursor = conn.cursor()

                # Delete from main table
                cursor.execute("DELETE FROM journal_entries WHERE id = ?", (entry_id,))

                # Delete from search index
                cursor.execute("DELETE FROM journal_search WHERE rowid = ?", (entry_id,))

                conn.commit()
                return cursor.rowcount > 0

        except Exception as e:
            self.logger.error(f"Error deleting journal entry {entry_id}: {e}")
            return False

    def get_entries_by_date_range(self, start_date: datetime, end_date: datetime) -> List[JournalEntry]:
        """Get entries within date range."""
        try:
            with self.database_manager.get_connection() as conn:
                cursor = conn.cursor()

                cursor.execute("""
                    SELECT * FROM journal_entries
                    WHERE created_at BETWEEN ? AND ?
                    ORDER BY created_at DESC
                """, (start_date, end_date))

                rows = cursor.fetchall()
                return [self._row_to_entry(row) for row in rows]

        except Exception as e:
            self.logger.error(f"Error getting entries by date range: {e}")
            return []

    def get_mood_statistics(self) -> Dict[str, int]:
        """Get mood statistics for all entries."""
        try:
            with self.database_manager.get_connection() as conn:
                cursor = conn.cursor()

                cursor.execute("""
                    SELECT mood, COUNT(*) as count
                    FROM journal_entries
                    WHERE mood IS NOT NULL
                    GROUP BY mood
                """)

                rows = cursor.fetchall()
                return {row[0]: row[1] for row in rows}

        except Exception as e:
            self.logger.error(f"Error getting mood statistics: {e}")
            return {}

    def _row_to_entry(self, row) -> JournalEntry:
        """Convert database row to JournalEntry object."""
        tags = json.loads(row[4]) if row[4] else []

        # Find mood enum
        mood = None
        if row[3]:
            for mood_enum in EntryMood:
                if mood_enum.value == row[3]:
                    mood = mood_enum
                    break

        return JournalEntry(
            id=row[0],
            title=row[1],
            content=row[2],
            mood=mood,
            tags=tags,
            created_at=datetime.fromisoformat(row[5]) if row[5] else None,
            updated_at=datetime.fromisoformat(row[6]) if row[6] else None,
            weather_temperature=row[7],
            weather_condition=row[8],
            weather_humidity=row[9],
            weather_pressure=row[10],
            weather_wind_speed=row[11],
            weather_location=row[12],
            word_count=row[13] or 0,
            reading_time=row[14] or 0,
            is_favorite=bool(row[15]),
            is_private=bool(row[16])
        )