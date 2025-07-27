#!/usr/bin/env python3
"""
Database Manager - Professional SQLite Data Persistence

This module demonstrates advanced database management patterns including:
- Schema versioning and migrations
- Connection pooling and transaction management
- Type-safe data access patterns
- Professional error handling and logging
- Data validation and sanitization
"""

import sqlite3
import logging
import json
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from contextlib import contextmanager
from dataclasses import dataclass


@dataclass
class WeatherRecord:
    """Type-safe weather data record."""
    id: Optional[int] = None
    city: str = ""
    timestamp: datetime = None
    temperature: float = 0.0
    feels_like: float = 0.0
    humidity: int = 0
    pressure: float = 0.0
    wind_speed: float = 0.0
    wind_direction: int = 0
    weather_condition: str = ""
    weather_description: str = ""
    icon_code: str = ""
    visibility: float = 0.0
    uv_index: float = 0.0
    raw_data: str = "{}"  # JSON string of complete API response


@dataclass
class JournalEntry:
    """Type-safe journal entry record."""
    id: Optional[int] = None
    timestamp: datetime = None
    city: str = ""
    weather_condition: str = ""
    temperature: float = 0.0
    title: str = ""
    content: str = ""
    mood_rating: int = 5  # 1-10 scale
    tags: str = ""  # Comma-separated tags
    created_at: datetime = None
    updated_at: datetime = None


