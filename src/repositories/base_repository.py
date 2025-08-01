"""Base Repository

Provides abstract base class for repository pattern implementation
with generic type support, async operations, and connection pooling.
"""

import asyncio
import json
import logging
import sqlite3
from abc import ABC, abstractmethod
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from pathlib import Path
from threading import Lock
from typing import Any, Dict, Generic, List, Optional, TypeVar, Union

from ..core.exceptions import DataPersistenceError
from ..core.interfaces import IDataRepository

T = TypeVar("T")


class ConnectionPool:
    """Simple SQLite connection pool for async operations."""

    def __init__(self, database_path: str, max_connections: int = 10):
        """Initialize connection pool.

        Args:
            database_path: Path to SQLite database
            max_connections: Maximum number of connections
        """
        self.database_path = database_path
        self.max_connections = max_connections
        self._connections: List[sqlite3.Connection] = []
        self._lock = Lock()
        self._logger = logging.getLogger(__name__)

    def get_connection(self) -> sqlite3.Connection:
        """Get a connection from the pool.

        Returns:
            SQLite connection
        """
        with self._lock:
            if self._connections:
                return self._connections.pop()

            # Create new connection if pool is empty
            conn = sqlite3.connect(self.database_path, check_same_thread=False)
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA foreign_keys = ON")
            conn.execute("PRAGMA journal_mode = WAL")
            return conn

    def return_connection(self, connection: sqlite3.Connection) -> None:
        """Return a connection to the pool.

        Args:
            connection: SQLite connection to return
        """
        with self._lock:
            if len(self._connections) < self.max_connections:
                self._connections.append(connection)
            else:
                connection.close()

    def close_all(self) -> None:
        """Close all connections in the pool."""
        with self._lock:
            for conn in self._connections:
                conn.close()
            self._connections.clear()


