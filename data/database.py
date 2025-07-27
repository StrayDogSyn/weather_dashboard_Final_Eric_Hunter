"""Database foundation with SQLite operations."""

import sqlite3
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Any
from contextlib import contextmanager

from config.settings import settings


class DatabaseError(Exception):
    """Custom exception for database operations."""
    pass


class Database:
    """SQLite database manager for weather data."""
    
    def __init__(self):
        self.db_path = Path(settings.database_path)
        self._ensure_database_exists()
        self._create_tables()
    
    def _ensure_database_exists(self):
        """Create database directory if it doesn't exist."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
    
    @contextmanager
    def get_connection(self):
        """Context manager for database connections."""
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row  # Enable dict-like access
            yield conn
        except sqlite3.Error as e:
            if conn:
                conn.rollback()
            raise DatabaseError(f"Database operation failed: {e}")
        finally:
            if conn:
                conn.close()
    
    def _create_tables(self):
        """Create necessary database tables."""
        with self.get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS weather_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    location TEXT NOT NULL,
                    temperature REAL NOT NULL,
                    humidity INTEGER NOT NULL,
                    description TEXT NOT NULL,
                    timestamp DATETIME NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()
    
    def insert_weather_data(self, location: str, temperature: float, 
                          humidity: int, description: str) -> int:
        """Insert weather data record."""
        with self.get_connection() as conn:
            cursor = conn.execute("""
                INSERT INTO weather_data (location, temperature, humidity, description, timestamp)
                VALUES (?, ?, ?, ?, ?)
            """, (location, temperature, humidity, description, datetime.now()))
            conn.commit()
            return cursor.lastrowid
    
    def get_recent_weather(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent weather data records."""
        with self.get_connection() as conn:
            cursor = conn.execute("""
                SELECT * FROM weather_data 
                ORDER BY timestamp DESC 
                LIMIT ?
            """, (limit,))
            return [dict(row) for row in cursor.fetchall()]
    
    def get_weather_by_location(self, location: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Get weather data for specific location."""
        with self.get_connection() as conn:
            cursor = conn.execute("""
                SELECT * FROM weather_data 
                WHERE location LIKE ? 
                ORDER BY timestamp DESC 
                LIMIT ?
            """, (f"%{location}%", limit))
            return [dict(row) for row in cursor.fetchall()]