"""Database Context Management

Handles database connections, transactions, and connection pooling.
"""

import sqlite3
import threading
from abc import ABC, abstractmethod
from contextlib import asynccontextmanager, contextmanager
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional


class DatabaseType(Enum):
    """Supported database types."""

    SQLITE = "sqlite"
    MEMORY = "memory"


class ConnectionState(Enum):
    """Database connection states."""

    CLOSED = "closed"
    OPEN = "open"
    TRANSACTION = "transaction"
    ERROR = "error"


@dataclass
class DatabaseConfig:
    """Database configuration."""

    db_type: DatabaseType = DatabaseType.SQLITE
    connection_string: str = ""
    max_connections: int = 10
    connection_timeout: int = 30
    enable_wal_mode: bool = True
    enable_foreign_keys: bool = True
    cache_size: int = -2000  # 2MB cache
    synchronous: str = "NORMAL"  # OFF, NORMAL, FULL
    journal_mode: str = "WAL"  # DELETE, TRUNCATE, PERSIST, MEMORY, WAL, OFF
    temp_store: str = "MEMORY"  # DEFAULT, FILE, MEMORY

    def get_pragma_settings(self) -> Dict[str, Any]:
        """Get SQLite PRAGMA settings."""
        return {
            "foreign_keys": "ON" if self.enable_foreign_keys else "OFF",
            "cache_size": self.cache_size,
            "synchronous": self.synchronous,
            "journal_mode": self.journal_mode,
            "temp_store": self.temp_store,
            "mmap_size": 268435456,  # 256MB
            "optimize": None,  # Run PRAGMA optimize on close
        }


@dataclass
class ConnectionInfo:
    """Information about a database connection."""

    connection_id: str
    database_path: str
    state: ConnectionState
    created_at: datetime
    last_used: datetime
    transaction_count: int = 0
    error_count: int = 0
    last_error: Optional[str] = None


class IDatabaseContext(ABC):
    """Abstract database context interface."""

    @abstractmethod
    async def get_connection(self, database_name: str) -> sqlite3.Connection:
        """Get database connection."""

    @abstractmethod
    async def begin_transaction(self) -> str:
        """Begin transaction."""

    @abstractmethod
    async def commit_transaction(self) -> bool:
        """Commit transaction."""

    @abstractmethod
    async def rollback_transaction(self) -> bool:
        """Rollback transaction."""

    @abstractmethod
    async def close(self):
        """Close all connections."""


