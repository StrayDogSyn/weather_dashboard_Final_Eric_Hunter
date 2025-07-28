"""Clean database foundation with SQLite operations."""

import sqlite3
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Any
from contextlib import contextmanager

from config.settings import get_settings


class DatabaseError(Exception):
    """Custom exception for database operations."""
    pass


class Database:
    """Simple SQLite database manager for weather data."""
    
    def __init__(self):
        self.settings = get_settings()
        self.db_path = Path(self.settings.database_path)
        self._ensure_database_exists()
        self._create_tables()
    
    def _ensure_database_exists(self) -> None:
        """Create database directory if it doesn't exist."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
    
    @contextmanager
    def get_connection(self):
        """Context manager for database connections with proper error handling."""
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row  # Enable dict-like access
            yield conn
        except sqlite3.Error as e:
            if conn:
                conn.rollback()
            logging.error(f"Database operation failed: {e}")
            raise DatabaseError(f"Database operation failed: {e}")
        finally:
            if conn:
                conn.close()
    
    def _create_tables(self) -> None:
        """Create necessary database tables."""
        with self.get_connection() as conn:
            # Weather data table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS weather_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    location TEXT NOT NULL,
                    temperature REAL NOT NULL,
                    feels_like REAL NOT NULL,
                    humidity INTEGER NOT NULL,
                    pressure INTEGER NOT NULL,
                    description TEXT NOT NULL,
                    icon TEXT NOT NULL,
                    wind_speed REAL NOT NULL,
                    wind_direction INTEGER NOT NULL,
                    visibility REAL,
                    timestamp DATETIME NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Weather journal entries
            conn.execute("""
                CREATE TABLE IF NOT EXISTS journal_entries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    content TEXT NOT NULL,
                    location TEXT,
                    weather_data TEXT,  -- JSON string of weather data
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # User preferences
            conn.execute("""
                CREATE TABLE IF NOT EXISTS user_preferences (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.commit()
    
    def save_weather_data(self, weather_data: Dict[str, Any]) -> int:
        """Save weather data to database.
        
        Args:
            weather_data: Dictionary containing weather information
            
        Returns:
            ID of the inserted record
        """
        with self.get_connection() as conn:
            cursor = conn.execute("""
                INSERT INTO weather_data (
                    location, temperature, feels_like, humidity, pressure,
                    description, icon, wind_speed, wind_direction, visibility, timestamp
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                weather_data.get('location', ''),
                weather_data.get('temperature', 0),
                weather_data.get('feels_like', 0),
                weather_data.get('humidity', 0),
                weather_data.get('pressure', 0),
                weather_data.get('description', ''),
                weather_data.get('icon', ''),
                weather_data.get('wind_speed', 0),
                weather_data.get('wind_direction', 0),
                weather_data.get('visibility'),
                weather_data.get('timestamp', datetime.now())
            ))
            conn.commit()
            return cursor.lastrowid
    
    def get_recent_weather(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent weather data records.
        
        Args:
            limit: Maximum number of records to return
            
        Returns:
            List of weather data dictionaries
        """
        with self.get_connection() as conn:
            cursor = conn.execute("""
                SELECT * FROM weather_data 
                ORDER BY timestamp DESC 
                LIMIT ?
            """, (limit,))
            return [dict(row) for row in cursor.fetchall()]
    
    def get_weather_by_location(self, location: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Get weather data for specific location.
        
        Args:
            location: Location name to search for
            limit: Maximum number of records to return
            
        Returns:
            List of weather data dictionaries
        """
        with self.get_connection() as conn:
            cursor = conn.execute("""
                SELECT * FROM weather_data 
                WHERE location LIKE ? 
                ORDER BY timestamp DESC 
                LIMIT ?
            """, (f"%{location}%", limit))
            return [dict(row) for row in cursor.fetchall()]
    
    def save_journal_entry(self, content: str, location: Optional[str] = None, 
                          weather_data: Optional[str] = None) -> int:
        """Save a journal entry.
        
        Args:
            content: Journal entry content
            location: Optional location
            weather_data: Optional weather data as JSON string
            
        Returns:
            ID of the inserted record
        """
        with self.get_connection() as conn:
            cursor = conn.execute("""
                INSERT INTO journal_entries (content, location, weather_data)
                VALUES (?, ?, ?)
            """, (content, location, weather_data))
            conn.commit()
            return cursor.lastrowid
    
    def get_journal_entries(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get recent journal entries.
        
        Args:
            limit: Maximum number of entries to return
            
        Returns:
            List of journal entry dictionaries
        """
        with self.get_connection() as conn:
            cursor = conn.execute("""
                SELECT * FROM journal_entries 
                ORDER BY created_at DESC 
                LIMIT ?
            """, (limit,))
            return [dict(row) for row in cursor.fetchall()]
    
    def set_preference(self, key: str, value: str) -> None:
        """Set a user preference.
        
        Args:
            key: Preference key
            value: Preference value
        """
        with self.get_connection() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO user_preferences (key, value, updated_at)
                VALUES (?, ?, ?)
            """, (key, value, datetime.now()))
            conn.commit()
    
    def get_preference(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """Get a user preference.
        
        Args:
            key: Preference key
            default: Default value if not found
            
        Returns:
            Preference value or default
        """
        with self.get_connection() as conn:
            cursor = conn.execute(
                "SELECT value FROM user_preferences WHERE key = ?", (key,)
            )
            row = cursor.fetchone()
            return row['value'] if row else default
    
    def cleanup_old_data(self, days: int = 30) -> int:
        """Clean up old weather data.
        
        Args:
            days: Number of days to keep
            
        Returns:
            Number of records deleted
        """
        with self.get_connection() as conn:
            cursor = conn.execute("""
                DELETE FROM weather_data 
                WHERE timestamp < datetime('now', '-{} days')
            """.format(days))
            conn.commit()
            return cursor.rowcount