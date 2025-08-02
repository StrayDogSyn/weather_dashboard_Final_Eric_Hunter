"""Base Repository Pattern Implementation

Defines abstract base class for all repository implementations.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, Generic, List, Optional, TypeVar, Union

# Generic type for entity models
T = TypeVar("T")
K = TypeVar("K")  # Key type (usually str or int)


class BaseRepository(ABC, Generic[T, K]):
    """Abstract base repository class defining common data access patterns."""

    def __init__(self, connection=None):
        """Initialize repository with optional database connection."""
        self._connection = connection
        self._cache = {}  # Simple in-memory cache
        self._cache_ttl = {}  # Cache time-to-live tracking
        self._default_cache_duration = 300  # 5 minutes default

    @abstractmethod
    async def get_by_id(self, entity_id: K) -> Optional[T]:
        """Retrieve entity by ID."""

    @abstractmethod
    async def get_all(self, limit: Optional[int] = None, offset: int = 0) -> List[T]:
        """Retrieve all entities with optional pagination."""

    @abstractmethod
    async def create(self, entity: T) -> T:
        """Create new entity."""

    @abstractmethod
    async def update(self, entity_id: K, entity: T) -> Optional[T]:
        """Update existing entity."""

    @abstractmethod
    async def delete(self, entity_id: K) -> bool:
        """Delete entity by ID."""

    @abstractmethod
    async def exists(self, entity_id: K) -> bool:
        """Check if entity exists."""

    async def find_by_criteria(self, criteria: Dict[str, Any]) -> List[T]:
        """Find entities matching criteria. Default implementation returns empty list."""
        return []

    async def count(self, criteria: Optional[Dict[str, Any]] = None) -> int:
        """Count entities matching criteria. Default implementation returns 0."""
        return 0

    # Cache management methods
    def _get_cache_key(self, key: Union[str, K]) -> str:
        """Generate cache key."""
        return f"{self.__class__.__name__}:{key}"

    def _is_cache_valid(self, cache_key: str) -> bool:
        """Check if cached item is still valid."""
        if cache_key not in self._cache_ttl:
            return False
        return datetime.now().timestamp() < self._cache_ttl[cache_key]

    def _get_from_cache(self, key: Union[str, K]) -> Optional[T]:
        """Get item from cache if valid."""
        cache_key = self._get_cache_key(key)
        if cache_key in self._cache and self._is_cache_valid(cache_key):
            return self._cache[cache_key]
        return None

    def _set_cache(self, key: Union[str, K], value: T, ttl_seconds: Optional[int] = None) -> None:
        """Set item in cache with TTL."""
        cache_key = self._get_cache_key(key)
        self._cache[cache_key] = value

        ttl = ttl_seconds or self._default_cache_duration
        self._cache_ttl[cache_key] = datetime.now().timestamp() + ttl

    def _invalidate_cache(self, key: Union[str, K]) -> None:
        """Remove item from cache."""
        cache_key = self._get_cache_key(key)
        self._cache.pop(cache_key, None)
        self._cache_ttl.pop(cache_key, None)

    def _clear_cache(self) -> None:
        """Clear all cached items."""
        self._cache.clear()
        self._cache_ttl.clear()

    def _cleanup_expired_cache(self) -> None:
        """Remove expired items from cache."""
        current_time = datetime.now().timestamp()
        expired_keys = [key for key, expiry in self._cache_ttl.items() if current_time >= expiry]

        for key in expired_keys:
            self._cache.pop(key, None)
            self._cache_ttl.pop(key, None)

    # Batch operations
    async def create_many(self, entities: List[T]) -> List[T]:
        """Create multiple entities. Default implementation creates one by one."""
        results = []
        for entity in entities:
            result = await self.create(entity)
            results.append(result)
        return results

    async def update_many(self, updates: Dict[K, T]) -> List[T]:
        """Update multiple entities. Default implementation updates one by one."""
        results = []
        for entity_id, entity in updates.items():
            result = await self.update(entity_id, entity)
            if result:
                results.append(result)
        return results

    async def delete_many(self, entity_ids: List[K]) -> int:
        """Delete multiple entities. Returns count of deleted entities."""
        deleted_count = 0
        for entity_id in entity_ids:
            if await self.delete(entity_id):
                deleted_count += 1
        return deleted_count

    # Transaction support (to be implemented by concrete repositories)
    async def begin_transaction(self):
        """Begin database transaction. Override in concrete implementations."""

    async def commit_transaction(self):
        """Commit database transaction. Override in concrete implementations."""

    async def rollback_transaction(self):
        """Rollback database transaction. Override in concrete implementations."""

    # Health check
    async def health_check(self) -> bool:
        """Check repository health. Override in concrete implementations."""
        return True

    # Cleanup resources
    async def close(self):
        """Close repository and cleanup resources."""
        self._clear_cache()
        if hasattr(self._connection, "close"):
            await self._connection.close()


class ReadOnlyRepository(BaseRepository[T, K]):
    """Read-only repository base class for immutable data sources."""

    async def create(self, entity: T) -> T:
        """Create operation not supported in read-only repository."""
        raise NotImplementedError("Create operation not supported in read-only repository")

    async def update(self, entity_id: K, entity: T) -> Optional[T]:
        """Update operation not supported in read-only repository."""
        raise NotImplementedError("Update operation not supported in read-only repository")

    async def delete(self, entity_id: K) -> bool:
        """Delete operation not supported in read-only repository."""
        raise NotImplementedError("Delete operation not supported in read-only repository")

    async def create_many(self, entities: List[T]) -> List[T]:
        """Batch create not supported in read-only repository."""
        raise NotImplementedError("Create operations not supported in read-only repository")

    async def update_many(self, updates: Dict[K, T]) -> List[T]:
        """Batch update not supported in read-only repository."""
        raise NotImplementedError("Update operations not supported in read-only repository")

    async def delete_many(self, entity_ids: List[K]) -> int:
        """Batch delete not supported in read-only repository."""
        raise NotImplementedError("Delete operations not supported in read-only repository")


class InMemoryRepository(BaseRepository[T, K]):
    """Simple in-memory repository implementation for testing and caching."""

    def __init__(self):
        super().__init__()
        self._data: Dict[K, T] = {}
        self._next_id = 1

    async def get_by_id(self, entity_id: K) -> Optional[T]:
        """Get entity by ID from memory."""
        return self._data.get(entity_id)

    async def get_all(self, limit: Optional[int] = None, offset: int = 0) -> List[T]:
        """Get all entities from memory with pagination."""
        entities = list(self._data.values())

        if offset > 0:
            entities = entities[offset:]

        if limit is not None:
            entities = entities[:limit]

        return entities

    async def create(self, entity: T) -> T:
        """Create entity in memory."""
        # If entity has an ID attribute, use it; otherwise generate one
        if hasattr(entity, "id") and getattr(entity, "id") is not None:
            entity_id = getattr(entity, "id")
        else:
            entity_id = self._next_id
            self._next_id += 1
            if hasattr(entity, "id"):
                setattr(entity, "id", entity_id)

        self._data[entity_id] = entity
        return entity

    async def update(self, entity_id: K, entity: T) -> Optional[T]:
        """Update entity in memory."""
        if entity_id in self._data:
            self._data[entity_id] = entity
            return entity
        return None

    async def delete(self, entity_id: K) -> bool:
        """Delete entity from memory."""
        if entity_id in self._data:
            del self._data[entity_id]
            return True
        return False

    async def exists(self, entity_id: K) -> bool:
        """Check if entity exists in memory."""
        return entity_id in self._data

    async def count(self, criteria: Optional[Dict[str, Any]] = None) -> int:
        """Count entities in memory."""
        return len(self._data)

    def clear(self):
        """Clear all data from memory."""
        self._data.clear()
        self._next_id = 1
