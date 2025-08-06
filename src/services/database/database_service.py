"""Simple database service for journal entries."""

import json
import sqlite3
import os
from datetime import datetime
from typing import List, Dict, Optional
from pathlib import Path


class DatabaseService:
    """Simple database service for journal entries."""
    
    def __init__(self, db_path: Optional[str] = None):
        """Initialize database service."""
        if db_path is None:
            # Create data directory if it doesn't exist
            data_dir = Path("data")
            data_dir.mkdir(exist_ok=True)
            db_path = data_dir / "journal.db"
        
        self.db_path = str(db_path)
        self.init_database()
    
    def init_database(self):
        """Initialize the database with required tables."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Create journal entries table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS journal_entries (
                        id TEXT PRIMARY KEY,
                        title TEXT NOT NULL,
                        content TEXT NOT NULL,
                        mood TEXT,
                        timestamp TEXT NOT NULL,
                        weather_data TEXT,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                        updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                conn.commit()
        except Exception as e:
            print(f"Error initializing database: {e}")
    
    def save_journal_entry(self, entry: Dict) -> bool:
        """Save a journal entry to the database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Convert weather data to JSON string
                weather_json = json.dumps(entry.get('weather', {})) if entry.get('weather') else None
                
                cursor.execute("""
                    INSERT INTO journal_entries 
                    (id, title, content, mood, timestamp, weather_data)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    entry['id'],
                    entry['title'],
                    entry['content'],
                    entry['mood'],
                    entry['timestamp'],
                    weather_json
                ))
                
                conn.commit()
                return True
                
        except Exception as e:
            print(f"Error saving journal entry: {e}")
            return False
    
    def get_journal_entries(self) -> List[Dict]:
        """Get all journal entries from the database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT id, title, content, mood, timestamp, weather_data, created_at, updated_at
                    FROM journal_entries
                    ORDER BY timestamp DESC
                """)
                
                entries = []
                for row in cursor.fetchall():
                    weather_data = {}
                    if row[5]:  # weather_data column
                        try:
                            weather_data = json.loads(row[5])
                        except json.JSONDecodeError:
                            weather_data = {}
                    
                    entry = {
                        'id': row[0],
                        'title': row[1],
                        'content': row[2],
                        'mood': row[3],
                        'timestamp': row[4],
                        'weather': weather_data,
                        'created_at': row[6],
                        'updated_at': row[7]
                    }
                    entries.append(entry)
                
                return entries
                
        except Exception as e:
            print(f"Error getting journal entries: {e}")
            return []
    
    def update_journal_entry(self, entry: Dict) -> bool:
        """Update an existing journal entry."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Convert weather data to JSON string
                weather_json = json.dumps(entry.get('weather', {})) if entry.get('weather') else None
                
                cursor.execute("""
                    UPDATE journal_entries 
                    SET title = ?, content = ?, mood = ?, timestamp = ?, weather_data = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (
                    entry['title'],
                    entry['content'],
                    entry['mood'],
                    entry['timestamp'],
                    weather_json,
                    entry['id']
                ))
                
                conn.commit()
                return cursor.rowcount > 0
                
        except Exception as e:
            print(f"Error updating journal entry: {e}")
            return False
    
    def delete_journal_entry(self, entry_id: str) -> bool:
        """Delete a journal entry from the database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    DELETE FROM journal_entries WHERE id = ?
                """, (entry_id,))
                
                conn.commit()
                return cursor.rowcount > 0
                
        except Exception as e:
            print(f"Error deleting journal entry: {e}")
            return False
    
    def get_journal_entry_by_id(self, entry_id: str) -> Optional[Dict]:
        """Get a specific journal entry by ID."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT id, title, content, mood, timestamp, weather_data, created_at, updated_at
                    FROM journal_entries
                    WHERE id = ?
                """, (entry_id,))
                
                row = cursor.fetchone()
                if row:
                    weather_data = {}
                    if row[5]:  # weather_data column
                        try:
                            weather_data = json.loads(row[5])
                        except json.JSONDecodeError:
                            weather_data = {}
                    
                    return {
                        'id': row[0],
                        'title': row[1],
                        'content': row[2],
                        'mood': row[3],
                        'timestamp': row[4],
                        'weather': weather_data,
                        'created_at': row[6],
                        'updated_at': row[7]
                    }
                
                return None
                
        except Exception as e:
            print(f"Error getting journal entry: {e}")
            return None
    
    def search_journal_entries(self, query: str) -> List[Dict]:
        """Search journal entries by title or content."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT id, title, content, mood, timestamp, weather_data, created_at, updated_at
                    FROM journal_entries
                    WHERE title LIKE ? OR content LIKE ?
                    ORDER BY timestamp DESC
                """, (f'%{query}%', f'%{query}%'))
                
                entries = []
                for row in cursor.fetchall():
                    weather_data = {}
                    if row[5]:  # weather_data column
                        try:
                            weather_data = json.loads(row[5])
                        except json.JSONDecodeError:
                            weather_data = {}
                    
                    entry = {
                        'id': row[0],
                        'title': row[1],
                        'content': row[2],
                        'mood': row[3],
                        'timestamp': row[4],
                        'weather': weather_data,
                        'created_at': row[6],
                        'updated_at': row[7]
                    }
                    entries.append(entry)
                
                return entries
                
        except Exception as e:
            print(f"Error searching journal entries: {e}")
            return []
    
    def get_entries_by_mood(self, mood: str) -> List[Dict]:
        """Get journal entries filtered by mood."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT id, title, content, mood, timestamp, weather_data, created_at, updated_at
                    FROM journal_entries
                    WHERE mood = ?
                    ORDER BY timestamp DESC
                """, (mood,))
                
                entries = []
                for row in cursor.fetchall():
                    weather_data = {}
                    if row[5]:  # weather_data column
                        try:
                            weather_data = json.loads(row[5])
                        except json.JSONDecodeError:
                            weather_data = {}
                    
                    entry = {
                        'id': row[0],
                        'title': row[1],
                        'content': row[2],
                        'mood': row[3],
                        'timestamp': row[4],
                        'weather': weather_data,
                        'created_at': row[6],
                        'updated_at': row[7]
                    }
                    entries.append(entry)
                
                return entries
                
        except Exception as e:
            print(f"Error getting entries by mood: {e}")
            return []
    
    def get_database_stats(self) -> Dict:
        """Get database statistics."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Get total entries count
                cursor.execute("SELECT COUNT(*) FROM journal_entries")
                total_entries = cursor.fetchone()[0]
                
                # Get entries by mood
                cursor.execute("""
                    SELECT mood, COUNT(*) 
                    FROM journal_entries 
                    WHERE mood IS NOT NULL 
                    GROUP BY mood
                """)
                mood_counts = dict(cursor.fetchall())
                
                # Get recent entries count (last 30 days)
                cursor.execute("""
                    SELECT COUNT(*) 
                    FROM journal_entries 
                    WHERE datetime(timestamp) >= datetime('now', '-30 days')
                """)
                recent_entries = cursor.fetchone()[0]
                
                return {
                    'total_entries': total_entries,
                    'mood_counts': mood_counts,
                    'recent_entries': recent_entries
                }
                
        except Exception as e:
            print(f"Error getting database stats: {e}")
            return {
                'total_entries': 0,
                'mood_counts': {},
                'recent_entries': 0
            }