import json
import sqlite3
from pathlib import Path
from typing import Dict, List


class WeatherJournal:
    """Weather journal with mood tracking and notes."""

    def __init__(self, db_path: str = None):
        if db_path is None:
            db_dir = Path("data")
            db_dir.mkdir(exist_ok=True)
            db_path = db_dir / "weather_journal.db"

        self.db_path = str(db_path)
        self._init_database()

    def _init_database(self):
        """Initialize journal database."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS journal_entries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date_created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    location TEXT NOT NULL,
                    weather_condition TEXT,
                    temperature REAL,
                    mood_rating INTEGER CHECK(mood_rating >= 1 AND mood_rating <= 10),
                    mood_emoji TEXT,
                    notes TEXT,
                    tags TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """
            )

            # Create index for faster queries
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_date_created
                ON journal_entries(date_created DESC)
            """
            )

            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_mood_rating
                ON journal_entries(mood_rating)
            """
            )

    def add_entry(
        self,
        location: str,
        weather_condition: str,
        temperature: float,
        mood_rating: int,
        mood_emoji: str,
        notes: str,
        tags: List[str] = None,
    ) -> int:
        """Add new journal entry."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """
                INSERT INTO journal_entries
                (location, weather_condition, temperature, mood_rating, mood_emoji, notes, tags)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    location,
                    weather_condition,
                    temperature,
                    mood_rating,
                    mood_emoji,
                    notes,
                    json.dumps(tags) if tags else None,
                ),
            )
            return cursor.lastrowid

    def get_entries(
        self, limit: int = 50, offset: int = 0, mood: str = None, location: str = None
    ) -> List[Dict]:
        """Get journal entries with optional filtering."""
        query = """
            SELECT * FROM journal_entries
            WHERE 1=1
        """
        params = []

        if mood:
            query += " AND mood_rating = ?"
            params.append(mood)

        if location:
            query += " AND location = ?"
            params.append(location)

        query += " ORDER BY date_created DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(query, params)

            entries = []
            for row in cursor:
                entry = dict(row)
                if entry["tags"]:
                    entry["tags"] = json.loads(entry["tags"])
                entries.append(entry)

            return entries

    def get_mood_statistics(self) -> Dict[str, int]:
        """Get mood distribution statistics."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """
                SELECT mood_rating, COUNT(*) as count
                FROM journal_entries
                WHERE mood_rating IS NOT NULL
                GROUP BY mood_rating
            """
            )

            return {row[0]: row[1] for row in cursor}

    def search_entries(self, query: str) -> List[Dict]:
        """Search entries by text in notes."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                """
                SELECT * FROM journal_entries
                WHERE notes LIKE ?
                ORDER BY date_created DESC
            """,
                (f"%{query}%",),
            )

            entries = []
            for row in cursor:
                entry = dict(row)
                if entry["tags"]:
                    entry["tags"] = json.loads(entry["tags"])
                entries.append(entry)

            return entries
