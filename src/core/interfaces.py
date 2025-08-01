"""Service Interfaces

Defines abstract base classes and interfaces for all services
to ensure proper separation of concerns and testability.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Optional


class IDisposable(ABC):
    """Interface for disposable resources."""

    @abstractmethod
    def dispose(self) -> None:
        """Dispose of resources."""


class IConfigurationService(ABC):
    """Interface for configuration management service."""

    @abstractmethod
    def get_api_key(self, service_name: str) -> Optional[str]:
        """Get API key for a specific service.

        Args:
            service_name: Name of the service (e.g., 'openweather', 'gemini')

        Returns:
            API key or None if not found
        """

    @abstractmethod
    def get_setting(self, key: str, default: Any = None) -> Any:
        """Get a configuration setting.

        Args:
            key: Configuration key
            default: Default value if key not found

        Returns:
            Configuration value or default
        """

    @abstractmethod
    def get_database_config(self) -> Dict[str, Any]:
        """Get database configuration.

        Returns:
            Database configuration dictionary
        """

    @abstractmethod
    def get_cache_config(self) -> Dict[str, Any]:
        """Get cache configuration.

        Returns:
            Cache configuration dictionary
        """

    @abstractmethod
    def validate_configuration(self) -> bool:
        """Validate the current configuration.

        Returns:
            True if configuration is valid, False otherwise
        """

    @abstractmethod
    def get_data_directory(self) -> Path:
        """Get the data directory path.

        Returns:
            Path to data directory
        """


class ILoggingService(ABC):
    """Interface for logging service."""

    @abstractmethod
    def log_info(self, message: str, **kwargs) -> None:
        """Log an info message.

        Args:
            message: Log message
            **kwargs: Additional context data
        """

    @abstractmethod
    def log_warning(self, message: str, **kwargs) -> None:
        """Log a warning message.

        Args:
            message: Log message
            **kwargs: Additional context data
        """

    @abstractmethod
    def log_error(self, message: str, exception: Optional[Exception] = None, **kwargs) -> None:
        """Log an error message.

        Args:
            message: Log message
            exception: Optional exception object
            **kwargs: Additional context data
        """

    @abstractmethod
    def log_debug(self, message: str, **kwargs) -> None:
        """Log a debug message.

        Args:
            message: Log message
            **kwargs: Additional context data
        """

    @abstractmethod
    def create_logger(self, name: str) -> Any:
        """Create a logger instance.

        Args:
            name: Logger name

        Returns:
            Logger instance
        """


class IWeatherService(ABC):
    """Interface for weather data service."""

    @abstractmethod
    async def get_current_weather(self, location: str, units: str = "metric") -> Dict[str, Any]:
        """Get current weather data for a location.

        Args:
            location: Location name or coordinates
            units: Temperature units (metric, imperial, kelvin)

        Returns:
            Current weather data dictionary
        """

    @abstractmethod
    async def get_weather_forecast(
        self, location: str, days: int = 5, units: str = "metric"
    ) -> Dict[str, Any]:
        """Get weather forecast for a location.

        Args:
            location: Location name or coordinates
            days: Number of forecast days
            units: Temperature units (metric, imperial, kelvin)

        Returns:
            Weather forecast data dictionary
        """

    @abstractmethod
    async def get_air_quality(self, lat: float, lon: float) -> Dict[str, Any]:
        """Get air quality data for coordinates.

        Args:
            lat: Latitude
            lon: Longitude

        Returns:
            Air quality data dictionary
        """

    @abstractmethod
    async def search_locations(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Search for locations by name.

        Args:
            query: Search query
            limit: Maximum number of results

        Returns:
            List of location dictionaries
        """

    @abstractmethod
    def is_available(self) -> bool:
        """Check if the weather service is available.

        Returns:
            True if service is available, False otherwise
        """


class IDataRepository(ABC):
    """Interface for data repository operations."""

    @abstractmethod
    async def save(self, entity: Any, entity_id: Optional[str] = None) -> str:
        """Save an entity to the repository.

        Args:
            entity: Entity to save
            entity_id: Optional entity ID

        Returns:
            Entity ID
        """

    @abstractmethod
    async def get_by_id(self, entity_id: str) -> Optional[Any]:
        """Get an entity by ID.

        Args:
            entity_id: Entity ID

        Returns:
            Entity or None if not found
        """

    @abstractmethod
    async def get_all(self, filters: Optional[Dict[str, Any]] = None) -> List[Any]:
        """Get all entities matching filters.

        Args:
            filters: Optional filter criteria

        Returns:
            List of entities
        """

    @abstractmethod
    async def update(self, entity_id: str, entity: Any) -> bool:
        """Update an entity.

        Args:
            entity_id: Entity ID
            entity: Updated entity

        Returns:
            True if updated successfully, False otherwise
        """

    @abstractmethod
    async def delete(self, entity_id: str) -> bool:
        """Delete an entity.

        Args:
            entity_id: Entity ID

        Returns:
            True if deleted successfully, False otherwise
        """

    @abstractmethod
    async def exists(self, entity_id: str) -> bool:
        """Check if an entity exists.

        Args:
            entity_id: Entity ID

        Returns:
            True if entity exists, False otherwise
        """

    @abstractmethod
    async def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """Count entities matching filters.

        Args:
            filters: Optional filter criteria

        Returns:
            Number of matching entities
        """


class ICacheService(ABC):
    """Interface for caching service."""

    @abstractmethod
    async def get(self, key: str) -> Optional[Any]:
        """Get a value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found
        """

    @abstractmethod
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set a value in cache.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds
        """

    @abstractmethod
    async def delete(self, key: str) -> bool:
        """Delete a value from cache.

        Args:
            key: Cache key

        Returns:
            True if deleted, False if key not found
        """

    @abstractmethod
    async def clear(self) -> None:
        """Clear all cached values."""

    @abstractmethod
    async def exists(self, key: str) -> bool:
        """Check if a key exists in cache.

        Args:
            key: Cache key

        Returns:
            True if key exists, False otherwise
        """


class INotificationService(ABC):
    """Interface for notification service."""

    @abstractmethod
    async def send_notification(self, title: str, message: str, level: str = "info") -> None:
        """Send a notification.

        Args:
            title: Notification title
            message: Notification message
            level: Notification level (info, warning, error)
        """

    @abstractmethod
    def subscribe(self, callback: callable) -> str:
        """Subscribe to notifications.

        Args:
            callback: Callback function to handle notifications

        Returns:
            Subscription ID
        """

    @abstractmethod
    def unsubscribe(self, subscription_id: str) -> bool:
        """Unsubscribe from notifications.

        Args:
            subscription_id: Subscription ID

        Returns:
            True if unsubscribed successfully, False otherwise
        """
