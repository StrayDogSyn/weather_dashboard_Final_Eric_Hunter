import json
from pathlib import Path
from typing import List, Dict, Any, Optional, Set, Callable
import sqlite3
import time
import threading

class SearchStateService:
    def __init__(self, db_path: str = "data/search_state.db"):
        self.db_path = db_path
        self.current_search = ""
        self.selected_cities = []
        self.search_mode = "single"  # single, multi, command
        self.observers = []
        self._db_lock = threading.Lock()
        
        self.init_database()
        self.load_state()
    
    def _execute_with_retry(self, operation, max_retries=3, delay=0.1):
        """Execute database operation with retry logic for locked database"""
        for attempt in range(max_retries):
            try:
                with self._db_lock:
                    with sqlite3.connect(self.db_path, timeout=10.0) as conn:
                        conn.execute('PRAGMA journal_mode=WAL')
                        return operation(conn)
            except sqlite3.OperationalError as e:
                if "database is locked" in str(e) and attempt < max_retries - 1:
                    time.sleep(delay * (2 ** attempt))  # Exponential backoff
                    continue
                else:
                    raise
            except Exception as e:
                if attempt < max_retries - 1:
                    time.sleep(delay)
                    continue
                else:
                    raise
        
    def init_database(self):
        """Initialize search state database"""
        Path(self.db_path).parent.mkdir(exist_ok=True)
        
        def _init_tables(conn):
            conn.execute('''
                CREATE TABLE IF NOT EXISTS search_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    query TEXT NOT NULL,
                    search_type TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    result_count INTEGER,
                    feature_used TEXT
                )
            ''')
            
            conn.execute('''
                CREATE TABLE IF NOT EXISTS favorites (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    city_name TEXT UNIQUE NOT NULL,
                    added_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                    use_count INTEGER DEFAULT 0,
                    last_used DATETIME
                )
            ''')
            
            conn.execute('''
                CREATE TABLE IF NOT EXISTS search_analytics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    pattern TEXT,
                    frequency INTEGER DEFAULT 1,
                    last_seen DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.execute('''
                CREATE TABLE IF NOT EXISTS search_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_start DATETIME DEFAULT CURRENT_TIMESTAMP,
                    session_end DATETIME,
                    total_searches INTEGER DEFAULT 0,
                    unique_cities INTEGER DEFAULT 0
                )
            ''')
        
        self._execute_with_retry(_init_tables)
    
    def update_search(self, query: str, cities: List[str], mode: str = "single"):
        """Update current search state and notify observers"""
        self.current_search = query
        self.selected_cities = cities
        self.search_mode = mode
        
        # Record in history
        self.add_to_history(query, mode, len(cities))
        
        # Notify all observers
        for observer in self.observers:
            observer({
                'query': query,
                'cities': cities,
                'mode': mode,
                'timestamp': datetime.now()
            })
    
    def add_observer(self, callback: Callable):
        """Register a feature to observe search state changes"""
        self.observers.append(callback)
    
    def remove_observer(self, callback: Callable):
        """Remove an observer"""
        if callback in self.observers:
            self.observers.remove(callback)
    
    def get_smart_suggestions(self, partial_query: str) -> List[Dict[str, Any]]:
        """Get intelligent suggestions based on user patterns"""
        suggestions = []
        
        def _get_suggestions(conn):
            # Get frequently searched cities
            cursor = conn.execute('''
                SELECT query, COUNT(*) as freq, MAX(timestamp) as last_used
                FROM search_history
                WHERE query LIKE ? AND search_type = 'city'
                GROUP BY query
                ORDER BY freq DESC, last_used DESC
                LIMIT 5
            ''', (f'%{partial_query}%',))
            
            for row in cursor:
                suggestions.append({
                    'text': row[0],
                    'type': 'frequent',
                    'score': row[1],
                    'icon': '🔥' if row[1] > 5 else '📍'
                })
            
            # Get favorites matching query
            cursor = conn.execute('''
                SELECT city_name, use_count
                FROM favorites
                WHERE city_name LIKE ?
                ORDER BY use_count DESC
                LIMIT 5
            ''', (f'%{partial_query}%',))
            
            for row in cursor:
                suggestions.append({
                    'text': row[0],
                    'type': 'favorite',
                    'score': row[1] + 100,  # Favorites get priority
                    'icon': '★'
                })
            
            return suggestions
        
        try:
            suggestions = self._execute_with_retry(_get_suggestions)
            
            # Get pattern-based suggestions (separate to avoid nested database calls)
            patterns = self.analyze_search_patterns()
            for pattern in patterns:
                if partial_query.lower() in pattern.lower():
                    suggestions.append({
                        'text': pattern,
                        'type': 'pattern',
                        'score': 50,
                        'icon': '🎯'
                    })
        except Exception:
            suggestions = []  # Return empty list if database operation fails
        
        # Sort by score and remove duplicates
        seen = set()
        unique_suggestions = []
        for s in sorted(suggestions, key=lambda x: x['score'], reverse=True):
            if s['text'] not in seen:
                seen.add(s['text'])
                unique_suggestions.append(s)
        
        return unique_suggestions[:10]
    
    def analyze_search_patterns(self) -> List[str]:
        """Analyze user search patterns for predictions"""
        def _analyze_patterns(conn):
            # Find common multi-city searches
            cursor = conn.execute('''
                SELECT query, COUNT(*) as freq
                FROM search_history
                WHERE search_type = 'command' AND query LIKE '%compare:%'
                GROUP BY query
                ORDER BY freq DESC
                LIMIT 5
            ''')
            
            patterns = []
            for row in cursor:
                patterns.append(row[0])
            
            # Find time-based patterns (e.g., user often searches Tokyo in morning)
            hour = datetime.now().hour
            cursor = conn.execute('''
                SELECT query, COUNT(*) as freq
                FROM search_history
                WHERE strftime('%H', timestamp) = ?
                GROUP BY query
                ORDER BY freq DESC
                LIMIT 3
            ''', (f'{hour:02d}',))
            
            for row in cursor:
                if row[1] > 2:  # Only suggest if searched multiple times at this hour
                    patterns.append(f"Time-based: {row[0]}")
            
            return patterns
        
        try:
            return self._execute_with_retry(_analyze_patterns)
        except Exception:
            return []  # Return empty list if database operation fails
    
    def add_to_history(self, query: str, search_type: str, result_count: int = 0, feature_used: str = None):
        """Add search to history with analytics"""
        def _add_history(conn):
            conn.execute('''
                INSERT INTO search_history (query, search_type, result_count, feature_used)
                VALUES (?, ?, ?, ?)
            ''', (query, search_type, result_count, feature_used))
        
        try:
            self._execute_with_retry(_add_history)
            # Update analytics patterns (separate call to avoid nested transactions)
            self.update_search_analytics(query)
        except Exception:
            pass  # Fail silently if history addition fails
    
    def update_search_analytics(self, query: str):
        """Update search pattern analytics"""
        def _update_analytics(conn):
            # Check if pattern exists
            cursor = conn.execute(
                'SELECT frequency FROM search_analytics WHERE pattern = ?',
                (query,)
            )
            result = cursor.fetchone()
            
            if result:
                # Update existing pattern
                conn.execute('''
                    UPDATE search_analytics 
                    SET frequency = frequency + 1, last_seen = CURRENT_TIMESTAMP
                    WHERE pattern = ?
                ''', (query,))
            else:
                # Insert new pattern
                conn.execute('''
                    INSERT INTO search_analytics (pattern, frequency)
                    VALUES (?, 1)
                ''', (query,))
        
        try:
            self._execute_with_retry(_update_analytics)
        except Exception:
            pass  # Fail silently if analytics update fails
    
    def add_to_favorites(self, city_name: str):
        """Add city to favorites or update usage count"""
        def _add_favorite(conn):
            cursor = conn.execute(
                'SELECT use_count FROM favorites WHERE city_name = ?',
                (city_name,)
            )
            result = cursor.fetchone()
            
            if result:
                # Update existing favorite
                conn.execute('''
                    UPDATE favorites 
                    SET use_count = use_count + 1, last_used = CURRENT_TIMESTAMP
                    WHERE city_name = ?
                ''', (city_name,))
            else:
                # Add new favorite
                conn.execute('''
                    INSERT INTO favorites (city_name, use_count, last_used)
                    VALUES (?, 1, CURRENT_TIMESTAMP)
                ''', (city_name,))
        
        try:
            self._execute_with_retry(_add_favorite)
        except Exception:
            pass  # Fail silently if favorites update fails
    
    def remove_from_favorites(self, city_name: str):
        """Remove city from favorites"""
        def _remove_favorite(conn):
            conn.execute('DELETE FROM favorites WHERE city_name = ?', (city_name,))
        
        try:
            self._execute_with_retry(_remove_favorite)
        except Exception:
            pass  # Fail silently if favorites removal fails
    
    def get_favorites(self) -> List[Dict[str, Any]]:
        """Get all favorite cities with usage stats"""
        def _get_favorites(conn):
            cursor = conn.execute('''
                SELECT city_name, use_count, added_date, last_used
                FROM favorites
                ORDER BY use_count DESC, last_used DESC
            ''')
            
            favorites = []
            for row in cursor:
                favorites.append({
                    'name': row[0],
                    'use_count': row[1],
                    'added_date': row[2],
                    'last_used': row[3]
                })
            
            return favorites
        
        try:
            return self._execute_with_retry(_get_favorites)
        except Exception:
            return []  # Return empty list if database operation fails
    
    def get_search_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent search history"""
        def _get_history(conn):
            cursor = conn.execute('''
                SELECT query, search_type, timestamp, result_count, feature_used
                FROM search_history
                ORDER BY timestamp DESC
                LIMIT ?
            ''', (limit,))
            
            history = []
            for row in cursor:
                history.append({
                    'query': row[0],
                    'search_type': row[1],
                    'timestamp': row[2],
                    'result_count': row[3],
                    'feature_used': row[4]
                })
            
            return history
        
        try:
            return self._execute_with_retry(_get_history)
        except Exception:
            return []  # Return empty list if database operation fails
    
    def get_usage_statistics(self) -> Dict[str, Any]:
        """Get comprehensive usage statistics"""
        def _get_stats(conn):
            stats = {}
            
            # Total searches
            cursor = conn.execute('SELECT COUNT(*) FROM search_history')
            stats['total_searches'] = cursor.fetchone()[0]
            
            # Unique cities searched
            cursor = conn.execute(
                'SELECT COUNT(DISTINCT query) FROM search_history WHERE search_type = "city"'
            )
            stats['unique_cities'] = cursor.fetchone()[0]
            
            # Most popular search type
            cursor = conn.execute('''
                SELECT search_type, COUNT(*) as count
                FROM search_history
                GROUP BY search_type
                ORDER BY count DESC
                LIMIT 1
            ''')
            result = cursor.fetchone()
            stats['most_popular_type'] = result[0] if result else 'none'
            
            # Average searches per day (last 30 days)
            cursor = conn.execute('''
                SELECT COUNT(*) / 30.0 as avg_per_day
                FROM search_history
                WHERE timestamp >= datetime('now', '-30 days')
            ''')
            stats['avg_searches_per_day'] = round(cursor.fetchone()[0], 2)
            
            # Top 5 most searched cities
            cursor = conn.execute('''
                SELECT query, COUNT(*) as count
                FROM search_history
                WHERE search_type = 'city'
                GROUP BY query
                ORDER BY count DESC
                LIMIT 5
            ''')
            stats['top_cities'] = [{'city': row[0], 'count': row[1]} for row in cursor]
            
            return stats
        
        try:
            return self._execute_with_retry(_get_stats)
        except Exception:
            return {  # Return default stats if database operation fails
                'total_searches': 0,
                'unique_cities': 0,
                'most_popular_type': 'none',
                'avg_searches_per_day': 0.0,
                'top_cities': []
            }
    
    def clear_history(self, older_than_days: int = None):
        """Clear search history, optionally only older entries"""
        def _clear_history(conn):
            if older_than_days:
                conn.execute('''
                    DELETE FROM search_history
                    WHERE timestamp < datetime('now', '-{} days')
                '''.format(older_than_days))
            else:
                conn.execute('DELETE FROM search_history')
        
        try:
            self._execute_with_retry(_clear_history)
        except Exception:
            pass  # Fail silently if history clearing fails
    
    def export_data(self) -> Dict[str, Any]:
        """Export all search data for backup"""
        def _export_data(conn):
            data = {
                'search_history': [],
                'favorites': [],
                'analytics': [],
                'export_timestamp': datetime.now().isoformat()
            }
            
            # Export search history
            cursor = conn.execute('SELECT * FROM search_history')
            columns = [description[0] for description in cursor.description]
            for row in cursor:
                data['search_history'].append(dict(zip(columns, row)))
            
            # Export favorites
            cursor = conn.execute('SELECT * FROM favorites')
            columns = [description[0] for description in cursor.description]
            for row in cursor:
                data['favorites'].append(dict(zip(columns, row)))
            
            # Export analytics
            cursor = conn.execute('SELECT * FROM search_analytics')
            columns = [description[0] for description in cursor.description]
            for row in cursor:
                data['analytics'].append(dict(zip(columns, row)))
            
            return data
        
        try:
            return self._execute_with_retry(_export_data)
        except Exception:
            return {  # Return empty data if export fails
                'search_history': [],
                'favorites': [],
                'analytics': [],
                'export_timestamp': datetime.now().isoformat()
            }
    
    def import_data(self, data: Dict[str, Any]):
        """Import search data from backup"""
        def _import_data(conn):
            # Clear existing data
            conn.execute('DELETE FROM search_history')
            conn.execute('DELETE FROM favorites')
            conn.execute('DELETE FROM search_analytics')
            
            # Import search history
            for item in data.get('search_history', []):
                conn.execute('''
                    INSERT INTO search_history (query, search_type, timestamp, result_count, feature_used)
                    VALUES (?, ?, ?, ?, ?)
                ''', (item.get('query'), item.get('search_type'), item.get('timestamp'),
                     item.get('result_count'), item.get('feature_used')))
            
            # Import favorites
            for item in data.get('favorites', []):
                conn.execute('''
                    INSERT INTO favorites (city_name, added_date, use_count, last_used)
                    VALUES (?, ?, ?, ?)
                ''', (item.get('city_name'), item.get('added_date'),
                     item.get('use_count'), item.get('last_used')))
            
            # Import analytics
            for item in data.get('analytics', []):
                conn.execute('''
                    INSERT INTO search_analytics (pattern, frequency, last_seen)
                    VALUES (?, ?, ?)
                ''', (item.get('pattern'), item.get('frequency'), item.get('last_seen')))
        
        try:
            self._execute_with_retry(_import_data)
        except Exception:
            pass  # Fail silently if import fails
    
    def load_state(self):
        """Load persistent search state"""
        state_file = Path("data/search_state.json")
        if state_file.exists():
            try:
                with open(state_file, 'r') as f:
                    state = json.load(f)
                    self.current_search = state.get('current_search', '')
                    self.selected_cities = state.get('selected_cities', [])
                    self.search_mode = state.get('search_mode', 'single')
            except Exception:
                pass  # Use defaults if loading fails
    
    def save_state(self):
        """Save current search state"""
        state_file = Path("data/search_state.json")
        state_file.parent.mkdir(exist_ok=True)
        
        state = {
            'current_search': self.current_search,
            'selected_cities': self.selected_cities,
            'search_mode': self.search_mode,
            'last_updated': datetime.now().isoformat()
        }
        
        try:
            with open(state_file, 'w') as f:
                json.dump(state, f, indent=2)
        except Exception:
            pass  # Fail silently if save fails
    
    def __del__(self):
        """Save state when service is destroyed"""
        self.save_state()