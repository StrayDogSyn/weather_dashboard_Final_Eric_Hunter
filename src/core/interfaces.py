#!/usr/bin/env python3
"""
Core Interfaces for Dependency Injection

This module defines all the interfaces (abstract base classes) that enable
dependency injection throughout the application. Following interface segregation
principle, each interface is focused on a specific responsibility.

Author: Eric Hunter (Cortana Builder Agent)
Version: 1.0.0 (Dependency Injection Implementation)
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Union
from datetime import datetime
from dataclasses import dataclass
from enum import Enum


# ============================================================================
# Data Transfer Objects (DTOs)
# ============================================================================

@dataclass
class WeatherDataDTO:
    """Data transfer object for weather information."""
    location: str
    temperature: float
    feels_like: float
    humidity: int
    pressure: float
    description: str
    icon: str
    wind_speed: float
    wind_direction: int
    visibility: Optional[float] = None
    uv_index: Optional[float] = None
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


@dataclass
class JournalEntryDTO:
    """Data transfer object for journal entries."""
    id: Optional[int]
    content: str
    location: Optional[str]
    weather_data: Optional[str]
    created_at: datetime


@dataclass
class UserPreferenceDTO:
    """Data transfer object for user preferences."""
    key: str
    value: str
    updated_at: datetime


class ServiceLifetime(Enum):
    """Service lifetime enumeration for dependency injection."""
    SINGLETON = "singleton"
    TRANSIENT = "transient"
    SCOPED = "scoped"


# ============================================================================
# Core Service Interfaces
# ============================================================================

class IWeatherService(ABC):
    """Interface for weather data services."""
    
    @abstractmethod
    def get_current_weather(self, location: str, use_cache: bool = True) -> Optional[WeatherDataDTO]:
        """Get current weather data for a location.
        
        Args:
            location: Location name or coordinates
            use_cache: Whether to use cached data if available
            
        Returns:
            Weather data or None if unavailable
        """
        pass
    
    @abstractmethod
    def get_forecast(self, location: str, days: int = 5) -> List[WeatherDataDTO]:
        """Get weather forecast for a location.
        
        Args:
            location: Location name or coordinates
            days: Number of days to forecast
            
        Returns:
            List of forecast data
        """
        pass
    
    @abstractmethod
    def test_connection(self) -> bool:
        """Test if the weather service is available.
        
        Returns:
            True if service is available, False otherwise
        """
        pass
    
    @abstractmethod
    def get_provider_status(self) -> Dict[str, Any]:
        """Get status of weather data providers.
        
        Returns:
            Dictionary containing provider status information
        """
        pass


class IDatabase(ABC):
    """Interface for database operations."""
    
    @abstractmethod
    def save_weather_data(self, weather_data: WeatherDataDTO) -> int:
        """Save weather data to database.
        
        Args:
            weather_data: Weather data to save
            
        Returns:
            ID of the saved record
        """
        pass
    
    @abstractmethod
    def get_recent_weather(self, limit: int = 10) -> List[WeatherDataDTO]:
        """Get recent weather data records.
        
        Args:
            limit: Maximum number of records to return
            
        Returns:
            List of weather data records
        """
        pass
    
    @abstractmethod
    def get_weather_by_location(self, location: str, limit: int = 5) -> List[WeatherDataDTO]:
        """Get weather data for specific location.
        
        Args:
            location: Location name to search for
            limit: Maximum number of records to return
            
        Returns:
            List of weather data records
        """
        pass
    
    @abstractmethod
    def save_journal_entry(self, entry: JournalEntryDTO) -> int:
        """Save a journal entry.
        
        Args:
            entry: Journal entry to save
            
        Returns:
            ID of the saved entry
        """
        pass
    
    @abstractmethod
    def get_journal_entries(self, limit: int = 20) -> List[JournalEntryDTO]:
        """Get recent journal entries.
        
        Args:
            limit: Maximum number of entries to return
            
        Returns:
            List of journal entries
        """
        pass
    
    @abstractmethod
    def set_preference(self, preference: UserPreferenceDTO) -> None:
        """Set a user preference.
        
        Args:
            preference: User preference to set
        """
        pass
    
    @abstractmethod
    def get_preference(self, key: str) -> Optional[UserPreferenceDTO]:
        """Get a user preference.
        
        Args:
            key: Preference key
            
        Returns:
            User preference or None if not found
        """
        pass


class ICacheService(ABC):
    """Interface for caching services."""
    
    @abstractmethod
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found
        """
        pass
    
    @abstractmethod
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set value in cache.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds
        """
        pass
    
    @abstractmethod
    def delete(self, key: str) -> bool:
        """Delete value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            True if key was deleted, False if not found
        """
        pass
    
    @abstractmethod
    def clear(self) -> None:
        """Clear all cached values."""
        pass


class IConfigurationService(ABC):
    """Interface for configuration management."""
    
    @abstractmethod
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value.
        
        Args:
            key: Configuration key
            default: Default value if key not found
            
        Returns:
            Configuration value
        """
        pass
    
    @abstractmethod
    def set(self, key: str, value: Any) -> None:
        """Set configuration value.
        
        Args:
            key: Configuration key
            value: Configuration value
        """
        pass
    
    @abstractmethod
    def get_section(self, section: str) -> Dict[str, Any]:
        """Get entire configuration section.
        
        Args:
            section: Section name
            
        Returns:
            Dictionary of configuration values
        """
        pass