class BaseRepository(Generic[T], IDataRepository, ABC):
    """Abstract base repository class with CRUD operations.

    Provides common database operations with generic type support,
    async operations, and connection pooling.
    """

    def __init__(self, database_path: str, table_name: str):
        """Initialize the repository.

        Args:
            database_path: Path to SQLite database
            table_name: Name of the database table
        """
        self.database_path = Path(database_path)
        self.table_name = table_name
        self._connection_pool = ConnectionPool(str(self.database_path))
        self._logger = logging.getLogger(__name__)

        # Ensure database directory exists
        self.database_path.parent.mkdir(parents=True, exist_ok=True)

        # Initialize database schema
        asyncio.create_task(self._initialize_schema())

    @asynccontextmanager
    async def _get_connection(self):
        """Get a database connection from the pool.

        Yields:
            SQLite connection
        """
        connection = None
        try:
            # Run in thread pool to avoid blocking
            connection = await asyncio.get_event_loop().run_in_executor(
                None, self._connection_pool.get_connection
            )
            yield connection
        except Exception as e:
            if connection:
                await asyncio.get_event_loop().run_in_executor(None, connection.rollback)
            raise DataPersistenceError(
                f"Database connection error: {e}",
                operation="connection",
                entity_type=self.table_name,
            ) from e
        finally:
            if connection:
                await asyncio.get_event_loop().run_in_executor(
                    None, self._connection_pool.return_connection, connection
                )

    @abstractmethod
    async def _initialize_schema(self) -> None:
        """Initialize database schema for this repository."""

    @abstractmethod
    def _serialize_entity(self, entity: T) -> Dict[str, Any]:
        """Serialize entity to dictionary for database storage.

        Args:
            entity: Entity to serialize

        Returns:
            Dictionary representation of entity
        """

    @abstractmethod
    def _deserialize_entity(self, data: Dict[str, Any]) -> T:
        """Deserialize dictionary to entity.

        Args:
            data: Dictionary data from database

        Returns:
            Entity instance
        """

    async def save(self, entity: T, entity_id: Optional[str] = None) -> str:
        """Save an entity to the repository.

        Args:
            entity: Entity to save
            entity_id: Optional entity ID

        Returns:
            Entity ID
        """
        try:
            data = self._serialize_entity(entity)

            if entity_id is None:
                entity_id = self._generate_id()

            data["id"] = entity_id
            data["created_at"] = datetime.utcnow().isoformat()
            data["updated_at"] = datetime.utcnow().isoformat()

            async with self._get_connection() as conn:
                # Prepare insert statement
                columns = list(data.keys())
                placeholders = ", ".join(["?" for _ in columns])
                values = [self._serialize_value(data[col]) for col in columns]

                query = f"INSERT OR REPLACE INTO {self.table_name} ({', '.join(columns)}) VALUES ({placeholders})"

                await asyncio.get_event_loop().run_in_executor(None, conn.execute, query, values)
                await asyncio.get_event_loop().run_in_executor(None, conn.commit)

            self._logger.debug(f"Saved entity {entity_id} to {self.table_name}")
            return entity_id

        except Exception as e:
            raise DataPersistenceError(
                f"Failed to save entity: {e}",
                operation="save",
                entity_type=self.table_name,
                entity_id=entity_id,
            ) from e

    async def get_by_id(self, entity_id: str) -> Optional[T]:
        """Get an entity by ID.

        Args:
            entity_id: Entity ID

        Returns:
            Entity or None if not found
        """
        try:
            async with self._get_connection() as conn:
                query = f"SELECT * FROM {self.table_name} WHERE id = ?"
                cursor = await asyncio.get_event_loop().run_in_executor(
                    None, conn.execute, query, (entity_id,)
                )
                row = await asyncio.get_event_loop().run_in_executor(None, cursor.fetchone)

                if row:
                    data = dict(row)
                    # Deserialize JSON fields
                    for key, value in data.items():
                        data[key] = self._deserialize_value(value)
                    return self._deserialize_entity(data)

                return None

        except Exception as e:
            raise DataPersistenceError(
                f"Failed to get entity: {e}",
                operation="get",
                entity_type=self.table_name,
                entity_id=entity_id,
            ) from e

    async def get_all(self, filters: Optional[Dict[str, Any]] = None) -> List[T]:
        """Get all entities matching filters.

        Args:
            filters: Optional filter criteria

        Returns:
            List of entities
        """
        try:
            query = f"SELECT * FROM {self.table_name}"
            params = []

            if filters:
                conditions = []
                for key, value in filters.items():
                    conditions.append(f"{key} = ?")
                    params.append(self._serialize_value(value))
                query += f" WHERE {' AND '.join(conditions)}"

            query += " ORDER BY created_at DESC"

            async with self._get_connection() as conn:
                cursor = await asyncio.get_event_loop().run_in_executor(
                    None, conn.execute, query, params
                )
                rows = await asyncio.get_event_loop().run_in_executor(None, cursor.fetchall)

                entities = []
                for row in rows:
                    data = dict(row)
                    # Deserialize JSON fields
                    for key, value in data.items():
                        data[key] = self._deserialize_value(value)
                    entities.append(self._deserialize_entity(data))

                return entities

        except Exception as e:
            raise DataPersistenceError(
                f"Failed to get entities: {e}", operation="get_all", entity_type=self.table_name
            ) from e

    async def update(self, entity_id: str, entity: T) -> bool:
        """Update an entity.

        Args:
            entity_id: Entity ID
            entity: Updated entity

        Returns:
            True if updated successfully, False otherwise
        """
        try:
            if not await self.exists(entity_id):
                return False

            data = self._serialize_entity(entity)
            data["id"] = entity_id
            data["updated_at"] = datetime.utcnow().isoformat()

            # Remove created_at to avoid overwriting
            data.pop("created_at", None)

            async with self._get_connection() as conn:
                # Prepare update statement
                set_clauses = [f"{col} = ?" for col in data.keys()]
                values = [self._serialize_value(data[col]) for col in data.keys()]

                query = f"UPDATE {self.table_name} SET {', '.join(set_clauses)} WHERE id = ?"
                values.append(entity_id)

                await asyncio.get_event_loop().run_in_executor(None, conn.execute, query, values)
                await asyncio.get_event_loop().run_in_executor(None, conn.commit)

            self._logger.debug(f"Updated entity {entity_id} in {self.table_name}")
            return True

        except Exception as e:
            raise DataPersistenceError(
                f"Failed to update entity: {e}",
                operation="update",
                entity_type=self.table_name,
                entity_id=entity_id,
            ) from e

    async def delete(self, entity_id: str) -> bool:
        """Delete an entity.

        Args:
            entity_id: Entity ID

        Returns:
            True if deleted successfully, False otherwise
        """
        try:
            async with self._get_connection() as conn:
                query = f"DELETE FROM {self.table_name} WHERE id = ?"
                cursor = await asyncio.get_event_loop().run_in_executor(
                    None, conn.execute, query, (entity_id,)
                )
                await asyncio.get_event_loop().run_in_executor(None, conn.commit)

                deleted = cursor.rowcount > 0
                if deleted:
                    self._logger.debug(f"Deleted entity {entity_id} from {self.table_name}")
                return deleted

        except Exception as e:
            raise DataPersistenceError(
                f"Failed to delete entity: {e}",
                operation="delete",
                entity_type=self.table_name,
                entity_id=entity_id,
            ) from e

    async def exists(self, entity_id: str) -> bool:
        """Check if an entity exists.

        Args:
            entity_id: Entity ID

        Returns:
            True if entity exists, False otherwise
        """
        try:
            async with self._get_connection() as conn:
                query = f"SELECT 1 FROM {self.table_name} WHERE id = ? LIMIT 1"
                cursor = await asyncio.get_event_loop().run_in_executor(
                    None, conn.execute, query, (entity_id,)
                )
                row = await asyncio.get_event_loop().run_in_executor(None, cursor.fetchone)
                return row is not None

        except Exception as e:
            raise DataPersistenceError(
                f"Failed to check entity existence: {e}",
                operation="exists",
                entity_type=self.table_name,
                entity_id=entity_id,
            ) from e

    async def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """Count entities matching filters.

        Args:
            filters: Optional filter criteria

        Returns:
            Number of matching entities
        """
        try:
            query = f"SELECT COUNT(*) FROM {self.table_name}"
            params = []

            if filters:
                conditions = []
                for key, value in filters.items():
                    conditions.append(f"{key} = ?")
                    params.append(self._serialize_value(value))
                query += f" WHERE {' AND '.join(conditions)}"

            async with self._get_connection() as conn:
                cursor = await asyncio.get_event_loop().run_in_executor(
                    None, conn.execute, query, params
                )
                row = await asyncio.get_event_loop().run_in_executor(None, cursor.fetchone)
                return row[0] if row else 0

        except Exception as e:
            raise DataPersistenceError(
                f"Failed to count entities: {e}", operation="count", entity_type=self.table_name
            ) from e

    def _generate_id(self) -> str:
        """Generate a unique ID for an entity.

        Returns:
            Unique ID string
        """
        import uuid

        return str(uuid.uuid4())

    def _serialize_value(self, value: Any) -> Union[str, int, float, None]:
        """Serialize a value for database storage.

        Args:
            value: Value to serialize

        Returns:
            Serialized value
        """
        if value is None or isinstance(value, (str, int, float)):
            return value
        elif isinstance(value, (dict, list)):
            return json.dumps(value)
        elif isinstance(value, datetime):
            return value.isoformat()
        else:
            return str(value)

    def _deserialize_value(self, value: Any) -> Any:
        """Deserialize a value from database storage.

        Args:
            value: Value to deserialize

        Returns:
            Deserialized value
        """
        if isinstance(value, str):
            # Try to parse as JSON
            try:
                return json.loads(value)
            except (json.JSONDecodeError, ValueError):
                # Try to parse as datetime
                try:
                    return datetime.fromisoformat(value)
                except ValueError:
                    return value
        return value

    async def cleanup_old_records(self, days: int = 30) -> int:
        """Clean up old records from the repository.

        Args:
            days: Number of days to keep records

        Returns:
            Number of records deleted
        """
        try:
            cutoff_date = (datetime.utcnow() - timedelta(days=days)).isoformat()

            async with self._get_connection() as conn:
                query = f"DELETE FROM {self.table_name} WHERE created_at < ?"
                cursor = await asyncio.get_event_loop().run_in_executor(
                    None, conn.execute, query, (cutoff_date,)
                )
                await asyncio.get_event_loop().run_in_executor(None, conn.commit)

                deleted_count = cursor.rowcount
                self._logger.info(f"Cleaned up {deleted_count} old records from {self.table_name}")
                return deleted_count

        except Exception as e:
            raise DataPersistenceError(
                f"Failed to cleanup old records: {e}",
                operation="cleanup",
                entity_type=self.table_name,
            ) from e

    def dispose(self) -> None:
        """Dispose of repository resources."""
        self._connection_pool.close_all()
        self._logger.debug(f"Disposed repository for {self.table_name}")
