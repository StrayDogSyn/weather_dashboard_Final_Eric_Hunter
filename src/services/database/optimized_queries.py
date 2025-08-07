import sqlite3
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
import logging
from contextlib import contextmanager
from pathlib import Path
import threading
from queue import Queue

logger = logging.getLogger(__name__)

class OptimizedDatabase:
    """Optimized database with connection pooling and prepared statements"""
    
    def __init__(self, db_path: str = "data/weather_dashboard.db", pool_size: int = 5):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.pool_size = pool_size
        self.connection_pool = Queue(maxsize=pool_size)
        self.prepared_statements = {}
        self._lock = threading.Lock()
        
        # Initialize connection pool
        self._initialize_pool()
        
        # Create tables first, then indexes
        self.create_tables()
        self.create_indexes()
    
    def _initialize_pool(self):
        """Initialize connection pool"""
        for _ in range(self.pool_size):
            conn = self._create_connection()
            self.connection_pool.put(conn)
    
    def _create_connection(self) -> sqlite3.Connection:
        """Create optimized database connection"""
        conn = sqlite3.connect(
            str(self.db_path),
            check_same_thread=False,
            timeout=30.0
        )
        
        # Enable WAL mode for better concurrency
        conn.execute("PRAGMA journal_mode=WAL")
        
        # Optimize SQLite settings
        conn.execute("PRAGMA synchronous=NORMAL")
        conn.execute("PRAGMA cache_size=10000")
        conn.execute("PRAGMA temp_store=MEMORY")
        conn.execute("PRAGMA mmap_size=268435456")  # 256MB
        
        # Enable foreign keys
        conn.execute("PRAGMA foreign_keys=ON")
        
        conn.row_factory = sqlite3.Row
        return conn
    
    @contextmanager
    def get_connection(self):
        """Get connection from pool"""
        conn = None
        try:
            conn = self.connection_pool.get(timeout=10)
            yield conn
        except Exception as e:
            logger.error(f"Database connection error: {e}")
            if conn:
                conn.rollback()
            raise
        finally:
            if conn:
                try:
                    conn.commit()
                    self.connection_pool.put(conn)
                except Exception as e:
                    logger.error(f"Failed to return connection to pool: {e}")
                    # Create new connection if current one is broken
                    try:
                        conn.close()
                    except:
                        pass
                    new_conn = self._create_connection()
                    self.connection_pool.put(new_conn)
    
    def create_indexes(self):
        """Create performance indexes"""
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_weather_timestamp ON weather_data(timestamp)",
            "CREATE INDEX IF NOT EXISTS idx_weather_city ON weather_data(city)",
            "CREATE INDEX IF NOT EXISTS idx_weather_city_timestamp ON weather_data(city, timestamp)",
            "CREATE INDEX IF NOT EXISTS idx_journal_date ON journal_entries(date)",
            "CREATE INDEX IF NOT EXISTS idx_journal_mood ON journal_entries(mood)",
            "CREATE INDEX IF NOT EXISTS idx_journal_user_date ON journal_entries(user_id, date)",
            "CREATE INDEX IF NOT EXISTS idx_locations_name ON favorite_locations(name)",
            "CREATE INDEX IF NOT EXISTS idx_search_timestamp ON search_history(timestamp)"
        ]
        
        try:
            with self.get_connection() as conn:
                for index in indexes:
                    conn.execute(index)
                logger.info("Database indexes created successfully")
        except Exception as e:
            logger.error(f"Failed to create indexes: {e}")
    
    def create_tables(self):
        """Create optimized database tables"""
        tables = {
            'weather_data': """
                CREATE TABLE IF NOT EXISTS weather_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    city TEXT NOT NULL,
                    timestamp DATETIME NOT NULL,
                    temperature REAL,
                    condition TEXT,
                    humidity INTEGER,
                    wind_speed REAL,
                    pressure REAL,
                    visibility REAL,
                    uv_index INTEGER,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """,
            'journal_entries': """
                CREATE TABLE IF NOT EXISTS journal_entries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT,
                    date DATE NOT NULL,
                    mood INTEGER CHECK(mood >= 1 AND mood <= 5),
                    content TEXT,
                    weather_condition TEXT,
                    temperature REAL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """,
            'favorite_locations': """
                CREATE TABLE IF NOT EXISTS favorite_locations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    latitude REAL NOT NULL,
                    longitude REAL NOT NULL,
                    country TEXT,
                    added_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """,
            'search_history': """
                CREATE TABLE IF NOT EXISTS search_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    query TEXT NOT NULL,
                    result_count INTEGER,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """
        }
        
        try:
            with self.get_connection() as conn:
                for table_name, sql in tables.items():
                    conn.execute(sql)
                logger.info("Database tables created successfully")
        except Exception as e:
            logger.error(f"Failed to create tables: {e}")
    
    def get_weather_history_optimized(self, city: str, days: int = 7) -> List[Dict[str, Any]]:
        """Optimized weather history query"""
        query = """
        SELECT 
            timestamp,
            temperature,
            condition,
            humidity,
            wind_speed,
            pressure,
            uv_index
        FROM weather_data 
        WHERE city = ? 
        AND timestamp > datetime('now', '-' || ? || ' days')
        ORDER BY timestamp DESC
        LIMIT 100
        """
        
        try:
            with self.get_connection() as conn:
                cursor = conn.execute(query, (city, days))
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Failed to get weather history: {e}")
            return []
    
    def get_recent_weather_batch(self, cities: List[str], hours: int = 24) -> Dict[str, List[Dict]]:
        """Get recent weather for multiple cities in one query"""
        if not cities:
            return {}
        
        placeholders = ','.join('?' * len(cities))
        query = f"""
        SELECT 
            city,
            timestamp,
            temperature,
            condition,
            humidity,
            wind_speed
        FROM weather_data 
        WHERE city IN ({placeholders})
        AND timestamp > datetime('now', '-{hours} hours')
        ORDER BY city, timestamp DESC
        """
        
        try:
            with self.get_connection() as conn:
                cursor = conn.execute(query, cities)
                results = {}
                for row in cursor.fetchall():
                    city = row['city']
                    if city not in results:
                        results[city] = []
                    results[city].append(dict(row))
                return results
        except Exception as e:
            logger.error(f"Failed to get batch weather data: {e}")
            return {}
    
    def insert_weather_data_batch(self, weather_records: List[Dict[str, Any]]) -> bool:
        """Insert multiple weather records efficiently"""
        if not weather_records:
            return True
        
        query = """
        INSERT OR REPLACE INTO weather_data 
        (city, timestamp, temperature, condition, humidity, wind_speed, pressure, uv_index)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        try:
            with self.get_connection() as conn:
                data = [
                    (
                        record.get('city'),
                        record.get('timestamp'),
                        record.get('temperature'),
                        record.get('condition'),
                        record.get('humidity'),
                        record.get('wind_speed'),
                        record.get('pressure'),
                        record.get('uv_index')
                    )
                    for record in weather_records
                ]
                conn.executemany(query, data)
                return True
        except Exception as e:
            logger.error(f"Failed to insert weather data batch: {e}")
            return False
    
    def get_journal_entries_optimized(self, user_id: str = None, days: int = 30) -> List[Dict[str, Any]]:
        """Optimized journal entries query"""
        if user_id:
            query = """
            SELECT id, date, mood, content, weather_condition, temperature, created_at
            FROM journal_entries 
            WHERE user_id = ?
            AND date > date('now', '-' || ? || ' days')
            ORDER BY date DESC
            """
            params = (user_id, days)
        else:
            query = """
            SELECT id, date, mood, content, weather_condition, temperature, created_at
            FROM journal_entries 
            WHERE date > date('now', '-' || ? || ' days')
            ORDER BY date DESC
            """
            params = (days,)
        
        try:
            with self.get_connection() as conn:
                cursor = conn.execute(query, params)
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Failed to get journal entries: {e}")
            return []
    
    def get_weather_statistics(self, city: str, days: int = 30) -> Dict[str, Any]:
        """Get weather statistics for a city"""
        query = """
        SELECT 
            COUNT(*) as record_count,
            AVG(temperature) as avg_temp,
            MIN(temperature) as min_temp,
            MAX(temperature) as max_temp,
            AVG(humidity) as avg_humidity,
            AVG(wind_speed) as avg_wind_speed,
            condition,
            COUNT(condition) as condition_count
        FROM weather_data 
        WHERE city = ?
        AND timestamp > datetime('now', '-' || ? || ' days')
        GROUP BY condition
        ORDER BY condition_count DESC
        """
        
        try:
            with self.get_connection() as conn:
                cursor = conn.execute(query, (city, days))
                results = cursor.fetchall()
                
                if results:
                    # Get overall stats
                    overall_query = """
                    SELECT 
                        COUNT(*) as total_records,
                        AVG(temperature) as avg_temp,
                        MIN(temperature) as min_temp,
                        MAX(temperature) as max_temp,
                        AVG(humidity) as avg_humidity,
                        AVG(wind_speed) as avg_wind_speed
                    FROM weather_data 
                    WHERE city = ?
                    AND timestamp > datetime('now', '-' || ? || ' days')
                    """
                    
                    overall_cursor = conn.execute(overall_query, (city, days))
                    overall_stats = dict(overall_cursor.fetchone())
                    
                    # Add condition breakdown
                    conditions = [dict(row) for row in results]
                    overall_stats['conditions'] = conditions
                    
                    return overall_stats
                
                return {}
        except Exception as e:
            logger.error(f"Failed to get weather statistics: {e}")
            return {}
    
    def cleanup_old_data(self, days_to_keep: int = 90) -> bool:
        """Clean up old data to maintain performance"""
        queries = [
            ("DELETE FROM weather_data WHERE timestamp < datetime('now', '-' || ? || ' days')", (days_to_keep,)),
            ("DELETE FROM search_history WHERE timestamp < datetime('now', '-' || ? || ' days')", (days_to_keep,)),
            ("VACUUM", ())
        ]
        
        try:
            with self.get_connection() as conn:
                for query, params in queries:
                    conn.execute(query, params)
                logger.info(f"Cleaned up data older than {days_to_keep} days")
                return True
        except Exception as e:
            logger.error(f"Failed to cleanup old data: {e}")
            return False
    
    def get_database_stats(self) -> Dict[str, Any]:
        """Get database statistics"""
        try:
            with self.get_connection() as conn:
                stats = {}
                
                # Table sizes
                tables = ['weather_data', 'journal_entries', 'favorite_locations', 'search_history']
                for table in tables:
                    cursor = conn.execute(f"SELECT COUNT(*) as count FROM {table}")
                    stats[f"{table}_count"] = cursor.fetchone()['count']
                
                # Database size
                cursor = conn.execute("PRAGMA page_count")
                page_count = cursor.fetchone()[0]
                cursor = conn.execute("PRAGMA page_size")
                page_size = cursor.fetchone()[0]
                stats['database_size_mb'] = round((page_count * page_size) / (1024 * 1024), 2)
                
                return stats
        except Exception as e:
            logger.error(f"Failed to get database stats: {e}")
            return {}
    
    def close(self):
        """Close all connections in pool"""
        while not self.connection_pool.empty():
            try:
                conn = self.connection_pool.get_nowait()
                conn.close()
            except Exception as e:
                logger.error(f"Error closing connection: {e}")

# Global instance
_global_db = None

def get_optimized_db() -> OptimizedDatabase:
    """Get global optimized database instance"""
    global _global_db
    if _global_db is None:
        _global_db = OptimizedDatabase()
    return _global_db