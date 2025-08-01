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

import json
from models.journal_entry import JournalEntry
from .enhanced_weather_service import EnhancedWeatherService
from utils.photo_manager import PhotoManager


class JournalService:
    """Service for managing weather journal entries with SQLite persistence."""
    
    def __init__(self, db_path: str = "data/weather_journal.db", weather_service: Optional[EnhancedWeatherService] = None, photo_manager: Optional[PhotoManager] = None):
        """Initialize the journal service.
        
        Args:
            db_path: Path to SQLite database file
            weather_service: Weather service for auto-population
            photo_manager: Optional PhotoManager instance to avoid duplicate initialization
        """
        self.db_path = Path(db_path)
        self.weather_service = weather_service
        self.logger = logging.getLogger(__name__)
        
        # Initialize photo manager
        self.photo_manager = photo_manager or PhotoManager()
        
        # Ensure database directory exists
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize database
        self._init_database()
        
        # Migrate database if needed
        self._migrate_database()
    
    def _init_database(self) -> None:
        """Initialize the SQLite database with required schema."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # Create journal entries table with proper constraints
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS journal_entries (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        date TEXT NOT NULL,
                        title TEXT NOT NULL,
                        content TEXT NOT NULL,
                        mood_score INTEGER DEFAULT 5 CHECK(mood_score >= 1 AND mood_score <= 10),
                        mood_tags TEXT,
                        tags TEXT,
                        location TEXT,
                        temperature REAL,
                        weather_condition TEXT,
                        weather_data TEXT,
                        photos TEXT,
                        created_at TEXT,
                        updated_at TEXT,
                        -- Legacy columns for backward compatibility
                        date_created TEXT,
                        mood_rating INTEGER,
                        entry_content TEXT,
                        category TEXT,
                        template_used TEXT
                    )
                """)
                
                # Create FTS virtual table for full-text search (basic version first)
                cursor.execute("""
                    CREATE VIRTUAL TABLE IF NOT EXISTS journal_entries_fts USING fts5(
                        entry_content,
                        tags,
                        content='journal_entries',
                        content_rowid='id'
                    )
                """)
                
                # Create basic triggers to keep FTS table in sync
                cursor.execute("""
                    CREATE TRIGGER IF NOT EXISTS journal_entries_ai AFTER INSERT ON journal_entries BEGIN
                        INSERT INTO journal_entries_fts(rowid, entry_content, tags)
                        VALUES (new.id, new.entry_content, new.tags);
                    END
                """)
                
                cursor.execute("""
                    CREATE TRIGGER IF NOT EXISTS journal_entries_ad AFTER DELETE ON journal_entries BEGIN
                        INSERT INTO journal_entries_fts(journal_entries_fts, rowid, entry_content, tags)
                        VALUES('delete', old.id, old.entry_content, old.tags);
                    END
                """)
                
                cursor.execute("""
                    CREATE TRIGGER IF NOT EXISTS journal_entries_au AFTER UPDATE ON journal_entries BEGIN
                        INSERT INTO journal_entries_fts(journal_entries_fts, rowid, entry_content, tags)
                        VALUES('delete', old.id, old.entry_content, old.tags);
                        INSERT INTO journal_entries_fts(rowid, entry_content, tags)
                        VALUES (new.id, new.entry_content, new.tags);
                    END
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
                
                # Basic indexes that should always exist
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_journal_location 
                    ON journal_entries(location)
                """)
                
                # Note: Additional indexes for new columns will be created in migration
                
                conn.commit()
                self.logger.info("Database initialized successfully")
                
        except sqlite3.Error as e:
            self.logger.error(f"Database initialization failed: {e}")
            raise
    
    def _migrate_database(self) -> None:
        """Migrate existing database to include new columns."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # Check if new columns exist
                cursor.execute("PRAGMA table_info(journal_entries)")
                columns = [column[1] for column in cursor.fetchall()]
                
                # Add missing columns for new schema
                if 'title' not in columns:
                    cursor.execute("ALTER TABLE journal_entries ADD COLUMN title TEXT DEFAULT ''")
                    self.logger.info("Added title column to journal_entries")
                
                if 'content' not in columns:
                    cursor.execute("ALTER TABLE journal_entries ADD COLUMN content TEXT DEFAULT ''")
                    self.logger.info("Added content column to journal_entries")
                
                if 'mood_score' not in columns:
                    cursor.execute("ALTER TABLE journal_entries ADD COLUMN mood_score INTEGER DEFAULT 5")
                    self.logger.info("Added mood_score column to journal_entries")
                
                if 'mood_tags' not in columns:
                    cursor.execute("ALTER TABLE journal_entries ADD COLUMN mood_tags TEXT")
                    self.logger.info("Added mood_tags column to journal_entries")
                
                if 'temperature' not in columns:
                    cursor.execute("ALTER TABLE journal_entries ADD COLUMN temperature REAL")
                    self.logger.info("Added temperature column to journal_entries")
                
                if 'weather_condition' not in columns:
                    cursor.execute("ALTER TABLE journal_entries ADD COLUMN weather_condition TEXT")
                    self.logger.info("Added weather_condition column to journal_entries")
                
                if 'date' not in columns:
                    cursor.execute("ALTER TABLE journal_entries ADD COLUMN date TEXT")
                    self.logger.info("Added date column to journal_entries")
                
                # Legacy columns for backward compatibility
                if 'category' not in columns:
                    cursor.execute("ALTER TABLE journal_entries ADD COLUMN category TEXT")
                    self.logger.info("Added category column to journal_entries")
                
                if 'photos' not in columns:
                    cursor.execute("ALTER TABLE journal_entries ADD COLUMN photos TEXT")
                    self.logger.info("Added photos column to journal_entries")
                
                if 'template_used' not in columns:
                    cursor.execute("ALTER TABLE journal_entries ADD COLUMN template_used TEXT")
                    self.logger.info("Added template_used column to journal_entries")
                
                if 'created_at' not in columns:
                    cursor.execute("ALTER TABLE journal_entries ADD COLUMN created_at TEXT")
                    self.logger.info("Added created_at column to journal_entries")
                
                if 'updated_at' not in columns:
                    cursor.execute("ALTER TABLE journal_entries ADD COLUMN updated_at TEXT")
                    self.logger.info("Added updated_at column to journal_entries")
                
                # Migrate data from legacy columns to new schema
                cursor.execute("""
                    UPDATE journal_entries 
                    SET date = COALESCE(date, date_created),
                        content = COALESCE(content, entry_content, ''),
                        mood_score = COALESCE(mood_score, mood_rating, 5),
                        title = COALESCE(title, 'Journal Entry')
                    WHERE date IS NULL OR content IS NULL OR mood_score IS NULL OR title IS NULL
                """)
                self.logger.info("Migrated legacy data to new schema")
                
                # Create indexes for new columns
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_journal_category 
                    ON journal_entries(category)
                """)
                
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_journal_created_at 
                    ON journal_entries(created_at)
                """)
                
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_journal_updated_at 
                    ON journal_entries(updated_at)
                """)
                
                conn.commit()
                self.logger.info("Database migration completed successfully")
                
        except sqlite3.Error as e:
            self.logger.error(f"Database migration failed: {e}")
            # Don't raise here - let the app continue with existing schema
    
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
                          category: Optional[str] = None, photos: Optional[List[str]] = None,
                          template_used: Optional[str] = None, auto_populate_weather: bool = True) -> JournalEntry:
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
                location=location,
                category=category,
                photos=photos or [],
                template_used=template_used
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
                        (date_created, weather_data, mood_rating, entry_content, tags, location, category, photos, template_used)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        entry_dict['date_created'],
                        entry_dict['weather_data'],
                        entry_dict['mood_rating'],
                        entry_dict['entry_content'],
                        entry_dict['tags'],
                        entry_dict['location'],
                        entry_dict['category'],
                        entry_dict['photos'],
                        entry_dict['template_used']
                    ))
                    
                    entry_id = cursor.lastrowid
                else:
                    # Update existing entry
                    cursor.execute("""
                        UPDATE journal_entries 
                        SET date_created=?, weather_data=?, mood_rating=?, 
                            entry_content=?, tags=?, location=?, category=?, photos=?, template_used=?, updated_at=CURRENT_TIMESTAMP
                        WHERE id=?
                    """, (
                        entry_dict['date_created'],
                        entry_dict['weather_data'],
                        entry_dict['mood_rating'],
                        entry_dict['entry_content'],
                        entry_dict['tags'],
                        entry_dict['location'],
                        entry_dict['category'],
                        entry_dict['photos'],
                        entry_dict['template_used'],
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
    
    async def get_entries_by_date_range(self, start_date: datetime, end_date: datetime, 
                                       limit: int = 1000) -> List[JournalEntry]:
        """Async method to get journal entries within a date range.
        
        Args:
            start_date: Start date for filtering
            end_date: End date for filtering
            limit: Maximum number of entries to return
            
        Returns:
            List of journal entries within the date range
        """
        import asyncio
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, 
            lambda: self.get_entries(limit=limit, start_date=start_date, end_date=end_date)
        )
    
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
    
    def search_entries(self, query: str = "", mood_range: Optional[Tuple[int, int]] = None,
                      date_range: Optional[Tuple[datetime, datetime]] = None,
                      weather_conditions: Optional[List[str]] = None,
                      categories: Optional[List[str]] = None,
                      tags: Optional[List[str]] = None,
                      limit: int = 50, offset: int = 0) -> List[JournalEntry]:
        """Advanced search for journal entries using FTS and filters.
        
        Args:
            query: Full-text search query
            mood_range: Tuple of (min_mood, max_mood)
            date_range: Tuple of (start_date, end_date)
            weather_conditions: List of weather conditions to filter by
            categories: List of categories to filter by
            tags: List of tags to filter by
            limit: Maximum number of results
            offset: Number of results to skip
            
        Returns:
            List of matching journal entries
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # Build the query
                if query.strip():
                    # Use FTS for text search
                    base_query = """
                        SELECT j.* FROM journal_entries j
                        JOIN journal_entries_fts fts ON j.id = fts.rowid
                        WHERE journal_entries_fts MATCH ?
                    """
                    params = [query]
                else:
                    # No text search, just filtering
                    base_query = "SELECT * FROM journal_entries WHERE 1=1"
                    params = []
                
                # Add filters
                if mood_range:
                    base_query += " AND mood_rating BETWEEN ? AND ?"
                    params.extend(mood_range)
                
                if date_range:
                    base_query += " AND date_created BETWEEN ? AND ?"
                    params.extend([d.isoformat() for d in date_range])
                
                if weather_conditions:
                    weather_filter = " AND (" + " OR ".join(["weather_data LIKE ?" for _ in weather_conditions]) + ")"
                    base_query += weather_filter
                    params.extend([f"%{condition}%" for condition in weather_conditions])
                
                if categories:
                    category_filter = " AND category IN (" + ",".join(["?" for _ in categories]) + ")"
                    base_query += category_filter
                    params.extend(categories)
                
                if tags:
                    tag_filter = " AND (" + " OR ".join(["tags LIKE ?" for _ in tags]) + ")"
                    base_query += tag_filter
                    params.extend([f"%{tag}%" for tag in tags])
                
                # Add ordering and pagination
                base_query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
                params.extend([limit, offset])
                
                cursor.execute(base_query, params)
                rows = cursor.fetchall()
                
                return [JournalEntry.from_dict(dict(row)) for row in rows]
                
        except sqlite3.Error as e:
            self.logger.error(f"Failed to search entries: {e}")
            return []
    
    def get_mood_weather_correlation(self, days: int = 30) -> Dict[str, Any]:
        """Analyze correlation between mood and weather conditions.
        
        Args:
            days: Number of days to analyze
            
        Returns:
            Dictionary with correlation analysis
        """
        try:
            start_date = datetime.now() - timedelta(days=days)
            
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT mood_rating, weather_data 
                    FROM journal_entries 
                    WHERE date_created >= ? AND mood_rating IS NOT NULL AND weather_data IS NOT NULL
                """, (start_date.isoformat(),))
                
                rows = cursor.fetchall()
                
                if not rows:
                    return {'error': 'No data available for correlation analysis'}
                
                # Analyze mood by weather condition
                weather_mood_data = {}
                temperature_mood_data = []
                
                for row in rows:
                    mood = row[0]
                    try:
                        weather_data = json.loads(row[1]) if isinstance(row[1], str) else row[1]
                        condition = weather_data.get('condition', 'Unknown')
                        temperature = weather_data.get('temperature')
                        
                        # Group by weather condition
                        if condition not in weather_mood_data:
                            weather_mood_data[condition] = []
                        weather_mood_data[condition].append(mood)
                        
                        # Collect temperature-mood pairs
                        if temperature is not None:
                            temperature_mood_data.append((temperature, mood))
                            
                    except (json.JSONDecodeError, TypeError):
                        continue
                
                # Calculate averages by weather condition
                condition_averages = {}
                for condition, moods in weather_mood_data.items():
                    if moods:  # Check if moods list is not empty
                        condition_averages[condition] = {
                            'average_mood': round(sum(moods) / len(moods), 2),
                            'count': len(moods),
                            'min_mood': min(moods),
                            'max_mood': max(moods)
                        }
                    else:
                        condition_averages[condition] = {
                            'average_mood': 0,
                            'count': 0,
                            'min_mood': 0,
                            'max_mood': 0
                        }
                
                # Simple temperature correlation
                temp_correlation = None
                if len(temperature_mood_data) > 1:
                    temps, moods = zip(*temperature_mood_data)
                    # Simple correlation coefficient calculation
                    n = len(temps)
                    sum_temp = sum(temps)
                    sum_mood = sum(moods)
                    sum_temp_mood = sum(t * m for t, m in zip(temps, moods))
                    sum_temp_sq = sum(t * t for t in temps)
                    sum_mood_sq = sum(m * m for m in moods)
                    
                    numerator = n * sum_temp_mood - sum_temp * sum_mood
                    denominator = ((n * sum_temp_sq - sum_temp * sum_temp) * 
                                 (n * sum_mood_sq - sum_mood * sum_mood)) ** 0.5
                    
                    if denominator != 0:
                        temp_correlation = round(numerator / denominator, 3)
                
                return {
                    'weather_condition_moods': condition_averages,
                    'temperature_mood_correlation': temp_correlation,
                    'analysis_period_days': days,
                    'total_entries_analyzed': len(rows)
                }
                
        except sqlite3.Error as e:
            self.logger.error(f"Failed to analyze mood-weather correlation: {e}")
            return {'error': str(e)}
    
    async def add_photos_to_entry(self, entry_id: int, photo_paths: List[str]) -> bool:
        """Add photos to an existing journal entry.
        
        Args:
            entry_id: ID of the journal entry
            photo_paths: List of photo file paths to add
            
        Returns:
            True if successful, False otherwise
        """
        try:
            entry = self.get_entry(entry_id)
            if not entry:
                self.logger.error(f"Entry {entry_id} not found")
                return False
            
            # Process and add photos
            processed_photos = []
            for photo_path in photo_paths:
                try:
                    processed_path = await self.photo_manager.add_photo(photo_path, entry_id)
                    if processed_path:
                        processed_photos.append(processed_path)
                except Exception as e:
                    self.logger.warning(f"Failed to process photo {photo_path}: {e}")
            
            if processed_photos:
                # Add to existing photos
                entry.add_photo(processed_photos[0])  # Use the method from JournalEntry
                for photo in processed_photos[1:]:
                    entry.add_photo(photo)
                
                # Update entry in database
                return self.update_entry(entry)
            
            return False
            
        except Exception as e:
            self.logger.error(f"Failed to add photos to entry {entry_id}: {e}")
            return False
    
    async def remove_photo_from_entry(self, entry_id: int, photo_path: str) -> bool:
        """Remove a photo from a journal entry.
        
        Args:
            entry_id: ID of the journal entry
            photo_path: Path of the photo to remove
            
        Returns:
            True if successful, False otherwise
        """
        try:
            entry = self.get_entry(entry_id)
            if not entry:
                return False
            
            # Remove photo from entry
            entry.remove_photo(photo_path)
            
            # Remove physical file
            await self.photo_manager.remove_photo(photo_path)
            
            # Update entry in database
            return self.update_entry(entry)
            
        except Exception as e:
            self.logger.error(f"Failed to remove photo from entry {entry_id}: {e}")
            return False
    
    def get_entry_suggestions(self, partial_query: str, limit: int = 5) -> Dict[str, List[str]]:
        """Get autocomplete suggestions for search.
        
        Args:
            partial_query: Partial search query
            limit: Maximum number of suggestions per category
            
        Returns:
            Dictionary with suggestion categories
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                suggestions = {
                    'tags': [],
                    'categories': [],
                    'locations': []
                }
                
                # Get tag suggestions
                cursor.execute("""
                    SELECT DISTINCT tags FROM journal_entries 
                    WHERE tags LIKE ? AND tags IS NOT NULL
                    LIMIT ?
                """, (f"%{partial_query}%", limit))
                
                for row in cursor.fetchall():
                    try:
                        tags = json.loads(row[0]) if isinstance(row[0], str) else row[0]
                        if isinstance(tags, list):
                            for tag in tags:
                                if partial_query.lower() in tag.lower() and tag not in suggestions['tags']:
                                    suggestions['tags'].append(tag)
                                    if len(suggestions['tags']) >= limit:
                                        break
                    except (json.JSONDecodeError, TypeError):
                        continue
                
                # Get category suggestions
                cursor.execute("""
                    SELECT DISTINCT category FROM journal_entries 
                    WHERE category LIKE ? AND category IS NOT NULL
                    LIMIT ?
                """, (f"%{partial_query}%", limit))
                
                suggestions['categories'] = [row[0] for row in cursor.fetchall()]
                
                # Get location suggestions
                cursor.execute("""
                    SELECT DISTINCT location FROM journal_entries 
                    WHERE location LIKE ? AND location IS NOT NULL
                    LIMIT ?
                """, (f"%{partial_query}%", limit))
                
                suggestions['locations'] = [row[0] for row in cursor.fetchall()]
                
                return suggestions
                
        except sqlite3.Error as e:
            self.logger.error(f"Failed to get suggestions: {e}")
            return {'tags': [], 'categories': [], 'locations': []}
    
    def export_entries(self, format_type: str = 'json', entries: Optional[List[JournalEntry]] = None,
                      include_photos: bool = False) -> str:
        """Export journal entries to various formats.
        
        Args:
            format_type: Export format ('json', 'html', 'txt')
            entries: Specific entries to export (None for all)
            include_photos: Whether to include photo data
            
        Returns:
            Exported data as string
        """
        try:
            if entries is None:
                entries = self.get_entries(limit=10000)  # Get all entries
            
            if format_type.lower() == 'json':
                export_data = []
                for entry in entries:
                    entry_dict = entry.to_dict()
                    if include_photos and entry.photos:
                        # Add photo metadata
                        entry_dict['photo_metadata'] = []
                        for photo_path in entry.photos:
                            photo_info = self.photo_manager.get_photo_info(photo_path)
                            if photo_info:
                                entry_dict['photo_metadata'].append(photo_info)
                    export_data.append(entry_dict)
                
                return json.dumps(export_data, indent=2, default=str)
            
            elif format_type.lower() == 'html':
                html_content = """
                <!DOCTYPE html>
                <html>
                <head>
                    <title>Weather Journal Export</title>
                    <style>
                        body { font-family: Arial, sans-serif; margin: 20px; }
                        .entry { border: 1px solid #ddd; margin: 20px 0; padding: 15px; border-radius: 5px; }
                        .entry-header { font-weight: bold; color: #333; }
                        .mood { color: #666; }
                        .tags { color: #888; font-style: italic; }
                        .weather { background: #f5f5f5; padding: 10px; margin: 10px 0; border-radius: 3px; }
                    </style>
                </head>
                <body>
                    <h1>Weather Journal Export</h1>
                """
                
                for entry in entries:
                    html_content += f"""
                    <div class="entry">
                        <div class="entry-header">{entry.date_created.strftime('%Y-%m-%d %H:%M')}</div>
                        <div class="mood">Mood: {entry.get_mood_description()}</div>
                        {f'<div class="category">Category: {entry.category}</div>' if entry.category else ''}
                        <div class="content">{entry.entry_content}</div>
                        {f'<div class="tags">Tags: {', '.join(entry.tags)}</div>' if entry.tags else ''}
                        {f'<div class="location">Location: {entry.location}</div>' if entry.location else ''}
                    """
                    
                    if entry.weather_data:
                        weather = entry.weather_data
                        html_content += f"""
                        <div class="weather">
                            <strong>Weather:</strong> {weather.get('condition', 'N/A')}, 
                            {weather.get('temperature', 'N/A')}°, 
                            Humidity: {weather.get('humidity', 'N/A')}%
                        </div>
                        """
                    
                    html_content += "</div>"
                
                html_content += """
                </body>
                </html>
                """
                
                return html_content
            
            elif format_type.lower() == 'txt':
                txt_content = "WEATHER JOURNAL EXPORT\n" + "=" * 50 + "\n\n"
                
                for entry in entries:
                    txt_content += f"Date: {entry.date_created.strftime('%Y-%m-%d %H:%M')}\n"
                    txt_content += f"Mood: {entry.get_mood_description()}\n"
                    if entry.category:
                        txt_content += f"Category: {entry.category}\n"
                    if entry.location:
                        txt_content += f"Location: {entry.location}\n"
                    if entry.tags:
                        txt_content += f"Tags: {', '.join(entry.tags)}\n"
                    
                    if entry.weather_data:
                        weather = entry.weather_data
                        txt_content += f"Weather: {weather.get('condition', 'N/A')}, {weather.get('temperature', 'N/A')}°\n"
                    
                    txt_content += f"\nContent:\n{entry.entry_content}\n"
                    txt_content += "-" * 50 + "\n\n"
                
                return txt_content
            
            else:
                raise ValueError(f"Unsupported export format: {format_type}")
                
        except Exception as e:
            self.logger.error(f"Failed to export entries: {e}")
            return f"Export failed: {str(e)}"