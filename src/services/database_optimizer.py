"""Database optimization service for efficient database operations.

Provides connection pooling, query caching, and performance monitoring.
"""

import sqlite3
import time
import threading
import logging
import hashlib
import json
from typing import Any, Dict, List, Optional, Tuple, Union, Callable
from dataclasses import dataclass, field
from collections import defaultdict, deque
from contextlib import contextmanager
from functools import wraps
from enum import Enum
import queue


class QueryType(Enum):
    """Query type enumeration."""
    SELECT = "SELECT"
    INSERT = "INSERT"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    CREATE = "CREATE"
    DROP = "DROP"
    OTHER = "OTHER"


@dataclass
class QueryStats:
    """Query execution statistics."""
    query_hash: str
    query_type: QueryType
    execution_count: int = 0
    total_time: float = 0.0
    min_time: float = float('inf')
    max_time: float = 0.0
    avg_time: float = 0.0
    last_executed: float = field(default_factory=time.time)
    error_count: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    
    def update(self, execution_time: float, from_cache: bool = False) -> None:
        """Update statistics with new execution.
        
        Args:
            execution_time: Query execution time
            from_cache: Whether result came from cache
        """
        if from_cache:
            self.cache_hits += 1
        else:
            self.cache_misses += 1
            self.execution_count += 1
            self.total_time += execution_time
            self.min_time = min(self.min_time, execution_time)
            self.max_time = max(self.max_time, execution_time)
            self.avg_time = self.total_time / self.execution_count
        
        self.last_executed = time.time()
    
    def add_error(self) -> None:
        """Add error to statistics."""
        self.error_count += 1


@dataclass
class ConnectionStats:
    """Connection pool statistics."""
    total_connections: int = 0
    active_connections: int = 0
    idle_connections: int = 0
    created_connections: int = 0
    closed_connections: int = 0
    connection_errors: int = 0
    avg_connection_time: float = 0.0
    max_pool_size: int = 0
    
    @property
    def pool_utilization(self) -> float:
        """Calculate pool utilization percentage."""
        if self.max_pool_size == 0:
            return 0.0
        return (self.active_connections / self.max_pool_size) * 100


