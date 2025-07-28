# 📚 API Reference

## Overview

This document provides comprehensive API reference for all service interfaces, data transfer objects (DTOs), error types, and configuration options in the Weather Dashboard project.

## Table of Contents

1. [Service Interfaces](#service-interfaces)
2. [Data Transfer Objects (DTOs)](#data-transfer-objects-dtos)
3. [Error Types](#error-types)
4. [Configuration Reference](#configuration-reference)
5. [Dependency Injection API](#dependency-injection-api)
6. [Utility Functions](#utility-functions)

## Service Interfaces

### IWeatherService

Interface for weather data operations.

```python
from abc import ABC, abstractmethod
from typing import List, Optional
from src.core.dtos import WeatherDataDTO

class IWeatherService(ABC):
    """Interface for weather service operations."""
    
    @abstractmethod
    def get_current_weather(self, location: str) -> WeatherDataDTO:
        """Get current weather data for specified location.
        
        Args:
            location: City name or coordinates (e.g., "London" or "51.5074,-0.1278")
            
        Returns:
            WeatherDataDTO: Current weather information
            
        Raises:
            ValidationError: If location is invalid
            ExternalServiceError: If weather API is unavailable
            NetworkError: If network request fails
        """
        pass
    
    @abstractmethod
    def get_forecast(self, location: str, days: int = 5) -> List[WeatherDataDTO]:
        """Get weather forecast for specified location.
        
        Args:
            location: City name or coordinates
            days: Number of forecast days (1-5, default: 5)
            
        Returns:
            List[WeatherDataDTO]: Weather forecast data
            
        Raises:
            ValidationError: If location or days parameter is invalid
            ExternalServiceError: If weather API is unavailable
        """
        pass
    
    @abstractmethod
    def get_weather_history(self, location: str, start_date: str, end_date: str) -> List[WeatherDataDTO]:
        """Get historical weather data.
        
        Args:
            location: City name or coordinates
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            
        Returns:
            List[WeatherDataDTO]: Historical weather data
        """
        pass
```

### IDatabase

Interface for database operations.

```python
class IDatabase(ABC):
    """Interface for database operations."""
    
    @abstractmethod
    def connect(self) -> bool:
        """Establish database connection.
        
        Returns:
            bool: True if connection successful
            
        Raises:
            DatabaseError: If connection fails
        """
        pass
    
    @abstractmethod
    def execute_query(self, query: str, parameters: Optional[dict] = None) -> List[dict]:
        """Execute SQL query.
        
        Args:
            query: SQL query string
            parameters: Query parameters (optional)
            
        Returns:
            List[dict]: Query results
            
        Raises:
            DatabaseError: If query execution fails
            ValidationError: If query is invalid
        """
        pass
    
    @abstractmethod
    def save_weather_data(self, weather_data: WeatherDataDTO) -> bool:
        """Save weather data to database.
        
        Args:
            weather_data: Weather data to save
            
        Returns:
            bool: True if save successful
        """
        pass
    
    @abstractmethod
    def get_weather_history(self, location: str, limit: int = 100) -> List[WeatherDataDTO]:
        """Get weather history from database.
        
        Args:
            location: Location to query
            limit: Maximum number of records
            
        Returns:
            List[WeatherDataDTO]: Historical weather data
        """
        pass
    
    @abstractmethod
    def close(self) -> None:
        """Close database connection."""
        pass
```

### ICacheService

Interface for caching operations.

```python
class ICacheService(ABC):
    """Interface for cache operations."""
    
    @abstractmethod
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            Optional[Any]: Cached value or None if not found
        """
        pass
    
    @abstractmethod
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set value in cache.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds (optional)
        """
        pass
    
    @abstractmethod
    def delete(self, key: str) -> bool:
        """Delete value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            bool: True if key was deleted
        """
        pass
    
    @abstractmethod
    def clear(self) -> None:
        """Clear all cache entries."""
        pass
    
    @abstractmethod
    def exists(self, key: str) -> bool:
        """Check if key exists in cache.
        
        Args:
            key: Cache key
            
        Returns:
            bool: True if key exists
        """
        pass
```

### IConfigurationService

Interface for configuration management.

```python
class IConfigurationService(ABC):
    """Interface for configuration service."""
    
    @abstractmethod
    def get(self, key: str, default: Optional[Any] = None) -> Any:
        """Get configuration value.
        
        Args:
            key: Configuration key
            default: Default value if key not found
            
        Returns:
            Any: Configuration value
        """
        pass
    
    @abstractmethod
    def get_section(self, section: str) -> dict:
        """Get configuration section.
        
        Args:
            section: Section name
            
        Returns:
            dict: Configuration section
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
    def reload(self) -> None:
        """Reload configuration from source."""
        pass
```

### ILoggingService

Interface for logging operations.

```python
class ILoggingService(ABC):
    """Interface for logging service."""
    
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
```

### IGeminiService

Interface for Google Gemini AI operations.

```python
class IGeminiService(ABC):
    """Interface for Gemini AI service."""
    
    @abstractmethod
    def generate_content(self, prompt: str) -> str:
        """Generate content using Gemini AI.
        
        Args:
            prompt: Input prompt for content generation
            
        Returns:
            str: Generated content
            
        Raises:
            ExternalServiceError: If Gemini API is unavailable
            ValidationError: If prompt is invalid
        """
        pass
    
    @abstractmethod
    def analyze_weather_data(self, weather_data: WeatherDataDTO) -> str:
        """Analyze weather data and provide insights.
        
        Args:
            weather_data: Weather data to analyze
            
        Returns:
            str: Weather analysis and insights
        """
        pass
```

### IGitHubService

Interface for GitHub operations.

```python
class IGitHubService(ABC):
    """Interface for GitHub service."""
    
    @abstractmethod
    def export_data(self, data: dict, filename: str) -> bool:
        """Export data to GitHub repository.
        
        Args:
            data: Data to export
            filename: Target filename
            
        Returns:
            bool: True if export successful
            
        Raises:
            ExternalServiceError: If GitHub API is unavailable
            ValidationError: If data or filename is invalid
        """
        pass
    
    @abstractmethod
    def get_repository_info(self) -> dict:
        """Get repository information.
        
        Returns:
            dict: Repository information
        """
        pass
```

### ISpotifyService

Interface for Spotify operations.

```python
class ISpotifyService(ABC):
    """Interface for Spotify service."""
    
    @abstractmethod
    def get_weather_playlist(self, weather_condition: str) -> dict:
        """Get playlist based on weather condition.
        
        Args:
            weather_condition: Current weather condition
            
        Returns:
            dict: Playlist information
            
        Raises:
            ExternalServiceError: If Spotify API is unavailable
        """
        pass
    
    @abstractmethod
    def search_tracks(self, query: str, limit: int = 10) -> List[dict]:
        """Search for tracks.
        
        Args:
            query: Search query
            limit: Maximum number of results
            
        Returns:
            List[dict]: Track information
        """
        pass
```

## Data Transfer Objects (DTOs)

### WeatherDataDTO

Data transfer object for weather information.

```python
from dataclasses import dataclass
from typing import Optional
from datetime import datetime

@dataclass(frozen=True)
class WeatherDataDTO:
    """Weather data transfer object."""
    
    location: str
    temperature: float
    humidity: int
    description: str
    timestamp: datetime
    feels_like: Optional[float] = None
    pressure: Optional[int] = None
    wind_speed: Optional[float] = None
    wind_direction: Optional[int] = None
    visibility: Optional[float] = None
    uv_index: Optional[float] = None
    
    def __post_init__(self):
        """Validate weather data after initialization."""
        if not self.location or not self.location.strip():
            raise ValueError("Location cannot be empty")
        
        if not isinstance(self.temperature, (int, float)):
            raise ValueError("Temperature must be a number")
        
        if not isinstance(self.humidity, int) or not (0 <= self.humidity <= 100):
            raise ValueError("Humidity must be an integer between 0 and 100")
        
        if not self.description or not self.description.strip():
            raise ValueError("Description cannot be empty")
    
    @property
    def temperature_celsius(self) -> float:
        """Get temperature in Celsius."""
        return self.temperature
    
    @property
    def temperature_fahrenheit(self) -> float:
        """Get temperature in Fahrenheit."""
        return (self.temperature * 9/5) + 32
    
    @property
    def is_hot(self) -> bool:
        """Check if temperature is considered hot (>25°C)."""
        return self.temperature > 25
    
    @property
    def is_cold(self) -> bool:
        """Check if temperature is considered cold (<10°C)."""
        return self.temperature < 10
    
    def to_dict(self) -> dict:
        """Convert to dictionary representation."""
        return {
            'location': self.location,
            'temperature': self.temperature,
            'humidity': self.humidity,
            'description': self.description,
            'timestamp': self.timestamp.isoformat(),
            'feels_like': self.feels_like,
            'pressure': self.pressure,
            'wind_speed': self.wind_speed,
            'wind_direction': self.wind_direction,
            'visibility': self.visibility,
            'uv_index': self.uv_index
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'WeatherDataDTO':
        """Create instance from dictionary."""
        timestamp = data.get('timestamp')
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp)
        
        return cls(
            location=data['location'],
            temperature=data['temperature'],
            humidity=data['humidity'],
            description=data['description'],
            timestamp=timestamp,
            feels_like=data.get('feels_like'),
            pressure=data.get('pressure'),
            wind_speed=data.get('wind_speed'),
            wind_direction=data.get('wind_direction'),
            visibility=data.get('visibility'),
            uv_index=data.get('uv_index')
        )
```

### ConfigurationDTO

Data transfer object for configuration settings.

```python
@dataclass(frozen=True)
class ConfigurationDTO:
    """Configuration data transfer object."""
    
    openweather_api_key: str
    openweather_base_url: str
    gemini_api_key: Optional[str] = None
    github_token: Optional[str] = None
    spotify_client_id: Optional[str] = None
    spotify_client_secret: Optional[str] = None
    database_url: Optional[str] = None
    cache_ttl: int = 600
    log_level: str = "INFO"
    debug_mode: bool = False
    
    def __post_init__(self):
        """Validate configuration after initialization."""
        if not self.openweather_api_key:
            raise ValueError("OpenWeather API key is required")
        
        if not self.openweather_base_url:
            raise ValueError("OpenWeather base URL is required")
        
        if self.cache_ttl < 0:
            raise ValueError("Cache TTL must be non-negative")
        
        valid_log_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if self.log_level not in valid_log_levels:
            raise ValueError(f"Log level must be one of: {valid_log_levels}")
```

### ServiceHealthDTO

Data transfer object for service health information.

```python
@dataclass(frozen=True)
class ServiceHealthDTO:
    """Service health data transfer object."""
    
    service_name: str
    is_healthy: bool
    status_message: str
    last_check: datetime
    response_time_ms: Optional[float] = None
    error_count: int = 0
    
    def to_dict(self) -> dict:
        """Convert to dictionary representation."""
        return {
            'service_name': self.service_name,
            'is_healthy': self.is_healthy,
            'status_message': self.status_message,
            'last_check': self.last_check.isoformat(),
            'response_time_ms': self.response_time_ms,
            'error_count': self.error_count
        }
```

## Error Types

### Base Exception Classes

```python
class BaseApplicationError(Exception):
    """Base exception for all application errors."""
    
    def __init__(self, message: str, error_code: Optional[str] = None, 
                 details: Optional[dict] = None):
        super().__init__(message)
        self.message = message
        self.error_code = error_code or self.__class__.__name__
        self.details = details or {}
        self.timestamp = datetime.utcnow()
    
    def to_dict(self) -> dict:
        """Convert exception to dictionary."""
        return {
            'error_type': self.__class__.__name__,
            'error_code': self.error_code,
            'message': self.message,
            'details': self.details,
            'timestamp': self.timestamp.isoformat()
        }
```

### Specific Exception Types

```python
class ValidationError(BaseApplicationError):
    """Raised when input validation fails."""
    pass

class ServiceError(BaseApplicationError):
    """Raised when a service operation fails."""
    pass

class ExternalServiceError(ServiceError):
    """Raised when an external service is unavailable or returns an error."""
    pass

class NetworkError(ExternalServiceError):
    """Raised when network operations fail."""
    pass

class TimeoutError(NetworkError):
    """Raised when operations timeout."""
    pass

class DatabaseError(ServiceError):
    """Raised when database operations fail."""
    pass

class ConfigurationError(BaseApplicationError):
    """Raised when configuration is invalid or missing."""
    pass

class ServiceResolutionError(BaseApplicationError):
    """Raised when dependency injection fails to resolve a service."""
    pass

class CircularDependencyError(ServiceResolutionError):
    """Raised when circular dependencies are detected."""
    pass
```

## Configuration Reference

### Environment Variables

| Variable | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `OPENWEATHER_API_KEY` | string | Yes | - | OpenWeatherMap API key |
| `OPENWEATHER_BASE_URL` | string | No | `https://api.openweathermap.org/data/2.5` | OpenWeatherMap API base URL |
| `GEMINI_API_KEY` | string | No | - | Google Gemini API key |
| `GITHUB_TOKEN` | string | No | - | GitHub personal access token |
| `SPOTIFY_CLIENT_ID` | string | No | - | Spotify client ID |
| `SPOTIFY_CLIENT_SECRET` | string | No | - | Spotify client secret |
| `DATABASE_URL` | string | No | `sqlite:///weather.db` | Database connection URL |
| `CACHE_TTL` | integer | No | `600` | Cache time-to-live in seconds |
| `LOG_LEVEL` | string | No | `INFO` | Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL) |
| `DEBUG` | boolean | No | `false` | Enable debug mode |
| `MAX_RETRY_ATTEMPTS` | integer | No | `3` | Maximum retry attempts for external services |
| `REQUEST_TIMEOUT` | integer | No | `30` | Request timeout in seconds |

### Configuration Sections

#### Weather Configuration
```python
weather_config = {
    'api_key': 'your_openweather_api_key',
    'base_url': 'https://api.openweathermap.org/data/2.5',
    'cache_ttl': 600,
    'units': 'metric',
    'language': 'en'
}
```

#### Database Configuration
```python
database_config = {
    'url': 'sqlite:///weather.db',
    'pool_size': 5,
    'max_overflow': 10,
    'pool_timeout': 30,
    'pool_recycle': 3600
}
```

#### Logging Configuration
```python
logging_config = {
    'level': 'INFO',
    'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    'file': 'weather_dashboard.log',
    'max_bytes': 10485760,  # 10MB
    'backup_count': 5
}
```

## Dependency Injection API

### DependencyContainer

```python
class DependencyContainer:
    """Dependency injection container."""
    
    def register_singleton(self, interface: Type[T], implementation: Type[T]) -> None:
        """Register a singleton service.
        
        Args:
            interface: Service interface type
            implementation: Service implementation type
        """
        pass
    
    def register_transient(self, interface: Type[T], implementation: Type[T]) -> None:
        """Register a transient service.
        
        Args:
            interface: Service interface type
            implementation: Service implementation type
        """
        pass
    
    def register_factory(self, interface: Type[T], factory: Callable[[], T], 
                        lifetime: ServiceLifetime) -> None:
        """Register a service factory.
        
        Args:
            interface: Service interface type
            factory: Factory function to create service instance
            lifetime: Service lifetime (SINGLETON or TRANSIENT)
        """
        pass
    
    def register_instance(self, interface: Type[T], instance: T) -> None:
        """Register a service instance.
        
        Args:
            interface: Service interface type
            instance: Service instance
        """
        pass
    
    def resolve(self, interface: Type[T]) -> T:
        """Resolve a service instance.
        
        Args:
            interface: Service interface type
            
        Returns:
            T: Service instance
            
        Raises:
            ServiceResolutionError: If service cannot be resolved
            CircularDependencyError: If circular dependency detected
        """
        pass
    
    def is_registered(self, interface: Type[T]) -> bool:
        """Check if service is registered.
        
        Args:
            interface: Service interface type
            
        Returns:
            bool: True if service is registered
        """
        pass
```

### ServiceLifetime

```python
from enum import Enum

class ServiceLifetime(Enum):
    """Service lifetime enumeration."""
    
    SINGLETON = "singleton"
    TRANSIENT = "transient"
    SCOPED = "scoped"  # Future enhancement
```

## Utility Functions

### Error Handling Utilities

```python
def safe_execute(operation: Callable[[], T], 
                fallback_value: Optional[T] = None,
                logger: Optional[ILoggingService] = None) -> Optional[T]:
    """Safely execute an operation with error handling.
    
    Args:
        operation: Operation to execute
        fallback_value: Value to return on error
        logger: Logger for error reporting
        
    Returns:
        Optional[T]: Operation result or fallback value
    """
    pass

def retry_with_backoff(operation: Callable[[], T],
                      max_attempts: int = 3,
                      base_delay: float = 1.0,
                      max_delay: float = 60.0,
                      backoff_factor: float = 2.0) -> T:
    """Retry operation with exponential backoff.
    
    Args:
        operation: Operation to retry
        max_attempts: Maximum retry attempts
        base_delay: Base delay in seconds
        max_delay: Maximum delay in seconds
        backoff_factor: Backoff multiplier
        
    Returns:
        T: Operation result
        
    Raises:
        Exception: Last exception if all attempts fail
    """
    pass
```

### Validation Utilities

```python
def validate_location(location: str) -> bool:
    """Validate location string.
    
    Args:
        location: Location to validate
        
    Returns:
        bool: True if location is valid
    """
    pass

def validate_api_key(api_key: str) -> bool:
    """Validate API key format.
    
    Args:
        api_key: API key to validate
        
    Returns:
        bool: True if API key is valid
    """
    pass

def validate_temperature(temperature: float) -> bool:
    """Validate temperature value.
    
    Args:
        temperature: Temperature to validate
        
    Returns:
        bool: True if temperature is valid
    """
    pass
```

### Conversion Utilities

```python
def celsius_to_fahrenheit(celsius: float) -> float:
    """Convert Celsius to Fahrenheit.
    
    Args:
        celsius: Temperature in Celsius
        
    Returns:
        float: Temperature in Fahrenheit
    """
    return (celsius * 9/5) + 32

def fahrenheit_to_celsius(fahrenheit: float) -> float:
    """Convert Fahrenheit to Celsius.
    
    Args:
        fahrenheit: Temperature in Fahrenheit
        
    Returns:
        float: Temperature in Celsius
    """
    return (fahrenheit - 32) * 5/9

def format_weather_description(description: str) -> str:
    """Format weather description for display.
    
    Args:
        description: Raw weather description
        
    Returns:
        str: Formatted description
    """
    return description.title()
```

---

*This API reference provides comprehensive documentation for all interfaces, DTOs, and utilities in the Weather Dashboard project. Use this reference when implementing new features or integrating with existing services.*