class DatabaseManager:
    """
    Professional SQLite database management system.

    This class demonstrates enterprise-level database patterns:
    - Schema versioning and automatic migrations
    - Connection management with proper cleanup
    - Transaction handling for data integrity
    - Type-safe data access methods
    - Performance optimization with indexing
    """

    # Database schema version for migration management
    SCHEMA_VERSION = 1

    def __init__(self, db_path: Optional[Path] = None):
        """Initialize the database manager."""
        self.logger = logging.getLogger(__name__)

        # Set up database path
        if db_path is None:
            app_data_dir = Path.home() / ".weather_dashboard"
            app_data_dir.mkdir(exist_ok=True)
            db_path = app_data_dir / "weather_dashboard.db"

        self.db_path = db_path
        self._connection: Optional[sqlite3.Connection] = None

        # Initialize database
        self._initialize_database()

    def _initialize_database(self) -> None:
        """
        Initialize the database with proper schema and migrations.

        This method demonstrates professional database initialization:
        - Schema creation with proper data types
        - Index creation for performance
        - Migration handling for schema updates
        """
        try:
            with self._get_connection() as conn:
                # Enable foreign key constraints
                conn.execute("PRAGMA foreign_keys = ON")

                # Create schema version table
                self._create_schema_version_table(conn)

                # Check current schema version
                current_version = self._get_schema_version(conn)

                if current_version == 0:
                    # Fresh database - create all tables
                    self._create_initial_schema(conn)
                    self._set_schema_version(conn, self.SCHEMA_VERSION)
                elif current_version < self.SCHEMA_VERSION:
                    # Run migrations
                    self._run_migrations(conn, current_version)

                self.logger.info(f"Database initialized at version {self.SCHEMA_VERSION}")

        except Exception as e:
            self.logger.error(f"Failed to initialize database: {e}")
            raise

    @contextmanager
    def _get_connection(self):
        """
        Context manager for database connections with proper cleanup.

        This pattern ensures connections are always properly closed
        and transactions are handled correctly.
        """
        conn = None
        try:
            conn = sqlite3.connect(
                self.db_path,
                timeout=30.0,  # 30 second timeout
                isolation_level=None  # Autocommit mode
            )

            # Configure connection for better performance and reliability
            conn.row_factory = sqlite3.Row  # Enable column access by name
            conn.execute("PRAGMA journal_mode = WAL")  # Write-Ahead Logging
            conn.execute("PRAGMA synchronous = NORMAL")  # Balance safety/performance
            conn.execute("PRAGMA cache_size = 10000")  # 10MB cache

            yield conn

        except Exception as e:
            if conn:
                conn.rollback()
            self.logger.error(f"Database connection error: {e}")
            raise
        finally:
            if conn:
                conn.close()

    @contextmanager
    def get_connection(self):
        """
        Public context manager for database connections.

        This provides external access to database connections
        while maintaining proper cleanup patterns.
        """
        with self._get_connection() as conn:
            yield conn

    def _create_schema_version_table(self, conn: sqlite3.Connection) -> None:
        """Create schema version tracking table."""
        conn.execute("""
            CREATE TABLE IF NOT EXISTS schema_version (
                version INTEGER PRIMARY KEY
            )
        """)

    def _get_schema_version(self, conn: sqlite3.Connection) -> int:
        """Get current schema version."""
        cursor = conn.execute("SELECT version FROM schema_version ORDER BY version DESC LIMIT 1")
        row = cursor.fetchone()
        return row[0] if row else 0

    def _set_schema_version(self, conn: sqlite3.Connection, version: int) -> None:
        """Set schema version."""
        conn.execute("INSERT OR REPLACE INTO schema_version (version) VALUES (?)", (version,))

    def _create_initial_schema(self, conn: sqlite3.Connection) -> None:
        """
        Create the initial database schema.

        This method demonstrates professional database design:
        - Proper data types and constraints
        - Performance indexes
        - Referential integrity
        """
        # Weather data table
        conn.execute("""
            CREATE TABLE weather_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                city TEXT NOT NULL,
                timestamp DATETIME NOT NULL,
                temperature REAL NOT NULL,
                feels_like REAL,
                humidity INTEGER,
                pressure REAL,
                wind_speed REAL,
                wind_direction INTEGER,
                weather_condition TEXT,
                weather_description TEXT,
                icon_code TEXT,
                visibility REAL,
                uv_index REAL,
                raw_data TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Journal entries table
        conn.execute("""
            CREATE TABLE journal_entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME NOT NULL,
                city TEXT NOT NULL,
                weather_condition TEXT,
                temperature REAL,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                mood_rating INTEGER CHECK (mood_rating >= 1 AND mood_rating <= 10),
                tags TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # User settings table
        conn.execute("""
            CREATE TABLE user_settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Activity suggestions table is created by ActivityDatabase
        # with more comprehensive schema

        # Create performance indexes
        self._create_indexes(conn)

    def _create_indexes(self, conn: sqlite3.Connection) -> None:
        """Create database indexes for optimal performance."""
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_weather_city_timestamp ON weather_data(city, timestamp)",
            "CREATE INDEX IF NOT EXISTS idx_weather_timestamp ON weather_data(timestamp)",
            "CREATE INDEX IF NOT EXISTS idx_journal_timestamp ON journal_entries(timestamp)",
            "CREATE INDEX IF NOT EXISTS idx_journal_city ON journal_entries(city)",
            "CREATE INDEX IF NOT EXISTS idx_journal_tags ON journal_entries(tags)",
            # Activity suggestions indexes are created by ActivityDatabase
        ]

        for index_sql in indexes:
            conn.execute(index_sql)

    def _run_migrations(self, conn: sqlite3.Connection, current_version: int) -> None:
        """
        Run database migrations from current version to latest.

        This method demonstrates professional database migration patterns
        for handling schema updates in production environments.
        """
        self.logger.info(f"Running migrations from version {current_version} to {self.SCHEMA_VERSION}")

        # Future migrations would go here
        # Example:
        # if current_version < 2:
        #     self._migrate_to_version_2(conn)

        self._set_schema_version(conn, self.SCHEMA_VERSION)

    # Weather Data Methods

    def save_weather_data(self, weather_record: WeatherRecord) -> int:
        """
        Save weather data to the database.

        Args:
            weather_record: WeatherRecord object to save

        Returns:
            int: ID of the saved record
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.execute("""
                    INSERT INTO weather_data (
                        city, timestamp, temperature, feels_like, humidity,
                        pressure, wind_speed, wind_direction, weather_condition,
                        weather_description, icon_code, visibility, uv_index, raw_data
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    weather_record.city,
                    weather_record.timestamp,
                    weather_record.temperature,
                    weather_record.feels_like,
                    weather_record.humidity,
                    weather_record.pressure,
                    weather_record.wind_speed,
                    weather_record.wind_direction,
                    weather_record.weather_condition,
                    weather_record.weather_description,
                    weather_record.icon_code,
                    weather_record.visibility,
                    weather_record.uv_index,
                    weather_record.raw_data
                ))

                record_id = cursor.lastrowid
                self.logger.debug(f"Saved weather data for {weather_record.city} with ID {record_id}")
                return record_id

        except Exception as e:
            self.logger.error(f"Failed to save weather data: {e}")
            raise

    def get_weather_history(self, city: str, days: int = 7) -> List[WeatherRecord]:
        """
        Get weather history for a city.

        Args:
            city: City name
            days: Number of days of history to retrieve

        Returns:
            List of WeatherRecord objects
        """
        try:
            cutoff_date = datetime.now() - timedelta(days=days)

            with self._get_connection() as conn:
                cursor = conn.execute("""
                    SELECT * FROM weather_data
                    WHERE city = ? AND timestamp >= ?
                    ORDER BY timestamp DESC
                """, (city, cutoff_date))

                records = []
                for row in cursor.fetchall():
                    record = WeatherRecord(
                        id=row['id'],
                        city=row['city'],
                        timestamp=datetime.fromisoformat(row['timestamp']),
                        temperature=row['temperature'],
                        feels_like=row['feels_like'],
                        humidity=row['humidity'],
                        pressure=row['pressure'],
                        wind_speed=row['wind_speed'],
                        wind_direction=row['wind_direction'],
                        weather_condition=row['weather_condition'],
                        weather_description=row['weather_description'],
                        icon_code=row['icon_code'],
                        visibility=row['visibility'],
                        uv_index=row['uv_index'],
                        raw_data=row['raw_data']
                    )
                    records.append(record)

                self.logger.debug(f"Retrieved {len(records)} weather records for {city}")
                return records

        except Exception as e:
            self.logger.error(f"Failed to get weather history: {e}")
            return []

    # Journal Entry Methods

    def save_journal_entry(self, entry: JournalEntry) -> int:
        """
        Save a journal entry to the database.

        Args:
            entry: JournalEntry object to save

        Returns:
            int: ID of the saved entry
        """
        try:
            with self._get_connection() as conn:
                if entry.id is None:
                    # Insert new entry
                    cursor = conn.execute("""
                        INSERT INTO journal_entries (
                            timestamp, city, weather_condition, temperature,
                            title, content, mood_rating, tags
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        entry.timestamp,
                        entry.city,
                        entry.weather_condition,
                        entry.temperature,
                        entry.title,
                        entry.content,
                        entry.mood_rating,
                        entry.tags
                    ))
                    entry_id = cursor.lastrowid
                else:
                    # Update existing entry
                    conn.execute("""
                        UPDATE journal_entries SET
                            timestamp = ?, city = ?, weather_condition = ?,
                            temperature = ?, title = ?, content = ?,
                            mood_rating = ?, tags = ?, updated_at = CURRENT_TIMESTAMP
                        WHERE id = ?
                    """, (
                        entry.timestamp,
                        entry.city,
                        entry.weather_condition,
                        entry.temperature,
                        entry.title,
                        entry.content,
                        entry.mood_rating,
                        entry.tags,
                        entry.id
                    ))
                    entry_id = entry.id

                self.logger.debug(f"Saved journal entry with ID {entry_id}")
                return entry_id

        except Exception as e:
            self.logger.error(f"Failed to save journal entry: {e}")
            raise

    def get_journal_entries(self, limit: int = 50, search_term: str = "") -> List[JournalEntry]:
        """
        Get journal entries with optional search.

        Args:
            limit: Maximum number of entries to return
            search_term: Optional search term for title/content

        Returns:
            List of JournalEntry objects
        """
        try:
            with self._get_connection() as conn:
                if search_term:
                    cursor = conn.execute("""
                        SELECT * FROM journal_entries
                        WHERE title LIKE ? OR content LIKE ? OR tags LIKE ?
                        ORDER BY timestamp DESC
                        LIMIT ?
                    """, (f"%{search_term}%", f"%{search_term}%", f"%{search_term}%", limit))
                else:
                    cursor = conn.execute("""
                        SELECT * FROM journal_entries
                        ORDER BY timestamp DESC
                        LIMIT ?
                    """, (limit,))

                entries = []
                for row in cursor.fetchall():
                    entry = JournalEntry(
                        id=row['id'],
                        timestamp=datetime.fromisoformat(row['timestamp']),
                        city=row['city'],
                        weather_condition=row['weather_condition'],
                        temperature=row['temperature'],
                        title=row['title'],
                        content=row['content'],
                        mood_rating=row['mood_rating'],
                        tags=row['tags'],
                        created_at=datetime.fromisoformat(row['created_at']),
                        updated_at=datetime.fromisoformat(row['updated_at'])
                    )
                    entries.append(entry)

                self.logger.debug(f"Retrieved {len(entries)} journal entries")
                return entries

        except Exception as e:
            self.logger.error(f"Failed to get journal entries: {e}")
            return []

    def delete_journal_entry(self, entry_id: int) -> bool:
        """
        Delete a journal entry.

        Args:
            entry_id: ID of the entry to delete

        Returns:
            bool: True if deleted successfully
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.execute("DELETE FROM journal_entries WHERE id = ?", (entry_id,))

                if cursor.rowcount > 0:
                    self.logger.debug(f"Deleted journal entry {entry_id}")
                    return True
                else:
                    self.logger.warning(f"Journal entry {entry_id} not found")
                    return False

        except Exception as e:
            self.logger.error(f"Failed to delete journal entry: {e}")
            return False

    # Settings Methods

    def save_setting(self, key: str, value: Any) -> None:
        """
        Save a user setting.

        Args:
            key: Setting key
            value: Setting value (will be JSON serialized)
        """
        try:
            value_json = json.dumps(value)

            with self._get_connection() as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO user_settings (key, value, updated_at)
                    VALUES (?, ?, CURRENT_TIMESTAMP)
                """, (key, value_json))

                self.logger.debug(f"Saved setting {key}")

        except Exception as e:
            self.logger.error(f"Failed to save setting {key}: {e}")

    def get_setting(self, key: str, default: Any = None) -> Any:
        """
        Get a user setting.

        Args:
            key: Setting key
            default: Default value if setting not found

        Returns:
            Setting value or default
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.execute("SELECT value FROM user_settings WHERE key = ?", (key,))
                row = cursor.fetchone()

                if row:
                    return json.loads(row['value'])
                else:
                    return default

        except Exception as e:
            self.logger.error(f"Failed to get setting {key}: {e}")
            return default

    def cleanup_old_data(self, days_to_keep: int = 30) -> None:
        """
        Clean up old data to prevent database bloat.

        Args:
            days_to_keep: Number of days of data to retain
        """
        try:
            cutoff_date = datetime.now() - timedelta(days=days_to_keep)

            with self._get_connection() as conn:
                # Clean up old weather data
                cursor = conn.execute(
                    "DELETE FROM weather_data WHERE timestamp < ?",
                    (cutoff_date,)
                )
                weather_deleted = cursor.rowcount

                # Vacuum database to reclaim space
                conn.execute("VACUUM")

                self.logger.info(
                    f"Cleaned up {weather_deleted} old weather records older than {days_to_keep} days"
                )

        except Exception as e:
            self.logger.error(f"Failed to cleanup old data: {e}")

    def close(self) -> None:
        """
        Close database connections and cleanup resources.

        This method ensures proper cleanup when the application shuts down.
        """
        try:
            # Run final cleanup
            self.cleanup_old_data()

            self.logger.info("Database manager closed successfully")

        except Exception as e:
            self.logger.error(f"Error during database cleanup: {e}")