class ConnectionPool:
    """Database connection pool for efficient connection management."""
    
    def __init__(self, 
                 database_path: str,
                 max_connections: int = 10,
                 min_connections: int = 2,
                 connection_timeout: float = 30.0,
                 idle_timeout: float = 300.0):
        """
        Initialize connection pool.
        
        Args:
            database_path: Path to SQLite database
            max_connections: Maximum number of connections
            min_connections: Minimum number of connections
            connection_timeout: Connection timeout in seconds
            idle_timeout: Idle connection timeout in seconds
        """
        self.database_path = database_path
        self.max_connections = max_connections
        self.min_connections = min_connections
        self.connection_timeout = connection_timeout
        self.idle_timeout = idle_timeout
        
        self._pool: queue.Queue = queue.Queue(maxsize=max_connections)
        self._active_connections: Dict[int, sqlite3.Connection] = {}
        self._connection_times: Dict[int, float] = {}
        self._stats = ConnectionStats(max_pool_size=max_connections)
        self._lock = threading.RLock()
        self._logger = logging.getLogger(__name__)
        
        # Initialize minimum connections
        self._initialize_pool()
        
        # Start cleanup thread
        self._cleanup_thread = threading.Thread(
            target=self._cleanup_idle_connections,
            daemon=True
        )
        self._cleanup_thread.start()
    
    def _create_connection(self) -> sqlite3.Connection:
        """Create a new database connection.
        
        Returns:
            SQLite connection
        """
        try:
            conn = sqlite3.connect(
                self.database_path,
                timeout=self.connection_timeout,
                check_same_thread=False
            )
            
            # Enable WAL mode for better concurrency
            conn.execute("PRAGMA journal_mode=WAL")
            
            # Enable foreign keys
            conn.execute("PRAGMA foreign_keys=ON")
            
            # Set reasonable timeouts
            conn.execute("PRAGMA busy_timeout=30000")
            
            with self._lock:
                self._stats.created_connections += 1
                self._stats.total_connections += 1
            
            self._logger.debug(f"Created new database connection: {id(conn)}")
            return conn
            
        except Exception as e:
            with self._lock:
                self._stats.connection_errors += 1
            self._logger.error(f"Failed to create database connection: {e}")
            raise
    
    def _initialize_pool(self) -> None:
        """Initialize connection pool with minimum connections."""
        for _ in range(self.min_connections):
            try:
                conn = self._create_connection()
                self._pool.put(conn, block=False)
                with self._lock:
                    self._stats.idle_connections += 1
            except Exception as e:
                self._logger.error(f"Failed to initialize connection pool: {e}")
                break
    
    @contextmanager
    def get_connection(self):
        """Get connection from pool.
        
        Yields:
            Database connection
        """
        conn = None
        conn_id = None
        start_time = time.time()
        
        try:
            # Try to get connection from pool
            try:
                conn = self._pool.get(block=False)
                with self._lock:
                    self._stats.idle_connections -= 1
            except queue.Empty:
                # Create new connection if pool is empty and under limit
                with self._lock:
                    if self._stats.total_connections < self.max_connections:
                        conn = self._create_connection()
                    else:
                        # Wait for available connection
                        try:
                            conn = self._pool.get(timeout=self.connection_timeout)
                            with self._lock:
                                self._stats.idle_connections -= 1
                        except queue.Empty:
                            raise RuntimeError("Connection pool exhausted")
            
            if conn is None:
                raise RuntimeError("Failed to obtain database connection")
            
            conn_id = id(conn)
            
            with self._lock:
                self._active_connections[conn_id] = conn
                self._connection_times[conn_id] = start_time
                self._stats.active_connections += 1
                
                # Update average connection time
                connection_time = time.time() - start_time
                if self._stats.avg_connection_time == 0:
                    self._stats.avg_connection_time = connection_time
                else:
                    self._stats.avg_connection_time = (
                        self._stats.avg_connection_time * 0.9 + connection_time * 0.1
                    )
            
            yield conn
            
        finally:
            # Return connection to pool
            if conn and conn_id:
                with self._lock:
                    if conn_id in self._active_connections:
                        del self._active_connections[conn_id]
                        del self._connection_times[conn_id]
                        self._stats.active_connections -= 1
                
                try:
                    # Check if connection is still valid
                    conn.execute("SELECT 1")
                    
                    # Return to pool if not full
                    try:
                        self._pool.put(conn, block=False)
                        with self._lock:
                            self._stats.idle_connections += 1
                    except queue.Full:
                        # Pool is full, close connection
                        conn.close()
                        with self._lock:
                            self._stats.closed_connections += 1
                            self._stats.total_connections -= 1
                        
                except Exception as e:
                    # Connection is invalid, close it
                    self._logger.warning(f"Closing invalid connection: {e}")
                    try:
                        conn.close()
                    except:
                        pass
                    
                    with self._lock:
                        self._stats.closed_connections += 1
                        self._stats.total_connections -= 1
    
    def _cleanup_idle_connections(self) -> None:
        """Clean up idle connections that exceed timeout."""
        while True:
            try:
                time.sleep(60)  # Check every minute
                
                current_time = time.time()
                connections_to_close = []
                
                with self._lock:
                    for conn_id, conn_time in self._connection_times.items():
                        if current_time - conn_time > self.idle_timeout:
                            connections_to_close.append(conn_id)
                
                # Close idle connections
                for conn_id in connections_to_close:
                    with self._lock:
                        if conn_id in self._active_connections:
                            conn = self._active_connections[conn_id]
                            try:
                                conn.close()
                            except:
                                pass
                            
                            del self._active_connections[conn_id]
                            del self._connection_times[conn_id]
                            self._stats.active_connections -= 1
                            self._stats.closed_connections += 1
                            self._stats.total_connections -= 1
                
            except Exception as e:
                self._logger.error(f"Error in connection cleanup: {e}")
    
    def get_stats(self) -> ConnectionStats:
        """Get connection pool statistics.
        
        Returns:
            Connection statistics
        """
        with self._lock:
            return ConnectionStats(
                total_connections=self._stats.total_connections,
                active_connections=self._stats.active_connections,
                idle_connections=self._stats.idle_connections,
                created_connections=self._stats.created_connections,
                closed_connections=self._stats.closed_connections,
                connection_errors=self._stats.connection_errors,
                avg_connection_time=self._stats.avg_connection_time,
                max_pool_size=self.max_connections
            )
    
    def close_all(self) -> None:
        """Close all connections in pool."""
        with self._lock:
            # Close active connections
            for conn in self._active_connections.values():
                try:
                    conn.close()
                except:
                    pass
            
            # Close idle connections
            while not self._pool.empty():
                try:
                    conn = self._pool.get(block=False)
                    conn.close()
                except:
                    pass
            
            self._active_connections.clear()
            self._connection_times.clear()
            self._stats = ConnectionStats(max_pool_size=self.max_connections)