class ILoggingService(ABC):
    """Interface for logging services."""
    
    @abstractmethod
    def debug(self, message: str, **kwargs) -> None:
        """Log debug message."""
        pass
    
    @abstractmethod
    def info(self, message: str, **kwargs) -> None:
        """Log info message."""
        pass
    
    @abstractmethod
    def warning(self, message: str, **kwargs) -> None:
        """Log warning message."""
        pass
    
    @abstractmethod
    def error(self, message: str, **kwargs) -> None:
        """Log error message."""
        pass
    
    @abstractmethod
    def critical(self, message: str, **kwargs) -> None:
        """Log critical message."""
        pass


class IGeminiService(ABC):
    """Interface for AI/Gemini services."""
    
    @abstractmethod
    def generate_activity_suggestions(self, weather_data: WeatherDataDTO) -> List[str]:
        """Generate activity suggestions based on weather.
        
        Args:
            weather_data: Current weather data
            
        Returns:
            List of activity suggestions
        """
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if the service is available.
        
        Returns:
            True if service is available, False otherwise
        """
        pass


class IGitHubService(ABC):
    """Interface for GitHub integration services."""
    
    @abstractmethod
    def is_connected(self) -> bool:
        """Check if connected to GitHub.
        
        Returns:
            True if connected, False otherwise
        """
        pass
    
    @abstractmethod
    def export_data(self, data: Dict[str, Any]) -> bool:
        """Export data to GitHub.
        
        Args:
            data: Data to export
            
        Returns:
            True if successful, False otherwise
        """
        pass


class ISpotifyService(ABC):
    """Interface for Spotify integration services."""
    
    @abstractmethod
    def get_weather_playlist(self, weather_condition: str) -> Optional[Dict[str, Any]]:
        """Get playlist recommendations based on weather.
        
        Args:
            weather_condition: Current weather condition
            
        Returns:
            Playlist information or None if unavailable
        """
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if the service is available.
        
        Returns:
            True if service is available, False otherwise
        """
        pass


# ============================================================================
# Dependency Injection Container Interface
# ============================================================================

class IDependencyContainer(ABC):
    """Interface for dependency injection container."""
    
    @abstractmethod
    def register_singleton(self, interface_type: type, implementation_type: type) -> None:
        """Register a singleton service.
        
        Args:
            interface_type: Interface type
            implementation_type: Implementation type
        """
        pass
    
    @abstractmethod
    def register_transient(self, interface_type: type, implementation_type: type) -> None:
        """Register a transient service.
        
        Args:
            interface_type: Interface type
            implementation_type: Implementation type
        """
        pass
    
    @abstractmethod
    def register_instance(self, interface_type: type, instance: Any) -> None:
        """Register a specific instance.
        
        Args:
            interface_type: Interface type
            instance: Instance to register
        """
        pass
    
    @abstractmethod
    def resolve(self, interface_type: type) -> Any:
        """Resolve a service instance.
        
        Args:
            interface_type: Interface type to resolve
            
        Returns:
            Service instance
        """
        pass
    
    @abstractmethod
    def is_registered(self, interface_type: type) -> bool:
        """Check if a service is registered.
        
        Args:
            interface_type: Interface type to check
            
        Returns:
            True if registered, False otherwise
        """
        pass