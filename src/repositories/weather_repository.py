"""Weather Repository

Implements weather data persistence with SQLite storage,
caching with TTL, and weather-specific operations.
"""

import asyncio
import json
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from ..core.exceptions import CacheError, DataPersistenceError
from .base_repository import BaseRepository


@dataclass
class WeatherCacheEntry:
    """Weather cache entry with TTL support."""

    data: Dict[str, Any]
    location: str
    data_type: str  # 'current', 'forecast', 'air_quality'
    expires_at: datetime
    created_at: datetime

    def is_expired(self) -> bool:
        """Check if cache entry is expired."""
        return datetime.utcnow() > self.expires_at

    def is_valid(self) -> bool:
        """Check if cache entry is valid (not expired)."""
        return not self.is_expired()


class WeatherRepository(BaseRepository[WeatherCacheEntry]):
    """Repository for weather data with caching and TTL support."""

    def __init__(self, database_path: str, cache_ttl_seconds: int = 300):
        """Initialize weather repository.

        Args:
            database_path: Path to SQLite database
            cache_ttl_seconds: Cache TTL in seconds (default: 5 minutes)
        """
        super().__init__(database_path, "weather_cache")
        self.cache_ttl_seconds = cache_ttl_seconds
        self._logger = logging.getLogger(__name__)

    async def _initialize_schema(self) -> None:
        """Initialize database schema for weather cache."""
        try:
            async with self._get_connection() as conn:
                # Create weather cache table
                await asyncio.get_event_loop().run_in_executor(
                    None,
                    conn.execute,
                    """
                    CREATE TABLE IF NOT EXISTS weather_cache (
                        id TEXT PRIMARY KEY,
                        location TEXT NOT NULL,
                        data_type TEXT NOT NULL,
                        data TEXT NOT NULL,
                        expires_at TEXT NOT NULL,
                        created_at TEXT NOT NULL,
                        updated_at TEXT NOT NULL
                    )
                    """,
                )

                # Create indexes for better performance
                await asyncio.get_event_loop().run_in_executor(
                    None,
                    conn.execute,
                    "CREATE INDEX IF NOT EXISTS idx_weather_location_type ON weather_cache(location, data_type)",
                )

                await asyncio.get_event_loop().run_in_executor(
                    None,
                    conn.execute,
                    "CREATE INDEX IF NOT EXISTS idx_weather_expires ON weather_cache(expires_at)",
                )

                await asyncio.get_event_loop().run_in_executor(None, conn.commit)

                self._logger.debug("Weather repository schema initialized")

        except Exception as e:
            raise DataPersistenceError(
                f"Failed to initialize weather repository schema: {e}",
                operation="schema_init",
                entity_type="weather_cache",
            ) from e

    def _serialize_entity(self, entity: WeatherCacheEntry) -> Dict[str, Any]:
        """Serialize weather cache entry to dictionary.

        Args:
            entity: Weather cache entry to serialize

        Returns:
            Dictionary representation
        """
        return {
            "location": entity.location,
            "data_type": entity.data_type,
            "data": json.dumps(entity.data),
            "expires_at": entity.expires_at.isoformat(),
            "created_at": entity.created_at.isoformat(),
        }

    def _deserialize_entity(self, data: Dict[str, Any]) -> WeatherCacheEntry:
        """Deserialize dictionary to weather cache entry.

        Args:
            data: Dictionary data from database

        Returns:
            Weather cache entry instance
        """
        return WeatherCacheEntry(
            data=json.loads(data["data"]) if isinstance(data["data"], str) else data["data"],
            location=data["location"],
            data_type=data["data_type"],
            expires_at=(
                datetime.fromisoformat(data["expires_at"])
                if isinstance(data["expires_at"], str)
                else data["expires_at"]
            ),
            created_at=(
                datetime.fromisoformat(data["created_at"])
                if isinstance(data["created_at"], str)
                else data["created_at"]
            ),
        )

    async def save_weather(
        self, location: str, weather_data: Dict[str, Any], data_type: str = "current"
    ) -> str:
        """Save weather data to cache.

        Args:
            location: Location identifier
            weather_data: Weather data to cache
            data_type: Type of weather data ('current', 'forecast', 'air_quality')

        Returns:
            Cache entry ID
        """
        try:
            # Create cache entry
            now = datetime.utcnow()
            expires_at = now + timedelta(seconds=self.cache_ttl_seconds)

            cache_entry = WeatherCacheEntry(
                data=weather_data,
                location=location.lower().strip(),
                data_type=data_type,
                expires_at=expires_at,
                created_at=now,
            )

            # Generate cache key
            cache_key = self._generate_cache_key(location, data_type)

            # Save to database
            entry_id = await self.save(cache_entry, cache_key)

            self._logger.debug(
                f"Saved weather data for {location} ({data_type}) with TTL {self.cache_ttl_seconds}s"
            )
            return entry_id

        except Exception as e:
            raise CacheError(
                f"Failed to save weather data: {e}",
                cache_key=f"{location}:{data_type}",
                operation="save",
            ) from e

    async def get_weather(
        self, location: str, data_type: str = "current"
    ) -> Optional[Dict[str, Any]]:
        """Get cached weather data for location.

        Args:
            location: Location identifier
            data_type: Type of weather data ('current', 'forecast', 'air_quality')

        Returns:
            Cached weather data or None if not found/expired
        """
        try:
            cache_key = self._generate_cache_key(location, data_type)
            cache_entry = await self.get_by_id(cache_key)

            if cache_entry is None:
                self._logger.debug(f"No cached weather data found for {location} ({data_type})")
                return None

            if cache_entry.is_expired():
                self._logger.debug(f"Cached weather data expired for {location} ({data_type})")
                # Clean up expired entry
                await self.delete(cache_key)
                return None

            self._logger.debug(f"Retrieved cached weather data for {location} ({data_type})")
            return cache_entry.data

        except Exception as e:
            self._logger.warning(f"Failed to get cached weather data: {e}")
            return None

    async def get_history(
        self, location: str, days: int = 7, data_type: str = "current"
    ) -> List[Dict[str, Any]]:
        """Get weather history for location.

        Args:
            location: Location identifier
            days: Number of days of history to retrieve
            data_type: Type of weather data

        Returns:
            List of historical weather data
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)

            # Get all entries for location and data type within time range
            filters = {"location": location.lower().strip(), "data_type": data_type}

            entries = await self.get_all(filters)

            # Filter by date and sort by creation time
            history = []
            for entry in entries:
                if entry.created_at >= cutoff_date:
                    history.append(
                        {
                            "data": entry.data,
                            "timestamp": entry.created_at.isoformat(),
                            "location": entry.location,
                        }
                    )

            # Sort by timestamp (newest first)
            history.sort(key=lambda x: x["timestamp"], reverse=True)

            self._logger.debug(
                f"Retrieved {len(history)} historical entries for {location} ({data_type})"
            )
            return history

        except Exception as e:
            raise DataPersistenceError(
                f"Failed to get weather history: {e}",
                operation="get_history",
                entity_type="weather_cache",
            ) from e

    async def clear_expired_cache(self) -> int:
        """Clear expired cache entries.

        Returns:
            Number of entries cleared
        """
        try:
            now = datetime.utcnow().isoformat()

            async with self._get_connection() as conn:
                query = f"DELETE FROM {self.table_name} WHERE expires_at < ?"
                cursor = await asyncio.get_event_loop().run_in_executor(
                    None, conn.execute, query, (now,)
                )
                await asyncio.get_event_loop().run_in_executor(None, conn.commit)

                cleared_count = cursor.rowcount
                self._logger.info(f"Cleared {cleared_count} expired weather cache entries")
                return cleared_count

        except Exception as e:
            raise CacheError(
                f"Failed to clear expired cache: {e}", operation="clear_expired"
            ) from e

    async def clear_location_cache(self, location: str) -> int:
        """Clear all cache entries for a specific location.

        Args:
            location: Location identifier

        Returns:
            Number of entries cleared
        """
        try:
            location_key = location.lower().strip()

            async with self._get_connection() as conn:
                query = f"DELETE FROM {self.table_name} WHERE location = ?"
                cursor = await asyncio.get_event_loop().run_in_executor(
                    None, conn.execute, query, (location_key,)
                )
                await asyncio.get_event_loop().run_in_executor(None, conn.commit)

                cleared_count = cursor.rowcount
                self._logger.debug(f"Cleared {cleared_count} cache entries for location {location}")
                return cleared_count

        except Exception as e:
            raise CacheError(
                f"Failed to clear location cache: {e}",
                cache_key=location,
                operation="clear_location",
            ) from e

    async def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics.

        Returns:
            Dictionary with cache statistics
        """
        try:
            async with self._get_connection() as conn:
                # Total entries
                cursor = await asyncio.get_event_loop().run_in_executor(
                    None, conn.execute, f"SELECT COUNT(*) FROM {self.table_name}"
                )
                total_entries = (
                    await asyncio.get_event_loop().run_in_executor(None, cursor.fetchone)
                )[0]

                # Expired entries
                now = datetime.utcnow().isoformat()
                cursor = await asyncio.get_event_loop().run_in_executor(
                    None,
                    conn.execute,
                    f"SELECT COUNT(*) FROM {self.table_name} WHERE expires_at < ?",
                    (now,),
                )
                expired_entries = (
                    await asyncio.get_event_loop().run_in_executor(None, cursor.fetchone)
                )[0]

                # Entries by type
                cursor = await asyncio.get_event_loop().run_in_executor(
                    None,
                    conn.execute,
                    f"SELECT data_type, COUNT(*) FROM {self.table_name} GROUP BY data_type",
                )
                type_counts = dict(
                    await asyncio.get_event_loop().run_in_executor(None, cursor.fetchall)
                )

                # Unique locations
                cursor = await asyncio.get_event_loop().run_in_executor(
                    None, conn.execute, f"SELECT COUNT(DISTINCT location) FROM {self.table_name}"
                )
                unique_locations = (
                    await asyncio.get_event_loop().run_in_executor(None, cursor.fetchone)
                )[0]

                return {
                    "total_entries": total_entries,
                    "expired_entries": expired_entries,
                    "valid_entries": total_entries - expired_entries,
                    "entries_by_type": type_counts,
                    "unique_locations": unique_locations,
                    "cache_ttl_seconds": self.cache_ttl_seconds,
                }

        except Exception as e:
            raise DataPersistenceError(
                f"Failed to get cache stats: {e}",
                operation="get_stats",
                entity_type="weather_cache",
            ) from e

    def _generate_cache_key(self, location: str, data_type: str) -> str:
        """Generate cache key for location and data type.

        Args:
            location: Location identifier
            data_type: Type of weather data

        Returns:
            Cache key string
        """
        import hashlib

        # Normalize location
        location_key = location.lower().strip()

        # Create hash for consistent key generation
        key_string = f"{location_key}:{data_type}"
        key_hash = hashlib.md5(key_string.encode()).hexdigest()[:16]

        return f"weather_{data_type}_{key_hash}"

    async def update_cache_ttl(self, new_ttl_seconds: int) -> None:
        """Update cache TTL for future entries.

        Args:
            new_ttl_seconds: New TTL in seconds
        """
        self.cache_ttl_seconds = new_ttl_seconds
        self._logger.info(f"Updated cache TTL to {new_ttl_seconds} seconds")

    async def refresh_cache_entry(self, location: str, data_type: str) -> bool:
        """Refresh cache entry expiration time.

        Args:
            location: Location identifier
            data_type: Type of weather data

        Returns:
            True if entry was refreshed, False if not found
        """
        try:
            cache_key = self._generate_cache_key(location, data_type)
            cache_entry = await self.get_by_id(cache_key)

            if cache_entry is None:
                return False

            # Update expiration time
            cache_entry.expires_at = datetime.utcnow() + timedelta(seconds=self.cache_ttl_seconds)

            # Save updated entry
            await self.update(cache_key, cache_entry)

            self._logger.debug(f"Refreshed cache entry for {location} ({data_type})")
            return True

        except Exception as e:
            self._logger.warning(f"Failed to refresh cache entry: {e}")
            return False