class QueryCache:
    """Cache for database query results."""
    
    def __init__(self, max_size: int = 1000, ttl_seconds: float = 300.0):
        """
        Initialize query cache.
        
        Args:
            max_size: Maximum number of cached queries
            ttl_seconds: Time-to-live for cached results
        """
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        
        self._cache: Dict[str, Tuple[Any, float]] = {}
        self._access_times: Dict[str, float] = {}
        self._lock = threading.RLock()
        self._logger = logging.getLogger(__name__)
    
    def _generate_key(self, query: str, params: Optional[Tuple] = None) -> str:
        """Generate cache key for query.
        
        Args:
            query: SQL query
            params: Query parameters
            
        Returns:
            Cache key
        """
        key_data = {
            'query': query.strip().lower(),
            'params': params or ()
        }
        key_str = json.dumps(key_data, sort_keys=True)
        return hashlib.md5(key_str.encode()).hexdigest()
    
    def get(self, query: str, params: Optional[Tuple] = None) -> Optional[Any]:
        """Get cached query result.
        
        Args:
            query: SQL query
            params: Query parameters
            
        Returns:
            Cached result or None
        """
        key = self._generate_key(query, params)
        
        with self._lock:
            if key in self._cache:
                result, timestamp = self._cache[key]
                
                # Check if result is still valid
                if time.time() - timestamp < self.ttl_seconds:
                    self._access_times[key] = time.time()
                    return result
                else:
                    # Remove expired entry
                    del self._cache[key]
                    if key in self._access_times:
                        del self._access_times[key]
        
        return None
    
    def set(self, query: str, params: Optional[Tuple], result: Any) -> None:
        """Cache query result.
        
        Args:
            query: SQL query
            params: Query parameters
            result: Query result
        """
        key = self._generate_key(query, params)
        current_time = time.time()
        
        with self._lock:
            # Remove oldest entries if cache is full
            if len(self._cache) >= self.max_size:
                self._evict_oldest()
            
            self._cache[key] = (result, current_time)
            self._access_times[key] = current_time
    
    def _evict_oldest(self) -> None:
        """Evict oldest cache entries."""
        if not self._access_times:
            return
        
        # Find oldest entry
        oldest_key = min(self._access_times.keys(), 
                        key=lambda k: self._access_times[k])
        
        # Remove oldest entry
        if oldest_key in self._cache:
            del self._cache[oldest_key]
        del self._access_times[oldest_key]
    
    def clear(self) -> None:
        """Clear all cached entries."""
        with self._lock:
            self._cache.clear()
            self._access_times.clear()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics.
        
        Returns:
            Dictionary with cache statistics
        """
        with self._lock:
            return {
                'cache_size': len(self._cache),
                'max_size': self.max_size,
                'utilization': len(self._cache) / self.max_size * 100,
                'ttl_seconds': self.ttl_seconds
            }


class DatabaseOptimizer:
    """Service for database optimization and monitoring."""
    
    def __init__(self, 
                 database_path: str,
                 max_connections: int = 10,
                 cache_size: int = 1000,
                 cache_ttl: float = 300.0):
        """
        Initialize database optimizer.
        
        Args:
            database_path: Path to SQLite database
            max_connections: Maximum number of connections
            cache_size: Maximum number of cached queries
            cache_ttl: Cache time-to-live in seconds
        """
        self.database_path = database_path
        
        self._connection_pool = ConnectionPool(
            database_path=database_path,
            max_connections=max_connections
        )
        
        self._query_cache = QueryCache(
            max_size=cache_size,
            ttl_seconds=cache_ttl
        )
        
        self._query_stats: Dict[str, QueryStats] = {}
        self._prepared_statements: Dict[str, str] = {}
        self._indexes_created: Set[str] = set()
        
        self._lock = threading.RLock()
        self._logger = logging.getLogger(__name__)
        
        # Create performance indexes
        self._create_performance_indexes()
    
    def _get_query_type(self, query: str) -> QueryType:
        """Determine query type.
        
        Args:
            query: SQL query
            
        Returns:
            Query type
        """
        query_upper = query.strip().upper()
        
        if query_upper.startswith('SELECT'):
            return QueryType.SELECT
        elif query_upper.startswith('INSERT'):
            return QueryType.INSERT
        elif query_upper.startswith('UPDATE'):
            return QueryType.UPDATE
        elif query_upper.startswith('DELETE'):
            return QueryType.DELETE
        elif query_upper.startswith('CREATE'):
            return QueryType.CREATE
        elif query_upper.startswith('DROP'):
            return QueryType.DROP
        else:
            return QueryType.OTHER
    
    def _get_query_hash(self, query: str) -> str:
        """Generate hash for query (for statistics).
        
        Args:
            query: SQL query
            
        Returns:
            Query hash
        """
        # Normalize query for hashing
        normalized = ' '.join(query.strip().lower().split())
        return hashlib.md5(normalized.encode()).hexdigest()[:16]
    
    def _create_performance_indexes(self) -> None:
        """Create performance indexes for common queries."""
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_weather_data_timestamp ON weather_data(timestamp)",
            "CREATE INDEX IF NOT EXISTS idx_weather_data_city ON weather_data(city_name)",
            "CREATE INDEX IF NOT EXISTS idx_weather_data_city_timestamp ON weather_data(city_name, timestamp)",
            "CREATE INDEX IF NOT EXISTS idx_forecast_data_timestamp ON forecast_data(timestamp)",
            "CREATE INDEX IF NOT EXISTS idx_forecast_data_city ON forecast_data(city_name)",
            "CREATE INDEX IF NOT EXISTS idx_user_preferences_user_id ON user_preferences(user_id)",
        ]
        
        try:
            with self._connection_pool.get_connection() as conn:
                for index_sql in indexes:
                    try:
                        conn.execute(index_sql)
                        index_name = index_sql.split()[5]  # Extract index name
                        self._indexes_created.add(index_name)
                        self._logger.debug(f"Created index: {index_name}")
                    except Exception as e:
                        self._logger.warning(f"Failed to create index: {e}")
                
                conn.commit()
                
        except Exception as e:
            self._logger.error(f"Failed to create performance indexes: {e}")
    
    def execute_query(self, 
                     query: str, 
                     params: Optional[Tuple] = None,
                     use_cache: bool = True,
                     fetch_all: bool = True) -> Any:
        """
        Execute database query with optimization.
        
        Args:
            query: SQL query
            params: Query parameters
            use_cache: Whether to use query cache
            fetch_all: Whether to fetch all results
            
        Returns:
            Query result
        """
        query_type = self._get_query_type(query)
        query_hash = self._get_query_hash(query)
        start_time = time.time()
        
        # Check cache for SELECT queries
        if use_cache and query_type == QueryType.SELECT:
            cached_result = self._query_cache.get(query, params)
            if cached_result is not None:
                execution_time = time.time() - start_time
                self._update_query_stats(query_hash, query_type, execution_time, from_cache=True)
                return cached_result
        
        try:
            with self._connection_pool.get_connection() as conn:
                cursor = conn.cursor()
                
                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)
                
                # Get result based on query type
                if query_type == QueryType.SELECT:
                    result = cursor.fetchall() if fetch_all else cursor.fetchone()
                    
                    # Cache SELECT results
                    if use_cache:
                        self._query_cache.set(query, params, result)
                else:
                    result = cursor.rowcount
                    conn.commit()
                
                execution_time = time.time() - start_time
                self._update_query_stats(query_hash, query_type, execution_time, from_cache=False)
                
                return result
                
        except Exception as e:
            execution_time = time.time() - start_time
            self._update_query_stats(query_hash, query_type, execution_time, error=True)
            self._logger.error(f"Query execution failed: {e}")
            raise
    
    def execute_batch(self, 
                     query: str, 
                     params_list: List[Tuple],
                     batch_size: int = 100) -> int:
        """
        Execute batch operations for better performance.
        
        Args:
            query: SQL query
            params_list: List of parameter tuples
            batch_size: Batch size for processing
            
        Returns:
            Total number of affected rows
        """
        query_type = self._get_query_type(query)
        query_hash = self._get_query_hash(query)
        start_time = time.time()
        total_affected = 0
        
        try:
            with self._connection_pool.get_connection() as conn:
                cursor = conn.cursor()
                
                # Process in batches
                for i in range(0, len(params_list), batch_size):
                    batch = params_list[i:i + batch_size]
                    cursor.executemany(query, batch)
                    total_affected += cursor.rowcount
                
                conn.commit()
                
                execution_time = time.time() - start_time
                self._update_query_stats(query_hash, query_type, execution_time, from_cache=False)
                
                return total_affected
                
        except Exception as e:
            execution_time = time.time() - start_time
            self._update_query_stats(query_hash, query_type, execution_time, error=True)
            self._logger.error(f"Batch execution failed: {e}")
            raise
    
    def _update_query_stats(self, 
                           query_hash: str, 
                           query_type: QueryType, 
                           execution_time: float,
                           from_cache: bool = False,
                           error: bool = False) -> None:
        """
        Update query statistics.
        
        Args:
            query_hash: Query hash
            query_type: Query type
            execution_time: Execution time
            from_cache: Whether result came from cache
            error: Whether query had an error
        """
        with self._lock:
            if query_hash not in self._query_stats:
                self._query_stats[query_hash] = QueryStats(
                    query_hash=query_hash,
                    query_type=query_type
                )
            
            stats = self._query_stats[query_hash]
            
            if error:
                stats.add_error()
            else:
                stats.update(execution_time, from_cache)
    
    def get_query_stats(self, limit: int = 50) -> List[QueryStats]:
        """
        Get query statistics.
        
        Args:
            limit: Maximum number of stats to return
            
        Returns:
            List of query statistics
        """
        with self._lock:
            stats_list = list(self._query_stats.values())
            
            # Sort by total execution time (descending)
            stats_list.sort(key=lambda s: s.total_time, reverse=True)
            
            return stats_list[:limit]
    
    def get_connection_stats(self) -> ConnectionStats:
        """
        Get connection pool statistics.
        
        Returns:
            Connection statistics
        """
        return self._connection_pool.get_stats()
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get query cache statistics.
        
        Returns:
            Cache statistics
        """
        return self._query_cache.get_stats()
    
    def optimize_database(self) -> Dict[str, Any]:
        """
        Optimize database performance.
        
        Returns:
            Optimization results
        """
        optimization_results = {
            'start_time': time.time(),
            'actions_taken': []
        }
        
        try:
            with self._connection_pool.get_connection() as conn:
                # Analyze database
                conn.execute("ANALYZE")
                optimization_results['actions_taken'].append("Analyzed database statistics")
                
                # Vacuum database
                conn.execute("VACUUM")
                optimization_results['actions_taken'].append("Vacuumed database")
                
                # Optimize indexes
                conn.execute("REINDEX")
                optimization_results['actions_taken'].append("Reindexed database")
                
                conn.commit()
                
        except Exception as e:
            self._logger.error(f"Database optimization failed: {e}")
            optimization_results['error'] = str(e)
        
        optimization_results['end_time'] = time.time()
        optimization_results['duration'] = optimization_results['end_time'] - optimization_results['start_time']
        
        return optimization_results
    
    def clear_cache(self) -> None:
        """Clear query cache."""
        self._query_cache.clear()
        self._logger.info("Query cache cleared")
    
    def close(self) -> None:
        """Close database optimizer."""
        self._connection_pool.close_all()
        self._query_cache.clear()
        self._logger.info("Database optimizer closed")


# Decorators for database optimization
def cached_query(ttl_seconds: float = 300.0):
    """Decorator for caching query results.
    
    Args:
        ttl_seconds: Cache time-to-live
        
    Returns:
        Decorator function
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # This would integrate with the database optimizer
            # For now, just execute the function
            return func(*args, **kwargs)
        
        return wrapper
    
    return decorator


def batch_operation(batch_size: int = 100):
    """Decorator for batch database operations.
    
    Args:
        batch_size: Batch size
        
    Returns:
        Decorator function
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # This would integrate with batch processing
            # For now, just execute the function
            return func(*args, **kwargs)
        
        return wrapper
    
    return decorator


# Global database optimizer instance
_global_db_optimizer = None


def get_database_optimizer(database_path: str = "weather_dashboard.db") -> DatabaseOptimizer:
    """Get global database optimizer instance.
    
    Args:
        database_path: Path to database file
        
    Returns:
        Database optimizer instance
    """
    global _global_db_optimizer
    if _global_db_optimizer is None:
        _global_db_optimizer = DatabaseOptimizer(database_path)
    return _global_db_optimizer