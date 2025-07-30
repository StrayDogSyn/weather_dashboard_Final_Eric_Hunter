"""Weather Journal Service

This module provides the core business logic and database operations
for the weather journal functionality.
"""

import sqlite3
import logging
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional, Dict, Any, Tuple
from contextlib import contextmanager

from models.journal_entry import JournalEntry
from services.enhanced_weather_service import EnhancedWeatherService


class JournalService:
    """Service for managing weather journal entries with SQLite persistence."""
    
    def __init__(self, db_path: str = "data/weather_journal.db", weather_service: Optional[EnhancedWeatherService] = None):
        """Initialize the journal service.
        
        Args:
            db_path: Path to SQLite database file
            weather_service: Weather service for auto-population
        """
        self.db_path = Path(db_path)
        self.weather_service = weather_service
        self.logger = logging.getLogger(__name__)
        
        # Ensure database directory exists
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize database
        self._init_database()
    
    def _init_database(self) -> None:
        """Initialize the SQLite database with required schema."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # Create journal entries table with proper constraints
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS journal_entries (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        date_created TEXT NOT NULL,
                        weather_data TEXT,
                        mood_rating INTEGER CHECK(mood_rating >= 1 AND mood_rating <= 10),
                        entry_content TEXT NOT NULL,
                        tags TEXT,
                        location TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Create indexes for better search performance
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_journal_date_created 
                    ON journal_entries(date_created)
                """)
                
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_journal_mood_rating 
                    ON journal_entries(mood_rating)
                """)
                
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_journal_location 
                    ON journal_entries(location)
                """)
                
                conn.commit()
                self.logger.info("Database initialized successfully")
                
        except sqlite3.Error as e:
            self.logger.error(f"Database initialization failed: {e}")
            raise
    
    @contextmanager
    def _get_connection(self):
        """Get database connection with proper error handling.
        
        Yields:
            sqlite3.Connection: Database connection
        """
        conn = None
        try:
            conn = sqlite3.connect(str(self.db_path))
            conn.row_factory = sqlite3.Row  # Enable column access by name
            yield conn
        except sqlite3.Error as e:
            if conn:
                conn.rollback()
            self.logger.error(f"Database error: {e}")
            raise
        finally:
            if conn:
                conn.close()
    
    async def create_entry(self, content: str, mood_rating: Optional[int] = None, 
                          tags: Optional[List[str]] = None, location: Optional[str] = None,
                          auto_populate_weather: bool = True) -> JournalEntry:
        """Create a new journal entry.
        
        Args:
            content: Entry content
            mood_rating: Mood rating (1-10)
            tags: List of tags
            location: Location for the entry
            auto_populate_weather: Whether to auto-populate weather data
            
        Returns:
            Created journal entry
        """
        try:
            # Get current weather data if requested
            weather_data = None
            if auto_populate_weather and self.weather_service:
                try:
                    current_weather = await self.weather_service.get_current_weather()
                    if current_weather:
                        weather_data = {
                            'temperature': current_weather.get('temperature'),
                            'condition': current_weather.get('condition'),
                            'humidity': current_weather.get('humidity'),
                            'wind_speed': current_weather.get('wind_speed'),
                            'pressure': current_weather.get('pressure'),
                            'visibility': current_weather.get('visibility')
                        }
                except Exception as e:
                    self.logger.warning(f"Failed to get weather data: {e}")
            
            # Create journal entry
            entry = JournalEntry(
                date_created=datetime.now(),
                weather_data=weather_data,
                mood_rating=mood_rating,
                entry_content=content,
                tags=tags or [],
                location=location
            )
            
            # Save to database
            entry_id = self._save_entry(entry)
            entry.id = entry_id
            
            self.logger.info(f"Created journal entry with ID: {entry_id}")
            return entry
            
        except Exception as e:
            self.logger.error(f"Failed to create journal entry: {e}")
            raise
    
    def _save_entry(self, entry: JournalEntry) -> int:
        """Save journal entry to database.
        
        Args:
            entry: Journal entry to save
            
        Returns:
            ID of saved entry
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                entry_dict = entry.to_dict()
                
                if entry.id is None:
                    # Insert new entry
                    cursor.execute("""
                        INSERT INTO journal_entries 
                        (date_created, weather_data, mood_rating, entry_content, tags, location)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (
                        entry_dict['date_created'],
                        entry_dict['weather_data'],
                        entry_dict['mood_rating'],
                        entry_dict['entry_content'],
                        entry_dict['tags'],
                        entry_dict['location']
                    ))
                    
                    entry_id = cursor.lastrowid
                else:
                    # Update existing entry
                    cursor.execute("""
                        UPDATE journal_entries 
                        SET date_created=?, weather_data=?, mood_rating=?, 
                            entry_content=?, tags=?, location=?, updated_at=CURRENT_TIMESTAMP
                        WHERE id=?
                    """, (
                        entry_dict['date_created'],
                        entry_dict['weather_data'],
                        entry_dict['mood_rating'],
                        entry_dict['entry_content'],
                        entry_dict['tags'],
                        entry_dict['location'],
                        entry.id
                    ))
                    
                    entry_id = entry.id
                
                conn.commit()
                return entry_id
                
        except sqlite3.Error as e:
            self.logger.error(f"Failed to save entry: {e}")
            raise
    
    def get_entry(self, entry_id: int) -> Optional[JournalEntry]:
        """Get journal entry by ID.
        
        Args:
            entry_id: Entry ID
            
        Returns:
            Journal entry or None if not found
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT * FROM journal_entries WHERE id = ?",
                    (entry_id,)
                )
                
                row = cursor.fetchone()
                if row:
                    return JournalEntry.from_dict(dict(row))
                return None
                
        except sqlite3.Error as e:
            self.logger.error(f"Failed to get entry {entry_id}: {e}")
            raise
    
    def get_entries(self, limit: int = 50, offset: int = 0, 
                   start_date: Optional[datetime] = None,
                   end_date: Optional[datetime] = None) -> List[JournalEntry]:
        """Get journal entries with pagination and date filtering.
        
        Args:
            limit: Maximum number of entries to return
            offset: Number of entries to skip
            start_date: Filter entries after this date
            end_date: Filter entries before this date
            
        Returns:
            List of journal entries
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                query = "SELECT * FROM journal_entries WHERE 1=1"
                params = []
                
                if start_date:
                    query += " AND date_created >= ?"
                    params.append(start_date.isoformat())
                
                if end_date:
                    query += " AND date_created <= ?"
                    params.append(end_date.isoformat())
                
                query += " ORDER BY date_created DESC LIMIT ? OFFSET ?"
                params.extend([limit, offset])
                
                cursor.execute(query, params)
                rows = cursor.fetchall()
                
                return [JournalEntry.from_dict(dict(row)) for row in rows]
                
        except sqlite3.Error as e:
            self.logger.error(f"Failed to get entries: {e}")
            raise
    
    def search_entries(self, query: str, limit: int = 50) -> List[JournalEntry]:
        """Search journal entries by content and tags.
        
        Args:
            query: Search query
            limit: Maximum number of results
            
        Returns:
            List of matching journal entries
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # Search in content, tags, and location
                search_query = """
                    SELECT * FROM journal_entries 
                    WHERE entry_content LIKE ? 
                       OR tags LIKE ? 
                       OR location LIKE ?
                    ORDER BY date_created DESC 
                    LIMIT ?
                """
                
                search_term = f"%{query}%"
                cursor.execute(search_query, (search_term, search_term, search_term, limit))
                rows = cursor.fetchall()
                
                return [JournalEntry.from_dict(dict(row)) for row in rows]
                
        except sqlite3.Error as e:
            self.logger.error(f"Failed to search entries: {e}")
            raise
    
    def update_entry(self, entry: JournalEntry) -> bool:
        """Update an existing journal entry.
        
        Args:
            entry: Journal entry to update
            
        Returns:
            True if update was successful
        """
        try:
            if entry.id is None:
                raise ValueError("Cannot update entry without ID")
            
            self._save_entry(entry)
            self.logger.info(f"Updated journal entry {entry.id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to update entry {entry.id}: {e}")
            return False
    
    def delete_entry(self, entry_id: int) -> bool:
        """Delete a journal entry.
        
        Args:
            entry_id: ID of entry to delete
            
        Returns:
            True if deletion was successful
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM journal_entries WHERE id = ?", (entry_id,))
                
                if cursor.rowcount > 0:
                    conn.commit()
                    self.logger.info(f"Deleted journal entry {entry_id}")
                    return True
                else:
                    self.logger.warning(f"Entry {entry_id} not found for deletion")
                    return False
                    
        except sqlite3.Error as e:
            self.logger.error(f"Failed to delete entry {entry_id}: {e}")
            return False
    
    def get_entry_count(self) -> int:
        """Get total number of journal entries.
        
        Returns:
            Total entry count
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM journal_entries")
                return cursor.fetchone()[0]
                
        except sqlite3.Error as e:
            self.logger.error(f"Failed to get entry count: {e}")
            return 0
    
    def get_mood_statistics(self, days: int = 30) -> Dict[str, Any]:
        """Get mood statistics for the specified period.
        
        Args:
            days: Number of days to analyze
            
        Returns:
            Dictionary with mood statistics
        """
        try:
            start_date = datetime.now() - timedelta(days=days)
            
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # Get mood statistics
                cursor.execute("""
                    SELECT 
                        AVG(mood_rating) as avg_mood,
                        MIN(mood_rating) as min_mood,
                        MAX(mood_rating) as max_mood,
                        COUNT(*) as total_entries
                    FROM journal_entries 
                    WHERE date_created >= ? AND mood_rating IS NOT NULL
                """, (start_date.isoformat(),))
                
                stats = cursor.fetchone()
                
                return {
                    'average_mood': round(stats[0], 2) if stats[0] else None,
                    'min_mood': stats[1],
                    'max_mood': stats[2],
                    'total_entries': stats[3],
                    'period_days': days
                }
                
        except sqlite3.Error as e:
            self.logger.error(f"Failed to get mood statistics: {e}")
            return {}
    
    def get_popular_tags(self, limit: int = 10) -> List[Tuple[str, int]]:
        """Get most popular tags.
        
        Args:
            limit: Maximum number of tags to return
            
        Returns:
            List of (tag, count) tuples
        """
        try:
            entries = self.get_entries(limit=1000)  # Get recent entries
            tag_counts = {}
            
            for entry in entries:
                for tag in entry.tags:
                    tag_counts[tag] = tag_counts.get(tag, 0) + 1
            
            # Sort by count and return top tags
            sorted_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)
            return sorted_tags[:limit]
            
        except Exception as e:
            self.logger.error(f"Failed to get popular tags: {e}")
            return []