class DatabaseContext(IDatabaseContext):
    """Concrete database context implementation."""

    def __init__(self, config: DatabaseConfig, base_path: str = "data"):
        self.config = config
        self.base_path = Path(base_path)
        self.base_path.mkdir(exist_ok=True)

        # Database paths
        self.weather_db_path = str(self.base_path / "weather.db")
        self.forecast_db_path = str(self.base_path / "forecast.db")
        self.preferences_db_path = str(self.base_path / "preferences.db")
        self.activities_db_path = str(self.base_path / "activities.db")

        # Connection management
        self._connections: Dict[str, sqlite3.Connection] = {}
        self._connection_info: Dict[str, ConnectionInfo] = {}
        self._transaction_connections: Dict[str, sqlite3.Connection] = {}
        self._lock = threading.RLock()
        self._transaction_lock = threading.RLock()

        # Transaction state
        self._current_transaction_id: Optional[str] = None
        self._transaction_connections_map: Dict[str, List[str]] = {}

    @property
    def database_paths(self) -> Dict[str, str]:
        """Get all database paths."""
        return {
            "weather": self.weather_db_path,
            "forecast": self.forecast_db_path,
            "preferences": self.preferences_db_path,
            "activities": self.activities_db_path,
        }

    async def initialize(self):
        """Initialize database context and create databases."""
        for db_name, db_path in self.database_paths.items():
            await self._ensure_database_exists(db_path)
            await self._configure_database(db_path)

    async def get_connection(self, database_name: str) -> sqlite3.Connection:
        """Get database connection for specified database."""
        db_path = self.database_paths.get(database_name)
        if not db_path:
            raise ValueError(f"Unknown database: {database_name}")

        return await self._get_or_create_connection(db_path)

    async def get_connection_by_path(self, db_path: str) -> sqlite3.Connection:
        """Get database connection by path."""
        return await self._get_or_create_connection(db_path)

    async def _get_or_create_connection(self, db_path: str) -> sqlite3.Connection:
        """Get existing connection or create new one."""
        with self._lock:
            connection_id = f"{db_path}_{threading.current_thread().ident}"

            if connection_id in self._connections:
                conn = self._connections[connection_id]

                # Update last used time
                if connection_id in self._connection_info:
                    self._connection_info[connection_id].last_used = datetime.now()

                return conn

            # Create new connection
            conn = await self._create_connection(db_path)
            self._connections[connection_id] = conn

            # Store connection info
            self._connection_info[connection_id] = ConnectionInfo(
                connection_id=connection_id,
                database_path=db_path,
                state=ConnectionState.OPEN,
                created_at=datetime.now(),
                last_used=datetime.now(),
            )

            return conn

    async def _create_connection(self, db_path: str) -> sqlite3.Connection:
        """Create new database connection."""
        try:
            # Create connection
            conn = sqlite3.connect(
                db_path, timeout=self.config.connection_timeout, check_same_thread=False
            )

            # Configure connection
            await self._configure_connection(conn)

            return conn

        except Exception as e:
            raise RuntimeError(f"Failed to create database connection to {db_path}: {str(e)}")

    async def _configure_connection(self, conn: sqlite3.Connection):
        """Configure database connection with PRAGMA settings."""
        pragma_settings = self.config.get_pragma_settings()

        for pragma, value in pragma_settings.items():
            if value is not None:
                conn.execute(f"PRAGMA {pragma} = {value}")
            else:
                conn.execute(f"PRAGMA {pragma}")

        conn.commit()

    async def _ensure_database_exists(self, db_path: str):
        """Ensure database file exists."""
        db_file = Path(db_path)
        if not db_file.exists():
            # Create empty database file
            conn = sqlite3.connect(db_path)
            conn.close()

    async def _configure_database(self, db_path: str):
        """Configure database with initial settings."""
        conn = await self._get_or_create_connection(db_path)
        await self._configure_connection(conn)

    async def begin_transaction(self) -> str:
        """Begin transaction across all databases."""
        with self._transaction_lock:
            if self._current_transaction_id:
                raise RuntimeError("Transaction already active")

            transaction_id = f"txn_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
            self._current_transaction_id = transaction_id
            self._transaction_connections_map[transaction_id] = []

            try:
                # Begin transaction on all databases
                for db_name, db_path in self.database_paths.items():
                    conn = await self._get_or_create_connection(db_path)
                    conn.execute("BEGIN IMMEDIATE")

                    # Store transaction connection
                    conn_id = f"{db_path}_{threading.current_thread().ident}"
                    self._transaction_connections[f"{transaction_id}_{conn_id}"] = conn
                    self._transaction_connections_map[transaction_id].append(
                        f"{transaction_id}_{conn_id}"
                    )

                    # Update connection state
                    if conn_id in self._connection_info:
                        self._connection_info[conn_id].state = ConnectionState.TRANSACTION
                        self._connection_info[conn_id].transaction_count += 1

                return transaction_id

            except Exception as e:
                # Cleanup on error
                await self._cleanup_failed_transaction(transaction_id)
                raise RuntimeError(f"Failed to begin transaction: {str(e)}")

    async def commit_transaction(self) -> bool:
        """Commit current transaction."""
        with self._transaction_lock:
            if not self._current_transaction_id:
                raise RuntimeError("No active transaction to commit")

            transaction_id = self._current_transaction_id

            try:
                # Commit all transaction connections
                for conn_key in self._transaction_connections_map.get(transaction_id, []):
                    if conn_key in self._transaction_connections:
                        conn = self._transaction_connections[conn_key]
                        conn.commit()

                # Update connection states
                await self._update_connection_states_after_transaction(
                    transaction_id, ConnectionState.OPEN
                )

                # Cleanup transaction
                await self._cleanup_transaction(transaction_id)

                return True

            except Exception as e:
                # Rollback on commit failure
                await self.rollback_transaction()
                raise RuntimeError(f"Failed to commit transaction: {str(e)}")

    async def rollback_transaction(self) -> bool:
        """Rollback current transaction."""
        with self._transaction_lock:
            if not self._current_transaction_id:
                return True  # Nothing to rollback

            transaction_id = self._current_transaction_id

            try:
                # Rollback all transaction connections
                for conn_key in self._transaction_connections_map.get(transaction_id, []):
                    if conn_key in self._transaction_connections:
                        conn = self._transaction_connections[conn_key]
                        try:
                            conn.rollback()
                        except Exception:
                            # Continue with other connections
                            pass

                # Update connection states
                await self._update_connection_states_after_transaction(
                    transaction_id, ConnectionState.OPEN
                )

                # Cleanup transaction
                await self._cleanup_transaction(transaction_id)

                return True

            except Exception as e:
                # Force cleanup even on rollback failure
                await self._cleanup_transaction(transaction_id)
                raise RuntimeError(f"Failed to rollback transaction: {str(e)}")

    async def _update_connection_states_after_transaction(
        self, transaction_id: str, new_state: ConnectionState
    ):
        """Update connection states after transaction completion."""
        for conn_key in self._transaction_connections_map.get(transaction_id, []):
            # Extract original connection ID
            original_conn_id = conn_key.replace(f"{transaction_id}_", "")

            if original_conn_id in self._connection_info:
                self._connection_info[original_conn_id].state = new_state

    async def _cleanup_transaction(self, transaction_id: str):
        """Clean up transaction resources."""
        # Remove transaction connections
        for conn_key in self._transaction_connections_map.get(transaction_id, []):
            if conn_key in self._transaction_connections:
                del self._transaction_connections[conn_key]

        # Remove transaction mapping
        if transaction_id in self._transaction_connections_map:
            del self._transaction_connections_map[transaction_id]

        # Clear current transaction
        self._current_transaction_id = None

    async def _cleanup_failed_transaction(self, transaction_id: str):
        """Clean up failed transaction."""
        try:
            # Try to rollback any started transactions
            for conn_key in self._transaction_connections_map.get(transaction_id, []):
                if conn_key in self._transaction_connections:
                    conn = self._transaction_connections[conn_key]
                    try:
                        conn.rollback()
                    except Exception:
                        pass

            # Cleanup resources
            await self._cleanup_transaction(transaction_id)

        except Exception:
            # Force cleanup
            self._current_transaction_id = None
            if transaction_id in self._transaction_connections_map:
                del self._transaction_connections_map[transaction_id]

    @contextmanager
    def transaction_scope(self):
        """Context manager for database transactions."""
        try:
            # Note: This is a sync context manager, so we can't use async methods
            # This is a simplified version for sync usage
            yield self
        except Exception:
            # Rollback would happen here in async version
            raise

    @asynccontextmanager
    async def async_transaction_scope(self):
        """Async context manager for database transactions."""
        await self.begin_transaction()
        try:
            yield self
            await self.commit_transaction()
        except Exception:
            await self.rollback_transaction()
            raise

    async def execute_query(
        self, database_name: str, query: str, params: tuple = ()
    ) -> sqlite3.Cursor:
        """Execute query on specified database."""
        conn = await self.get_connection(database_name)
        return conn.execute(query, params)

    async def execute_many(
        self, database_name: str, query: str, params_list: List[tuple]
    ) -> sqlite3.Cursor:
        """Execute query with multiple parameter sets."""
        conn = await self.get_connection(database_name)
        return conn.executemany(query, params_list)

    async def get_connection_info(self) -> List[ConnectionInfo]:
        """Get information about all connections."""
        with self._lock:
            return list(self._connection_info.values())

    async def get_database_stats(self) -> Dict[str, Any]:
        """Get database statistics."""
        stats = {
            "total_connections": len(self._connections),
            "active_transactions": 1 if self._current_transaction_id else 0,
            "databases": {},
        }

        for db_name, db_path in self.database_paths.items():
            try:
                conn = await self.get_connection(db_name)
                cursor = conn.execute("PRAGMA page_count")
                page_count = cursor.fetchone()[0]

                cursor = conn.execute("PRAGMA page_size")
                page_size = cursor.fetchone()[0]

                cursor = conn.execute("PRAGMA freelist_count")
                free_pages = cursor.fetchone()[0]

                stats["databases"][db_name] = {
                    "path": db_path,
                    "size_bytes": page_count * page_size,
                    "free_pages": free_pages,
                    "page_size": page_size,
                    "page_count": page_count,
                }

            except Exception as e:
                stats["databases"][db_name] = {"path": db_path, "error": str(e)}

        return stats

    async def vacuum_databases(self) -> Dict[str, bool]:
        """Vacuum all databases to reclaim space."""
        results = {}

        for db_name, db_path in self.database_paths.items():
            try:
                conn = await self.get_connection(db_name)
                conn.execute("VACUUM")
                conn.commit()
                results[db_name] = True
            except Exception:
                results[db_name] = False

        return results

    async def optimize_databases(self) -> Dict[str, bool]:
        """Optimize all databases."""
        results = {}

        for db_name, db_path in self.database_paths.items():
            try:
                conn = await self.get_connection(db_name)
                conn.execute("PRAGMA optimize")
                conn.commit()
                results[db_name] = True
            except Exception:
                results[db_name] = False

        return results

    async def close_connection(self, database_name: str):
        """Close specific database connection."""
        db_path = self.database_paths.get(database_name)
        if not db_path:
            return

        with self._lock:
            connection_id = f"{db_path}_{threading.current_thread().ident}"

            if connection_id in self._connections:
                conn = self._connections[connection_id]
                try:
                    conn.close()
                except Exception:
                    pass

                del self._connections[connection_id]

                if connection_id in self._connection_info:
                    self._connection_info[connection_id].state = ConnectionState.CLOSED

    async def close(self):
        """Close all database connections."""
        with self._lock:
            # Rollback any active transaction
            if self._current_transaction_id:
                try:
                    await self.rollback_transaction()
                except Exception:
                    pass

            # Close all connections
            for conn in self._connections.values():
                try:
                    conn.close()
                except Exception:
                    pass

            # Clear all connection data
            self._connections.clear()
            self._connection_info.clear()
            self._transaction_connections.clear()
            self._transaction_connections_map.clear()

    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on all databases."""
        health_status = {
            "overall_healthy": True,
            "databases": {},
            "connections": len(self._connections),
            "active_transaction": self._current_transaction_id is not None,
        }

        for db_name, db_path in self.database_paths.items():
            try:
                conn = await self.get_connection(db_name)
                cursor = conn.execute("SELECT 1")
                cursor.fetchone()

                health_status["databases"][db_name] = {"healthy": True, "path": db_path}

            except Exception as e:
                health_status["databases"][db_name] = {
                    "healthy": False,
                    "path": db_path,
                    "error": str(e),
                }
                health_status["overall_healthy"] = False

        return health_status


class DatabaseContextFactory:
    """Factory for creating database contexts."""

    @staticmethod
    def create_sqlite_context(base_path: str = "data", **config_kwargs) -> DatabaseContext:
        """Create SQLite database context."""
        config = DatabaseConfig(db_type=DatabaseType.SQLITE, **config_kwargs)
        return DatabaseContext(config, base_path)

    @staticmethod
    def create_memory_context(**config_kwargs) -> DatabaseContext:
        """Create in-memory database context for testing."""
        config = DatabaseConfig(db_type=DatabaseType.MEMORY, **config_kwargs)
        return DatabaseContext(config, ":memory:")
